# 작업 S2 — LoRA v5 3 seed 다수결 재채점 (보조 지표, 학습·추론 없음)

2026-11-03. 기존 v5 seed 42·43·44 예측 파일(reports/eval/lora_v5/lora_v5_s*/eval/, oas_code, 기본 디코딩)을 레코드별 label 다수결로 합쳐 재채점했다. 재추론 없음. 주지표(test_v30 207 단일 seed 평균)와 발표 수치(presentation_numbers_v5.md)는 바꾸지 않는다.

동률 규칙(채점 전 AGENTS.md에 기록): 3 seed가 모두 다르면 seed 42 예측. 출력 오류는 기권으로 보고 나머지 2개로 다수결, 그래도 동률이면 seed 42 예측(seed 42가 기권이면 출력 오류). 지표 정의는 scripts/eval_combined_v5.py와 같다(7-class, macro-F1은 support>0 label 평균, 구체 정밀도 = 정답 구체 건 중 구체로 답한 건의 정답률, 구체 재현율 = 정답 구체 건 전체 대비 정답률). 단일 seed 열은 3 seed 평균 ± 표본 표준편차.

## 1. 요약 (단일 seed 평균 ± sd vs 다수결)

| 셋 | n | 지표 | 단일 seed (3) | 다수결 | 차이 | sd 초과 |
|---|---:|---|---:|---:|---:|:--:|
| test_v30 oas_code 합성 제외 | 207 | macro-F1 | 0.374 ± 0.010 | 0.386 | +0.011 | 예 |
| test_v30 oas_code 합성 제외 | 207 | 정확도 | 0.568 ± 0.010 | 0.585 | +0.016 | 예 |
| test_v30 oas_code 합성 제외 | 207 | 구체 정밀도 | 0.796 ± 0.025 | 0.805 | +0.010 | 아니오 |
| test_v30 oas_code 합성 제외 | 207 | 구체 재현율 | 0.566 ± 0.010 | 0.583 | +0.016 | 예 |
| test_v30 oas_code 합성 제외 | 207 | 구체 응답률 | 0.712 ± 0.017 | 0.723 | +0.011 | 아니오 |
| test_v30 oas_code 합성 제외 | 207 | manual 비율 | 28.2 ± 2.3% | 27.5% | -0.6%p | 아니오 |
| test_v30 oas_code 합성 제외 | 207 | 출력 오류 | 4 / 0 / 2 | 1 | - | - |
| test_v31_supp oas_code | 222 | macro-F1 | 0.485 ± 0.026 | 0.495 | +0.010 | 아니오 |
| test_v31_supp oas_code | 222 | 정확도 | 0.419 ± 0.039 | 0.432 | +0.013 | 아니오 |
| test_v31_supp oas_code | 222 | 구체 정밀도 | 0.561 ± 0.007 | 0.586 | +0.025 | 예 |
| test_v31_supp oas_code | 222 | 구체 재현율 | 0.446 ± 0.042 | 0.464 | +0.017 | 아니오 |
| test_v31_supp oas_code | 222 | 구체 응답률 | 0.795 ± 0.065 | 0.792 | -0.003 | 아니오 |
| test_v31_supp oas_code | 222 | manual 비율 | 20.7 ± 5.5% | 21.2% | +0.5%p | 아니오 |
| test_v31_supp oas_code | 222 | 출력 오류 | 0 / 1 / 1 | 0 | - | - |
| test_v5 oas_code | 283 | macro-F1 | 0.683 ± 0.016 | 0.688 | +0.006 | 아니오 |
| test_v5 oas_code | 283 | 정확도 | 0.691 ± 0.007 | 0.703 | +0.012 | 예 |
| test_v5 oas_code | 283 | 구체 정밀도 | 0.845 ± 0.009 | 0.847 | +0.002 | 아니오 |
| test_v5 oas_code | 283 | 구체 재현율 | 0.769 ± 0.003 | 0.789 | +0.020 | 예 |
| test_v5 oas_code | 283 | 구체 응답률 | 0.910 ± 0.012 | 0.931 | +0.021 | 예 |
| test_v5 oas_code | 283 | manual 비율 | 16.6 ± 1.6% | 14.8% | -1.8%p | 예 |
| test_v5 oas_code | 283 | 출력 오류 | 1 / 0 / 2 | 0 | - | - |

"sd 초과"는 다수결과 단일 seed 평균의 차이 절대값이 3 seed 표본 표준편차보다 큰지 여부(작업 C 규칙: 표준편차보다 큰 차이만 차이로 인정). manual 비율 열의 sd 초과도 같은 기준이다.

## 2. label별 F1 (support)

### test_v30 oas_code 합성 제외 (207건)

| label (support) | 단일 seed F1 | 다수결 F1 | 차이 | 다수결 P / R |
|---|---:|---:|---:|---:|
| public (58) | 0.644 ± 0.047 | 0.667 | +0.022 | 0.745 / 0.603 |
| role_required (39) | 0.442 ± 0.030 | 0.464 | +0.023 | 0.765 / 0.333 |
| owner_match (106) | 0.752 ± 0.018 | 0.762 | +0.010 | 0.868 / 0.679 |
| owner_or_admin (3) | 0.000 ± 0.000 | 0.000 | +0.000 | 0.000 / 0.000 |
| manual_review_required (1) | 0.034 ± 0.003 | 0.035 | +0.001 | 0.018 / 1.000 |

정답 support 0인 label(제외): membership_required, tenant_match

### test_v31_supp oas_code (222건)

| label (support) | 단일 seed F1 | 다수결 F1 | 차이 | 다수결 P / R |
|---|---:|---:|---:|---:|
| public (2) | 1.000 ± 0.000 | 1.000 | +0.000 | 1.000 / 1.000 |
| role_required (39) | 0.491 ± 0.055 | 0.544 | +0.052 | 0.438 / 0.718 |
| membership_required (55) | 0.601 ± 0.089 | 0.586 | -0.015 | 0.659 / 0.527 |
| tenant_match (55) | 0.235 ± 0.043 | 0.226 | -0.009 | 1.000 / 0.127 |
| owner_match (21) | 0.541 ± 0.072 | 0.560 | +0.019 | 0.483 / 0.667 |
| owner_or_admin (20) | 0.328 ± 0.024 | 0.367 | +0.039 | 0.310 / 0.450 |
| manual_review_required (30) | 0.198 ± 0.052 | 0.182 | -0.017 | 0.149 / 0.233 |

### test_v5 oas_code (283건)

| label (support) | 단일 seed F1 | 다수결 F1 | 차이 | 다수결 P / R |
|---|---:|---:|---:|---:|
| public (19) | 0.894 ± 0.063 | 0.882 | -0.012 | 1.000 / 0.789 |
| role_required (111) | 0.818 ± 0.026 | 0.843 | +0.025 | 0.867 / 0.820 |
| membership_required (33) | 0.589 ± 0.048 | 0.565 | -0.024 | 0.462 / 0.727 |
| owner_match (34) | 0.760 ± 0.024 | 0.732 | -0.028 | 0.703 / 0.765 |
| owner_or_admin (21) | 0.536 ± 0.031 | 0.604 | +0.068 | 0.500 / 0.762 |
| manual_review_required (65) | 0.499 ± 0.027 | 0.505 | +0.005 | 0.643 / 0.415 |

정답 support 0인 label(제외): tenant_match

## 3. 다수결 구성

| 셋 | n | 3 seed 일치 | 과반(3개 유효) | 기권 후 과반 | 유효 1개 | 동률(3개 다름→s42) | 기권 후 동률→s42 | s42 기권 동률→오류 | 전부 기권 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| test_v30 oas_code 합성 제외 | 207 | 138 | 201 | 5 | 0 | 0 | 0 | 1 | 0 |
| test_v31_supp oas_code | 222 | 139 | 212 | 0 | 0 | 8 | 2 | 0 | 0 |
| test_v5 oas_code | 283 | 214 | 271 | 3 | 0 | 9 | 0 | 0 | 0 |

### 다수결이 각 seed 단독 예측을 바꾼 건수 (정답 기준 득·실)

| 셋 | seed | 바뀐 건 | 오답→정답 | 정답→오답 | 순득 |
|---|---:|---:|---:|---:|---:|
| test_v30 oas_code 합성 제외 | 42 | 26 | 12 | 7 | +5 |
| test_v30 oas_code 합성 제외 | 43 | 17 | 7 | 6 | +1 |
| test_v30 oas_code 합성 제외 | 44 | 27 | 9 | 5 | +4 |
| test_v31_supp oas_code | 42 | 18 | 9 | 2 | +7 |
| test_v31_supp oas_code | 43 | 48 | 6 | 13 | -7 |
| test_v31_supp oas_code | 44 | 27 | 12 | 3 | +9 |
| test_v5 oas_code | 42 | 13 | 8 | 4 | +4 |
| test_v5 oas_code | 43 | 36 | 17 | 12 | +5 |
| test_v5 oas_code | 44 | 29 | 13 | 12 | +1 |

### 동률 레코드 (seed 42 규칙 적용)

test_v30 oas_code 합성 제외:

| id | 정답 | s42 | s43 | s44 | 채택 | 사유 |
|---|---|---|---|---|---|---|
| 905507d01b81ba5eb1f0 | owner_match | output_error | owner_match | manual_review_required | output_error | tie_seed42_abstain |

test_v31_supp oas_code:

| id | 정답 | s42 | s43 | s44 | 채택 | 사유 |
|---|---|---|---|---|---|---|
| v4t-chatwoot-9396815365 | membership_required | manual_review_required | role_required | owner_or_admin | manual_review_required | tie_all_differ |
| v4t-chatwoot-078e43f1a5 | membership_required | manual_review_required | membership_required | owner_or_admin | manual_review_required | tie_all_differ |
| v4t-chamilo-386a6eb88b | owner_match | membership_required | owner_match | role_required | membership_required | tie_all_differ |
| v4t-flowise-0ede58cae4 | tenant_match | membership_required | role_required | tenant_match | membership_required | tie_all_differ |
| v4t-flowise-c96b4158a8 | tenant_match | membership_required | role_required | manual_review_required | membership_required | tie_all_differ |
| v4t-flowise-e5ed133463 | tenant_match | manual_review_required | role_required | tenant_match | manual_review_required | tie_all_differ |
| v4t-flowise-8dcd3b5cde | tenant_match | manual_review_required | role_required | membership_required | manual_review_required | tie_all_differ |
| v4t-flowise-9a7ff520ac | tenant_match | membership_required | manual_review_required | output_error | membership_required | tie_after_abstain |
| v4t-flowise-11e232587e | tenant_match | membership_required | manual_review_required | tenant_match | membership_required | tie_all_differ |
| v4t-flowise-58ad7b33a8 | tenant_match | membership_required | output_error | manual_review_required | membership_required | tie_after_abstain |

test_v5 oas_code:

| id | 정답 | s42 | s43 | s44 | 채택 | 사유 |
|---|---|---|---|---|---|---|
| v5t-rocketchat-223b6d8be3 | manual_review_required | owner_match | owner_or_admin | manual_review_required | owner_match | tie_all_differ |
| v5t-rocketchat-29963cbc5b | manual_review_required | owner_match | owner_or_admin | manual_review_required | owner_match | tie_all_differ |
| v5t-rocketchat-2b42fcece3 | manual_review_required | owner_match | manual_review_required | owner_or_admin | owner_match | tie_all_differ |
| v5t-rocketchat-38a3cfd41a | membership_required | owner_or_admin | membership_required | manual_review_required | owner_or_admin | tie_all_differ |
| v5t-rocketchat-ba4b8c9067 | membership_required | owner_match | membership_required | manual_review_required | owner_match | tie_all_differ |
| v5t-rocketchat-63a1732919 | role_required | manual_review_required | role_required | membership_required | manual_review_required | tie_all_differ |
| v5t-rocketchat-a447ce62f1 | role_required | owner_or_admin | manual_review_required | role_required | owner_or_admin | tie_all_differ |
| v5t-rocketchat-c2f1c961aa | role_required | role_required | membership_required | manual_review_required | role_required | tie_all_differ |
| v5t-rocketchat-ff636d6df7 | role_required | manual_review_required | owner_or_admin | role_required | manual_review_required | tie_all_differ |

## 4. 비고

- 다수결은 3 seed 모두의 추론을 요구하므로(추론 비용 3배) 배포 모델(단일 어댑터 s42 GGUF)과 조건이 다르다. 보조 지표로만 기록하며 주지표·발표 수치·판정에 쓰지 않는다.
- 단일 seed 값은 scores_test_v30.json(main_excl_synthetic)·scores_supp.json·scores_test_v5.json의 oas_code v5 값과 같다(같은 예측 파일, 같은 정의).
- 예측 파일: test_v30 oas_code 합성 제외: reports/eval/lora_v5/lora_v5_s42/eval/predictions_oas_code_lora_v5_s42_final.jsonl, reports/eval/lora_v5/lora_v5_s43/eval/predictions_oas_code_lora_v5_s43_final.jsonl, reports/eval/lora_v5/lora_v5_s44/eval/predictions_oas_code_lora_v5_s44_final.jsonl; test_v31_supp oas_code: reports/eval/lora_v5/lora_v5_s42/eval/supp_predictions_oas_code_lora_v5_s42_final.jsonl, reports/eval/lora_v5/lora_v5_s43/eval/supp_predictions_oas_code_lora_v5_s43_final.jsonl, reports/eval/lora_v5/lora_v5_s44/eval/supp_predictions_oas_code_lora_v5_s44_final.jsonl; test_v5 oas_code: reports/eval/lora_v5/lora_v5_s42/eval/v5test_predictions_oas_code_lora_v5_s42_final.jsonl, reports/eval/lora_v5/lora_v5_s43/eval/v5test_predictions_oas_code_lora_v5_s43_final.jsonl, reports/eval/lora_v5/lora_v5_s44/eval/v5test_predictions_oas_code_lora_v5_s44_final.jsonl
- 정답 해시: test_v30 9bd47216575afc60…, test_v31_supp 803d914902c7ca20…, test_v5 7b8e4a940967ec47… (manifest 57fd384f46e89e90…). 원자료 scores_ensemble_vote.json(레코드별 다수결 label 포함). 생성 scripts/eval_ensemble_vote_v5.py.
