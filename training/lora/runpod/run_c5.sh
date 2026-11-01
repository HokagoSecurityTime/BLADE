#!/usr/bin/env bash
# C-5 a–c on RunPod (AGENTS.md 작업 C, user approval 2026-10-31): seed-42 LoRA v5 final adapter -> fp16 merge -> GGUF Q4_K_M (container disk),
# Ollama registration with Modelfile.blade-qwen-lora-v5, then GGUF inference on (b) test_v30 oas_code (equivalence vs HF s42) and (c) val_sft_v5 (threshold).
# Scoring, threshold choice, local Ollama registration and the pipeline check happen locally afterwards (README_runpod_rerun.md 4.6).
# Layout (bundle blade_c5_v5_<date>.tgz extracted at $BASE): runs/lora_v5_s42/adapter/, data_v5/, runpod/, eval_ollama_v5.py, Modelfile.blade-qwen-lora-v5
# Usage: bash runpod/setup_c5.sh && tmux new -d -s c5 "bash /workspace/blade_c5/runpod/run_c5.sh"; tail -f /workspace/blade_c5/export/c5.log
# Outputs under $BASE/export: gguf/blade-qwen-lora-v5-s42-Q4_K_M.gguf, gguf/merge_manifest_v5_s42.json, gguf/SHA256SUMS_gguf_s42, gguf/merge.log,
#   gguf_eval/predictions_oas_code_lora_v5_s42_gguf_q4km.jsonl, gguf_eval/val_predictions_lora_v5_s42_gguf_q4km.jsonl, gguf_eval/template_check.log, SHA256SUMS_c5, c5.log
set -uo pipefail
export BASE=${BASE:-/workspace/blade_c5}     # exported: merge_gguf_v5.sh reads BASE too (its default is the old /workspace/blade_lora_v3)
LOCAL=${C5_LOCAL:-/root/c5}
STOP_POD=${STOP_POD:-1}
export HF_HOME=${HF_HOME:-$LOCAL/hf}
export OLLAMA_MODELS=${OLLAMA_MODELS:-$LOCAL/ollama}
ADAPTER_SHA=75ea08c194cb925556abcf4054f3236b8cea3c42e41eede31300ba443561b5d5     # lora_v5_s42 adapter_model.safetensors (lora_v5_report.md 4절)
HASHES_SHA=39c302c5fb33d1b1506487678cd15f40cc83ffd59435449522786388554753ac     # data_v5_hashes.json (AGENTS.md data-v5)
mkdir -p "$BASE/export/gguf" "$BASE/export/gguf_eval" "$LOCAL"
LOG="$BASE/export/c5.log"
exec > >(tee -a "$LOG") 2>&1
say() { echo "=== $(date -Is) $*"; }
fail() { say "FAILED: $*"; finish 1; }
finish() {
  (cd "$BASE/export" && sha256sum gguf/*.gguf gguf/*.json gguf/SHA256SUMS* gguf_eval/*.jsonl 2>/dev/null > SHA256SUMS_c5; cat SHA256SUMS_c5; ls -lh gguf gguf_eval)
  say "end (status $1)"
  if [ "$STOP_POD" = "1" ]; then
    say "stopping pod ${RUNPOD_POD_ID:-?} in 60 s (STOP_POD=0 to keep it running)"; sleep 60
    if command -v runpodctl >/dev/null 2>&1 && [ -n "${RUNPOD_POD_ID:-}" ]; then runpodctl stop pod "$RUNPOD_POD_ID" || say "POD NOT STOPPED: runpodctl stop failed. STOP IT MANUALLY."
    else say "POD NOT STOPPED: runpodctl or RUNPOD_POD_ID missing. STOP IT MANUALLY in the RunPod console."; fi
  fi
  exit "$1"
}
cd "$BASE" || { echo "no $BASE"; exit 1; }
say "run_c5 BASE=$BASE LOCAL=$LOCAL pod=${RUNPOD_POD_ID:-?}"
python -c "import transformers, peft, httpx" 2>/dev/null || fail "python packages missing: run bash runpod/setup_c5.sh first"
command -v ollama >/dev/null || fail "ollama missing: run bash runpod/setup_c5.sh first"
[ "$(sha256sum runs/lora_v5_s42/adapter/adapter_model.safetensors | cut -d' ' -f1)" = "$ADAPTER_SHA" ] || fail "adapter sha mismatch"
[ "$(sha256sum data_v5/data_v5_hashes.json | cut -d' ' -f1)" = "$HASHES_SHA" ] || fail "data_v5_hashes.json sha mismatch"
free -g | head -2; df -h / "$BASE" | tail -2

Q4="$BASE/export/gguf/blade-qwen-lora-v5-s42-Q4_K_M.gguf"
if [ -f "$Q4" ] && [ -f "$BASE/export/gguf/SHA256SUMS_gguf_s42" ] && (cd "$BASE/export/gguf" && sha256sum -c --quiet SHA256SUMS_gguf_s42); then
  say "a) GGUF already present and verified, skipping merge"
else
  say "a) GGUF merge (work dir on container disk: $LOCAL/work)"
  WORK_DIR="$LOCAL/work" LLAMA_SRC="$LOCAL/llama.cpp" DROP_HF_CACHE=1 bash runpod/merge_gguf_v5.sh 42 || fail "merge_gguf_v5.sh"
  say "a) GGUF ok"
fi

say "ollama serve (models in $OLLAMA_MODELS)"
if ! curl -fs http://127.0.0.1:11434/api/tags >/dev/null; then
  nohup ollama serve > "$BASE/export/ollama_serve.log" 2>&1 &
  for i in $(seq 1 60); do curl -fs http://127.0.0.1:11434/api/tags >/dev/null && break; sleep 2; done
  curl -fs http://127.0.0.1:11434/api/tags >/dev/null || fail "ollama serve did not start (export/ollama_serve.log)"
fi
cp Modelfile.blade-qwen-lora-v5 "$BASE/export/gguf/" && (cd "$BASE/export/gguf" && ollama create blade-qwen-lora-v5 -f Modelfile.blade-qwen-lora-v5) || fail "ollama create"
ollama show blade-qwen-lora-v5 --modelfile | head -5

say "b) test_v30 oas_code with the GGUF (equivalence input; nothing tuned on it)"
python eval_ollama_v5.py --split test --data-dir data_v5 --check-template 3 --tokenizer runs/lora_v5_s42/adapter \
  --out export/gguf_eval/predictions_oas_code_lora_v5_s42_gguf_q4km.jsonl 2>&1 | tee export/gguf_eval/template_check.log | grep -v '^[0-9]*/[0-9]* ' || true
[ -s export/gguf_eval/predictions_oas_code_lora_v5_s42_gguf_q4km.jsonl ] || fail "test predictions missing"
say "c) val_sft_v5 with the GGUF (threshold input only)"
python eval_ollama_v5.py --split val --data-dir data_v5 --out export/gguf_eval/val_predictions_lora_v5_s42_gguf_q4km.jsonl | grep -v '^[0-9]*/[0-9]* ' || true
[ -s export/gguf_eval/val_predictions_lora_v5_s42_gguf_q4km.jsonl ] || fail "val predictions missing"
ollama ps
finish 0
