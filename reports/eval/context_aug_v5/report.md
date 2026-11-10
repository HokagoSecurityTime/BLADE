# S4 권한 문맥 보강 추론 실험 — 결과 보고 (2026-11-04)

실험 조건은 AGENTS.md "작업 S4" 절의 사전 기록 그대로다: 프롬프트 v3.0.1 고정, LoRA v5 final 어댑터 3 seed(42·43·44), 기본 디코딩(greedy, max_new_tokens 256, batch 8), 입력 = 기존 oas_code 입력 + `[관련 권한 코드]` 블록. 학습 없음, test_v6 추론 없음. Pod 실행 번들 `export/blade_s4_ctx_h100_20261104.tgz`(SHA-256 `1920ffff…`), 결과 회수본 `reports/eval/context_aug_v5/pod_results/`(tar SHA-256 `09755545…`, TAR_SHA256.txt). 채점은 scripts/eval_combined_v5.py 정의(score_ctx.metrics)로 로컬에서 다시 했고 Pod 채점(scores_all.json)과 일치한다.

## 1. 판정 — 채택 기준 미달 (불채택)

사전 고정 채택 기준 세 가지(셋 다 충족해야 채택):

| 기준 | v5 (3 seed) | ctx4096 (3 seed) | 차이 | 판정 |
|---|---|---|---|---|
| test_v5 macro-F1 ≥ v5 + 0.016 | 0.683 ± 0.016 | 0.606 ± 0.029 | -0.0766 | **미달** |
| test_v30 207 구체 정밀도 하락 ≤ 0.025 | 0.796 ± 0.025 | 0.812 ± 0.035 | 하락 -0.0167 | 충족 |
| test_v30 207 public 오판(/35) 평균 ≤ 2.0 | 3 / 2 / 1 (평균 2.00) | 3 / 3 / 1 (평균 2.33) | | **미달** |

**결론: 불채택.** 권한 문맥 블록을 붙인 입력은 test_v5 macro-F1을 v5 대비 0.077 낮췄다(seed 표준편차 0.016·0.029보다 큰 하락). test_v30 207 구체 정밀도는 오히려 0.017 올랐지만(블록이 붙은 건은 13/207뿐이라 사실상 표식 `[관련 권한 코드] (없음)` 추가에 대한 회귀 확인), public 오판 평균은 2.33건으로 기준 2.0을 넘는다. 프롬프트 v3.0.1과 현재 v5 어댑터는 문맥 블록 없이 학습됐으므로, 블록은 학습 분포 밖 입력으로 작용했다. S5(v3.1 프롬프트·토큰 확률 confidence) 설계에서 문맥 블록을 다시 쓰려면 학습 입력에도 같은 형식을 넣어야 한다.

## 2. 실행 환경·게이트·시간

- GPU NVIDIA H100 80GB HBM3(capability (9, 0), VRAM 79 GB), 드라이버 595.91.07, Python 3.12.3, torch 2.8.0+cu128(CUDA 12.8), transformers 5.22.1, peft 0.21.2, bitsandbytes 0.50.2, unsloth 미설치(로더 hf: AutoModelForCausalLM + bnb 4bit 체크포인트 + attn_implementation=sdpa), flash-attn 미설치.
- 환경 게이트(env_check.json): torch≥2.4·CUDA≥12.1·capability (9,0)·bitsandbytes NF4 forward·sdpa 모두 통과(`ENV_OK=1`). 번들 해시·기준 예측 3파일 해시 OK. 어댑터는 `/workspace/blade_v5_adapters.tar.gz`(SHA-256 `db6abe46…`)에서 복원(어댑터 3개 각 161,533,192 bytes).
- 기준선 재현(v5 s42, 문맥 없는 원본 test_v5 입력 20건 층화 seed 42): label 일치 20/20(100%), raw 출력 바이트 동일 16/20 → 게이트 통과(`BASELINE_PASSED=1`). unsloth 로더(기존 v5 평가) 대신 transformers+bitsandbytes 로더를 써도 label이 같음을 확인했다. raw가 다른 4건은 rationale 문구 차이다.
- Pod 시간: 시작 16:38:16 → 마지막 추론 종료 17:10:03 UTC(약 32분, 설치·어댑터 복원·기준선 포함). 절단(tokenizer truncation) 0건, 프롬프트 최대 토큰 ctx4096 4,090 / ctx6144 5,583.

| 작업 | 행 | 모델 로드 s | 추론 벽시계 s | ms/행 | 파싱 오류 | 프롬프트 최대 토큰 |
|---|---:|---:|---:|---:|---:|---:|
| baseline_s42.jsonl | 20 | 55.8 | 15.5 | 763.7 | 0 | 3926 |
| pred_test_v30_ctx4096_s42.jsonl | 265 | 8.0 | 187.6 | 699.5 | 2 | 3852 |
| pred_test_v30_ctx4096_s43.jsonl | 265 | 7.3 | 186.5 | 695.2 | 2 | 3852 |
| pred_test_v30_ctx4096_s44.jsonl | 265 | 7.5 | 175.2 | 653.0 | 3 | 3852 |
| pred_test_v30_ctx6144_s42.jsonl | 265 | 7.2 | 171.3 | 638.4 | 2 | 3852 |
| pred_test_v5_ctx4096_s42.jsonl | 283 | 7.7 | 214.3 | 747.0 | 1 | 4090 |
| pred_test_v5_ctx4096_s43.jsonl | 283 | 7.4 | 220.3 | 768.4 | 0 | 4090 |
| pred_test_v5_ctx4096_s44.jsonl | 283 | 8.6 | 222.3 | 775.3 | 0 | 4090 |
| pred_test_v5_ctx6144_s42.jsonl | 283 | 6.8 | 228.5 | 796.9 | 0 | 5583 |

(test_v30 행 265 = oas_code 전체; 채점은 취약 API 207건. 파싱 오류 수는 265건 기준이며 207건 기준 출력 오류는 4절 표.)

- Pod 스크립트의 마지막 `summary` 단계는 score_ctx.py의 timing 키 오기(`rows` → `rows_total`)로 KeyError가 났다. 이 단계는 모든 추론·채점·pack 뒤의 표 출력뿐이라 예측·채점 파일에는 영향이 없고, 로컬에서 키를 고친 뒤 같은 코드로 재채점했다(Pod `scores_all.json`과 수치 일치). `ALL DONE`·Pod 정지 호출은 그 뒤 줄이라 회수본 로그에는 없다(Pod 정지 여부는 콘솔에서 확인).

## 3. 예산 선택 (seed 42, 사전 규칙)

| 조건 | test_v5 macro-F1 | test_v30 207 구체 정밀도 | test_v30 207 public 오판 |
|---|---|---|---|
| v5 (문맥 없음) | 0.6661 | 0.7667 | 3 |
| ctx4096 | 0.5738 | 0.7793 | 3 |
| ctx6144 | 0.5567 | 0.7793 | 3 |

- 선택: **ctx4096** (Pod 기록: `rule 1: ctx6144 test_v30 concrete precision drop -0.0126 > 0.025 or public misjudge 3 > 2`). 규칙 1이 public 오판 3 > 2로 발동했는데, 이 3건은 v5 s42 자체의 3건과 같은 id이고 test_v30 입력은 두 예산이 바이트 동일(블록 13/207)이라 ctx6144 고유의 악화가 아니다. 규칙 2로 판단해도 test_v5 macro-F1 차이 +0.0171로 ctx4096이 높아 결과는 같다. test_v30 두 예산의 예측 label은 207건 전부 동일(확인).
- ctx6144는 학습 길이(4096) 밖 입력이며 test_v5에서 ctx4096보다 더 낮았다(Umami 0.474). 이후 s43·s44는 ctx4096만 실행했다.

## 4. test_v5 283건 (dev, oas_code)

| 모델 | seeds | macro-F1 | 정확도 | 구체 정밀도 | 구체 재현율 | manual 비율 | 출력 오류 |
|---|---|---|---|---|---|---|---|
| v5 | 42,43,44 | 0.683 ± 0.016 | 0.691 ± 0.007 | 0.845 ± 0.009 | 0.769 ± 0.003 | 16.6% ± 1.6% | 1 / 0 / 2 |
| ctx4096 | 42,43,44 | 0.606 ± 0.029 | 0.651 ± 0.007 | 0.822 ± 0.012 | 0.735 ± 0.023 | 16.5% ± 4.1% | 1 / 0 / 0 |
| ctx6144 | 42 | 0.557 | 0.629 | 0.813 | 0.697 | 20.1% | 0 |

label별 F1 (support, v5 → ctx4096, 3 seed 평균 ± sd):

| label | support | v5 | ctx4096 | 차이 |
|---|---:|---|---|---|
| public | 19 | 0.894 ± 0.063 | 0.691 ± 0.084 | -0.203 |
| role_required | 111 | 0.818 ± 0.026 | 0.793 ± 0.007 | -0.025 |
| membership_required | 33 | 0.589 ± 0.048 | 0.562 ± 0.029 | -0.027 |
| owner_match | 34 | 0.760 ± 0.024 | 0.743 ± 0.033 | -0.017 |
| owner_or_admin | 21 | 0.536 ± 0.031 | 0.421 ± 0.128 | -0.115 |
| manual_review_required | 65 | 0.499 ± 0.027 | 0.427 ± 0.039 | -0.072 |

프로젝트별 정확도:

| 프로젝트 | n | v5 | ctx4096 | 차이 |
|---|---:|---|---|---|
| Ghost | 69 | 0.758 ± 0.008 | 0.710 ± 0.038 | -0.048 |
| Rocket.Chat | 157 | 0.656 ± 0.013 | 0.654 ± 0.004 | -0.002 |
| Umami | 57 | 0.708 ± 0.066 | 0.573 ± 0.036 | -0.134 |

입력: 블록이 붙은 건 226/283, 예산 절단(cut) 88건, 블록 종류 {'perm_table': 277, 'helper': 156, 'permissible': 25, 'perm_flow': 80}, 프로젝트별 블록 포함 Ghost 65/69, Rocket.Chat 116/157, Umami 45/57.

블록 유무별 정확도·manual 비율 (3 seed):

| 구간 | n | v5 정확도 | ctx 정확도 | v5 manual | ctx manual |
|---|---:|---|---|---|---|
| with_blocks | 226 | 0.693 ± 0.018 | 0.639 ± 0.003 | 17.3% ± 1.6% | 16.4% ± 4.4% |
| no_blocks | 57 | 0.684 ± 0.046 | 0.702 ± 0.030 | 14.0% ± 1.8% | 17.0% ± 3.6% |

- 예측이 바뀐 건(v5 → ctx, seed별): s42 51, s43 52, s44 63. 고쳐진/새로 틀린(seed별): s42 +13/−26, s43 +16/−25, s44 +22/−34. 3 seed 모두 고쳐진 4건, 3 seed 모두 새로 틀린 9건(목록 fixed_newly_wrong.md).
- 전이 상위(v5 예측 → ctx 예측, 3 seed 합산): manual_review_required→role_required 33, owner_or_admin→role_required 28, membership_required→role_required 23, membership_required→manual_review_required 16, public→manual_review_required 15, owner_match→membership_required 10, manual_review_required→membership_required 7, owner_match→role_required 6.

## 5. test_v30 oas_code 합성 제외 207건 (회귀 확인)

| 모델 | seeds | macro-F1 | 정확도 | 구체 정밀도 | 구체 재현율 | manual 비율 | 출력 오류 | public 오판 /35 |
|---|---|---|---|---|---|---|---|---|
| v5 | 42,43,44 | 0.374 ± 0.010 | 0.568 ± 0.010 | 0.796 ± 0.025 | 0.566 ± 0.010 | 28.2% ± 2.3% | 4 / 0 / 2 | 3 / 2 / 1 |
| ctx4096 | 42,43,44 | 0.359 ± 0.023 | 0.525 ± 0.053 | 0.812 ± 0.035 | 0.523 ± 0.053 | 34.9% ± 8.7% | 2 / 1 / 2 | 3 / 3 / 1 |
| ctx6144 | 42 | 0.354 | 0.551 | 0.779 | 0.548 | 29.0% | 2 | 3 |

label별 F1 (support, v5 → ctx4096, 3 seed 평균 ± sd):

| label | support | v5 | ctx4096 | 차이 |
|---|---:|---|---|---|
| public | 58 | 0.644 ± 0.047 | 0.655 ± 0.044 | +0.010 |
| role_required | 39 | 0.442 ± 0.030 | 0.399 ± 0.070 | -0.042 |
| owner_match | 106 | 0.752 ± 0.018 | 0.711 ± 0.041 | -0.041 |
| owner_or_admin | 3 | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 |
| manual_review_required | 1 | 0.034 ± 0.003 | 0.028 ± 0.006 | -0.006 |

프로젝트별 정확도:

| 프로젝트 | n | v5 | ctx4096 | 차이 |
|---|---:|---|---|---|
| DVWS-node | 25 | 0.533 ± 0.061 | 0.467 ± 0.061 | -0.067 |
| Pixi | 48 | 0.562 ± 0.000 | 0.542 ± 0.062 | -0.021 |
| VAmPI | 12 | 0.917 ± 0.000 | 0.917 ± 0.000 | +0.000 |
| crAPI | 53 | 0.679 ± 0.019 | 0.604 ± 0.098 | -0.075 |
| juice-shop | 69 | 0.440 ± 0.017 | 0.406 ± 0.029 | -0.034 |

입력: 블록이 붙은 건 13/207, 예산 절단(cut) 0건, 블록 종류 {'helper': 14}, 프로젝트별 블록 포함 DVWS-node 0/25, Pixi 0/48, VAmPI 0/12, crAPI 1/53, juice-shop 12/69.

블록 유무별 정확도·manual 비율 (3 seed):

| 구간 | n | v5 정확도 | ctx 정확도 | v5 manual | ctx manual |
|---|---:|---|---|---|---|
| with_blocks | 13 | 0.205 ± 0.044 | 0.154 ± 0.000 | 71.8% ± 4.4% | 74.4% ± 11.8% |
| no_blocks | 194 | 0.593 ± 0.009 | 0.550 ± 0.057 | 25.3% ± 2.7% | 32.3% ± 8.6% |

- 예측이 바뀐 건(v5 → ctx, seed별): s42 23, s43 19, s44 38. 고쳐진/새로 틀린(seed별): s42 +5/−7, s43 +3/−7, s44 +2/−23. 3 seed 모두 고쳐진 0건, 3 seed 모두 새로 틀린 0건(목록 fixed_newly_wrong.md).
- 전이 상위(v5 예측 → ctx 예측, 3 seed 합산): owner_match→manual_review_required 37, membership_required→manual_review_required 6, manual_review_required→public 6, role_required→manual_review_required 5, public→manual_review_required 5, manual_review_required→owner_match 3, output_error→owner_match 3, owner_match→output_error 3.

## 6. 해석

- test_v5에서 하락은 블록이 붙은 226건에 집중된다(블록 없는 57건은 표식만 추가되어 정확도가 오히려 약간 올랐다; 위 블록 유무별 표). 전이는 구체 label 사이 이동과 구체→manual이 섞여 있어 블록이 '근거 추가'보다 '판단 흔들기'로 작용했다.
- **권한표 블록의 role_required 편향**: v5→ctx 전이 중 role_required로 간 94건(3 seed 합산) 가운데 92건이 perm_table 블록(Rocket.Chat permission→roles 행, Ghost rolePermissions, Umami ROLE_PERMISSIONS)을 포함한 레코드다(perm_table 포함 레코드 207/283). 새로 틀린 건도 perm_table 포함 62 vs 미포함 23. 정답이 owner_or_admin·manual(설정·가시성 분기)·membership인 핸들러에 역할 목록이 보이자 모델이 role_required로 기울었다(3 seed 일관 새로 틀린 9건 중 Rocket.Chat hasPermission 3건·Umami ROLES 1건이 이 유형). 반대로 public 19건은 블록(Ghost tokenPermissionCheck·authentication 권한표)이 붙자 manual로 물러났다(public F1 0.894 → 0.691). 3 seed 일관 고쳐진 4건은 모두 Rocket.Chat roomAccessValidators(canAccessRoom 분기) 블록 건으로, 방 접근 분기를 보여주면 manual/membership 구분이 나아진다는 신호는 있다.
- 모델이 블록을 활용하지 못한 원인 후보: (1) 학습 입력에 없던 형식(분포 밖), (2) 핸들러 본문 뒤에 붙은 권한표·헬퍼가 rationale의 "description/path_params" 근거 선택을 흐트러뜨림, (3) 예산 절단으로 핸들러 뒤 블록이 잘린 건(cut)의 불완전한 문맥. 어느 것이 주원인인지는 이 실험으로 가릴 수 없다(학습 없는 문맥 효과 분리 실험).
- test_v30 207에서는 블록이 13건뿐인데도 s44 manual 비율이 30.0% → 44.9%로 뛰었다. 표식 한 줄(`[관련 권한 코드] (없음)`)만으로도 seed에 따라 보류가 늘 수 있어, 입력 형식 변경은 학습과 함께 가야 한다.

## 7. 한계

- 문맥 없는 v5 기준 수치는 재추론하지 않고 기존 기록(reports/eval/lora_v5, unsloth 로더)을 썼다. 로더 차이는 기준선 재현 20/20으로만 확인했다.
- test_v30 207은 블록 13건이라 문맥 효과가 아니라 표식 회귀 확인이다. 채택 기준의 test_v30 조건은 이 한계 안에서 적용했다.
- ctx6144는 seed 42·test_v5·test_v30만 실행했다(사전 규칙).
- 정적 분석기의 정밀도(stop12_precision.md: 30건 분류)는 바뀌지 않았으며, 블록의 "직접 근거" 비율 자체가 낮은 레코드가 남아 있다.
- S4 산출물은 커밋하지 않았다(사용자 지시). 주지표·발표 수치는 불변.

## 8. 파일

- `test_v5|v5|s42`: reports/eval/lora_v5/lora_v5_s42/eval/v5test_predictions_oas_code_lora_v5_s42_final.jsonl (283행, SHA-256 `7d5879b5a7ab…`)
- `test_v5|v5|s43`: reports/eval/lora_v5/lora_v5_s43/eval/v5test_predictions_oas_code_lora_v5_s43_final.jsonl (283행, SHA-256 `1e8737d32947…`)
- `test_v5|v5|s44`: reports/eval/lora_v5/lora_v5_s44/eval/v5test_predictions_oas_code_lora_v5_s44_final.jsonl (283행, SHA-256 `69e32931dbfa…`)
- `test_v5|ctx4096|s42`: reports/eval/context_aug_v5/pod_results/pred_test_v5_ctx4096_s42.jsonl (283행, SHA-256 `68eeb88c17d9…`)
- `test_v5|ctx4096|s43`: reports/eval/context_aug_v5/pod_results/pred_test_v5_ctx4096_s43.jsonl (283행, SHA-256 `349c6656baad…`)
- `test_v5|ctx4096|s44`: reports/eval/context_aug_v5/pod_results/pred_test_v5_ctx4096_s44.jsonl (283행, SHA-256 `de098fdd10bd…`)
- `test_v5|ctx6144|s42`: reports/eval/context_aug_v5/pod_results/pred_test_v5_ctx6144_s42.jsonl (283행, SHA-256 `073695619f73…`)
- `test_v30|v5|s42`: reports/eval/lora_v5/lora_v5_s42/eval/predictions_oas_code_lora_v5_s42_final.jsonl (265행, SHA-256 `2121253538e4…`)
- `test_v30|v5|s43`: reports/eval/lora_v5/lora_v5_s43/eval/predictions_oas_code_lora_v5_s43_final.jsonl (265행, SHA-256 `202326dac652…`)
- `test_v30|v5|s44`: reports/eval/lora_v5/lora_v5_s44/eval/predictions_oas_code_lora_v5_s44_final.jsonl (265행, SHA-256 `534e15cade68…`)
- `test_v30|ctx4096|s42`: reports/eval/context_aug_v5/pod_results/pred_test_v30_ctx4096_s42.jsonl (265행, SHA-256 `1a566881889a…`)
- `test_v30|ctx4096|s43`: reports/eval/context_aug_v5/pod_results/pred_test_v30_ctx4096_s43.jsonl (265행, SHA-256 `8a5c83e111a7…`)
- `test_v30|ctx4096|s44`: reports/eval/context_aug_v5/pod_results/pred_test_v30_ctx4096_s44.jsonl (265행, SHA-256 `46b870fffe64…`)
- `test_v30|ctx6144|s42`: reports/eval/context_aug_v5/pod_results/pred_test_v30_ctx6144_s42.jsonl (265행, SHA-256 `00198201e21b…`)
- 분석: reports/eval/context_aug_v5/analysis.json, fixed_newly_wrong.md (scripts/analyze_context_aug_v5.py)
- 입력 통계: test_v5_ctx4096_stats.json 등, appendix_test_v30_inputs.md, stop12_precision.md
