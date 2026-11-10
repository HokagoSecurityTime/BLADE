#!/usr/bin/env bash
# S9: test_v6 (frozen 2026-11-08, 289 rows) inference for LoRA v5 (3 seeds) and LoRA v7 (3 seeds) in the SAME pod / libraries, then pod stop.
# Order: gates -> v5 s42 -> v5 s43 -> v5 s44 -> v7 s42 -> v7 s43 -> v7 s44 (each: --eval-only --jobs v6test, oas + oas_code, resumable row-append) -> pack per run -> final tar -> pod stop.
# Requires in $BASE: data_v7/ (data-v7 files + test_v6_inputs.jsonl + test_v6_manifest.json), runpod/run_train_v7.py (TESTV6 sha set), runs/lora_v7_s4{2,3,4}/adapter (from run_v7.sh),
#                    runs/lora_v5_s4{2,3,4}/adapter (tar -xzf blade_v5_adapters.tar.gz -C $BASE/runs ; SHA-256 db6abe46…). No training, no test_v5 / test_v31_supp. No commit.
# Start detached:   tmux new -d -s s9 "bash $BASE/runpod/run_s9.sh"     watch: tail -f $BASE/runs/run_s9.log
set -uo pipefail
if [ -z "${BASE:-}" ]; then if [ -d /workspace/blade_lora_v3 ]; then BASE=/workspace/blade_lora_v3; elif [ -d /workspace-2/blade_lora_v3 ]; then BASE=/workspace-2/blade_lora_v3; else echo "set BASE"; exit 1; fi; fi
SEEDS=${SEEDS:-"42 43 44"}; MODELS=${MODELS:-"v5 v7"}; STOP_POD=${STOP_POD:-1}; STOP_DELAY_MIN=${STOP_DELAY_MIN:-0}; SKIP_SETUP=${SKIP_SETUP:-1}; RETRIEVE_CMD=${RETRIEVE_CMD:-}
if [ -z "${HF_HOME:-}" ]; then if [ ! -d /workspace/hf ] && [ -d /workspace-2/hf ]; then export HF_HOME=/workspace-2/hf; else export HF_HOME=/workspace/hf; fi; else export HF_HOME; fi; export BLADE_TESTV6_STAGE=S9
HASH_V7=bd33f1bcf0f68ab5fe5b96195c0da3cf6affbb3486fb85bef542b3f77e88ba73          # data_v7/data_v7_hashes.json
HASH_PROMPT=d0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef      # policy_label_v3.0.1.md
HASH_TESTV6_MANIFEST=a9ca4fca05ee3e59226411c08c9f102440d5f36b2d4b45dc870bd74e346f3edc   # test_v6_manifest.json (freeze 2026-11-08) = run_train_v7.py TESTV6 sha
HASH_TESTV6_INPUTS=33d1aecdbd1a685416523eddf73722e105c2c761154a6bf95403fe1431435741     # test_v6_inputs.jsonl (289 rows)
HASH_V5_ADAPTERS=db6abe46438b27795b51a12e875d24678932e5b3bcd3f50edb152275b294f983     # blade_v5_adapters.tar.gz (optional check if the tar is present in $BASE)
OUT=$BASE/export; mkdir -p "$BASE/runs" "$OUT"; LOG=$BASE/runs/run_s9.log
log(){ echo "=== $(date -Is) $*" | tee -a "$LOG"; }
stop_pod(){ if [ "$STOP_POD" = "1" ]; then [ "$STOP_DELAY_MIN" != "0" ] && { log "waiting $STOP_DELAY_MIN min before stopping"; sleep "$((STOP_DELAY_MIN * 60))"; }
  if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then log "POD STOP REQUESTED (runpodctl stop pod $RUNPOD_POD_ID)"; runpodctl stop pod "$RUNPOD_POD_ID" 2>&1 | tee -a "$LOG"; else log "WARNING: runpodctl/RUNPOD_POD_ID missing - stop the pod from the console"; fi
  else log "STOP_POD=0: pod left running"; fi; }
pack(){ local r=$1
  if [ -d "$BASE/runs/$r" ]; then
    tar czf "$OUT/blade_s9_${r}_v6test.tar.gz" -C "$BASE/runs" $(cd "$BASE/runs" && ls -d $r/config.json $r/env.json $r/eval/v6test_* $r/logs/run.log 2>/dev/null) run_s9.log
    (cd "$OUT" && sha256sum "blade_s9_${r}_v6test.tar.gz" | tee -a SHA256SUMS_s9 | tee -a "$LOG")
    [ -n "$RETRIEVE_CMD" ] && { $RETRIEVE_CMD "$OUT/blade_s9_${r}_v6test.tar.gz" 2>&1 | tee -a "$LOG" || log "retrieve failed for $r"; }
  fi; }
final_tar(){ log "final archive"
  tar czf "$OUT/blade_s9_all_v6test.tar.gz" -C "$BASE/runs" $(cd "$BASE/runs" && ls -d lora_v5_s*/config.json lora_v5_s*/env.json lora_v5_s*/eval/v6test_* lora_v5_s*/logs/run.log lora_v7_s*/config.json lora_v7_s*/env.json lora_v7_s*/eval/v6test_* lora_v7_s*/logs/run.log 2>/dev/null) run_s9.log
  (cd "$OUT" && sha256sum blade_s9_all_v6test.tar.gz | tee -a SHA256SUMS_s9 | tee -a "$LOG"); [ -n "$RETRIEVE_CMD" ] && { $RETRIEVE_CMD "$OUT/blade_s9_all_v6test.tar.gz" 2>&1 | tee -a "$LOG" || true; }; ls -lh "$OUT" | tee -a "$LOG"; }
stop_run(){ log "STOP: $1"; for m in $MODELS; do for s in $SEEDS; do pack "lora_${m}_s$s"; done; done; final_tar; stop_pod; exit 1; }
run_done(){ local r=$BASE/runs/$1 t=$2; [ "$(ls $r/eval/v6test_predictions_*.jsonl 2>/dev/null | wc -l)" = "2" ] && grep -q "INFO done $t" "$r/logs/run.log" 2>/dev/null && [ "$(wc -l < $r/eval/v6test_predictions_oas_code_$t.jsonl)" = "289" ] && [ "$(wc -l < $r/eval/v6test_predictions_oas_$t.jsonl)" = "289" ]; }
run_one(){ local m=$1 s=$2 r=lora_${m}_s$s t=lora_${m}_s${s}_final
  [ -f "$BASE/runs/$r/adapter/adapter_model.safetensors" ] || stop_run "adapter missing: runs/$r/adapter (v5: tar -xzf blade_v5_adapters.tar.gz -C $BASE/runs; v7: run_v7.sh output)"
  if run_done "$r" "$t"; then log "$r v6test already complete: skip"; return 0; fi
  log "$r: test_v6 inference (oas + oas_code, resumable)"
  if python runpod/run_train_v7.py --data "$m" --seed "$s" --base "$BASE" --eval-only --jobs v6test 2>&1 | grep -v "it/s\]" | tee -a "$LOG"; then log "$r ok"; else log "$r FAILED"; stop_run "$r failed (see runs/$r/logs/run.log)"; fi
  run_done "$r" "$t" || stop_run "$r did not finish (289 rows x 2 conditions expected)"; pack "$r"; }
cd "$BASE" || { echo "base dir not found: $BASE"; exit 1; }
log "run_s9 start pod=${RUNPOD_POD_ID:-?} BASE=$BASE MODELS=[$MODELS] SEEDS=[$SEEDS] STOP_POD=$STOP_POD"
if [ "$STOP_POD" = "1" ]; then if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then log "auto-stop armed"; else log "WARNING: runpodctl or RUNPOD_POD_ID missing - the pod will NOT stop itself"; fi; fi
log "0/4 hashes"
[ "$(sha256sum data_v7/data_v7_hashes.json | cut -d' ' -f1)" = "$HASH_V7" ] || stop_run "data_v7_hashes.json hash mismatch"
[ "$(sha256sum data_v7/policy_label_v3.0.1.md | cut -d' ' -f1)" = "$HASH_PROMPT" ] || stop_run "policy_label_v3.0.1.md hash mismatch"
[ "$(sha256sum data_v7/test_v6_manifest.json | cut -d' ' -f1)" = "$HASH_TESTV6_MANIFEST" ] || stop_run "test_v6_manifest.json missing or differs from the frozen one"
[ "$(sha256sum data_v7/test_v6_inputs.jsonl | cut -d' ' -f1)" = "$HASH_TESTV6_INPUTS" ] || stop_run "test_v6_inputs.jsonl missing or differs from the frozen one"
[ "$(wc -l < data_v7/test_v6_inputs.jsonl)" = "289" ] || stop_run "test_v6_inputs.jsonl must have 289 rows"
grep -q "sha='$HASH_TESTV6_MANIFEST'" runpod/run_train_v7.py || stop_run "run_train_v7.py TESTV6 sha not set to the frozen manifest (old bundle?)"
[ -e data_v7/test_v5_inputs.jsonl ] || [ -e data_v7/test_v31_supp_inputs.jsonl ] && stop_run "test_v5/test_v31_supp inputs must not be in data_v7"
for f in "$BASE"/blade_v5_adapters.tar.gz "$BASE"/export/blade_v5_adapters.tar.gz; do [ -f "$f" ] && { [ "$(sha256sum "$f" | cut -d' ' -f1)" = "$HASH_V5_ADAPTERS" ] && log "v5 adapters tar ok ($f)" || stop_run "blade_v5_adapters.tar.gz hash mismatch ($f)"; }; done
for m in $MODELS; do for s in $SEEDS; do [ -f "runs/lora_${m}_s$s/adapter/adapter_model.safetensors" ] || stop_run "adapter missing: runs/lora_${m}_s$s/adapter"; done; done
log "adapters: $(ls -d runs/lora_v5_s*/adapter runs/lora_v7_s*/adapter 2>/dev/null | tr '\n' ' ')"
log "1/4 environment"; nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | tee -a "$LOG"; df -h "$BASE" 2>/dev/null | tee -a "$LOG"
if [ "$SKIP_SETUP" != "1" ]; then bash runpod/setup.sh 2>&1 | tail -5 | tee -a "$LOG" || stop_run "setup.sh failed"; fi
python -c "import unsloth, trl, peft, transformers, torch; print('unsloth', unsloth.__version__, 'trl', trl.__version__, 'peft', peft.__version__, 'transformers', transformers.__version__, 'torch', torch.__version__)" 2>&1 | tee -a "$LOG" || { if [ "$SKIP_SETUP" = "1" ]; then log "imports failed: running setup.sh"; bash runpod/setup.sh 2>&1 | tail -5 | tee -a "$LOG" || stop_run "setup.sh failed"; python -c "import unsloth, trl, peft, transformers, torch" || stop_run "imports failed after setup"; else stop_run "imports failed"; fi; }
log "2/4 inference"; for m in $MODELS; do for s in $SEEDS; do run_one "$m" "$s"; done; done
log "3/4 final archive"; final_tar
log "4/4 ALL DONE — $OUT/blade_s9_lora_<v5|v7>_s<seed>_v6test.tar.gz, $OUT/blade_s9_all_v6test.tar.gz, $OUT/SHA256SUMS_s9"
stop_pod
