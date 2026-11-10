# S9 보고 — data-v7 LoRA v7 vs LoRA v5, hold-out test_v6 (추론 2026-11-08 13:54–14:40 UTC, 채점 2026-11-09, 커밋 없음)

사전 기록 AGENTS.md "작업 data-v7"(채택 기준 3조건)·"test_v6 동결"(S9 절차). test_v6 289건(동결 2026-11-08, manifest `a9ca4fca05ee3e59…`, A안 라벨링: AI 1차 + 독립 AI 2차 + 경계 사례 사람 확정)을 **같은 Pod(n1tl7hwtpbqnew, H100 80GB)·같은 라이브러리**에서 v5 어댑터 3개(s42·43·44, blade_v5_adapters.tar.gz `db6abe46…`)와 v7 어댑터 3개로 한 번에 추론했다(run_s9.sh, 각 run 해시 게이트 data_v7·test_v6 manifest 통과, 학습 없음, 기본 디코딩 greedy·max_new_tokens 256). v5·v7 어느 쪽도 S9 전에 test_v6을 추론하지 않았다. 판정 조건은 oas_code(주지표와 같은 입력 조건), oas(명세만)는 보조. test_v5·test_v31_supp는 v7 학습 데이터라 비교에 쓰지 않는다. 주지표(test_v30 207)·발표 수치(v5)는 이 보고로 바뀌지 않으며 전환은 사용자 승인 뒤의 별도 작업이다.

## 1. 판정 — 사전 기준 3개 모두 충족 → **채택 후보**(사용자 승인 대상; 승인 전까지 v5가 최종 모델)

| 기준(3 seed 평균) | v5 | v7 | 차이 | 기준 | 충족 |
|---|---:|---:|---:|---|---|
| (1) test_v6 oas_code macro-F1 상승 ≥ 0.016 | 0.586 ± 0.006 | 0.650 ± 0.016 | +0.064 | ≥ +0.016 | **예** |
| (2) test_v30 207 구체 정밀도 하락 ≤ 0.025 (1단계) | 0.796 ± 0.025 | 0.824 ± 0.020 | +0.028 | 하락 ≤ 0.025 | 예 |
| (3) test_v30 207 public 오판(/35) 평균 ≤ 2.0 (1단계) | 3 / 2 / 1 (평균 2.00) | 1 / 1 / 2 (평균 1.33) | -0.67 | ≤ 2.0 | 예 |

- 같은 seed끼리의 test_v6 macro-F1 차이(v7 − v5): +0.088, +0.053, +0.050 — 세 seed 모두 v5 표준편차(0.006)와 v7 표준편차(0.016)보다 크다("표준편차보다 큰 차이만 인정" 규칙 충족).
- test_v6 정확도 0.606 → 0.661, 구체 정밀도 0.688 → 0.758, 구체 재현율 0.629 → 0.682, manual 비율 15.8% → 18.1%, public 오판(/265) 1 / 1 / 1 → 1 / 0 / 0. 네 프로젝트 중 세 곳(seahub·Redash·Penpot) 상승, GlitchTip 제자리.
- 시한: 추론은 2026-11-08 23:40 KST에 끝났고(마감 11-09 18:00 KST 이전), 결과 파일 회수·채점은 11-09 18:44 KST 이후다. 중단 규칙 적용 여부는 사용자 판단 사항으로 기록한다.

## 2. test_v6 289 — oas_code

| 모델 | macro-F1 | 정확도 | 구체 정밀도 | 구체 재현율 | manual 비율 | public 오판(/265, seed별) | 출력 오류(seed별) |
|---|---:|---:|---:|---:|---:|---|---|
| lora_v5 | 0.586 ± 0.006 | 0.606 ± 0.006 | 0.688 ± 0.012 | 0.629 ± 0.008 | 15.8 ± 2.9% | 1 / 1 / 1 | 0 / 1 / 1 |
| lora_v7 | 0.650 ± 0.016 | 0.661 ± 0.012 | 0.758 ± 0.038 | 0.682 ± 0.024 | 18.1 ± 2.9% | 1 / 0 / 0 | 1 / 0 / 1 |

### label별 F1 (support)

| 모델 | public (21) | role_required (65) | membership_required (37) | tenant_match (38) | owner_match (59) | owner_or_admin (17) | manual_review_required (52) |
|---|---:|---:|---:|---:|---:|---:|---:|
| lora_v5 | 0.913 ± 0.000 | 0.537 ± 0.025 | 0.536 ± 0.025 | 0.131 ± 0.027 | 0.871 ± 0.019 | 0.585 ± 0.003 | 0.532 ± 0.015 |
| lora_v7 | 0.927 ± 0.012 | 0.618 ± 0.024 | 0.568 ± 0.027 | 0.249 ± 0.076 | 0.912 ± 0.016 | 0.714 ± 0.042 | 0.564 ± 0.055 |

### label별 정밀도 / 재현율 / F1 (seed별)

| run | public P / R / F1 | role P / R / F1 | member P / R / F1 | tenant P / R / F1 | owner P / R / F1 | own+adm P / R / F1 | manual P / R / F1 |
|---|---|---|---|---|---|---|---|
| lora_v5_s42 | 0.840 / 1.000 / 0.913 | 0.487 / 0.569 / 0.525 | 0.439 / 0.784 / 0.563 | 1.000 / 0.053 / 0.100 | 0.906 / 0.814 / 0.857 | 0.452 / 0.824 / 0.583 | 0.639 / 0.442 / 0.523 |
| lora_v5_s43 | 0.840 / 1.000 / 0.913 | 0.449 / 0.615 / 0.519 | 0.545 / 0.486 / 0.514 | 1.000 / 0.079 / 0.146 | 0.943 / 0.848 / 0.893 | 0.441 / 0.882 / 0.588 | 0.529 / 0.519 / 0.524 |
| lora_v5_s44 | 0.840 / 1.000 / 0.913 | 0.494 / 0.661 / 0.566 | 0.500 / 0.568 / 0.532 | 1.000 / 0.079 / 0.146 | 0.940 / 0.797 / 0.862 | 0.452 / 0.824 / 0.583 | 0.560 / 0.538 / 0.549 |
| lora_v7_s42 | 0.840 / 1.000 / 0.913 | 0.556 / 0.769 / 0.645 | 0.667 / 0.540 / 0.597 | 0.800 / 0.210 / 0.333 | 0.964 / 0.898 / 0.930 | 0.615 / 0.941 / 0.744 | 0.519 / 0.519 / 0.519 |
| lora_v7_s43 | 0.875 / 1.000 / 0.933 | 0.529 / 0.692 / 0.600 | 0.588 / 0.540 / 0.563 | 0.800 / 0.105 / 0.186 | 0.929 / 0.881 / 0.904 | 0.625 / 0.882 / 0.732 | 0.508 / 0.596 / 0.549 |
| lora_v7_s44 | 0.875 / 1.000 / 0.933 | 0.516 / 0.739 / 0.608 | 0.500 / 0.595 / 0.543 | 0.833 / 0.132 / 0.227 | 0.962 / 0.848 / 0.901 | 0.560 / 0.824 / 0.667 | 0.682 / 0.577 / 0.625 |

### 프로젝트별 정확도

| 모델 | seahub (92) | redash (72) | glitchtip (70) | penpot (55) |
|---|---:|---:|---:|---:|
| lora_v5 | 0.649 ± 0.038 | 0.519 ± 0.029 | 0.690 ± 0.079 | 0.539 ± 0.021 |
| lora_v7 | 0.746 ± 0.017 | 0.588 ± 0.021 | 0.686 ± 0.000 | 0.582 ± 0.031 |

### 정답 출처(label_status)별 정확도 · Redash G1-b 경계 18건

| 모델 | human_confirmed (5) | ai_double_confirmed (67) | ai_single (217) | G1-b 18 정확도(seed별) | G1-b 예측 분포(s42) |
|---|---:|---:|---:|---|---|
| lora_v5 | 0.400 ± 0.000 | 0.448 ± 0.015 | 0.659 ± 0.005 | 0.00 / 0.00 / 0.00 | {'manual_review_required': 1, 'owner_or_admin': 1, 'role_required': 16} |
| lora_v7 | 0.533 ± 0.115 | 0.493 ± 0.015 | 0.716 ± 0.015 | 0.00 / 0.00 / 0.00 | {'manual_review_required': 1, 'role_required': 17} |

G1-b 18건(Redash `@require_admin` + `current_org` → tenant_match로 확정한 경계)은 두 모델 모두 거의 전부 role_required로 예측해 0/18이다. 이 18건을 role_required로 채점하면 두 모델 모두 정확도가 오르지만 상대 비교는 바뀌지 않는다(두 모델 예측이 같음). 사람 확정 5건·AI 이중 확정 67건의 정확도가 AI 단독 217건보다 낮은 것은 경계 사례·감사 표본의 난도가 높아서이며 표본이 작아 해석에 주의한다.

### 혼동표 (정답 행 → 예측 열, 3 seed 평균 건수)

| 정답 \ 예측 | public | role | member | tenant | owner | own+adm | manual | ERR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **public** (v5) | 21 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| public (v7) | 21 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **role** (v5) | 0 | 40 | 13.7 | 0 | 1 | 4 | 6.3 | 0 |
| role (v7) | 0 | 47.7 | 12 | 0 | 0 | 0 | 5.3 | 0 |
| **member** (v5) | 0 | 9 | 22.7 | 0 | 0 | 0.3 | 5 | 0 |
| member (v7) | 0 | 5.7 | 20.7 | 0 | 0 | 0 | 10.7 | 0 |
| **tenant** (v5) | 0 | 26 | 1.3 | 2.7 | 0 | 2 | 5.7 | 0.3 |
| tenant (v7) | 0 | 26 | 0 | 5.7 | 0 | 1.7 | 4 | 0.7 |
| **owner** (v5) | 0.3 | 0 | 7 | 0 | 48.3 | 0.3 | 2.7 | 0.3 |
| owner (v7) | 0 | 0.7 | 2.3 | 0.7 | 51.7 | 0.7 | 3 | 0 |
| **own+adm** (v5) | 0 | 2 | 0.7 | 0 | 0 | 14.3 | 0 | 0 |
| own+adm (v7) | 0 | 2 | 0 | 0 | 0 | 15 | 0 | 0 |
| **manual** (v5) | 3.7 | 7 | 1.7 | 0 | 2.7 | 11 | 26 | 0 |
| manual (v7) | 3.3 | 7.3 | 1 | 0.7 | 2.7 | 7.7 | 29.3 | 0 |

### manual 예측의 정답 label 분포 (seed별)

| run | public | role | member | tenant | owner | own+adm | manual | 합 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lora_v5_s42 | 0 | 2 | 2 | 6 | 3 | 0 | 23 | 36 |
| lora_v5_s43 | 0 | 11 | 6 | 5 | 2 | 0 | 27 | 51 |
| lora_v5_s44 | 0 | 6 | 7 | 6 | 3 | 0 | 28 | 50 |
| lora_v7_s42 | 0 | 8 | 12 | 1 | 4 | 0 | 27 | 52 |
| lora_v7_s43 | 0 | 7 | 12 | 7 | 4 | 0 | 31 | 61 |
| lora_v7_s44 | 0 | 1 | 8 | 4 | 1 | 0 | 30 | 44 |

public 오판 id — v5: s42: v6t-seahub-d1f95197b7; s43: v6t-seahub-327926aa2e; s44: v6t-seahub-c350e74c81. v7: s42: v6t-seahub-327926aa2e; s43: -; s44: -.

### oas(명세만) — 보조

| 모델 | macro-F1 | 정확도 | manual 비율 | public 오판(/265, seed별) | 출력 오류(seed별) |
|---|---:|---:|---:|---|---|
| lora_v5 | 0.319 ± 0.035 | 0.383 ± 0.040 | 59.6 ± 6.1% | 5 / 7 / 6 | 1 / 0 / 0 |
| lora_v7 | 0.302 ± 0.033 | 0.393 ± 0.014 | 58.6 ± 1.4% | 14 / 24 / 6 | 3 / 5 / 21 |

oas 조건에서는 두 모델이 비슷하고(macro-F1 0.319 vs 0.302), v7의 public 오판(14 / 24 / 6)과 s44 출력 오류(21건)가 v5보다 많다. 판정 기준은 oas_code이지만 명세만 입력일 때 v7의 public 과대 예측은 한계로 기록한다(test_v30 oas에서는 v7 public 오판 0/0/2).

원자료 s9/scores_test_v6.json, eval_test_v6.md(scripts/eval_test_v6.py).

## 3. 예측 변화 v5 → v7 (test_v6 oas_code, 같은 seed)

| seed | 고쳐짐(v5 오답→v7 정답) | 새로 틀림(v5 정답→v7 오답) | 바뀐 전이 상위 |
|---|---:|---:|---|
| s42 | 34 | 13 | member→manual 20, member→role 13, manual→tenant 6, own+adm→role 5, role→manual 4, manual→owner 3, member→owner 3 |
| s43 | 24 | 10 | role→manual 12, member→manual 8, own+adm→role 8, manual→member 7, role→member 5, manual→owner 3, member→role 3 |
| s44 | 18 | 5 | manual→member 9, own+adm→role 5, member→role 4, role→manual 3, member→manual 3, own+adm→manual 3, manual→owner 2 |

고쳐진 건 / 새로 틀린 건의 정답 label:

| seed | public | role | member | tenant | owner | own+adm | manual |
|---|---:|---:|---:|---:|---:|---:|---:|
| s42 고쳐짐 | 0 | 13 | 0 | 6 | 5 | 2 | 8 |
| s42 새로 틀림 | 0 | 0 | 9 | 0 | 0 | 0 | 4 |
| s43 고쳐짐 | 0 | 7 | 4 | 1 | 4 | 1 | 7 |
| s43 새로 틀림 | 0 | 2 | 2 | 0 | 2 | 1 | 3 |
| s44 고쳐짐 | 0 | 5 | 3 | 2 | 4 | 0 | 4 |
| s44 새로 틀림 | 0 | 0 | 2 | 0 | 1 | 0 | 2 |

seed 간 예측이 갈린 레코드: v5 70/289(세 seed 모두 다름 5), v7 56/289(세 seed 모두 다름 2). v7에서 갈린 label 쌍: manual|member 17, manual|role 9, member|role 7, manual|tenant 7, own+adm|role 5, manual|owner 4, owner|own+adm 3, manual|own+adm 3.

v5·v7 여섯 run 모두 틀린 레코드 70/289 — 정답 label별 role 14, member 6, tenant 30, owner 4, own+adm 1, manual 15; 프로젝트별 glitchtip 11, penpot 18, redash 22, seahub 19; 정답 출처별 ai_single 40, ai_double_confirmed 29, human_confirmed 1. 여기에는 G1-b 18건(tenant → role)과 Redash owner_or_admin·manual 경계가 몰려 있다.

## 4. 실행 환경·추론 시간·출력 오류

- Pod n1tl7hwtpbqnew(NVIDIA H100 80GB HBM3 79 GB, 볼륨 /workspace), torch 2.13.0+cu129(CUDA 12.9), transformers 5.17.0, trl 1.15.0, peft 0.21.2, unsloth 2026.11.3, python 3.12.3 — **여섯 run 동일**(env.json 일치 assert). v7 학습 Pod(kufx154dteqn1b, torch 2.14.1+cu130)와 torch 버전이 다르지만 v5·v7 비교는 같은 환경 안에서 이뤄졌다. 번들 blade_s9_test_v6_20261108.tgz(`fa7b93f4…`), 2026-11-08 13:52–14:40 UTC(setup 1분, run당 7~8분), 게이트(data_v7_hashes·test_v6 manifest `a9ca4fca…`, `final adapter exists: skip training`) 6 run 모두 확인, 자동 정지.

| run | 조건 | 행당 ms | 출력 토큰 평균/최대 | 256 도달 | 프롬프트 최대 토큰 | 절단 | 출력 오류 | 중국어 혼입 | 피크 GiB |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| lora_v5_s42 | oas_code | 748.7 | 80.1 / 97 | 0 | 3771 | 0 | 0 | 0 | 14.41 |
| lora_v5_s42 | oas | 657.4 | 75.1 / 148 | 0 | 2896 | 0 | 1 | 1 | 12.45 |
| lora_v5_s43 | oas_code | 758.2 | 79.8 / 97 | 0 | 3771 | 0 | 1 | 1 | 14.41 |
| lora_v5_s43 | oas | 630.5 | 71.5 / 102 | 0 | 2896 | 0 | 0 | 0 | 12.45 |
| lora_v5_s44 | oas_code | 744.7 | 79.3 / 101 | 0 | 3771 | 0 | 1 | 0 | 14.41 |
| lora_v5_s44 | oas | 640.9 | 71.4 / 134 | 0 | 2896 | 0 | 0 | 0 | 12.45 |
| lora_v7_s42 | oas_code | 755.9 | 79.9 / 192 | 0 | 3771 | 0 | 1 | 1 | 14.41 |
| lora_v7_s42 | oas | 696.7 | 75.3 / 167 | 0 | 2896 | 0 | 3 | 3 | 12.45 |
| lora_v7_s43 | oas_code | 758.5 | 80.3 / 102 | 0 | 3771 | 0 | 0 | 0 | 14.41 |
| lora_v7_s43 | oas | 715.7 | 76.9 / 170 | 0 | 2896 | 0 | 5 | 4 | 12.45 |
| lora_v7_s44 | oas_code | 759.9 | 81.4 / 97 | 0 | 3771 | 0 | 1 | 0 | 14.41 |
| lora_v7_s44 | oas | 794.4 | 80.6 / 256 | 6 | 2896 | 0 | 21 | 20 | 12.45 |

## 5. 한계

- test_v6 정답의 75%(217/289)는 AI 1차 판정 단독, 23%(67)는 AI 둘의 일치, 사람 확정은 5건(A안, 마감 사유). 감사 일치율 92.7%는 AI 간 일치다. 정답 오류가 두 모델에 같은 방향으로 작용한다고 가정할 수 없으나, v5·v7 비교는 같은 정답·같은 입력·같은 환경에서 이뤄졌다.
- label 편중: tenant_match 38 중 Redash 27, membership_required 37 중 GlitchTip 27, owner_or_admin 17 중 Redash 13; Penpot에 tenant·membership·owner_or_admin 0. G1-b 18건은 두 모델 모두 0/18(tenant → role).
- v7의 학습 데이터에는 test_v5 281·test_v31_supp 221이 들어 있어 그 두 셋의 v7 수치는 존재하지 않는다. v7 1단계(test_v30 207) 결과는 reports/eval/lora_v7/report.md. oas(명세만) 조건의 v7 public 오판 증가와 s44 출력 오류 21건(중국어 혼입)은 배포 전환 시 확인 항목.
- 채점 시각이 사전 마감(11-09 18:00 KST)을 넘었다(추론 완료는 11-08 23:40 KST). data-v7 사람 확인 시트(review/data_v7_human_check.xlsx)는 미회수.

## 6. 다음 (사용자 승인 대상)

- 채택 승인 시 C-5와 같은 절차: s42 어댑터 fp16 병합 → GGUF Q4_K_M(컨테이너 디스크), 변환 동등성(test_v30 oas_code, v4/v5 때와 같은 허용 폭 규칙), MIN_CONFIDENCE(val_sft_v7, choose_threshold --rule precision), Ollama blade-qwen-lora-v7 등록·환경변수 전환, verify_lora_pipeline + pytest, 발표 수치 표 갱신(v5 병기). 전환 전까지 v5가 최종 모델이며 발표 주 수치는 v5다.
- 산출물: reports/eval/lora_v7/s9/{report.md, analysis.json, scores_test_v6.json, eval_test_v6.md, lora_v5_s4*/, lora_v7_s4*/, run_s9.log, SHA256SUMS_s9}(scripts/eval_test_v6.py, analyze_s9_v7.py). 커밋하지 않았다.
