# 보조 지표 — 세 test 셋 합산 712건 (test_v30 oas_code 합성 제외 207 + test_v31_supp oas_code 222 + test_v5 oas_code 283)

사용자 결정 2026-10-31(C-5 수용·마무리 3항). 주지표(test_v30 207건)는 그대로이고 이 표는 보조 지표다. 정의는 scripts/eval_combined_v5.py 머리말(7-class macro-F1은 support>0 label 평균 — 712건에는 7 label 모두 support 있음; 구체 정밀도·재현율은 eval_v30.py concrete()와 동일). 기존 예측 파일 재채점, 재추론 없음. base 1회, v4·v5는 3 seed 평균 ± 표본 표준편차.

정답 support(712): public 79, role_required 189, membership_required 88, tenant_match 55, owner_match 161, owner_or_admin 44, manual_review_required 96

## 합산 712건

| 모델 | macro-F1(7종) | 정확도 | 구체 정밀도 | 구체 재현율 | 구체 응답률 | manual 비율 | 출력 오류(seed별) |
|---|---:|---:|---:|---:|---:|---:|---|
| base | 0.147 | 0.275 | 0.388 | 0.317 | 0.815 | 2.0% | 111 |
| v4 | 0.469 ± 0.013 | 0.513 ± 0.019 | 0.698 ± 0.008 | 0.534 ± 0.020 | 0.765 ± 0.036 | 24.4 ± 2.8% | 12 / 10 / 5 |
| v5 | 0.521 ± 0.016 | 0.571 ± 0.013 | 0.744 ± 0.007 | 0.601 ± 0.017 | 0.808 ± 0.026 | 21.3 ± 2.3% | 5 / 1 / 5 |

## label별 F1 (합산 712)

| 모델 | public (79) | role_required (189) | membership_required (88) | tenant_match (55) | owner_match (161) | owner_or_admin (44) | manual_review_required (96) |
|---|---:|---:|---:|---:|---:|---:|---:|
| base | 0.517 | 0.419 | 0.000 | 0.000 | 0.078 | 0.000 | 0.018 |
| v4 | 0.588 ± 0.105 | 0.571 ± 0.001 | 0.506 ± 0.016 | 0.276 ± 0.099 | 0.727 ± 0.006 | 0.344 ± 0.033 | 0.272 ± 0.040 |
| v5 | 0.716 ± 0.034 | 0.671 ± 0.024 | 0.588 ± 0.070 | 0.235 ± 0.043 | 0.720 ± 0.007 | 0.420 ± 0.004 | 0.294 ± 0.010 |

## 셋별 기여 (같은 정의로 셋 안에서 계산)

| 모델 | 셋 | n | macro-F1 | 정확도 | 구체 정밀도 | 구체 재현율 | manual 비율 |
|---|---|---:|---:|---:|---:|---:|---:|
| base | test_v30_207 | 207 | 0.197 | 0.319 | 0.353 | 0.316 | 6.8% |
| base | test_v31_supp | 222 | 0.048 | 0.099 | 0.172 | 0.115 | 0.0% |
| base | test_v5 | 283 | 0.238 | 0.382 | 0.568 | 0.495 | 0.0% |
| v4 | test_v30_207 | 207 | 0.356 ± 0.045 | 0.560 ± 0.065 | 0.811 ± 0.025 | 0.558 ± 0.065 | 29.8 ± 5.6% |
| v4 | test_v31_supp | 222 | 0.448 ± 0.030 | 0.377 ± 0.016 | 0.522 ± 0.034 | 0.396 ± 0.024 | 23.3 ± 5.0% |
| v4 | test_v5 | 283 | 0.582 ± 0.016 | 0.585 ± 0.012 | 0.751 ± 0.012 | 0.631 ± 0.007 | 21.4 ± 1.1% |
| v5 | test_v30_207 | 207 | 0.374 ± 0.010 | 0.568 ± 0.010 | 0.796 ± 0.025 | 0.566 ± 0.010 | 28.2 ± 2.3% |
| v5 | test_v31_supp | 222 | 0.485 ± 0.026 | 0.419 ± 0.039 | 0.561 ± 0.007 | 0.446 ± 0.042 | 20.7 ± 5.5% |
| v5 | test_v5 | 283 | 0.683 ± 0.016 | 0.691 ± 0.007 | 0.845 ± 0.009 | 0.769 ± 0.003 | 16.6 ± 1.6% |

- 주의: 셋별 macro-F1은 그 셋에 support가 있는 label만 평균하므로(test_v30 207은 5종, supp 6종, test_v5 6종) 합산 7종 macro-F1과 직접 비교하지 않는다. test_v30 207의 값은 scores_test_v30.json main_excl_synthetic과 같고, supp·test_v5 값은 scores_supp.json·scores_test_v5.json과 같다.
- 예측 파일: base_qwen_runpod: reports/eval/lora_v4/base_qwen_runpod/eval/predictions_oas_code_base_qwen_runpod.jsonl, reports/eval/lora_v4/base_qwen_runpod/eval/supp_predictions_oas_code_base_qwen_runpod.jsonl, reports/eval/lora_v5/base_qwen_runpod/eval/v5test_predictions_oas_code_base_qwen_runpod.jsonl; lora_v4_s42_final: reports/eval/lora_v4/lora_v4_s42/eval/predictions_oas_code_lora_v4_s42_final.jsonl, reports/eval/lora_v4/lora_v4_s42/eval/supp_predictions_oas_code_lora_v4_s42_final.jsonl, reports/eval/lora_v5/lora_v4_s42/eval/v5test_predictions_oas_code_lora_v4_s42_final.jsonl; lora_v4_s43_final: reports/eval/lora_v4/lora_v4_s43/eval/predictions_oas_code_lora_v4_s43_final.jsonl, reports/eval/lora_v4/lora_v4_s43/eval/supp_predictions_oas_code_lora_v4_s43_final.jsonl, reports/eval/lora_v5/lora_v4_s43/eval/v5test_predictions_oas_code_lora_v4_s43_final.jsonl; lora_v4_s44_final: reports/eval/lora_v4/lora_v4_s44/eval/predictions_oas_code_lora_v4_s44_final.jsonl, reports/eval/lora_v4/lora_v4_s44/eval/supp_predictions_oas_code_lora_v4_s44_final.jsonl, reports/eval/lora_v5/lora_v4_s44/eval/v5test_predictions_oas_code_lora_v4_s44_final.jsonl; lora_v5_s42_final: reports/eval/lora_v5/lora_v5_s42/eval/predictions_oas_code_lora_v5_s42_final.jsonl, reports/eval/lora_v5/lora_v5_s42/eval/supp_predictions_oas_code_lora_v5_s42_final.jsonl, reports/eval/lora_v5/lora_v5_s42/eval/v5test_predictions_oas_code_lora_v5_s42_final.jsonl; lora_v5_s43_final: reports/eval/lora_v5/lora_v5_s43/eval/predictions_oas_code_lora_v5_s43_final.jsonl, reports/eval/lora_v5/lora_v5_s43/eval/supp_predictions_oas_code_lora_v5_s43_final.jsonl, reports/eval/lora_v5/lora_v5_s43/eval/v5test_predictions_oas_code_lora_v5_s43_final.jsonl; lora_v5_s44_final: reports/eval/lora_v5/lora_v5_s44/eval/predictions_oas_code_lora_v5_s44_final.jsonl, reports/eval/lora_v5/lora_v5_s44/eval/supp_predictions_oas_code_lora_v5_s44_final.jsonl, reports/eval/lora_v5/lora_v5_s44/eval/v5test_predictions_oas_code_lora_v5_s44_final.jsonl
- 정답 해시: test_v30 9bd47216575afc60…, test_v31_supp 803d914902c7ca20…, test_v5 7b8e4a940967ec47… (manifest 57fd384f46e89e90…). supp 정답·예측 파일은 코드 본문 비공개로 .gitignore.
