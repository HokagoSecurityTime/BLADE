"""Merge the LoRA v4 adapter into the unquantized Qwen2.5-7B-Instruct base and write an f16 GGUF.

The base weights are read tensor by tensor from Hugging Face (llama.cpp convert_hf_to_gguf remote mode, pinned revision),
so no base shard or merged HF checkpoint is written to disk. Each LoRA target weight is merged in fp32
(W + alpha/r * B @ A) and handed to the converter, which casts it to f16. The 4-bit training base is not used.
Quantization to Q4_K_M is a separate llama-quantize step (training/lora/README_serve_v4.md).

Usage: python -X utf8 training/lora/merge_gguf_v4.py --adapter <dir with adapter_model.safetensors> --llama-src <llama.cpp source dir> --out <f16.gguf>
"""
import argparse, hashlib, json, logging, re, shutil, sys, time
from pathlib import Path

BASE_REPO = 'Qwen/Qwen2.5-7B-Instruct'
BASE_REVISION = 'a09a35458c702b33eeacc393d103063234e8bc28'   # HF main on 2026-10-29
TOKENIZER_FILES = ('tokenizer.json', 'tokenizer_config.json', 'chat_template.jinja')   # from the adapter = training tokenizer/template
LAYERS, TARGETS = 28, 7


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for block in iter(lambda: f.read(1 << 24), b''): h.update(block)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--adapter', type=Path, required=True)
    ap.add_argument('--llama-src', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    log = logging.getLogger('merge')
    sys.path.insert(0, str(args.llama_src)); sys.path.insert(1, str(args.llama_src / 'gguf-py'))
    import requests, torch, gguf
    from safetensors.torch import load_file
    from conversion import get_model_architecture, get_model_class, ModelType
    from conversion.base import LazyTorchTensor, ModelBase
    from gguf.utility import SafetensorRemote, RemoteTensor

    cfg = json.loads((args.adapter / 'adapter_config.json').read_text(encoding='utf-8'))
    assert cfg['peft_type'] == 'LORA' and not cfg['use_dora'] and not cfg['use_rslora'] and cfg['modules_to_save'] is None
    scale = cfg['lora_alpha'] / cfg['r']
    lora: dict[str, dict[str, torch.Tensor]] = {}
    for k, v in load_file(str(args.adapter / 'adapter_model.safetensors')).items():
        m = re.fullmatch(r'base_model\.model\.(.+)\.lora_([AB])\.weight', k)
        assert m, k
        lora.setdefault(m[1] + '.weight', {})[m[2]] = v.float()
    assert len(lora) == LAYERS * TARGETS and all(set(p) == {'A', 'B'} for p in lora.values()), len(lora)

    # Local model dir: base config + training tokenizer files; weights stay remote.
    meta = args.out.parent / 'hf_meta'; meta.mkdir(parents=True, exist_ok=True)
    for name in ('config.json', 'generation_config.json'):
        r = requests.get(f'https://huggingface.co/{BASE_REPO}/resolve/{BASE_REVISION}/{name}', timeout=60); r.raise_for_status()
        (meta / name).write_bytes(r.content)
    for name in TOKENIZER_FILES: shutil.copy(args.adapter / name, meta / name)

    def listing(model_id: str) -> dict[str, RemoteTensor]:
        assert model_id == BASE_REPO
        root = f'{SafetensorRemote.BASE_DOMAIN}/{BASE_REPO}/resolve/{BASE_REVISION}'
        index = json.loads(SafetensorRemote.get_data_by_range(f'{root}/model.safetensors.index.json', 0).decode('utf-8'))
        tensors: dict[str, RemoteTensor] = {}
        for file in sorted(set(index['weight_map'].values())):
            for key, val in SafetensorRemote.get_list_tensors(f'{root}/{file}').items():
                val._blade_name = key; tensors[key] = val
        return tensors

    def data(self: RemoteTensor) -> bytearray:   # upstream has no retry; one network error would abort a 15 GB stream
        for attempt in range(6):
            try:
                out = bytearray(SafetensorRemote.get_data_by_range(url=self.url, start=self.offset_start, size=self.size))
                if len(out) == self.size: return out
                raise IOError(f'short read {len(out)}/{self.size}')
            except Exception as exc:
                if attempt == 5: raise
                log.warning('retry %s (%s)', getattr(self, '_blade_name', '?'), exc); time.sleep(2 ** attempt)
        raise AssertionError

    merged: list[str] = []
    upstream = LazyTorchTensor.from_remote_tensor.__func__

    def from_remote(cls, r: RemoteTensor):
        pair = lora.get(getattr(r, '_blade_name', ''))
        if pair is None: return upstream(cls, r)
        name, shape = r._blade_name, tuple(r.shape)
        assert r.dtype == 'BF16' and tuple(pair['B'].shape[:1]) + tuple(pair['A'].shape[1:]) == shape, name

        def load(r: RemoteTensor) -> torch.Tensor:
            import numpy as np
            w = torch.from_numpy(np.frombuffer(r.data(), dtype=np.float16)).view(torch.bfloat16).reshape(shape).float()
            merged.append(name)
            return w + scale * (pair['B'] @ pair['A'])
        return cls(meta=cls.meta_with_dtype_and_shape(torch.float32, shape), args=(r,), func=load)

    SafetensorRemote.get_list_tensors_hf_model = classmethod(lambda cls, model_id: listing(model_id))
    RemoteTensor.data = data
    LazyTorchTensor.from_remote_tensor = classmethod(from_remote)

    t0 = time.time()
    with torch.inference_mode():
        hparams = ModelBase.load_hparams(meta, False)
        model_class = get_model_class(get_model_architecture(hparams, ModelType.TEXT))
        model_class.set_vocab = lambda self: self._set_vocab_gpt2()   # Qwen2.5 has no tokenizer.model; upstream reaches this branch via FileNotFoundError
        model = model_class(meta, gguf.LlamaFileType.MOSTLY_F16, args.out, remote_hf_model_id=BASE_REPO,
                            model_name='blade-qwen-lora-v4')
        model.write()
    assert sorted(merged) == sorted(lora), f'merged {len(merged)} of {len(lora)} LoRA targets'
    manifest = dict(base=BASE_REPO, base_revision=BASE_REVISION, adapter=str(args.adapter),
                    adapter_sha256=sha(args.adapter / 'adapter_model.safetensors'), lora_scale=scale,
                    merged_tensors=len(merged), merge_dtype='float32', out=str(args.out), out_type='f16',
                    out_sha256=sha(args.out), minutes=round((time.time() - t0) / 60, 1))
    (args.out.parent / 'merge_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    log.info('done %s', manifest)


if __name__ == '__main__':
    main()
