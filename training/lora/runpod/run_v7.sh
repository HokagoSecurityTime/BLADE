#!/usr/bin/env bash
# data-v7: LoRA v7 = LoRA v5 recipe on data-v7 — RunPod H100/A100 80GB, auto-stop.
# 0 hashes -> 1 environment (setup.sh) -> 2 preflight -> 3 seed 42 -> 4 seed 43 -> 5 seed 44 (train + test_v30 predictions; pack each) -> 6 final tar -> pod stop.
# Evaluation here is test_v30 ONLY (test_v31_supp / test_v5 are training data in data-v7; test_v6 is run later with --jobs v6test after its freeze).
# Start detached:   tmux new -d -s v7 "bash /workspace/blade_lora_v3/runpod/run_v7.sh"     watch: tail -f /workspace/blade_lora_v3/runs/run_v7.log
# Re-running resumes (finished seed skipped, interrupted seed resumes from its checkpoint / appended rows). A failing seed STOPs (pack + pod stop). No commit.
set -uo pipefail
BASE=${BASE:-/workspace/blade_lora_v3}; SEEDS=${SEEDS:-"42 43 44"}; STOP_POD=${STOP_POD:-1}; STOP_DELAY_MIN=${STOP_DELAY_MIN:-0}; SKIP_SETUP=${SKIP_SETUP:-0}
RETRIEVE_CMD=${RETRIEVE_CMD:-}
export HF_HOME=${HF_HOME:-/workspace/hf}
HASH_V7=bd33f1bcf0f68ab5fe5b96195c0da3cf6affbb3486fb85bef542b3f77e88ba73       # data_v7/data_v7_hashes.json (run_train_v7.py DATASETS sha, data-v7 freeze)
HASH_PROMPT=d0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef   # policy_label_v3.0.1.md (frozen)
OUT=$BASE/export; mkdir -p "$BASE/runs" "$OUT"; LOG=$BASE/runs/run_v7.log
log(){ echo "=== $(date -Is) $*" | tee -a "$LOG"; }
stop_pod(){ if [ "$STOP_POD" = "1" ]; then [ "$STOP_DELAY_MIN" != "0" ] && { log "waiting $STOP_DELAY_MIN min before stopping"; sleep "$((STOP_DELAY_MIN * 60))"; }
  if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then log "POD STOP REQUESTED (runpodctl stop pod $RUNPOD_POD_ID)"; runpodctl stop pod "$RUNPOD_POD_ID" 2>&1 | tee -a "$LOG"; else log "WARNING: runpodctl/RUNPOD_POD_ID missing - stop the pod from the console"; fi
  else log "STOP_POD=0: pod left running"; fi; }
pack(){ local r=$1 f
  if [ -d "$BASE/runs/$r" ]; then
    tar czf "$OUT/blade_v7_${r}_results.tar.gz" -C "$BASE/runs" $(cd "$BASE/runs" && ls -d $r/config.json $r/env.json $r/eval $r/logs 2>/dev/null) run_v7.log
    [ -f "$BASE/runs/$r/adapter/adapter_model.safetensors" ] && tar czf "$OUT/blade_v7_${r}_adapter.tar.gz" -C "$BASE/runs" "$r/adapter"
    (cd "$OUT" && sha256sum blade_v7_${r}_*.tar.gz | tee -a SHA256SUMS_blade_v7 | tee -a "$LOG")
    for f in "$OUT"/blade_v7_${r}_*.tar.gz; do [ -n "$RETRIEVE_CMD" ] && { $RETRIEVE_CMD "$f" 2>&1 | tee -a "$LOG" || log "retrieve failed for $f"; }; done
  fi; }
final_tar(){ log "final archive"
  tar czf "$OUT/blade_v7_all_results.tar.gz" -C "$BASE/runs" $(cd "$BASE/runs" && ls -d lora_v7_s*/config.json lora_v7_s*/env.json lora_v7_s*/eval lora_v7_s*/logs 2>/dev/null) run_v7.log
  (cd "$OUT" && sha256sum blade_v7_all_results.tar.gz | tee -a SHA256SUMS_blade_v7 | tee -a "$LOG"); [ -n "$RETRIEVE_CMD" ] && { $RETRIEVE_CMD "$OUT/blade_v7_all_results.tar.gz" 2>&1 | tee -a "$LOG" || true; }; ls -lh "$OUT" | tee -a "$LOG"; }
stop_run(){ log "STOP: $1"; for s in $SEEDS; do pack "lora_v7_s$s"; done; final_tar; stop_pod; exit 1; }
seed_done(){ local r=$BASE/runs/lora_v7_s$1; [ -f "$r/adapter/adapter_model.safetensors" ] && [ "$(ls $r/eval/predictions_*.jsonl 2>/dev/null | wc -l)" = "2" ] && grep -q "INFO done lora_v7_s${1}_final" "$r/logs/run.log" 2>/dev/null; }
run_seed(){ local s=$1
  if seed_done "$s"; then log "seed $s already complete: skip"; return 0; fi
  log "seed $s: train + eval (resumable)"
  if python runpod/run_train_v7.py --data v7 --seed "$s" --base "$BASE" 2>&1 | grep -v "it/s\]" | tee -a "$LOG"; then log "seed $s ok"; else log "seed $s FAILED"; stop_run "seed $s failed (see runs/lora_v7_s$s/logs/run.log)"; fi
  seed_done "$s" || stop_run "seed $s did not finish"; pack "lora_v7_s$s"; }
cd "$BASE" || { echo "base dir not found: $BASE"; exit 1; }
log "run_v7 start pod=${RUNPOD_POD_ID:-?} BASE=$BASE SEEDS=[$SEEDS] STOP_POD=$STOP_POD"
if [ "$STOP_POD" = "1" ]; then if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then log "auto-stop armed"; else log "WARNING: runpodctl or RUNPOD_POD_ID missing - the pod will NOT stop itself"; fi; fi
log "0/6 hashes"
[ "$(sha256sum data_v7/data_v7_hashes.json | cut -d' ' -f1)" = "$HASH_V7" ] || stop_run "data_v7_hashes.json hash mismatch"
[ "$(sha256sum data_v7/policy_label_v3.0.1.md | cut -d' ' -f1)" = "$HASH_PROMPT" ] || stop_run "policy_label_v3.0.1.md hash mismatch"
[ -e data_v7/test_v5_inputs.jsonl ] || [ -e data_v7/test_v31_supp_inputs.jsonl ] && stop_run "test_v5/test_v31_supp inputs must not be in data_v7 (training data)"
python - <<'PY' 2>&1 | tee -a "$LOG" || stop_run "data_v7 file hash mismatch"
import hashlib, json
h = json.load(open('data_v7/data_v7_hashes.json')); bad = {n: v for n, v in h['generated'].items() if hashlib.sha256(open('data_v7/' + n, 'rb').read()).hexdigest() != v}
print('generated files ok:', not bad, bad); assert not bad
PY
log "1/6 environment"; nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | tee -a "$LOG"; df -h "$BASE" 2>/dev/null | tee -a "$LOG"
if [ "$SKIP_SETUP" != "1" ]; then bash runpod/setup.sh 2>&1 | tail -5 | tee -a "$LOG" || stop_run "setup.sh failed"; fi
python -c "import unsloth, trl, peft, transformers, torch; print('unsloth', unsloth.__version__, 'trl', trl.__version__, 'peft', peft.__version__, 'transformers', transformers.__version__, 'torch', torch.__version__)" 2>&1 | tee -a "$LOG" || stop_run "imports failed"
FIRST=${SEEDS%% *}; log "2/6 preflight"
python runpod/run_train_v7.py --data v7 --seed "$FIRST" --base "$BASE" --preflight 2>&1 | tail -8 | tee -a "$LOG"
grep -q "preflight done" "$BASE/runs/lora_v7_s$FIRST/logs/run.log" || stop_run "preflight failed"
n=3; for s in $SEEDS; do log "$n/6 seed $s"; run_seed "$s"; n=$((n + 1)); done
log "6/6 final archive"; final_tar
log "ALL DONE — results $OUT/blade_v7_lora_v7_s<seed>_results.tar.gz (+ _adapter.tar.gz), $OUT/blade_v7_all_results.tar.gz, $OUT/SHA256SUMS_blade_v7"
stop_pod
