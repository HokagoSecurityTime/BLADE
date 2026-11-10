# S8 LoRA v6c 보고 — 베이스 모델만 14B로 교체 (2026-11-05, 3 seed + base 14B zero-shot, 커밋 없음)

사전 기록 AGENTS.md "작업 S8". 변경은 베이스 모델 하나뿐(`unsloth/Qwen2.5-7B-Instruct-bnb-4bit` → `unsloth/Qwen2.5-14B-Instruct-bnb-4bit`): 데이터 data-v5 train/val(해시 게이트), 프롬프트 v3.0.1, 출력 순서(label 먼저), max_seq_len 4096, max_new_tokens 256, LoRA r16·α16·3 epoch·lr 2e-4·cosine·adamw_8bit·batch 2×4, completion-only 마스킹, greedy 디코딩은 v5와 동일. 판정셋 test_v5 283(dev, oas_code) + 회귀 test_v30 oas_code 합성 제외 207, 보조 test_v31_supp 222. v5 수치는 reports/eval/lora_v5의 기존 예측을 같은 채점기로 재채점한 값(재추론 없음). test_v6은 추론하지 않았다. 주지표·발표 수치(v5)는 바꾸지 않는다.

## 1. 판정 — 기준 (1) 미달, **불채택** (v5가 최종 모델, S9 대상)

| 기준(3 seed 평균) | v5 | v6c | 차이 | 기준 | 충족 |
|---|---:|---:|---:|---|---|
| (1) test_v5 oas_code macro-F1 상승 ≥ 0.016 | 0.683 ± 0.016 | 0.680 ± 0.015 | -0.003 | ≥ +0.016 | **아니오** |
| (2) test_v30 207 구체 정밀도 하락 ≤ 0.025 | 0.796 ± 0.025 | 0.813 ± 0.019 | +0.017 | 하락 ≤ 0.025 | 예 |
| (3) test_v30 207 public 오판(/35) 평균 ≤ 2.0 | 3 / 2 / 1 (평균 2.00) | 2 / 2 / 1 (평균 1.67) | -0.33 | ≤ 2.0 | 예 |

- 조기 판정(Pod, early_gate.json): v6c s42 test_v5 macro-F1 0.686 > v5 s42 0.6661 → PASS(+0.0199), s43·s44·base zero-shot을 실행했다. 그러나 3 seed 평균은 v5와 같은 수준이고(seed별 0.686 / 0.690 / 0.663 vs v5 0.666 / 0.684 / 0.699) 차이가 사전 기준 +0.016은 물론 seed 표준편차보다 작다. (2)·(3)은 충족(정밀도 소폭 상승, public 오판 감소)이지만 세 조건을 모두 충족해야 채택이다.
- 사전 기록대로 **v5를 최종 모델로 확정한다(S9 대상)**. 14B 채택 시 필요했던 GGUF 병합 Pod 요건(RAM ≥ 80 GB, 디스크 ≥ 120 GB)·로컬 CPU 추론 2배 지연은 해당 없다.

## 2. 실행 환경·학습

- Pod: RunPod zra2rcdj6gbixh, NVIDIA A100 80GB PCIe 79 GB, torch 2.14.1+cu130(CUDA 13.0), transformers 5.17.0, trl 1.15.0, peft 0.21.2, unsloth 2026.11.1, python 3.12.3. 2026-11-04 14:49 UTC 시작 → 11-05 00:32 UTC 종료(9시간 43분: 설치·preflight·seed 3개·base zero-shot 포함), 번들 blade_v6c_20261104.tgz(`7ff02800…`), 해시 게이트(data_v5_hashes.json `39c302c5…`, test_v5_manifest `57fd384f…`, 프롬프트 `d0913c27…`) 통과, Pod 자동 정지. 회수 zip BLADE_lora_v6c_export.zip SHA-256 `97cd45dd2634831d…`, 결과 tar 해시는 SHA256SUMS_blade_v6c와 일치.
- v5 환경(비교): NVIDIA A100-SXM4-80GB, torch 2.14.1+cu130, transformers 5.17.0, unsloth 2026.10.11. 이번 Pod도 unsloth가 'Padding-free batching'을 자동으로 켰다(S5와 같음, v5 로그에는 없음). preflight: 14B 4bit 로드(48층·hidden 5120 확인), 짧은 generate 파싱 성공, 메모리 10.4 GiB.
- 손실 마스킹(completion-only): 0번 행 `loss mask check (row 0): 2857/2950 tokens masked (-100), 93 assistant tokens in loss` (3 seed 동일, v5 run_train.py 119행과 같은 train_on_responses_only 호출). trainable 파라미터 68,812,800(v5 7B 로그에는 기록 없음).

| run | steps | 학습 분 | train_loss | val oas loss(final / 최저) | val oas_code loss(final / 최저) | 학습 피크 GiB(alloc / reserved) | v5 같은 seed train_loss / val final(oas, oas_code) / 분 |
|---|---:|---:|---:|---|---|---|---|
| lora_v6c_s42 | 480 | 132.0 | 0.1344 | 0.2341 / 0.2163 | 0.1229 / 0.116 | 11.71 / 16.45 | 0.1464 / 0.2425, 0.1469 / 56.2 |
| lora_v6c_s43 | 480 | 131.8 | 0.1387 | 0.2358 / 0.2103 | 0.1223 / 0.1147 | 11.71 / 16.41 | 0.15 / 0.2479, 0.1447 / 56.2 |
| lora_v6c_s44 | 480 | 132.1 | 0.1376 | 0.2373 / 0.2169 | 0.1188 / 0.1102 | 11.71 / 15.28 | 0.1483 / 0.2535, 0.1404 / 56.1 |

세 seed 모두 480 step 완주, 발산 없음. val은 학습 정상 여부 확인용이며 체크포인트 선택에 쓰지 않았다(final 고정). 학습 시간은 seed당 132분으로 7B(A100 56분)의 2.4배다. val loss는 v5보다 조금 낮다(final oas 0.235 vs 0.248, oas_code 0.12 vs 0.14 수준)이나 test 지표 차이로 이어지지 않았다(3절).

## 3. test_v5 283 (dev) — oas_code

| 모델 | macro-F1 | 정확도 | manual 비율 | manual 건수(seed별) | 출력 오류(합) |
|---|---:|---:|---:|---|---:|
| lora_v5 (7B) | 0.683 ± 0.016 | 0.691 ± 0.007 | 16.6 ± 1.6% | 46 / 43 / 52 | 3 |
| lora_v6c (14B) | 0.680 ± 0.015 | 0.710 ± 0.012 | 14.3 ± 1.7% | 44 / 35 / 42 | 0 |
| base Qwen2.5-14B zero-shot | 0.504 | 0.576 | 0.7% | 2 | 0 |
| base Qwen2.5-7B zero-shot | 0.238 | 0.382 | 0.0% | 0 | 35 |

### label별 F1 (support)

| 모델 | public (19) | role_required (111) | membership_required (33) | tenant_match (0) | owner_match (34) | owner_or_admin (21) | manual_review_required (65) |
|---|---:|---:|---:|---:|---:|---:|---:|
| lora_v5 | 0.894 ± 0.063 | 0.818 ± 0.026 | 0.589 ± 0.048 | 0.000 ± 0.000 | 0.760 ± 0.024 | 0.536 ± 0.031 | 0.499 ± 0.027 |
| lora_v6c | 0.889 ± 0.080 | 0.870 ± 0.006 | 0.595 ± 0.012 | 0.000 ± 0.000 | 0.711 ± 0.028 | 0.539 ± 0.042 | 0.474 ± 0.035 |
| base 14B | 0.889 | 0.675 | 0.385 | 0.000 | 0.750 | 0.296 | 0.030 |

### 판정 label 정밀도 / 재현율 (seed별)

| run | owner_or_admin P / R / F1 | membership_required P / R / F1 | role_required P / R / F1 | public P / R / F1 | manual P / R / F1 |
|---|---|---|---|---|---|
| lora_v5_s42 | 0.500 / 0.619 / 0.553 | 0.453 / 0.727 / 0.558 | 0.867 / 0.820 / 0.843 | 0.933 / 0.737 / 0.824 | 0.587 / 0.415 / 0.486 |
| lora_v5_s43 | 0.400 / 0.667 / 0.500 | 0.518 / 0.849 / 0.644 | 0.838 / 0.748 / 0.790 | 1.000 / 0.842 / 0.914 | 0.605 / 0.400 / 0.481 |
| lora_v5_s44 | 0.455 / 0.714 / 0.556 | 0.489 / 0.667 / 0.564 | 0.861 / 0.784 / 0.821 | 1.000 / 0.895 / 0.944 | 0.596 / 0.477 / 0.530 |
| lora_v6c_s42 | 0.518 / 0.667 / 0.583 | 0.511 / 0.727 / 0.600 | 0.845 / 0.883 / 0.863 | 1.000 / 0.684 / 0.812 | 0.636 / 0.431 / 0.514 |
| lora_v6c_s43 | 0.500 / 0.571 / 0.533 | 0.491 / 0.788 / 0.605 | 0.861 / 0.892 / 0.876 | 1.000 / 0.947 / 0.973 | 0.657 / 0.354 / 0.460 |
| lora_v6c_s44 | 0.478 / 0.524 / 0.500 | 0.472 / 0.758 / 0.581 | 0.866 / 0.874 / 0.870 | 1.000 / 0.789 / 0.882 | 0.571 / 0.369 / 0.449 |

### 프로젝트별 정확도

| 모델 | rocketchat (157) | ghost (69) | umami (57) |
|---|---:|---:|---:|
| lora_v5 | 0.656 ± 0.013 | 0.758 ± 0.008 | 0.708 ± 0.066 |
| lora_v6c | 0.686 ± 0.026 | 0.783 ± 0.043 | 0.690 ± 0.037 |
| base 14B | 0.522 | 0.710 | 0.561 |

### 혼동표 (정답 행 → 예측 열, 3 seed 평균 건수)

| 정답 \ 예측 | public | role | member | tenant | owner | own+adm | manual | ERR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **public** (v5) | 15.7 | 0 | 0 | 0 | 0 | 0 | 3.3 | 0 |
| public (v6c) | 15.3 | 0 | 0 | 0 | 0 | 0 | 3.7 | 0 |
| **role** (v5) | 0 | 87 | 7.3 | 0 | 1.3 | 6 | 8.7 | 0.7 |
| role (v6c) | 0 | 98 | 4.7 | 0 | 1 | 3.3 | 4 | 0 |
| **member** (v5) | 0 | 0 | 24.7 | 0 | 4.3 | 0.3 | 3.7 | 0 |
| member (v6c) | 0 | 0 | 25 | 0 | 5.7 | 0 | 2.3 | 0 |
| **owner** (v5) | 0 | 0 | 6 | 0 | 26.3 | 0 | 1.7 | 0 |
| owner (v6c) | 0 | 0 | 6.7 | 0 | 25.3 | 0 | 2 | 0 |
| **own+adm** (v5) | 0 | 4.7 | 0.7 | 0 | 0 | 14 | 1.7 | 0 |
| own+adm (v6c) | 0 | 4.3 | 0 | 0 | 1 | 12.3 | 3.3 | 0 |
| **manual** (v5) | 0.3 | 10 | 12 | 0 | 3.3 | 11 | 28 | 0.3 |
| manual (v6c) | 0 | 12 | 14.7 | 0 | 4.3 | 9 | 25 | 0 |

### oas(명세만) 보조

| 모델 | macro-F1 | 정확도 | manual 비율 | 출력 오류(합) |
|---|---:|---:|---:|---:|
| lora_v5 | 0.402 ± 0.021 | 0.515 ± 0.023 | 26.3 ± 10.4% | 1 |
| lora_v6c | 0.432 ± 0.020 | 0.543 ± 0.021 | 20.5 ± 3.6% | 5 |
| base 14B | 0.238 | 0.293 | 66.4% | 0 |

원자료 scores_test_v5.json, eval_test_v5.md(scripts/eval_test_v5.py, manifest 해시 검증).

## 4. test_v30 회귀 — oas_code 합성 제외 207 (주지표 조건)

| 모델 | macro-F1(207) | macro-F1(265) | 정확도 | 구체 정밀도 | 구체 재현율 | 구체 응답률 | manual 비율 | public 오판(신, /35, seed별) | 출력 오류(seed별) |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| lora_v5 | 0.374 ± 0.010 | 0.700 ± 0.009 | 0.568 ± 0.010 | 0.796 ± 0.025 | 0.566 ± 0.010 | 0.712 ± 0.017 | 28.2 ± 2.3% | 3 / 2 / 1 | 4 / 0 / 2 |
| lora_v6c | 0.439 ± 0.015 | 0.695 ± 0.011 | 0.644 ± 0.010 | 0.813 ± 0.019 | 0.646 ± 0.008 | 0.795 ± 0.011 | 20.3 ± 1.3% | 2 / 2 / 1 | 1 / 0 / 1 |
| base 14B | 0.295 | 0.665 | 0.411 | 0.620 | 0.413 | 0.665 | 32.4% | 5 | 2 |

| 모델 | public | role_required | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|
| lora_v5 | 0.644 ± 0.047 | 0.442 ± 0.030 | 0.752 ± 0.018 | 0.000 ± 0.000 | 0.034 ± 0.003 |
| lora_v6c | 0.750 ± 0.012 | 0.624 ± 0.056 | 0.807 ± 0.014 | 0.000 ± 0.000 | 0.014 ± 0.025 |
| base 14B | 0.661 | 0.337 | 0.479 | 0.000 | 0.000 |

public 오판 id(v6c): s42: fc9dac901542ca88d688, 5a72ac6384c12b441687; s43: fc9dac901542ca88d688, 5a72ac6384c12b441687; s44: 5a72ac6384c12b441687. v5: s42: fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219; s43: 0797f5bb072770d50159, fc9dac901542ca88d688; s44: d8c5cf5eb0bfbd488219.

14B는 보류가 줄고(manual 28% → 20%) 응답한 것의 정밀도도 소폭 올랐다. public 오판은 줄었다. 회귀 기준 (2)·(3)은 충족이다.

### oas(명세만) 160

| 모델 | macro-F1(160) | 합성 제외 102 | 구체 정밀도 | manual 비율 | public 오판(신) | 출력 오류 |
|---|---:|---:|---:|---:|---|---|
| lora_v5 | 0.740 ± 0.016 | 0.462 ± 0.042 | 0.908 ± 0.021 | 43.1 ± 5.3% | 0 / 0 / 0 | 3 / 1 / 0 |
| lora_v6c | 0.721 ± 0.030 | 0.516 ± 0.052 | 0.854 ± 0.039 | 38.5 ± 3.0% | 2 / 1 / 0 | 0 / 0 / 0 |
| base 14B | 0.708 | 0.414 | 0.835 | 41.9% | 3 | 8 |

원자료 scores_test_v30.json, eval_v30.md(scripts/eval_v30.py --eval-def both).

## 5. test_v31_supp 222 (보조 조건)

| 모델 | oas_code macro-F1 | oas_code 정확도 | oas_code manual | oas macro-F1 | oas 정확도 | oas manual |
|---|---:|---:|---:|---:|---:|---:|
| lora_v5 | 0.485 ± 0.026 | 0.419 ± 0.039 | 20.7 ± 5.5% | 0.258 ± 0.057 | 0.218 ± 0.027 | 49.1 ± 6.2% |
| lora_v6c | 0.531 ± 0.059 | 0.479 ± 0.060 | 17.0 ± 2.8% | 0.299 ± 0.014 | 0.188 ± 0.030 | 59.5 ± 1.6% |
| base 14B | 0.245 | 0.230 | 6.3% | 0.155 | 0.126 | 66.2% |

| 모델 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| lora_v5 (oas_code F1) | 1.000 ± 0.000 | 0.491 ± 0.055 | 0.601 ± 0.089 | 0.235 ± 0.043 | 0.541 ± 0.072 | 0.328 ± 0.024 | 0.198 ± 0.052 |
| lora_v6c (oas_code F1) | 0.933 ± 0.115 | 0.542 ± 0.058 | 0.602 ± 0.145 | 0.233 ± 0.071 | 0.573 ± 0.133 | 0.535 ± 0.068 | 0.297 ± 0.028 |

| 모델 | chatwoot | chamilo | flowise | multitenant_lab | generic_university |
|---|---:|---:|---:|---:|---:|
| lora_v5 (oas_code 정확도) | 0.502 ± 0.072 | 0.374 ± 0.020 | 0.200 ± 0.000 | 0.667 ± 0.144 | 0.810 ± 0.165 |
| lora_v6c (oas_code 정확도) | 0.625 ± 0.128 | 0.443 ± 0.026 | 0.189 ± 0.042 | 0.750 ± 0.000 | 0.810 ± 0.095 |

supp oas_code macro-F1은 평균이 오르지만 seed 편차(s43만 0.598)가 커서 차이로 인정하지 않는다. 원자료 scores_supp.json, eval_supp.md(scripts/eval_v31_supp.py).

## 6. 예측 변화 v5 → v6c (test_v5 oas_code, 같은 seed)

| seed | 고쳐짐(v5 오답→v6c 정답) | 새로 틀림(v5 정답→v6c 오답) | 바뀐 전이 상위 |
|---|---:|---:|---|
| s42 | 28 | 20 | manual→role 8, role→own+adm 7, own+adm→role 6, member→manual 5, manual→own+adm 4, manual→member 4 |
| s43 | 31 | 22 | manual→role 9, manual→member 8, own+adm→role 8, member→role 5, own+adm→manual 4, member→manual 4 |
| s44 | 33 | 34 | manual→member 16, own+adm→role 13, role→manual 9, manual→role 6, member→role 5, member→owner 4 |

새로 manual이 된 건(v5 구체 → v6c manual)의 정답 label:

| seed | public | role | member | tenant | owner | own+adm | manual |
|---|---:|---:|---:|---:|---:|---:|---:|
| s42 | 2 | 1 | 3 | 0 | 0 | 2 | 7 |
| s43 | 1 | 2 | 2 | 0 | 1 | 2 | 6 |
| s44 | 3 | 4 | 0 | 0 | 0 | 4 | 7 |

seed 간 예측이 갈린 레코드: v6c 62/283(세 seed 모두 다름 3), v5 69/283. v6c에서 갈린 label 쌍: manual|member 17, manual|role 16, own+adm|role 12, manual|public 6, member|role 6, manual|own+adm 4, member|owner 3, manual|owner 2.

고쳐진 건과 새로 틀린 건이 seed마다 비슷한 수로 맞물려 순효과가 없다. 14B가 특정 경계(membership·owner_or_admin·manual)를 더 잘 푸는 증거는 없다.

## 7. S1-3 불일치 12건에서의 예측 (v5 → v6c, seed 42/43/44)

| id | 유형 | method path | 정답 | v5 s42/43/44 | v6c s42/43/44 |
|---|---|---|---|---|---|
| v5t-ghost-924636cc9d | G3-b/G6-c 경계(모든 역할 보유 권한) | GET /ghost/api/admin/posts/ | manual | role / role / role | role / role / role |
| v5t-rocketchat-0398a2f985 | canAccessRoom(G6-a) | GET /api/v1/rooms.membersOrderedByRole | manual | manual / manual / manual | manual / manual / manual |
| v5t-rocketchat-0780c8e386 | G3-a 그룹 안 역할 | POST /api/v1/groups.addOwner | role | role / role / role | role / role / role |
| v5t-rocketchat-09c0e4be92 | G3-a 그룹 안 역할 | POST /api/v1/groups.invite | role | role / role / manual | role / role / role |
| v5t-rocketchat-0d896bf7fc | G3-a 그룹 안 역할 | POST /api/v1/groups.setType | role | member / member / role | member / member / member |
| v5t-rocketchat-23a530da4b | G4-c/G6-b 경계(설정 의존) | POST /api/v1/users.resetAvatar | manual | own+adm / own+adm / own+adm | own+adm / own+adm / own+adm |
| v5t-rocketchat-7508165c03 | G3-a 그룹 안 역할 | POST /api/v1/groups.rename | role | member / member / member | member / member / member |
| v5t-rocketchat-d83dae7c4e | canAccessRoom(G6-a) | GET /api/v1/rooms.roles | manual | manual / manual / manual | manual / manual / manual |
| v5t-rocketchat-ec189eb0b4 | G3-a 그룹 안 역할 | POST /api/v1/e2e.resetRoomKey | role | manual / role / manual | role / role / role |
| v5t-rocketchat-f7c14cc85e | canAccessRoom(G6-a) | GET /api/v1/rooms.info | manual | manual / manual / manual | manual / manual / manual |
| v5t-umami-bf7e66056f | G6-a 복합 OR(Umami canView) | GET /api/websites/{websiteId}/shares | manual | manual / manual / manual | manual / manual / manual |
| v5t-umami-dd7523bace | G6-a 복합 OR(Umami canDelete) | DELETE /api/share/id/{shareId} | manual | own+adm / own+adm / own+adm | role / own+adm / own+adm |

| 유형 | 건수 | v5 정답(3 seed 합 / 가능) | v6c 정답(3 seed 합 / 가능) |
|---|---:|---:|---:|
| G3-b/G6-c 경계(모든 역할 보유 권한) | 1 | 0 / 3 | 0 / 3 |
| canAccessRoom(G6-a) | 3 | 9 / 9 | 9 / 9 |
| G3-a 그룹 안 역할 | 5 | 7 / 15 | 9 / 15 |
| G4-c/G6-b 경계(설정 의존) | 1 | 0 / 3 | 0 / 3 |
| G6-a 복합 OR(Umami canView) | 1 | 3 / 3 | 3 / 3 |
| G6-a 복합 OR(Umami canDelete) | 1 | 0 / 3 | 0 / 3 |

12건 합계 v5 19/36 → v6c 21/36. 이 12건은 라벨 정의(G3-a 등)가 학습 데이터와 어긋나는 경계라 베이스 크기로는 풀리지 않는다(작업 C′의 대상).

## 8. 출력 오류·출력 길이·추론 시간

| 셋·조건 | v5 출력 오류(s42/43/44) | v6c 출력 오류(s42/43/44) | v6c 오류 중 중국어 혼입 | base 14B 오류 | v6c 출력 토큰 평균/최대(s42) | 출력 문자 수 평균 v5 → v6c(s42) | v6c 프롬프트 토큰 평균/최대 |
|---|---|---|---:|---:|---|---|---|
| test_v5 oas_code | 1 / 0 / 2 | 0 / 0 / 0 | 0 | 0 | 80.4 / 110 | 232.3 → 229.2 | 3491.2 / 4051 |
| test_v5 oas | 0 / 1 / 0 | 2 / 0 / 3 | 5 | 0 | 71.7 / 103 | 189.3 → 203.4 | 2816.6 / 2843 |
| test_v30 oas_code | 5 / 4 / 3 | 1 / 0 / 1 | 1 | 6 | 73.8 / 112 | 203.8 → 201.7 | 3038.7 / 3841 |
| test_v30 oas | 3 / 1 / 0 | 0 / 0 / 0 | 0 | 8 | 71.8 / 102 | 189.6 → 197.9 | 2816.8 / 2976 |
| supp oas_code | 0 / 1 / 1 | 0 / 5 / 0 | 0 | 0 | 77.7 / 95 | 239.1 → 222.2 | 3324.3 / 4033 |
| supp oas | 2 / 0 / 1 | 0 / 0 / 1 | 1 | 0 | 72.1 / 106 | 207.6 → 200.5 | 2841.2 / 3428 |

| 셋·조건 | v5 행당 ms(A100, 7B, s42) | v6c 행당 ms(A100, 14B, s42/43/44) | v6c 벽시계 s(s42) | v6c 평가 피크 GiB(s42) | base 14B 행당 ms | 프롬프트 절단 |
|---|---:|---|---:|---:|---:|---:|
| test_v5 oas_code | 808.9 | 1787.8 / 1838.4 / 1819.2 | 506.0 | 24.19 | 1784.0 | 0 |
| test_v5 oas | 651.8 | 1549.4 / 1515.6 / 1600.1 | 438.6 | 24.14 | 1344.3 | 0 |
| test_v30 oas_code | 744.8 | 1810.9 / 1674.4 / 1715.5 | 480.0 | 23.57 | 1523.6 | 0 |
| test_v30 oas | 625.5 | 1581.6 / 1551.5 / 1583.6 | 425.5 | 21.01 | 1261.0 | 0 |
| supp oas_code | 753.8 | 1746.3 / 1744.2 / 1730.7 | 387.7 | 24.14 | 1682.1 | 0 |
| supp oas | 679.8 | 1660.7 / 1571.3 / 1594.0 | 368.8 | 23.57 | 1361.8 | 0 |

행당 ms는 배치 8 기준(배치 벽시계 / 8). 같은 A100에서 14B 추론은 7B의 약 2배다. 출력 오류(JSON 깨짐·7종 밖 label)는 14B에서 test_v5 oas_code 0건, test_v30 oas_code seed당 0~1건으로 v5(seed당 3~5건)보다 적다.

## 9. 해석·한계·다음 단계

- **불채택.** 베이스를 14B로 키워도 test_v5 macro-F1은 v5와 같은 수준(0.683 ± 0.016 → 0.680 ± 0.015)이고, 회귀 지표만 소폭 좋아졌다. 학습 데이터(data-v5)와 평가셋 사이의 라벨 정의 차이(S1-4: G3-a 그룹 안 역할, G6-a 복합 OR, G4-c 설정 의존)는 모델 크기로 메워지지 않는다. 사전 기록대로 v5를 최종 모델로 확정하고 S9(test_v6)는 v5로 간다.
- base 14B zero-shot은 base 7B zero-shot보다 크게 낫지만(test_v5 macro-F1 0.238 → 0.504), LoRA v5(7B)에는 미치지 못한다. 판정에는 쓰지 않았다.
- 작업 C′(v6d, 학습 정답만 교정)의 베이스는 S8 불채택이므로 7B(`unsloth/Qwen2.5-7B-Instruct-bnb-4bit`)다. 로컬 Ollama의 v4·qwen2.5:7b 부재(prep.md)는 S9 이후 배포 정리 때 복구한다.
- 산출물: 예측·로그 reports/eval/lora_v6c/{lora_v6c_s42,43,44,base_qwen14b_runpod}/, run_v6c.log, SHA256SUMS_blade_v6c(어댑터 tar 3개 ≈ 257 MB씩은 git 밖, 로컬 zip BLADE_lora_v6c_export.zip), 채점 scores_test_v5.json·eval_test_v5.md·scores_test_v30.json·eval_v30.md·scores_supp.json·eval_supp.md, 분석 analysis.json(scripts/analyze_lora_v6c.py). 커밋하지 않았다. 주지표·발표 수치(v5) 불변, test_v6 추론 없음.
