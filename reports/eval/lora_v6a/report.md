# S5 LoRA v6a 보고 — 프롬프트 v3.1 + 근거 먼저 출력 + label 토큰 확률 confidence (2026-11-04, 3 seed, 커밋 없음)

사전 기록 AGENTS.md "작업 S5". 데이터 data-v5 그대로(label·rationale·user 불변, assistant 키 순서만 변경), 프롬프트 policy_label_v3.1.md(3,798 토큰), max_seq_len 6144(유일한 하이퍼파라미터 변경), max_new_tokens 512, 기본 디코딩(greedy). 판정셋 test_v5 283(dev, oas_code) + 회귀 test_v30 oas_code 합성 제외 207. v5 수치는 reports/eval/lora_v5의 기존 예측 파일을 같은 채점기로 재채점한 값(재추론 없음). test_v6은 추론하지 않았다. 주지표·발표 수치(v5)는 바꾸지 않는다.

## 1. 판정 — 사전 기준 3개 모두 미달, **불채택**

| 기준(3 seed 평균) | v5 | v6a | 차이 | 기준 | 충족 |
|---|---:|---:|---:|---|---|
| (1) test_v5 oas_code macro-F1 상승 ≥ 0.016 | 0.683 ± 0.016 | 0.549 ± 0.008 | -0.134 | ≥ +0.016 | **아니오** |
| (2) test_v30 207 구체 정밀도 하락 ≤ 0.025 | 0.796 ± 0.025 | 0.607 ± 0.056 | -0.188 | 하락 ≤ 0.025 | **아니오** |
| (3) test_v30 207 public 오판(/35) 평균 ≤ 2.0 | 3 / 2 / 1 (평균 2.00) | 5 / 7 / 3 (평균 5.00) | +3.00 | ≤ 2.0 | **아니오** |

세 기준 모두 미달이라 v6a는 채택하지 않는다. v5(프롬프트 v3.0.1, 발표 주 수치)는 그대로다. test_v5에서는 보류(manual)가 늘고 membership_required·owner_or_admin F1이 크게 떨어졌으며, test_v30에서는 반대로 보류가 6.6%까지 줄면서 틀린 구체 답(특히 public)이 늘었다(4·5절). seed 간 예측이 갈린 레코드도 v5 69건 → v6a 143건으로 늘어 불안정하다.

## 2. 실행 환경·학습

- Pod: RunPod y3fn8g1psetyh8, NVIDIA H100 80GB HBM3 79 GB, torch 2.14.1+cu130(CUDA 13.0), transformers 5.17.0, trl 1.15.0, peft 0.21.2, unsloth 2026.11.1, python 3.12.3. 2026-11-03 23:21 UTC 시작 → 11-04 01:33 UTC 종료(2시간 12분, 설치·preflight 포함), 번들 blade_v6a_20261104.tgz(`91c0c204…`), 해시 게이트(data_v6a_hashes.json `c079b9f5…`, test_v5_manifest `57fd384f…`) 통과, Pod 자동 정지.
- v5 환경(비교): NVIDIA A100-SXM4-80GB, torch 2.14.1+cu130, transformers 5.17.0, unsloth 2026.10.11. 이번 Pod의 unsloth는 'Padding-free batching'을 자동으로 켰다(로그 `Padding-free auto-enabled`; v5 로그에는 없음). 손실 값은 같은 정의이나 배치 구성이 달라 v5와 완전히 같은 실행 환경은 아니다.
- 첫 시도는 RTX PRO 4000 Blackwell Pod(02c4twegbgj8g3)에서 시작했으나 학습 전(setup 단계)에 중단하고 H100으로 옮겼다. 결과는 H100 1회 실행분이다.
- 손실 마스킹(completion-only) 확인: 학습 시작 시 0번 행 `loss mask check (row 0): 3956/4049 tokens masked (-100), 93 assistant tokens in loss` (3 seed 동일). v5와 같은 train_on_responses_only 호출.

| run | steps | 학습 분 | train_loss | val oas loss(final / 최저) | val oas_code loss(final / 최저) | v5 같은 seed train_loss / val final(oas, oas_code) / 분 |
|---|---:|---:|---:|---|---|---|
| lora_v6a_s42 | 480 | 32.6 | 0.1488 | 0.2748 / 0.255 | 0.1504 / 0.1455 | 0.1464 / 0.2425, 0.1469 / 56.2 |
| lora_v6a_s43 | 480 | 32.5 | 0.1531 | 0.2652 / 0.2488 | 0.1381 / 0.1355 | 0.15 / 0.2479, 0.1447 / 56.2 |
| lora_v6a_s44 | 480 | 32.5 | 0.1517 | 0.2614 / 0.2467 | 0.1489 / 0.1418 | 0.1483 / 0.2535, 0.1404 / 56.1 |

val은 학습 정상 여부 확인용이며(발산 없음, 세 seed 모두 480 step 완주) 체크포인트 선택에 쓰지 않았다(final 고정). val loss는 v5와 비슷하거나 약간 높다(v3.1 프롬프트가 길어 같은 데이터의 손실 비교는 참고치).

## 3. test_v5 283 (dev) — oas_code

| 모델 | macro-F1 | 정확도 | manual 비율 | manual 건수(seed별) | 출력 오류(합) |
|---|---:|---:|---:|---|---:|
| lora_v5 | 0.683 ± 0.016 | 0.691 ± 0.007 | 16.6 ± 1.6% | 46 / 43 / 52 | 3 |
| lora_v6a | 0.549 ± 0.008 | 0.592 ± 0.023 | 31.4 ± 8.6% | 76 / 74 / 117 | 0 |

### label별 F1 (support)

| 모델 | public (19) | role_required (111) | membership_required (33) | tenant_match (0) | owner_match (34) | owner_or_admin (21) | manual_review_required (65) |
|---|---:|---:|---:|---:|---:|---:|---:|
| lora_v5 | 0.894 ± 0.063 | 0.818 ± 0.026 | 0.589 ± 0.048 | 0.000 ± 0.000 | 0.760 ± 0.024 | 0.536 ± 0.031 | 0.499 ± 0.027 |
| lora_v6a | 0.803 ± 0.107 | 0.702 ± 0.051 | 0.243 ± 0.128 | 0.000 ± 0.000 | 0.728 ± 0.044 | 0.345 ± 0.070 | 0.472 ± 0.032 |

### 판정 label 정밀도 / 재현율 (seed별)

| run | owner_or_admin P / R / F1 | membership_required P / R / F1 | role_required P / R / F1 | public P / R / F1 |
|---|---|---|---|---|
| lora_v5_s42 | 0.500 / 0.619 / 0.553 | 0.453 / 0.727 / 0.558 | 0.867 / 0.820 / 0.843 | 0.933 / 0.737 / 0.824 |
| lora_v5_s43 | 0.400 / 0.667 / 0.500 | 0.518 / 0.849 / 0.644 | 0.838 / 0.748 / 0.790 | 1.000 / 0.842 / 0.914 |
| lora_v5_s44 | 0.455 / 0.714 / 0.556 | 0.489 / 0.667 / 0.564 | 0.861 / 0.784 / 0.821 | 1.000 / 0.895 / 0.944 |
| lora_v6a_s42 | 0.333 / 0.238 / 0.278 | 0.562 / 0.273 / 0.367 | 0.770 / 0.694 / 0.730 | 0.750 / 0.789 / 0.769 |
| lora_v6a_s43 | 0.370 / 0.476 / 0.417 | 0.667 / 0.061 / 0.111 | 0.778 / 0.694 / 0.733 | 0.559 / 1.000 / 0.717 |
| lora_v6a_s44 | 0.350 / 0.333 / 0.342 | 0.714 / 0.151 / 0.250 | 0.889 / 0.504 / 0.644 | 0.900 / 0.947 / 0.923 |

### 프로젝트별 정확도

| 모델 | rocketchat (157) | ghost (69) | umami (57) |
|---|---:|---:|---:|
| lora_v5 | 0.656 ± 0.013 | 0.758 ± 0.008 | 0.708 ± 0.066 |
| lora_v6a | 0.582 ± 0.051 | 0.585 ± 0.036 | 0.632 ± 0.046 |

### 혼동표 (정답 행 → 예측 열, 3 seed 평균 건수)

| 정답 \ 예측 | public | role | member | tenant | owner | own+adm | manual | ERR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **public** (v5) | 15.7 | 0 | 0 | 0 | 0 | 0 | 3.3 | 0 |
| public (v6a) | 17.3 | 0 | 0 | 0 | 0 | 0 | 1.7 | 0 |
| **role** (v5) | 0 | 87 | 7.3 | 0 | 1.3 | 6 | 8.7 | 0.7 |
| role (v6a) | 2.7 | 70 | 1 | 0 | 0.7 | 4.3 | 32.3 | 0 |
| **member** (v5) | 0 | 0 | 24.7 | 0 | 4.3 | 0.3 | 3.7 | 0 |
| member (v6a) | 0 | 3.7 | 5.3 | 0 | 9 | 0.3 | 14.7 | 0 |
| **owner** (v5) | 0 | 0 | 6 | 0 | 26.3 | 0 | 1.7 | 0 |
| owner (v6a) | 1.7 | 0 | 0.3 | 0.3 | 31.3 | 0 | 0.3 | 0 |
| **own+adm** (v5) | 0 | 4.7 | 0.7 | 0 | 0 | 14 | 1.7 | 0 |
| own+adm (v6a) | 0 | 5 | 0 | 0 | 5 | 7.3 | 3.7 | 0 |
| **manual** (v5) | 0.3 | 10 | 12 | 0 | 3.3 | 11 | 28 | 0.3 |
| manual (v6a) | 3 | 8.7 | 2 | 0 | 6.3 | 8.7 | 36.3 | 0 |

### oas(명세만) 보조

| 모델 | macro-F1 | 정확도 | manual 비율 | 출력 오류(합) |
|---|---:|---:|---:|---:|
| lora_v5 | 0.402 ± 0.021 | 0.515 ± 0.023 | 26.3 ± 10.4% | 1 |
| lora_v6a | 0.313 ± 0.031 | 0.386 ± 0.069 | 49.2 ± 8.7% | 3 |

원자료 scores_test_v5.json, eval_test_v5.md(scripts/eval_test_v5.py, manifest 해시 검증).

## 4. test_v30 회귀 — oas_code 합성 제외 207 (주지표 조건)

| 모델 | macro-F1(207) | macro-F1(265) | 정확도 | 구체 정밀도 | 구체 재현율 | 구체 응답률 | manual 비율 | public 오판(신, /35, seed별) | 출력 오류(seed별) |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| lora_v5 | 0.374 ± 0.010 | 0.700 ± 0.009 | 0.568 ± 0.010 | 0.796 ± 0.025 | 0.566 ± 0.010 | 0.712 ± 0.017 | 28.2 ± 2.3% | 3 / 2 / 1 | 4 / 0 / 2 |
| lora_v6a | 0.335 ± 0.049 | 0.700 ± 0.021 | 0.549 ± 0.048 | 0.607 ± 0.056 | 0.550 ± 0.046 | 0.906 ± 0.015 | 6.6 ± 2.2% | 5 / 7 / 3 | 4 / 5 / 9 |

| 모델 | public | role_required | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|
| lora_v5 | 0.644 ± 0.047 | 0.442 ± 0.030 | 0.752 ± 0.018 | 0.000 ± 0.000 | 0.034 ± 0.003 |
| lora_v6a | 0.474 ± 0.064 | 0.477 ± 0.112 | 0.691 ± 0.039 | 0.000 ± 0.000 | 0.033 ± 0.058 |

public 오판 id(v6a): s42: acdc8447219278841824, fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219, 6224f0ab777c554bb796; s43: acdc8447219278841824, 0797f5bb072770d50159, dcc8f1be82d40ee3d5cf, fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219, 6224f0ab777c554bb796; s44: acdc8447219278841824, fc9dac901542ca88d688, 6224f0ab777c554bb796. v5: s42: fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219; s43: 0797f5bb072770d50159, fc9dac901542ca88d688; s44: d8c5cf5eb0bfbd488219.

보류가 28% → 7%로 줄며 응답률은 올랐지만 응답의 정밀도가 0.80 → 0.61로 떨어졌다. v3.1의 public 정의(G7: "조건 없는 익명 허용만 public")와 보류 절 변경이 취약 API(명세에 security 선언, 코드에 검사 없음) 입력에서 public·구체 답을 늘린 것으로 보인다. v3.1 안전 가드(public 오판 ≤ 2.0)가 바로 이 경우를 막기 위한 것이었고 미달했다.

### oas(명세만) 160

| 모델 | macro-F1(160) | 합성 제외 102 | 구체 정밀도 | manual 비율 | public 오판(신) | 출력 오류 |
|---|---:|---:|---:|---:|---|---|
| lora_v5 | 0.740 ± 0.016 | 0.462 ± 0.042 | 0.908 ± 0.021 | 43.1 ± 5.3% | 0 / 0 / 0 | 3 / 1 / 0 |
| lora_v6a | 0.642 ± 0.049 | 0.376 ± 0.018 | 0.771 ± 0.050 | 41.0 ± 5.8% | 0 / 0 / 1 | 3 / 7 / 1 |

원자료 scores_test_v30.json, eval_v30.md(scripts/eval_v30.py --eval-def both). reports/eval_v30_redef/segments.json은 재생성됐으나 내용 동일(git diff 없음).

## 5. 예측 변화 v5 → v6a (test_v5 oas_code, 같은 seed)

| seed | 고쳐짐(v5 오답→v6a 정답) | 새로 틀림(v5 정답→v6a 오답) | 바뀐 전이 상위 |
|---|---:|---:|---|
| s42 | 24 | 51 | role→manual 25, member→manual 16, member→owner 13, member→role 7, own+adm→role 6, own+adm→owner 6 |
| s43 | 37 | 57 | member→manual 25, role→manual 16, member→role 16, role→public 10, member→owner 9, manual→role 7 |
| s44 | 30 | 67 | role→manual 45, member→manual 24, member→owner 11, own+adm→owner 9, own+adm→manual 6, manual→owner 4 |

새로 manual이 된 건(v5 구체 → v6a manual)의 정답 label:

| seed | public | role | member | tenant | owner | own+adm | manual |
|---|---:|---:|---:|---:|---:|---:|---:|
| s42 | 1 | 24 | 10 | 0 | 0 | 2 | 8 |
| s43 | 0 | 13 | 16 | 0 | 0 | 2 | 14 |
| s44 | 1 | 43 | 13 | 0 | 0 | 6 | 16 |

seed 간 예측이 갈린 레코드: v6a 143/283(세 seed 모두 다름 18), v5 69/283. v6a에서 갈린 label 쌍: manual|role 79, manual|public 18, manual|member 18, manual|owner 12, own+adm|role 10, public|role 9, owner|own+adm 9, owner|role 6.

manual 비율이 seed에 따라 24%~41%로 크게 흔들리고(s44 117건), 구체 답을 내던 membership_required·role_required 건이 manual로 후퇴한 것이 macro-F1 하락의 주된 경로다. 이는 v3.1 보류 절(독립 조건 AND 결합·설정 의존 → 보류)의 문구가 학습 데이터(data-v5의 rationale은 v3.0.1 기준으로 쓰인 것)와 어긋나, 모델이 프롬프트의 보류 규칙을 넓게 적용한 결과로 보인다. 학습 target(rationale·label)은 v3.1 정의로 다시 쓰지 않았으므로 프롬프트와 target의 기준이 불일치한 채 학습됐다.

## 6. S1-3 불일치 12건에서의 예측 (v5 → v6a, seed 42/43/44)

| id | 유형 | method path | 정답 | v5 s42/43/44 | v6a s42/43/44 |
|---|---|---|---|---|---|
| v5t-ghost-924636cc9d | G3-b/G6-c 경계(모든 역할 보유 권한) | GET /ghost/api/admin/posts/ | manual | role / role / role | role / manual / manual |
| v5t-rocketchat-0398a2f985 | canAccessRoom(G6-a) | GET /api/v1/rooms.membersOrderedByRole | manual | manual / manual / manual | role / manual / manual |
| v5t-rocketchat-0780c8e386 | G3-a 그룹 안 역할 | POST /api/v1/groups.addOwner | role | role / role / role | role / role / role |
| v5t-rocketchat-09c0e4be92 | G3-a 그룹 안 역할 | POST /api/v1/groups.invite | role | role / role / manual | role / role / role |
| v5t-rocketchat-0d896bf7fc | G3-a 그룹 안 역할 | POST /api/v1/groups.setType | role | member / member / role | owner / role / manual |
| v5t-rocketchat-23a530da4b | G4-c/G6-b 경계(설정 의존) | POST /api/v1/users.resetAvatar | manual | own+adm / own+adm / own+adm | owner / own+adm / owner |
| v5t-rocketchat-7508165c03 | G3-a 그룹 안 역할 | POST /api/v1/groups.rename | role | member / member / member | role / role / manual |
| v5t-rocketchat-d83dae7c4e | canAccessRoom(G6-a) | GET /api/v1/rooms.roles | manual | manual / manual / manual | manual / manual / manual |
| v5t-rocketchat-ec189eb0b4 | G3-a 그룹 안 역할 | POST /api/v1/e2e.resetRoomKey | role | manual / role / manual | role / manual / manual |
| v5t-rocketchat-f7c14cc85e | canAccessRoom(G6-a) | GET /api/v1/rooms.info | manual | manual / manual / manual | manual / manual / manual |
| v5t-umami-bf7e66056f | G6-a 복합 OR(Umami canView) | GET /api/websites/{websiteId}/shares | manual | manual / manual / manual | manual / manual / manual |
| v5t-umami-dd7523bace | G6-a 복합 OR(Umami canDelete) | DELETE /api/share/id/{shareId} | manual | own+adm / own+adm / own+adm | role / own+adm / own+adm |

| 유형 | 건수 | v5 정답(3 seed 합 / 가능) | v6a 정답(3 seed 합 / 가능) |
|---|---:|---:|---:|
| G3-b/G6-c 경계(모든 역할 보유 권한) | 1 | 0 / 3 | 2 / 3 |
| canAccessRoom(G6-a) | 3 | 9 / 9 | 8 / 9 |
| G3-a 그룹 안 역할 | 5 | 7 / 15 | 10 / 15 |
| G4-c/G6-b 경계(설정 의존) | 1 | 0 / 3 | 0 / 3 |
| G6-a 복합 OR(Umami canView) | 1 | 3 / 3 | 3 / 3 |
| G6-a 복합 OR(Umami canDelete) | 1 | 0 / 3 | 0 / 3 |

v3.1이 명문화한 G3-a(그룹 구성원 확인 뒤 그룹 안 역할 → role_required) 5건은 v5 7/15 → v6a 10/15로 조금 나아졌고(groups.rename이 member→role), G3-b 경계(GET posts, 모든 역할 보유 권한 → manual)도 0/3 → 2/3이다. 그러나 setType·resetRoomKey는 seed마다 갈리고(owner/role/manual), 설정 의존(resetAvatar)·Umami canDelete는 그대로 틀렸다. 12건 합계 v5 19/36 → v6a 23/36. 이 12건의 국소 개선은 전체 하락(3절)을 상쇄하지 못하며, 프롬프트 정의만 바꾸고 학습 target을 그대로 둔 상태에서는 규칙이 안정적으로 적용되지 않는다.

## 7. label 토큰 확률(p_norm) 정확도–보류율 곡선 (test_v5 oas_code)

| seed | n | p_norm 최소 | 1% 분위 | 5% 분위 | 중앙값 | < 0.99 건수 | < 0.999 건수 | 생성 confidence 값 분포 | 토큰화 일치 | 생성 label = 파싱 label |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| s42 | 283 | 0.999997 | 0.999999 | 1.0 | 1.0 | 0 | 0 | {'0.9': 283} | True | True |
| s43 | 283 | 0.876789 | 0.999995 | 0.999998 | 1.0 | 1 | 1 | {'0.9': 283} | True | True |
| s44 | 283 | 0.999991 | 0.999999 | 0.999999 | 1.0 | 0 | 0 | {'0.9': 283} | True | True |

| t | s42 유지 n / 유지 정확도 / 보류율 / 전체 정확도 / macro-F1 | s43 유지 n / 유지 정확도 / 보류율 / 전체 정확도 / macro-F1 | s44 유지 n / 유지 정확도 / 보류율 / 전체 정확도 / macro-F1 | 평균 보류율 | 평균 전체 정확도 | 평균 macro-F1 |
|---|---|---|---|---:|---:|---:|
| 0.50 | 207 / 0.6618 / 0.269 / 0.594 / 0.545 | 209 / 0.6651 / 0.262 / 0.615 / 0.543 | 166 / 0.7108 / 0.413 / 0.569 / 0.558 | 0.315 | 0.592 | 0.549 |
| 0.55 | 207 / 0.6618 / 0.269 / 0.594 / 0.545 | 209 / 0.6651 / 0.262 / 0.615 / 0.543 | 166 / 0.7108 / 0.413 / 0.569 / 0.558 | 0.315 | 0.592 | 0.549 |
| 0.60 | 207 / 0.6618 / 0.269 / 0.594 / 0.545 | 209 / 0.6651 / 0.262 / 0.615 / 0.543 | 166 / 0.7108 / 0.413 / 0.569 / 0.558 | 0.315 | 0.592 | 0.549 |
| 0.65 | 207 / 0.6618 / 0.269 / 0.594 / 0.545 | 209 / 0.6651 / 0.262 / 0.615 / 0.543 | 166 / 0.7108 / 0.413 / 0.569 / 0.558 | 0.315 | 0.592 | 0.549 |
| 0.70 | 207 / 0.6618 / 0.269 / 0.594 / 0.545 | 209 / 0.6651 / 0.262 / 0.615 / 0.543 | 166 / 0.7108 / 0.413 / 0.569 / 0.558 | 0.315 | 0.592 | 0.549 |
| 0.75 | 207 / 0.6618 / 0.269 / 0.594 / 0.545 | 209 / 0.6651 / 0.262 / 0.615 / 0.543 | 166 / 0.7108 / 0.413 / 0.569 / 0.558 | 0.315 | 0.592 | 0.549 |
| 0.80 | 207 / 0.6618 / 0.269 / 0.594 / 0.545 | 209 / 0.6651 / 0.262 / 0.615 / 0.543 | 166 / 0.7108 / 0.413 / 0.569 / 0.558 | 0.315 | 0.592 | 0.549 |
| 0.85 | 207 / 0.6618 / 0.269 / 0.594 / 0.545 | 209 / 0.6651 / 0.262 / 0.615 / 0.543 | 166 / 0.7108 / 0.413 / 0.569 / 0.558 | 0.315 | 0.592 | 0.549 |
| 0.90 | 207 / 0.6618 / 0.269 / 0.594 / 0.545 | 208 / 0.6635 / 0.265 / 0.611 / 0.538 | 166 / 0.7108 / 0.413 / 0.569 / 0.558 | 0.316 | 0.591 | 0.547 |
| 0.95 | 207 / 0.6618 / 0.269 / 0.594 / 0.545 | 208 / 0.6635 / 0.265 / 0.611 / 0.538 | 166 / 0.7108 / 0.413 / 0.569 / 0.558 | 0.316 | 0.591 | 0.547 |
| 0.99 | 207 / 0.6618 / 0.269 / 0.594 / 0.545 | 208 / 0.6635 / 0.265 / 0.611 / 0.538 | 166 / 0.7108 / 0.413 / 0.569 / 0.558 | 0.316 | 0.591 | 0.547 |

- p_norm은 greedy 디코딩에서 label 키 다음 토큰의 7종 후보 정규화 확률이다. 세 seed 모두 거의 전 건이 1.0에 붙어 있어(0.99 미만 0, 1, 0건) 문턱 0.5~0.99 구간에서 곡선이 평탄하다. **생성 confidence(0.9 단일값)와 마찬가지로 label 토큰 확률도 보류 조절 수단이 되지 못했다.**
- 원인: 출력 순서를 근거 먼저로 바꾸면 rationale 문장이 label 이름을 먼저 적고(rationale 안에 label 문자열 포함 207, 208, 166/283) `"label"` 키의 토큰은 그 문장을 복사하는 결정적 토큰이 된다. 불확실성은 rationale 안에서 label 이름이 처음 나오는 위치의 토큰 확률에 있으며, 이번 추론은 그 위치의 scores를 저장하지 않았다. 대안은 (a) rationale에서 label 이름이 처음 등장하는 토큰의 확률을 저장, (b) label을 먼저 내는 순서에서 label 토큰 확률 측정, (c) 7종 label을 각각 강제한 teacher-forcing 로그확률 비교(추가 forward 7회).

## 8. 출력 오류·출력 길이·추론 시간

| 셋·조건 | v5 출력 오류(s42/43/44) | v6a 출력 오류(s42/43/44) | v6a 오류 중 중국어 혼입 | v6a 오류 중 512 토큰 도달 | v6a 출력 토큰 평균/최대(s42) | 출력 문자 수 평균 v5 → v6a(s42) | v6a 프롬프트 토큰 평균/최대 |
|---|---|---|---:|---:|---|---|---|
| test_v5 oas_code | 1 / 0 / 2 | 0 / 0 / 0 | 0 | 0 | 79.4 / 97 | 232.3 → 225.5 | 4590.2 / 5150 |
| test_v5 oas | 0 / 1 / 0 | 0 / 1 / 2 | 3 | 0 | 75.4 / 97 | 189.3 → 213.9 | 3915.6 / 3942 |
| test_v30 oas_code(265) | 5 / 4 / 3 | 6 / 6 / 9 | 19 | 3 | 78.3 / 512 | 203.8 → 203.6 | 4137.7 / 4940 |
| test_v30 oas(269) | 3 / 1 / 0 | 3 / 7 / 1 | 11 | 4 | 67.7 / 512 | 189.6 → 193.2 | 3915.8 / 4075 |

v6a 출력 오류는 test_v5 oas_code에서는 0건, test_v30(취약 API)에서 seed당 4~9건이며 대부분 rationale 중간에 중국어·영어가 섞여 들어가 JSON이 깨진 경우다(중국어 혼입 위치 전후 발췌: eef733c4cdf73432c9bc 129토큰 `… 핸들러 원문 — 요청자 id와 객체 소유자 id를 비교해 다르면 허용,相同的响应： {"evidence_fields": ["description", "path_params"], "…`; 06ba24e97fdcb059ad92 150토큰 `…tionale": "description: 핸들러 원문 — 요청자 id와笔记翻译 用户 请求者和目标对象之间的关系或实际访问条件无法明确，仅凭现有信息不足以确定一个合适的标签。因此，需要人工审…`; be2ff7c9ec46320a97af 512토큰 `…escription: 검사 코드는 없으나 경로·리소스 의미상 사용자 전체笔记：以下是翻译后的结果：  作为API安全审核员，输入的该端点需要选择一个固定标签或进入手动审核。选择标签的依据是提取…`; folio_wiki_workspace_1 99토큰 `…d"], "rationale": "description: 요청자는 객체와相同的翻译 tica {"证据字段": ["description", "path_params:item_id"], …`). v5(v3.0.1)도 test_v30에서 seed당 0~5건의 같은 유형 오류가 있었고 v6a에서 조금 늘었다.

| 셋·조건 | v5 행당 ms(A100, s42) | v6a 행당 ms(H100, s42/43/44) | v6a 벽시계 s(s42) | 프롬프트 절단 |
|---|---:|---|---:|---:|
| test_v5 oas_code | 808.9 | 499.5 / 501.1 / 480.7 | 141.8 | 0 |
| test_v5 oas | 651.8 | 440.5 / 454.9 / 416.4 | 125.1 | 0 |
| test_v30 oas_code | 744.8 | 557.8 / 500.0 / 557.3 | 148.2 | 0 |
| test_v30 oas | 625.5 | 472.4 / 498.9 / 432.7 | 127.5 | 0 |

행당 ms는 배치 8 기준(배치 벽시계 / 8)이며 GPU가 다르므로(v5 A100, v6a H100) 직접 비교는 참고치다. 학습은 seed당 32.5분(v5 A100 56분).

## 9. 해석·한계·다음 단계

- **불채택.** v3.1 정의를 프롬프트에만 넣고 학습 target(data-v5 rationale·label, v3.0.1 기준 작성)은 그대로 둔 결과, 프롬프트 규칙과 target이 어긋난 채 학습됐다. test_v5에서는 보류가 늘고 test_v30에서는 보류가 줄어, 두 셋에서 반대 방향으로 나빠졌다. 프롬프트 변경 효과와 출력 순서 변경 효과는 이 실험에서 분리되지 않는다(둘을 함께 바꿈).
- label 토큰 확률은 근거 먼저 출력 설계에서는 결정적(≈1.0)이라 보류 조절에 쓸 수 없다(7절). confidence를 쓰려면 측정 위치나 출력 순서를 바꿔야 한다.
- v3.1 반영이 목표라면 학습 target을 v3.1 정의로 다시 쓰는 단계(data-v5 rationale 재작성·G3-a 등 라벨 재검토)가 먼저 필요하며, 이는 별도 설계·승인 대상이다. S5b(문맥 블록을 학습 입력에 포함)는 이 결과와 별개로 보류한다.
- 산출물: 예측·로그 reports/eval/lora_v6a/lora_v6a_s{42,43,44}/, run_v6.log, SHA256SUMS_blade_v6a(어댑터 tar 3개는 git 밖, 로컬 zip BLADE_lora_v6a_export.zip SHA-256 `78f3f7db06a6c7d2…`), 채점 scores_test_v5.json·eval_test_v5.md·scores_test_v30.json·eval_v30.md, 분석 analysis.json(scripts/analyze_lora_v6a.py). 커밋하지 않았다. 주지표·발표 수치(v5) 불변, test_v6 추론 없음.
