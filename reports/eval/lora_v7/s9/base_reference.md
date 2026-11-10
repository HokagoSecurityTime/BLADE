# S9-base — 베이스 모델 참고 수치 (2026-11-09 추론, 2026-11-10 채점; 채택 판정과 무관, 커밋 없음)

사전 기록 AGENTS.md "S9-base". S9 판정(v5 vs v7, 채택 확정) 이후에 돌린 **참고용** 추론이며 판정·채택에 영향이 없다.

## 설정

- 모델: unsloth/Qwen2.5-7B-Instruct-bnb-4bit, **어댑터 없음**(zero-shot). 프롬프트 v3.0.1, greedy, max_new_tokens 256, eval_batch 8 — S9와 같은 디코딩. 단일 run(학습 없는 모델이라 seed 반복 불필요, `--data base --seed 0 --eval-only --jobs v6test`).
- Pod 49dkegbotxusbe(H100 80GB, 볼륨 /workspace), torch 2.13.0+cu129·transformers 5.17.0·trl 1.15.0·peft 0.21.2·unsloth 2026.11.3 — **S9 여섯 run과 같은 라이브러리 버전**(env.json 일치). 게이트: data_v7_hashes·test_v6 manifest `a9ca4fca…` 통과, `no adapter: base model … zero-shot` 로그, BLADE_TESTV6_STAGE=S9. 2026-11-09 15:29–15:42 UTC(setup 1분, oas 3.5분, oas_code 7분), 자동 정지. 회수 tar SHA-256 `938ee76d088797b1ca0d95f6fd9f0a68781b7855d4b42d140837d0a21dd36e61`.
- 스크립트: runpod/run_train_v7.py DATASETS `base`(no_adapter), runpod/run_s9_base.sh. 채점 scripts/eval_test_v6.py(base + v5 3 + v7 3 재채점; v5·v7 항목은 S9 채점과 바이트 동일 확인) → s9/scores_test_v6.json, eval_test_v6.md.

## test_v6 289 — oas_code

| 모델 | macro-F1 | 정확도 | 구체 정밀도 | 구체 재현율 | 구체 응답률 | manual 비율 | public 오판(/265) | 출력 오류 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Base (단일 run) | 0.214 | 0.304 | 0.425 | 0.371 | 0.873 | 0.0% | 36 | 37 |
| LoRA v5 (3 seed) | 0.586 ± 0.006 | 0.606 ± 0.006 | 0.688 ± 0.012 | 0.629 ± 0.008 | - | 15.8 ± 2.9% | 1.0 ± 0.0 | 0 / 1 / 1 |
| LoRA v7 (3 seed) | 0.650 ± 0.016 | 0.661 ± 0.012 | 0.758 ± 0.038 | 0.682 ± 0.024 | - | 18.1 ± 2.9% | 0.3 ± 0.6 | 1 / 0 / 1 |

- Base 예측 분포: role_required 173 · public 59 · output_error 37 · owner_match 15 · membership 3 · owner_or_admin 2 · tenant 0 · manual 0. 보류를 한 번도 내지 않고(manual 0) public 59 중 36이 security 선언 엔드포인트의 오판이다. label F1: public 0.500 · role 0.445 · owner 0.297 · membership 0.150 · owner_or_admin 0.105 · tenant 0 · manual 0.
- 프로젝트별 정확도 Base: seahub 0.380 · Redash 0.083 · GlitchTip 0.243 · Penpot 0.545. 정답 출처별: human 0.20(5) · ai_double 0.239(67) · ai_single 0.327(217). Redash G1-b 18건: role_required 18(0/18, v5·v7과 동일).
- oas(명세만) 보조: Base macro-F1 0.039 · 정확도 0.062 · 출력 오류 142/289(JSON 형식 불이행) · public 오판 125/265. 명세만으로는 베이스가 사실상 동작하지 않는다.
- test_v30 207(기존 base_qwen_runpod 예측 재채점, 추론 없음): 정확도 0.319 · macro-F1 0.197 · 구체 정밀도 0.353 · 재현율 0.316 · manual 6.8% · public 오판 17/35 · 출력 오류 9(reports/eval/lora_v5/scores_test_v30.json).

## 발표 표 반영

presentation_numbers_v7.md를 test_v6 하나, Base vs BLADE LoRA(v7), 지표 4개(macro-F1·정확도·구체 정밀도·public 오판)로 재구성했다. v5 열·test_v30 표·test_v5/supp 참고값은 presentation_numbers_v7.json에 보존.
