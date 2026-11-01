#!/usr/bin/env bash
# C-5: resume merge_gguf_v5.sh at step 4/4 from the finished f16 GGUF (the first run was killed during llama-quantize on a 20 GB-RAM pod, 2026-10-31 11:36 UTC).
# Same output files as merge_gguf_v5.sh: export/gguf/blade-qwen-lora-v5-s42-Q4_K_M.gguf, merge_manifest_v5_s42.json, SHA256SUMS_gguf_s42 (+ merge.log, quantize.log).
# The f16 file is verified against the "f16 gguf <sha> <bytes>" line that step 3/4 wrote to merge.log, so the resumed Q4 is built from the same bytes.
# Usage: tmux new -d -s q4 "bash /workspace/blade_c5/runpod/quantize_resume_c5.sh"; tail -f /workspace/blade_c5/export/gguf/quantize.log
set -euo pipefail
export BASE=${BASE:-/workspace/blade_c5}
LOCAL=${C5_LOCAL:-/root/c5}; SEED=${1:-42}; THREADS=${THREADS:-4}
WORK="$LOCAL/work"; OUT="$BASE/export/gguf"; LLAMA="$LOCAL/llama.cpp"
ADAPTER="$BASE/runs/lora_v5_s$SEED/adapter"
F16="$WORK/blade-qwen-lora-v5-s$SEED-f16.gguf"; Q4="$OUT/blade-qwen-lora-v5-s$SEED-Q4_K_M.gguf"
BASE_REPO=Qwen/Qwen2.5-7B-Instruct; BASE_REV=a09a35458c702b33eeacc393d103063234e8bc28
exec > >(tee -a "$OUT/merge.log") 2>&1
echo "=== $(date -Is) quantize_resume seed=$SEED threads=$THREADS f16=$F16"
[ -f "$F16" ] || { echo "no f16 at $F16 (run merge_gguf_v5.sh from the start)"; exit 1; }
[ -x "$LLAMA/build/bin/llama-quantize" ] || { echo "no llama-quantize at $LLAMA/build/bin"; exit 1; }
cat /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.events 2>/dev/null || true
free -g | head -2
EXP_SHA=$(grep -m1 '^f16 gguf ' "$OUT/merge.log" | cut -d' ' -f3 || true)
EXP_BYTES=$(grep -m1 '^f16 gguf ' "$OUT/merge.log" | cut -d' ' -f4 || true)
F16_SHA=$(sha256sum "$F16" | cut -d' ' -f1); F16_BYTES=$(stat -c %s "$F16")
echo "f16 gguf $F16_SHA $F16_BYTES bytes (step 3/4 logged: ${EXP_SHA:-?} ${EXP_BYTES:-?})"
if [ -n "$EXP_SHA" ] && [ "$EXP_SHA" != "$F16_SHA" ]; then echo "f16 sha differs from the step-3 log: stop"; exit 1; fi
ADAPTER_SHA=$(sha256sum "$ADAPTER/adapter_model.safetensors" | cut -d' ' -f1); echo "adapter_model.safetensors $ADAPTER_SHA"
rm -f "$Q4"
echo "== 4/4 Q4_K_M (resume, $THREADS threads; progress in $OUT/quantize.log)"
nice -n 10 "$LLAMA/build/bin/llama-quantize" "$F16" "$Q4" Q4_K_M "$THREADS" > "$OUT/quantize.log" 2>&1
Q4_SHA=$(sha256sum "$Q4" | cut -d' ' -f1); Q4_SIZE=$(stat -c %s "$Q4"); echo "Q4_K_M gguf $Q4_SHA $Q4_SIZE bytes"
python - "$OUT/merge_manifest_v5_s$SEED.json" "$SEED" "$ADAPTER" "$ADAPTER_SHA" "$F16_SHA" "$Q4" "$Q4_SHA" "$Q4_SIZE" "$BASE_REPO" "$BASE_REV" "$LLAMA" <<'PY'
import json, sys, subprocess, torch, transformers, peft
o, seed, adapter, a_sha, f16_sha, q4, q4_sha, q4_size, repo, rev, llama = sys.argv[1:12]
tag = subprocess.run(['git', '-C', llama, 'describe', '--tags', '--always'], capture_output=True, text=True).stdout.strip()
json.dump(dict(model='blade-qwen-lora-v5', seed=int(seed), adapter=adapter, adapter_sha256=a_sha, base=repo, base_revision=rev, merge_dtype='float32', merged_checkpoint_dtype='float16',
               f16_gguf_sha256=f16_sha, q4_k_m_gguf=q4, q4_k_m_sha256=q4_sha, q4_k_m_bytes=int(q4_size), llama_cpp=tag,
               versions=dict(torch=torch.__version__, transformers=transformers.__version__, peft=peft.__version__),
               note='same construction as training/lora/README_serve_v4.md (LoRA v4 s42); Q4_K_M step resumed from the step-3 f16 by quantize_resume_c5.sh'),
          open(o, 'w'), indent=2)
print('manifest', o)
PY
( cd "$OUT" && sha256sum "$(basename "$Q4")" merge_manifest_v5_s$SEED.json > "SHA256SUMS_gguf_s$SEED" && cat "SHA256SUMS_gguf_s$SEED" )
rm -f "$F16"; rmdir "$WORK" 2>/dev/null || true
echo "=== $(date -Is) quantize_resume done: $Q4"
