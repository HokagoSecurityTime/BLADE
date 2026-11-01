# LoRA v1 (data-v1) — test_v30 평가, run lora_v1_run1, GPU NVIDIA A100-SXM4-80GB

프롬프트 v3.0.1, 베이스 unsloth/Qwen2.5-7B-Instruct-bnb-4bit, 해시 검증 통과(hashes.json). 하이퍼파라미터 config.json.

## 요약

| 조건/모델 | macro-F1 | support 있는 label 수 | manual 비율 | public 오판(declared 중) | 출력 오류 | 평균 ms |
|---|---|---|---|---|---|---|
| oas/base_v301 | 0.572 | 7 | 28.6% | 27/64 | 35 | 1032.4 |
| oas/lora_v1 | 0.5636 | 7 | 68.4% | 11/64 | 0 | 1042.3 |
| oas_code/base_v301 | 0.6457 | 7 | 9.4% | 33/64 | 11 | 1536.4 |
| oas_code/lora_v1 | 0.5762 | 7 | 29.4% | 7/64 | 1 | 1054.8 |

## oas/base_v301: label별 P/R/F1

| label | support | P | R | F1 |
|---|---|---|---|---|
| public | 66 | 0.4522 | 0.7879 | 0.5746 |
| role_required | 51 | 0.6 | 0.1765 | 0.2727 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 1.0 | 0.0789 | 0.1463 |
| owner_or_admin | 11 | 1.0 | 0.5455 | 0.7059 |
| manual_review_required | 15 | 0.1818 | 0.9333 | 0.3043 |

혼동행렬(행=정답, 열=예측):

| 정답\예측 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required | output_error |
|---|---|---|---|---|---|---|---|---|
| public | 52 | 1 | 0 | 0 | 0 | 0 | 7 | 6 |
| role_required | 20 | 9 | 0 | 0 | 0 | 0 | 16 | 6 |
| membership_required | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0 |
| owner_match | 41 | 5 | 0 | 0 | 9 | 0 | 39 | 20 |
| owner_or_admin | 2 | 0 | 0 | 0 | 0 | 6 | 1 | 2 |
| manual_review_required | 0 | 0 | 0 | 0 | 0 | 0 | 14 | 1 |

출처별 정확도: {"synthetic": {"records": 58, "accuracy": 0.9138}, "vuln": {"records": 211, "accuracy": 0.2322}}

public 오판 id: 759eb32d69ab1820e44d, aae57acca0e9317e81c1, 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, d93acb187b6c273464f0, 15af38ebe8faf15c930f, 860383f68102b772bb99, 6bca6097b26cf226f405, cdd3d3e140b0b509bcd3, af6e2ae1b29132ee1d77, c085f5d6b9f87dd6d4a1, 324601a8dc9e9ea969bb, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, dcc8f1be82d40ee3d5cf, fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219, d553cdd9276767f1b1bc, 956a6feb1b1f65eb5a9a, 0b0918598294090d14c3, beacon_iot_catalogue_0, beacon_iot_catalogue_1

## oas/lora_v1: label별 P/R/F1

| label | support | P | R | F1 |
|---|---|---|---|---|
| public | 66 | 0.9583 | 0.3485 | 0.5111 |
| role_required | 51 | 0.5263 | 0.1961 | 0.2857 |
| membership_required | 4 | 0.8 | 1.0 | 0.8889 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.8571 | 0.1579 | 0.2667 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.0815 | 1.0 | 0.1508 |

혼동행렬(행=정답, 열=예측):

| 정답\예측 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required | output_error |
|---|---|---|---|---|---|---|---|---|
| public | 23 | 1 | 0 | 0 | 2 | 0 | 40 | 0 |
| role_required | 0 | 10 | 0 | 0 | 1 | 0 | 40 | 0 |
| membership_required | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0 |
| owner_match | 1 | 8 | 1 | 0 | 18 | 0 | 86 | 0 |
| owner_or_admin | 0 | 0 | 0 | 0 | 0 | 8 | 3 | 0 |
| manual_review_required | 0 | 0 | 0 | 0 | 0 | 0 | 15 | 0 |

출처별 정확도: {"synthetic": {"records": 58, "accuracy": 1.0}, "vuln": {"records": 211, "accuracy": 0.1327}}

public 오판 id: 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, 860383f68102b772bb99, 7a19e5a3a9eb0d5947f3, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1

## oas_code/base_v301: label별 P/R/F1

| label | support | P | R | F1 |
|---|---|---|---|---|
| public | 66 | 0.4296 | 0.8788 | 0.5771 |
| role_required | 47 | 0.2623 | 0.3404 | 0.2963 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 1.0 | 0.114 | 0.2047 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.48 | 0.8 | 0.6 |

혼동행렬(행=정답, 열=예측):

| 정답\예측 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required | output_error |
|---|---|---|---|---|---|---|---|---|
| public | 58 | 6 | 0 | 0 | 0 | 0 | 0 | 2 |
| role_required | 19 | 16 | 0 | 0 | 0 | 0 | 10 | 2 |
| membership_required | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0 |
| owner_match | 56 | 38 | 0 | 0 | 13 | 0 | 3 | 4 |
| owner_or_admin | 2 | 0 | 0 | 0 | 0 | 8 | 0 | 1 |
| manual_review_required | 0 | 1 | 0 | 0 | 0 | 0 | 12 | 2 |

출처별 정확도: {"synthetic": {"records": 58, "accuracy": 0.9138}, "vuln": {"records": 207, "accuracy": 0.3188}}

public 오판 id: 759eb32d69ab1820e44d, ff8c5eda79000fa6687f, b3906a959a0b669047ba, aae57acca0e9317e81c1, 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, acdc8447219278841824, d93acb187b6c273464f0, d0afe4b052514b189dfa, 5928631c56d36ced026a, c3203410c4072686beaa, 15af38ebe8faf15c930f, 860383f68102b772bb99, 6bca6097b26cf226f405, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, dcc8f1be82d40ee3d5cf, c917e3e10dce94cc245c, fc9dac901542ca88d688, 5a72ac6384c12b441687, 4de2f44349d88f3d6b3a, d8c5cf5eb0bfbd488219, d553cdd9276767f1b1bc, 0b0918598294090d14c3, beacon_iot_catalogue_0, beacon_iot_catalogue_1

## oas_code/lora_v1: label별 P/R/F1

| label | support | P | R | F1 |
|---|---|---|---|---|
| public | 66 | 0.7429 | 0.3939 | 0.5149 |
| role_required | 47 | 0.3099 | 0.4681 | 0.3729 |
| membership_required | 4 | 0.2857 | 1.0 | 0.4444 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.88 | 0.386 | 0.5366 |
| owner_or_admin | 11 | 1.0 | 0.7273 | 0.8421 |
| manual_review_required | 15 | 0.1923 | 1.0 | 0.3226 |

혼동행렬(행=정답, 열=예측):

| 정답\예측 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required | output_error |
|---|---|---|---|---|---|---|---|---|
| public | 26 | 16 | 6 | 0 | 6 | 0 | 11 | 1 |
| role_required | 5 | 22 | 0 | 0 | 0 | 0 | 20 | 0 |
| membership_required | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0 |
| owner_match | 4 | 33 | 4 | 0 | 44 | 0 | 29 | 0 |
| owner_or_admin | 0 | 0 | 0 | 0 | 0 | 8 | 3 | 0 |
| manual_review_required | 0 | 0 | 0 | 0 | 0 | 0 | 15 | 0 |

출처별 정확도: {"synthetic": {"records": 58, "accuracy": 1.0}, "vuln": {"records": 207, "accuracy": 0.3333}}

public 오판 id: 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, 61f662463e13765b9478, d8c5cf5eb0bfbd488219, beacon_iot_catalogue_0, beacon_iot_catalogue_1
