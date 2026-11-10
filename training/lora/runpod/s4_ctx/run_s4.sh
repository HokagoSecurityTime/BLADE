#!/usr/bin/env bash
# S4-3 권한 문맥 보강 추론 (RunPod H100 SXM 80GB 기준, 학습 없음; A100·Blackwell도 실행 가능). 번들을 /workspace/blade_s4_ctx 에 풀고 tmux 안에서 실행:
#     cd /workspace && tar -xzf blade_s4_ctx_*.tgz && cd blade_s4_ctx
#     tmux new -d -s s4 "bash /workspace/blade_s4_ctx/run_s4.sh"
#     tail -f /workspace/blade_s4_ctx/out/run_s4.log
# 단계: 1 환경 점검(env_check.py: torch>=2.4/cu12.1+, capability (9,0)=H100 권장, bitsandbytes 4bit 동작, sdpa) → 2 기준선 재현(v5 s42, 문맥 없는 test_v5 20건, 일치 ≥95% 게이트)
#       → 4 추론: s42 ctx4096 test_v5 → s42 ctx6144 test_v5 → s42 ctx4096 test_v30 → s42 ctx6144 test_v30 → 채점·예산 선택 → 선택 예산 s43·s44(test_v5 → test_v30)
#       → 요약 → /workspace/blade_s4_results.tar.gz. 각 예측 파일은 한 건마다 append 저장(--resume)이며 재실행 시 이어서 한다.
# 회수: 파일이 끝날 때마다 RETRIEVE_CMD(환경변수, 예: 'bash /workspace/push_results.sh')가 있으면 실행한다. 없으면 로컬에서 scp로 out/ 을 주기적으로 가져온다.
# 게이트 실패(환경·bitsandbytes·기준선 <95%)면 out/run_s4.log 에 STOP 이유를 남기고 멈춘다. 정상 종료·STOP 모두 결과 tar 생성 후 runpodctl stop pod 로 Pod를 자동 정지한다(STOP_POD=0 이면 유지).
set -uo pipefail
S4=${S4:-/workspace/blade_s4_ctx}
RUNS=${RUNS:-/workspace/blade_lora_v3/runs}          # runs/lora_v5_s4{2,3,4}/adapter
ADAPTERS=${ADAPTERS:-/workspace/blade_v5_adapters.tar.gz}
ADAPTERS_SHA=db6abe46438b27795b51a12e875d24678932e5b3bcd3f50edb152275b294f983
LOADER=${LOADER:-hf}                                  # hf = transformers + bitsandbytes 4bit + sdpa (기본). unsloth = 기존 v5 평가 로더(참고용)
RETRIEVE_CMD=${RETRIEVE_CMD:-}
STOP_POD=${STOP_POD:-1}; STOP_DELAY_MIN=${STOP_DELAY_MIN:-0}   # 1 = 끝나면(정상 종료·게이트 STOP 모두) 결과 tar를 만든 뒤 runpodctl stop pod. 결과는 /workspace에 남는다.
export HF_HOME=${HF_HOME:-/workspace/hf}
OUT=$S4/out; mkdir -p "$OUT"; LOG=$OUT/run_s4.log
log(){ echo "=== $(date -Is) $*" | tee -a "$LOG"; }
retrieve(){ if [ -n "$RETRIEVE_CMD" ]; then log "retrieve: $RETRIEVE_CMD"; bash -c "$RETRIEVE_CMD" 2>&1 | tail -3 | tee -a "$LOG"; fi; }
pack(){ ( cd /workspace && tar -czf blade_s4_results.tar.gz -C "$S4" out && sha256sum blade_s4_results.tar.gz > SHA256SUMS_blade_s4 && cat SHA256SUMS_blade_s4 ) | tee -a "$LOG"; }
stop_pod(){ if [ "$STOP_POD" = "1" ]; then [ "$STOP_DELAY_MIN" != "0" ] && { log "waiting $STOP_DELAY_MIN min before stopping"; sleep "$((STOP_DELAY_MIN * 60))"; }
  if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then log "stopping pod $RUNPOD_POD_ID"; runpodctl stop pod "$RUNPOD_POD_ID" 2>&1 | tee -a "$LOG"; log "POD STOP REQUESTED"; else log "POD NOT STOPPED: runpodctl/RUNPOD_POD_ID missing — stop it from the console"; fi; else log "STOP_POD=0: pod left running"; fi; }
stop_run(){ log "STOP: $1"; pack; retrieve; stop_pod; exit 1; }
cd "$S4" || { echo "bundle dir not found: $S4"; exit 1; }
log "run_s4 (S4-3) start pod=${RUNPOD_POD_ID:-?} S4=$S4 RUNS=$RUNS LOADER=$LOADER STOP_POD=$STOP_POD"
if [ "$STOP_POD" = "1" ]; then if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then log "auto-stop armed: runpodctl stop pod $RUNPOD_POD_ID will run when this script ends"; else log "WARNING: runpodctl or RUNPOD_POD_ID missing - the pod will NOT stop itself"; fi; fi
log "0/5 bundle hashes"; (cd "$S4" && sha256sum -c SHA256SUMS_bundle) | tail -3 | tee -a "$LOG" || stop_run "bundle hash mismatch"
log "1/5 environment"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | tee -a "$LOG"
if ! python -c "import transformers, peft, bitsandbytes" 2>/dev/null; then log "installing transformers/peft/bitsandbytes/accelerate"; pip install -q "transformers>=4.48" "peft>=0.14" "bitsandbytes>=0.45" accelerate 2>&1 | tail -2 | tee -a "$LOG"; fi
python "$S4/env_check.py" "$OUT/env_check.json" 2>&1 | tee -a "$LOG" || stop_run "environment gate failed (see env_check.json; bitsandbytes on sm_120?)"
command -v tmux >/dev/null || (apt-get update -qq && apt-get install -y -qq tmux) >/dev/null 2>&1
log "adapters"
for s in 42 43 44; do
  if [ ! -f "$RUNS/lora_v5_s$s/adapter/adapter_model.safetensors" ]; then
    [ -f "$ADAPTERS" ] || stop_run "adapter runs/lora_v5_s$s missing and $ADAPTERS not found"
    got=$(sha256sum "$ADAPTERS" | cut -d' ' -f1); [ "$got" = "$ADAPTERS_SHA" ] || stop_run "adapter archive hash mismatch: $got"
    mkdir -p "$RUNS" && tar -xzf "$ADAPTERS" -C "$RUNS" && log "adapters restored from $ADAPTERS"
  fi
  [ -f "$RUNS/lora_v5_s$s/adapter/adapter_model.safetensors" ] || stop_run "adapter lora_v5_s$s still missing"
done
ls -la "$RUNS"/lora_v5_s4*/adapter/adapter_model.safetensors | tee -a "$LOG"
log "2/5 baseline reproduction (v5 s42, no-context test_v5, 20 stratified rows)"
python "$S4/baseline_check.py" ids --inputs "$S4/data/test_v5_inputs.jsonl" --out "$OUT/baseline_ids.json" | tee -a "$LOG"
python "$S4/run_ctx_eval.py" --adapter "$RUNS/lora_v5_s42/adapter" --inputs "$S4/data/test_v5_inputs.jsonl" --out "$OUT/baseline_s42.jsonl" --max-len 4096 --ids "$OUT/baseline_ids.json" --loader "$LOADER" --resume --system "$S4/data/policy_label_v3.0.1.md" 2>&1 | tee -a "$LOG"
python "$S4/baseline_check.py" compare --pred "$OUT/baseline_s42.jsonl" --baseline "$S4/baseline/v5test_predictions_oas_code_lora_v5_s42_final.jsonl" --out "$OUT/baseline_check.json" 2>&1 | tee -a "$LOG"
grep -q "BASELINE_PASSED=1" "$LOG" || stop_run "baseline reproduction < 95% (see out/baseline_check.json mismatches)"
retrieve
infer(){ # set budget seed
  local set=$1 bk=$2 seed=$3 ml=${2#ctx}
  log "infer $set $bk s$seed (max_len $ml)"
  python "$S4/run_ctx_eval.py" --adapter "$RUNS/lora_v5_s$seed/adapter" --inputs "$S4/data/${set}_${bk}_inputs.jsonl" --out "$OUT/pred_${set}_${bk}_s${seed}.jsonl" --max-len "$ml" --loader "$LOADER" --resume --system "$S4/data/policy_label_v3.0.1.md" 2>&1 | tee -a "$LOG"
  local n; n=$(wc -l < "$OUT/pred_${set}_${bk}_s${seed}.jsonl" 2>/dev/null || echo 0); local want=283; [ "$set" = "test_v30" ] && want=207
  [ "$n" -ge "$want" ] || { log "INCOMPLETE $set $bk s$seed ($n/$want rows) — rerun run_s4.sh to resume"; return 1; }
  local kind=test_v5; [ "$set" = "test_v30" ] && kind=test_v30_207
  python "$S4/score_ctx.py" score --pred "$OUT/pred_${set}_${bk}_s${seed}.jsonl" --inputs "$S4/data/${set}_${bk}_inputs.jsonl" --kind "$kind" --out "$OUT/score_${set}_${bk}_s${seed}.json" 2>&1 | tee -a "$LOG"
  pack; retrieve
}
log "4/5 seed 42: ctx4096 test_v5 → ctx6144 test_v5 → ctx4096 test_v30 → ctx6144 test_v30"
for job in "test_v5 ctx4096" "test_v5 ctx6144" "test_v30 ctx4096" "test_v30 ctx6144"; do set -- $job; infer "$1" "$2" 42 || stop_run "seed 42 $1 $2 incomplete"; done
log "budget selection"
python "$S4/score_ctx.py" select --out-dir "$OUT" --baseline-dir "$S4/baseline" 2>&1 | tee -a "$LOG"
BUDGET=$(python -c "import json;print(json.load(open('$OUT/selection.json'))['chosen'])" 2>/dev/null || echo "")
[ -n "$BUDGET" ] || stop_run "selection failed (missing s42 scores?)"
log "5/5 seeds 43, 44 with $BUDGET (test_v5 → test_v30)"
for seed in 43 44; do for set in test_v5 test_v30; do infer "$set" "$BUDGET" "$seed" || stop_run "seed $seed $set incomplete"; done; done
log "summary"; python "$S4/score_ctx.py" summary --out-dir "$OUT" --baseline-dir "$S4/baseline" 2>&1 | tail -40 | tee -a "$LOG"
pack; retrieve
log "ALL DONE — results /workspace/blade_s4_results.tar.gz + /workspace/SHA256SUMS_blade_s4"
stop_pod
