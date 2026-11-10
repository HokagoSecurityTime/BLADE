"""S4 permission-context augmentation: inference only (no training). Revision S4-3 (H100 SXM plan; any CUDA GPU).
Loading mirrors the LoRA v5 HF evaluation (training/lora/runpod/run_train.py lines 176-178): base 'unsloth/Qwen2.5-7B-Instruct-bnb-4bit'
(pre-quantized bitsandbytes 4-bit), dtype auto (bf16 compute), final LoRA adapter via peft, batch 8, greedy, max_new_tokens 256, left padding,
same JSON parser. Differences for this pod: --loader hf (transformers AutoModelForCausalLM + attn_implementation='sdpa', no flash-attn; unsloth
is optional via --loader unsloth), the input file and the sequence budget (--max-len 4096 | 6144) are arguments.
Resumable: --resume keeps the existing output rows (by id) and appends one row per record as soon as it is generated.
    python run_ctx_eval.py --adapter runs/lora_v5_s42/adapter --inputs data/test_v5_ctx4096_inputs.jsonl --out out/pred_test_v5_ctx4096_s42.jsonl --max-len 4096 --resume
--adapter none = base model. --ids FILE = only these ids (baseline reproduction check). --limit N = smoke test into <out>.smoke.jsonl.
Writes <out>.timing.json (gpu, versions, wall time) and out/env.json (environment record)."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, re, sys, time
from pathlib import Path

LABELS = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']
BASE_MODEL = 'unsloth/Qwen2.5-7B-Instruct-bnb-4bit'; MAX_NEW, BATCH = 256, 8
PROMPT_SHA = 'd0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef'


def parse(text):
    m = re.search(r'\{.*\}', text, re.S)
    try:
        o = json.loads(m.group(0)) if m else None
        return o if isinstance(o, dict) and o.get('label') in LABELS else None
    except Exception: return None


def env_record():
    import torch, transformers, peft
    try: import bitsandbytes as bnb; bnb_v = bnb.__version__
    except Exception as e: bnb_v = f'import failed: {e}'
    try: import unsloth; us_v = unsloth.__version__
    except Exception: us_v = None
    cap = torch.cuda.get_device_capability(0)
    return dict(gpu=torch.cuda.get_device_name(0), vram_gb=torch.cuda.get_device_properties(0).total_memory // 2**30, capability=list(cap), torch=torch.__version__, cuda=torch.version.cuda,
                transformers=transformers.__version__, peft=peft.__version__, bitsandbytes=bnb_v, unsloth=us_v, python=platform.python_version(), driver=os.popen('nvidia-smi --query-gpu=driver_version --format=csv,noheader').read().strip())


def load_model(adapter, max_len, loader):
    import torch
    from peft import PeftModel
    if loader == 'unsloth':
        from unsloth import FastLanguageModel
        base, tok = FastLanguageModel.from_pretrained(model_name=BASE_MODEL, max_seq_length=max_len, dtype=None, load_in_4bit=True)
        model = PeftModel.from_pretrained(base, adapter) if adapter != 'none' else base; FastLanguageModel.for_inference(model); return model, tok
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(BASE_MODEL)
    try: base = AutoModelForCausalLM.from_pretrained(BASE_MODEL, device_map={'': 0}, dtype=torch.bfloat16, attn_implementation='sdpa')  # checkpoint carries its bnb 4-bit config (transformers >= 4.56 / 5.x)
    except TypeError: base = AutoModelForCausalLM.from_pretrained(BASE_MODEL, device_map={'': 0}, torch_dtype=torch.bfloat16, attn_implementation='sdpa')  # older transformers
    model = PeftModel.from_pretrained(base, adapter) if adapter != 'none' else base; model.eval()
    if tok.pad_token_id is None: tok.pad_token = tok.eos_token
    return model, tok


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--adapter', required=True); ap.add_argument('--inputs', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--max-len', type=int, required=True); ap.add_argument('--system', default=str(Path(__file__).resolve().parent / 'data/policy_label_v3.0.1.md'))
    ap.add_argument('--key', default='oas_code_user'); ap.add_argument('--batch', type=int, default=BATCH); ap.add_argument('--limit', type=int, default=0); ap.add_argument('--ids', default=None)
    ap.add_argument('--resume', action='store_true'); ap.add_argument('--loader', choices=['hf', 'unsloth'], default='hf'); a = ap.parse_args()
    system = open(a.system, encoding='utf-8').read(); assert hashlib.sha256(open(a.system, 'rb').read()).hexdigest() == PROMPT_SHA, 'prompt v3.0.1 hash mismatch'
    rows = [json.loads(l) for l in open(a.inputs, encoding='utf-8') if l.strip()]; rows = [r for r in rows if a.key in r]
    if a.ids: keep = set(json.loads(open(a.ids, encoding='utf-8').read())); rows = [r for r in rows if r['id'] in keep]
    rows = rows[:a.limit or None]; out = a.out + ('.smoke.jsonl' if a.limit else ''); Path(out).parent.mkdir(parents=True, exist_ok=True)
    done = {}
    if a.resume and os.path.exists(out) and not a.limit:
        for l in open(out, encoding='utf-8'):
            if l.strip(): r = json.loads(l); done[r['id']] = r
    todo = [r for r in rows if r['id'] not in done]
    print(f'{len(rows)} rows, {len(done)} already done, {len(todo)} to run', flush=True)
    env = env_record(); Path(Path(out).parent, 'env.json').write_text(json.dumps(env, ensure_ascii=False, indent=1), encoding='utf-8'); print(json.dumps(env), flush=True)
    if not todo:
        print('nothing to do:', out); return
    import torch
    t_load = time.perf_counter(); model, tok = load_model(a.adapter, a.max_len, a.loader); load_s = time.perf_counter() - t_load
    gen_kw = dict(max_new_tokens=MAX_NEW, do_sample=False, temperature=None, top_p=None, pad_token_id=tok.pad_token_id)
    n_err = n_manual = truncated = 0; ms_sum = 0.; tok_max = 0; t_all = time.perf_counter()
    f = open(out, 'a' if (a.resume and not a.limit) else 'w', encoding='utf-8')
    for i in range(0, len(todo), a.batch):
        batch = todo[i:i + a.batch]; prompts = [tok.apply_chat_template([{'role': 'system', 'content': system}, {'role': 'user', 'content': r[a.key]}], tokenize=False, add_generation_prompt=True) for r in batch]
        tok.padding_side = 'left'; lens = [len(tok(p).input_ids) for p in prompts]; truncated += sum(l > a.max_len for l in lens); tok_max = max(tok_max, max(lens))
        enc = tok(prompts, return_tensors='pt', padding=True, truncation=True, max_length=a.max_len).to('cuda'); t0 = time.perf_counter()
        with torch.no_grad(): gen = model.generate(**enc, **gen_kw)
        ms = (time.perf_counter() - t0) * 1000 / len(batch)
        for j, r in enumerate(batch):
            text = tok.decode(gen[j][enc.input_ids.shape[1]:], skip_special_tokens=True); p = parse(text)
            n_err += p is None; n_manual += bool(p) and p['label'] == 'manual_review_required'; ms_sum += ms
            f.write(json.dumps(dict(id=r['id'], label=r['label'], source=r.get('source'), security_state=r.get('security_state'), prediction=p, raw=text, inference_ms=round(ms, 1), prompt_tokens=lens[j]), ensure_ascii=False) + '\n'); f.flush()
        if (i // a.batch) % 5 == 0: print(f'{len(done) + i + len(batch)}/{len(rows)} rows, {ms:.0f} ms/row', flush=True)
    f.close(); wall = time.perf_counter() - t_all
    timing = dict(out=out, adapter=a.adapter, inputs=a.inputs, max_len=a.max_len, loader=a.loader, rows_total=len(rows), rows_run=len(todo), resumed=len(done), gpu=env['gpu'], model_load_s=round(load_s, 1),
                  inference_wall_s=round(wall, 1), mean_ms_per_row=round(ms_sum / max(1, len(todo)), 1), parse_errors=n_err, manual=n_manual, prompt_tokens_max=tok_max, truncated_prompts=truncated, finished=time.strftime('%Y-%m-%dT%H:%M:%S'))
    prev = Path(out + '.timing.json')
    if prev.exists() and a.resume and not a.limit:  # accumulate across resumed runs
        try:
            old = json.loads(prev.read_text(encoding='utf-8')); timing['inference_wall_s'] = round(old.get('inference_wall_s', 0) + timing['inference_wall_s'], 1); timing['model_load_s'] = round(old.get('model_load_s', 0) + load_s, 1); timing['runs'] = old.get('runs', 1) + 1
        except Exception: pass
    prev.write_text(json.dumps(timing, ensure_ascii=False, indent=1), encoding='utf-8'); print(json.dumps(timing, ensure_ascii=False))
    del model; torch.cuda.empty_cache()


if __name__ == '__main__': main()
