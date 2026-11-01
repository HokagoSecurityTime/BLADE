# LoRA v4 서빙 (Ollama, blade-qwen-lora-v4)

LoRA v4 s42 final 어댑터를 unquantized Qwen2.5-7B-Instruct에 병합하고, GGUF Q4_K_M으로 변환해 Ollama에 등록한다. 학습은 하지 않는다.

| 항목 | 값 |
|---|---|
| 어댑터 | `~/Downloads/blade_v4_adapters.tar.gz` 안의 `lora_v4_s42/adapter/` (adapter_model.safetensors SHA-256 `789bb180181bf16406c1106543fce2e8f0f4fbebfd50be07e49a8bfe0e1ef682`) |
| 베이스 | `Qwen/Qwen2.5-7B-Instruct` 리비전 `a09a35458c702b33eeacc393d103063234e8bc28` (bf16, 4bit 아님) |
| 병합 | 대상 196개 텐서(28층 × 7모듈), fp32로 `W + (alpha/r)·B·A`, alpha/r = 1 → f16 GGUF |
| f16 GGUF | SHA-256 `93c4a2491ba8e0da971a395f82c77eee514479b3990f7d093438ff827554337d` (양자화 후 디스크 확보를 위해 삭제) |
| Q4_K_M GGUF | 4,683,073,504 bytes, SHA-256 `9fe332d94f5ade3d98d0b1f202ecd65c03b6f59cad741925954c9e0ce5403a40` (= Ollama blob) |
| 도구 | llama.cpp b11693 (소스: convert 코드, Windows CPU x64 바이너리: llama-quantize) |
| 토크나이저·템플릿 | 어댑터의 tokenizer.json, tokenizer_config.json, chat_template.jinja (학습 때와 동일) |

## 절차

```bash
# 1) 어댑터 추출
tar -xzf ~/Downloads/blade_v4_adapters.tar.gz -C <work>/adapter lora_v4_s42/adapter
# 2) 병합 + f16 GGUF. 베이스는 HF에서 텐서 단위 range 요청으로 읽으므로 샤드·병합 체크포인트를 디스크에 쓰지 않는다(약 65분, 7MB/s)
.python/python.exe -X utf8 training/lora/merge_gguf_v4.py --adapter <work>/adapter/lora_v4_s42/adapter --llama-src <llama.cpp-b11693> --out <work>/gguf/blade-qwen-lora-v4-f16.gguf
# 3) Q4_K_M (약 7분)
llama-quantize.exe blade-qwen-lora-v4-f16.gguf blade-qwen-lora-v4-Q4_K_M.gguf Q4_K_M
# 4) Ollama 등록: Modelfile을 GGUF 옆에 복사
cp training/lora/Modelfile.blade-qwen-lora-v4 <work>/gguf/ && ollama create blade-qwen-lora-v4 -f <work>/gguf/Modelfile.blade-qwen-lora-v4
```

- 디스크 최대 사용량은 f16(15.2GB) + Q4_K_M(4.7GB)이다.
- Modelfile TEMPLATE은 system + user 턴에 대해 chat_template.jinja와 같은 프롬프트를 만든다. `eval_ollama_v4.py --check-template N`이 HF 템플릿 토큰 수와 Ollama `prompt_eval_count`(raw·chat)가 같은지 assert한다.
- 디코딩은 run_train.py 평가와 같다: greedy(temperature 0), repeat_penalty 1(패널티 없음), num_predict 256. num_ctx 8192(입력 최대 3,916토큰).
- CPU greedy 출력은 KV 캐시 상태(직전 요청과 공유된 접두부)에 따라 드물게 달라진다. 같은 프롬프트를 반복하면 같은 출력이 나온다.

## 동등성 확인 (test_v30 oas_code, 튜닝 없음)

```bash
.python/python.exe -X utf8 training/lora/eval_ollama_v4.py --split test --check-template 3 --tokenizer <adapter dir> --out reports/eval/lora_v4_gguf/predictions_oas_code_lora_v4_s42_gguf_q4km.jsonl
.python/python.exe -X utf8 scripts/eval_v30.py --pred reports/eval/lora_v4_gguf/predictions_oas_code_lora_v4_s42_gguf_q4km.jsonl reports/eval/lora_v4/lora_v4_s42/eval/predictions_oas_code_lora_v4_s42_final.jsonl --out reports/eval/lora_v4_gguf/scores_test_v30.json
```

## 파이프라인 문턱 (val_v4만 사용)

```bash
.python/python.exe -X utf8 training/lora/eval_ollama_v4.py --split val --out reports/eval/lora_v4_gguf/val_predictions_lora_v4_s42_gguf_q4km.jsonl
.python/python.exe -X utf8 training/lora/choose_threshold_v4.py --pred reports/eval/lora_v4_gguf/val_predictions_lora_v4_s42_gguf_q4km.jsonl --out reports/eval/lora_v4_gguf/threshold_val_v4.json
```

파이프라인 사용: `BLADE_CLASSIFIER=lora` (기본 `llm`), `BLADE_LORA_MODEL`(기본 blade-qwen-lora-v4), `BLADE_LORA_MIN_CONFIDENCE`, `BLADE_LORA_TIMEOUT`(기본 600초), `BLADE_LORA_PROMPT_PATH`(기본 training/data/prompts/policy_label_v3.0.1.md, SHA 검사), `BLADE_OLLAMA_URL`.
