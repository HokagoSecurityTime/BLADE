# eval-def v2 재계산 — LoRA v1 4개 조합 (test_v30, 예측 파일 재사용, 추론 없음)

구간(reports/eval_v30_redef/segments.json): 전체 269 · 합성 58 · 취약 route_only 109 · 취약 repository_spec 102 · security declared 64 · oas 주지표(route_only 제외) 160. test_v30.jsonl은 불변. 정의 변경 내용은 AGENTS.md '평가 정의 eval-def v2'.

## 1. 구 정의(v1) vs 신 정의(v2) 비교

주지표 macro-F1은 support 있는 label 평균. 신 정의 oas 주지표는 route_only 109건 제외(160건), oas_code는 전체 265건(정답 변경 없음). "합성 제외"는 주지표에서 합성 58건을 뺀 값(oas 102건 = repository_spec, oas_code 207건). public 오판 신 정의 = declared ∧ 예측 public ∧ 정답≠public, 분모 declared ∧ 정답≠public(47건). 구체 응답 정밀도/재현율 = 정답이 구체 label인 건 중 구체로 답한 비율의 정확도 / 전체 대비 정답률.

| 조건 | 모델 | macro-F1 구(전체) | macro-F1 신(주지표) | 신·합성 제외 | 합성 58만 | manual 구 | manual 신(주지표) | public 오판 구 | public 오판 신 | 구체 P/R 구 | 구체 P/R 신 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| oas | lora_v5_s42_final | 0.6251 | 0.7574 | 0.5036 | 0.9796 | 60.6% | 37.5% | 12/64 | 0/47 | 0.8932 / 0.3622 (응답률 0.4055) | 0.8866 / 0.589 (응답률 0.6644) |
| oas | lora_v5_s43_final | 0.5918 | 0.7279 | 0.4632 | 0.9905 | 65.4% | 43.8% | 7/64 | 0/47 | 0.913 / 0.3307 (응답률 0.3622) | 0.9101 / 0.5548 (응답률 0.6096) |
| oas | lora_v5_s44_final | 0.5991 | 0.7333 | 0.4196 | 1.0 | 68.4% | 48.1% | 8/64 | 0/47 | 0.9294 / 0.311 (응답률 0.3346) | 0.9277 / 0.5274 (응답률 0.5685) |
| oas | lora_v6d_s42_final | 0.4722 | 0.6155 | 0.4817 | 0.8571 | 65.4% | 43.1% | 11/64 | 0/47 | 0.9294 / 0.311 (응답률 0.3346) | 0.9277 / 0.5274 (응답률 0.5685) |
| oas | lora_v6d_s43_final | 0.6097 | 0.7388 | 0.4532 | 0.9905 | 65.4% | 45.0% | 7/64 | 0/47 | 0.913 / 0.3307 (응답률 0.3622) | 0.908 / 0.5411 (응답률 0.5959) |
| oas | lora_v6d_s44_final | 0.5649 | 0.7039 | 0.4483 | 0.9796 | 66.5% | 44.4% | 8/64 | 0/47 | 0.8864 / 0.3071 (응답률 0.3465) | 0.8851 / 0.5274 (응답률 0.5959) |
| oas_code | lora_v5_s42_final | 0.6947 | 0.6947 | 0.3661 | 0.9905 | 25.3% | 25.3% | 16/64 | 3/47 | 0.8187 / 0.632 (응답률 0.772) | 0.8187 / 0.632 (응답률 0.772) |
| oas_code | lora_v5_s43_final | 0.6943 | 0.6943 | 0.386 | 0.9496 | 27.9% | 27.9% | 15/64 | 2/47 | 0.8503 / 0.636 (응답률 0.748) | 0.8503 / 0.636 (응답률 0.748) |
| oas_code | lora_v5_s44_final | 0.7109 | 0.7109 | 0.3711 | 0.9905 | 28.7% | 28.7% | 12/64 | 1/47 | 0.8548 / 0.636 (응답률 0.744) | 0.8548 / 0.636 (응답률 0.744) |
| oas_code | lora_v6d_s42_final | 0.7122 | 0.7122 | 0.357 | 0.9829 | 25.3% | 25.3% | 14/64 | 3/47 | 0.8229 / 0.632 (응답률 0.768) | 0.8229 / 0.632 (응답률 0.768) |
| oas_code | lora_v6d_s43_final | 0.7419 | 0.7419 | 0.3666 | 1.0 | 24.1% | 24.1% | 16/64 | 2/47 | 0.8308 / 0.668 (응답률 0.804) | 0.8308 / 0.668 (응답률 0.804) |
| oas_code | lora_v6d_s44_final | 0.7313 | 0.7313 | 0.383 | 1.0 | 27.2% | 27.2% | 12/64 | 1/47 | 0.8705 / 0.672 (응답률 0.772) | 0.8705 / 0.672 (응답률 0.772) |

합성 58건 주석: test 합성 58건 중 56건이 train 합성과 같은 경로 템플릿, 43건은 정규화한 인가 검사 줄까지 동일(reports/data_v1_audit.md 4절). 합성 구간 수치는 일반화 근거로 쓰지 않는다.

## 2. oas 보조지표 — route_only 109건(명세 없음), manual 예측을 정답으로 인정

| 모델 | N | 정확도(manual 인정) | macro-F1(manual 인정) | manual 예측 비율 | 정확도(엄격, 구 정의) | macro-F1(엄격) |
|---|---:|---:|---:|---:|---:|---:|
| lora_v5_s42_final | 109 | 100.0% | 1.0 | 94.5% | 6.4% | 0.0838 |
| lora_v5_s43_final | 109 | 100.0% | 1.0 | 97.2% | 3.7% | 0.0482 |
| lora_v5_s44_final | 109 | 100.0% | 1.0 | 98.2% | 2.8% | 0.0345 |
| lora_v6d_s42_final | 109 | 100.0% | 1.0 | 98.2% | 2.8% | 0.0345 |
| lora_v6d_s43_final | 109 | 100.0% | 1.0 | 95.4% | 5.5% | 0.0728 |
| lora_v6d_s44_final | 109 | 100.0% | 1.0 | 99.1% | 1.8% | 0.0197 |

## 3. public 오판 재정의 효과 — 구 정의로 잡힌 건 중 정답이 실제 public인 건

| 조건 | 모델 | 구 정의 건수 | 그중 정답이 public(오판 아님) | 신 정의 건수/분모 | 정답 public인 id |
|---|---|---:|---:|---:|---:|
| oas | lora_v5_s42_final | 12 | 12 | 0/47 | 860383f68102b772bb99, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v5_s43_final | 7 | 7 | 0/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v5_s44_final | 8 | 8 | 0/47 | d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v6d_s42_final | 11 | 11 | 0/47 | 860383f68102b772bb99, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v6d_s43_final | 7 | 7 | 0/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v6d_s44_final | 8 | 8 | 0/47 | d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v5_s42_final | 16 | 13 | 3/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v5_s43_final | 15 | 13 | 2/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, 860383f68102b772bb99, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v5_s44_final | 12 | 11 | 1/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v6d_s42_final | 14 | 11 | 3/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v6d_s43_final | 16 | 14 | 2/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v6d_s44_final | 12 | 11 | 1/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |

신 정의 오판 id:

- oas / lora_v5_s42_final: 없음
- oas / lora_v5_s43_final: 없음
- oas / lora_v5_s44_final: 없음
- oas / lora_v6d_s42_final: 없음
- oas / lora_v6d_s43_final: 없음
- oas / lora_v6d_s44_final: 없음
- oas_code / lora_v5_s42_final: fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219
- oas_code / lora_v5_s43_final: 0797f5bb072770d50159, fc9dac901542ca88d688
- oas_code / lora_v5_s44_final: d8c5cf5eb0bfbd488219
- oas_code / lora_v6d_s42_final: fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219
- oas_code / lora_v6d_s43_final: fc9dac901542ca88d688, d8c5cf5eb0bfbd488219
- oas_code / lora_v6d_s44_final: d8c5cf5eb0bfbd488219

## 4. 신 정의 주지표 label별 P/R/F1 (support 포함)

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

### oas / lora_v6d_s42_final — 주지표 160건, macro-F1 0.6155 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.5952 | 0.7463 |
| role_required | 22 | 0.9091 | 0.4545 | 0.6061 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 0.0 | 0.0 | 0.0 |
| owner_match | 62 | 0.8571 | 0.4839 | 0.6186 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.2029 | 1.0 | 0.3373 |

### oas / lora_v6d_s43_final — 주지표 160건, macro-F1 0.7388 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.4762 | 0.6452 |
| role_required | 22 | 0.7857 | 0.5 | 0.6111 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8485 | 0.4516 | 0.5895 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1944 | 1.0 | 0.3256 |

### oas / lora_v6d_s44_final — 주지표 160건, macro-F1 0.7039 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.5238 | 0.6875 |
| role_required | 22 | 0.7857 | 0.5 | 0.6111 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 0.75 | 0.8571 |
| owner_match | 62 | 0.8125 | 0.4194 | 0.5532 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1972 | 1.0 | 0.3294 |

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

### oas_code / lora_v6d_s42_final — 주지표 265건, macro-F1 0.7122 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.7368 | 0.6364 | 0.6829 |
| role_required | 47 | 0.8182 | 0.383 | 0.5217 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8478 | 0.6842 | 0.7573 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.1791 | 0.8 | 0.2927 |

### oas_code / lora_v6d_s43_final — 주지표 265건, macro-F1 0.7419 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.75 | 0.7273 | 0.7385 |
| role_required | 47 | 0.8889 | 0.3404 | 0.4923 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8469 | 0.7281 | 0.783 |
| owner_or_admin | 11 | 0.8889 | 0.7273 | 0.8 |
| manual_review_required | 15 | 0.2344 | 1.0 | 0.3797 |

### oas_code / lora_v6d_s44_final — 주지표 265건, macro-F1 0.7313 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.9111 | 0.6212 | 0.7387 |
| role_required | 47 | 0.9 | 0.383 | 0.5373 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8396 | 0.7807 | 0.8091 |
| owner_or_admin | 11 | 0.8889 | 0.7273 | 0.8 |
| manual_review_required | 15 | 0.2083 | 1.0 | 0.3448 |


원자료: scores.json. (모델 집합이 base_v301/lora_v1이 아니므로 5절 결론 생략)
