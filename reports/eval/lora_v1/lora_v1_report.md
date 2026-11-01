> **eval-def v2 재계산: reports/eval_v30_redef.md 참조** (route_only 109건 제외 주지표, public 오판 재정의, 합성 분리). 아래 본문은 구 정의(eval-def v1) 기준 원문 그대로다.

# LoRA v1 (data-v1) — test_v30 평가 최종 보고서

run `lora_v1_run1`, GPU NVIDIA A100-SXM4-80GB, 베이스 `unsloth/Qwen2.5-7B-Instruct-bnb-4bit`, 프롬프트 v3.0.1(고정). 학습·평가 모두 같은 Colab 세션(A100)에서 실행했고 라벨 생성에는 API를 쓰지 않았다. Colab이 쓴 원본 보고서는 같은 폴더의 report.md, 원시 예측은 predictions_*.jsonl.

**data-v1 해시 검증**: hashes.json의 원본 해시(train_v30 `a99d30da2d29907e…`, val_v30 `62bdadb29cae7aaf…`, test_v30 `9bd47216575afc60…`, 프롬프트 `d0913c27b5de185e…`)가 AGENTS.md data-v1 기록과 일치(노트북 셀 4에서 assert 통과, verified_at 2026-10-22T05:45:50Z).

**하이퍼파라미터**: QLoRA 4bit, r=16, alpha=16, dropout=0.0, target=q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj, epochs=3, lr=0.0002, batch=2×grad_acc=4, max_seq_len=4096, seed=42. 학습 177 step, 19.0분, 최종 train_loss 0.2303, 재개 None.

train loss: step 5 0.750 → step 175 0.102; val loss: step 30 0.292, step 60 0.245, step 90 0.231, step 120 0.214, step 150 0.223, step 177 0.223.

어댑터는 Drive `blade_lora_v1/runs/lora_v1_run1/adapter/`에만 있고 로컬·git에는 없다(reports/untracked_artifacts.md에 경로 기록, 해시 미확인).

## 1. 요약

입력 조건: `oas` = 명세만(269건), `oas_code` = 명세 + 핸들러 원문(controller_text 있는 265건). public 오판 = security_state=declared인 건을 public으로 예측한 수(declared 64건). macro-F1은 support가 있는 label 평균(7종 모두 support 있음).

| 조건 | 모델 | macro-F1 | label 수 | manual 비율 | public 오판 | 출력 오류 | 평균 ms | 합성 정확도(58) | 취약 API 정확도(211/207) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| oas | (a) 베이스 + v3.0.1 | 0.572 | 7 | 28.6% | 27/64 | 35 | 1032.4 | 91.4% | 23.2% |
| oas | (b) LoRA v1 | 0.5636 | 7 | 68.4% | 11/64 | 0 | 1042.3 | 100.0% | 13.3% |
| oas_code | (a) 베이스 + v3.0.1 | 0.6457 | 7 | 9.4% | 33/64 | 11 | 1536.4 | 91.4% | 31.9% |
| oas_code | (b) LoRA v1 | 0.5762 | 7 | 29.4% | 7/64 | 1 | 1054.8 | 100.0% | 33.3% |
| oas | 참고: gpt-4o-mini + v3.0.1 (로컬 API) | N/A |  |  |  |  |  |  |  |
| oas | 참고: qwen2.5:7b Ollama CPU + v3.0.1 | N/A |  |  |  |  |  |  |  |

참고 열의 로컬 베이스라인(gpt-4o-mini·qwen CPU)은 test_v30 + v3.0.1 조합으로 아직 실행되지 않았다(기존 baseline_summary.md는 test.jsonl + v2.0 런타임이라 같은 표에 넣지 않는다).

## 2. oas / (a) 베이스 + v3.0.1 — label별 P/R/F1 (macro-F1 0.572, label 7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.452 | 0.788 | 0.575 |
| role_required | 51 | 0.6 | 0.176 | 0.273 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 1.0 | 0.079 | 0.146 |
| owner_or_admin | 11 | 1.0 | 0.545 | 0.706 |
| manual_review_required | 15 | 0.182 | 0.933 | 0.304 |

혼동행렬(행=정답, 열=예측):

| 정답\예측 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required | output_error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| public | 52 | 1 | 0 | 0 | 0 | 0 | 7 | 6 |
| role_required | 20 | 9 | 0 | 0 | 0 | 0 | 16 | 6 |
| membership_required | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0 |
| owner_match | 41 | 5 | 0 | 0 | 9 | 0 | 39 | 20 |
| owner_or_admin | 2 | 0 | 0 | 0 | 0 | 6 | 1 | 2 |
| manual_review_required | 0 | 0 | 0 | 0 | 0 | 0 | 14 | 1 |

public 오판 27건: 759eb32d69ab1820e44d, aae57acca0e9317e81c1, 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, d93acb187b6c273464f0, 15af38ebe8faf15c930f, 860383f68102b772bb99, 6bca6097b26cf226f405, cdd3d3e140b0b509bcd3, af6e2ae1b29132ee1d77, c085f5d6b9f87dd6d4a1, 324601a8dc9e9ea969bb, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, dcc8f1be82d40ee3d5cf, fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219, d553cdd9276767f1b1bc, 956a6feb1b1f65eb5a9a, 0b0918598294090d14c3, beacon_iot_catalogue_0, beacon_iot_catalogue_1

## 2. oas / (b) LoRA v1 — label별 P/R/F1 (macro-F1 0.5637, label 7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.958 | 0.348 | 0.511 |
| role_required | 51 | 0.526 | 0.196 | 0.286 |
| membership_required | 4 | 0.8 | 1.0 | 0.889 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.857 | 0.158 | 0.267 |
| owner_or_admin | 11 | 1.0 | 0.727 | 0.842 |
| manual_review_required | 15 | 0.082 | 1.0 | 0.151 |

혼동행렬(행=정답, 열=예측):

| 정답\예측 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required | output_error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| public | 23 | 1 | 0 | 0 | 2 | 0 | 40 | 0 |
| role_required | 0 | 10 | 0 | 0 | 1 | 0 | 40 | 0 |
| membership_required | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0 |
| owner_match | 1 | 8 | 1 | 0 | 18 | 0 | 86 | 0 |
| owner_or_admin | 0 | 0 | 0 | 0 | 0 | 8 | 3 | 0 |
| manual_review_required | 0 | 0 | 0 | 0 | 0 | 0 | 15 | 0 |

public 오판 11건: 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, 860383f68102b772bb99, 7a19e5a3a9eb0d5947f3, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, 58e3df2930d0ce4c3175, bb532c95786f45e07314, d553cdd9276767f1b1bc, beacon_iot_catalogue_0, beacon_iot_catalogue_1

## 2. oas_code / (a) 베이스 + v3.0.1 — label별 P/R/F1 (macro-F1 0.6457, label 7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.43 | 0.879 | 0.577 |
| role_required | 47 | 0.262 | 0.34 | 0.296 |
| membership_required | 4 | 1.0 | 1.0 | 1.0 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 1.0 | 0.114 | 0.205 |
| owner_or_admin | 11 | 1.0 | 0.727 | 0.842 |
| manual_review_required | 15 | 0.48 | 0.8 | 0.6 |

혼동행렬(행=정답, 열=예측):

| 정답\예측 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required | output_error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| public | 58 | 6 | 0 | 0 | 0 | 0 | 0 | 2 |
| role_required | 19 | 16 | 0 | 0 | 0 | 0 | 10 | 2 |
| membership_required | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0 |
| owner_match | 56 | 38 | 0 | 0 | 13 | 0 | 3 | 4 |
| owner_or_admin | 2 | 0 | 0 | 0 | 0 | 8 | 0 | 1 |
| manual_review_required | 0 | 1 | 0 | 0 | 0 | 0 | 12 | 2 |

public 오판 33건: 759eb32d69ab1820e44d, ff8c5eda79000fa6687f, b3906a959a0b669047ba, aae57acca0e9317e81c1, 149fc53d41cf49d52bb9, 9a7d3d59efab53f32063, acdc8447219278841824, d93acb187b6c273464f0, d0afe4b052514b189dfa, 5928631c56d36ced026a, c3203410c4072686beaa, 15af38ebe8faf15c930f, 860383f68102b772bb99, 6bca6097b26cf226f405, c085f5d6b9f87dd6d4a1, 3dc50d2c3650a204001d, d72193f9a1b7d79700d0, bc1dce3621c7da44ddfe, 58e3df2930d0ce4c3175, 61f662463e13765b9478, be8b11cdbabe4486aeda, 7e3f8c20d798e8b34143, bb532c95786f45e07314, dcc8f1be82d40ee3d5cf, c917e3e10dce94cc245c, fc9dac901542ca88d688, 5a72ac6384c12b441687, 4de2f44349d88f3d6b3a, d8c5cf5eb0bfbd488219, d553cdd9276767f1b1bc, 0b0918598294090d14c3, beacon_iot_catalogue_0, beacon_iot_catalogue_1

## 2. oas_code / (b) LoRA v1 — label별 P/R/F1 (macro-F1 0.5763, label 7종)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 66 | 0.743 | 0.394 | 0.515 |
| role_required | 47 | 0.31 | 0.468 | 0.373 |
| membership_required | 4 | 0.286 | 1.0 | 0.444 |
| tenant_match | 8 | 1.0 | 1.0 | 1.0 |
| owner_match | 114 | 0.88 | 0.386 | 0.537 |
| owner_or_admin | 11 | 1.0 | 0.727 | 0.842 |
| manual_review_required | 15 | 0.192 | 1.0 | 0.323 |

혼동행렬(행=정답, 열=예측):

| 정답\예측 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required | output_error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| public | 26 | 16 | 6 | 0 | 6 | 0 | 11 | 1 |
| role_required | 5 | 22 | 0 | 0 | 0 | 0 | 20 | 0 |
| membership_required | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0 |
| owner_match | 4 | 33 | 4 | 0 | 44 | 0 | 29 | 0 |
| owner_or_admin | 0 | 0 | 0 | 0 | 0 | 8 | 3 | 0 |
| manual_review_required | 0 | 0 | 0 | 0 | 0 | 0 | 15 | 0 |

public 오판 7건: 149fc53d41cf49d52bb9, c085f5d6b9f87dd6d4a1, d72193f9a1b7d79700d0, 61f662463e13765b9478, d8c5cf5eb0bfbd488219, beacon_iot_catalogue_0, beacon_iot_catalogue_1

## 3. 출처·OAS 유형별 정확도

취약 API 211건 중 route_only(명세 없음, 경로만) 109건·repository_spec 102건, 합성 58건(quill_blog·folio_wiki·beacon_iot·summit_club, OAS 원본 export).

| 조건/모델 | 구간 | N | 정확도 | macro-F1(support 있는 label) | manual 예측 비율 | public 오판 |
|---|---|---:|---:|---:|---:|---:|
| oas/base_v301 | 합성 | 58 | 91.4% | 0.9539 | 22.4% | 2 |
| oas/base_v301 | 취약 route_only | 109 | 17.4% | 0.1044 | 50.5% | 0 |
| oas/base_v301 | 취약 repository_spec | 102 | 29.4% | 0.2893 | 8.8% | 25 |
| oas/lora_v1 | 합성 | 58 | 100.0% | 1.0 | 24.1% | 2 |
| oas/lora_v1 | 취약 route_only | 109 | 0.9% | 0.0036 | 100.0% | 0 |
| oas/lora_v1 | 취약 repository_spec | 102 | 26.5% | 0.353 | 59.8% | 9 |
| oas_code/base_v301 | 합성 | 58 | 91.4% | 0.9543 | 19.0% | 2 |
| oas_code/base_v301 | 취약 route_only | 109 | 22.0% | 0.1474 | 12.8% | 0 |
| oas_code/base_v301 | 취약 repository_spec | 98 | 42.9% | 0.3863 | 0.0% | 31 |
| oas_code/lora_v1 | 합성 | 58 | 100.0% | 1.0 | 24.1% | 2 |
| oas_code/lora_v1 | 취약 route_only | 109 | 26.6% | 0.2154 | 42.2% | 0 |
| oas_code/lora_v1 | 취약 repository_spec | 98 | 40.8% | 0.4363 | 18.4% | 5 |

## 4. LoRA v1이 manual로 보낸 건의 정답 분포 (보류 편향 분석)

| 조건/모델 | manual 예측 수 | 그중 정답도 manual | 정답이 구체 label인 건(과보류) |
|---|---:|---:|---:|
| oas/lora_v1 | 184 | 15 | public 40 / role_required 40 / owner_match 86 / owner_or_admin 3 |
| oas_code/lora_v1 | 78 | 15 | public 11 / role_required 20 / owner_match 29 / owner_or_admin 3 |
| oas/base_v301 | 77 | 14 | public 7 / role_required 16 / owner_match 39 / owner_or_admin 1 |
| oas_code/base_v301 | 25 | 12 | role_required 10 / owner_match 3 |

## 5. 구체 label 6종만의 성능 (manual 제외, 보류 비용과 분리해 보기)

| 조건/모델 | 정답 구체 N | 구체로 예측한 수 | 구체 응답률 | 구체 응답 중 정답률(정밀도) | 전체 정답률(재현율) |
|---|---:|---:|---:|---:|---:|
| oas/base_v301 | 254 | 157 | 61.8% | 56.1% | 34.6% |
| oas/lora_v1 | 254 | 85 | 33.5% | 83.5% | 28.0% |
| oas_code/base_v301 | 250 | 228 | 91.2% | 46.9% | 42.8% |
| oas_code/lora_v1 | 250 | 186 | 74.4% | 60.2% | 44.8% |

## 6. 해석

- LoRA v1은 macro-F1을 올리지 못했다(oas 0.572→0.564, oas_code 0.646→0.576). 대신 출력 형식 오류를 없앴고(35→0, 11→1), security 선언 건의 public 오판을 크게 줄였다(27→11, 33→7).
- 그 대가로 보류가 늘었다(oas 28.6%→68.4%, oas_code 9.4%→29.4%). 4절처럼 보류 중 다수가 정답이 구체 label인 과보류다. data-v1이 manual 25% + "OAS만으로 관계 확인 불가 → 보류" 규칙으로 라벨된 데이터라 보류를 강하게 학습했다.
- 베이스 모델의 oas F1은 "모르면 public"으로 찍어 얻은 public recall(0.79, precision 0.45)에 기대고 있다. 같은 F1이라도 안전성은 반대다(LoRA public precision 0.96).
- 합성 58건은 두 조건 모두 LoRA가 100%로 올렸지만(베이스 91.4%), 합성 train 서비스와 템플릿을 공유하므로 낙관 편향이 있다. 취약 API 211건에서는 oas 조건에서 LoRA가 더 나빠졌고(23.2%→13.3%), oas_code 조건에서는 비슷하다(31.9%→33.3%).
- 취약 API 중 route_only 109건은 명세가 없어 oas 조건은 정보가 거의 없다. 의미 있는 비교는 oas_code 열이며, 거기서 LoRA의 약점은 코드가 있는 구체 사례가 train에 60건(합성)뿐인 점이다. data-v2(Gitea 구체 93건 + 코드 변형 129건)가 이 부분을 겨냥한다.
- tenant_match 8·membership_required 4·owner_or_admin 11건은 support가 작아 해당 label 점수는 불안정하다. membership·tenant 정답은 전부 합성이다.

## 7. 한계

- 단일 run(seed 42), 반복 없음. val_v30 52건은 조기 종료·선택에 쓰지 않았다(eval loss만 기록).
- 어댑터 파일은 Drive에만 있어 해시를 확인하지 못했다. 재현하려면 같은 노트북·같은 data-v1·seed 42로 다시 학습해야 한다.
- 로컬 베이스라인(gpt-4o-mini, qwen CPU)의 test_v30 + v3.0.1 수치는 아직 없다.
