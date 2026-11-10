#!/usr/bin/env bash
# D1 a–c on RunPod (AGENTS.md 작업 D1, 2026-11-10; same procedure as C-5 run_c5.sh): seed-42 LoRA v7 final adapter -> fp32 merge -> GGUF Q4_K_M (container disk),
# Ollama registration with Modelfile.blade-qwen-lora-v7, then GGUF inference on (b) test_v30 oas_code (equivalence vs HF s42) and (c) val_sft_v7 (threshold).
# Scoring, threshold choice, local Ollama registration and the pipeline check happen locally afterwards (training/lora/README_serve_v7.md).
# Pod requirements (checked below, user instruction 2026-11-10): RAM >= 64 GB (fp32 merge), container disk >= 70 GB free, volume at /workspace or /workspace-2.
# Layout: $BASE = the existing volume dir that holds runs/lora_v7_s42/adapter and data_v7/ (auto-detected: /workspace/blade_lora_v3 or /workspace-2/blade_lora_v3),
#   or a fresh dir where blade_c7_v7_<date>.tgz was extracted (it carries runs/lora_v7_s42/adapter, data_v7/, runpod/, eval_ollama_v7.py, Modelfile.blade-qwen-lora-v7).
# Usage: bash runpod/setup_c5.sh && tmux new -d -s c7 "bash <BASE>/runpod/run_c7.sh"; tail -f <BASE>/export/c7.log
# Outputs under $BASE/export: gguf/blade-qwen-lora-v7-s42-Q4_K_M.gguf, gguf/merge_manifest_v7_s42.json, gguf/SHA256SUMS_gguf_v7_s42, gguf/merge.log, gguf/quantize.log,
#   gguf_eval/predictions_oas_code_lora_v7_s42_gguf_q4km.jsonl, gguf_eval/val_predictions_lora_v7_s42_gguf_q4km.jsonl, gguf_eval/template_check.log, SHA256SUMS_c7, c7.log
set -uo pipefail
if [ -z "${BASE:-}" ]; then
  for d in /workspace/blade_lora_v3 /workspace-2/blade_lora_v3 /workspace/blade_c7 /workspace-2/blade_c7; do
    if [ -f "$d/runs/lora_v7_s42/adapter/adapter_model.safetensors" ]; then BASE=$d; break; fi
  done
fi
export BASE=${BASE:?set BASE (dir with runs/lora_v7_s42/adapter and data_v7/)}
LOCAL=${C7_LOCAL:-/root/c7}                      # container disk: HF cache, merge work dir, llama.cpp build, Ollama models
STOP_POD=${STOP_POD:-1}
MIN_RAM_GB=${MIN_RAM_GB:-60}                     # `free -g` rounds down; a 64 GB pod reports 62-63
MIN_DISK_GB=${MIN_DISK_GB:-70}                   # peak ~30 GB (DROP_HF_CACHE=1) + llama.cpp build + Ollama blob 4.7 GB
export HF_HOME=${HF_HOME:-$LOCAL/hf}
export OLLAMA_MODELS=${OLLAMA_MODELS:-$LOCAL/ollama}
ADAPTER_SHA=66c68a58b81a859ea77b9ccfe7d88716c3223f78a8a050754955d70e25184777     # lora_v7_s42 adapter_model.safetensors (blade_v7_lora_v7_s42_adapter.tar.gz 9dc03740…)
HASHES_SHA=bd33f1bcf0f68ab5fe5b96195c0da3cf6affbb3486fb85bef542b3f77e88ba73      # data_v7/data_v7_hashes.json (AGENTS.md data-v7 동결)
PROMPT_SHA=d0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef      # policy_label_v3.0.1.md
mkdir -p "$BASE/export/gguf" "$BASE/export/gguf_eval" "$LOCAL"
LOG="$BASE/export/c7.log"
exec > >(tee -a "$LOG") 2>&1
say() { echo "=== $(date -Is) $*"; }
fail() { say "FAILED: $*"; finish 1; }
finish() {
  (cd "$BASE/export" && sha256sum gguf/*.gguf gguf/*.json gguf/SHA256SUMS* gguf_eval/*.jsonl 2>/dev/null > SHA256SUMS_c7; cat SHA256SUMS_c7; ls -lh gguf gguf_eval)
  say "end (status $1)"
  if [ "$STOP_POD" = "1" ]; then
    say "stopping pod ${RUNPOD_POD_ID:-?} in 60 s (STOP_POD=0 to keep it running)"; sleep 60
    if command -v runpodctl >/dev/null 2>&1 && [ -n "${RUNPOD_POD_ID:-}" ]; then runpodctl stop pod "$RUNPOD_POD_ID" || say "POD NOT STOPPED: runpodctl stop failed. STOP IT MANUALLY."
    else say "POD NOT STOPPED: runpodctl or RUNPOD_POD_ID missing. STOP IT MANUALLY in the RunPod console."; fi
  fi
  exit "$1"
}
cd "$BASE" || { echo "no $BASE"; exit 1; }
SCRIPTS=$(cd "$(dirname "$0")" && pwd)             # runpod/ dir that holds merge_gguf_v7.sh; eval_ollama_v7.py + Modelfile sit one level up or in $BASE
EVAL_PY=$([ -f "$BASE/eval_ollama_v7.py" ] && echo "$BASE/eval_ollama_v7.py" || echo "$SCRIPTS/../eval_ollama_v7.py")
MODELFILE=$([ -f "$BASE/Modelfile.blade-qwen-lora-v7" ] && echo "$BASE/Modelfile.blade-qwen-lora-v7" || echo "$SCRIPTS/../Modelfile.blade-qwen-lora-v7")
say "run_c7 BASE=$BASE LOCAL=$LOCAL pod=${RUNPOD_POD_ID:-?} scripts=$SCRIPTS"
say "-- gates (pod spec, user instruction 2026-11-10)"
RAM_GB=$(free -g | awk '/^Mem:/{print $2}'); DISK_GB=$(df -BG --output=avail "$LOCAL" | tail -1 | tr -dc '0-9')
free -g | head -2; df -h / "$LOCAL" "$BASE" | tail -3; nproc; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || true
[ "$RAM_GB" -ge "$MIN_RAM_GB" ] || fail "RAM ${RAM_GB} GB < ${MIN_RAM_GB} GB: fp32 merge of a 7.6B model needs >= 64 GB (C-5 2026-10-31 died at 20 GB). Pick a bigger pod."
[ "$DISK_GB" -ge "$MIN_DISK_GB" ] || fail "container disk free ${DISK_GB} GB < ${MIN_DISK_GB} GB at $LOCAL (merged fp16 15 GB + f16 GGUF 15 GB + Q4 5 GB + llama.cpp)."
case "$BASE" in /workspace/*|/workspace-2/*) say "volume path ok: $BASE";; *) say "WARNING: BASE is not under /workspace or /workspace-2 — results would be lost with the container";; esac
python -c "import transformers, peft, httpx" 2>/dev/null || fail "python packages missing: run bash runpod/setup_c5.sh first"
command -v ollama >/dev/null || fail "ollama missing: run bash runpod/setup_c5.sh first"
[ -f "$EVAL_PY" ] || fail "eval_ollama_v7.py not found ($EVAL_PY)"; [ -f "$MODELFILE" ] || fail "Modelfile.blade-qwen-lora-v7 not found ($MODELFILE)"
[ "$(sha256sum runs/lora_v7_s42/adapter/adapter_model.safetensors | cut -d' ' -f1)" = "$ADAPTER_SHA" ] || fail "adapter sha mismatch (expected lora_v7_s42 final $ADAPTER_SHA)"
[ "$(sha256sum data_v7/data_v7_hashes.json | cut -d' ' -f1)" = "$HASHES_SHA" ] || fail "data_v7_hashes.json sha mismatch"
[ "$(sha256sum data_v7/policy_label_v3.0.1.md | cut -d' ' -f1)" = "$PROMPT_SHA" ] || fail "prompt v3.0.1 sha mismatch"
python - <<'PY' || fail "data_v7 generated-file hashes mismatch (test_v30_inputs / val_sft_v7)"
import hashlib, json
h = json.load(open('data_v7/data_v7_hashes.json'))['generated']
for n in ('test_v30_inputs.jsonl', 'val_sft_v7.jsonl'):
    assert hashlib.sha256(open(f'data_v7/{n}', 'rb').read()).hexdigest() == h[n], n
print('data_v7 inputs verified')
PY
say "-- gates passed"

Q4="$BASE/export/gguf/blade-qwen-lora-v7-s42-Q4_K_M.gguf"
if [ -f "$Q4" ] && [ -f "$BASE/export/gguf/SHA256SUMS_gguf_v7_s42" ] && (cd "$BASE/export/gguf" && sha256sum -c --quiet SHA256SUMS_gguf_v7_s42); then
  say "a) GGUF already present and verified, skipping merge"
else
  say "a) GGUF merge (work dir on container disk: $LOCAL/work)"
  WORK_DIR="$LOCAL/work" LLAMA_SRC="$LOCAL/llama.cpp" DROP_HF_CACHE=1 bash "$SCRIPTS/merge_gguf_v7.sh" 42 || fail "merge_gguf_v7.sh"
  say "a) GGUF ok"
fi

say "ollama serve (models in $OLLAMA_MODELS)"
if ! curl -fs http://127.0.0.1:11434/api/tags >/dev/null; then
  nohup ollama serve > "$BASE/export/ollama_serve.log" 2>&1 &
  for i in $(seq 1 60); do curl -fs http://127.0.0.1:11434/api/tags >/dev/null && break; sleep 2; done
  curl -fs http://127.0.0.1:11434/api/tags >/dev/null || fail "ollama serve did not start (export/ollama_serve.log)"
fi
cp "$MODELFILE" "$BASE/export/gguf/" && (cd "$BASE/export/gguf" && ollama create blade-qwen-lora-v7 -f Modelfile.blade-qwen-lora-v7) || fail "ollama create"
ollama show blade-qwen-lora-v7 --modelfile | head -5

say "b) test_v30 oas_code with the GGUF (equivalence input; nothing tuned on it)"
python "$EVAL_PY" --split test --data-dir data_v7 --check-template 3 --tokenizer runs/lora_v7_s42/adapter \
  --out export/gguf_eval/predictions_oas_code_lora_v7_s42_gguf_q4km.jsonl 2>&1 | tee export/gguf_eval/template_check.log | grep -v '^[0-9]*/[0-9]* ' || true
[ -s export/gguf_eval/predictions_oas_code_lora_v7_s42_gguf_q4km.jsonl ] || fail "test predictions missing"
say "c) val_sft_v7 with the GGUF (threshold input only)"
python "$EVAL_PY" --split val --data-dir data_v7 --out export/gguf_eval/val_predictions_lora_v7_s42_gguf_q4km.jsonl | grep -v '^[0-9]*/[0-9]* ' || true
[ -s export/gguf_eval/val_predictions_lora_v7_s42_gguf_q4km.jsonl ] || fail "val predictions missing"
ollama ps
say "pack results (GGUF is separate: export/gguf/blade-qwen-lora-v7-s42-Q4_K_M.gguf, 4.7 GB)"
(cd "$BASE/export" && tar czf blade_c7_v7_results.tar.gz gguf/merge_manifest_v7_s42.json gguf/SHA256SUMS_gguf_v7_s42 gguf/merge.log gguf/quantize.log gguf_eval c7.log 2>/dev/null; sha256sum blade_c7_v7_results.tar.gz)
finish 0
