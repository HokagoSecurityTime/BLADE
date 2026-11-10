#!/usr/bin/env bash
# S5: LoRA v6a (prompt v3.1, output order evidence_fields/rationale/label/confidence, max_seq_len 6144, label-token probability) — RunPod H100 80GB.
# One pass: 0 hashes -> 1 environment (setup.sh: unsloth) -> 2 preflight (base load + generate(output_scores)) -> 3 seeds 42, 43, 44 in turn
# (train + test_v30/test_v5 predictions, resumable) -> per-seed pack (+ optional RETRIEVE_CMD) -> 4 final tar -> pod stop (STOP_POD=1).
# Start detached:   tmux new -d -s v6 "bash /workspace/blade_lora_v3/runpod/run_v6.sh"      watch: tail -f /workspace/blade_lora_v3/runs/run_v6.log
# Re-running resumes: a finished seed (adapter + 4 complete prediction files) is skipped, an interrupted one resumes from its last checkpoint / appended rows.
# A failing seed STOPs the script (pack what exists, stop the pod) instead of running the next seeds into the same failure. No commit, no test_v6.
set -uo pipefail
BASE=${BASE:-/workspace/blade_lora_v3}; SEEDS=${SEEDS:-"42 43 44"}; STOP_POD=${STOP_POD:-1}; STOP_DELAY_MIN=${STOP_DELAY_MIN:-0}; SKIP_SETUP=${SKIP_SETUP:-0}
RETRIEVE_CMD=${RETRIEVE_CMD:-}      # optional, run after every pack with the archive path as $1 (e.g. an scp/rclone command); empty = just leave files in $BASE/export
export HF_HOME=${HF_HOME:-/workspace/hf}
HASH_V6A=c079b9f5735242b4bf2a340dce530236e6d5a2da806dad7c0b7e0d42ebaae288      # data_v6a/data_v6a_hashes.json (run_train_v6.py DATASETS sha)
HASH_T5=57fd384f46e89e905209e627a7ff7fb9f312e22a7bed222639e91a80bd05fccd       # data_v6a/test_v5_manifest.json (TESTV5 gate)
OUT=$BASE/export; mkdir -p "$BASE/runs" "$OUT"; LOG=$BASE/runs/run_v6.log
log(){ echo "=== $(date -Is) $*" | tee -a "$LOG"; }
stop_pod(){ if [ "$STOP_POD" = "1" ]; then [ "$STOP_DELAY_MIN" != "0" ] && { log "waiting $STOP_DELAY_MIN min before stopping"; sleep "$((STOP_DELAY_MIN * 60))"; }
  if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then log "POD STOP REQUESTED (runpodctl stop pod $RUNPOD_POD_ID)"; runpodctl stop pod "$RUNPOD_POD_ID" 2>&1 | tee -a "$LOG"; else log "WARNING: runpodctl/RUNPOD_POD_ID missing - stop the pod from the console"; fi
  else log "STOP_POD=0: pod left running"; fi; }
pack(){ # $1 = seed: results (config/env/eval/logs + run_v6.log) and the adapter, each with a hash line; then RETRIEVE_CMD if set
  local s=$1 r=lora_v6a_s$1 f
  if [ -d "$BASE/runs/$r" ]; then
    tar czf "$OUT/blade_v6a_s${s}_results.tar.gz" -C "$BASE/runs" $(cd "$BASE/runs" && ls -d $r/config.json $r/env.json $r/eval $r/logs 2>/dev/null) run_v6.log
    [ -f "$BASE/runs/$r/adapter/adapter_model.safetensors" ] && tar czf "$OUT/blade_v6a_s${s}_adapter.tar.gz" -C "$BASE/runs" "$r/adapter"
    (cd "$OUT" && sha256sum blade_v6a_s${s}_*.tar.gz | tee -a SHA256SUMS_blade_v6a | tee -a "$LOG")
    for f in "$OUT"/blade_v6a_s${s}_*.tar.gz; do [ -n "$RETRIEVE_CMD" ] && { $RETRIEVE_CMD "$f" 2>&1 | tee -a "$LOG" || log "retrieve failed for $f (archive kept in $OUT)"; }; done
  fi; }
stop_run(){ log "STOP: $1"; for s in $SEEDS; do pack "$s"; done; stop_pod; exit 1; }
cd "$BASE" || { echo "base dir not found: $BASE"; exit 1; }
log "run_v6 start pod=${RUNPOD_POD_ID:-?} BASE=$BASE SEEDS=[$SEEDS] STOP_POD=$STOP_POD"
if [ "$STOP_POD" = "1" ]; then if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then log "auto-stop armed: runpodctl stop pod $RUNPOD_POD_ID will run when this script ends"; else log "WARNING: runpodctl or RUNPOD_POD_ID missing - the pod will NOT stop itself"; fi; fi
log "0/4 hashes"
[ "$(sha256sum data_v6a/data_v6a_hashes.json | cut -d' ' -f1)" = "$HASH_V6A" ] || stop_run "data_v6a_hashes.json hash mismatch"
[ "$(sha256sum data_v6a/test_v5_manifest.json | cut -d' ' -f1)" = "$HASH_T5" ] || stop_run "test_v5_manifest.json hash mismatch"
python - <<'PY' 2>&1 | tee -a "$LOG" || stop_run "data_v6a file hash mismatch"
import hashlib, json
h = json.load(open('data_v6a/data_v6a_hashes.json')); bad = {n: v for n, v in h['generated'].items() if hashlib.sha256(open('data_v6a/' + n, 'rb').read()).hexdigest() != v}
m = json.load(open('data_v6a/test_v5_manifest.json')); t5 = hashlib.sha256(open('data_v6a/test_v5_inputs.jsonl', 'rb').read()).hexdigest() == m['sha256']['training/lora/data_v5/test_v5_inputs.jsonl']
print('generated files ok:', not bad, bad, '| test_v5_inputs vs manifest:', t5); assert not bad and t5
PY
log "1/4 environment"; nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | tee -a "$LOG"
if [ "$SKIP_SETUP" != "1" ]; then bash runpod/setup.sh 2>&1 | tail -5 | tee -a "$LOG" || stop_run "setup.sh failed"; fi
python -c "import unsloth, trl, peft, transformers, torch; print('unsloth', unsloth.__version__, 'trl', trl.__version__, 'peft', peft.__version__, 'transformers', transformers.__version__, 'torch', torch.__version__)" 2>&1 | tee -a "$LOG" || stop_run "imports failed (unsloth/trl/peft)"
log "2/4 preflight (base model load, generate with output_scores, label tokenizer checks)"
python runpod/run_train_v6.py --data v6a --seed 42 --base "$BASE" --preflight 2>&1 | tail -15 | tee -a "$LOG"
grep -q "preflight done" "$BASE/runs/lora_v6a_s42/logs/run.log" || stop_run "preflight failed (see runs/lora_v6a_s42/logs/run.log)"
log "3/4 seeds"
for s in $SEEDS; do
  r=$BASE/runs/lora_v6a_s$s
  if [ -f "$r/adapter/adapter_model.safetensors" ] && [ "$(ls $r/eval/*.jsonl 2>/dev/null | wc -l)" = "4" ] && grep -q "INFO done lora_v6a_s${s}_final" "$r/logs/run.log" 2>/dev/null; then log "seed $s already complete: skip"; continue; fi
  log "seed $s: train + eval (resumable)"
  if python runpod/run_train_v6.py --data v6a --seed "$s" --base "$BASE" 2>&1 | grep -v "it/s\]" | tee -a "$LOG"; then log "seed $s ok"; else log "seed $s FAILED"; pack "$s"; stop_run "seed $s failed (see runs/lora_v6a_s$s/logs/run.log)"; fi
  grep -q "INFO done lora_v6a_s${s}_final" "$r/logs/run.log" || { pack "$s"; stop_run "seed $s did not finish"; }
  pack "$s"
done
log "4/4 final archive"
tar czf "$OUT/blade_v6a_all_results.tar.gz" -C "$BASE/runs" $(cd "$BASE/runs" && ls -d lora_v6a_s*/config.json lora_v6a_s*/env.json lora_v6a_s*/eval lora_v6a_s*/logs 2>/dev/null) run_v6.log
(cd "$OUT" && sha256sum blade_v6a_all_results.tar.gz | tee -a SHA256SUMS_blade_v6a | tee -a "$LOG")
[ -n "$RETRIEVE_CMD" ] && { $RETRIEVE_CMD "$OUT/blade_v6a_all_results.tar.gz" 2>&1 | tee -a "$LOG" || true; }
ls -lh "$OUT" | tee -a "$LOG"
log "ALL DONE — results $OUT/blade_v6a_s{42,43,44}_results.tar.gz (+ _adapter.tar.gz), $OUT/blade_v6a_all_results.tar.gz, $OUT/SHA256SUMS_blade_v6a"
stop_pod
