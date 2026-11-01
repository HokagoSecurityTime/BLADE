# eval-def v2 재계산 — LoRA v1 4개 조합 (test_v30, 예측 파일 재사용, 추론 없음)

구간(reports/eval_v30_redef/segments.json): 전체 269 · 합성 58 · 취약 route_only 109 · 취약 repository_spec 102 · security declared 64 · oas 주지표(route_only 제외) 160. test_v30.jsonl은 불변. 정의 변경 내용은 AGENTS.md '평가 정의 eval-def v2'.

## 1. 구 정의(v1) vs 신 정의(v2) 비교

주지표 macro-F1은 support 있는 label 평균. 신 정의 oas 주지표는 route_only 109건 제외(160건), oas_code는 전체 265건(정답 변경 없음). "합성 제외"는 주지표에서 합성 58건을 뺀 값(oas 102건 = repository_spec, oas_code 207건). public 오판 신 정의 = declared ∧ 예측 public ∧ 정답≠public, 분모 declared ∧ 정답≠public(47건). 구체 응답 정밀도/재현율 = 정답이 구체 label인 건 중 구체로 답한 비율의 정확도 / 전체 대비 정답률.

| 조건 | 모델 | macro-F1 구(전체) | macro-F1 신(주지표) | 신·합성 제외 | 합성 58만 | manual 구 | manual 신(주지표) | public 오판 구 | public 오판 신 | 구체 P/R 구 | 구체 P/R 신 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| oas | base_qwen_runpod_stable | 0.6136 | 0.7579 | 0.3244 | 1.0 | 28.6% | 13.1% | 40/64 | 23/47 | 0.5988 / 0.3937 (응답률 0.6575) | 0.6357 / 0.5616 (응답률 0.8836) |
| oas | lora_v2_s42_runpod_final_stable | 0.5432 | 0.668 | 0.2743 | 1.0 | 75.5% | 58.8% | 5/64 | 0/47 | 0.9242 / 0.2402 (응답률 0.2598) | 0.9242 / 0.4178 (응답률 0.4521) |
| oas | lora_v2_s43_runpod_final_stable | 0.5407 | 0.6624 | 0.3025 | 1.0 | 71.4% | 52.5% | 6/64 | 0/47 | 0.8571 / 0.2598 (응답률 0.3031) | 0.8553 / 0.4452 (응답률 0.5205) |
| oas | lora_v2_s44_runpod_final_stable | 0.5376 | 0.6653 | 0.3044 | 1.0 | 73.2% | 55.0% | 5/64 | 0/47 | 0.8889 / 0.252 (응답률 0.2835) | 0.8889 / 0.4384 (응답률 0.4932) |
| oas | lora_v3b_s42_final_stable | 0.5581 | 0.6828 | 0.3865 | 1.0 | 64.3% | 40.6% | 11/64 | 0/47 | 0.7708 / 0.2913 (응답률 0.378) | 0.7684 / 0.5 (응답률 0.6507) |
| oas | lora_v3b_s43_final_stable | 0.5297 | 0.6524 | 0.3493 | 0.9762 | 68.0% | 47.5% | 8/64 | 1/47 | 0.878 / 0.2835 (응답률 0.3228) | 0.875 / 0.4795 (응답률 0.5479) |
| oas | lora_v3b_s44_final_stable | 0.5693 | 0.6976 | 0.4512 | 1.0 | 61.0% | 37.5% | 8/64 | 0/47 | 0.8 / 0.3307 (응답률 0.4134) | 0.8 / 0.5479 (응답률 0.6849) |
| oas | lora_v4_s42_final_stable | 0.6101 | 0.7456 | 0.4514 | 1.0 | 65.8% | 44.4% | 8/64 | 0/47 | 0.9239 / 0.3346 (응답률 0.3622) | 0.9213 / 0.5616 (응답률 0.6096) |
| oas | lora_v4_s43_final_stable | 0.5742 | 0.712 | 0.4438 | 1.0 | 65.1% | 42.5% | 9/64 | 1/47 | 0.8617 / 0.3189 (응답률 0.3701) | 0.8587 / 0.5411 (응답률 0.6301) |
| oas | lora_v4_s44_final_stable | 0.6194 | 0.7511 | 0.4817 | 1.0 | 58.4% | 38.8% | 12/64 | 0/47 | 0.8214 / 0.3622 (응답률 0.4409) | 0.8673 / 0.5822 (응답률 0.6712) |
| oas_code | base_qwen_runpod_stable | 0.6265 | 0.6265 | 0.1988 | 0.9308 | 10.9% | 10.9% | 31/64 | 15/47 | 0.4596 / 0.432 (응답률 0.94) | 0.4596 / 0.432 (응답률 0.94) |
| oas_code | lora_v2_s42_runpod_final_stable | 0.4874 | 0.4874 | 0.3162 | 0.7228 | 27.2% | 27.2% | 11/64 | 2/47 | 0.6852 / 0.444 (응답률 0.648) | 0.6852 / 0.444 (응답률 0.648) |
| oas_code | lora_v2_s43_runpod_final_stable | 0.585 | 0.585 | 0.2938 | 0.9552 | 34.0% | 34.0% | 7/64 | 1/47 | 0.7455 / 0.492 (응답률 0.66) | 0.7455 / 0.492 (응답률 0.66) |
| oas_code | lora_v2_s44_runpod_final_stable | 0.5437 | 0.5437 | 0.2654 | 0.889 | 42.6% | 42.6% | 6/64 | 0/47 | 0.7664 / 0.42 (응답률 0.548) | 0.7664 / 0.42 (응답률 0.548) |
| oas_code | lora_v3b_s42_final_stable | 0.632 | 0.632 | 0.3463 | 1.0 | 17.0% | 17.0% | 8/64 | 0/47 | 0.6804 / 0.596 (응답률 0.876) | 0.6804 / 0.596 (응답률 0.876) |
| oas_code | lora_v3b_s43_final_stable | 0.577 | 0.577 | 0.3166 | 0.961 | 21.1% | 21.1% | 6/64 | 0/47 | 0.6717 / 0.532 (응답률 0.792) | 0.6717 / 0.532 (응답률 0.792) |
| oas_code | lora_v3b_s44_final_stable | 0.6179 | 0.6179 | 0.3254 | 1.0 | 17.0% | 17.0% | 5/64 | 0/47 | 0.6545 / 0.576 (응답률 0.88) | 0.6545 / 0.576 (응답률 0.88) |
| oas_code | lora_v4_s42_final_stable | 0.6595 | 0.6595 | 0.3784 | 1.0 | 27.9% | 27.9% | 11/64 | 1/47 | 0.8421 / 0.64 (응답률 0.76) | 0.8421 / 0.64 (응답률 0.76) |
| oas_code | lora_v4_s43_final_stable | 0.637 | 0.637 | 0.3021 | 1.0 | 33.2% | 33.2% | 4/64 | 0/47 | 0.8079 / 0.572 (응답률 0.708) | 0.8079 / 0.572 (응답률 0.708) |
| oas_code | lora_v4_s44_final_stable | 0.6973 | 0.6973 | 0.3831 | 0.9947 | 23.8% | 23.8% | 12/64 | 0/47 | 0.84 / 0.672 (응답률 0.8) | 0.84 / 0.672 (응답률 0.8) |

합성 58건 주석: test 합성 58건 중 56건이 train 합성과 같은 경로 템플릿, 43건은 정규화한 인가 검사 줄까지 동일(reports/data_v1_audit.md 4절). 합성 구간 수치는 일반화 근거로 쓰지 않는다.

## 2. oas 보조지표 — route_only 109건(명세 없음), manual 예측을 정답으로 인정

| 모델 | N | 정확도(manual 인정) | macro-F1(manual 인정) | manual 예측 비율 | 정확도(엄격, 구 정의) | macro-F1(엄격) |
|---|---:|---:|---:|---:|---:|---:|
| base_qwen_runpod_stable | 109 | 67.9% | 0.3286 | 51.4% | 17.4% | 0.1231 |
| lora_v2_s42_runpod_final_stable | 109 | 100.0% | 1.0 | 100.0% | 0.9% | 0.0036 |
| lora_v2_s43_runpod_final_stable | 109 | 100.0% | 1.0 | 99.1% | 1.8% | 0.0197 |
| lora_v2_s44_runpod_final_stable | 109 | 100.0% | 1.0 | 100.0% | 0.9% | 0.0036 |
| lora_v3b_s42_final_stable | 109 | 100.0% | 1.0 | 99.1% | 1.8% | 0.0197 |
| lora_v3b_s43_final_stable | 109 | 100.0% | 1.0 | 98.2% | 2.8% | 0.0345 |
| lora_v3b_s44_final_stable | 109 | 99.1% | 0.6296 | 95.4% | 4.6% | 0.059 |
| lora_v4_s42_final_stable | 109 | 100.0% | 1.0 | 97.2% | 3.7% | 0.0482 |
| lora_v4_s43_final_stable | 109 | 100.0% | 1.0 | 98.2% | 2.8% | 0.0345 |
| lora_v4_s44_final_stable | 109 | 93.6% | 0.4167 | 87.2% | 7.3% | 0.0778 |

## 3. public 오판 재정의 효과 — 구 정의로 잡힌 건 중 정답이 실제 public인 건

| 조건 | 모델 | 구 정의 건수 | 그중 정답이 public(오판 아님) | 신 정의 건수/분모 | 정답 public인 id |
|---|---|---:|---:|---:|---:|
| oas | base_qwen_runpod_stable | 40 | 17 | 23/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, 860383f68102b772bb99, 7a19e5a3a9eb0d5947f3, c085f5d6b9f87dd6d4a1, 324601a8dc9e9ea969bb, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v2_s42_runpod_final_stable | 5 | 5 | 0/47 | 860383f68102b772bb99, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v2_s43_runpod_final_stable | 6 | 6 | 0/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v2_s44_runpod_final_stable | 5 | 5 | 0/47 | 860383f68102b772bb99, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v3b_s42_final_stable | 11 | 11 | 0/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v3b_s43_final_stable | 8 | 7 | 1/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, 7a19e5a3a9eb0d5947f3, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v3b_s44_final_stable | 8 | 8 | 0/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v4_s42_final_stable | 8 | 8 | 0/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, 7a19e5a3a9eb0d5947f3, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v4_s43_final_stable | 9 | 8 | 1/47 | 149fc53d41cf49d52bb9, 860383f68102b772bb99, 7a19e5a3a9eb0d5947f3, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas | lora_v4_s44_final_stable | 12 | 12 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | base_qwen_runpod_stable | 31 | 16 | 15/47 | 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, 860383f68102b772bb99, 7a19e5a3a9eb0d5947f3, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v2_s42_runpod_final_stable | 11 | 9 | 2/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v2_s43_runpod_final_stable | 7 | 6 | 1/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v2_s44_runpod_final_stable | 6 | 6 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v3b_s42_final_stable | 8 | 8 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v3b_s43_final_stable | 6 | 6 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v3b_s44_final_stable | 5 | 5 | 0/47 | 149fc53d41cf49d52bb9, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v4_s42_final_stable | 11 | 10 | 1/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, 7e3f8c20d798e8b34143, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v4_s43_final_stable | 4 | 4 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |
| oas_code | lora_v4_s44_final_stable | 12 | 12 | 0/47 | 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, beacon_iot_catalogue_0, beacon_iot_catalogue_1 |

신 정의 오판 id:

- oas / base_qwen_runpod_stable: 759eb32d69ab1820e44d, aae57acca0e9317e81c1, acdc8447219278841824, d93acb187b6c273464f0, d0afe4b052514b189dfa, 5928631c56d36ced026a, c3203410c4072686beaa, 15af38ebe8faf15c930f, 6bca6097b26cf226f405, cdd3d3e140b0b509bcd3, af6e2ae1b29132ee1d77, d42ed128370ce4d3ce71, cd33a23103c412ea5651, dcc8f1be82d40ee3d5cf, c917e3e10dce94cc245c, fc9dac901542ca88d688, 5a72ac6384c12b441687, 4de2f44349d88f3d6b3a, 97abea85e395e6649df4, d8c5cf5eb0bfbd488219, 956a6feb1b1f65eb5a9a, 0f7dacc4c4c5dc50ad69, 0b0918598294090d14c3
- oas / lora_v2_s42_runpod_final_stable: 없음
- oas / lora_v2_s43_runpod_final_stable: 없음
- oas / lora_v2_s44_runpod_final_stable: 없음
- oas / lora_v3b_s42_final_stable: 없음
- oas / lora_v3b_s43_final_stable: d8c5cf5eb0bfbd488219
- oas / lora_v3b_s44_final_stable: 없음
- oas / lora_v4_s42_final_stable: 없음
- oas / lora_v4_s43_final_stable: d8c5cf5eb0bfbd488219
- oas / lora_v4_s44_final_stable: 없음
- oas_code / base_qwen_runpod_stable: 759eb32d69ab1820e44d, aae57acca0e9317e81c1, acdc8447219278841824, d93acb187b6c273464f0, d0afe4b052514b189dfa, 5928631c56d36ced026a, c3203410c4072686beaa, 6bca6097b26cf226f405, dcc8f1be82d40ee3d5cf, c917e3e10dce94cc245c, fc9dac901542ca88d688, 5a72ac6384c12b441687, 4de2f44349d88f3d6b3a, d8c5cf5eb0bfbd488219, 0b0918598294090d14c3
- oas_code / lora_v2_s42_runpod_final_stable: fc9dac901542ca88d688, d8c5cf5eb0bfbd488219
- oas_code / lora_v2_s43_runpod_final_stable: d8c5cf5eb0bfbd488219
- oas_code / lora_v2_s44_runpod_final_stable: 없음
- oas_code / lora_v3b_s42_final_stable: 없음
- oas_code / lora_v3b_s43_final_stable: 없음
- oas_code / lora_v3b_s44_final_stable: 없음
- oas_code / lora_v4_s42_final_stable: d8c5cf5eb0bfbd488219
- oas_code / lora_v4_s43_final_stable: 없음
- oas_code / lora_v4_s44_final_stable: 없음

## 4. 신 정의 주지표 label별 P/R/F1 (support 포함)

### oas / base_qwen_runpod_stable — 주지표 160건, macro-F1 0.7579 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.5062 | 0.9762 | 0.6667 |
| role_required | 22 | 0.6316 | 0.5455 | 0.5854 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 1.0 | 0.1452 | 0.2535 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.6667 | 1.0 | 0.8 |

### oas / lora_v2_s42_runpod_final_stable — 주지표 160건, macro-F1 0.668 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.3571 | 0.5263 |
| role_required | 22 | 0.9091 | 0.4545 | 0.6061 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8421 | 0.2581 | 0.3951 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1489 | 1.0 | 0.2593 |

### oas / lora_v2_s43_runpod_final_stable — 주지표 160건, macro-F1 0.6624 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.9 | 0.4286 | 0.5806 |
| role_required | 22 | 0.7143 | 0.4545 | 0.5556 |
| membership_required | 4 | 0.6667 | 1.0 | 0.8 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.85 | 0.2742 | 0.4146 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1667 | 1.0 | 0.2857 |

### oas / lora_v2_s44_runpod_final_stable — 주지표 160건, macro-F1 0.6653 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.9444 | 0.4048 | 0.5667 |
| role_required | 22 | 0.9091 | 0.4545 | 0.6061 |
| membership_required | 4 | 0.6667 | 1.0 | 0.8 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8095 | 0.2742 | 0.4096 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1591 | 1.0 | 0.2745 |

### oas / lora_v3b_s42_final_stable — 주지표 160건, macro-F1 0.6828 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.9565 | 0.5238 | 0.6769 |
| role_required | 22 | 0.4643 | 0.5909 | 0.52 |
| membership_required | 4 | 0.6667 | 1.0 | 0.8 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8182 | 0.2903 | 0.4286 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.2154 | 1.0 | 0.3544 |

### oas / lora_v3b_s43_final_stable — 주지표 160건, macro-F1 0.6524 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.9444 | 0.4048 | 0.5667 |
| role_required | 22 | 0.8333 | 0.4545 | 0.5882 |
| membership_required | 4 | 0.5 | 1.0 | 0.6667 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8846 | 0.371 | 0.5227 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1316 | 0.7143 | 0.2222 |

### oas / lora_v3b_s44_final_stable — 주지표 160건, macro-F1 0.6976 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.5476 | 0.7077 |
| role_required | 22 | 0.4815 | 0.5909 | 0.5306 |
| membership_required | 4 | 0.5714 | 1.0 | 0.7273 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8889 | 0.3871 | 0.5393 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.2333 | 1.0 | 0.3784 |

### oas / lora_v4_s42_final_stable — 주지표 160건, macro-F1 0.7456 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.5476 | 0.7077 |
| role_required | 22 | 0.7692 | 0.4545 | 0.5714 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8788 | 0.4677 | 0.6105 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.1972 | 1.0 | 0.3294 |

### oas / lora_v4_s43_final_stable — 주지표 160건, macro-F1 0.712 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 0.9167 | 0.5238 | 0.6667 |
| role_required | 22 | 0.8462 | 0.5 | 0.6286 |
| membership_required | 4 | 0.6667 | 1.0 | 0.8 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.7879 | 0.4194 | 0.5474 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.2059 | 1.0 | 0.3415 |

### oas / lora_v4_s44_final_stable — 주지표 160건, macro-F1 0.7511 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 42 | 1.0 | 0.6667 | 0.8 |
| role_required | 22 | 0.55 | 0.5 | 0.5238 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 62 | 0.8667 | 0.4194 | 0.5652 |
| owner_or_admin | 8 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 14 | 0.2258 | 1.0 | 0.3684 |

### oas_code / base_qwen_runpod_stable — 주지표 265건, macro-F1 0.6265 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.4394 | 0.8788 | 0.5859 |
| role_required | 47 | 0.2714 | 0.4043 | 0.3248 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8235 | 0.1228 | 0.2137 |
| owner_or_admin | 11 | 1.0 | 0.4545 | 0.625 |
| manual_review_required | 15 | 0.4828 | 0.9333 | 0.6364 |

### oas_code / lora_v2_s42_runpod_final_stable — 주지표 265건, macro-F1 0.4874 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8158 | 0.4697 | 0.5962 |
| role_required | 47 | 0.619 | 0.2766 | 0.3824 |
| membership_required | 4 | 0.1333 | 1.0 | 0.2353 |
| tenant_match | 8 | 1.0 | 0.375 | 0.5455 |
| owner_match | 114 | 0.8413 | 0.4649 | 0.5989 |
| owner_or_admin | 11 | 1.0 | 0.6364 | 0.7778 |
| manual_review_required | 15 | 0.1667 | 0.8 | 0.2759 |

### oas_code / lora_v2_s43_runpod_final_stable — 주지표 265건, macro-F1 0.585 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8065 | 0.3788 | 0.5155 |
| role_required | 47 | 0.6 | 0.383 | 0.4675 |
| membership_required | 4 | 0.2105 | 1.0 | 0.3478 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8696 | 0.5263 | 0.6557 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.1556 | 0.9333 | 0.2667 |

### oas_code / lora_v2_s44_runpod_final_stable — 주지표 265건, macro-F1 0.5437 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8235 | 0.4242 | 0.56 |
| role_required | 47 | 0.55 | 0.234 | 0.3284 |
| membership_required | 4 | 0.2667 | 1.0 | 0.4211 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8889 | 0.4211 | 0.5714 |
| owner_or_admin | 11 | 1.0 | 0.5455 | 0.7059 |
| manual_review_required | 15 | 0.1239 | 0.9333 | 0.2188 |

### oas_code / lora_v3b_s42_final_stable — 주지표 265건, macro-F1 0.632 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.875 | 0.4242 | 0.5714 |
| role_required | 47 | 0.5185 | 0.5957 | 0.5545 |
| membership_required | 4 | 0.125 | 1.0 | 0.2222 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8588 | 0.6404 | 0.7337 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.3333 | 1.0 | 0.5 |

### oas_code / lora_v3b_s43_final_stable — 주지표 265건, macro-F1 0.577 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8571 | 0.3636 | 0.5106 |
| role_required | 47 | 0.697 | 0.4894 | 0.575 |
| membership_required | 4 | 0.0909 | 1.0 | 0.1667 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8571 | 0.5789 | 0.6911 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.1607 | 0.6 | 0.2535 |

### oas_code / lora_v3b_s44_final_stable — 주지표 265건, macro-F1 0.6179 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8571 | 0.3636 | 0.5106 |
| role_required | 47 | 0.4912 | 0.5957 | 0.5385 |
| membership_required | 4 | 0.1176 | 1.0 | 0.2105 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8471 | 0.6316 | 0.7236 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.3333 | 1.0 | 0.5 |

### oas_code / lora_v4_s42_final_stable — 주지표 265건, macro-F1 0.6595 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.8718 | 0.5152 | 0.6476 |
| role_required | 47 | 0.875 | 0.4468 | 0.5915 |
| membership_required | 4 | 0.2353 | 1.0 | 0.381 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.9043 | 0.7456 | 0.8173 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.2027 | 1.0 | 0.3371 |

### oas_code / lora_v4_s43_final_stable — 주지표 265건, macro-F1 0.637 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.7857 | 0.3333 | 0.4681 |
| role_required | 47 | 0.75 | 0.383 | 0.507 |
| membership_required | 4 | 0.4 | 1.0 | 0.5714 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8384 | 0.7281 | 0.7793 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.1705 | 1.0 | 0.2913 |

### oas_code / lora_v4_s44_final_stable — 주지표 265건, macro-F1 0.6973 (7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.85 | 0.5152 | 0.6415 |
| role_required | 47 | 0.8148 | 0.4681 | 0.5946 |
| membership_required | 4 | 0.4444 | 1.0 | 0.6154 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8519 | 0.807 | 0.8288 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.2222 | 0.9333 | 0.359 |


원자료: scores.json. (모델 집합이 base_v301/lora_v1이 아니므로 5절 결론 생략)
