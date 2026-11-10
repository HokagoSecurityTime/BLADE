# eval-def v2 재계산 — LoRA v1 4개 조합 (test_v30, 예측 파일 재사용, 추론 없음)

구간(reports/eval_v30_redef/segments.json): 전체 269 · 합성 58 · 취약 route_only 109 · 취약 repository_spec 102 · security declared 64 · oas 주지표(route_only 제외) 160. test_v30.jsonl은 불변. 정의 변경 내용은 AGENTS.md '평가 정의 eval-def v2'.

## 1. 구 정의(v1) vs 신 정의(v2) 비교

주지표 macro-F1은 support 있는 label 평균. 신 정의 oas 주지표는 route_only 109건 제외(160건), oas_code는 전체 265건(정답 변경 없음). "합성 제외"는 주지표에서 합성 58건을 뺀 값(oas 102건 = repository_spec, oas_code 207건). public 오판 신 정의 = declared ∧ 예측 public ∧ 정답≠public, 분모 declared ∧ 정답≠public(47건). 구체 응답 정밀도/재현율 = 정답이 구체 label인 건 중 구체로 답한 비율의 정확도 / 전체 대비 정답률.

| 조건 | 모델 | macro-F1 구(전체) | macro-F1 신(주지표) | 신·합성 제외 | 합성 58만 | manual 구 | manual 신(주지표) | public 오판 구 | public 오판 신 | 구체 P/R 구 | 구체 P/R 신 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| oas | base_qwen14b_runpod | 0.5889 | 0.7082 | 0.414 | 0.8836 | 62.1% | 41.9% | 15/64 | 3/47 | 0.8085 / 0.2992 (응답률 0.3701) | 0.8353 / 0.4863 (응답률 0.5822) |
| oas | lora_v5_s42_final | 0.6251 | 0.7574 | 0.5036 | 0.9796 | 60.6% | 37.5% | 12/64 | 0/47 | 0.8932 / 0.3622 (응답률 0.4055) | 0.8866 / 0.589 (응답률 0.6644) |
| oas | lora_v5_s43_final | 0.5918 | 0.7279 | 0.4632 | 0.9905 | 65.4% | 43.8% | 7/64 | 0/47 | 0.913 / 0.3307 (응답률 0.3622) | 0.9101 / 0.5548 (응답률 0.6096) |
| oas | lora_v5_s44_final | 0.5991 | 0.7333 | 0.4196 | 1.0 | 68.4% | 48.1% | 8/64 | 0/47 | 0.9294 / 0.311 (응답률 0.3346) | 0.9277 / 0.5274 (응답률 0.5685) |
| oas | lora_v6c_s42_final | 0.604 | 0.7325 | 0.4908 | 1.0 | 62.8% | 41.9% | 13/64 | 2/47 | 0.87 / 0.3425 (응답률 0.3937) | 0.871 / 0.5548 (응답률 0.637) |
| oas | lora_v6c_s43_final | 0.6001 | 0.744 | 0.5754 | 1.0 | 58.7% | 36.2% | 13/64 | 1/47 | 0.8739 / 0.3819 (응답률 0.437) | 0.8824 / 0.6164 (응답률 0.6986) |
| oas | lora_v6c_s44_final | 0.5638 | 0.6879 | 0.4813 | 1.0 | 58.7% | 37.5% | 11/64 | 0/47 | 0.8108 / 0.3543 (응답률 0.437) | 0.81 / 0.5548 (응답률 0.6849) |
| oas_code | base_qwen14b_runpod | 0.6648 | 0.6648 | 0.2953 | 0.9524 | 30.6% | 30.6% | 15/64 | 5/47 | 0.7062 / 0.5 (응답률 0.708) | 0.7062 / 0.5 (응답률 0.708) |
| oas_code | lora_v5_s42_final | 0.6947 | 0.6947 | 0.3661 | 0.9905 | 25.3% | 25.3% | 16/64 | 3/47 | 0.8187 / 0.632 (응답률 0.772) | 0.8187 / 0.632 (응답률 0.772) |
| oas_code | lora_v5_s43_final | 0.6943 | 0.6943 | 0.386 | 0.9496 | 27.9% | 27.9% | 15/64 | 2/47 | 0.8503 / 0.636 (응답률 0.748) | 0.8503 / 0.636 (응답률 0.748) |
| oas_code | lora_v5_s44_final | 0.7109 | 0.7109 | 0.3711 | 0.9905 | 28.7% | 28.7% | 12/64 | 1/47 | 0.8548 / 0.636 (응답률 0.744) | 0.8548 / 0.636 (응답률 0.744) |
| oas_code | lora_v6c_s42_final | 0.705 | 0.705 | 0.4505 | 1.0 | 22.3% | 22.3% | 15/64 | 2/47 | 0.8683 / 0.712 (응답률 0.82) | 0.8683 / 0.712 (응답률 0.82) |
| oas_code | lora_v6c_s43_final | 0.684 | 0.684 | 0.4223 | 1.0 | 20.8% | 20.8% | 17/64 | 2/47 | 0.8373 / 0.7 (응답률 0.836) | 0.8373 / 0.7 (응답률 0.836) |
| oas_code | lora_v6c_s44_final | 0.6954 | 0.6954 | 0.4449 | 1.0 | 20.4% | 20.4% | 15/64 | 1/47 | 0.8517 / 0.712 (응답률 0.836) | 0.8517 / 0.712 (응답률 0.836) |

합성 58건 주석: test 합성 58건 중 56건이 train 합성과 같은 경로 템플릿, 43건은 정규화한 인가 검사 줄까지 동일(reports/data_v1_audit.md 4절). 합성 구간 수치는 일반화 근거로 쓰지 않는다.

## 2. oas 보조지표 — route_only 109건(명세 없음), manual 예측을 정답으로 인정

| 모델 | N | 정확도(manual 인정) | macro-F1(manual 인정) | manual 예측 비율 | 정확도(엄격, 구 정의) | macro-F1(엄격) |
|---|---:|---:|---:|---:|---:|---:|
| base_qwen14b_runpod | 109 | 96.3% | 0.4286 | 91.7% | 5.5% | 0.0646 |
| lora_v5_s42_final | 109 | 100.0% | 1.0 | 94.5% | 6.4% | 0.0838 |
| lora_v5_s43_final | 109 | 100.0% | 1.0 | 97.2% | 3.7% | 0.0482 |
| lora_v5_s44_final | 109 | 100.0% | 1.0 | 98.2% | 2.8% | 0.0345 |
| lora_v6c_s42_final | 109 | 99.1% | 0.8586 | 93.6% | 6.4% | 0.0839 |
| lora_v6c_s43_final | 109 | 98.2% | 0.4688 | 91.7% | 7.3% | 0.0888 |
| lora_v6c_s44_final | 109 | 98.2% | 0.6389 | 89.9% | 9.2% | 0.1115 |

## 3. public 오판 재정의 효과 — 구 정의로 잡힌 건 중 정답이 실제 public인 건

| 조건 | 모델 | 구 정의 건수 | 그중 정답이 public(오판 아님) | 신 정의 건수/분모 | 정답 public인 id |
|---|---|---:|---:|---:|---:|
| oas | base_qwen14b_runpod | 15 | 12 | 3/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc |
| oas | lora_v5_s42_final | 12 | 12 | 0/47 | 860383f68102b772bb99, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v5_s43_final | 7 | 7 | 0/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v5_s44_final | 8 | 8 | 0/47 | d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v6c_s42_final | 13 | 11 | 2/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v6c_s43_final | 13 | 12 | 1/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, 7a19e5a3a9eb0d5947f3, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v6c_s44_final | 11 | 11 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | base_qwen14b_runpod | 15 | 10 | 5/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, c085f5d6b9f87dd6d4a1, 324601a8dc9e9ea969bb, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, d553cdd9276767f1b1bc |
| oas_code | lora_v5_s42_final | 16 | 13 | 3/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v5_s43_final | 15 | 13 | 2/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, 860383f68102b772bb99, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v5_s44_final | 12 | 11 | 1/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v6c_s42_final | 15 | 13 | 2/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v6c_s43_final | 17 | 15 | 2/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, 860383f68102b772bb99, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v6c_s44_final | 15 | 14 | 1/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |

신 정의 오판 id:

- oas / base_qwen14b_runpod: dcc8f1be82d40ee3d5cf, fc9dac901542ca88d688, 5a72ac6384c12b441687
- oas / lora_v5_s42_final: 없음
- oas / lora_v5_s43_final: 없음
- oas / lora_v5_s44_final: 없음
- oas / lora_v6c_s42_final: fc9dac901542ca88d688, 5a72ac6384c12b441687
- oas / lora_v6c_s43_final: 5a72ac6384c12b441687
- oas / lora_v6c_s44_final: 없음
- oas_code / base_qwen14b_runpod: c3203410c4072686beaa, dcc8f1be82d40ee3d5cf, fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219
- oas_code / lora_v5_s42_final: fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219
- oas_code / lora_v5_s43_final: 0797f5bb072770d50159, fc9dac901542ca88d688
- oas_code / lora_v5_s44_final: d8c5cf5eb0bfbd488219
- oas_code / lora_v6c_s42_final: fc9dac901542ca88d688, 5a72ac6384c12b441687
- oas_code / lora_v6c_s43_final: fc9dac901542ca88d688, 5a72ac6384c12b441687
- oas_code / lora_v6c_s44_final: 5a72ac6384c12b441687

## 4. 신 정의 주지표 label별 P/R/F1 (support 포함)

### oas / base_qwen14b_runpod — 주지표 160건, macro-F1 0.7082 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.8667 | 0.619 | 0.7222 |
| role_required | 22 | 0.6471 | 0.5 | 0.5641 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.7778 | 0.2258 | 0.35 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.194 | 0.9286 | 0.321 |

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

### oas / lora_v6c_s42_final — 주지표 160건, macro-F1 0.7325 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.9286 | 0.619 | 0.7429 |
| role_required | 22 | 0.7222 | 0.5909 | 0.65 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8462 | 0.3548 | 0.5 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.209 | 1.0 | 0.3457 |

### oas / lora_v6c_s43_final — 주지표 160건, macro-F1 0.744 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.9667 | 0.6905 | 0.8056 |
| role_required | 22 | 0.8667 | 0.5909 | 0.7027 |
| membership_required | 4 | 0.5714 | 1.0 | 0.7273 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8235 | 0.4516 | 0.5833 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.2414 | 1.0 | 0.3889 |

### oas / lora_v6c_s44_final — 주지표 160건, macro-F1 0.6879 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.9615 | 0.5952 | 0.7353 |
| role_required | 22 | 0.65 | 0.5909 | 0.619 |
| membership_required | 4 | 0.4 | 1.0 | 0.5714 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8214 | 0.371 | 0.5111 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.2333 | 1.0 | 0.3784 |

### oas_code / base_qwen14b_runpod — 주지표 265건, macro-F1 0.6648 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.7273 | 0.6061 | 0.6612 |
| role_required | 47 | 0.3966 | 0.4894 | 0.4381 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.9545 | 0.3684 | 0.5316 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.1728 | 0.9333 | 0.2917 |

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

### oas_code / lora_v6c_s42_final — 주지표 265건, macro-F1 0.705 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8868 | 0.7121 | 0.7899 |
| role_required | 47 | 0.9032 | 0.5957 | 0.7179 |
| membership_required | 4 | 0.25 | 1.0 | 0.4 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.9432 | 0.7281 | 0.8218 |
| owner_or_admin | 11 | 0.8889 | 0.7273 | 0.8 |
| manual_review_required | 15 | 0.2542 | 1.0 | 0.4054 |

### oas_code / lora_v6c_s43_final — 주지표 265건, macro-F1 0.684 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8197 | 0.7576 | 0.7874 |
| role_required | 47 | 0.9231 | 0.5106 | 0.6575 |
| membership_required | 4 | 0.2 | 1.0 | 0.3333 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.9419 | 0.7105 | 0.81 |
| owner_or_admin | 11 | 0.8889 | 0.7273 | 0.8 |
| manual_review_required | 15 | 0.2545 | 0.9333 | 0.4 |

### oas_code / lora_v6c_s44_final — 주지표 265건, macro-F1 0.6954 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.9556 | 0.6515 | 0.7748 |
| role_required | 47 | 0.9062 | 0.617 | 0.7342 |
| membership_required | 4 | 0.16 | 1.0 | 0.2759 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.9348 | 0.7544 | 0.835 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.2593 | 0.9333 | 0.4058 |


원자료: scores.json. (모델 집합이 base_v301/lora_v1이 아니므로 5절 결론 생략)
