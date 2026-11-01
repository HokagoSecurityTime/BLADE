# GGUF Q4_K_M 변환 동등성 확인 — LoRA v5 s42 (test_v30 oas_code, 튜닝 없음) — 수용 확정 (사용자 2026-10-31, v4 허용 폭 기준)

모델 blade-qwen-lora-v5 (LoRA v5 s42 final 어댑터 SHA `75ea08c1…` → unquantized Qwen2.5-7B-Instruct 리비전 `a09a3545…`에 fp32 병합 → f16 GGUF(SHA `2018d6f6…`) → llama.cpp b11693 Q4_K_M). Q4_K_M 4,683,073,504 bytes, SHA-256 `2935029694548ed0dff2f5e1aa5bcb87ae553bdfa5535d59ea62b5da9ab2976d` (= Ollama blob). 빌드 기록 merge_manifest_v5_s42.json, merge.log, quantize.log (RunPod, 2026-10-31 11:27–12:10 UTC; 양자화는 RAM 20GB Pod에서 한 번 죽어 f16에서 재개 — quantize_resume_c5.sh, f16 해시 일치 확인).

추론: Pod GPU의 Ollama(/api/chat, Modelfile.blade-qwen-lora-v5, greedy·repeat_penalty 1·num_predict 256·num_ctx 8192), eval_ollama_v5.py. 템플릿 검사 3건: HF chat_template 토큰 수 = Ollama raw = Ollama chat (3060·2890·3184). 채점 scripts/eval_v30.py(eval-def v2) → scores_test_v30.json, eval_v30.md. 비교 대상은 **같은 어댑터(s42)의 HF final 예측**(reports/eval/lora_v5/lora_v5_s42/eval/predictions_oas_code_lora_v5_s42_final.jsonl, RunPod 4bit 학습 환경·bf16 추론).

## 수치 (equivalence_numbers.json)

| 지표 | GGUF Q4_K_M | HF s42 final | 차이 | 허용 폭 v4 3-seed sd(v4 때 규칙) | 판정 | 참고: v5 3-seed sd |
|---|---:|---:|---:|---:|---|---:|
| macro-F1 합성 제외 207 (주지표) | 0.3996 | 0.3661 | +0.034 | 0.045 | 안 | 0.010 (이탈, 상승 방향) |
| 구체 정밀도 합성 제외 207 | 0.7805 | 0.7667 | +0.014 | 0.026 | 안 | 0.025 (안) |
| 구체 정밀도 265 | 0.8261 | 0.8187 | +0.007 | 0.018 | 안 | 0.020 (안) |
| 구체 재현율 합성 제외 207 | 0.6214 | 0.5583 | +0.063 | 0.065 | 안 | 0.010 (이탈, 상승) |
| macro-F1 265 | 0.7731 | 0.6947 | +0.078 | 0.022 | 이탈(상승) | 0.010 (이탈, 상승) |
| manual 비율 265 | 18.5% | 25.3% | −6.8%p | | | |
| 출력 오류 265 | 9 | 5 | +4 | | | |
| public 오판(신, /47) | 2 | 3 | −1 | | | |

- 행 단위 label 일치 215/265 (81.1%). 불일치 50건 중 23건은 HF manual/출력오류 → GGUF 구체 label(owner_match 9+3, role 6, public 5 등), 9건은 그 반대(GGUF 보류·오류), 12건은 구체↔구체. 불일치 50건에서 정답을 맞힌 쪽은 GGUF 21 / HF 8.
- 해석: v4 때와 같은 양상이다. 양자화·GPU 디코딩으로 보류가 줄고(25.3% → 18.5%) 구체 응답이 늘어, 재현율·macro-F1은 오르고 정밀도는 거의 같다(+0.007~+0.014). 성능 저하가 아니라 보류 경향 이동이다. 출력 오류가 5 → 9로 늘었는데 전부 manual·파이프라인에서는 보류 처리된다.

## 판정 제안 (사용자 지시: "v4 때와 같은 허용 폭")

- v4 판정 규칙(equivalence_check.md, 2026-10-30): 같은 adapter(s42) HF final과 비교, 허용 폭은 **v4 3-seed 표준편차**, 지표는 주지표 macro-F1 합성 제외·합성 제외 구체 정밀도·265 구체 정밀도.
- 세 지표 모두 v4 허용 폭 안이다(+0.034 ≤ 0.045, +0.014 ≤ 0.026, +0.007 ≤ 0.018). v4 때 조건부였던 265 정밀도도 이번에는 안이다. → **수용 제안** → **사용자 수용 확정(2026-10-31, "사전 지정대로 v4 허용 폭 기준 수용. v5 폭 기준 해석은 보고서에 병기 유지")**. 배포 모델 보류율(18.5%)이 평가 모델(25.3%)보다 낮은 점은 lora_v5_report.md 한계 절에 적었다.
- 주의: 허용 폭을 v5 자체의 3-seed sd로 읽으면 macro-F1(+0.034 > 0.010)은 벗어난다(상승 방향). v5는 seed 분산이 작아 폭이 좁다. 어느 폭을 쓸지는 사용자 지시대로 v4 폭을 적용했고, v5 폭 결과를 병기한다.
- 표기: 발표·보고서 성능 수치는 LoRA v5 3-seed(HF) 평가를 유지한다. 위 GGUF 수치는 "배포 모델 변환 동등성 확인"으로만 별도 표기한다.

## 파이프라인 문턱 (val_v5만 사용, test 미사용)

choose_threshold_v4.py `--rule precision`(v4와 같은 규칙: val 구체 정밀도 최대, 동률이면 낮은 문턱, 기존 바닥 0.7) → threshold_val_v5.json. val_sft_v5 179건(oas 52 + oas_code 127; 조건별 값은 JSON), 출력 오류 1, confidence 분포 0.7:3 · 0.8:2 · 0.85:20 · 0.9:135 · 1.0:18.

| 문턱 | val macro-F1 | 구체 정밀도 | manual 비율 |
|---|---:|---:|---:|
| 0 ~ 0.85 | 0.697 | 0.702 | 15.6% |
| **0.9** | 0.666 | **0.703** | 19.0% |
| 1.0 | 0.236 | 0.588 | 90.5% |

선택 **MIN_CONFIDENCE = 0.9** (v4와 같음; 정밀도 차이는 0.001이고 규칙상 최대값을 택했다). 조건별(0.9): oas 정밀도 0.636 / manual 15.4%, oas_code 정밀도 0.733 / manual 20.5%.

## 파일

- predictions_oas_code_lora_v5_s42_gguf_q4km.jsonl (265), val_predictions_lora_v5_s42_gguf_q4km.jsonl (179), template_check.log, scores_test_v30.json, eval_v30.md, equivalence_numbers.json, threshold_val_v5.json, merge_manifest_v5_s42.json, SHA256SUMS_gguf_s42, merge.log, quantize.log, c5.log.
- GGUF 본체는 git 밖(*.gguf ignore): 로컬 Ollama blob `<USERPROFILE>\.ollama\models\blobs\sha256-2935029694…`(= Q4_K_M 파일 그대로, 복사 없이 등록). 원본 zip `<USERPROFILE>\Downloads\GGUF_v5.zip`.
