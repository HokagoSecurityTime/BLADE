# GGUF Q4_K_M 변환 동등성 확인 — LoRA v7 s42 (test_v30 oas_code, 튜닝 없음) — 조건부 수용 확정 (사용자 2026-11-10)

**사용자 확정 조건(2026-11-10)**: (1) 발표·보고 수치는 HF 3-seed 유지, "평가는 HF 어댑터 기준, 배포는 Q4_K_M GGUF"를 명시. (2) 한계 절에 배포 GGUF 구체 정밀도 −0.03·public 오판 +2(crAPI owner_match 2건) 기록(reports/eval/lora_v7/report.md 6절). (3) 운영 조건: public 판정 정책은 승인(PENDING → ACTIVE) 시 우선 검토 대상. (4) GGUF confidence가 261/265건 0.9로 고정이라 MIN_CONFIDENCE 문턱이 GGUF 경로에서 실질적으로 거르는 행이 0건임을 한계에 명시(발표 자료 점검: "문턱으로 불확실 판정 차단" 류 문구 없음, G_example21_pixi_user_loves.md 62행의 "confidence 0.9가 문턱을 넘어 채택됨"은 사실 서술). (5) v5 롤백 유지.

비교 대상은 **같은 어댑터(lora_v7_s42 final)의 HF 예측**(reports/eval/lora_v7/lora_v7_s42/eval/predictions_oas_code_lora_v7_s42_final.jsonl, RunPod 4bit 학습 환경·bf16 추론). GGUF 추론은 Pod GPU Ollama(/api/chat, Modelfile.blade-qwen-lora-v7, greedy·repeat_penalty 1·num_predict 256·num_ctx 8192), eval_ollama_v7.py. 채점 scripts/eval_v30.py(eval-def v2).

## 수치 (equivalence_numbers.json)

| 지표 | GGUF Q4_K_M | HF s42 final | 차이 | 허용 폭(주, v4 3-seed sd = v5 때 적용 폭) | 판정 | v5 sd | v7 sd |
|---|---:|---:|---:|---:|---|---:|---:|
| macro-F1 합성 제외 207 (주지표) (주) | 0.3705 | 0.3775 | -0.0070 | 0.0454 | 안 | 0.0104 | 0.0187 |
| 구체 정밀도 합성 제외 207 (주) | 0.7756 | 0.8077 | -0.0321 | 0.0255 | 이탈(하락) | 0.0252 (이탈) | 0.0200 (이탈) |
| 구체 재현율 합성 제외 207 | 0.5874 | 0.6117 | -0.0243 | 0.0654 | 안 | 0.0101 (이탈) | 0.0148 (이탈) |
| 구체 정밀도 265 (주) | 0.8250 | 0.8500 | -0.0250 | 0.0175 | 이탈(하락) | 0.0197 (이탈) | 0.0150 (이탈) |
| macro-F1 265 | 0.7305 | 0.7282 | +0.0023 | 0.0217 | 안 | 0.0095 | 0.0091 |
| manual 비율 265 | 0.2340 | 0.2264 | +0.0076 | 0.0437 |  | 0.0178 | 0.0100 |
| 출력 오류 265 | 3 | 5 | -2 | | | | |
| public 오판(신, /47) | 3 | 1 | +2 | | | | |

- 행 단위 label 일치 229/265 (86.4%). 불일치 36건 중 HF 보류/오류 → GGUF 구체 12, 그 반대 12, 구체↔구체 10. 불일치에서 정답을 맞힌 쪽은 GGUF 9 / HF 14. 상위 전이: manual_review_required->public 9, owner_match->manual_review_required 8, owner_match->public 5, membership_required->owner_match 2, output_error->manual_review_required 2, role_required->owner_or_admin 1.
- GGUF public 오판 id: acdc8447219278841824, fc9dac901542ca88d688, d8c5cf5eb0bfbd488219; HF: fc9dac901542ca88d688.
- 템플릿 검사 3건: HF chat_template 토큰 수 = Ollama raw = Ollama chat (3060, 2890, 3184).

## 판정 제안 (사전 기록 2026-11-10: "v5 때와 같은 허용 폭" = v4 3-seed sd)

- 주지표 3개(macro-F1 합성 제외 207 (주지표), 구체 정밀도 합성 제외 207, 구체 정밀도 265) 허용 폭 안: 1/3 → **조건부 수용 제안(사용자 판단)**.
- 참고: v5 3-seed sd 기준 1/3, v7 3-seed sd 기준 1/3 (좁은 폭으로 읽으면 이탈 방향을 병기).
- 발표·보고서 성능 수치는 LoRA v7 3-seed(HF) 평가(reports/eval/lora_v7/presentation_numbers_v7.md)를 유지하고, 위 GGUF 수치는 "배포 모델 변환 동등성 확인"으로만 표기한다.

### 판정 제안 상세 (2026-11-10, 사용자 확정 전)

- 이탈 지표는 구체 정밀도 2개이며 방향은 하락이다(207: −0.032, 폭 0.0255의 1.26배; 265: −0.025, 폭 0.0175의 1.43배). v5 때(정밀도 +0.014/+0.007, 보류 25.3% → 18.5%)와 달리 **보류 비율 이동으로 설명되지 않는다**(manual 22.6% → 23.4%, +0.8%p). 불일치 36건 중 HF 보류·오류 → GGUF 구체 12건과 그 반대 12건이 상쇄되고, 구체↔구체 10건(owner_match → public 5 등)과 manual → public 9건이 정밀도를 깎았다. 규모로는 구체 예측 약 160건 중 5건 안팎의 차이다.
- 행 일치율은 86.4%(229/265)로 v5 때(81.1%)보다 높다. 즉 변환 자체의 흔들림은 v5보다 작고, 흔들린 행이 v5 때는 정답 쪽(GGUF 21 / HF 8)으로, 이번에는 오답 쪽(GGUF 9 / HF 14)으로 기울었다.
- public 오판 3건(GGUF)은 전부 crAPI owner_match 정답: `GET /identity/api/v2/user/dashboard`(acdc8447…, HF owner_match), `POST /identity/api/v2/user/reset-password`(fc9dac90…, HF도 public), `POST /identity/api/v2/vehicle/resend_email`(d8c5cf5e…, HF owner_match). security_state 미선언 입력이다.
- **배포 문턱을 적용해도 수치는 같다**: GGUF test 예측의 confidence는 0.9가 261건·0.85가 1건(해당 행은 이미 manual)·출력 오류 3건이라 MIN_CONFIDENCE 0.9로 보류되는 행이 0건이다. 따라서 위 정밀도 하락은 실제 배포 경로(blade-qwen-lora-v7 + 0.9)의 수치다.
- 제안: 사전 규칙대로 **조건부 수용 제안** — 조건은 (1) 발표·보고서 수치는 HF 3-seed 유지, (2) 보고서 한계 절에 "배포 GGUF는 HF s42 대비 구체 정밀도 −0.03(207)·public 오판 +2(crAPI owner_match 2건)"를 기록, (3) 롤백 모델 v5 유지. 대안인 Q8_0·f16 재양자화는 로컬 디스크(여유 6.1 GB, Q8_0 약 8.1 GB)상 v5 blob을 지우지 않으면 불가하고 Pod 재실행이 필요하다. 어느 쪽이든 사용자 확정 사항이다.

## 파이프라인 문턱 (val_v7만 사용, test 미사용)

choose_threshold_v4.py `--rule precision`(v5·v4와 같은 규칙: val 구체 정밀도 최대, 동률이면 낮은 문턱, 기존 바닥 0.7) → threshold_val_v7.json. val_sft_v7 159건(oas 32 + oas_code 127; 조건별 값은 JSON), 출력 오류 0, confidence 분포 0.7:5 · 0.85:24 · 0.9:112 · 1.0:18.

| 문턱 | val macro-F1 | 구체 정밀도 | manual 비율 |
|---|---:|---:|---:|
| 0 ~ 0.85 | 0.779 | 0.831 | 22.0% |
| **0.9** | 0.763 | **0.835** | 23.9% |
| 1.0 | 0.288 | 0.667 | 88.7% |

선택 **MIN_CONFIDENCE = 0.9** (v5·v4와 같음; 정밀도 차이는 0.004이고 규칙상 최대값을 택했다). 조건별(0.9): oas 정밀도 0.905 / manual 34.4%, oas_code 정밀도 0.820 / manual 21.3%.

## 파일

- predictions_oas_code_lora_v7_s42_gguf_q4km.jsonl (265), val_predictions_lora_v7_s42_gguf_q4km.jsonl (159), template_check.log, scores_test_v30.json, eval_v30.md, equivalence_numbers.json, threshold_val_v7.json, merge_manifest_v7_s42.json, SHA256SUMS_gguf_v7_s42, merge.log, quantize.log, c7.log. 결과 tar `blade_c7_v7_results.tar.gz` SHA-256 `dd4f771ea23ba0037260b388ea0e9f2b0a79bb98631031d9b81a2bb37905bcaf`.
- 빌드(Pod, 2026-11-10 03:0x–03:42 UTC): 어댑터 `66c68a58…` → Qwen/Qwen2.5-7B-Instruct `a09a3545…` fp32 병합 → fp16 → f16 GGUF `ab60f867…` → llama.cpp b11693 Q4_K_M 4,683,073,504 bytes SHA-256 `1dd24dcdff60619d055277591b134f133a24a4cd62a9b51f3cec8abcdc88144d`(torch 2.13.0+cu129·transformers 5.22.2·peft 0.21.2). Pod 추론 평균 0.9 s/행.
- GGUF 본체는 git 밖(*.gguf ignore): 로컬 Ollama blob `<USERPROFILE>\.ollama\models\blobs\sha256-1dd24dcd…`(= Q4_K_M 파일을 Downloads에서 이동, 복사 없이 등록; 2026-11-10 `ollama create blade-qwen-lora-v7 -f training/lora/Modelfile.blade-qwen-lora-v7.local`, .local은 .gitignore). 응답 확인 "OK"(9 s). blade-qwen-lora-v5·qwen2.5:7b 유지.
