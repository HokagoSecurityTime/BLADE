#!/usr/bin/env bash
# S9-base (reference only, after the S9 verdict): base unsloth/Qwen2.5-7B-Instruct-bnb-4bit WITHOUT adapter on the frozen test_v6 (289), prompt v3.0.1, greedy, same decoding as S9.
# Same pod / libraries as S9. Single run (no training, so no seed repetition): --data base --seed 0 --eval-only --jobs v6test (oas + oas_code). Then pack + pod stop.
# Requires in $BASE: data_v7/ (incl. test_v6_inputs.jsonl + test_v6_manifest.json), runpod/run_train_v7.py (this bundle's version: DATASETS 'base').
# Start detached:   tmux new -d -s s9b "bash $BASE/runpod/run_s9_base.sh"     watch: tail -f $BASE/runs/run_s9_base.log
set -uo pipefail
if [ -z "${BASE:-}" ]; then if [ -d /workspace/blade_lora_v3 ]; then BASE=/workspace/blade_lora_v3; elif [ -d /workspace-2/blade_lora_v3 ]; then BASE=/workspace-2/blade_lora_v3; else echo "set BASE"; exit 1; fi; fi
STOP_POD=${STOP_POD:-1}; STOP_DELAY_MIN=${STOP_DELAY_MIN:-0}; SKIP_SETUP=${SKIP_SETUP:-1}; RETRIEVE_CMD=${RETRIEVE_CMD:-}
if [ -z "${HF_HOME:-}" ]; then if [ ! -d /workspace/hf ] && [ -d /workspace-2/hf ]; then export HF_HOME=/workspace-2/hf; else export HF_HOME=/workspace/hf; fi; else export HF_HOME; fi; export BLADE_TESTV6_STAGE=S9
HASH_V7=bd33f1bcf0f68ab5fe5b96195c0da3cf6affbb3486fb85bef542b3f77e88ba73
HASH_PROMPT=d0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef
HASH_TESTV6_MANIFEST=a9ca4fca05ee3e59226411c08c9f102440d5f36b2d4b45dc870bd74e346f3edc
HASH_TESTV6_INPUTS=33d1aecdbd1a685416523eddf73722e105c2c761154a6bf95403fe1431435741
RUN=base_qwen7b_s9; OUT=$BASE/export; mkdir -p "$BASE/runs" "$OUT"; LOG=$BASE/runs/run_s9_base.log
log(){ echo "=== $(date -Is) $*" | tee -a "$LOG"; }
stop_pod(){ if [ "$STOP_POD" = "1" ]; then [ "$STOP_DELAY_MIN" != "0" ] && { log "waiting $STOP_DELAY_MIN min before stopping"; sleep "$((STOP_DELAY_MIN * 60))"; }
  if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then log "POD STOP REQUESTED (runpodctl stop pod $RUNPOD_POD_ID)"; runpodctl stop pod "$RUNPOD_POD_ID" 2>&1 | tee -a "$LOG"; else log "WARNING: runpodctl/RUNPOD_POD_ID missing - stop the pod from the console"; fi
  else log "STOP_POD=0: pod left running"; fi; }
pack(){ if [ -d "$BASE/runs/$RUN" ]; then
    tar czf "$OUT/blade_s9_${RUN}_v6test.tar.gz" -C "$BASE/runs" $(cd "$BASE/runs" && ls -d $RUN/config.json $RUN/env.json $RUN/eval/v6test_* $RUN/logs/run.log 2>/dev/null) run_s9_base.log
    (cd "$OUT" && sha256sum "blade_s9_${RUN}_v6test.tar.gz" | tee -a SHA256SUMS_s9_base | tee -a "$LOG"); [ -n "$RETRIEVE_CMD" ] && { $RETRIEVE_CMD "$OUT/blade_s9_${RUN}_v6test.tar.gz" 2>&1 | tee -a "$LOG" || true; }; ls -lh "$OUT" | tee -a "$LOG"; fi; }
stop_run(){ log "STOP: $1"; pack; stop_pod; exit 1; }
run_done(){ local r=$BASE/runs/$RUN; [ "$(ls $r/eval/v6test_predictions_*.jsonl 2>/dev/null | wc -l)" = "2" ] && grep -q "INFO done $RUN" "$r/logs/run.log" 2>/dev/null && [ "$(wc -l < $r/eval/v6test_predictions_oas_code_$RUN.jsonl)" = "289" ] && [ "$(wc -l < $r/eval/v6test_predictions_oas_$RUN.jsonl)" = "289" ]; }
cd "$BASE" || { echo "base dir not found: $BASE"; exit 1; }
log "run_s9_base start pod=${RUNPOD_POD_ID:-?} BASE=$BASE STOP_POD=$STOP_POD"
if [ "$STOP_POD" = "1" ]; then if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then log "auto-stop armed"; else log "WARNING: runpodctl or RUNPOD_POD_ID missing - the pod will NOT stop itself"; fi; fi
log "0/3 hashes"
[ "$(sha256sum data_v7/data_v7_hashes.json | cut -d' ' -f1)" = "$HASH_V7" ] || stop_run "data_v7_hashes.json hash mismatch"
[ "$(sha256sum data_v7/policy_label_v3.0.1.md | cut -d' ' -f1)" = "$HASH_PROMPT" ] || stop_run "policy_label_v3.0.1.md hash mismatch"
[ "$(sha256sum data_v7/test_v6_manifest.json | cut -d' ' -f1)" = "$HASH_TESTV6_MANIFEST" ] || stop_run "test_v6_manifest.json missing or differs from the frozen one"
[ "$(sha256sum data_v7/test_v6_inputs.jsonl | cut -d' ' -f1)" = "$HASH_TESTV6_INPUTS" ] || stop_run "test_v6_inputs.jsonl missing or differs from the frozen one"
grep -q "sha='$HASH_TESTV6_MANIFEST'" runpod/run_train_v7.py || stop_run "run_train_v7.py TESTV6 sha not set"
grep -q "'base': dict(" runpod/run_train_v7.py || stop_run "run_train_v7.py has no 'base' dataset entry (old file; extract the S9-base bundle)"
[ -e data_v7/test_v5_inputs.jsonl ] || [ -e data_v7/test_v31_supp_inputs.jsonl ] && stop_run "test_v5/test_v31_supp inputs must not be in data_v7"
log "1/3 environment"; nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | tee -a "$LOG"; df -h "$BASE" 2>/dev/null | tee -a "$LOG"
if [ "$SKIP_SETUP" != "1" ]; then bash runpod/setup.sh 2>&1 | tail -5 | tee -a "$LOG" || stop_run "setup.sh failed"; fi
python -c "import unsloth, trl, peft, transformers, torch; print('unsloth', unsloth.__version__, 'trl', trl.__version__, 'peft', peft.__version__, 'transformers', transformers.__version__, 'torch', torch.__version__)" 2>&1 | tee -a "$LOG" || { log "imports failed: running setup.sh"; bash runpod/setup.sh 2>&1 | tail -5 | tee -a "$LOG" || stop_run "setup.sh failed"; python -c "import unsloth, trl, peft, transformers, torch" || stop_run "imports failed after setup"; }
log "2/3 inference (base, no adapter)"
if run_done; then log "$RUN already complete: skip"; else
  if python runpod/run_train_v7.py --data base --seed 0 --base "$BASE" --eval-only --jobs v6test 2>&1 | grep -v "it/s\]" | tee -a "$LOG"; then log "$RUN ok"; else stop_run "$RUN failed (see runs/$RUN/logs/run.log)"; fi
  run_done || stop_run "$RUN did not finish (289 rows x 2 conditions expected)"; fi
log "3/3 pack"; pack
log "ALL DONE — $OUT/blade_s9_${RUN}_v6test.tar.gz, $OUT/SHA256SUMS_s9_base"
stop_pod
