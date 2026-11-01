# LoRA v4 보조 지표 (사후 정의) — 기존 예측 재채점

- 작업 A: 학습·추론·문턱 변경 없음. reports/eval/lora_v4/*/eval/ 의 oas_code 조건 예측 파일만 다시 채점했다(2026-10-31).
- **주지표(eval-def v2 macro-F1, scripts/eval_v30.py)는 그대로다.** 아래는 사후에 정의한 보조 지표이며 주지표를 대체하지 않는다. 재채점 과정에서 7-class 표준 macro-F1·출력 오류 건수가 기존 scores_test_v30.json·scores_supp.json 과 일치함을 assert 했다.
- 모델: base(어댑터 없음, 단일 run — seed 편차 없음), v2·v3b·v4 각 seed 42·43·44. 수치는 seed 평균 ± 표본표준편차. 표준편차보다 큰 차이만 차이로 인정한다.
- 데이터: A = test_v30 oas_code 합성 제외 207건, B = test_v31_supp oas_code 222건, C = A ∪ B 429건. 출력 오류(JSON 파싱 실패)는 어떤 label 도 아닌 오답이며 1번 지표에서는 보류로 함께 뺀다.
- 해시 assert: test_v30 `9bd47216575afc60…`, test_v31_supp `803d914902c7ca20…`, segments.json `76f3210137fc8723…`, data-v1 guard 통과. 예측 파일 24개 SHA-256 은 supplementary_metrics.json 에 기록.

## 지표 정의

1. **구체 label macro-F1(보류 제외)**: 예측이 manual_review_required 이거나 출력 오류인 건을 보류로 보고 제외한 뒤, 남은 건에서 6개 구체 label 의 P/R/F1 을 계산하고 해당 셋에 정답 support 가 있는 구체 label 만 평균한다(A 는 public·role_required·owner_match·owner_or_admin 4종, B·C 는 6종). 정답이 manual 인 건이 구체로 답해지면 그 label 의 FP 다. **커버리지** = 1 − 보류율(manual 예측 + 출력 오류). 커버리지가 낮을수록 같은 F1 이라도 적용 범위가 좁으므로 반드시 함께 읽는다.
   - 변형(보류=누락): 정밀도 분모는 응답 건, 재현율 분모는 전체 정답 건. 보류한 정답 구체 건은 재현율 누락이다. 커버리지 차이를 F1 에 반영한 값이다.
2. **support ≥ 10 label macro-F1**: eval-def v2 와 같은 7-class 채점(manual 도 class, 보류 제외 없음)에서 그 셋의 정답 support ≥ 10 인 label 만 평균. 포함 label 은 표에 명시.
3. **label별 F1 + support(C 합산)**: 7-class 표준 F1 과 1번의 보류 제외 F1 을 각각 표로 싣는다.
4. **seed별 출력 오류**: prediction 없음(JSON 파싱 실패) 건수.

## A. test_v30 oas_code 합성 제외 (207)

정답 support: public 58, role_required 39, owner_match 106, owner_or_admin 3, manual_review_required 1

### 1. 구체 label macro-F1(보류 제외)과 커버리지

| 모델 | 구체 macro-F1(보류 제외) | 커버리지 | manual 예측률 | 출력 오류율 | 응답 건 정확도 | 변형: 보류=누락 macro-F1 | 포함 label |
|---|---:|---:|---:|---:|---:|---:|---|
| base | 0.224 | 0.889 | 0.068 | 0.043 | 0.353 | 0.213 | public, role_required, owner_match, owner_or_admin |
| v2 | 0.511 ± 0.024 | 0.572 ± 0.072 | 0.420 ± 0.066 | 0.008 ± 0.006 | 0.721 ± 0.032 | 0.368 ± 0.048 | public, role_required, owner_match, owner_or_admin |
| v3b | 0.465 ± 0.035 | 0.804 ± 0.064 | 0.184 ± 0.063 | 0.013 ± 0.007 | 0.643 ± 0.028 | 0.409 ± 0.021 | public, role_required, owner_match, owner_or_admin |
| v4 | 0.562 ± 0.045 | 0.684 ± 0.070 | 0.298 ± 0.056 | 0.018 ± 0.016 | 0.811 ± 0.025 | 0.437 ± 0.055 | public, role_required, owner_match, owner_or_admin |

### 2. support ≥ 10 label macro-F1 (7-class 표준 채점)

| 모델 | support≥10 macro-F1 | 참고: support>0 전체 macro-F1(eval-def v2 방식) | 포함 label |
|---|---:|---:|---|
| base | 0.283 | 0.197 | public (58), role_required (39), owner_match (106) |
| v2 | 0.490 ± 0.063 | 0.299 ± 0.039 | public (58), role_required (39), owner_match (106) |
| v3b | 0.545 ± 0.028 | 0.338 ± 0.017 | public (58), role_required (39), owner_match (106) |
| v4 | 0.583 ± 0.074 | 0.356 ± 0.045 | public (58), role_required (39), owner_match (106) |

### 4. seed별 출력 오류 건수

| 모델 | seed 42 | seed 43 | seed 44 |
|---|---:|---:|---:|
| base | 9 | - | - |
| v2 | 1 | 1 | 3 |
| v3b | 1 | 3 | 4 |
| v4 | 5 | 6 | 0 |

## B. test_v31_supp oas_code (222)

정답 support: public 2, role_required 39, membership_required 55, tenant_match 55, owner_match 21, owner_or_admin 20, manual_review_required 30

### 1. 구체 label macro-F1(보류 제외)과 커버리지

| 모델 | 구체 macro-F1(보류 제외) | 커버리지 | manual 예측률 | 출력 오류율 | 응답 건 정확도 | 변형: 보류=누락 macro-F1 | 포함 label |
|---|---:|---:|---:|---:|---:|---:|---|
| base | 0.058 | 0.698 | 0.000 | 0.302 | 0.142 | 0.056 | public, role_required, membership_required, tenant_match, owner_match, owner_or_admin |
| v2 | 0.436 ± 0.017 | 0.905 ± 0.028 | 0.089 ± 0.021 | 0.006 ± 0.007 | 0.355 ± 0.005 | 0.425 ± 0.019 | public, role_required, membership_required, tenant_match, owner_match, owner_or_admin |
| v3b | 0.473 ± 0.027 | 0.963 ± 0.007 | 0.019 ± 0.005 | 0.018 ± 0.004 | 0.378 ± 0.040 | 0.470 ± 0.026 | public, role_required, membership_required, tenant_match, owner_match, owner_or_admin |
| v4 | 0.546 ± 0.044 | 0.757 ± 0.056 | 0.233 ± 0.050 | 0.010 ± 0.007 | 0.453 ± 0.027 | 0.492 ± 0.037 | public, role_required, membership_required, tenant_match, owner_match, owner_or_admin |

### 2. support ≥ 10 label macro-F1 (7-class 표준 채점)

| 모델 | support≥10 macro-F1 | 참고: support>0 전체 macro-F1(eval-def v2 방식) | 포함 label |
|---|---:|---:|---|
| base | 0.045 | 0.048 | role_required (39), membership_required (55), tenant_match (55), owner_match (21), owner_or_admin (20), manual_review_required (30) |
| v2 | 0.308 ± 0.005 | 0.387 ± 0.017 | role_required (39), membership_required (55), tenant_match (55), owner_match (21), owner_or_admin (20), manual_review_required (30) |
| v3b | 0.322 ± 0.026 | 0.419 ± 0.022 | role_required (39), membership_required (55), tenant_match (55), owner_match (21), owner_or_admin (20), manual_review_required (30) |
| v4 | 0.367 ± 0.019 | 0.448 ± 0.030 | role_required (39), membership_required (55), tenant_match (55), owner_match (21), owner_or_admin (20), manual_review_required (30) |

### 4. seed별 출력 오류 건수

| 모델 | seed 42 | seed 43 | seed 44 |
|---|---:|---:|---:|
| base | 67 | - | - |
| v2 | 0 | 1 | 3 |
| v3b | 3 | 5 | 4 |
| v4 | 4 | 2 | 1 |

## C. 두 셋 합산 (429)

정답 support: public 60, role_required 78, membership_required 55, tenant_match 55, owner_match 127, owner_or_admin 23, manual_review_required 31

### 1. 구체 label macro-F1(보류 제외)과 커버리지

| 모델 | 구체 macro-F1(보류 제외) | 커버리지 | manual 예측률 | 출력 오류율 | 응답 건 정확도 | 변형: 보류=누락 macro-F1 | 포함 label |
|---|---:|---:|---:|---:|---:|---:|---|
| base | 0.138 | 0.790 | 0.033 | 0.177 | 0.257 | 0.132 | public, role_required, membership_required, tenant_match, owner_match, owner_or_admin |
| v2 | 0.451 ± 0.009 | 0.744 ± 0.049 | 0.249 ± 0.043 | 0.007 ± 0.006 | 0.491 ± 0.020 | 0.383 ± 0.023 | public, role_required, membership_required, tenant_match, owner_match, owner_or_admin |
| v3b | 0.436 ± 0.019 | 0.886 ± 0.034 | 0.099 ± 0.032 | 0.015 ± 0.005 | 0.494 ± 0.019 | 0.410 ± 0.005 | public, role_required, membership_required, tenant_match, owner_match, owner_or_admin |
| v4 | 0.562 ± 0.012 | 0.722 ± 0.055 | 0.264 ± 0.045 | 0.014 ± 0.010 | 0.617 ± 0.018 | 0.460 ± 0.017 | public, role_required, membership_required, tenant_match, owner_match, owner_or_admin |

### 2. support ≥ 10 label macro-F1 (7-class 표준 채점)

| 모델 | support≥10 macro-F1 | 참고: support>0 전체 macro-F1(eval-def v2 방식) | 포함 label |
|---|---:|---:|---|
| base | 0.119 | 0.119 | public (60), role_required (78), membership_required (55), tenant_match (55), owner_match (127), owner_or_admin (23), manual_review_required (31) |
| v2 | 0.338 ± 0.019 | 0.338 ± 0.019 | public (60), role_required (78), membership_required (55), tenant_match (55), owner_match (127), owner_or_admin (23), manual_review_required (31) |
| v3b | 0.363 ± 0.002 | 0.363 ± 0.002 | public (60), role_required (78), membership_required (55), tenant_match (55), owner_match (127), owner_or_admin (23), manual_review_required (31) |
| v4 | 0.412 ± 0.016 | 0.412 ± 0.016 | public (60), role_required (78), membership_required (55), tenant_match (55), owner_match (127), owner_or_admin (23), manual_review_required (31) |

### 4. seed별 출력 오류 건수

| 모델 | seed 42 | seed 43 | seed 44 |
|---|---:|---:|---:|
| base | 76 | - | - |
| v2 | 1 | 2 | 6 |
| v3b | 4 | 8 | 8 |
| v4 | 9 | 8 | 1 |

## 3. label별 F1 + support (C 합산 429건)

### 3a. 7-class 표준 F1 (보류 제외 없음)

| 모델 | public (60) | role_required (78) | membership_required (55) | tenant_match (55) | owner_match (127) | owner_or_admin (23) | manual_review_required (31) |
|---|---:|---:|---:|---:|---:|---:|---:|
| base | 0.468 | 0.253 | 0.000 | 0.000 | 0.071 | 0.000 | 0.044 |
| v2 | 0.497 ± 0.049 | 0.302 ± 0.028 | 0.587 ± 0.049 | 0.036 ± 0.000 | 0.590 ± 0.052 | 0.284 ± 0.021 | 0.072 ± 0.006 |
| v3b | 0.474 ± 0.061 | 0.380 ± 0.021 | 0.546 ± 0.036 | 0.059 ± 0.020 | 0.665 ± 0.004 | 0.337 ± 0.018 | 0.084 ± 0.014 |
| v4 | 0.532 ± 0.123 | 0.409 ± 0.025 | 0.524 ± 0.025 | 0.276 ± 0.099 | 0.729 ± 0.010 | 0.292 ± 0.005 | 0.121 ± 0.017 |

### 3b. 보류 제외 F1 (6개 구체 label; 보류 건 제외 후 계산)

| 모델 | public (60) | role_required (78) | membership_required (55) | tenant_match (55) | owner_match (127) | owner_or_admin (23) |
|---|---:|---:|---:|---:|---:|---:|
| base | 0.477 | 0.273 | 0.000 | 0.000 | 0.079 | 0.000 |
| v2 | 0.659 ± 0.015 | 0.353 ± 0.023 | 0.611 ± 0.043 | 0.038 ± 0.000 | 0.721 ± 0.019 | 0.322 ± 0.036 |
| v3b | 0.528 ± 0.062 | 0.414 ± 0.032 | 0.552 ± 0.033 | 0.062 ± 0.020 | 0.703 ± 0.010 | 0.358 ± 0.021 |
| v4 | 0.675 ± 0.081 | 0.485 ± 0.036 | 0.608 ± 0.002 | 0.473 ± 0.157 | 0.799 ± 0.022 | 0.332 ± 0.010 |

### 3c. 보류 제외 정밀도 / 재현율 (C, 6개 구체 label)

| 모델 | public P / R | role_required P / R | membership_required P / R | tenant_match P / R | owner_match P / R | owner_or_admin P / R |
|---|---:|---:|---:|---:|---:|---:|
| base | 0.32 / 0.91 | 0.19 / 0.52 | 0.00 / 0.00 | 0.00 / 0.00 | 0.36 / 0.04 | 0.00 / 0.00 |
| v2 | 0.73 ± 0.05 / 0.60 ± 0.03 | 0.25 ± 0.02 / 0.62 ± 0.02 | 0.61 ± 0.05 / 0.61 ± 0.04 | 1.00 ± 0.00 / 0.02 ± 0.00 | 0.68 ± 0.03 / 0.76 ± 0.04 | 0.34 ± 0.05 / 0.31 ± 0.05 |
| v3b | 0.83 ± 0.02 / 0.39 ± 0.06 | 0.30 ± 0.03 / 0.66 ± 0.03 | 0.52 ± 0.06 / 0.62 ± 0.16 | 1.00 ± 0.00 / 0.03 ± 0.01 | 0.68 ± 0.05 / 0.74 ± 0.04 | 0.31 ± 0.04 / 0.43 ± 0.03 |
| v4 | 0.79 ± 0.06 / 0.59 ± 0.09 | 0.43 ± 0.03 / 0.56 ± 0.05 | 0.66 ± 0.06 / 0.57 ± 0.05 | 0.97 ± 0.05 / 0.32 ± 0.14 | 0.71 ± 0.04 / 0.92 ± 0.01 | 0.29 ± 0.04 / 0.40 ± 0.05 |

### 3d. 보류 제외 label별 응답 건수 (C, seed 평균; 보류로 빠진 정답 건 = support − 응답)

| 모델 | public (60) | role_required (78) | membership_required (55) | tenant_match (55) | owner_match (127) | owner_or_admin (23) |
|---|---:|---:|---:|---:|---:|---:|
| base | 56.0 | 60.0 | 24.0 | 40.0 | 113.0 | 19.0 |
| v2 | 37.7 ± 5.0 | 48.7 ± 4.0 | 50.7 ± 1.5 | 51.7 ± 0.6 | 86.7 ± 9.3 | 18.3 ± 1.2 |
| v3b | 52.0 ± 8.7 | 61.0 ± 4.0 | 53.7 ± 0.6 | 52.0 ± 1.0 | 113.7 ± 2.3 | 20.0 ± 0.0 |
| v4 | 40.7 ± 6.8 | 54.7 ± 3.8 | 42.3 ± 4.0 | 28.3 ± 6.7 | 104.3 ± 5.1 | 17.3 ± 0.6 |
## 5. public 오판 (신 정의, 사후 추가) — 기존 채점에 없던 supp·합산 분모

기존 채점 결과 확인: scores_test_v30.json 에는 신 정의 public 오판(분모 declared ∧ 정답≠public = 47, 합성 포함 265건 기준)이 있으나 scores_supp.json 에는 public 오판 항목이 없다. 여기서는 세 셋을 같은 정의로 다시 센다. A 는 합성 제외 207건 기준이라 분모가 47 이 아니라 35 다(합성 beacon_iot 의 declared ∧ 비public 12건 제외). security_state 는 test 파일 값(eval_v30.py security_state() 와 같은 규칙: operation 또는 spec 에 security 선언)이며 supp 는 declared 192 · unknown 30(chamilo 8 · generic_university 21 · multitenant_lab 1).

### A. test_v30 oas_code 합성 제외 (207) — declared 50, 분모(declared ∧ 정답≠public) 35, unknown 157

| 모델 | 오판 건수(seed별) | 오판률 | 구 정의 건수(declared ∧ 예측 public, seed별) | 오판 정답 label(seed 합) | 오판 프로젝트(seed 합) | unknown ∧ 예측 public ∧ 정답≠public(seed별) |
|---|---:|---:|---:|---|---|---:|
| base | 17 | 0.486 | 30 | owner_match 17 | test_v30 17 | 60 |
| v2 | 2 / 1 / 0 | 0.029 ± 0.029 | 9 / 5 / 4 | owner_match 3 | test_v30 3 | 5 / 6 / 9 |
| v3b | 0 / 0 / 0 | 0.000 ± 0.000 | 6 / 4 / 3 | - | - | 4 / 4 / 4 |
| v4 | 1 / 0 / 0 | 0.010 ± 0.017 | 9 / 2 / 10 | owner_match 1 | test_v30 1 | 4 / 6 / 6 |

### B. test_v31_supp oas_code (222) — declared 192, 분모(declared ∧ 정답≠public) 191, unknown 30

| 모델 | 오판 건수(seed별) | 오판률 | 구 정의 건수(declared ∧ 예측 public, seed별) | 오판 정답 label(seed 합) | 오판 프로젝트(seed 합) | unknown ∧ 예측 public ∧ 정답≠public(seed별) |
|---|---:|---:|---:|---|---|---:|
| base | 15 | 0.079 | 15 | tenant_match 6, membership_required 3, owner_match 3, manual_review_required 2, owner_or_admin 1 | chatwoot 6, flowise 6, multitenant_lab 3 | 15 |
| v2 | 0 / 0 / 0 | 0.000 ± 0.000 | 1 / 1 / 1 | - | - | 1 / 0 / 1 |
| v3b | 0 / 0 / 0 | 0.000 ± 0.000 | 1 / 1 / 1 | - | - | 0 / 0 / 0 |
| v4 | 1 / 0 / 0 | 0.002 ± 0.003 | 2 / 1 / 1 | tenant_match 1 | flowise 1 | 0 / 0 / 0 |

### C. 두 셋 합산 (429) — declared 242, 분모(declared ∧ 정답≠public) 226, unknown 187

| 모델 | 오판 건수(seed별) | 오판률 | 구 정의 건수(declared ∧ 예측 public, seed별) | 오판 정답 label(seed 합) | 오판 프로젝트(seed 합) | unknown ∧ 예측 public ∧ 정답≠public(seed별) |
|---|---:|---:|---:|---|---|---:|
| base | 32 | 0.142 | 45 | owner_match 20, tenant_match 6, membership_required 3, manual_review_required 2, owner_or_admin 1 | test_v30 17, chatwoot 6, flowise 6, multitenant_lab 3 | 75 |
| v2 | 2 / 1 / 0 | 0.004 ± 0.004 | 10 / 6 / 5 | owner_match 3 | test_v30 3 | 6 / 6 / 10 |
| v3b | 0 / 0 / 0 | 0.000 ± 0.000 | 7 / 5 / 4 | - | - | 4 / 4 / 4 |
| v4 | 2 / 0 / 0 | 0.003 ± 0.005 | 11 / 3 / 11 | owner_match 1, tenant_match 1 | test_v30 1, flowise 1 | 4 / 6 / 6 |


## 판정 (표준편차보다 큰 차이만 차이로 인정; 수치는 위 표, 2026-10-31 재채점 결과에 근거)

보조 지표는 주지표를 대체하지 않는다. 특히 1번(보류 제외 F1)은 보류를 많이 할수록 유리하므로 커버리지와 변형(보류=누락)을 같이 읽어야 한다.

- **C 합산 429건, 보류 제외 구체 macro-F1**: v4 0.562 ± 0.012 > v2 0.451 ± 0.009 ≈ v3b 0.436 ± 0.019 (v4 와의 차이 0.11 이상, 표준편차의 5배 이상). v2 와 v3b 는 차이 없음(0.015 < 0.019).
  - 커버리지는 v3b 0.886 ± 0.034 가 v4 0.722 ± 0.055 · v2 0.744 ± 0.049 보다 높다(차이 0.14 이상 > 표준편차). v4 와 v2 는 차이 없음.
  - 보류를 누락으로 넣는 변형에서도 v4 0.460 ± 0.017 > v3b 0.410 ± 0.005 (차이 0.050 > 0.017). v3b 와 v2 0.383 ± 0.023 의 차이 0.027 은 v2 표준편차(0.023)와 비슷해 경계.
  - 응답 건 정확도: v4 0.617 ± 0.018 > v3b 0.494 ± 0.019 ≈ v2 0.491 ± 0.020. v4 는 구체로 답한 건에서 가장 정확하고, 그 대신 v3b 보다 보류가 많다.
- **A test_v30 207건**: 보류 제외 F1 은 v4 0.562 ± 0.045 > v3b 0.465 ± 0.035 (차이 0.097). v2 0.511 ± 0.024 는 v3b 보다 높지만(차이 0.046) 커버리지가 0.572 ± 0.072 로 v3b(0.804 ± 0.064)보다 0.23 낮다. 변형(보류=누락)에서는 v4 0.437 ± 0.055 vs v3b 0.409 ± 0.021 로 차이 없음(0.028 < 0.055). support ≥ 10 macro-F1(public·role_required·owner_match 3종) 도 v4 0.583 ± 0.074 vs v3b 0.545 ± 0.028 은 차이 없음(0.038 < 0.074); v4 vs v2 0.490 ± 0.063 은 차이 0.093 으로 인정. 주지표가 0.3 대인 것은 support 3·1 인 owner_or_admin·manual 이 평균에 들어가기 때문이며, 3종만 보면 0.5 대다.
- **B test_v31_supp 222건**: 보류 제외 F1 v4 0.546 ± 0.044 > v3b 0.473 ± 0.027 (차이 0.073) > v2 0.436 ± 0.017 (차이 0.037, 경계). 커버리지는 v3b 0.963 ± 0.007 > v2 0.905 ± 0.028 > v4 0.757 ± 0.056. 변형에서는 v4 vs v3b 차이 없음(0.022 < 0.037). support ≥ 10 macro-F1(6종, public 제외): v4 0.367 ± 0.019 > v3b 0.322 ± 0.026 (차이 0.045); v3b 와 v2 0.308 ± 0.005 는 차이 없음.
- **C label별(보류 제외 F1, 3b)**: v4 가 v3b 보다 표준편차를 넘어 높은 label 은 public(0.675 vs 0.528), role_required(0.485 vs 0.414), membership_required(0.608 vs 0.552), tenant_match(0.473 ± 0.157 vs 0.062), owner_match(0.799 vs 0.703). owner_or_admin(23건)은 세 모델 모두 0.32~0.36 으로 차이 없음. tenant_match 는 v4 가 55건 중 평균 28.3건만 구체로 답해(나머지 보류) 정밀도 0.97 · 재현율 0.32 이고 seed 편차(± 0.157)가 커서 수치보다 방향만 읽는다. v2 대비로는 public·membership 이 차이 없고 role_required·tenant_match·owner_match 만 v4 가 높다.
- **출력 오류(4번)**: 합산 C 에서 base 76(supp 222건 중 67 = 30%), v2 1/2/6, v3b 4/8/8, v4 9/8/1. v4 는 seed 편차가 커서(1~9) v3b 와 우열을 말할 수 없다. base 의 supp 커버리지 0.698 은 manual 예측이 아니라 출력 오류 때문이다.
- base 는 단일 run 이라 표준편차가 없으며, 모든 지표에서 LoRA 세 모델보다 낮다(합산 보류 제외 F1 0.138, support ≥ 10 0.119).
- **public 오판(5번, 신 정의)**: 기존 채점에는 test_v30 분모(47, 합성 포함)만 있고 supp 분모는 없었다. supp 분모 191(declared 192 중 정답 public 1 제외)에서 v2·v3b 0/0/0, v4 1/0/0(Flowise GET /api/v1/upsert-history/{id}, 정답 tenant_match, seed 42만), base 15(tenant_match 6·membership 3·owner_match 3·manual 2·owner_or_admin 1). 합산 분모 226 에서 v4 2/0/0 · v2 2/1/0 · v3b 0/0/0 으로 LoRA 세 모델은 모두 1% 미만이고 서로 차이 없음(표준편차 안). test_v30 쪽 v4·v2 의 오판 1건은 같은 레코드(crAPI POST /identity/api/v2/vehicle/resend_email, 정답 owner_match)다. 구 정의(declared ∧ 예측 public) 건수가 더 큰 것은 정답이 public 인 declared 건(test_v30 합성 제외 15건)을 세기 때문이며 오판이 아니다. unknown 구간(security 미선언)에서 비public 정답에 public 을 답한 건은 정의상 오판에 들어가지 않지만 참고로 적었다(LoRA 세 모델 합산 4~10건, base 75건).

요약: 보류를 뺀 구체 label 성능과 응답 건 정확도는 v4 가 v2·v3b 보다 일관되게 높다(세 셋 모두, 합산에서는 표준편차의 5배 이상). 커버리지는 v3b 가 가장 높고 v4 는 v2 수준이다. 보류를 누락으로 세면 v4 의 우위는 합산·supp 에서는 유지되나 test_v30 단독에서는 표준편차 안이다. 주지표(eval-def v2 macro-F1) 판정 "v4 vs v3b 차이 없음"은 바뀌지 않는다.

원자료: reports/eval/lora_v4/supplementary_metrics.json (run별 전체 수치, 예측 파일 해시). 스크립트: scripts/eval_lora_v4_supplementary.py.
