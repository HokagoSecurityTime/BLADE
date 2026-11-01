# eval-def v2 재계산 — LoRA v1 4개 조합 (test_v30, 예측 파일 재사용, 추론 없음)

구간(reports/eval_v30_redef/segments.json): 전체 269 · 합성 58 · 취약 route_only 109 · 취약 repository_spec 102 · security declared 64 · oas 주지표(route_only 제외) 160. test_v30.jsonl은 불변. 정의 변경 내용은 AGENTS.md '평가 정의 eval-def v2'.

## 1. 구 정의(v1) vs 신 정의(v2) 비교

주지표 macro-F1은 support 있는 label 평균. 신 정의 oas 주지표는 route_only 109건 제외(160건), oas_code는 전체 265건(정답 변경 없음). "합성 제외"는 주지표에서 합성 58건을 뺀 값(oas 102건 = repository_spec, oas_code 207건). public 오판 신 정의 = declared ∧ 예측 public ∧ 정답≠public, 분모 declared ∧ 정답≠public(47건). 구체 응답 정밀도/재현율 = 정답이 구체 label인 건 중 구체로 답한 비율의 정확도 / 전체 대비 정답률.

| 조건 | 모델 | macro-F1 구(전체) | macro-F1 신(주지표) | 신·합성 제외 | 합성 58만 | manual 구 | manual 신(주지표) | public 오판 구 | public 오판 신 | 구체 P/R 구 | 구체 P/R 신 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| oas | base_qwen_runpod | 0.5671 | 0.7066 | 0.2867 | 0.9413 | 27.9% | 12.5% | 28/64 | 15/47 | 0.5404 / 0.3425 (응답률 0.6339) | 0.625 / 0.4795 (응답률 0.7671) |
| oas | lora_v4_s42_final | 0.6101 | 0.7456 | 0.4514 | 1.0 | 65.8% | 44.4% | 8/64 | 0/47 | 0.9239 / 0.3346 (응답률 0.3622) | 0.9213 / 0.5616 (응답률 0.6096) |
| oas | lora_v4_s43_final | 0.6059 | 0.7449 | 0.4565 | 1.0 | 65.1% | 42.5% | 9/64 | 1/47 | 0.883 / 0.3268 (응답률 0.3701) | 0.8804 / 0.5548 (응답률 0.6301) |
| oas | lora_v4_s44_final | 0.4765 | 0.6082 | 0.4817 | 0.8571 | 58.4% | 38.8% | 12/64 | 0/47 | 0.8077 / 0.3307 (응답률 0.4094) | 0.8556 / 0.5274 (응답률 0.6164) |
| oas | lora_v5_s42_final | 0.6251 | 0.7574 | 0.5036 | 0.9796 | 60.6% | 37.5% | 12/64 | 0/47 | 0.8932 / 0.3622 (응답률 0.4055) | 0.8866 / 0.589 (응답률 0.6644) |
| oas | lora_v5_s43_final | 0.5918 | 0.7279 | 0.4632 | 0.9905 | 65.4% | 43.8% | 7/64 | 0/47 | 0.913 / 0.3307 (응답률 0.3622) | 0.9101 / 0.5548 (응답률 0.6096) |
| oas | lora_v5_s44_final | 0.5991 | 0.7333 | 0.4196 | 1.0 | 68.4% | 48.1% | 8/64 | 0/47 | 0.9294 / 0.311 (응답률 0.3346) | 0.9277 / 0.5274 (응답률 0.5685) |
| oas_code | base_qwen_runpod | 0.6537 | 0.6537 | 0.1967 | 0.9712 | 9.8% | 9.8% | 32/64 | 17/47 | 0.4758 / 0.432 (응답률 0.908) | 0.4758 / 0.432 (응답률 0.908) |
| oas_code | lora_v4_s42_final | 0.7081 | 0.7081 | 0.3796 | 0.9796 | 27.9% | 27.9% | 11/64 | 1/47 | 0.875 / 0.644 (응답률 0.736) | 0.875 / 0.644 (응답률 0.736) |
| oas_code | lora_v4_s43_final | 0.6988 | 0.6988 | 0.3042 | 0.9905 | 33.2% | 33.2% | 4/64 | 0/47 | 0.8412 / 0.572 (응답률 0.68) | 0.8412 / 0.572 (응답률 0.68) |
| oas_code | lora_v4_s44_final | 0.7402 | 0.7402 | 0.3856 | 1.0 | 24.5% | 24.5% | 12/64 | 0/47 | 0.85 / 0.68 (응답률 0.8) | 0.85 / 0.68 (응답률 0.8) |
| oas_code | lora_v5_s42_final | 0.6947 | 0.6947 | 0.3661 | 0.9905 | 25.3% | 25.3% | 16/64 | 3/47 | 0.8187 / 0.632 (응답률 0.772) | 0.8187 / 0.632 (응답률 0.772) |
| oas_code | lora_v5_s43_final | 0.6943 | 0.6943 | 0.386 | 0.9496 | 27.9% | 27.9% | 15/64 | 2/47 | 0.8503 / 0.636 (응답률 0.748) | 0.8503 / 0.636 (응답률 0.748) |
| oas_code | lora_v5_s44_final | 0.7109 | 0.7109 | 0.3711 | 0.9905 | 28.7% | 28.7% | 12/64 | 1/47 | 0.8548 / 0.636 (응답률 0.744) | 0.8548 / 0.636 (응답률 0.744) |

합성 58건 주석: test 합성 58건 중 56건이 train 합성과 같은 경로 템플릿, 43건은 정규화한 인가 검사 줄까지 동일(reports/data_v1_audit.md 4절). 합성 구간 수치는 일반화 근거로 쓰지 않는다.

## 2. oas 보조지표 — route_only 109건(명세 없음), manual 예측을 정답으로 인정

| 모델 | N | 정확도(manual 인정) | macro-F1(manual 인정) | manual 예측 비율 | 정확도(엄격, 구 정의) | macro-F1(엄격) |
|---|---:|---:|---:|---:|---:|---:|
| base_qwen_runpod | 109 | 66.1% | 0.3015 | 50.5% | 16.5% | 0.1003 |
| lora_v4_s42_final | 109 | 100.0% | 1.0 | 97.2% | 3.7% | 0.0482 |
| lora_v4_s43_final | 109 | 100.0% | 1.0 | 98.2% | 2.8% | 0.0345 |
| lora_v4_s44_final | 109 | 93.6% | 0.4167 | 87.2% | 7.3% | 0.0778 |
| lora_v5_s42_final | 109 | 100.0% | 1.0 | 94.5% | 6.4% | 0.0838 |
| lora_v5_s43_final | 109 | 100.0% | 1.0 | 97.2% | 3.7% | 0.0482 |
| lora_v5_s44_final | 109 | 100.0% | 1.0 | 98.2% | 2.8% | 0.0345 |

## 3. public 오판 재정의 효과 — 구 정의로 잡힌 건 중 정답이 실제 public인 건

| 조건 | 모델 | 구 정의 건수 | 그중 정답이 public(오판 아님) | 신 정의 건수/분모 | 정답 public인 id |
|---|---|---:|---:|---:|---:|
| oas | base_qwen_runpod | 28 | 13 | 15/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, 860383f68102b772bb99, 7a19e5a3a9eb0d5947f3, c085f5d6b9f87dd6d4a1, 324601a8dc9e9ea969bb, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v4_s42_final | 8 | 8 | 0/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, 7a19e5a3a9eb0d5947f3, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v4_s43_final | 9 | 8 | 1/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, 7a19e5a3a9eb0d5947f3, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v4_s44_final | 12 | 12 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v5_s42_final | 12 | 12 | 0/47 | 860383f68102b772bb99, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v5_s43_final | 7 | 7 | 0/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v5_s44_final | 8 | 8 | 0/47 | d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | base_qwen_runpod | 32 | 15 | 17/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, 860383f68102b772bb99, 7a19e5a3a9eb0d5947f3, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v4_s42_final | 11 | 10 | 1/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, 7e3f8c20d798e8b34143, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v4_s43_final | 4 | 4 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v4_s44_final | 12 | 12 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v5_s42_final | 16 | 13 | 3/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v5_s43_final | 15 | 13 | 2/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, 860383f68102b772bb99, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v5_s44_final | 12 | 11 | 1/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |

신 정의 오판 id:

- oas / base_qwen_runpod: 759eb32d69ab1820e44d, aae57acca0e9317e81c1, d93acb187b6c273464f0, 15af38ebe8faf15c930f, 6bca6097b26cf226f405, cdd3d3e140b0b509bcd3, a0f5f54a6d4c22bb18e7, af6e2ae1b29132ee1d77, d42ed128370ce4d3ce71, dcc8f1be82d40ee3d5cf, fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219, 956a6feb1b1f65eb5a9a, 0b0918598294090d14c3
- oas / lora_v4_s42_final: 없음
- oas / lora_v4_s43_final: d8c5cf5eb0bfbd488219
- oas / lora_v4_s44_final: 없음
- oas / lora_v5_s42_final: 없음
- oas / lora_v5_s43_final: 없음
- oas / lora_v5_s44_final: 없음
- oas_code / base_qwen_runpod: 759eb32d69ab1820e44d, ff8c5eda79000fa6687f, b3906a959a0b669047ba, aae57acca0e9317e81c1, acdc8447219278841824, d93acb187b6c273464f0, d0afe4b052514b189dfa, 5928631c56d36ced026a, c3203410c4072686beaa, 6bca6097b26cf226f405, dcc8f1be82d40ee3d5cf, c917e3e10dce94cc245c, fc9dac901542ca88d688, 5a72ac6384c12b441687, 4de2f44349d88f3d6b3a, d8c5cf5eb0bfbd488219, 0b0918598294090d14c3
- oas_code / lora_v4_s42_final: d8c5cf5eb0bfbd488219
- oas_code / lora_v4_s43_final: 없음
- oas_code / lora_v4_s44_final: 없음
- oas_code / lora_v5_s42_final: fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219
- oas_code / lora_v5_s43_final: 0797f5bb072770d50159, fc9dac901542ca88d688
- oas_code / lora_v5_s44_final: d8c5cf5eb0bfbd488219

## 4. 신 정의 주지표 label별 P/R/F1 (support 포함)

### oas / base_qwen_runpod — 주지표 160건, macro-F1 0.7066 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.4861 | 0.8333 | 0.614 |
| role_required | 22 | 0.6154 | 0.3636 | 0.4571 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 1.0 | 0.1452 | 0.2535 |
| owner_or_admin | 8 | 1.0 | 0.75 | 0.8571 |
| manual_review_required | 14 | 0.65 | 0.9286 | 0.7647 |

### oas / lora_v4_s42_final — 주지표 160건, macro-F1 0.7456 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.5476 | 0.7077 |
| role_required | 22 | 0.7692 | 0.4545 | 0.5714 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8788 | 0.4677 | 0.6105 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1972 | 1.0 | 0.3294 |

### oas / lora_v4_s43_final — 주지표 160건, macro-F1 0.7449 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.9167 | 0.5238 | 0.6667 |
| role_required | 22 | 0.8462 | 0.5 | 0.6286 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8 | 0.4516 | 0.5773 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.2059 | 1.0 | 0.3415 |

### oas / lora_v4_s44_final — 주지표 160건, macro-F1 0.6082 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.6667 | 0.8 |
| role_required | 22 | 0.55 | 0.5 | 0.5238 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 0.0 | 0.0 | 0.0 |
| owner_match | 62 | 0.8667 | 0.4194 | 0.5652 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.2258 | 1.0 | 0.3684 |

### oas / lora_v5_s42_final — 주지표 160건, macro-F1 0.7574 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.9643 | 0.6429 | 0.7714 |
| role_required | 22 | 0.6111 | 0.5 | 0.55 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.9032 | 0.4516 | 0.6022 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.2333 | 1.0 | 0.3784 |

### oas / lora_v5_s43_final — 주지표 160건, macro-F1 0.7279 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.4524 | 0.623 |
| role_required | 22 | 0.7857 | 0.5 | 0.6111 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8857 | 0.5 | 0.6392 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.2 | 1.0 | 0.3333 |

### oas / lora_v5_s44_final — 주지표 160건, macro-F1 0.7333 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.5238 | 0.6875 |
| role_required | 22 | 0.8333 | 0.4545 | 0.5882 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8621 | 0.4032 | 0.5495 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1818 | 1.0 | 0.3077 |

### oas_code / base_qwen_runpod — 주지표 265건, macro-F1 0.6537 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.4296 | 0.8788 | 0.5771 |
| role_required | 47 | 0.2833 | 0.3617 | 0.3178 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 1.0 | 0.114 | 0.2047 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.5 | 0.8667 | 0.6341 |

### oas_code / lora_v4_s42_final — 주지표 265건, macro-F1 0.7081 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8718 | 0.5152 | 0.6476 |
| role_required | 47 | 0.875 | 0.4468 | 0.5915 |
| membership_required | 4 | 0.5714 | 1.0 | 0.7273 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8776 | 0.7544 | 0.8113 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.2027 | 1.0 | 0.3371 |

### oas_code / lora_v4_s43_final — 주지표 265건, macro-F1 0.6988 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.7857 | 0.3333 | 0.4681 |
| role_required | 47 | 0.75 | 0.383 | 0.507 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8469 | 0.7281 | 0.783 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.1705 | 1.0 | 0.2913 |

### oas_code / lora_v4_s44_final — 주지표 265건, macro-F1 0.7402 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8537 | 0.5303 | 0.6542 |
| role_required | 47 | 0.8148 | 0.4681 | 0.5946 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8378 | 0.8158 | 0.8267 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.2308 | 1.0 | 0.375 |

### oas_code / lora_v5_s42_final — 주지표 265건, macro-F1 0.6947 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.7097 | 0.6667 | 0.6875 |
| role_required | 47 | 0.8261 | 0.4043 | 0.5429 |
| membership_required | 4 | 0.5 | 1.0 | 0.6667 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8929 | 0.6579 | 0.7576 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.2239 | 1.0 | 0.3659 |

### oas_code / lora_v5_s43_final — 주지표 265건, macro-F1 0.6943 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8113 | 0.6515 | 0.7227 |
| role_required | 47 | 0.84 | 0.4468 | 0.5833 |
| membership_required | 4 | 0.75 | 0.75 | 0.75 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8571 | 0.6842 | 0.761 |
| owner_or_admin | 11 | 1.0 | 0.5455 | 0.7059 |
| manual_review_required | 15 | 0.2027 | 1.0 | 0.3371 |

### oas_code / lora_v5_s44_final — 주지표 265건, macro-F1 0.7109 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.7872 | 0.5606 | 0.6549 |
| role_required | 47 | 0.9048 | 0.4043 | 0.5588 |
| membership_required | 4 | 0.6667 | 1.0 | 0.8 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8646 | 0.7281 | 0.7905 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.1974 | 1.0 | 0.3297 |


원자료: scores.json. (모델 집합이 base_v301/lora_v1이 아니므로 5절 결론 생략)
