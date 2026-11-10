# S4-3 권한 문맥 보강 추론 — RunPod H100 SXM 80GB 실행 안내 (2026-11-04, 자동 정지 포함)

학습 없음, test_v6 없음. v5 final 어댑터 3개(seed 42·43·44)로 문맥 보강 입력을 추론한다. 환경·기준선 게이트를 통과하면 멈추지 않고 추론까지 간다. **끝나면(정상 종료·게이트 STOP 모두) 결과 tar를 만든 뒤 `runpodctl stop pod`로 Pod를 자동 정지한다(STOP_POD=0이면 유지). 결과는 /workspace에 남는다.**

## 올릴 파일

| 파일 | 내용 |
|---|---|
| `blade_s4_ctx_<날짜>.tgz` | 이 번들. `/workspace`에 풀면 `/workspace/blade_s4_ctx/` |
| `blade_v5_adapters.tar.gz` | v5 어댑터 3개(903 MB, SHA-256 `db6abe46…`). 로컬 위치 `<USERPROFILE>/Downloads/export_v5_pahse1/export/blade_v5_adapters.tar.gz`. **새 Pod에는 반드시 `/workspace/`에 올린다**(볼륨에 `/workspace/blade_lora_v3/runs/lora_v5_s4{2,3,4}/adapter/`가 이미 있을 때만 생략) |

## 실행

```bash
cd /workspace && tar -xzf blade_s4_ctx_*.tgz && cd blade_s4_ctx
# 어댑터 tar 경로가 다르면: export ADAPTERS=/workspace/<경로>/blade_v5_adapters.tar.gz
tmux new -d -s s4 "bash /workspace/blade_s4_ctx/run_s4.sh"
tail -f /workspace/blade_s4_ctx/out/run_s4.log
```

- 끊기면 같은 명령으로 다시 실행한다. 예측 파일은 한 건마다 append 저장되므로 이어서 한다(--resume).
- 결과: `/workspace/blade_s4_results.tar.gz` + `/workspace/SHA256SUMS_blade_s4`(각 파일이 끝날 때마다 갱신). `RETRIEVE_CMD='...'`를 환경변수로 주면 그때마다 그 명령을 실행해 밖으로 보낸다(예: git push, rclone). 없으면 로컬에서 `scp`로 `out/`을 가져온다.
- 게이트: `ENV_OK=0`(torch/CUDA/capability/bitsandbytes 4bit/sdpa) 또는 `BASELINE_PASSED=0`(20건 일치 < 95%)이면 로그에 `STOP:` 줄을 남기고 멈춘다. 그 상태로 보고.

## 예상 시간 (H100 SXM)

설치·점검 5~10분, 기준선 20건 2분, 작업당(모델 로드 1분 + 283건 5~7분 / 207건 4~5분) × 8작업 ≈ 45~60분. **합계 약 1~1.2시간.** 끝나면 결과 tar를 만든 뒤 Pod가 스스로 정지한다(`STOP_POD=0 bash run_s4.sh`로 실행하면 유지). 정지 뒤에도 /workspace는 남는다.

## 단계

1. 환경 점검 `env_check.py`: torch ≥ 2.4, CUDA ≥ 12.1, capability (9,0)=H100(다른 GPU는 경고만), transformers·peft·bitsandbytes 버전, bitsandbytes NF4 Linear forward, sdpa. flash-attn 미사용. transformers 4.x/5.x 모두 지원(dtype 인자 자동 선택). 기록 `out/env_check.json`, `out/env.json`.
2. 기준선 재현: v5 s42 + 문맥 없는 기존 `test_v5_inputs.jsonl` 20건(label 비례 층화, seed 42) → 기존 예측(`baseline/v5test_predictions_oas_code_lora_v5_s42_final.jsonl`)과 label 일치율. ≥ 95%면 진행.
3. test_v30 207 입력은 번들에 이미 있다(`data/test_v30_ctx*_inputs.jsonl`, 부록 reports/eval/context_aug_v5/appendix_test_v30_inputs.md).
4. 추론 순서: s42 ctx4096 test_v5 → s42 ctx6144 test_v5 → s42 ctx4096 test_v30 → s42 ctx6144 test_v30 → 채점·예산 선택(`score_ctx.py select`) → 선택 예산으로 s43·s44(test_v5 → test_v30) → `summary.md`.
5. 보고서는 로컬에서 작성(reports/eval/context_aug_v5/report.md).

## 로딩 방식(기존 v5 HF 평가와 동일 근거)

training/lora/runpod/run_train.py 176-178행: `FastLanguageModel.from_pretrained(model_name='unsloth/Qwen2.5-7B-Instruct-bnb-4bit', max_seq_length=4096, dtype=None, load_in_4bit=True)` + `PeftModel.from_pretrained(base, adapter)`; `HP['eval_batch']=8`, `eval_max_new_tokens=256`, greedy(do_sample=False), left padding. 이 번들은 같은 체크포인트(bnb 4bit 사전 양자화)·bf16 계산·배치 8·greedy·256을 쓰되 로더만 transformers(`attn_implementation="sdpa"`)다(`LOADER=unsloth`로 기존 로더 선택 가능). 두 로더 차이는 2번 기준선 재현으로 확인한다.

## 파일

`run_ctx_eval.py`(추론, --resume) · `score_ctx.py`(채점·선택·요약) · `env_check.py` · `baseline_check.py` · `data/`(test_v5_inputs.jsonl 원본 + ctx 입력 4개 + 프롬프트) · `baseline/`(v5 3 seed 기존 oas_code 예측) · `SHA256SUMS_bundle`.
