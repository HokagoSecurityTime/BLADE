#!/usr/bin/env bash
# Task C-4 (AGENTS.md 작업 C): merge the FINAL LoRA v5 adapter of one seed (default 42) into the unquantized Qwen2.5-7B-Instruct base and write GGUF Q4_K_M.
# Same construction as the local LoRA v4 serving build (training/lora/README_serve_v4.md, merge_gguf_v4.py): base revision a09a3545…, fp32 merge
# W + (alpha/r)·B·A, f16 GGUF via llama.cpp b11693 convert_hf_to_gguf.py, then llama-quantize Q4_K_M. The tokenizer/chat template come from the adapter dir.
# Usage: bash merge_gguf_v5.sh [seed]        (run_all.sh calls it after all runs; GGUF_SEED= disables)
# Output: <BASE>/export/gguf/blade-qwen-lora-v5-s<seed>-Q4_K_M.gguf, merge_manifest_v5_s<seed>.json (hashes, versions), SHA256SUMS_gguf, merge.log
# Disk: merged fp16 checkpoint ~15GB + f16 GGUF ~15GB + Q4_K_M ~4.7GB at peak; the first two are deleted afterwards. RAM: fp32 merge on CPU needs ~32GB.
# Never trains, never touches runs/<run>/adapter. Re-running overwrites the GGUF of the same seed.
# C-5 (2026-10-31): the merged checkpoint + f16 GGUF (30 GB) must NOT go on a quota-limited network volume (Disk quota exceeded on 10-31).
#   WORK_DIR / HF_HOME / LLAMA_SRC point them at the container disk; DROP_HF_CACHE=1 deletes the base download right after the merge (peak 30 GB instead of 45 GB).
set -euo pipefail
BASE=${BASE:-/workspace/blade_lora_v3}
SEED=${1:-42}
RUN="$BASE/runs/lora_v5_s$SEED"; ADAPTER="$RUN/adapter"
OUT="$BASE/export/gguf"; WORK=${WORK_DIR:-$BASE/gguf_work_s$SEED}
LLAMA=${LLAMA_SRC:-/workspace/llama.cpp}; LLAMA_TAG=${LLAMA_TAG:-b11693}
BASE_REPO=Qwen/Qwen2.5-7B-Instruct; BASE_REV=a09a35458c702b33eeacc393d103063234e8bc28
export HF_HOME=${HF_HOME:-/workspace/hf}
mkdir -p "$OUT" "$WORK"
exec > >(tee -a "$OUT/merge.log") 2>&1
echo "=== $(date -Is) merge_gguf_v5 seed=$SEED adapter=$ADAPTER"
[ -f "$ADAPTER/adapter_model.safetensors" ] || { echo "no final adapter at $ADAPTER (training not finished?)"; exit 1; }
[ -f "$RUN/logs/train_result.json" ] || echo "warning: $RUN/logs/train_result.json missing (adapter restored from an archive?)"
ADAPTER_SHA=$(sha256sum "$ADAPTER/adapter_model.safetensors" | cut -d' ' -f1); echo "adapter_model.safetensors $ADAPTER_SHA"
df -h "$BASE" | tail -1

echo "== 1/4 llama.cpp $LLAMA_TAG (convert script + llama-quantize)"
if [ ! -d "$LLAMA/.git" ]; then git clone -q --depth 1 --branch "$LLAMA_TAG" https://github.com/ggml-org/llama.cpp "$LLAMA"; fi
( cd "$LLAMA" && echo "llama.cpp $(git describe --tags --always)" )
pip install -q sentencepiece >/dev/null 2>&1 || true     # convert_hf_to_gguf needs only numpy/torch/transformers/sentencepiece + the repo's gguf-py (no requirements file: it would re-pin torch)
command -v cmake >/dev/null || pip install -q cmake
if [ ! -x "$LLAMA/build/bin/llama-quantize" ]; then
  cmake -S "$LLAMA" -B "$LLAMA/build" -DGGML_CUDA=OFF -DLLAMA_CURL=OFF -DBUILD_SHARED_LIBS=OFF -DCMAKE_BUILD_TYPE=Release >/dev/null
  cmake --build "$LLAMA/build" --target llama-quantize -j "$(nproc)" >/dev/null
fi
"$LLAMA/build/bin/llama-quantize" --help >/dev/null 2>&1 || true

echo "== 2/4 fp32 merge -> fp16 HF checkpoint ($WORK/merged)"
python - "$ADAPTER" "$WORK/merged" "$BASE_REPO" "$BASE_REV" <<'PY'
import json, sys, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
adapter, out, repo, rev = sys.argv[1:5]
cfg = json.load(open(f'{adapter}/adapter_config.json'))
assert cfg['peft_type'] == 'LORA' and not cfg.get('use_dora') and not cfg.get('use_rslora') and not cfg.get('modules_to_save'), cfg
try: model = AutoModelForCausalLM.from_pretrained(repo, revision=rev, dtype=torch.float32, device_map='cpu', low_cpu_mem_usage=True)
except TypeError: model = AutoModelForCausalLM.from_pretrained(repo, revision=rev, torch_dtype=torch.float32, device_map='cpu', low_cpu_mem_usage=True)
model = PeftModel.from_pretrained(model, adapter)
n_lora = sum('lora_A' in n for n, _ in model.named_parameters()); print('lora target weights:', n_lora)
assert n_lora == 28 * 7, n_lora
model = model.merge_and_unload()                       # W += (alpha/r) * B @ A, in fp32
model = model.to(torch.float16); model.save_pretrained(out, safe_serialization=True, max_shard_size='5GB')
tok = AutoTokenizer.from_pretrained(adapter); tok.save_pretrained(out)   # training tokenizer + chat template
print('merged fp16 checkpoint written to', out)
PY

if [ "${DROP_HF_CACHE:-0}" = "1" ]; then rm -rf "$HF_HOME/hub/models--Qwen--Qwen2.5-7B-Instruct"; echo "dropped HF cache of the base (DROP_HF_CACHE=1)"; fi
df -h "$WORK" | tail -1

echo "== 3/4 f16 GGUF"
F16="$WORK/blade-qwen-lora-v5-s$SEED-f16.gguf"
PYTHONPATH="$LLAMA/gguf-py" python "$LLAMA/convert_hf_to_gguf.py" "$WORK/merged" --outtype f16 --outfile "$F16"
F16_SHA=$(sha256sum "$F16" | cut -d' ' -f1); echo "f16 gguf $F16_SHA $(stat -c %s "$F16") bytes"
rm -rf "$WORK/merged"

echo "== 4/4 Q4_K_M"
Q4="$OUT/blade-qwen-lora-v5-s$SEED-Q4_K_M.gguf"
"$LLAMA/build/bin/llama-quantize" "$F16" "$Q4" Q4_K_M >/dev/null
Q4_SHA=$(sha256sum "$Q4" | cut -d' ' -f1); Q4_SIZE=$(stat -c %s "$Q4"); echo "Q4_K_M gguf $Q4_SHA $Q4_SIZE bytes"
rm -f "$F16"; rmdir "$WORK" 2>/dev/null || true
python - "$OUT/merge_manifest_v5_s$SEED.json" "$SEED" "$ADAPTER" "$ADAPTER_SHA" "$F16_SHA" "$Q4" "$Q4_SHA" "$Q4_SIZE" "$BASE_REPO" "$BASE_REV" "$LLAMA" <<'PY'
import json, sys, subprocess, torch, transformers, peft
o, seed, adapter, a_sha, f16_sha, q4, q4_sha, q4_size, repo, rev, llama = sys.argv[1:12]
tag = subprocess.run(['git', '-C', llama, 'describe', '--tags', '--always'], capture_output=True, text=True).stdout.strip()
json.dump(dict(model='blade-qwen-lora-v5', seed=int(seed), adapter=adapter, adapter_sha256=a_sha, base=repo, base_revision=rev, merge_dtype='float32', merged_checkpoint_dtype='float16',
               f16_gguf_sha256=f16_sha, q4_k_m_gguf=q4, q4_k_m_sha256=q4_sha, q4_k_m_bytes=int(q4_size), llama_cpp=tag,
               versions=dict(torch=torch.__version__, transformers=transformers.__version__, peft=peft.__version__), note='same construction as training/lora/README_serve_v4.md (LoRA v4 s42)'),
          open(o, 'w'), indent=2)
print('manifest', o)
PY
( cd "$OUT" && sha256sum "$(basename "$Q4")" merge_manifest_v5_s$SEED.json > "SHA256SUMS_gguf_s$SEED" && cat "SHA256SUMS_gguf_s$SEED" )
echo "=== $(date -Is) merge_gguf_v5 done: $Q4"
