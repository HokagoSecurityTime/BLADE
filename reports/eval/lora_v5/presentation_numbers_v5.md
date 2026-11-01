# 발표용 수치 표 — LoRA v5 (C-5 수용·마무리, 2026-10-31)

**발표 주 수치는 LoRA v5(data-v5, 3 seed)다**(사용자 결정 2026-10-31 "C-5 수용 및 마무리" 2항; 이전 "v4 원본 유지" 문구를 대체). v4는 비교 기준으로 함께 적는다. 모든 값은 기본 디코딩, 3 seed(42·43·44) 평균 ± 표본 표준편차(base는 1회), HF 어댑터 평가(배포용 GGUF 수치는 4절 별도). 근거 파일은 각 표 아래. 수치는 presentation_numbers_v5.json에서 그대로 읽을 수 있다(생성 scripts/presentation_numbers_v5.py).

## 1. test_v30 oas_code, 합성 제외 207건 (eval-def v2 주지표)

| 모델 | 구체 정밀도 | 구체 재현율 | macro-F1 | manual 비율(207) | public 오판(신 정의, /35) |
|---|---:|---:|---:|---:|---:|
| base (qwen2.5-7b-instruct, 미학습) | 0.353 | 0.316 | 0.197 | 6.8% | 17 |
| LoRA v4 (data-v4, 비교 기준) | 0.811 ± 0.025 | 0.558 ± 0.065 | 0.356 ± 0.045 | 29.8 ± 5.6% | 0.3 ± 0.6 |
| **LoRA v5 (data-v5, 주 수치)** | 0.796 ± 0.025 | 0.566 ± 0.010 | 0.374 ± 0.010 | 28.2 ± 2.3% | 2.0 ± 1.0 |

- 근거: reports/eval/lora_v5/scores_test_v30.json (condition oas_code, eval_def v2, main_excl_synthetic: concrete.precision/recall, macro_f1, manual_ratio; public 오판은 public_misjudge_new.ids에서 합성 id(reports/eval_v30_redef/segments.json 'synthetic' 58건)를 뺀 건수, 분모 35 = 207건 중 declared ∧ 정답≠public). 표 원본 reports/eval/lora_v5/eval_v30.md. 예측 파일 base·v4 reports/eval/lora_v4/<run>/eval/predictions_oas_code_*.jsonl, v5 reports/eval/lora_v5/lora_v5_s4*/eval/predictions_oas_code_*.jsonl. 채점기 scripts/eval_v30.py. 정답 datasets/blade/processed/test_v30.jsonl(SHA 9bd47216…).
- public 오판 건(id): base_qwen_runpod: 759eb32d69ab1820e44d, ff8c5eda79000fa6687f, b3906a959a0b669047ba, aae57acca0e9317e81c1, acdc8447219278841824, d93acb187b6c273464f0, d0afe4b052514b189dfa, 5928631c56d36ced026a, c3203410c4072686beaa, 6bca6097b26cf226f405, dcc8f1be82d40ee3d5cf, c917e3e10dce94cc245c, fc9dac901542ca88d688, 5a72ac6384c12b441687, 4de2f44349d88f3d6b3a, d8c5cf5eb0bfbd488219, 0b0918598294090d14c3; lora_v4_s42_final: d8c5cf5eb0bfbd488219; lora_v4_s43_final: 없음; lora_v4_s44_final: 없음; lora_v5_s42_final: fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219; lora_v5_s43_final: 0797f5bb072770d50159, fc9dac901542ca88d688; lora_v5_s44_final: d8c5cf5eb0bfbd488219
- **manual 비율 분모 확인(2항 d)**: v4 test_v30 manual 비율은 분모에 따라 두 값이 있다. 합성 제외 207건 기준 29.8 ± 5.6%(seed별 29.0% / 35.8% / 24.6%; supplementary_metrics.md의 'manual 예측률' 0.298과 이 표), 합성 포함 265건 기준 28.6 ± 4.4%(seed별 27.9% / 33.2% / 24.5%; lora_v4_report.md·lora_v5_report.md 1절 표의 'manual 비율(265)'). 둘 다 같은 예측 파일(scores_test_v30.json main vs main_excl_synthetic)이며 차이는 합성 58건(세 seed 모두 manual 24.1%)이 들어가느냐뿐이다. v5도 같다: 207 기준 28.2 ± 2.3%, 265 기준 27.3 ± 1.8%. 발표 표는 주지표 조건(207)으로 통일한다.

## 2. test_v5 oas_code 283건 (hold-out, 별도 조건)

| 모델 | macro-F1(6종) | 정확도 | manual 비율 | owner_or_admin F1 (21) | membership_required F1 (33) |
|---|---:|---:|---:|---:|---:|
| base | 0.238 | 0.382 | 0.0% | 0.000 | 0.000 |
| LoRA v4 (비교 기준) | 0.582 ± 0.016 | 0.585 ± 0.012 | 21.4 ± 1.1% | 0.394 ± 0.055 | 0.488 ± 0.022 |
| **LoRA v5 (주 수치)** | 0.683 ± 0.016 | 0.691 ± 0.007 | 16.6 ± 1.6% | 0.536 ± 0.031 | 0.589 ± 0.048 |

프로젝트별 정확도:

| 모델 | rocketchat (157) | ghost (69) | umami (57) |
|---|---:|---:|---:|
| base | 0.363 | 0.522 | 0.263 |
| LoRA v4 | 0.522 ± 0.006 | 0.691 ± 0.017 | 0.632 ± 0.046 |
| **LoRA v5** | 0.656 ± 0.013 | 0.758 ± 0.008 | 0.708 ± 0.066 |

- **macro-F1의 tenant_match 처리**: scripts/eval_test_v5.py는 그 셋에 정답 support > 0인 label만 평균한다. test_v5에는 tenant_match 정답이 0건이므로 macro-F1은 6종(public·role_required·membership_required·owner_match·owner_or_admin·manual_review_required) 평균이며, tenant_match 예측(FP)은 정확도와 다른 label의 재현율에만 반영된다. 7종으로 나누면(tenant_match F1 = 0) 값은 6/7배가 된다.
- 근거: reports/eval/lora_v5/scores_test_v5.json (condition oas_code: macro_f1, accuracy, manual_ratio, per_label.owner_or_admin.f1, per_label.membership_required.f1, per_project.<p>.accuracy), 표 원본 reports/eval/lora_v5/eval_test_v5.md, 예측 reports/eval/lora_v5/<run>/eval/v5test_predictions_oas_code_*.jsonl, 정답 datasets/blade/processed/test_v5.jsonl(SHA 7b8e4a94…, manifest datasets/blade/processed/data_v5/test_v5_manifest.json 57fd384f…), 채점기 scripts/eval_test_v5.py. 판정 reports/eval/lora_v5/lora_v5_report.md 3b절. 한계: membership_required 33건 중 28건 Rocket.Chat, owner_or_admin support 21.

## 3. test_v31_supp oas_code 222건 (별도 조건)

| 모델 | macro-F1(7종) | 정확도 | manual 비율 | public 오판(신 정의, /191) |
|---|---:|---:|---:|---:|
| base | 0.048 | 0.099 | 0.0% | 15 |
| LoRA v4 (비교 기준) | 0.448 ± 0.030 | 0.377 ± 0.016 | 23.3 ± 5.0% | 0.3 ± 0.6 |
| **LoRA v5 (주 수치)** | 0.485 ± 0.026 | 0.419 ± 0.039 | 20.7 ± 5.5% | 0.0 ± 0.0 |

- public 오판 건(id, seed별): base_qwen_runpod: v4t-chatwoot-a7959f6c9f, v4t-chatwoot-bd801cfc57, v4t-chatwoot-03a9708adc, v4t-chatwoot-f8a59a7139, v4t-chatwoot-8e5b8fab5d, v4t-chatwoot-bfc74394f6, v4t-flowise-0ddedb6fa0, v4t-flowise-710e06fe88, v4t-flowise-a72fabf788, v4t-flowise-f8f20b3606, v4t-flowise-4af3d5d1a4, v4t-flowise-ff9e6ab2b4, v4t-multitenant_lab-b6b35fc009, v4t-multitenant_lab-4871532f96, v4t-multitenant_lab-8119383409; lora_v4_s42_final: v4t-flowise-0ddedb6fa0; lora_v4_s43_final: 없음; lora_v4_s44_final: 없음; lora_v5_s42_final: 없음; lora_v5_s43_final: 없음; lora_v5_s44_final: 없음
- 근거: reports/eval/lora_v5/scores_supp.json (condition oas_code: macro_f1, accuracy, manual_ratio; macro-F1은 scripts/eval_v31_supp.py 규칙상 support>0 label 평균이며 supp는 7 label 모두 정답이 있어(public 2 포함) 7종 평균; supplementary_metrics.md의 'support ≥ 10' 6종 macro-F1과는 다른 값), 표 원본 reports/eval/lora_v5/eval_supp.md, 채점기 scripts/eval_v31_supp.py. public 오판은 이 스크립트가 예측 파일과 정답 파일(security_state)로 재계산: declared 192 중 정답 public 1건을 뺀 191건에서 예측 public인 건(정의 reports/eval/lora_v4/supplementary_metrics.md 5번과 동일; v4 1/0/0은 그 문서 값과 일치). 정답 datasets/blade/processed/data_v4/test_v31_supp.jsonl(SHA 803d9149…, 코드 본문 비공개 .gitignore). 예측 base·v4 reports/eval/lora_v4/<run>/eval/supp_predictions_oas_code_*.jsonl, v5 reports/eval/lora_v5/lora_v5_s4*/eval/supp_predictions_oas_code_*.jsonl(모두 .gitignore). 한계: label이 프로젝트에 몰려 있다(membership 50/55 Chatwoot, tenant 52/55 Flowise, owner_or_admin 19/20 Chamilo).

## 4. 보조 지표 — 세 셋 합산 712건 (207 + 222 + 283)

| 모델 | macro-F1(7종) | 정확도 | 구체 정밀도 | 구체 재현율 | manual 비율 |
|---|---:|---:|---:|---:|---:|
| base | 0.147 | 0.275 | 0.388 | 0.317 | 2.0% |
| LoRA v4 (비교 기준) | 0.469 ± 0.013 | 0.513 ± 0.019 | 0.698 ± 0.008 | 0.534 ± 0.020 | 24.4 ± 2.8% |
| **LoRA v5 (주 수치)** | 0.521 ± 0.016 | 0.571 ± 0.013 | 0.744 ± 0.007 | 0.601 ± 0.017 | 21.3 ± 2.3% |

- 근거: reports/eval/lora_v5/scores_combined_712.json (scripts/eval_combined_v5.py, 표 원본 reports/eval/lora_v5/eval_combined_712.md). 7 label 모두 support가 있어 7종 평균. 구체 정밀도·재현율은 eval_v30.py concrete()와 같은 정의(정답 구체 건 중 응답한 건의 정확도 / 정답 구체 건 전체 대비 일치). 보조 지표이며 주지표(1절)는 바뀌지 않는다.

## 5. 배포 모델 (GGUF Q4_K_M, s42) — 변환 동등성 확인용 별도 표기

- reports/eval/lora_v5_gguf/equivalence_check.md: test_v30 oas_code에서 GGUF와 HF s42 final 비교(v4 허용 폭 기준 수용 확정 2026-10-31). 위 1~4절 수치는 HF 3-seed 평가이며 배포 GGUF의 보류율(18.5%)은 평가 모델(s42 HF 25.3%)보다 낮다(보고서 한계 절).
