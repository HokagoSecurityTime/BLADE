#!/usr/bin/env bash
# C′: LoRA v6d = LoRA v5 recipe (7B base, prompt v3.0.1, same hyperparameters) with ONE change: training targets data-v5 -> data-v6d — RunPod, auto-stop.
# One pass (AGENTS.md "작업 C′", pre-registered 2026-11-05):
#   0 hashes -> 1 environment (setup.sh) -> 2 preflight (7B load + generate) -> 3 seed 42 train + 6 prediction jobs -> pack -> 4 seed 43 -> 5 seed 44 -> 6 final tar -> pod stop (STOP_POD=1).
# No early gate (not pre-registered for C′); the adoption decision uses the 3-seed means (test_v5 oas_code macro-F1 >= v5 + 0.016, test_v30 207 precision drop <= 0.025, public misjudge <= 2.0).
# Start detached:   tmux new -d -s v6d "bash /workspace/blade_lora_v3/runpod/run_v6d.sh"     watch: tail -f /workspace/blade_lora_v3/runs/run_v6d.log
# Re-running resumes: a finished seed (adapter + 6 complete prediction files + "done" line) is skipped, an interrupted one resumes from its last checkpoint /
# appended prediction rows. A failing seed STOPs the script (pack what exists, stop the pod). No commit, no test_v6.
set -uo pipefail
BASE=${BASE:-/workspace/blade_lora_v3}; SEEDS=${SEEDS:-"42 43 44"}; STOP_POD=${STOP_POD:-1}; STOP_DELAY_MIN=${STOP_DELAY_MIN:-0}; SKIP_SETUP=${SKIP_SETUP:-0}
RETRIEVE_CMD=${RETRIEVE_CMD:-}      # optional, run after every pack with the archive path as $1 (scp/rclone ...); empty = archives stay in $BASE/export
REQUIRE_STOP=${REQUIRE_STOP:-1}     # 1 = refuse to start unless the pod can be stopped from this script (runpodctl + RUNPOD_POD_ID, or RUNPOD_API_KEY for the GraphQL fallback)
STOPPED=0
export HF_HOME=${HF_HOME:-/workspace/hf}   # fresh pod: the 7B base (5.6 GB) is downloaded here; no network volume or earlier run is needed
HASH_V6D=82efda868e7bde511d0838e10bf0e8a5cc3e6aae577c68b15fcbf370a9d94b53      # data_v6d/data_v6d_hashes.json (run_train_v6d.py DATASETS sha, data-v6d freeze)
HASH_T5=57fd384f46e89e905209e627a7ff7fb9f312e22a7bed222639e91a80bd05fccd       # data_v6d/test_v5_manifest.json (TESTV5 gate, byte-identical to data_v5's)
HASH_PROMPT=d0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef   # policy_label_v3.0.1.md (frozen)
OUT=$BASE/export; mkdir -p "$BASE/runs" "$OUT"; LOG=$BASE/runs/run_v6d.log; FIRST=${SEEDS%% *}
log(){ echo "=== $(date -Is) $*" | tee -a "$LOG"; }
stop_pod(){ # idempotent; runpodctl first, RunPod GraphQL (RUNPOD_API_KEY) as fallback. Also called by the EXIT trap, so an error exit stops the pod too.
  [ "$STOPPED" = "1" ] && return 0; STOPPED=1
  if [ "$STOP_POD" != "1" ]; then log "STOP_POD=0: pod left running"; return 0; fi
  [ "$STOP_DELAY_MIN" != "0" ] && { log "waiting $STOP_DELAY_MIN min before stopping"; sleep "$((STOP_DELAY_MIN * 60))"; }
  if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then log "POD STOP REQUESTED (runpodctl stop pod $RUNPOD_POD_ID)"; runpodctl stop pod "$RUNPOD_POD_ID" 2>&1 | tee -a "$LOG" && return 0; fi
  if [ -n "${RUNPOD_API_KEY:-}" ] && [ -n "${RUNPOD_POD_ID:-}" ]; then log "POD STOP REQUESTED (GraphQL podStop $RUNPOD_POD_ID)"
    curl -s -X POST "https://api.runpod.io/graphql?api_key=$RUNPOD_API_KEY" -H 'Content-Type: application/json' -d "{\"query\":\"mutation { podStop(input: {podId: \\\"$RUNPOD_POD_ID\\\"}) { id desiredStatus } }\"}" 2>&1 | tee -a "$LOG"; echo | tee -a "$LOG"; return 0; fi
  log "WARNING: no stop mechanism (runpodctl + RUNPOD_POD_ID, or RUNPOD_API_KEY) - STOP THE POD FROM THE CONSOLE NOW"; }
ensure_stop(){ # before anything expensive: make sure the pod can be stopped from here; otherwise abort (REQUIRE_STOP=1)
  [ "$STOP_POD" = "1" ] || { log "STOP_POD=0: the pod will be left running (not the default)"; return 0; }
  command -v runpodctl >/dev/null || { log "runpodctl missing: installing from cli.runpod.net"; (wget -qO- cli.runpod.net | bash) >/dev/null 2>&1 || (curl -sL cli.runpod.net | bash) >/dev/null 2>&1 || true; hash -r; }
  if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then log "auto-stop armed: runpodctl stop pod $RUNPOD_POD_ID (runs when this script ends, also on error/abort)"; return 0; fi
  if [ -n "${RUNPOD_API_KEY:-}" ] && [ -n "${RUNPOD_POD_ID:-}" ]; then log "auto-stop armed: GraphQL podStop $RUNPOD_POD_ID (runpodctl unavailable)"; return 0; fi
  if [ "$REQUIRE_STOP" = "1" ]; then log "ABORT before training: this pod cannot be stopped from the script (need runpodctl + RUNPOD_POD_ID, or export RUNPOD_API_KEY). Fix that or run with REQUIRE_STOP=0."; exit 2; fi
  log "WARNING: REQUIRE_STOP=0 and no stop mechanism - the pod will NOT stop itself"; }
pack(){ # $1 = run dir name (lora_v6d_s42): results (config/env/eval/logs + run_v6d.log) and the adapter if any, hash lines, then RETRIEVE_CMD
  local r=$1 f
  if [ -d "$BASE/runs/$r" ]; then
    tar czf "$OUT/blade_v6d_${r}_results.tar.gz" -C "$BASE/runs" $(cd "$BASE/runs" && ls -d $r/config.json $r/env.json $r/eval $r/logs 2>/dev/null) run_v6d.log
    [ -f "$BASE/runs/$r/adapter/adapter_model.safetensors" ] && tar czf "$OUT/blade_v6d_${r}_adapter.tar.gz" -C "$BASE/runs" "$r/adapter"
    (cd "$OUT" && sha256sum blade_v6d_${r}_*.tar.gz | tee -a SHA256SUMS_blade_v6d | tee -a "$LOG")
    for f in "$OUT"/blade_v6d_${r}_*.tar.gz; do [ -n "$RETRIEVE_CMD" ] && { $RETRIEVE_CMD "$f" 2>&1 | tee -a "$LOG" || log "retrieve failed for $f (archive kept in $OUT)"; }; done
  fi; }
final_tar(){ log "final archive"
  tar czf "$OUT/blade_v6d_all_results.tar.gz" -C "$BASE/runs" $(cd "$BASE/runs" && ls -d lora_v6d_s*/config.json lora_v6d_s*/env.json lora_v6d_s*/eval lora_v6d_s*/logs 2>/dev/null) run_v6d.log
  (cd "$OUT" && sha256sum blade_v6d_all_results.tar.gz | tee -a SHA256SUMS_blade_v6d | tee -a "$LOG")
  [ -n "$RETRIEVE_CMD" ] && { $RETRIEVE_CMD "$OUT/blade_v6d_all_results.tar.gz" 2>&1 | tee -a "$LOG" || true; }
  ls -lh "$OUT" | tee -a "$LOG"; }
stop_run(){ log "STOP: $1"; for s in $SEEDS; do pack "lora_v6d_s$s"; done; final_tar; stop_pod; exit 1; }
seed_done(){ local r=$BASE/runs/lora_v6d_s$1; [ -f "$r/adapter/adapter_model.safetensors" ] && [ "$(ls $r/eval/*.jsonl 2>/dev/null | wc -l)" = "6" ] && grep -q "INFO done lora_v6d_s${1}_final" "$r/logs/run.log" 2>/dev/null; }
run_seed(){ # $1 = seed: train + eval (resumable), pack; STOP on failure
  local s=$1 r=$BASE/runs/lora_v6d_s$1
  if seed_done "$s"; then log "seed $s already complete: skip"; return 0; fi
  log "seed $s: train + eval (resumable)"
  if python runpod/run_train_v6d.py --data v6d --seed "$s" --base "$BASE" 2>&1 | grep -v "it/s\]" | tee -a "$LOG"; then log "seed $s ok"; else log "seed $s FAILED"; stop_run "seed $s failed (see runs/lora_v6d_s$s/logs/run.log)"; fi
  seed_done "$s" || stop_run "seed $s did not finish"
  pack "lora_v6d_s$s"; }
cd "$BASE" || { echo "base dir not found: $BASE"; exit 1; }
log "run_v6d start pod=${RUNPOD_POD_ID:-?} BASE=$BASE SEEDS=[$SEEDS] STOP_POD=$STOP_POD REQUIRE_STOP=$REQUIRE_STOP"
trap 'rc=$?; log "script exiting (rc=$rc)"; stop_pod' EXIT   # every exit path (done, STOP, abort, unexpected error) ends with a pod stop
ensure_stop
log "0/6 hashes"
[ "$(sha256sum data_v6d/data_v6d_hashes.json | cut -d' ' -f1)" = "$HASH_V6D" ] || stop_run "data_v6d_hashes.json hash mismatch"
[ "$(sha256sum data_v6d/test_v5_manifest.json | cut -d' ' -f1)" = "$HASH_T5" ] || stop_run "test_v5_manifest.json hash mismatch"
[ "$(sha256sum data_v6d/policy_label_v3.0.1.md | cut -d' ' -f1)" = "$HASH_PROMPT" ] || stop_run "policy_label_v3.0.1.md hash mismatch"
python - <<'PY' 2>&1 | tee -a "$LOG" || stop_run "data_v6d file hash mismatch"
import hashlib, json
h = json.load(open('data_v6d/data_v6d_hashes.json')); bad = {n: v for n, v in h['generated'].items() if hashlib.sha256(open('data_v6d/' + n, 'rb').read()).hexdigest() != v}
m = json.load(open('data_v6d/test_v5_manifest.json')); t5 = hashlib.sha256(open('data_v6d/test_v5_inputs.jsonl', 'rb').read()).hexdigest() == m['sha256']['training/lora/data_v5/test_v5_inputs.jsonl']
print('generated files ok:', not bad, bad, '| test_v5_inputs vs manifest:', t5); assert not bad and t5
PY
log "1/6 environment"; nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | tee -a "$LOG"; df -h "$BASE" "$HF_HOME" 2>/dev/null | tee -a "$LOG"
if [ "$SKIP_SETUP" != "1" ]; then bash runpod/setup.sh 2>&1 | tail -5 | tee -a "$LOG" || stop_run "setup.sh failed"; fi
python -c "import unsloth, trl, peft, transformers, torch; print('unsloth', unsloth.__version__, 'trl', trl.__version__, 'peft', peft.__version__, 'transformers', transformers.__version__, 'torch', torch.__version__)" 2>&1 | tee -a "$LOG" || stop_run "imports failed (unsloth/trl/peft)"
log "2/6 preflight (7B base load + generate + memory)"
python runpod/run_train_v6d.py --data v6d --seed "$FIRST" --base "$BASE" --preflight 2>&1 | tail -12 | tee -a "$LOG"
grep -q "preflight done" "$BASE/runs/lora_v6d_s$FIRST/logs/run.log" || stop_run "preflight failed (see runs/lora_v6d_s$FIRST/logs/run.log)"
n=3; for s in $SEEDS; do log "$n/6 seed $s"; run_seed "$s"; n=$((n + 1)); done
log "6/6 final archive"; final_tar
log "ALL DONE — results $OUT/blade_v6d_lora_v6d_s<seed>_results.tar.gz (+ _adapter.tar.gz), $OUT/blade_v6d_all_results.tar.gz, $OUT/SHA256SUMS_blade_v6d"
stop_pod
