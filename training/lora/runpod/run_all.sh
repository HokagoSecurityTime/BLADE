#!/usr/bin/env bash
# Runs the data-v4 experiment (reports/eval/lora_v4 plan) one run after another:
#   train+eval: v2 seed 43, 44 (RunPod baseline, with the existing v2 s42 = 3 seeds) -> v4 seed 42, 43, 44
#   eval only : v2 s42, v3b s42/43/44 (existing final adapters: adds the test_v31_supp predictions) -> base model (no adapter)
# Items are data:seed, data:seed:eval (--eval-only, never trains) or data:seed:v5test (--eval-only --jobs v5test: ONLY the test_v5 predictions; test_v30/supp are
# never recomputed for base/v4 — C-4 evaluation scope, user decision 2026-10-31: v2/v3b not re-inferred, base/v4 keep their exported test_v30/supp predictions). Override with RUNS="...".
# Start it detached so a closed browser/SSH does not stop it:
#     tmux new -d -s blade "bash /workspace/blade_lora_v3/runpod/run_all.sh"
#     tmux attach -t blade        # watch; Ctrl-b d to detach again
# Each run writes <BASE>/runs/<run>/logs/run.log; this loop also appends to <BASE>/runs/run_all.log.
# Re-running resumes: finished runs are skipped (final adapter + prediction files present), an interrupted one resumes from its last checkpoint.
# When every run has ended (ok or failed) the results are exported (export_results.sh) and the pod is stopped with runpodctl (STOP_POD=0 keeps it running).
# The last line of run_all.log always says whether the pod was stopped.
# Task B (output stabilisation, reports/eval/stable_decoding): DECODING=stable re-evaluates existing adapters + base with repetition_penalty 1.1 and
# JSON-schema constrained decoding (run_train.py DECODING). Never trains. Default RUNS then = the 10 models of the LoRA v4 report; log = run_all_stable.log.
set -uo pipefail
BASE=${BASE:-/workspace/blade_lora_v3}
DECODING=${DECODING:-default}
if [ "$DECODING" = "default" ]; then
  RUNS=${RUNS:-"v2:43 v2:44 v4:42 v4:43 v4:44 v2:42:eval v3b:42:eval v3b:43:eval v3b:44:eval base:0"}
  LOG="$BASE/runs/run_all.log"
  case " $RUNS " in *" v5:"*) dn=blade_v5 ;; *) dn=blade_v4 ;; esac   # task C-4 (LoRA v5) exports as blade_v5_*
  export EXPORT_NAME=${EXPORT_NAME:-$dn} EXPORT_ADAPTERS=${EXPORT_ADAPTERS:-1}
else
  RUNS=${RUNS:-"base:0:eval v2:42:eval v2:43:eval v2:44:eval v3b:42:eval v3b:43:eval v3b:44:eval v4:42:eval v4:43:eval v4:44:eval"}
  LOG="$BASE/runs/run_all_$DECODING.log"; export EXPORT_NAME=${EXPORT_NAME:-blade_$DECODING} EXPORT_ADAPTERS=${EXPORT_ADAPTERS:-0}
fi
STOP_POD=${STOP_POD:-1}
# Task C-4: after every run has ended, merge the seed-GGUF_SEED LoRA v5 final adapter into fp16 and quantize to GGUF Q4_K_M (merge_gguf_v5.sh) before export/stop.
# Default: seed 42 when "v5:42" (a training item) is in RUNS; GGUF_SEED="" disables. A GGUF failure is logged and never blocks export or the pod stop.
GGUF_SEED=${GGUF_SEED-$(case " $RUNS " in *" v5:42 "*) echo 42 ;; esac)}
STOP_DELAY_MIN=${STOP_DELAY_MIN:-0}   # optional grace period between export and stop (minutes) to download export/ from a pod without a network volume
export HF_HOME=${HF_HOME:-/workspace/hf}
mkdir -p "$BASE/runs"
echo "=== $(date -Is) run_all decoding=$DECODING RUNS=[$RUNS] STOP_POD=$STOP_POD pod=${RUNPOD_POD_ID:-?}" | tee -a "$LOG"
for item in $RUNS; do
  IFS=: read -r d s mode <<<"$item"
  extra=""; [ "${mode:-}" = "eval" ] && extra="--eval-only"; [ "${mode:-}" = "v5test" ] && extra="--eval-only --jobs v5test"
  echo "=== $(date -Is) start data=$d seed=$s $extra decoding=$DECODING" | tee -a "$LOG"
  if python "$BASE/runpod/run_train.py" --data "$d" --seed "$s" --base "$BASE" --decoding "$DECODING" $extra 2>&1 | tee -a "$LOG"; then
    echo "=== $(date -Is) ok data=$d seed=$s" | tee -a "$LOG"
  else
    echo "=== $(date -Is) FAILED data=$d seed=$s (see its logs/run*.log); continuing" | tee -a "$LOG"
  fi
done
echo "=== $(date -Is) all runs ended" | tee -a "$LOG"
if [ -n "${GGUF_SEED:-}" ]; then
  echo "=== $(date -Is) GGUF: merging lora_v5_s$GGUF_SEED into fp16 + Q4_K_M (merge_gguf_v5.sh)" | tee -a "$LOG"
  if bash "$BASE/runpod/merge_gguf_v5.sh" "$GGUF_SEED" >>"$LOG" 2>&1; then
    echo "=== $(date -Is) GGUF ok: $BASE/export/gguf" | tee -a "$LOG"
  else
    echo "=== $(date -Is) GGUF FAILED (see $BASE/export/gguf/merge.log and above); continuing with export" | tee -a "$LOG"
  fi
fi
bash "$BASE/runpod/export_results.sh" >>"$LOG" 2>&1 && echo "=== $(date -Is) exported to $BASE/export ($EXPORT_NAME)" | tee -a "$LOG" || echo "=== $(date -Is) export FAILED (run export_results.sh by hand)" | tee -a "$LOG"
if [ "$STOP_POD" = "1" ]; then
  if [ "$STOP_DELAY_MIN" != "0" ]; then
    echo "=== $(date -Is) export done; waiting $STOP_DELAY_MIN min before stopping the pod (download $BASE/export now if this pod has no network volume)" | tee -a "$LOG"
    sleep "$((STOP_DELAY_MIN * 60))"
  fi
  if command -v runpodctl >/dev/null 2>&1 && [ -n "${RUNPOD_POD_ID:-}" ]; then
    echo "=== $(date -Is) stopping pod $RUNPOD_POD_ID" | tee -a "$LOG"
    if runpodctl stop pod "$RUNPOD_POD_ID" >>"$LOG" 2>&1; then
      echo "=== $(date -Is) POD STOP REQUESTED ($RUNPOD_POD_ID). Confirm in the RunPod console that it is stopped." | tee -a "$LOG"
    else
      echo "=== $(date -Is) POD NOT STOPPED: runpodctl stop failed. STOP THE POD MANUALLY in the RunPod console (billing continues)." | tee -a "$LOG"
    fi
  else
    echo "=== $(date -Is) POD NOT STOPPED: runpodctl or RUNPOD_POD_ID not available. STOP THE POD MANUALLY in the RunPod console (billing continues)." | tee -a "$LOG"
  fi
else
  echo "=== $(date -Is) POD NOT STOPPED: STOP_POD=0. Stop it manually when done." | tee -a "$LOG"
fi
exit 0
