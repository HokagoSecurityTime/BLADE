# C′ LoRA v6d 보고 — v5 설정 + 학습 정답만 교정 (2026-11-07 채점, 학습 2026-11-05, 3 seed, 커밋 없음)

사전 기록 AGENTS.md "작업 C′"·"data-v6d 동결". 변경은 학습 정답뿐: data-v6d = data-v5 SFT 행에 C1 확정 label 36건(전부 gitea; owner_match→role_required 23 등) + C2 rationale 42건을 반영한 것이며 user 입력·행 순서·나머지 행은 바이트 동일. 베이스 7B(S8 불채택으로 확정), 프롬프트 v3.0.1, 출력 순서, max_seq_len 4096, max_new_tokens 256, LoRA r16/α16·3 epoch·lr 2e-4·batch 2×4·cosine·adamw_8bit·completion-only 마스킹·greedy는 v5와 같다. 판정셋 test_v5 283(dev, oas_code) + 회귀 test_v30 oas_code 합성 제외 207, 보조 test_v31_supp 222. v5 수치는 기존 예측 파일을 같은 채점기로 재채점한 값(재추론 없음). test_v6은 추론하지 않았다. 주지표·발표 수치(v5)는 바꾸지 않는다.

## 1. 판정 — 사전 기준 미달, **불채택** → v5 유지(최종 모델, S9 대상)

| 기준(3 seed 평균) | v5 | v6d | 차이 | 기준 | 충족 |
|---|---:|---:|---:|---|---|
| (1) test_v5 oas_code macro-F1 상승 ≥ 0.016 | 0.683 ± 0.016 | 0.694 ± 0.038 | +0.011 | ≥ +0.016 | **아니오** |
| (2) test_v30 207 구체 정밀도 하락 ≤ 0.025 | 0.796 ± 0.025 | 0.795 ± 0.033 | -0.001 | 하락 ≤ 0.025 | 예 |
| (3) test_v30 207 public 오판(/35) 평균 ≤ 2.0 | 3 / 2 / 1 (평균 2.00) | 3 / 2 / 1 (평균 2.00) | +0.00 | ≤ 2.0 | 예 |

- 같은 seed끼리의 test_v5 macro-F1 차이(v6d − v5): +0.021, +0.051, -0.038. seed별 v6d 0.687, 0.735, 0.660 — seed 표준편차가 0.038(v5 0.016)로 커져 평균 차이 +0.011은 v6d 자체 표준편차 안이다. 기준 (1)은 미달이고, 실험 규칙 "표준편차보다 큰 차이만 차이로 인정"으로 봐도 seed 하나(s43 +0.051)가 끌어올린 결과라 안정적 개선이 아니다. manual 비율도 16.6% → 21.0%로 올라 보류가 늘었다.
- test_v5 정확도 0.691 → 0.697, manual 건수 46 / 43 / 52 → 44 / 65 / 69(seed별). test_v30 207 구체 정밀도 0.796 → 0.795, public 오판 평균 2.00 → 2.00, test_v30 macro-F1(207) 0.374 → 0.369. supp macro-F1 0.485 → 0.487.

## 2. 실행 환경·학습

- Pod: RunPod H100(NVIDIA H100 80GB HBM3 79 GB), torch 2.14.1+cu130(CUDA 13.0), transformers 5.17.0, trl 1.15.0, peft 0.21.2, unsloth 2026.11.2, python 3.12.3. 2026-11-05 07:18 → 09:14 UTC(1시간 56분: 설치 2분, preflight 1분, seed당 37~38분 × 3), 번들 blade_v6d_20261105.tgz(`3c52b2cd…`), 해시 게이트(data_v6d_hashes.json `82efda86…`, test_v5_manifest `57fd384f…`, 프롬프트 `d0913c27…`, run.log `inputs verified` 3 seed 확인) 통과, Pod 자동 정지. 조기 판정 없음(사전 기록대로).
- v5 환경(비교): NVIDIA A100-SXM4-80GB, unsloth 2026.10.11. 손실 마스킹 0번 행 `loss mask check (row 0): 2857/2950 tokens masked (-100), 93 assistant tokens in loss`(3 seed 동일, v5·v6c와 같은 값). LoRA trainable 40,370,176, 유효 배치 8, padding_free=True.

| run | steps | 학습 분 | train_loss | val oas loss(final / 최저) | val oas_code loss(final / 최저) | 피크 GPU GiB(alloc / reserved) | v5 같은 seed train_loss / val final(oas, oas_code) / 분 |
|---|---:|---:|---:|---|---|---|---|
| lora_v6d_s42 | 480 | 24.6 | 0.1559 | 0.2601 / 0.2371 | 0.187 / 0.1791 | 7.35 / 13.39 | 0.1464 / 0.2425, 0.1469 / 56.2 |
| lora_v6d_s43 | 480 | 24.6 | 0.1593 | 0.2549 / 0.2379 | 0.1831 / 0.1744 | 7.35 / 13.29 | 0.15 / 0.2479, 0.1447 / 56.2 |
| lora_v6d_s44 | 480 | 24.6 | 0.1598 | 0.2624 / 0.2407 | 0.1853 / 0.1774 | 7.35 / 12.21 | 0.1483 / 0.2535, 0.1404 / 56.1 |

val은 학습 정상 여부 확인용(발산 없음, 480 step 완주)이며 체크포인트 선택에 쓰지 않았다(final 고정). train_loss·val loss는 v5보다 약간 높다(교정된 36행의 label이 바뀌어 같은 입력에 대한 target 분포가 달라짐; val_v6d에도 교정 6행 포함).

## 3. test_v5 283 (dev) — oas_code

| 모델 | macro-F1 | 정확도 | manual 비율 | manual 건수(seed별) | 출력 오류(합) |
|---|---:|---:|---:|---|---:|
| lora_v5 | 0.683 ± 0.016 | 0.691 ± 0.007 | 16.6 ± 1.6% | 46 / 43 / 52 | 3 |
| lora_v6d | 0.694 ± 0.038 | 0.697 ± 0.030 | 21.0 ± 4.7% | 44 / 65 / 69 | 2 |

### label별 F1 (support)

| 모델 | public (19) | role_required (111) | membership_required (33) | tenant_match (0) | owner_match (34) | owner_or_admin (21) | manual_review_required (65) |
|---|---:|---:|---:|---:|---:|---:|---:|
| lora_v5 | 0.894 ± 0.063 | 0.818 ± 0.026 | 0.589 ± 0.048 | 0.000 ± 0.000 | 0.760 ± 0.024 | 0.536 ± 0.031 | 0.499 ± 0.027 |
| lora_v6d | 0.907 ± 0.016 | 0.808 ± 0.012 | 0.587 ± 0.071 | 0.000 ± 0.000 | 0.758 ± 0.008 | 0.562 ± 0.083 | 0.541 ± 0.066 |

### 판정 label 정밀도 / 재현율 (seed별)

| run | owner_or_admin P / R / F1 | membership_required P / R / F1 | role_required P / R / F1 | owner_match P / R / F1 | manual P / R / F1 |
|---|---|---|---|---|---|
| lora_v5_s42 | 0.500 / 0.619 / 0.553 | 0.453 / 0.727 / 0.558 | 0.867 / 0.820 / 0.843 | 0.703 / 0.765 / 0.732 | 0.587 / 0.415 / 0.486 |
| lora_v5_s43 | 0.400 / 0.667 / 0.500 | 0.518 / 0.849 / 0.644 | 0.838 / 0.748 / 0.790 | 0.750 / 0.794 / 0.771 | 0.605 / 0.400 / 0.481 |
| lora_v5_s44 | 0.455 / 0.714 / 0.556 | 0.489 / 0.667 / 0.564 | 0.861 / 0.784 / 0.821 | 0.788 / 0.765 / 0.776 | 0.596 / 0.477 / 0.530 |
| lora_v6d_s42 | 0.441 / 0.714 / 0.545 | 0.452 / 0.849 / 0.590 | 0.871 / 0.730 / 0.794 | 0.765 / 0.765 / 0.765 | 0.636 / 0.431 / 0.514 |
| lora_v6d_s43 | 0.571 / 0.762 / 0.653 | 0.600 / 0.727 / 0.657 | 0.892 / 0.748 / 0.814 | 0.711 / 0.794 / 0.750 | 0.615 / 0.615 / 0.615 |
| lora_v6d_s44 | 0.458 / 0.524 / 0.489 | 0.515 / 0.515 / 0.515 | 0.853 / 0.784 / 0.817 | 0.730 / 0.794 / 0.761 | 0.478 / 0.508 / 0.492 |

### 프로젝트별 정확도

| 모델 | rocketchat (157) | ghost (69) | umami (57) |
|---|---:|---:|---:|
| lora_v5 | 0.656 ± 0.013 | 0.758 ± 0.008 | 0.708 ± 0.066 |
| lora_v6d | 0.648 ± 0.032 | 0.763 ± 0.036 | 0.754 ± 0.035 |

### 혼동표 (정답 행 → 예측 열, 3 seed 평균 건수)

| 정답 \ 예측 | public | role | member | tenant | owner | own+adm | manual | ERR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **public** (v5) | 15.7 | 0 | 0 | 0 | 0 | 0 | 3.3 | 0 |
| public (v6d) | 16.3 | 0 | 0 | 0 | 0 | 0 | 2.7 | 0 |
| **role** (v5) | 0 | 87 | 7.3 | 0 | 1.3 | 6 | 8.7 | 0.7 |
| role (v6d) | 0 | 83.7 | 7.7 | 0 | 1.7 | 4.3 | 13.7 | 0 |
| **member** (v5) | 0 | 0 | 24.7 | 0 | 4.3 | 0.3 | 3.7 | 0 |
| member (v6d) | 0 | 0.3 | 23 | 0 | 5 | 0.3 | 4.3 | 0 |
| **owner** (v5) | 0 | 0 | 6 | 0 | 26.3 | 0 | 1.7 | 0 |
| owner (v6d) | 0 | 0 | 5.7 | 0 | 26.7 | 0 | 1.3 | 0.3 |
| **own+adm** (v5) | 0 | 4.7 | 0.7 | 0 | 0 | 14 | 1.7 | 0 |
| own+adm (v6d) | 0 | 3 | 0.3 | 0 | 0 | 14 | 3.7 | 0 |
| **manual** (v5) | 0.3 | 10 | 12 | 0 | 3.3 | 11 | 28 | 0.3 |
| manual (v6d) | 0.7 | 9 | 8.3 | 0 | 3 | 10 | 33.7 | 0.3 |

### manual 예측의 정답 label 분포 (seed별)

| run | public | role | member | owner | own+adm | manual | 합 |
|---|---:|---:|---:|---:|---:|---:|---:|
| lora_v5_s42 | 5 | 6 | 3 | 2 | 3 | 27 | 46 |
| lora_v5_s43 | 3 | 11 | 1 | 1 | 1 | 26 | 43 |
| lora_v5_s44 | 2 | 9 | 7 | 2 | 1 | 31 | 52 |
| lora_v6d_s42 | 3 | 8 | 1 | 2 | 2 | 28 | 44 |
| lora_v6d_s43 | 2 | 17 | 3 | 1 | 2 | 40 | 65 |
| lora_v6d_s44 | 3 | 16 | 9 | 1 | 7 | 33 | 69 |

### oas(명세만) 보조

| 모델 | macro-F1 | 정확도 | manual 비율 | 출력 오류(합) |
|---|---:|---:|---:|---:|
| lora_v5 | 0.402 ± 0.021 | 0.515 ± 0.023 | 26.3 ± 10.4% | 1 |
| lora_v6d | 0.399 ± 0.034 | 0.511 ± 0.018 | 24.6 ± 10.6% | 0 |

원자료 scores_test_v5.json, eval_test_v5.md(scripts/eval_test_v5.py, manifest 해시 검증).

## 4. test_v30 회귀 — oas_code 합성 제외 207 (주지표 조건)

| 모델 | macro-F1(207) | macro-F1(265) | 정확도 | 구체 정밀도 | 구체 재현율 | 구체 응답률 | manual 비율 | public 오판(신, /35, seed별) | 출력 오류(seed별) |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| lora_v5 | 0.374 ± 0.010 | 0.700 ± 0.009 | 0.568 ± 0.010 | 0.796 ± 0.025 | 0.566 ± 0.010 | 0.712 ± 0.017 | 28.2 ± 2.3% | 3 / 2 / 1 | 4 / 0 / 2 |
| lora_v6d | 0.369 ± 0.013 | 0.728 ± 0.015 | 0.586 ± 0.027 | 0.795 ± 0.033 | 0.584 ± 0.027 | 0.735 ± 0.024 | 26.4 ± 2.0% | 3 / 2 / 1 | 3 / 0 / 0 |

| 모델 | public | role_required | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|
| lora_v5 | 0.644 ± 0.047 | 0.442 ± 0.030 | 0.752 ± 0.018 | 0.000 ± 0.000 | 0.034 ± 0.003 |
| lora_v6d | 0.677 ± 0.036 | 0.365 ± 0.034 | 0.765 ± 0.029 | 0.000 ± 0.000 | 0.036 ± 0.003 |

public 오판 id(v6d): s42: fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219; s43: fc9dac901542ca88d688, d8c5cf5eb0bfbd488219; s44: d8c5cf5eb0bfbd488219. v5: s42: fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219; s43: 0797f5bb072770d50159, fc9dac901542ca88d688; s44: d8c5cf5eb0bfbd488219.

### oas(명세만) 160

| 모델 | macro-F1(160) | 합성 제외 102 | 구체 정밀도 | manual 비율 | public 오판(신) | 출력 오류 |
|---|---:|---:|---:|---:|---|---|
| lora_v5 | 0.740 ± 0.016 | 0.462 ± 0.042 | 0.908 ± 0.021 | 43.1 ± 5.3% | 0 / 0 / 0 | 3 / 1 / 0 |
| lora_v6d | 0.686 ± 0.064 | 0.461 ± 0.018 | 0.907 ± 0.021 | 44.2 ± 1.0% | 0 / 0 / 0 | 8 / 1 / 2 |

원자료 scores_test_v30.json, eval_v30.md(scripts/eval_v30.py --eval-def both).

## 5. test_v31_supp 222 (보조 조건)

| 모델 | oas_code macro-F1 | 정확도 | manual 비율 | 출력 오류(합) | oas macro-F1 | oas manual 비율 |
|---|---:|---:|---:|---:|---:|---:|
| lora_v5 | 0.485 ± 0.026 | 0.419 ± 0.039 | 20.7 ± 5.5% | 2 | 0.258 ± 0.057 | 49.1 ± 6.2% |
| lora_v6d | 0.487 ± 0.036 | 0.425 ± 0.052 | 24.0 ± 2.5% | 2 | 0.288 ± 0.035 | 45.5 ± 4.3% |

| 모델 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| lora_v5 | 1.000 ± 0.000 | 0.491 ± 0.055 | 0.601 ± 0.089 | 0.235 ± 0.043 | 0.541 ± 0.072 | 0.328 ± 0.024 | 0.198 ± 0.052 |
| lora_v6d | 0.933 ± 0.115 | 0.541 ± 0.109 | 0.622 ± 0.074 | 0.215 ± 0.059 | 0.587 ± 0.050 | 0.386 ± 0.039 | 0.127 ± 0.020 |

| 모델 | chatwoot | chamilo | flowise | multitenant_lab | generic_university |
|---|---:|---:|---:|---:|---:|
| lora_v5 | 0.502 ± 0.072 | 0.374 ± 0.020 | 0.200 ± 0.000 | 0.667 ± 0.144 | 0.810 ± 0.165 |
| lora_v6d | 0.544 ± 0.046 | 0.345 ± 0.052 | 0.189 ± 0.042 | 0.750 ± 0.000 | 0.809 ± 0.172 |

원자료 scores_supp.json, eval_supp.md(scripts/eval_v31_supp.py). supp 예측 파일은 .gitignore 대상(Flowise 코드 발췌가 raw에 섞일 수 있음).

## 6. 예측 변화 v5 → v6d (test_v5 oas_code, 같은 seed)

| seed | 고쳐짐(v5 오답→v6d 정답) | 새로 틀림(v5 정답→v6d 오답) | 바뀐 전이 상위 |
|---|---:|---:|---:|
| s42 | 17 | 18 | role→own+adm 5, role→manual 5, manual→own+adm 4, manual→public 4, manual→member 4, public→manual 3 |
| s43 | 30 | 17 | member→manual 14, role→manual 8, own+adm→manual 7, role→own+adm 5, manual→role 4, own+adm→role 4 |
| s44 | 15 | 22 | member→manual 9, role→manual 8, own+adm→role 6, own+adm→manual 5, member→owner 2, manual→member 2 |

고쳐진 건 / 새로 틀린 건의 정답 label:

| seed | public | role | member | owner | own+adm | manual |
|---|---:|---:|---:|---:|---:|---:|
| s42 고쳐짐 | 4 | 2 | 4 | 0 | 3 | 4 |
| s42 새로 틀림 | 2 | 12 | 0 | 0 | 1 | 3 |
| s43 고쳐짐 | 1 | 9 | 1 | 0 | 3 | 16 |
| s43 새로 틀림 | 0 | 9 | 5 | 0 | 1 | 2 |
| s44 고쳐짐 | 1 | 8 | 2 | 1 | 0 | 3 |
| s44 새로 틀림 | 2 | 8 | 7 | 0 | 4 | 1 |

seed 간 예측이 갈린 레코드: v6d 74/283(세 seed 모두 다름 6), v5 69/283. v6d에서 갈린 label 쌍: manual|member 24, manual|role 13, manual|own+adm 11, own+adm|role 7, member|owner 7, member|role 7, manual|public 5, manual|owner 5.

v5·v6d 여섯 run 모두 틀린 레코드 43/283 — 정답 label별 public 1, role 10, member 3, owner 7, own+adm 3, manual 19; 프로젝트별 ghost 10, rocketchat 24, umami 9(S8 v6c 대비 때는 39건).

학습에서 바뀐 것은 gitea의 owner_match→role_required 23건 등 C1 42건(label 변경 36: membership_required->manual_review_required 2, manual_review_required->owner_or_admin 1, owner_match->manual_review_required 1, manual_review_required->owner_match 2, owner_match->role_required 23, manual_review_required->role_required 5, role_required->public 1, membership_required->owner_match 1)이다. test_v5에서 그 방향(owner→role, manual→role)으로 예측이 옮겨간 것이 위 전이 표에 보이면 교정 효과이고, manual로 옮겨간 것은 교정과 무관한 seed 변동일 가능성이 크다.

## 7. S1-3 불일치 12건에서의 예측 (v5 → v6d, seed 42/43/44)

| id | 유형 | method path | 정답 | v5 s42/43/44 | v6d s42/43/44 |
|---|---|---|---|---|---|
| v5t-ghost-924636cc9d | G3-b/G6-c 경계(모든 역할 보유 권한) | GET /ghost/api/admin/posts/ | manual | role / role / role | role / role / role |
| v5t-rocketchat-0398a2f985 | canAccessRoom(G6-a) | GET /api/v1/rooms.membersOrderedByRole | manual | manual / manual / manual | manual / manual / manual |
| v5t-rocketchat-0780c8e386 | G3-a 그룹 안 역할 | POST /api/v1/groups.addOwner | role | role / role / role | role / role / role |
| v5t-rocketchat-09c0e4be92 | G3-a 그룹 안 역할 | POST /api/v1/groups.invite | role | role / role / manual | manual / manual / manual |
| v5t-rocketchat-0d896bf7fc | G3-a 그룹 안 역할 | POST /api/v1/groups.setType | role | member / member / role | member / member / manual |
| v5t-rocketchat-23a530da4b | G4-c/G6-b 경계(설정 의존) | POST /api/v1/users.resetAvatar | manual | own+adm / own+adm / own+adm | own+adm / own+adm / own+adm |
| v5t-rocketchat-7508165c03 | G3-a 그룹 안 역할 | POST /api/v1/groups.rename | role | member / member / member | member / member / member |
| v5t-rocketchat-d83dae7c4e | canAccessRoom(G6-a) | GET /api/v1/rooms.roles | manual | manual / manual / manual | member / manual / manual |
| v5t-rocketchat-ec189eb0b4 | G3-a 그룹 안 역할 | POST /api/v1/e2e.resetRoomKey | role | manual / role / manual | role / manual / manual |
| v5t-rocketchat-f7c14cc85e | canAccessRoom(G6-a) | GET /api/v1/rooms.info | manual | manual / manual / manual | manual / manual / manual |
| v5t-umami-bf7e66056f | G6-a 복합 OR(Umami canView) | GET /api/websites/{websiteId}/shares | manual | manual / manual / manual | manual / manual / manual |
| v5t-umami-dd7523bace | G6-a 복합 OR(Umami canDelete) | DELETE /api/share/id/{shareId} | manual | own+adm / own+adm / own+adm | own+adm / own+adm / own+adm |

| 유형 | 건수 | v5 정답(3 seed 합 / 가능) | v6d 정답(3 seed 합 / 가능) |
|---|---:|---:|---:|
| G3-b/G6-c 경계(모든 역할 보유 권한) | 1 | 0 / 3 | 0 / 3 |
| canAccessRoom(G6-a) | 3 | 9 / 9 | 8 / 9 |
| G3-a 그룹 안 역할 | 5 | 7 / 15 | 4 / 15 |
| G4-c/G6-b 경계(설정 의존) | 1 | 0 / 3 | 0 / 3 |
| G6-a 복합 OR(Umami canView) | 1 | 3 / 3 | 3 / 3 |
| G6-a 복합 OR(Umami canDelete) | 1 | 0 / 3 | 0 / 3 |

12건 합계 v5 19/36 → v6d 15/36. G3-a(그룹 안 역할 → role_required)는 C1 교정(gitea reqOrgOwnership owner_match → role_required 23건)과 같은 규약 항목이라 이 유형이 교정 효과의 직접 신호인데, 7/15 → 4/15로 오히려 내렸다(Rocket.Chat 그룹 안 역할 건이 role 대신 manual로 감). gitea 23건의 교정이 다른 프로젝트의 같은 규약 패턴으로 전이되지 않았다.

## 8. 출력 오류·출력 길이·추론 시간

| 셋·조건 | v5 출력 오류(s42/43/44) | v6d 출력 오류(s42/43/44) | v6d 오류 중 중국어 혼입 | v6d 오류 중 256 토큰 도달 | v6d 출력 토큰 평균/최대(s42) | v6d 행당 ms(H100, s42/43/44) |
|---|---|---|---:|---:|---|---|
| test_v5 oas_code | 1 / 0 / 2 | 0 / 1 / 1 | 2 | 0 | 82.4 / 110 | 470.7 / 442.9 / 458.0 |
| test_v5 oas | 0 / 1 / 0 | 0 / 0 / 0 | 0 | 0 | 64.7 / 101 | 363.2 / 394.1 / 366.3 |
| test_v30 oas_code(265) | 5 / 4 / 3 | 6 / 0 / 0 | 6 | 2 | 75.4 / 256 | 461.7 / 403.1 / 401.9 |
| test_v30 oas(269) | 3 / 1 / 0 | 8 / 1 / 2 | 11 | 0 | 70.2 / 96 | 403.0 / 388.8 / 384.9 |
| supp oas_code | 0 / 1 / 1 | 1 / 1 / 0 | 2 | 1 | 82.9 / 147 | 477.5 / 503.7 / 429.2 |
| supp oas | 2 / 0 / 1 | 1 / 1 / 0 | 2 | 0 | 71.8 / 127 | 418.2 / 395.8 / 387.5 |

v6d 출력 오류 18작업 합계 23건(v5 25건). s42 test_v30 oas 8건·oas_code 6건이 두드러지며 대부분 rationale 중국어 혼입이다. 학습 24.6분/seed(H100), 추론 행당 0.36~0.50 s.

## 9. 해석·한계·다음 단계

- 숫자상 기준 (1)은 미달, (2)·(3)은 충족. 그러나 v6d의 seed 표준편차(0.038)가 v5(0.016)의 두 배가 넘고 세 seed 중 하나(s43)만 크게 올랐다. "표준편차보다 큰 차이만 인정" 규칙으로는 개선으로 보기 어렵고, manual 비율이 16.6% → 21.0%로 올라 보류가 늘었다. 학습 라벨 36건(2.8%) 교정으로 기대할 수 있는 효과 크기가 seed 잡음보다 작다는 것이 이 실험의 결론이다.
- 한계: data-v6d의 C1 검수자는 사람이 아니라 Claude(AI)이고 블라인드 감사 불일치 41.2%는 한계로 기록된 상태다(reports/data_v6d/stop_c1_c2_data_v6d.md). OAS-only 390행은 이번 범위 밖이다. 이 결과는 "코드 행 라벨 소폭 교정"의 효과이지 "학습 라벨 전면 재정의"의 효과가 아니다.
- 다음: 사전 기준 (1) 미달이므로 작업 C′ 중단 규칙대로 **v5 유지**가 기본 결론이다. 발표 주 수치는 v5이며 S9(test_v6) 전까지 바꾸지 않는다. 교정 라벨 data-v6d 자체는 보존하며(동결 해시 불변), 마감 후 OAS-only 390행·블라인드 불일치 28건의 사람 전수 검수와 합쳐 더 큰 교정분으로 재실험할 때 재사용한다.
- 산출물: 예측·로그 reports/eval/lora_v6d/lora_v6d_s{42,43,44}/, run_v6d.log, SHA256SUMS_blade_v6d(어댑터 tar 3개는 git 밖, 로컬 zip BLADE_lora_v6d_export.zip SHA-256 `a9b587c06358d0c7…`), 채점 scores_test_v5.json·eval_test_v5.md·scores_test_v30.json·eval_v30.md·scores_supp.json·eval_supp.md, 분석 analysis.json(scripts/analyze_lora_v6d.py). 커밋하지 않았다. test_v6 추론 없음.
