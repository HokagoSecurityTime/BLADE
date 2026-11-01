# LoRA v5 서빙 (Ollama, blade-qwen-lora-v5) — C-5 전환 (사용자 승인 2026-10-31)

LoRA v5 s42 final 어댑터를 unquantized Qwen2.5-7B-Instruct에 병합하고 GGUF Q4_K_M으로 변환해 Ollama에 등록한다. v4(README_serve_v4.md)와 같은 구성이며 학습은 하지 않는다. v4 모델(blade-qwen-lora-v4)은 롤백용으로 남긴다.

| 항목 | 값 |
|---|---|
| 어댑터 | training/lora/runs/lora_v5_s42/adapter (adapter_model.safetensors SHA-256 `75ea08c194cb925556abcf4054f3236b8cea3c42e41eede31300ba443561b5d5`) |
| 베이스 | `Qwen/Qwen2.5-7B-Instruct` 리비전 `a09a35458c702b33eeacc393d103063234e8bc28` (bf16, 4bit 아님) |
| 병합 | 196개 텐서(28층 × 7모듈), fp32 `W + (alpha/r)·B·A` → fp16 체크포인트 → f16 GGUF (runpod/merge_gguf_v5.sh, RunPod 컨테이너 디스크) |
| f16 GGUF | SHA-256 `2018d6f6dbbbcf604cc1eb80f7cdfc1ac6353b6b21e00d3350e95af3133e3da9` (양자화 후 삭제) |
| Q4_K_M GGUF | 4,683,073,504 bytes, SHA-256 `2935029694548ed0dff2f5e1aa5bcb87ae553bdfa5535d59ea62b5da9ab2976d` (= Ollama blob) |
| 도구 | llama.cpp b11693 (convert_hf_to_gguf.py + llama-quantize), transformers 5.22.1, peft 0.21.2, torch 2.8.0 (Pod) |
| 토크나이저·템플릿 | 어댑터의 tokenizer.json, tokenizer_config.json, chat_template.jinja |
| 빌드 기록 | reports/eval/lora_v5_gguf/merge_manifest_v5_s42.json, SHA256SUMS_gguf_s42, merge.log, quantize.log, c5.log |

## 절차 (실행 완료 2026-10-31)

```bash
# Pod: README_runpod_rerun.md 4.6절 (setup_c5.sh → run_c5.sh; 양자화는 quantize_resume_c5.sh로 재개)
# 로컬: GGUF를 Ollama blob 이름(sha256-<Q4 SHA>)으로 두면 ollama create가 복사 없이 재사용한다(C: 여유 4GB라 복사 불가)
mv blade-qwen-lora-v5-s42-Q4_K_M.gguf %USERPROFILE%\.ollama\models\blobs\sha256-2935029694548ed0dff2f5e1aa5bcb87ae553bdfa5535d59ea62b5da9ab2976d
# Modelfile의 FROM을 그 blob 경로로 바꾼 복사본으로 등록 (TEMPLATE·PARAMETER는 training/lora/Modelfile.blade-qwen-lora-v5 그대로)
ollama create blade-qwen-lora-v5 -f Modelfile.blade-qwen-lora-v5.local
ollama list    # blade-qwen-lora-v5, blade-qwen-lora-v4(유지), qwen2.5:7b
```

- 디코딩은 run_train.py 평가와 같다: greedy(temperature 0), repeat_penalty 1, num_predict 256, num_ctx 8192.
- 동등성 확인(test_v30 oas_code, Pod GPU Ollama): reports/eval/lora_v5_gguf/equivalence_check.md — 주지표 macro-F1 +0.034, 합성 제외 구체 정밀도 +0.014, 265 정밀도 +0.007, 모두 v4 허용 폭(v4 3-seed sd) 안. 보류 25.3% → 18.5%.
- 문턱(val_v5만): choose_threshold_v4.py --rule precision → **0.9** (threshold_val_v5.json).

## 파이프라인 전환 (런타임 코드 수정 없음, 환경변수만)

```powershell
$env:BLADE_CLASSIFIER = 'lora'                 # 기본 llm
$env:BLADE_LORA_MODEL = 'blade-qwen-lora-v5'   # 기본(코드 상수) blade-qwen-lora-v4 — 롤백은 이 변수를 지우면 된다
$env:BLADE_LORA_MIN_CONFIDENCE = '0.9'         # val_v5 선택값(v4와 같음)
```

- 그 외 `BLADE_LORA_TIMEOUT`(600초), `BLADE_LORA_PROMPT_PATH`(policy_label_v3.0.1.md, SHA 검사), `BLADE_OLLAMA_URL`은 v4와 같다(pipeline/classifier/lora.py).
- 종단간 검증: `BLADE_VERIFY_OUT=reports/eval/lora_v5_gguf BLADE_LORA_MODEL=blade-qwen-lora-v5 BLADE_LORA_MIN_CONFIDENCE=0.9 BLADE_LLM_MODEL=qwen2.5:7b python -X utf8 scripts/verify_lora_pipeline.py` → reports/eval/lora_v5_gguf/pipeline_compare.{json,md}. 전체 테스트 `python -m pytest tests`.
