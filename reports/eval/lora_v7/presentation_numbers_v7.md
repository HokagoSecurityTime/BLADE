# 발표용 수치 표 — BLADE LoRA (LoRA v7, S9 채택 2026-11-09; 표 형식 2026-11-10)

hold-out **test_v6** 289건(seahub·Redash·GlitchTip·Penpot, 동결 2026-11-08, manifest `a9ca4fca05ee…`), 입력 조건 oas_code(OpenAPI 명세 + 핸들러 코드), 기본 디코딩(greedy, max_new_tokens 256), 프롬프트 v3.0.1. Base = unsloth/Qwen2.5-7B-Instruct-bnb-4bit 어댑터 없음(단일 run, S9-base 2026-11-09, 참고용). BLADE LoRA = LoRA v7(data-v7, QLoRA r16) 3 seed(42·43·44) 평균 ± 표본 표준편차. 두 모델 모두 같은 Pod·같은 라이브러리(torch 2.13.0+cu129·transformers 5.17.0·unsloth 2026.11.3)에서 추론. 수치는 presentation_numbers_v7.json에서 그대로 읽을 수 있다(생성 scripts/presentation_numbers_v7.py).

| 모델 | macro-F1 | 정확도 | 구체 정밀도 | public 오판 (/265) |
|---|---:|---:|---:|---:|
| Base (Qwen2.5-7B-Instruct, 미학습) | 0.214 | 0.304 | 0.425 | 36 |
| **BLADE LoRA (v7)** | **0.650 ± 0.016** | **0.661 ± 0.012** | **0.758 ± 0.038** | **0.3 ± 0.6** |

지표 정의: macro-F1 = support>0 label 7종의 F1 평균. 정확도 = label 일치율(289). 구체 정밀도 = 정답이 구체 label(manual 제외, 237건)인 건 중 구체 label로 답한 건의 정답률(보류·출력 오류 제외). public 오판 = security 선언이 있고 정답이 public이 아닌 265건 중 public으로 예측한 건수.

- 부가: manual 비율 Base 0.0% / BLADE 18.1 ± 2.9%, 구체 응답률 0.873 / 0.900 ± 0.033, 구체 재현율 0.371 / 0.682 ± 0.024, 출력 오류(JSON 파싱 실패) Base 37건 / BLADE 1 / 0 / 1건(seed별). Base는 보류(manual)를 한 번도 내지 않고 role_required 173·public 59로 답해 public 오판이 많다.
- 근거: reports/eval/lora_v7/s9/scores_test_v6.json(condition oas_code; group base_qwen7b·lora_v7), eval_test_v6.md, report.md(S9 판정), base_qwen7b_s9/(S9-base run). 예측 s9/base_qwen7b_s9/eval/v6test_predictions_oas_code_base_qwen7b_s9.jsonl, s9/lora_v7_s4*/eval/v6test_predictions_oas_code_*.jsonl. 채점기 scripts/eval_test_v6.py. 정답 test_v6.jsonl(SHA 87267595…).
- 채택 근거(사전 등록 기준, 비교 기준 v5 → v7): (1) test_v6 macro-F1 +0.064 ≥ 0.016, (2) test_v30 207 구체 정밀도 +0.028(하락 ≤ 0.025), (3) test_v30 207 public 오판 평균 1.33 ≤ 2.0. v5 수치와 test_v30 표는 이 파일의 json(`test_v6_289.v5`, `test_v30_207`)에 보존하며 발표 표에는 넣지 않는다.

## 정답 출처 한계 (발표에 함께 명시)

- test_v6 라벨은 A안(2026-11-08, 마감 사유): AI(Claude) 1차 확정 + 독립 AI 2차 검수(블라인드 감사 41건 일치 38 = 92.7%, **AI 간 일치율**) + 불일치·저확신 건만 사람 확정. 289건 중 사람 확정 5(1.7%), AI 이중 확정 67(23.2%), AI 단독 217(75.1%). 사람 대비 정확도는 측정되지 않았다. Base·BLADE 비교는 같은 정답·입력·환경이므로 상대 비교는 유효하나 절대 수치에는 정답 오류가 포함된다.
- 정답 출처별 정확도(Base / BLADE): human_confirmed(5) 0.200 / 0.533 ± 0.115, ai_double_confirmed(67) 0.239 / 0.493 ± 0.015, ai_single(217) 0.327 / 0.716 ± 0.015.
- label 편중: tenant_match 38 중 Redash 27, membership_required 37 중 GlitchTip 27, owner_or_admin 17 중 Redash 13. Redash G1-b 경계 18건은 Base·v5·v7 모두 0/18(role_required 예측). 프로젝트별 정확도(Base / BLADE): seahub 0.380 / 0.746 ± 0.017, redash 0.083 / 0.588 ± 0.021, glitchtip 0.243 / 0.686 ± 0.000, penpot 0.545 / 0.582 ± 0.031.
- label별 F1(Base / BLADE): public 0.500 / 0.927 ± 0.012, role_required 0.445 / 0.618 ± 0.024, membership_required 0.150 / 0.568 ± 0.027, tenant_match 0.000 / 0.249 ± 0.076, owner_match 0.297 / 0.912 ± 0.016, owner_or_admin 0.105 / 0.714 ± 0.042, manual_review_required 0.000 / 0.564 ± 0.055.
- 참고(발표 표 밖): 회귀·안전 지표 test_v30 207(v7 학습 미포함) 구체 정밀도 Base 0.353 → BLADE 0.824, public 오판(/35) 17 → 1.3, 정확도 0.319 → 0.630 — json `test_v30_207`. test_v5·test_v31_supp는 v7 학습 데이터라 v7 수치가 없다(v5 시점 값은 json `*_v5_reference`).

## 모델·데이터 요약

- BLADE LoRA v7: 베이스 unsloth/Qwen2.5-7B-Instruct-bnb-4bit, QLoRA r16/α16, 3 epoch, lr 2e-4, batch 2×4, cosine, adamw_8bit, max_seq_len 4096, 프롬프트 v3.0.1(`d0913c27…`), completion-only 마스킹, seed 42·43·44. 학습 데이터 data-v7(train 1,540 / val 159). 학습 29.2분/seed(H100). 상세 reports/data_v7/stop5_build_report.md, reports/eval/lora_v7/report.md(1단계), s9/report.md(S9).
- 중간 실험 S4(문맥 보강)·S5(v3.1 프롬프트)·S8(14B)·C′(라벨 36건 교정)는 사전 기준 미달로 불채택(reports/eval/{context_aug_v5,lora_v6a,lora_v6c,lora_v6d}/report.md). **평가는 HF 어댑터 기준(위 표), 배포는 s42 Q4_K_M GGUF**(Ollama blade-qwen-lora-v7, MIN_CONFIDENCE 0.9, 2026-11-10 D1 조건부 수용). 배포 GGUF는 같은 어댑터 HF s42 대비 test_v30 207 구체 정밀도 −0.03·public 오판 +2(crAPI owner_match 2건)이며, GGUF 경로 confidence는 265건 중 261건이 0.9로 고정이라 문턱이 실질적으로 거르는 행이 0건이다(reports/eval/lora_v7_gguf/equivalence_check.md, report.md 6절). 운영 조건: public 판정 정책은 승인 시 우선 검토. 롤백 blade-qwen-lora-v5 유지.
