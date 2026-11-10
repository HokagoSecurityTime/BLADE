# data-v7 LoRA v7 1단계 보고 — test_v30 회귀만 (2026-11-08 채점, 학습 2026-11-07, 3 seed, 커밋 없음)

사전 기록 AGENTS.md "작업 data-v7"·"data-v7 동결"·"학습 승인·S9 사전 기록". 변경은 학습 데이터뿐: data-v7 = data-v6d SFT 행에 LLM 라벨 615행 재판정 반영(label 변경 45, OAS-only 새 manual 256행 제외) + test_v31_supp 221 + test_v5 281 추가(train 1,540 / val 159). 베이스 7B, 프롬프트 v3.0.1, label 먼저 출력, max_seq_len 4096, max_new_tokens 256, LoRA r16/α16·3 epoch·lr 2e-4·batch 2×4·cosine·adamw_8bit·completion-only 마스킹·greedy는 v5와 같다.
**(2026-11-09 추기) S9 결과는 s9/report.md — test_v6 oas_code macro-F1 v5 0.586 → v7 0.650(+0.064), 기준 3개 충족, 채택 후보(승인 대상).** 아래 본문은 1단계(2026-11-08) 시점 기록이다. 당시 판정셋 test_v6은 아직 추론하지 않았다(S9: test_v6 동결 후 같은 Pod에서 v5 3 seed + v7 3 seed 동시 추론). 이 보고는 회귀 지표 test_v30(oas_code 합성 제외 207 = 주지표 조건, oas 보조)만 다룬다. **test_v5·test_v31_supp는 v7의 학습 데이터이므로 채점하지 않았고 예측 파일도 없다**(run_v7.sh·run_train_v7.py가 입력 존재를 거부, 결과 디렉터리에 v5test_/supp_ 파일 0건 assert). v5 수치는 기존 예측 파일을 같은 채점기로 재채점한 값(재추론 없음). 주지표·발표 수치(v5)는 바꾸지 않는다.

## 1. 회귀 기준 (2)·(3) — 둘 다 충족(S9 대기)

| 기준(3 seed 평균) | v5 | v7 | 차이 | 기준 | 충족 |
|---|---:|---:|---:|---|---|
| (1) test_v6 macro-F1 상승 ≥ 0.016 | - | - | - | ≥ +0.016 | **S9 대기**(test_v6 미동결·미추론) |
| (2) test_v30 207 구체 정밀도 하락 ≤ 0.025 | 0.796 ± 0.025 | 0.824 ± 0.020 | +0.028 | 하락 ≤ 0.025 | 예 |
| (3) test_v30 207 public 오판(/35) 평균 ≤ 2.0 | 3 / 2 / 1 (평균 2.00) | 1 / 1 / 2 (평균 1.33) | -0.67 | ≤ 2.0 | 예 |

- 같은 seed끼리의 구체 정밀도 차이(v7 − v5): +0.041, +0.037, +0.006; macro-F1(207) 차이: +0.011, +0.028, +0.032.
- test_v30 207 macro-F1 0.374 → 0.398, 정확도 0.568 → 0.630, 구체 재현율 0.566 → 0.628, manual 비율 28.2% → 22.9%. 채택 여부는 S9(test_v6)에서 기준 (1)까지 보고 결정한다. test_v30은 v7 학습에 들어가지 않았다(겹침 0, 빌드 assert).

## 2. 실행 환경·학습

- Pod: RunPod kufx154dteqn1b(NVIDIA H100 80GB HBM3 79 GB, 볼륨 /workspace-2), torch 2.14.1+cu130(CUDA 13.0), transformers 5.17.0, trl 1.15.0, peft 0.21.2, unsloth 2026.11.3, python 3.12.3. 2026-11-07 07:37 → 09:22 UTC(1시간 45분: 설치·preflight 3분, seed당 약 34분 = 학습 29.2분 + test_v30 예측 2작업 약 3.5분). 번들 blade_v7_20261107.tgz(`80fc3795…`), 해시 게이트(SHA256SUMS_bundle·data_v7_hashes.json `bd33f1bc…`·프롬프트 `d0913c27…`, run.log `inputs verified against data_v7_hashes.json` 3 seed) 통과, `auto-stop armed`, 종료 후 Pod 정지(terminate 아님; S9를 같은 Pod에서 돌린다). 조기 판정 없음.
- v5 환경(비교): NVIDIA A100-SXM4-80GB, unsloth 2026.10.11. v6d(2026-11-05)는 unsloth 2026.11.2·transformers 5.x였고 v7은 unsloth 2026.11.3·torch 2.14.1+cu130로 라이브러리가 더 올라갔다(S9에서는 v5·v7 어댑터를 같은 Pod·같은 라이브러리로 돌려 이 차이를 상쇄한다). 손실 마스킹 0번 행 `loss mask check (row 0): 2904/2971 tokens masked (-100), 67 assistant tokens in loss`(3 seed 동일; v5·v6d는 2857/2950·93 — data-v7 0번 행의 rationale이 재판정으로 바뀌어 assistant 토큰 수가 다름, 마스킹 방식은 같음). LoRA trainable 40,370,176, 유효 배치 8, padding_free=True, resume 없음.

| run | steps | 학습 분 | train_loss | val oas loss(final / 최저) | val oas_code loss(final / 최저) | 피크 GPU GiB(alloc / reserved) | v5 같은 seed steps / train_loss / val final(oas, oas_code) / 분 |
|---|---:|---:|---:|---|---|---|---|
| lora_v7_s42 | 579 | 29.2 | 0.119 | 0.2885 / 0.2619 | 0.1746 / 0.1618 | 7.33 / 14.87 | 480 / 0.1464 / 0.2425, 0.1469 / 56.2 |
| lora_v7_s43 | 579 | 29.2 | 0.1166 | 0.312 / 0.2779 | 0.1869 / 0.1656 | 7.32 / 11.95 | 480 / 0.15 / 0.2479, 0.1447 / 56.2 |
| lora_v7_s44 | 579 | 29.2 | 0.1169 | 0.299 / 0.2676 | 0.1867 / 0.1722 | 7.31 / 13.53 | 480 / 0.1483 / 0.2535, 0.1404 / 56.1 |

579 step(1,540행 × 3 epoch / 유효 배치 8; v5 480 step) 완주, 발산 없음. val_v7(159)은 data-v6d val에 재판정만 반영한 것이고 체크포인트 선택에 쓰지 않았다(final 고정). train_loss는 v5보다 낮다(추가된 평가셋 502행의 rationale이 템플릿 형식이라 예측이 쉬움).

## 3. test_v30 회귀 — oas_code 합성 제외 207 (주지표 조건)

| 모델 | macro-F1(207) | macro-F1(265) | 정확도 | 구체 정밀도 | 구체 재현율 | 구체 응답률 | manual 비율 | public 오판(신, /35, seed별) | 출력 오류(seed별) |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| lora_v5 | 0.374 ± 0.010 | 0.700 ± 0.009 | 0.568 ± 0.010 | 0.796 ± 0.025 | 0.566 ± 0.010 | 0.712 ± 0.017 | 28.2 ± 2.3% | 3 / 2 / 1 | 4 / 0 / 2 |
| lora_v7 | 0.398 ± 0.019 | 0.732 ± 0.009 | 0.630 ± 0.015 | 0.824 ± 0.020 | 0.628 ± 0.015 | 0.762 ± 0.008 | 22.9 ± 1.6% | 1 / 1 / 2 | 5 / 0 / 3 |

### label별 F1 (support; membership·tenant는 207에 정답 0)

| 모델 | public (58) | role_required (39) | owner_match (106) | owner_or_admin (3) | manual_review_required (1) |
|---|---:|---:|---:|---:|---:|
| lora_v5 | 0.644 ± 0.047 | 0.442 ± 0.030 | 0.752 ± 0.018 | 0.000 ± 0.000 | 0.034 ± 0.003 |
| lora_v7 | 0.662 ± 0.015 | 0.476 ± 0.075 | 0.811 ± 0.009 | 0.000 ± 0.000 | 0.042 ± 0.003 |

### label별 정밀도 / 재현율 / F1 (seed별)

| run | public P / R / F1 | role P / R / F1 | owner P / R / F1 | own+adm P / R / F1 | manual P / R / F1 |
|---|---|---|---|---|---|
| lora_v5_s42 | 0.667 / 0.621 / 0.643 | 0.733 / 0.282 / 0.407 | 0.883 / 0.641 / 0.743 | 0.000 / 0.000 / 0.000 | 0.019 / 1.000 / 0.037 |
| lora_v5_s43 | 0.783 / 0.621 / 0.692 | 0.765 / 0.333 / 0.464 | 0.843 / 0.660 / 0.741 | 0.000 / 0.000 / 0.000 | 0.017 / 1.000 / 0.033 |
| lora_v5_s44 | 0.744 / 0.500 / 0.598 | 0.857 / 0.308 / 0.453 | 0.852 / 0.708 / 0.773 | 0.000 / 0.000 / 0.000 | 0.016 / 1.000 / 0.032 |
| lora_v7_s42 | 0.857 / 0.517 / 0.645 | 0.833 / 0.256 / 0.392 | 0.804 / 0.811 / 0.807 | 0.000 / 0.000 / 0.000 | 0.022 / 1.000 / 0.043 |
| lora_v7_s43 | 0.865 / 0.552 / 0.674 | 0.882 / 0.385 / 0.536 | 0.842 / 0.802 / 0.821 | 0.000 / 0.000 / 0.000 | 0.020 / 1.000 / 0.038 |
| lora_v7_s44 | 0.886 / 0.534 / 0.667 | 0.824 / 0.359 / 0.500 | 0.809 / 0.802 / 0.806 | 0.000 / 0.000 / 0.000 | 0.022 / 1.000 / 0.043 |

### 혼동표 (정답 행 → 예측 열, 3 seed 평균 건수, 207)

| 정답 \ 예측 | public | role | member | tenant | owner | own+adm | manual | ERR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **public** (v5) | 33.7 | 1.7 | 1.3 | 0 | 11 | 0 | 10.3 | 0 |
| public (v7) | 31 | 1 | 0 | 0 | 15.7 | 0 | 10 | 0.3 |
| **role** (v5) | 6.3 | 12 | 0.7 | 0 | 0.7 | 0 | 19 | 0.3 |
| role (v7) | 2.7 | 13 | 0 | 0 | 3 | 0 | 18.7 | 1.7 |
| **owner** (v5) | 6.3 | 1.7 | 0.3 | 0 | 71 | 0 | 25 | 1.7 |
| owner (v7) | 2 | 1.3 | 1.7 | 0 | 85.3 | 0 | 15 | 0.7 |
| **own+adm** (v5) | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| own+adm (v7) | 0 | 0 | 0 | 0 | 0.3 | 0 | 2.7 | 0 |
| **manual** (v5) | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| manual (v7) | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |

### manual 예측의 정답 label 분포 (v7, seed별)

| run | public | role | owner | own+adm | manual | 합 |
|---|---:|---:|---:|---:|---:|---:|
| lora_v7_s42 | 8 | 20 | 14 | 3 | 1 | 46 |
| lora_v7_s43 | 12 | 18 | 17 | 3 | 1 | 51 |
| lora_v7_s44 | 10 | 18 | 14 | 2 | 1 | 45 |

public 오판 id(v7): s42: fc9dac901542ca88d688; s43: fc9dac901542ca88d688; s44: fc9dac901542ca88d688, d8c5cf5eb0bfbd488219. v5: s42: fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219; s43: 0797f5bb072770d50159, fc9dac901542ca88d688; s44: d8c5cf5eb0bfbd488219. 합성 58건 macro-F1 v5 0.977 ± 0.024 → v7 0.988 ± 0.020(별도 구간).

### oas(명세만) 160 — 보조

| 모델 | macro-F1(160) | 합성 제외 102 | 구체 정밀도 | manual 비율 | public 오판(신, /47) | 출력 오류 |
|---|---:|---:|---:|---:|---|---|
| lora_v5 | 0.740 ± 0.016 | 0.462 ± 0.042 | 0.908 ± 0.021 | 43.1 ± 5.3% | 0 / 0 / 0 | 3 / 1 / 0 |
| lora_v7 | 0.755 ± 0.010 | 0.454 ± 0.029 | 0.886 ± 0.010 | 39.4 ± 1.7% | 0 / 0 / 2 | 0 / 0 / 1 |

원자료 scores_test_v30.json, eval_v30.md(scripts/eval_v30.py --eval-def both, v5·v7 6 run 한 번에 채점).

## 4. 예측 변화 v5 → v7 (test_v30 207, 같은 seed)

| seed | 고쳐짐(v5 오답→v7 정답) | 새로 틀림(v5 정답→v7 오답) | 바뀐 전이 상위 |
|---|---:|---:|---|
| s42 | 24 | 13 | manual→owner 15, public→manual 11, public→owner 10, manual→public 4, member→owner 3, ERR→owner 3 |
| s43 | 24 | 11 | manual→owner 18, public→manual 7, public→owner 4, owner→manual 4, manual→public 2, role→manual 2 |
| s44 | 20 | 6 | manual→owner 13, public→manual 7, manual→public 7, public→owner 3, manual→role 3, member→owner 2 |

고쳐진 건 / 새로 틀린 건의 정답 label:

| seed | public | role | owner | own+adm | manual |
|---|---:|---:|---:|---:|---:|
| s42 고쳐짐 | 3 | 1 | 20 | 0 | 0 |
| s42 새로 틀림 | 9 | 2 | 2 | 0 | 0 |
| s43 고쳐짐 | 2 | 3 | 19 | 0 | 0 |
| s43 새로 틀림 | 6 | 1 | 4 | 0 | 0 |
| s44 고쳐짐 | 6 | 2 | 12 | 0 | 0 |
| s44 새로 틀림 | 4 | 0 | 2 | 0 | 0 |

seed 간 예측이 갈린 레코드(207): v5 69(세 seed 모두 다름 1), v7 34(세 seed 모두 다름 3). v7에서 갈린 label 쌍: manual|owner 14, manual|public 7, manual|role 4, owner|public 4, manual|ERR 4, ERR|role 3, ERR|owner 2, member|owner 1.

v5·v7 여섯 run 모두 틀린 레코드 58/207 — 정답 label별 public 18, role 23, owner 14, own+adm 3.

## 5. 출력 오류·출력 길이·추론 시간

| 셋·조건 | v5 출력 오류(s42/43/44) | v7 출력 오류(s42/43/44) | v7 오류 중 중국어 혼입 | v7 오류 중 256 토큰 도달 | v7 출력 토큰 평균/최대(s42/43/44) | v7 행당 ms(H100, s42/43/44) |
|---|---|---|---:|---:|---|---|
| test_v30 oas_code(265) | 5 / 4 / 3 | 5 / 3 / 3 | 9 | 0 | 75.8/197 / 77.3/132 / 71.1/123 | 379.0 / 369.3 / 363.5 |
| test_v30 oas(269) | 3 / 1 / 0 | 0 / 0 / 1 | 1 | 1 | 68.4/108 / 73.5/105 / 64.8/256 | 324.9 / 342.3 / 333.3 |

v7 출력 오류 6작업 합계 12건(v5 같은 6작업 16건). 학습 29.2분/seed(H100), 추론 행당 0.33~0.38 s, 프롬프트 절단 0.

## 6. 해석·한계·다음 단계

- 회귀 기준 (2) 충족(구체 정밀도 0.796 → 0.824), (3) 충족(public 오판 평균 1.33). test_v30은 v7 학습에 들어가지 않은 유일한 기존 평가셋이라 이 수치가 회귀 확인의 전부다. 채택 판정 기준 (1)은 test_v6(S9)에서만 나온다.
- 한계: (a) v7 train에 test_v5 281·test_v31_supp 221이 들어갔으므로 v5와 v7의 test_v5·supp 수치는 비교 불가이고 이 보고에 없다. (b) data-v7 재판정 검수자는 Claude(AI)이고 사람 확인 시트(review/data_v7_human_check.xlsx: 변경 45·블라인드 31·추가행 rationale 50)는 미회수 — 불일치는 회수 후 한계로 기록한다. (c) v7 라이브러리(unsloth 2026.11.3, torch 2.14.1+cu130)가 v5 학습 때와 다르다. S9에서 v5·v7 어댑터를 같은 환경으로 추론해 비교 조건을 맞춘다. (d) 0번 행 마스킹 수치가 v5와 다른 것은 행 내용 변경 때문이며 completion-only 마스킹 자체는 동일하다.
- 다음(사전 기록대로): test_v6 사람 확인(공개_우선확인 44건 필수, 2026-11-09 12:00 KST) → 동결(manifest 해시) → S9 번들(test_v6 입력·manifest·TESTV6 기입 run_train_v7.py·run_s9.sh·v5 어댑터 `db6abe46…`) → 같은 Pod에서 v5 3 + v7 3 추론 → 기준 (1)·(2)·(3) 판정(마감 2026-11-09 18:00 KST, 미달이면 v5 유지).
- **배포 모델 한계(D1, 2026-11-10 사용자 조건부 수용 확정)**: 평가는 HF 어댑터(3 seed) 기준이고 배포는 s42 Q4_K_M GGUF(blade-qwen-lora-v7)다. 같은 어댑터 HF s42 대비 GGUF는 test_v30 oas_code 207 구체 정밀도 −0.032(0.808 → 0.776, 허용 폭 v4 sd 0.026 이탈)·265 구체 정밀도 −0.025(폭 0.018 이탈), public 오판 1 → 3(+2: crAPI owner_match 2건 `GET /identity/api/v2/user/dashboard`·`POST /identity/api/v2/vehicle/resend_email`), macro-F1 207 −0.007(폭 안), manual 비율 22.6% → 23.4%. v5 때(보류 감소·정밀도 유지)와 달리 보류 이동으로 설명되지 않는 소폭 정밀도 하락이다(구체 예측 약 160건 중 5건 규모). GGUF 경로의 confidence는 test 265건 중 261건이 0.9로 고정이라 **MIN_CONFIDENCE 0.9가 실질적으로 거르는 행은 0건**이다(val에서는 0.7·0.85가 29/159). 운영 조건: public 판정 정책은 승인(PENDING → ACTIVE) 시 우선 검토 대상으로 둔다. 롤백 모델 blade-qwen-lora-v5(문턱 0.9) 유지. 상세 reports/eval/lora_v7_gguf/equivalence_check.md.
- 산출물: 예측·로그 reports/eval/lora_v7/lora_v7_s{42,43,44}/, run_v7.log, SHA256SUMS_blade_v7(어댑터 tar 3개는 git 밖, 로컬 zip BLADE_lora_v7_export.zip SHA-256 `283d2349227fc592…`; S9에 필요), 채점 scores_test_v30.json·eval_v30.md, 분석 analysis.json(scripts/analyze_lora_v7.py). 커밋하지 않았다. test_v6 추론 없음.
