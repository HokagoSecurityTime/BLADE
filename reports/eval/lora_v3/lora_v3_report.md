# LoRA v3 결과 (data-v3a / data-v3b, RunPod, 2026-10-27)

평가: test_v30(불변), eval-def v2(scripts/eval_v30.py). final 어댑터만 평가했고 체크포인트 선택·문턱 조정은 하지 않았다(AGENTS.md data-v3 실험 규칙). 원자료: scores.json, eval_v30.md(라벨별 표). 비교용 Colab LoRA v2 s42·43·44 final과 베이스(base_v301)도 같은 스크립트로 다시 채점했다.

## 0. 실행 확인

- 7 run 모두 정상 종료(run_all.log, 각 run의 logs/run.log). 학습 loss 0.206~0.228, val loss 발산 없음.
- 환경: A100-SXM4-80GB, torch 2.14.1+cu130, transformers 5.17.0, trl 1.15.0, peft 0.21.2, unsloth 2026.10.9. 하이퍼파라미터는 LoRA v2와 같다(config.json).
- export의 data_v2·data_v3·runpod 파일은 로컬 동결본과 바이트 동일. 압축 파일 SHA256SUMS 일치.
- oas_code는 265행이다. LoRA v2·베이스와 같은 입력 파일(test_v30_inputs.jsonl)이라 채점 대상이 같다.
- run_all.log 마지막 줄 "pod stop skipped by shim": runpodctl 정지가 실행되지 않았다. Pod 정지 여부는 RunPod 콘솔에서 확인해야 한다.

## 1. 주지표 — oas_code, 합성 제외 207건 (seed 평균 ± 표준편차)

| 모델 | n | macro-F1 | 구체 정밀도 | 구체 재현율 | manual 비율 | public 오판(신) | 출력 오류(3 seed 합) |
|---|---:|---:|---:|---:|---:|---:|---:|
| base_v301 | 1 | 0.196 | 0.349 | 0.316 | 6.8% | 18/47 | 11 |
| LoRA v2 (Colab) | 3 | 0.284 ± 0.022 | 0.706 ± 0.028 | 0.382 ± 0.050 | 45.6% ± 7.8 | 1 | 3 |
| LoRA v2 s42 (RunPod 기준점) | 1 | 0.337 | 0.748 | 0.476 | 36.2% | 2/47 | 1 |
| **v3a** (쿼터 25%) | 3 | 0.315 ± 0.016 | 0.633 ± 0.086 | 0.458 ± 0.020 | 25.1% ± 6.7 | 0 | 15 |
| **v3b** (쿼터 10%) | 3 | 0.338 ± 0.017 | 0.643 ± 0.028 | 0.519 ± 0.046 | 18.4% ± 6.3 | 0 | 9 |

macro-F1은 support가 있는 5종(public 58, role 39, owner_match 106, owner_or_admin 3, manual 1) 평균이다. owner_or_admin·manual은 모든 모델이 F1 ≈ 0이라 절대값이 0.3대로 낮다.

## 2. oas 조건 — 주지표 중 합성 제외 102건(repository_spec)

| 모델 | macro-F1 | 구체 정밀도 | 구체 재현율 | manual 비율 |
|---|---:|---:|---:|---:|
| base_v301 | 0.290 | 0.448 | 0.294 | 8.8% |
| LoRA v2 (Colab) | 0.298 ± 0.019 | 0.723 | 0.203 | 71.2% |
| LoRA v2 s42 (RunPod) | 0.283 | 0.818 | 0.176 | 78.4% |
| v3a | 0.272 ± 0.056 | 0.783 | 0.170 | 78.4% |
| v3b | 0.403 ± 0.058 | 0.685 | 0.307 | 54.2% |

## 3. 판정 (실험 규칙: seed 표준편차보다 큰 차이만 인정)

1. **v3b > v3a.** oas_code macro-F1 차이 +0.023(표준편차 0.016·0.017), 재현율 +0.061, manual −6.7%p. oas 조건은 +0.131(표준편차 0.06)로 차이가 더 크다. 다만 seed 3개라 oas_code 차이는 경계선이다.
2. **data-v3가 data-v2보다 낫다고는 아직 말할 수 없다.** 같은 RunPod 환경 v2 s42가 0.337로 v3b 평균(0.338)과 같고 v3a(0.315)보다 높다. Colab v2 평균(0.284)과 비교하면 v3가 좋아 보이지만, v2 s42 하나만 놓고도 Colab 0.308 → RunPod 0.337(+0.029)이라 환경 차이가 seed 편차만큼 크다. v2 RunPod 기준점이 seed 1개뿐이어서 환경 효과와 데이터 효과를 분리할 수 없다.
3. **v3에서 나아진 것:** manual 감소(oas_code 36% → v3b 18%), owner_match F1 0.67 → 0.73, 신 정의 public 오판 0(6 run 모두 oas_code 0).
4. **v3에서 나빠진 것:** 구체 정밀도 0.748 → 0.64, public F1 0.54 → 0.45(v3a 0.40), 출력 오류 증가(v3a 15건, v3b 9건 / 3 seed).

## 4. 오류 유형 (oas_code 합성 제외, 3 seed 합)

| 정답 → 예측 | LoRA v2 (Colab) | v3a | v3b |
|---|---:|---:|---:|
| public → role_required | 14 | 35 | 46 |
| owner_match → membership_required | 12 | 43 | 34 |
| owner_match → manual | 130 | 46 | 32 |
| role_required → manual | 72 | 51 | 47 |

- v3는 manual로 미루던 건을 구체 label로 답하게 되었지만, 그중 일부가 엉뚱한 구체 label로 갔다.
- public → role_required는 crAPI가 대부분이다(v3b에서 2 seed 이상 반복 17건 중 10건). 예: GET /workshop/api/mechanic, GET /workshop/api/shop/products, 로그인·회원가입(POST /api/Users, /users/v1/login).
- owner_match → membership_required는 crAPI 차량 엔드포인트(/identity/api/v2/vehicle/...)에 몰려 있다.
- 위 목록은 test 오류 기술이며 학습·규칙 수정에 test를 쓰지 않는다.

## 5. 출력 오류와 학습 target의 검수 메타 문구

- 출력 오류는 길이 초과가 아니라 rationale 중간에 중국어로 넘어가거나 같은 JSON을 반복하는 경우다.
- 학습 target 일부에 검수 작업 메타 문구가 그대로 들어 있다. 예: `review_sheet_reviewed.xlsx sheet C: AUTH_ANY … 시트 A #22 …`, `판단: human_review_v2 기준으로 …`, `판단: R1_self_owner 기준으로 …`. train_sft_v3a 기준 review_sheet 34건, human_review_v2 39건, R1_self_owner 30건. data-v2에서 이어진 것이며 data-v3 정합성 점검(보류 표현만 검사)에서 걸러지지 않았다.
- test oas_code 출력에서 이 문구(human_review_v2 기준, review_sheet…xlsx, human_review_v2.9 같은 없는 버전명까지)가 v3 run마다 20~37건 나온다. LoRA v2는 0~1건.
- 이 문구가 나온 출력의 정확도는 41.5%(66/159)로, 없는 출력 51.3%(544/1061)보다 낮다(v3 6 run, 합성 제외).

## 6. 다음 단계 제안

1. **기준점 보강:** RunPod에서 data-v2 s43·s44를 추가로 돌려(약 1시간 10분) v2와 v3를 같은 환경 3 seed끼리 비교한다. 이것 없이는 "data-v3 효과"를 주장하기 어렵다.
2. **target 정리(data-v3.1 후보):** rationale에서 시트·규칙 ID·검수 버전 문구를 템플릿으로 바꾼다(label 불변, LLM 없이). 출력 오류와 엉뚱한 근거 문장을 줄이는 효과를 기대할 수 있다. data-v3는 동결이므로 새 버전으로 만든다.
3. **추론 측 형식 안정화:** 중국어 전환은 Qwen 계열의 알려진 현상이다. 생성 시 JSON 형식 제약(grammar)이나 CJK 토큰 억제를 쓰면 학습 없이 출력 오류를 줄일 수 있다. 다만 평가 조건이 바뀌므로 별도 조건으로 보고한다.
4. **본격 채택 후보는 v3b.** manual 쿼터 10%가 25%보다 낫다는 신호는 일관된다(oas·oas_code 모두).
