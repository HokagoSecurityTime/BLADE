#!/usr/bin/env bash
# S8: LoRA v6c = LoRA v5 recipe with the base model 7B -> 14B (unsloth/Qwen2.5-14B-Instruct-bnb-4bit) — RunPod H100 80GB, auto-stop.
# One pass (AGENTS.md "작업 S8", user decision 2026-11-04):
#   0 hashes -> 1 environment (setup.sh) -> 2 preflight (14B load + generate) -> 3 seed 42 train + 6 prediction jobs -> pack s42 -> EARLY GATE
#   (v6c s42 test_v5 oas_code macro-F1 <= v5 s42 0.6661 -> STOP: no s43/s44, no base zero-shot, final tar, pod stop)
#   -> 4 seed 43 -> 5 seed 44 (pack each) -> 6 base 14B zero-shot (eval only, last) -> 7 final tar -> pod stop (STOP_POD=1).
# Start detached:   tmux new -d -s v6c "bash /workspace/blade_lora_v3/runpod/run_v6c.sh"     watch: tail -f /workspace/blade_lora_v3/runs/run_v6c.log
# Re-running resumes: a finished seed (adapter + 6 complete prediction files + "done" line) is skipped, an interrupted one resumes from its last checkpoint /
# appended prediction rows. A failing seed STOPs the script (pack what exists, stop the pod). No commit, no test_v6.
set -uo pipefail
BASE=${BASE:-/workspace/blade_lora_v3}; SEEDS=${SEEDS:-"42 43 44"}; STOP_POD=${STOP_POD:-1}; STOP_DELAY_MIN=${STOP_DELAY_MIN:-0}; SKIP_SETUP=${SKIP_SETUP:-0}
RUN_BASE14B=${RUN_BASE14B:-1}       # base 14B zero-shot after the last seed (only when the early gate passed)
RETRIEVE_CMD=${RETRIEVE_CMD:-}      # optional, run after every pack with the archive path as $1 (scp/rclone ...); empty = archives stay in $BASE/export
export HF_HOME=${HF_HOME:-/workspace/hf}
HASH_V5=39c302c5fb33d1b1506487678cd15f40cc83ffd59435449522786388554753ac       # data_v5/data_v5_hashes.json (run_train_v6c.py DATASETS sha, data-v5 freeze)
HASH_T5=57fd384f46e89e905209e627a7ff7fb9f312e22a7bed222639e91a80bd05fccd       # data_v5/test_v5_manifest.json (TESTV5 gate)
HASH_PROMPT=d0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef   # policy_label_v3.0.1.md (frozen)
OUT=$BASE/export; mkdir -p "$BASE/runs" "$OUT"; LOG=$BASE/runs/run_v6c.log; FIRST=${SEEDS%% *}
log(){ echo "=== $(date -Is) $*" | tee -a "$LOG"; }
stop_pod(){ if [ "$STOP_POD" = "1" ]; then [ "$STOP_DELAY_MIN" != "0" ] && { log "waiting $STOP_DELAY_MIN min before stopping"; sleep "$((STOP_DELAY_MIN * 60))"; }
  if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then log "POD STOP REQUESTED (runpodctl stop pod $RUNPOD_POD_ID)"; runpodctl stop pod "$RUNPOD_POD_ID" 2>&1 | tee -a "$LOG"; else log "WARNING: runpodctl/RUNPOD_POD_ID missing - stop the pod from the console"; fi
  else log "STOP_POD=0: pod left running"; fi; }
pack(){ # $1 = run dir name (lora_v6c_s42 / base_qwen14b_runpod): results (config/env/eval/logs + run_v6c.log) and the adapter if any, hash lines, then RETRIEVE_CMD
  local r=$1 f
  if [ -d "$BASE/runs/$r" ]; then
    tar czf "$OUT/blade_v6c_${r}_results.tar.gz" -C "$BASE/runs" $(cd "$BASE/runs" && ls -d $r/config.json $r/env.json $r/eval $r/logs 2>/dev/null) run_v6c.log
    [ -f "$BASE/runs/$r/adapter/adapter_model.safetensors" ] && tar czf "$OUT/blade_v6c_${r}_adapter.tar.gz" -C "$BASE/runs" "$r/adapter"
    (cd "$OUT" && sha256sum blade_v6c_${r}_*.tar.gz | tee -a SHA256SUMS_blade_v6c | tee -a "$LOG")
    for f in "$OUT"/blade_v6c_${r}_*.tar.gz; do [ -n "$RETRIEVE_CMD" ] && { $RETRIEVE_CMD "$f" 2>&1 | tee -a "$LOG" || log "retrieve failed for $f (archive kept in $OUT)"; }; done
  fi; }
final_tar(){ log "final archive"
  tar czf "$OUT/blade_v6c_all_results.tar.gz" -C "$BASE/runs" $(cd "$BASE/runs" && ls -d lora_v6c_s*/config.json lora_v6c_s*/env.json lora_v6c_s*/eval lora_v6c_s*/logs base_qwen14b_runpod/config.json base_qwen14b_runpod/env.json base_qwen14b_runpod/eval base_qwen14b_runpod/logs 2>/dev/null) run_v6c.log
  (cd "$OUT" && sha256sum blade_v6c_all_results.tar.gz | tee -a SHA256SUMS_blade_v6c | tee -a "$LOG")
  [ -n "$RETRIEVE_CMD" ] && { $RETRIEVE_CMD "$OUT/blade_v6c_all_results.tar.gz" 2>&1 | tee -a "$LOG" || true; }
  ls -lh "$OUT" | tee -a "$LOG"; }
stop_run(){ log "STOP: $1"; for s in $SEEDS; do pack "lora_v6c_s$s"; done; pack base_qwen14b_runpod; final_tar; stop_pod; exit 1; }
seed_done(){ local r=$BASE/runs/lora_v6c_s$1; [ -f "$r/adapter/adapter_model.safetensors" ] && [ "$(ls $r/eval/*.jsonl 2>/dev/null | wc -l)" = "6" ] && grep -q "INFO done lora_v6c_s${1}_final" "$r/logs/run.log" 2>/dev/null; }
run_seed(){ # $1 = seed: train + eval (resumable), pack; STOP on failure
  local s=$1 r=$BASE/runs/lora_v6c_s$1
  if seed_done "$s"; then log "seed $s already complete: skip"; return 0; fi
  log "seed $s: train + eval (resumable)"
  if python runpod/run_train_v6c.py --data v6c --seed "$s" --base "$BASE" 2>&1 | grep -v "it/s\]" | tee -a "$LOG"; then log "seed $s ok"; else log "seed $s FAILED"; stop_run "seed $s failed (see runs/lora_v6c_s$s/logs/run.log)"; fi
  seed_done "$s" || stop_run "seed $s did not finish"
  pack "lora_v6c_s$s"; }
cd "$BASE" || { echo "base dir not found: $BASE"; exit 1; }
log "run_v6c start pod=${RUNPOD_POD_ID:-?} BASE=$BASE SEEDS=[$SEEDS] STOP_POD=$STOP_POD RUN_BASE14B=$RUN_BASE14B"
if [ "$STOP_POD" = "1" ]; then if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then log "auto-stop armed: runpodctl stop pod $RUNPOD_POD_ID will run when this script ends"; else log "WARNING: runpodctl or RUNPOD_POD_ID missing - the pod will NOT stop itself"; fi; fi
log "0/7 hashes"
[ "$(sha256sum data_v5/data_v5_hashes.json | cut -d' ' -f1)" = "$HASH_V5" ] || stop_run "data_v5_hashes.json hash mismatch"
[ "$(sha256sum data_v5/test_v5_manifest.json | cut -d' ' -f1)" = "$HASH_T5" ] || stop_run "test_v5_manifest.json hash mismatch"
[ "$(sha256sum data_v5/policy_label_v3.0.1.md | cut -d' ' -f1)" = "$HASH_PROMPT" ] || stop_run "policy_label_v3.0.1.md hash mismatch"
python - <<'PY' 2>&1 | tee -a "$LOG" || stop_run "data_v5 file hash mismatch"
import hashlib, json
h = json.load(open('data_v5/data_v5_hashes.json')); bad = {n: v for n, v in h['generated'].items() if hashlib.sha256(open('data_v5/' + n, 'rb').read()).hexdigest() != v}
m = json.load(open('data_v5/test_v5_manifest.json')); t5 = hashlib.sha256(open('data_v5/test_v5_inputs.jsonl', 'rb').read()).hexdigest() == m['sha256']['training/lora/data_v5/test_v5_inputs.jsonl']
print('generated files ok:', not bad, bad, '| test_v5_inputs vs manifest:', t5); assert not bad and t5
PY
log "1/7 environment"; nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | tee -a "$LOG"; df -h "$BASE" "$HF_HOME" 2>/dev/null | tee -a "$LOG"
if [ "$SKIP_SETUP" != "1" ]; then bash runpod/setup.sh 2>&1 | tail -5 | tee -a "$LOG" || stop_run "setup.sh failed"; fi
python -c "import unsloth, trl, peft, transformers, torch; print('unsloth', unsloth.__version__, 'trl', trl.__version__, 'peft', peft.__version__, 'transformers', transformers.__version__, 'torch', torch.__version__)" 2>&1 | tee -a "$LOG" || stop_run "imports failed (unsloth/trl/peft)"
log "2/7 preflight (14B base load + generate + memory)"
python runpod/run_train_v6c.py --data v6c --seed "$FIRST" --base "$BASE" --preflight 2>&1 | tail -12 | tee -a "$LOG"
grep -q "preflight done" "$BASE/runs/lora_v6c_s$FIRST/logs/run.log" || stop_run "preflight failed (see runs/lora_v6c_s$FIRST/logs/run.log)"
log "3/7 seed $FIRST"
run_seed "$FIRST"
log "EARLY GATE (pre-registered): v6c s$FIRST test_v5 oas_code macro-F1 vs v5 s42 (0.6661)"
GATE_OUT=$BASE/runs/lora_v6c_s$FIRST/eval/early_gate.json
python runpod/early_gate_v6c.py --pred "runs/lora_v6c_s$FIRST/eval/v5test_predictions_oas_code_lora_v6c_s${FIRST}_final.jsonl" --baseline baseline/v5test_predictions_oas_code_lora_v5_s42_final.jsonl \
       --inputs data_v5/test_v5_inputs.jsonl --out "$GATE_OUT" 2>&1 | tee -a "$LOG"
GATE=$(python -c "import json; print(json.load(open('$GATE_OUT'))['gate'])" 2>/dev/null || echo ERROR)
pack "lora_v6c_s$FIRST"   # re-pack so the archive contains early_gate.json
if [ "$GATE" != "PASS" ]; then log "EARLY GATE $GATE: seeds after $FIRST and the base zero-shot are NOT run (not adopted by the pre-registered rule; ERROR = scoring failed, see log)"; final_tar; log "ALL DONE (early stop)"; stop_pod; exit 0; fi
log "EARLY GATE PASS: continuing with the remaining seeds"
n=4; for s in $SEEDS; do [ "$s" = "$FIRST" ] && continue; log "$n/7 seed $s"; run_seed "$s"; n=$((n + 1)); done
if [ "$RUN_BASE14B" = "1" ]; then
  log "6/7 base 14B zero-shot (eval only, 6 jobs)"
  r=$BASE/runs/base_qwen14b_runpod
  if [ "$(ls $r/eval/*.jsonl 2>/dev/null | wc -l)" = "6" ] && grep -q "INFO done base_qwen14b_runpod" "$r/logs/run.log" 2>/dev/null; then log "base14b already complete: skip"
  elif python runpod/run_train_v6c.py --data base14b --seed 0 --base "$BASE" 2>&1 | grep -v "it/s\]" | tee -a "$LOG"; then log "base14b ok"; else log "base14b FAILED (not part of the adoption decision; continuing to the final archive)"; fi
  pack base_qwen14b_runpod
fi
log "7/7 final archive"; final_tar
log "ALL DONE — results $OUT/blade_v6c_lora_v6c_s<seed>_results.tar.gz (+ _adapter.tar.gz), $OUT/blade_v6c_base_qwen14b_runpod_results.tar.gz, $OUT/blade_v6c_all_results.tar.gz, $OUT/SHA256SUMS_blade_v6c"
stop_pod
