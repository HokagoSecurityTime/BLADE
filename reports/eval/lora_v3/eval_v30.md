# eval-def v2 재계산 — LoRA v1 4개 조합 (test_v30, 예측 파일 재사용, 추론 없음)

구간(reports/eval_v30_redef/segments.json): 전체 269 · 합성 58 · 취약 route_only 109 · 취약 repository_spec 102 · security declared 64 · oas 주지표(route_only 제외) 160. test_v30.jsonl은 불변. 정의 변경 내용은 AGENTS.md '평가 정의 eval-def v2'.

## 1. 구 정의(v1) vs 신 정의(v2) 비교

주지표 macro-F1은 support 있는 label 평균. 신 정의 oas 주지표는 route_only 109건 제외(160건), oas_code는 전체 265건(정답 변경 없음). "합성 제외"는 주지표에서 합성 58건을 뺀 값(oas 102건 = repository_spec, oas_code 207건). public 오판 신 정의 = declared ∧ 예측 public ∧ 정답≠public, 분모 declared ∧ 정답≠public(47건). 구체 응답 정밀도/재현율 = 정답이 구체 label인 건 중 구체로 답한 비율의 정확도 / 전체 대비 정답률.

| 조건 | 모델 | macro-F1 구(전체) | macro-F1 신(주지표) | 신·합성 제외 | 합성 58만 | manual 구 | manual 신(주지표) | public 오판 구 | public 오판 신 | 구체 P/R 구 | 구체 P/R 신 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| oas | base_v301 | 0.572 | 0.7078 | 0.2896 | 0.9539 | 28.6% | 13.8% | 27/64 | 13/47 | 0.5605 / 0.3465 (응답률 0.6181) | 0.6542 / 0.4795 (응답률 0.7329) |
| oas | lora_v2_s42_final | 0.5714 | 0.696 | 0.3125 | 1.0 | 71.0% | 51.9% | 6/64 | 0/47 | 0.8701 / 0.2638 (응답률 0.3031) | 0.8684 / 0.4521 (응답률 0.5205) |
| oas | lora_v2_s42_runpod_final | 0.5609 | 0.6866 | 0.2832 | 1.0 | 75.5% | 58.8% | 5/64 | 0/47 | 0.9394 / 0.2441 (응답률 0.2598) | 0.9394 / 0.4247 (응답률 0.4521) |
| oas | lora_v2_s43_final | 0.5533 | 0.6718 | 0.2761 | 1.0 | 72.5% | 55.0% | 5/64 | 0/47 | 0.9041 / 0.2598 (응답률 0.2874) | 0.9014 / 0.4384 (응답률 0.4863) |
| oas | lora_v2_s44_final | 0.5505 | 0.6763 | 0.3043 | 1.0 | 73.6% | 55.6% | 5/64 | 0/47 | 0.9014 / 0.252 (응답률 0.2795) | 0.9014 / 0.4384 (응답률 0.4863) |
| oas | lora_v3a_s42_final | 0.5591 | 0.6881 | 0.3343 | 1.0 | 73.6% | 56.2% | 6/64 | 0/47 | 0.9437 / 0.2638 (응답률 0.2795) | 0.9429 / 0.4521 (응답률 0.4795) |
| oas | lora_v3a_s43_final | 0.5293 | 0.6479 | 0.2546 | 1.0 | 76.2% | 60.6% | 6/64 | 0/47 | 0.9375 / 0.2362 (응답률 0.252) | 0.9365 / 0.4041 (응답률 0.4315) |
| oas | lora_v3a_s44_final | 0.5528 | 0.6698 | 0.2262 | 1.0 | 75.5% | 59.4% | 2/64 | 0/47 | 0.9091 / 0.2362 (응답률 0.2598) | 0.9077 / 0.4041 (응답률 0.4452) |
| oas | lora_v3b_s42_final | 0.5726 | 0.6982 | 0.3948 | 1.0 | 64.3% | 40.6% | 11/64 | 0/47 | 0.7812 / 0.2953 (응답률 0.378) | 0.7789 / 0.5068 (응답률 0.6507) |
| oas | lora_v3b_s43_final | 0.5489 | 0.6733 | 0.3493 | 0.9575 | 70.6% | 51.9% | 8/64 | 1/47 | 0.9067 / 0.2677 (응답률 0.2953) | 0.9041 / 0.4521 (응답률 0.5) |
| oas | lora_v3b_s44_final | 0.5935 | 0.7224 | 0.4651 | 0.9905 | 61.0% | 37.5% | 7/64 | 0/47 | 0.8173 / 0.3346 (응답률 0.4094) | 0.8182 / 0.5548 (응답률 0.6781) |
| oas_code | base_v301 | 0.6457 | 0.6457 | 0.1958 | 0.9543 | 9.4% | 9.4% | 33/64 | 18/47 | 0.4693 / 0.428 (응답률 0.912) | 0.4693 / 0.428 (응답률 0.912) |
| oas_code | lora_v2_s42_final | 0.6172 | 0.6172 | 0.3081 | 1.0 | 34.0% | 34.0% | 6/64 | 0/47 | 0.7657 / 0.536 (응답률 0.7) | 0.7657 / 0.536 (응답률 0.7) |
| oas_code | lora_v2_s42_runpod_final | 0.6664 | 0.6664 | 0.3368 | 1.0 | 33.6% | 33.6% | 11/64 | 2/47 | 0.8114 / 0.568 (응답률 0.7) | 0.8114 / 0.568 (응답률 0.7) |
| oas_code | lora_v2_s43_final | 0.6356 | 0.6356 | 0.2804 | 1.0 | 43.4% | 43.4% | 7/64 | 1/47 | 0.8163 / 0.48 (응답률 0.588) | 0.8163 / 0.48 (응답률 0.588) |
| oas_code | lora_v2_s44_final | 0.5969 | 0.5969 | 0.264 | 1.0 | 45.3% | 45.3% | 8/64 | 0/47 | 0.7862 / 0.456 (응답률 0.58) | 0.7862 / 0.456 (응답률 0.58) |
| oas_code | lora_v3a_s42_final | 0.633 | 0.633 | 0.3281 | 1.0 | 30.9% | 30.9% | 6/64 | 0/47 | 0.7978 / 0.568 (응답률 0.712) | 0.7978 / 0.568 (응답률 0.712) |
| oas_code | lora_v3a_s43_final | 0.6011 | 0.6011 | 0.3202 | 0.9905 | 21.5% | 21.5% | 7/64 | 0/47 | 0.665 / 0.532 (응답률 0.8) | 0.665 / 0.532 (응답률 0.8) |
| oas_code | lora_v3a_s44_final | 0.6084 | 0.6084 | 0.2979 | 1.0 | 22.3% | 22.3% | 4/64 | 0/47 | 0.6814 / 0.556 (응답률 0.816) | 0.6814 / 0.556 (응답률 0.816) |
| oas_code | lora_v3b_s42_final | 0.6884 | 0.6884 | 0.3579 | 1.0 | 17.0% | 17.0% | 8/64 | 0/47 | 0.7352 / 0.644 (응답률 0.876) | 0.7352 / 0.644 (응답률 0.876) |
| oas_code | lora_v3b_s43_final | 0.6124 | 0.6124 | 0.3309 | 1.0 | 25.3% | 25.3% | 6/64 | 0/47 | 0.7282 / 0.568 (응답률 0.78) | 0.7282 / 0.568 (응답률 0.78) |
| oas_code | lora_v3b_s44_final | 0.6435 | 0.6435 | 0.3259 | 0.9905 | 16.6% | 16.6% | 5/64 | 0/47 | 0.6898 / 0.596 (응답률 0.864) | 0.6898 / 0.596 (응답률 0.864) |

합성 58건 주석: test 합성 58건 중 56건이 train 합성과 같은 경로 템플릿, 43건은 정규화한 인가 검사 줄까지 동일(reports/data_v1_audit.md 4절). 합성 구간 수치는 일반화 근거로 쓰지 않는다.

## 2. oas 보조지표 — route_only 109건(명세 없음), manual 예측을 정답으로 인정

| 모델 | N | 정확도(manual 인정) | macro-F1(manual 인정) | manual 예측 비율 | 정확도(엄격, 구 정의) | macro-F1(엄격) |
|---|---:|---:|---:|---:|---:|---:|
| base_v301 | 109 | 67.0% | 0.3059 | 50.5% | 17.4% | 0.1044 |
| lora_v2_s42_final | 109 | 100.0% | 1.0 | 99.1% | 1.8% | 0.0197 |
| lora_v2_s42_runpod_final | 109 | 100.0% | 1.0 | 100.0% | 0.9% | 0.0036 |
| lora_v2_s43_final | 109 | 100.0% | 1.0 | 98.2% | 2.8% | 0.0345 |
| lora_v2_s44_final | 109 | 100.0% | 1.0 | 100.0% | 0.9% | 0.0036 |
| lora_v3a_s42_final | 109 | 100.0% | 1.0 | 99.1% | 1.8% | 0.0197 |
| lora_v3a_s43_final | 109 | 100.0% | 1.0 | 99.1% | 1.8% | 0.0197 |
| lora_v3a_s44_final | 109 | 100.0% | 1.0 | 99.1% | 1.8% | 0.0197 |
| lora_v3b_s42_final | 109 | 100.0% | 1.0 | 99.1% | 1.8% | 0.0197 |
| lora_v3b_s43_final | 109 | 100.0% | 1.0 | 98.2% | 2.8% | 0.0345 |
| lora_v3b_s44_final | 109 | 99.1% | 0.6296 | 95.4% | 4.6% | 0.059 |

## 3. public 오판 재정의 효과 — 구 정의로 잡힌 건 중 정답이 실제 public인 건

| 조건 | 모델 | 구 정의 건수 | 그중 정답이 public(오판 아님) | 신 정의 건수/분모 | 정답 public인 id |
|---|---|---:|---:|---:|---:|
| oas | base_v301 | 27 | 14 | 13/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, 860383f68102b772bb99, c085f5d6b9f87dd6d4a1, 324601a8dc9e9ea969bb, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v2_s42_final | 6 | 6 | 0/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v2_s42_runpod_final | 5 | 5 | 0/47 | 860383f68102b772bb99, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v2_s43_final | 5 | 5 | 0/47 | 860383f68102b772bb99, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v2_s44_final | 5 | 5 | 0/47 | 860383f68102b772bb99, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v3a_s42_final | 6 | 6 | 0/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v3a_s43_final | 6 | 6 | 0/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v3a_s44_final | 2 | 2 | 0/47 | beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v3b_s42_final | 11 | 11 | 0/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v3b_s43_final | 8 | 7 | 1/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, 7a19e5a3a9eb0d5947f3, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v3b_s44_final | 7 | 7 | 0/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, bb532c95786f45e07314, beacon_iot_catalogue_0 |
| oas_code | base_v301 | 33 | 15 | 18/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, 860383f68102b772bb99, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v2_s42_final | 6 | 6 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v2_s42_runpod_final | 11 | 9 | 2/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v2_s43_final | 7 | 6 | 1/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v2_s44_final | 8 | 8 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, be8b11cdbabe4486aeda, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v3a_s42_final | 6 | 6 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v3a_s43_final | 7 | 7 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v3a_s44_final | 4 | 4 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v3b_s42_final | 8 | 8 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v3b_s43_final | 6 | 6 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v3b_s44_final | 5 | 5 | 0/47 | 149fc53d41cf49d52bb9, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |

신 정의 오판 id:

- oas / base_v301: 759eb32d69ab1820e44d, aae57acca0e9317e81c1, d93acb187b6c273464f0, 15af38ebe8faf15c930f, 6bca6097b26cf226f405, cdd3d3e140b0b509bcd3, af6e2ae1b29132ee1d77, dcc8f1be82d40ee3d5cf, fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219, 956a6feb1b1f65eb5a9a, 0b0918598294090d14c3
- oas / lora_v2_s42_final: 없음
- oas / lora_v2_s42_runpod_final: 없음
- oas / lora_v2_s43_final: 없음
- oas / lora_v2_s44_final: 없음
- oas / lora_v3a_s42_final: 없음
- oas / lora_v3a_s43_final: 없음
- oas / lora_v3a_s44_final: 없음
- oas / lora_v3b_s42_final: 없음
- oas / lora_v3b_s43_final: d8c5cf5eb0bfbd488219
- oas / lora_v3b_s44_final: 없음
- oas_code / base_v301: 759eb32d69ab1820e44d, ff8c5eda79000fa6687f, b3906a959a0b669047ba, aae57acca0e9317e81c1, acdc8447219278841824, d93acb187b6c273464f0, d0afe4b052514b189dfa, 5928631c56d36ced026a, c3203410c4072686beaa, 15af38ebe8faf15c930f, 6bca6097b26cf226f405, dcc8f1be82d40ee3d5cf, c917e3e10dce94cc245c, fc9dac901542ca88d688, 5a72ac6384c12b441687, 4de2f44349d88f3d6b3a, d8c5cf5eb0bfbd488219, 0b0918598294090d14c3
- oas_code / lora_v2_s42_final: 없음
- oas_code / lora_v2_s42_runpod_final: fc9dac901542ca88d688, d8c5cf5eb0bfbd488219
- oas_code / lora_v2_s43_final: d8c5cf5eb0bfbd488219
- oas_code / lora_v2_s44_final: 없음
- oas_code / lora_v3a_s42_final: 없음
- oas_code / lora_v3a_s43_final: 없음
- oas_code / lora_v3a_s44_final: 없음
- oas_code / lora_v3b_s42_final: 없음
- oas_code / lora_v3b_s43_final: 없음
- oas_code / lora_v3b_s44_final: 없음

## 4. 신 정의 주지표 label별 P/R/F1 (support 포함)

### oas / base_v301 — 주지표 160건, macro-F1 0.7078 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.5231 | 0.8095 | 0.6355 |
| role_required | 22 | 0.6 | 0.4091 | 0.4865 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 1.0 | 0.1452 | 0.2535 |
| owner_or_admin | 8 | 1.0 | 0.75 | 0.8571 |
| manual_review_required | 14 | 0.5909 | 0.9286 | 0.7222 |

### oas / lora_v2_s42_final — 주지표 160건, macro-F1 0.696 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.8571 | 0.4286 | 0.5714 |
| role_required | 22 | 0.8333 | 0.4545 | 0.5882 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.7826 | 0.2903 | 0.4235 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1687 | 1.0 | 0.2887 |

### oas / lora_v2_s42_runpod_final — 주지표 160건, macro-F1 0.6866 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.3571 | 0.5263 |
| role_required | 22 | 0.9091 | 0.4545 | 0.6061 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.85 | 0.2742 | 0.4146 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1489 | 1.0 | 0.2593 |

### oas / lora_v2_s43_final — 주지표 160건, macro-F1 0.6718 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.4048 | 0.5763 |
| role_required | 22 | 0.75 | 0.4091 | 0.5294 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8571 | 0.2903 | 0.4337 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1591 | 1.0 | 0.2745 |

### oas / lora_v2_s44_final — 주지표 160건, macro-F1 0.6763 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.9474 | 0.4286 | 0.5902 |
| role_required | 22 | 0.8333 | 0.4545 | 0.5882 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8421 | 0.2581 | 0.3951 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1573 | 1.0 | 0.2718 |

### oas / lora_v3a_s42_final — 주지표 160건, macro-F1 0.6881 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.4286 | 0.6 |
| role_required | 22 | 1.0 | 0.4545 | 0.625 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8571 | 0.2903 | 0.4337 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1556 | 1.0 | 0.2692 |

### oas / lora_v3a_s43_final — 주지표 160건, macro-F1 0.6479 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.3571 | 0.5263 |
| role_required | 22 | 0.8333 | 0.4545 | 0.5882 |
| membership_required | 4 | 0.6667 | 1.0 | 0.8 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 1.0 | 0.2258 | 0.3684 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1443 | 1.0 | 0.2523 |

### oas / lora_v3a_s44_final — 주지표 160건, macro-F1 0.6698 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.2619 | 0.4151 |
| role_required | 22 | 0.8333 | 0.4545 | 0.5882 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8182 | 0.2903 | 0.4286 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1474 | 1.0 | 0.2569 |

### oas / lora_v3b_s42_final — 주지표 160건, macro-F1 0.6982 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.9565 | 0.5238 | 0.6769 |
| role_required | 22 | 0.4643 | 0.5909 | 0.52 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8261 | 0.3065 | 0.4471 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.2154 | 1.0 | 0.3544 |

### oas / lora_v3b_s43_final — 주지표 160건, macro-F1 0.6733 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.9333 | 0.3333 | 0.4912 |
| role_required | 22 | 0.8333 | 0.4545 | 0.5882 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 0.875 | 0.9333 |
| owner_match | 62 | 0.8846 | 0.371 | 0.5227 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1687 | 1.0 | 0.2887 |

### oas / lora_v3b_s44_final — 주지표 160건, macro-F1 0.7224 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.5238 | 0.6875 |
| role_required | 22 | 0.4815 | 0.5909 | 0.5306 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8966 | 0.4194 | 0.5714 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.2333 | 1.0 | 0.3784 |

### oas_code / base_v301 — 주지표 265건, macro-F1 0.6457 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.4296 | 0.8788 | 0.5771 |
| role_required | 47 | 0.2623 | 0.3404 | 0.2963 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 1.0 | 0.114 | 0.2047 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.48 | 0.8 | 0.6 |

### oas_code / lora_v2_s42_final — 주지표 265건, macro-F1 0.6172 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8438 | 0.4091 | 0.551 |
| role_required | 47 | 0.5833 | 0.4468 | 0.506 |
| membership_required | 4 | 0.2857 | 1.0 | 0.4444 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8571 | 0.5789 | 0.6911 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.1667 | 1.0 | 0.2857 |

### oas_code / lora_v2_s42_runpod_final — 주지표 265건, macro-F1 0.6664 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8205 | 0.4848 | 0.6095 |
| role_required | 47 | 0.6875 | 0.4681 | 0.557 |
| membership_required | 4 | 0.5 | 1.0 | 0.6667 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.85 | 0.5965 | 0.701 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.1685 | 1.0 | 0.2885 |

### oas_code / lora_v2_s43_final — 주지표 265건, macro-F1 0.6356 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8438 | 0.4091 | 0.551 |
| role_required | 47 | 0.6429 | 0.383 | 0.48 |
| membership_required | 4 | 0.5714 | 1.0 | 0.7273 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8594 | 0.4825 | 0.618 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.1304 | 1.0 | 0.2308 |

### oas_code / lora_v2_s44_final — 주지표 265건, macro-F1 0.5969 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8286 | 0.4394 | 0.5743 |
| role_required | 47 | 0.5714 | 0.3404 | 0.4267 |
| membership_required | 4 | 0.3636 | 1.0 | 0.5333 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8909 | 0.4298 | 0.5799 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.125 | 1.0 | 0.2222 |

### oas_code / lora_v3a_s42_final — 주지표 265건, macro-F1 0.633 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8889 | 0.3636 | 0.5161 |
| role_required | 47 | 0.6486 | 0.5106 | 0.5714 |
| membership_required | 4 | 0.2857 | 1.0 | 0.4444 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.881 | 0.6491 | 0.7475 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.1829 | 1.0 | 0.3093 |

### oas_code / lora_v3a_s43_final — 주지표 265건, macro-F1 0.6011 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8438 | 0.4091 | 0.551 |
| role_required | 47 | 0.5435 | 0.5319 | 0.5376 |
| membership_required | 4 | 0.1026 | 1.0 | 0.186 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.9104 | 0.5351 | 0.674 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.2632 | 1.0 | 0.4167 |

### oas_code / lora_v3a_s44_final — 주지표 265건, macro-F1 0.6084 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8696 | 0.303 | 0.4494 |
| role_required | 47 | 0.45 | 0.5745 | 0.5047 |
| membership_required | 4 | 0.2 | 1.0 | 0.3333 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8471 | 0.6316 | 0.7236 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.2542 | 1.0 | 0.4054 |

### oas_code / lora_v3b_s42_final — 주지표 265건, macro-F1 0.6884 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8824 | 0.4545 | 0.6 |
| role_required | 47 | 0.4828 | 0.5957 | 0.5333 |
| membership_required | 4 | 0.4 | 1.0 | 0.5714 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8218 | 0.7281 | 0.7721 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.3333 | 1.0 | 0.5 |

### oas_code / lora_v3b_s43_final — 주지표 265건, macro-F1 0.6124 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8571 | 0.3636 | 0.5106 |
| role_required | 47 | 0.6579 | 0.5319 | 0.5882 |
| membership_required | 4 | 0.1379 | 1.0 | 0.2424 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.869 | 0.6404 | 0.7374 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.2239 | 1.0 | 0.3659 |

### oas_code / lora_v3b_s44_final — 주지표 265건, macro-F1 0.6435 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8519 | 0.3485 | 0.4946 |
| role_required | 47 | 0.4444 | 0.5957 | 0.5091 |
| membership_required | 4 | 0.25 | 1.0 | 0.4 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8298 | 0.6842 | 0.75 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.3409 | 1.0 | 0.5085 |


원자료: scores.json. (모델 집합이 base_v301/lora_v1이 아니므로 5절 결론 생략)
