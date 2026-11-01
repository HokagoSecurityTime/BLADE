# LoRA v5 (data-v5) 평가 보고서 — test_v30 · test_v31_supp · test_v5 — 판정: 개선 인정(oas_code 조건, 사용자 확정 2026-10-31) · C-5 전환 9절 · 수용·마무리 10절

작업 C-4(AGENTS.md 작업 C). **발표 주 수치는 LoRA v5(3 seed)다**(사용자 결정 2026-10-31 "C-5 수용 및 마무리" 2항, 10절). 작업 C 기간 중에는 v4 원본이 주 수치였고 v5는 추가 실험이었으며, 그 규칙 아래 쓴 1~9절 문구는 기록으로 남긴다. 1단계(학습 + test_v30/test_v31_supp 평가, 2026-10-31 02:05–05:32 UTC)와 2단계(test_v5 예측, 07:39–08:39 UTC) 결과를 모두 담는다. 사전 고정 판정 기준(AGENTS.md 작업 C)은 3b절에서 적용했고 결과는 **개선 인정**(oas_code 조건)이다. 사용자가 2026-10-31에 oas_code 적용을 확정하고 C-5 전환을 승인했다(9절).

- 학습 데이터: data-v5(train_sft_v5 1,274 / val_sft_v5 179; data_v5_hashes.json `39c302c5…`, run.log에서 5개 입력 해시 검증 기록). 프롬프트 v3.0.1. 하이퍼파라미터·베이스 모델(unsloth/Qwen2.5-7B-Instruct-bnb-4bit)은 v4와 동일(config.json). seed 42·43·44, final 어댑터만 평가, 체크포인트 선택·문턱 조정 없음.
- 디코딩: 기본(greedy, repetition_penalty 없음, max_new_tokens 256). 작업 B 안정화 디코딩은 쓰지 않았다.
- 채점: test_v30은 scripts/eval_v30.py(eval-def v2) → scores_test_v30.json, eval_v30.md. test_v31_supp는 scripts/eval_v31_supp.py → scores_supp.json, eval_supp.md. test_v5는 scripts/eval_test_v5.py(manifest 해시 `57fd384f…` 검증) → scores_test_v5.json, eval_test_v5.md. base·v4 수치는 reports/eval/lora_v4의 기존 예측 파일을 같은 스크립트로 재채점한 것이며(재추론 없음, 사용자 결정 2026-10-31) v4 보고서 값과 일치한다. v2·v3b는 재추론·재채점하지 않았다.
- 판정 규칙: seed 3개 평균 ± 표본 표준편차. 차이가 표준편차보다 클 때만 우열을 인정한다.

## 1. 주지표 — test_v30 oas_code, 합성 제외 207건 (eval-def v2)

| 모델 | macro-F1(합성 제외 207) | macro-F1(합성 포함 265) | 구체 정밀도 | 구체 재현율 | 구체 응답률 | manual 비율(265) | public 오판(신, /35, 207 기준) | 출력 오류(seed별) |
|---|---:|---:|---:|---:|---:|---:|---|---|
| base | 0.197 | 0.654 | 0.353 | 0.316 | 0.893 | 9.8% | 17 | 11 |
| v4 | 0.356 ± 0.045 | 0.716 ± 0.022 | **0.811 ± 0.025** | 0.558 ± 0.065 | 0.688 ± 0.070 | 28.6 ± 4.4% | 1 / 0 / 0 | 7 / 7 / 0 |
| v5 | 0.374 ± 0.010 | 0.700 ± 0.009 | **0.796 ± 0.025** | 0.566 ± 0.010 | 0.712 ± 0.017 | 27.3 ± 1.8% | 3 / 2 / 1 | 5 / 4 / 3 |

label별 F1(합성 제외; support public 58 · role 39 · owner_match 106 · owner_or_admin 3 · manual 1):

| 모델 | public | role_required | owner_match | owner_or_admin | manual |
|---|---:|---:|---:|---:|---:|
| v4 | 0.512 ± 0.133 | 0.440 ± 0.066 | 0.798 ± 0.023 | 0.000 | 0.033 ± 0.006 |
| v5 | 0.644 ± 0.047 | 0.442 ± 0.030 | 0.752 ± 0.018 | 0.000 | 0.034 ± 0.003 |

seed별 구체 정밀도(207): v4 0.838 / 0.787 / 0.808, v5 0.767 / 0.809 / 0.811.

### 사전 기준 중 test_v30 절반의 판정

사전 기준: "test_v30 구체 정밀도(합성 제외 207건, v4 0.811 ± 0.025)가 v4보다 표준편차 이상 떨어지지 않을 것".

- v5 0.796 ± 0.025. 차이 −0.015로 v4 표준편차(0.025) 안이다. **이 절반은 충족**한다(떨어졌다고 볼 수 없음).
- 그 외 주지표는 모두 표준편차 안의 차이다: 합성 제외 macro-F1 +0.018(v4 sd 0.045), 재현율 +0.008, manual 비율 −1.3%p. v5는 seed 간 편차가 작다(macro-F1 sd 0.010, 정밀도 제외).
- label별로는 public F1이 오르고(0.512 → 0.644, v4 sd 0.133 안) owner_match F1이 내렸다(0.798 → 0.752, 차이 0.046 > v4 sd 0.023). owner_match 하락은 표준편차보다 큰 유일한 차이이며, 한계 절에 적는다.
- public 오판(신 정의)은 v4 1/0/0 → v5 3/2/1로 소폭 늘었다. 분모는 합성 제외 207건 기준 35건(declared ∧ 정답≠public)으로 통일했다(합성 58건에는 declared ∧ 정답≠public이 12건 있으나 두 모델 모두 그 안에서 오판 0이라 265 기준 /47과 건수가 같다). 건 목록은 8절.

## 2. 보조 조건 — test_v30 oas(명세만)

| 모델 | macro-F1(합성 제외 102) | macro-F1(주지표 160) | 구체 정밀도 | 구체 재현율 | manual 비율 | public 오판(신) | 출력 오류 |
|---|---:|---:|---:|---:|---:|---|---|
| base | 0.287 | 0.707 | 0.425 | 0.304 | 12.5% | 15 | 28 |
| v4 | 0.463 ± 0.016 | 0.700 ± 0.079 | 0.791 ± 0.046 | 0.379 ± 0.020 | 41.9 ± 2.9% | 0 / 1 / 0 | 0 / 0 / 8 |
| v5 | 0.462 ± 0.042 | 0.740 ± 0.016 | 0.824 ± 0.023 | 0.376 ± 0.054 | 43.1 ± 5.3% | 0 / 0 / 0 | 3 / 1 / 0 |

차이는 모두 표준편차 안이다.

## 3. 별도 조건 — test_v31_supp 222건 (eval_supp.md)

oas_code:

| 모델 | macro-F1 | 정확도 | manual 비율 | 출력 오류(합) |
|---|---:|---:|---:|---:|
| base | 0.048 | 0.099 | 0.000 | 67 |
| v4 | 0.448 ± 0.030 | 0.377 ± 0.016 | 0.233 ± 0.050 | 7 |
| v5 | 0.485 ± 0.026 | 0.419 ± 0.039 | 0.207 ± 0.055 | 2 |

label별 F1(oas_code; support public 2 · role 39 · membership 55 · tenant 55 · owner_match 21 · owner_or_admin 20 · manual 30):

| 모델 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual |
|---|---:|---:|---:|---:|---:|---:|---:|
| v4 | 0.933 ± 0.115 | 0.391 ± 0.038 | 0.531 ± 0.021 | 0.276 ± 0.099 | 0.507 ± 0.047 | 0.311 ± 0.006 | 0.188 ± 0.017 |
| v5 | 1.000 ± 0.000 | 0.491 ± 0.055 | 0.601 ± 0.089 | 0.235 ± 0.043 | 0.541 ± 0.072 | 0.328 ± 0.024 | 0.198 ± 0.052 |

- macro-F1 +0.037(v4 sd 0.030보다 큼), 정확도 +0.042(v4 sd 0.016보다 큼). role_required +0.100(sd 0.038보다 큼), membership_required +0.070(v5 sd 0.089 안). 나머지는 표준편차 안이다.
- 프로젝트별 정확도(oas_code): chatwoot 0.418 → 0.502 ± 0.072, chamilo 0.328 → 0.374, flowise 0.217 → 0.200, generic_university 0.746 → 0.810 ± 0.165. label이 프로젝트에 몰려 있어(membership→Chatwoot, tenant→Flowise, owner_or_admin→Chamilo) label별 표와 함께 본다.
- oas 조건: macro-F1 v4 0.210 ± 0.018 → v5 0.258 ± 0.057(v5 sd 안), 정확도 0.216 → 0.218.
- supp는 사전 판정 기준에 들어 있지 않다. 참고 지표다.

## 3b. 별도 조건 — test_v5 283건 (hold-out, eval_test_v5.md) · 사전 고정 기준 판정

test_v5(Rocket.Chat·Ghost·Umami, 사람 확정, 동결 2026-10-31 정지 지점 2)는 v5 예측 생성 전에 동결했고, 예측은 base 1회·v4 3 seed·v5 3 seed를 같은 Pod 실행에서 기본 디코딩으로 만들었다(run.log `test_v5 inputs verified against test_v5_manifest.json (57fd384f46e8)`). eval-def v2의 별도 조건이며 주지표는 바뀌지 않는다.

### oas_code (코드 입력, 283건)

| 모델 | macro-F1 | 정확도 | manual 비율 | 출력 오류(3 seed 합) |
|---|---:|---:|---:|---:|
| base (1회) | 0.238 | 0.382 | 0.000 | 35 |
| lora_v4 | 0.582 ± 0.016 | 0.585 ± 0.012 | 0.214 ± 0.011 | 9 |
| lora_v5 | **0.683 ± 0.016** | **0.691 ± 0.007** | 0.166 ± 0.016 | 3 |

label별 F1 (support): public(19) 0.751 → 0.894 · role_required(111) 0.696 → 0.818 · membership_required(33) 0.488 → 0.589 · owner_match(34) 0.721 → 0.760 · owner_or_admin(21) 0.394 → 0.536 · manual(65) 0.445 → 0.499. tenant_match는 support 0이라 정의되지 않는다. 프로젝트별 정확도: rocketchat 0.522 → 0.656, ghost 0.691 → 0.758, umami 0.632 → 0.708 (세 프로젝트 모두 상승, 표는 eval_test_v5.md).

### 판정 label seed별 값 (oas_code)

| run | owner_or_admin P / R / F1 | membership_required P / R / F1 |
|---|---|---|
| lora_v4_s42 | 0.379 / 0.524 / 0.440 | 0.407 / 0.667 / 0.506 |
| lora_v4_s43 | 0.357 / 0.476 / 0.408 | 0.355 / 0.667 / 0.463 |
| lora_v4_s44 | 0.333 / 0.333 / 0.333 | 0.404 / 0.636 / 0.494 |
| lora_v5_s42 | 0.500 / 0.619 / 0.553 | 0.453 / 0.727 / 0.558 |
| lora_v5_s43 | 0.400 / 0.667 / 0.500 | 0.519 / 0.848 / 0.644 |
| lora_v5_s44 | 0.455 / 0.714 / 0.556 | 0.489 / 0.667 / 0.564 |

정답 owner_or_admin 21건 × 3 seed = 63건의 예측 합: v4 = owner_or_admin 28 · role_required 19 · manual 10 · owner_match 4 · 출력 오류 2 / v5 = owner_or_admin 42 · role_required 14 · manual 5 · membership 2. 정답 membership_required 33 × 3 = 99건: v4 = membership 65 · owner_match 15 · manual 11 · owner_or_admin 6 · 오류 2 / v5 = membership 74 · owner_match 13 · manual 11 · owner_or_admin 1.

### 사전 고정 기준 적용 (AGENTS.md 작업 C, 작업 시작 전 기록)

| 조건 | v4 | v5 | 차이 | seed 표준편차(둘 중 큰 값) | 충족 |
|---|---:|---:|---:|---:|---|
| test_v5 owner_or_admin F1 상승 ≥ sd | 0.394 ± 0.055 | 0.536 ± 0.031 | +0.142 | 0.055 | 예 |
| test_v5 membership_required F1 상승 ≥ sd | 0.488 ± 0.022 | 0.589 ± 0.048 | +0.101 | 0.048 | 예 |
| test_v30 구체 정밀도(합성 제외 207) 하락 < sd | 0.811 ± 0.025 | 0.796 ± 0.025 | −0.015 | 0.025 | 예 |

세 조건을 모두 충족하므로 **개선 인정**이다. 판정은 사전 기준 그대로이며 문턱·체크포인트·조건 선택을 사후에 바꾸지 않았다.

주의 1 — 조건 명시: 사전 기준 문구는 입력 조건(oas/oas_code)을 적지 않았다. 여기서는 작업 C 이전의 모든 판정(data-v3 실험 규칙, v4 보고서)이 주지표로 쓰는 **oas_code 조건**에 적용했다. oas 조건(명세만)에서는 두 label이 v4·v5 모두 0 근처라(owner_or_admin 0.000 vs 0.056 ± 0.096, membership 0.149 ± 0.135 vs 0.090 ± 0.086) 차이를 인정할 수 없고 macro-F1도 같다(0.406 ± 0.027 vs 0.402 ± 0.021). 즉 개선은 코드 입력 조건에서만 확인됐다. 이 적용 방식은 사용자 확인 대상이다.

주의 2 — support: owner_or_admin 21건, membership_required 33건(Rocket.Chat 28)이라 F1 한 건 차이가 약 0.03이다. 차이(+0.142, +0.101)는 그보다 크지만, membership 결과는 Rocket.Chat 한 프로젝트의 방 구성원 검사 패턴에 크게 의존한다.

### oas (명세만, 283건)

| 모델 | macro-F1 | 정확도 | manual 비율 | 출력 오류(합) |
|---|---:|---:|---:|---:|
| base (1회) | 0.127 | 0.247 | 0.000 | 87 |
| lora_v4 | 0.406 ± 0.027 | 0.514 ± 0.025 | 0.270 ± 0.152 | 4 |
| lora_v5 | 0.402 ± 0.021 | 0.515 ± 0.023 | 0.263 ± 0.104 | 1 |

명세만으로는 v4·v5 차이가 없다(모든 label 차이가 sd 안). manual 비율의 sd가 크다(seed별 0.11~0.44).

## 4. 학습 기록

| run | steps | minutes | train_loss | val oas loss(final) | val oas_code loss(final) | 출력 오류 test_v30 oas / oas_code | supp oas / oas_code |
|---|---:|---:|---:|---:|---:|---|---|
| lora_v5_s42 | 480 | 56.2 | 0.1464 | 0.2425 | 0.1469 | 3 / 5 | 2 / 0 |
| lora_v5_s43 | 480 | 56.2 | 0.1500 | 0.2479 | 0.1447 | 1 / 4 | 0 / 1 |
| lora_v5_s44 | 480 | 56.1 | 0.1483 | 0.2535 | 0.1404 | 0 / 3 | 1 / 1 |

- loss 발산·형식 붕괴 없음(val은 정상 여부 확인용으로만 사용). 어댑터 SHA-256(adapter_model.safetensors): s42 `75ea08c194cb925556abcf4054f3236b8cea3c42e41eede31300ba443561b5d5`, s43 `af022125e8d4fbc76e3cd0227de0600cfafd7eec1bd21b5fc8d009acf5a82a77`, s44 `91aea71812e99684b55adb828a93c9ebb6976cb1df57e52ef39092f3c8161764`.
- 환경(env.json): A100-SXM4-80GB, torch 2.14.1+cu130, transformers 5.17.0, trl 1.15.0, peft 0.21.2, python 3.12.3. **환경 차이**: unsloth 2026.10.11(v4는 2026.10.9). setup.sh가 최신 unsloth를 받기 때문이며 그 외 버전은 같다.

### 실행 기록 (run_all.log, UTC)

1. Pod `tv1h7qd5afrpyr`: 02:05 `RUNS='v5:42 v5:43 v5:44'` 시작 → s42 ok 03:14 → s43 ok 04:23 → s44 ok 05:31 (항목당 약 69분 = 학습 56분 + 평가 13분, 총 3시간 27분) → GGUF 단계는 merge_gguf_v5.sh가 없어(사용자가 디스크 우려로 `.off`로 이름 변경) 즉시 실패 기록 후 계속 → 05:32 export 성공(blade_v5_results/adapters, SHA256SUMS) → Pod 자동 정지.
2. Pod `g0d739m5ennfoc`(같은 네트워크 볼륨): 06:17 2단계 명령(`…:v5test`)을 test_v5 미동결 상태에서 실행 → 7개 항목 모두 즉시 FAILED(`--jobs v5test but test_v5 is not frozen / not present (TESTV5)`). **TESTV5 게이트가 설계대로 작동했고 test_v5 예측 파일은 생성되지 않았다**(runs/*/eval에 v5test_* 없음, 이 export에도 없음). export는 lora_v4·base 디렉터리에 config/eval/logs가 없어 tar가 실패했고(export_results.sh의 경로 생성이 존재하지 않는 파일을 넘김) Pod 자동 정지.
3. 06:29 1단계 명령 재실행 → 세 run 모두 "이미 완료"로 18초 안에 건너뜀 → 같은 export 실패 → 자동 정지.
4. 수동 export: export_results.sh의 run별 경로를 `ls -d … 2>/dev/null`로 바꿔(로컬 저장소 동일 수정) `EXPORT_NAME=blade_v5 EXPORT_ADAPTERS=1`로 재실행. 내려받은 파일 해시가 SHA256SUMS_blade_v5와 일치: results `61cbb831b1f8dd53b3b8b5d18b3c0bba9a66b5af427ae1c67cf082812c1e0a7a`, adapters `db6abe46438b27795b51a12e875d24678932e5b3bcd3f50edb152275b294f983`(v4 3 seed + v5 3 seed 어댑터 포함).

5. 07:12 Pod `g0d739m5ennfoc` 재시작 후 2단계 명령을 `setup.sh` 없이 실행 → 7개 항목 모두 2초 안에 FAILED(`ModuleNotFoundError: No module named 'transformers'`; pip 패키지는 컨테이너에 있어 Pod 재시작 때 사라짐). 작업 지시(README 4.5절)에 setup.sh 재실행이 빠져 있던 것이 원인이며 README에 규칙을 추가했다. 예측 파일 없음.
6. 07:39 Pod `puuowjuwg8uw3e`(같은 볼륨, setup.sh 뒤): `RUNS='v5:42:v5test v5:43:v5test v5:44:v5test v4:42:v5test v4:43:v5test v4:44:v5test base:0:v5test' GGUF_SEED=42` → v5 s42 ok 07:48 · s43 ok 07:56 · s44 ok 08:04 · v4 s42 ok 08:12 · s43 ok 08:21 · s44 ok 08:29 · base ok 08:39(모델당 8~10분, base는 출력 오류가 많아 느림). **7개 run 모두 test_v5 manifest 해시 검증 통과 후 283건 × 2조건 예측 생성.**
7. 08:39 GGUF(merge_gguf_v5.sh 42): fp32 병합·fp16 체크포인트까지 성공, f16 GGUF 쓰기 39%(5.9/15.2GB)에서 **Network Volume 할당량 초과(Disk quota exceeded)**로 중단. 이어진 export도 같은 이유로 실패(SUMMARY.tsv 0바이트). 10:24 수동 재시도도 병합 저장 단계에서 같은 오류. 사용자 결정: GGUF는 만들지 않는다(5절).
8. 10:2x 수동 export: `rm -rf gguf_work_s42`(실패한 임시 산출물) 후 `EXPORT_NAME=blade_v5 EXPORT_ADAPTERS=0 bash runpod/export_results.sh` 성공. 내려받은 blade_v5_results.tar.gz SHA-256 `428e56f49b0af15064feab0ee23072f76372a7e76667e44503e2600037982ff1`(SUMMARY.tsv v5test 열: 출력 오류 base 87/35, v4 1/3·1/2·2/4, v5 0/1·1/0·0/2 = oas/oas_code).

run.log의 02:05 입력 검증 줄(`inputs verified against data_v5_hashes.json (5 files)`)로 학습 입력이 동결 data-v5와 같음을 확인했다.

## 5. GGUF (seed 42) — C-4 시점 미생성 (이후 C-5에서 컨테이너 디스크로 생성, 9절)

Pod에서 두 번(08:39, 10:24 UTC) 시도했으나 merge_gguf_v5.sh의 임시 파일(fp16 병합 체크포인트 15GB + f16 GGUF 15GB)이 Network Volume 할당량을 넘겨 `Disk quota exceeded`로 실패했다(1단계의 `.off` 건너뜀과는 별개). 로컬도 C: 여유 15GB라 불가. **사용자 결정(2026-10-31): GGUF는 만들지 않는다.** GGUF는 C-5 전환에만 필요하므로 판정과 무관하다. C-5가 승인되면 임시 디렉터리를 컨테이너 디스크(100GB 이상)로 돌려 별도로 만든다. s42 어댑터(SHA `75ea08c1…`)는 로컬 training/lora/runs/lora_v5_s42/adapter/에 있다.

## 6. 한계·주의

- test_v30 owner_match F1 하락(0.798 → 0.752)은 test_v30에서 표준편차보다 큰 유일한 하락이다. data-v5 보강분(Dendrite·NodeBB·Taiga)의 owner_match 76건(train)이 test_v30 취약 API의 owner_match와 다른 형태(본인 고정 처리·request.user 필터)인 것이 원인 후보다. test_v5에서는 owner_match가 오르고(0.721 → 0.760) 8절 혼동표에서 owner_match → owner_or_admin 오예측은 0이므로, 하락은 test_v30 취약 API 형태에 국한된 것으로 보이나 확정은 아니다.
- 합성 제외 macro-F1은 support 3(owner_or_admin)·1(manual) label이 2/5 비중이라 0.4 근처에 묶인다(v4 보고서와 같은 한계). 그래서 구체 정밀도·재현율과 label별 F1을 함께 본다.
- test_v5는 v5 예측 생성 전에 동결했다(06:17·07:12 시도는 예측을 만들지 못했고, 07:39 실행만 manifest 검증 후 예측을 만들었다). test_v5 한계: membership_required의 Rocket.Chat 편중 28/33, tenant_match 0건(F1 정의 불가), owner_or_admin support 21. 개선은 oas_code 조건에서만 확인됐고 oas 조건에서는 차이가 없다(3b절).
- 발표 주 수치는 작업 C 기간 중 v4 원본이었으나 2026-10-31 사용자 결정으로 LoRA v5로 전환했다(10절, reports/eval/lora_v5/presentation_numbers_v5.md).
- (사용자 요청 2026-10-31 추가) **배포 모델의 보류율이 평가 모델보다 낮다**: 발표 수치는 HF 어댑터(bf16) 3-seed 평가인데, 실제 배포되는 GGUF Q4_K_M(s42)은 test_v30 oas_code 265건에서 manual 보류 18.5%로 같은 어댑터 HF s42(25.3%)보다 6.8%p 낮다(equivalence_check.md; 행 일치 215/265, HF 보류·오류 → GGUF 구체 응답 23건). 구체 정밀도는 거의 같고(+0.014) 재현율·macro-F1은 오르지만, 운영에서는 평가 때보다 보류가 덜 걸려 구체 label로 집행되는 건이 늘고 그만큼 오판이 집행에 노출될 가능성도 커진다. 출력 오류는 5 → 9건이며 전부 파이프라인에서 보류 처리된다. 발표 때 "평가 수치 = HF, 배포 = GGUF(보류율 더 낮음)"를 함께 말한다.
- (사용자 요청 2026-10-31 추가) **test_v30 public 오판(신 정의, 합성 제외 207건, 분모 35)**: v4 1/0/0 → v5 3/2/1 (seed 42/43/44). 건별 id — v4 s42: d8c5cf5eb0bfbd488219; v5 s42: fc9dac901542ca88d688, 5a72ac6384c12b441687, d8c5cf5eb0bfbd488219; v5 s43: 0797f5bb072770d50159, fc9dac901542ca88d688; v5 s44: d8c5cf5eb0bfbd488219. 전부 crAPI identity·community 경로(정답 owner_match 3종, role_required 1종)이며 v5가 public을 더 자주 답하는 경향의 대가다(8절 목록·혼동표).
- (추가) **test_v30 owner_match F1 하락 0.798 → 0.752**: 8절 혼동표(합성 제외 207, 정답 owner_match 106건) 기준 owner_match → owner_or_admin 오예측은 v4·v5 모든 seed에서 0건이고, owner_match → manual이 v4 20/23/16 → v5 23/30/22, owner_match → public이 v4 2/2/1 → v5 9/4/6으로 늘었다. 즉 하락은 보류 증가와 public 오판 증가에서 오며, test_v5에서는 owner_match F1이 오른다(0.721 → 0.760).
- (추가) **test_v5 membership_required 33건 중 28건이 Rocket.Chat**이다. membership F1 상승(+0.101)은 Rocket.Chat 방 구성원 검사 패턴에 크게 의존하므로 다른 프로젝트로 일반화됐다고 말할 수 없다. tenant_match는 test_v5에 0건이다.
- (추가) **test_v5 라벨링 방식**: AI(Claude)가 코드 발췌·경로·스키마로 1차 판정(초안)하고 사람이 검수 시트(review/test_v5_review_reviewed.xlsx, 담당자 열)에서 확인·확정했다. 초안 대비 변경 5건, 제외 13건(G8). 사람 확인의 범위(전수 확인인지 표본 확인인지)는 사용자가 별도로 알려주기로 했으며 확인되는 대로 이 항목을 갱신한다.
- supp의 label 편중(membership 50/55 Chatwoot, tenant 52/55 Flowise, owner_or_admin 19/20 Chamilo)은 v4 보고서와 같다.

## 8. 사후 분석 보완 (사용자 요청 2026-10-31, 판정 변경 없음)

사후 분석이다. 판정 기준·수치는 바꾸지 않는다. test_v30 oas_code, 합성 제외 207건, seed별.

분모 통일: 합성 제외 207건 중 declared ∧ 정답≠public = 35건.

| 모델/seed | public 오판(신, /35) | 정답 owner_match → 예측 owner_or_admin | 정답 owner_match → 예측 manual | 정답 owner_match → 예측 public | 정답 owner_match → 예측 role |
|---|---:|---:|---:|---:|---:|
| v4 s42 | 1 | 0 | 20 | 2 | 1 |
| v4 s43 | 0 | 0 | 23 | 2 | 2 |
| v4 s44 | 0 | 0 | 16 | 1 | 4 |
| v5 s42 | 3 | 0 | 23 | 9 | 2 |
| v5 s43 | 2 | 0 | 30 | 4 | 2 |
| v5 s44 | 1 | 0 | 22 | 6 | 1 |

혼동표 v4 s42 (행 정답, 열 예측; 합성 제외 207)

| 정답 \ 예측 | pub | role | memb | ten | own | own_adm | manual | err | n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pub | 26 | 2 | 2 | 0 | 11 | 0 | 15 | 2 | 58 |
| role | 3 | 13 | 0 | 0 | 1 | 0 | 21 | 1 | 39 |
| own | 2 | 1 | 1 | 0 | 80 | 0 | 20 | 2 | 106 |
| own_adm | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 3 |
| manual | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |

혼동표 v4 s43 (행 정답, 열 예측; 합성 제외 207)

| 정답 \ 예측 | pub | role | memb | ten | own | own_adm | manual | err | n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pub | 14 | 4 | 0 | 0 | 13 | 0 | 24 | 3 | 58 |
| role | 4 | 10 | 0 | 0 | 2 | 0 | 23 | 0 | 39 |
| own | 2 | 2 | 0 | 0 | 76 | 0 | 23 | 3 | 106 |
| own_adm | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 3 |
| manual | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |

혼동표 v4 s44 (행 정답, 열 예측; 합성 제외 207)

| 정답 \ 예측 | pub | role | memb | ten | own | own_adm | manual | err | n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pub | 27 | 1 | 0 | 0 | 16 | 0 | 14 | 0 | 58 |
| role | 5 | 14 | 1 | 0 | 2 | 0 | 17 | 0 | 39 |
| own | 1 | 4 | 0 | 0 | 85 | 0 | 16 | 0 | 106 |
| own_adm | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 3 |
| manual | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |

혼동표 v5 s42 (행 정답, 열 예측; 합성 제외 207)

| 정답 \ 예측 | pub | role | memb | ten | own | own_adm | manual | err | n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pub | 36 | 2 | 2 | 0 | 9 | 0 | 9 | 0 | 58 |
| role | 9 | 11 | 1 | 0 | 0 | 0 | 17 | 1 | 39 |
| own | 9 | 2 | 1 | 0 | 68 | 0 | 23 | 3 | 106 |
| own_adm | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 3 |
| manual | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |

혼동표 v5 s43 (행 정답, 열 예측; 합성 제외 207)

| 정답 \ 예측 | pub | role | memb | ten | own | own_adm | manual | err | n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pub | 36 | 2 | 0 | 0 | 12 | 0 | 8 | 0 | 58 |
| role | 6 | 13 | 1 | 0 | 1 | 0 | 18 | 0 | 39 |
| own | 4 | 2 | 0 | 0 | 70 | 0 | 30 | 0 | 106 |
| own_adm | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 3 |
| manual | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |

혼동표 v5 s44 (행 정답, 열 예측; 합성 제외 207)

| 정답 \ 예측 | pub | role | memb | ten | own | own_adm | manual | err | n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pub | 29 | 1 | 2 | 0 | 12 | 0 | 14 | 0 | 58 |
| role | 4 | 12 | 0 | 0 | 1 | 0 | 22 | 0 | 39 |
| own | 6 | 1 | 0 | 0 | 75 | 0 | 22 | 2 | 106 |
| own_adm | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 3 |
| manual | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |

v5 public 오판 건 목록(신 정의; declared ∧ 예측 public ∧ 정답≠public, 207건 기준):

| id | 정답 label | seed | service | method path |
|---|---|---|---|---|
| 0797f5bb072770d50159 | role_required | s43 | crAPI | POST /community/api/v2/coupon/new-coupon |
| 5a72ac6384c12b441687 | owner_match | s42 | crAPI | POST /identity/api/v2/user/verify-email-token |
| d8c5cf5eb0bfbd488219 | owner_match | s42 | crAPI | POST /identity/api/v2/vehicle/resend_email |
| d8c5cf5eb0bfbd488219 | owner_match | s44 | crAPI | POST /identity/api/v2/vehicle/resend_email |
| fc9dac901542ca88d688 | owner_match | s42 | crAPI | POST /identity/api/v2/user/reset-password |
| fc9dac901542ca88d688 | owner_match | s43 | crAPI | POST /identity/api/v2/user/reset-password |

관찰:
- 정답 owner_match → 예측 owner_or_admin은 v4·v5 모든 seed에서 **0건**이다. owner_match F1 하락은 owner_or_admin으로의 혼동이 아니라 **owner_match → public**(v4 2/2/1 → v5 9/4/6)과 **owner_match → manual**(v4 20/23/16 → v5 23/30/22)이 늘어난 결과다.
- v5의 public 오판 6건(중복 id 제외 4건)은 전부 crAPI의 identity·community 경로이며 정답은 owner_match 3건·role_required 1건이다. v4 s42의 오판 1건과 같은 계열(crAPI)이다.
- public 재현율은 v5가 높다(정답 public 58건 중 예측 public v4 26/14/27 → v5 36/36/29). 즉 v5는 public을 더 자주 답하며, 그 대가가 owner_match → public 오판이다.

## 7. 산출물

- reports/eval/lora_v5/: lora_v5_s42·43·44(config.json, env.json, logs/, eval/ 예측 — supp_predictions_*는 .gitignore), lora_v4_s42·43·44 및 base_qwen_runpod(eval/v5test_predictions_* + logs/run.log만; test_v30·supp 예측은 reports/eval/lora_v4에 있음), run_all.log·SUMMARY.tsv(2단계 export본), SHA256SUMS_blade_v5(1·2단계 두 export 해시), scores_test_v30.json, eval_v30.md, scores_supp.json, eval_supp.md, scores_test_v5.json, eval_test_v5.md, 이 보고서.
- test_v5 예측 파일 SHA-256(oas_code / oas): v5 s42 `7d5879b5…` / `d1f5ee37…`, s43 `1e8737d3…` / `6d0f5a89…`, s44 `69e32931…` / `e414e716…`; v4 s42 `af58f78d…` / `d91ac362…`, s43 `c7f05abf…` / `55a30b5d…`, s44 `49309c70…` / `6a9d114f…`; base `b6e0c542…` / `b03fa120…`.
- 어댑터: training/lora/runs/lora_v5_s4{2,3,4}/adapter/(.gitignore). 원본 archive `<USERPROFILE>\Downloads\export_v5_pahse1\export\`.
- 판정: 개선 인정(3b절). C-5 전환은 9절, 수용·커밋은 10절(태그는 없음).
- (10절 추가) scores_combined_712.json·eval_combined_712.md(scripts/eval_combined_v5.py), presentation_numbers_v5.{md,json}(scripts/presentation_numbers_v5.py).

## 9. C-5 전환 (사용자 승인 2026-10-31; 커밋은 10절)

| 단계 | 결과 | 근거 |
|---|---|---|
| a. s42 GGUF Q4_K_M | RunPod 컨테이너 디스크에서 병합·변환(11:27–12:10 UTC; 양자화는 RAM 20GB Pod에서 한 번 죽어 f16 해시 확인 후 재개). Q4_K_M SHA `2935029694…`, 4,683,073,504 bytes | reports/eval/lora_v5_gguf/merge_manifest_v5_s42.json, SHA256SUMS_gguf_s42, merge.log, quantize.log |
| b. 변환 동등성 (test_v30 oas_code, HF s42 final 대비) | macro-F1 합성 제외 +0.034(허용 0.045), 합성 제외 구체 정밀도 +0.014(0.026), 265 정밀도 +0.007(0.018) — v4 때 규칙(v4 3-seed sd) 안. 보류 25.3% → 18.5%, 행 일치 215/265. **수용 확정(사용자 2026-10-31, 사전 지정 v4 허용 폭 기준; v5 자체 sd로 읽으면 macro-F1은 상승 방향으로 이탈 — 병기 유지)** | reports/eval/lora_v5_gguf/equivalence_check.md, equivalence_numbers.json, scores_test_v30.json |
| c. MIN_CONFIDENCE (val_v5만) | choose_threshold_v4.py --rule precision → **0.9** (v4와 같음). val 구체 정밀도 0.703, manual 19.0% | reports/eval/lora_v5_gguf/threshold_val_v5.json |
| d. Ollama 등록 | blade-qwen-lora-v5 등록(GGUF를 blob 이름으로 두어 복사 없이 등록), blade-qwen-lora-v4·qwen2.5:7b 유지. 전환은 환경변수 BLADE_CLASSIFIER=lora, BLADE_LORA_MODEL=blade-qwen-lora-v5, BLADE_LORA_MIN_CONFIDENCE=0.9 (런타임 코드 수정 없음) | training/lora/README_serve_v5.md |
| e. 종단간 검증 · 전체 테스트 | pytest tests: **397 passed, 1 skipped** (38초). verify_lora_pipeline.py: 아래 "종단간 검증" 항목 | reports/eval/lora_v5_gguf/pipeline_compare.md |

- **종단간 검증(scripts/verify_lora_pipeline.py, demo_backend, 로컬 Ollama CPU)**: lora 경로(blade-qwen-lora-v5, MIN_CONFIDENCE 0.9) 7개 엔드포인트 중 6개가 의도 label과 일치(public, owner_match 2, owner_or_admin, role_required, tenant_match), GET /premium/content는 모델이 membership_required(0.9)를 냈으나 현재 런타임이 집행할 수 없어 규칙대로 manual_review_required로 보류(v4 때와 동일, AGENTS.md v2.9). owner_lookup(orders.id·users.id·orgs.id)과 roles(['admin'])도 추출됐다. 승인된 정책으로 프록시 요청 9건 전부 기대 상태 코드와 일치(BOLA 403·소유자 200·타 테넌트 403·비관리자 403·관리자 200·공개 200). llm 경로(qwen2.5:7b)는 5/7 일치(users → manual, premium → membership). 소요 lora 509.6초/7건(v4 482초), llm 592.3초. 결과 reports/eval/lora_v5_gguf/pipeline_compare.{md,json}.
- 첫 실행(pipeline_compare_noprovider.{md,json}로 보존)은 BLADE_LLM_PROVIDER를 안 넣어 2-b 파라미터 추출(roles)과 llm 경로가 실패했고, lora label 7건은 모두 의도와 일치했으나 roles가 없어 owner_or_admin·role_required 2건이 manual로 내려갔다. 환경변수를 넣고 재실행한 위 결과가 유효하다. 전환에 필요한 환경변수 전체: BLADE_CLASSIFIER=lora, BLADE_LORA_MODEL=blade-qwen-lora-v5, BLADE_LORA_MIN_CONFIDENCE=0.9, BLADE_LLM_PROVIDER=ollama, BLADE_LLM_MODEL=qwen2.5:7b(파라미터 추출용).
- 관찰: 첫 실행의 premium rationale에 중국어가 섞여 나왔다(GGUF Q4_K_M·CPU greedy 출력 드리프트). label·confidence 자체는 정상이었고 재실행에서는 재현되지 않았다. rationale 언어 드리프트는 집행에 영향이 없지만 한계로 기록한다.
- 발표용 수치 표(근거 경로 포함): reports/eval/lora_v5/presentation_numbers_v5.md (+ .json).
- Pod 실행 기록: c5.log — 11:19 첫 실행은 run_c5.sh가 BASE를 병합 스크립트에 넘기지 않아 즉시 실패(수정 후 재실행), 11:27 병합·f16 성공, 양자화 중단(RAM) → 12:07 quantize_resume_c5.sh → 12:13 Ollama 등록·템플릿 검사(토큰 수 3건 일치) → test_v30 265건(평균 3.0초/건, 출력 오류 9) → 12:28 val 179건.

## 10. C-5 수용·마무리 (사용자 결정 2026-10-31)

사용자 결정 "[결정] C-5 수용 및 마무리" 5항을 반영했다.

1. **변환 동등성 수용 확정**: 사전 지정대로 v4 허용 폭(v4 3-seed sd) 기준으로 수용. v5 폭 기준 해석(macro-F1 상승 방향 이탈)은 equivalence_check.md와 9절 b행에 병기 유지. 배포 모델 보류율 18.5% < 평가 모델 25.3%는 6절 한계에 추가.
2. **발표 주 수치를 LoRA v5로 전환**: presentation_numbers_v5.md를 다시 썼다(생성 scripts/presentation_numbers_v5.py, 모든 값 근거 경로 포함). a. test_v30 207 base/v4/v5(구체 정밀도·재현율·macro-F1·manual 비율·public 오판 /35), b. test_v5 283 base/v4/v5(macro-F1·정확도·manual 비율·owner_or_admin F1·membership F1·프로젝트별 정확도; macro-F1은 정답 support>0 label 6종 평균이고 tenant_match 정답 0건은 평균에서 빠짐), c. test_v31_supp 222 base/v4/v5(macro-F1 ± sd·정확도·manual 비율·public 오판 /191: base 15, v4 1/0/0, v5 seed별 값은 표), d. **manual 비율 불일치**: v4 test_v30 manual 비율 29.8 ± 5.6%(supplementary_metrics.md, presentation 표)는 합성 제외 207건 분모(seed별 29.0 / 35.8 / 24.6%), 28.6 ± 4.4%(lora_v4_report.md·이 보고서 1절 표 'manual 비율(265)')는 합성 포함 265건 분모(27.9 / 33.2 / 24.5%)다. 같은 예측 파일에서 scores_test_v30.json의 main_excl_synthetic vs main 값이며, 합성 58건이 세 seed 모두 manual 24.1%라 포함 시 평균이 내려간다. 둘 다 정확하고 발표 표는 주지표 조건(207)으로 통일했다. v5는 207 기준 28.2 ± 2.3%, 265 기준 27.3 ± 1.8%.
3. **세 셋 합산 712건 보조 지표**(scripts/eval_combined_v5.py → scores_combined_712.json, eval_combined_712.md; 7종 macro-F1, 구체 정밀도·재현율은 eval_v30.py concrete() 정의): base macro-F1 0.147 · 정확도 0.275 · 구체 정밀도 0.388 · 재현율 0.317; v4 0.469 ± 0.013 · 0.513 ± 0.019 · 0.698 ± 0.008 · 0.534 ± 0.020; **v5 0.521 ± 0.016 · 0.571 ± 0.013 · 0.744 ± 0.007 · 0.601 ± 0.017** (manual 비율 v4 24.4 ± 2.8% → v5 21.3 ± 2.3%). 네 지표 모두 v5가 v4보다 표준편차보다 큰 차이로 높다. 주지표(1절)는 바뀌지 않는다.
4. **커밋**: feat/lora-pipeline 브랜치에 data-v5·test_v5 manifest·보고서·스크립트를 나눠 커밋했다(태그 없음). 코드 본문 비공개 파일은 .gitignore 확인 — 커밋 전 점검에서 Flowise 코드가 든 training/lora/data_v5/test_v31_supp_inputs.jsonl이 ignore 목록에 빠져 있어 추가했다. 커밋 해시는 git log와 보고 메시지 참조.
5. **test_v5 사람 확인 범위**는 사용자가 별도로 전달하기로 했다(6절 라벨링 방식 항목은 전달 후 갱신).
