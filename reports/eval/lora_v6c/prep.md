# S8 준비 보고 — 베이스 모델만 14B로 교체 (LoRA v6c), 2026-11-04 (1단계, 학습 전 정지)

변경은 베이스 모델 하나뿐: `unsloth/Qwen2.5-7B-Instruct-bnb-4bit` → **`unsloth/Qwen2.5-14B-Instruct-bnb-4bit`**. 데이터 data-v5 train/val(해시 확인), 프롬프트 v3.0.1, 출력 순서 v5와 동일(label 먼저), max_seq_len 4096, max_new_tokens 256, LoRA r16·α16·3 epoch·lr 2e-4·cosine·adamw_8bit, seed 42/43/44, completion-only 마스킹. 문맥 블록·label 토큰 확률 없음. 마감 2026-11-11.

## 1. 후보 비교 (HF API 조회 2026-11-04)

| 모델 | 라이선스 | 최근 수정 | unsloth bnb-4bit | 토크나이저·채팅 템플릿(Qwen2.5-7B 대비) | 판단 |
|---|---|---|---|---|---|
| **Qwen/Qwen2.5-14B-Instruct** (unsloth/Qwen2.5-14B-Instruct-bnb-4bit) | Apache-2.0 | 2024-09-25 (bnb 2025-04-28) | 있음, 9.27 GB (2 shard) | **동일** — tokenizer.json SHA `9c5ae00e…`·vocab·merges·tokenizer_config 모두 7B와 바이트 동일, chat_template 문자열 동일, eos `<|im_end|>`·pad 동일 | **선택(기본)** |
| Qwen/Qwen2.5-Coder-14B-Instruct | Apache-2.0 | 2025-01-12 | 있음, 9.3 GB | Qwen2 계열(템플릿 동일 추정, 바이트 비교 미실시) | 보류 — 코드 특화 instruct라 "베이스 크기만 바꾼다"는 단일 변수 비교가 흐려짐 |
| Qwen/Qwen3-14B | Apache-2.0 | 2025-07-26 | 있음(Qwen3-14B-bnb-4bit 9.26 GB, -unsloth-bnb-4bit 10.37 GB) | **다름** — hybrid thinking(기본 thinking on, `enable_thinking` 스위치), 템플릿에 `<think>` 블록, added tokens 26(7B 22), tokenizer.json SHA `aeb13307…` | 제외(템플릿 다름 → 규칙대로 Qwen2.5 유지). non-thinking으로 쓰려면 SFT target에 빈 `<think></think>` 삽입·마스킹 경계·Ollama 템플릿까지 바뀜 |
| Qwen3-14B-2507 | — | 없음 | — | — | 존재하지 않음(2507 갱신은 4B·30B-A3B·235B만) |
| Qwen3.5 (2026-02~04: 0.8B·2B·4B·9B·27B·35B-A3B·122B·397B) | Apache-2.0 | 9B 2026-03-02, 27B 2026-04-24 | 9B unsloth 재업로드만(bf16 18 GB), 27B bnb-4bit 없음 | 다름 — `Qwen3_5ForConditionalGeneration`(멀티모달 아키텍처), thinking 템플릿, added tokens 33 | 제외 — 14B급 없음(9B는 작고 27B는 Q4_K_M ≈ 16 GB로 로컬 CPU PC 범위 밖), 템플릿 다름, unsloth 4bit 학습 경로 미검증 |
| Qwen3.6-27B / 35B-A3B (2026) | Apache-2.0 | — | — | 다름 | 제외(크기·템플릿) |

결론: 2026년 현재 Qwen 계열에 "14B급·Qwen2.5 템플릿 동일" 최신 모델은 없다. Qwen2.5-14B-Instruct를 쓴다. (WebWorld-14B 2026-05는 웹 에이전트 특화라 제외.)

## 2. 토큰 길이 재계산 (14B 토크나이저, reports/eval/lora_v6c/prep_tokens.json)

14B 토크나이저로 system v3.0.1 + user + assistant를 `apply_chat_template`로 조립해 셌다. 7B 결과와 **전 행 동일**(토크나이저 파일이 같으므로 당연).

| 파일 | n | 평균 | 최대 | 4096 초과 |
|---|---:|---:|---:|---:|
| train_sft_v5.jsonl | 1274 | 3286.9 | 4085 | **0** |
| val_sft_v5.jsonl | 179 | 3283.0 | 4015 | 0 |
| test_v30_inputs oas / oas_code | 269 / 265 | 2816.8 / 3038.7 | 2976 / 3841 | 0 / 0 |
| test_v5_inputs oas / oas_code | 283 / 283 | 2816.6 / 3491.2 | 2843 / 4051 | 0 / 0 |

- data_v5 해시: train_sft_v5·val_sft_v5·test_v30_inputs는 data_v5_hashes.json generated와 일치, test_v5_inputs는 manifest(`57fd384f…`) 경로로 검증(기존 규약).
- 참고: train 행의 저장된 `tokens` 필드와 재계산값이 71행에서 최대 24 토큰 차이(예: gitea POST /markdown −24). 최대값(4085)은 같고 4096 초과는 둘 다 0이라 v6c에 영향 없다(저장 필드는 빌드 당시 계산치, 학습 입력은 run_train이 다시 토큰화).

## 3. completion-only 마스킹

v5·v6a와 같은 `train_on_responses_only(trainer, instruction_part='<|im_start|>user\n', response_part='<|im_start|>assistant\n')`(run_train.py 119행). 14B의 chat_template이 7B와 동일하므로 경계 문자열이 그대로 맞는다. v6c 스크립트도 학습 시작 시 0번 행 마스킹 비율을 로그에 남긴다(v6a와 같은 검사).

## 4. H100 80GB 기준 시간·메모리 추정

실측 근거: v5 7B A100 학습 56.2분/seed(480 step, total_flos 5.36e17), v6a 7B H100(6144, padding-free) 32.5분/seed, v6a 추론 H100 배치 8 약 0.45~0.56 s/row(프롬프트 4.6k 토큰).

| 항목 | 추정 | 근거 |
|---|---|---|
| 학습 FLOPs | ≈ 1.0e18 / seed | 파라미터 14.7B / 7.6B = 1.93배 |
| 학습 시간 | **50~65분 / seed** | H100 7B@4096 ≈ 25~30분 × 1.9~2.1 |
| 평가 시간 | test_v30 534행 + test_v5 566행 ≈ 15분, test_v31_supp 444행 추가 시 +6분 | 14B ≈ 0.8~1.0 s/row(7B의 2배) |
| seed당 | **70~90분** | |
| 3 seed 합계 | **3.5~4.5시간** + 설치 15분 + 베이스 9.3 GB 다운로드 | v6a 실측 2시간 12분의 약 2배 |
| 학습 메모리 | 4bit 가중치 ≈ 9.3 GB + LoRA 59.1M 파라미터(옵티마 포함 < 1 GB) + 체크포인트 활성화(48층 × 2 × 4096 × 5120 bf16 ≈ 4 GB) + 로짓(2 × 4096 × 152064) → **피크 약 20~30 GB** | batch 2 × grad_acc 4 = 8 유지, 조정 불필요 |
| 평가 메모리 | KV 192 KB/token × 8 × 4352 ≈ 6.7 GB + 가중치 | 48층·KV head 8·head dim 128 |

- 14B 구성: 48층, hidden 5120, 40 head / KV 8 head, intermediate 13824, vocab 152064.
- unsloth Padding-free 자동 활성은 이번에도 켜질 수 있다(v6a에서 켜짐). env.json·로그에 기록한다.

## 5. 배포 영향 추정 (로컬 Ollama, 현재 PC)

로컬 PC: **NVIDIA GPU 없음**(Intel UHD 630 1 GB), CPU i5-9400 6코어, RAM 31.8 GB, C: 여유 17.2 GB, Ollama blob 4.36 GB(현재 `ollama list`에는 blade-qwen-lora-v5만 있고 blade-qwen-lora-v4·qwen2.5:7b는 없음 — README_serve_v5.md의 "v4 롤백용 유지"와 다른 상태. 사실만 기록하며 복구는 S9 이후 배포 정리 때 한다(사용자 결정 2026-11-04)).

| 항목 | v5 (7B) | v6c (14B) 추정 |
|---|---|---|
| GGUF Q4_K_M 크기 | 4,683,073,504 B (4.36 GiB) | **≈ 8.4 GiB(9.0 GB)** — bartowski Q4_K_M 8.37 GiB, 공식 분할 3.72+3.72+0.94 GiB |
| f16 GGUF / 병합 fp16 체크포인트 | 15 GB / 15 GB | 29.5 GB / 29.5 GB |
| Pod 병합 디스크 피크 | 30~35 GB (DROP_HF_CACHE=1) | **≈ 60 GB**(베이스 bf16 29.5 삭제 후) ~ 90 GB(미삭제); 컨테이너 디스크 **≥ 120 GB** 권장 |
| Pod 병합 RAM | fp32 병합 32 GB | **fp32 병합 ≈ 59 GB → RAM ≥ 80 GB**(없으면 GPU 위 bf16 병합으로 바꾸고 v5 구성과의 차이를 기록) |
| 로컬 메모리(CPU 추론) | 가중치 4.7 GB + KV(num_ctx 8192, 57 KB/token) 0.45 GB | 가중치 9 GB + KV 1.5 GB(192 KB/token) ≈ **11 GB**, RAM 31.8 GB 안 |
| 로컬 디스크 | blob 4.7 GB | blob 9 GB(여유 17.2 GB; v5처럼 blob 이름으로 직접 두어 복사본 없이 등록, 복사하면 18 GB 필요) |
| 정책 1건 분류 지연(CPU, 프롬프트 ≈ 3k 토큰) | 72.8 s/policy(pipeline_compare 7건 509.6 s) | **≈ 140~160 s/policy**(prompt eval이 파라미터 수에 비례) — BLADE_LORA_TIMEOUT 600 s 안, verify_lora_pipeline 7건 ≈ 17분 |
| 프록시 요청 지연(p95 +2.0 ms) | 영향 없음 | 영향 없음(분류는 정책 승인 시점, 요청 경로 밖) |
| 전환 절차 | 변환 동등성(v4 sd 폭)·MIN_CONFIDENCE(val만, 바닥 0.7)·Modelfile 등록·환경변수 | 동일 절차, Modelfile FROM만 교체(TEMPLATE·PARAMETER 동일) |

**14B 채택 시 GGUF 병합 Pod 요건(사전 기록 2026-11-04)**: RAM ≥ 80 GB(fp32 병합 ≈ 59 GB), 컨테이너 디스크 ≥ 120 GB(베이스 bf16 29.5 + 병합 fp16 29.5 + f16 GGUF 29.5 + Q4_K_M 8.4 GB + HF 캐시), merge_gguf_v5.sh의 WORK_DIR·HF_HOME·DROP_HF_CACHE=1 그대로. RAM이 모자라면 GPU 위 bf16 병합으로 바꾸고 v5 구성과의 차이를 기록한다.

배포 판단은 채택 뒤 별도 승인이다. 14B는 로컬 CPU에서 정책당 2배 이상 느려 데모 시나리오(12장면) 사전 분류 시간이 늘어나고, GPU가 없는 현재 PC에서는 실시간 데모용으로는 7B가 유리하다.

## 6. 2단계 실행 계획 (1단계 승인 2026-11-04, 학습 전 사전 기록)

- 베이스 `unsloth/Qwen2.5-14B-Instruct-bnb-4bit` 확정. 스크립트 `training/lora/runpod/run_train_v6c.py` = run_train.py에서 `HP['base_model']`만 교체(그 외 HP·마스킹·디코딩 동일), DATASETS는 data_v5 그대로(해시 `39c302c5…` 게이트, test_v5 manifest `57fd384f…` 게이트, 프롬프트 `d0913c27…`), run 이름 `lora_v6c_s{seed}`, 예측은 행 단위 append·id 기준 resume, env.json에 베이스 모델명, train_result.json에 피크 GPU 메모리·trainable 파라미터·padding_free, 파일별 .timing.json에 시간·메모리. preflight는 14B 로드(48층·hidden 5120 assert) + 짧은 generate + 메모리(logs/preflight.json).
- **조기 판정(사전 고정)**: s42 test_v5 oas_code macro-F1 ≤ 0.6661(v5 s42, scores_test_v5.json)이면 s43·s44·base zero-shot 미실행, 불채택, Pod 정지. `runpod/early_gate_v6c.py`가 번들의 `baseline/v5test_predictions_oas_code_lora_v5_s42_final.jsonl`을 같은 코드(scripts/eval_combined_v5.py 정의)로 재채점해 0.6661을 재현한 뒤 비교한다(자체 검사: 기준 파일 대 기준 파일 → 0.6661 = 0.6661, GATE=STOP).
- **채택 기준(사전 고정, 3 seed 평균)**: S5와 같은 3조건 — (1) test_v5 oas_code macro-F1 ≥ v5 + 0.016(v5 0.683 ± 0.016), (2) test_v30 207 구체 정밀도 하락 ≤ 0.025(v5 0.796 ± 0.025), (3) test_v30 207 public 오판(/35) 평균 ≤ 2.0(v5 2.0). **불채택이면 v5를 최종 모델로 확정(S9 대상)**.
- 평가: test_v30(oas·oas_code 269/265) + test_v31_supp(oas·oas_code 222) + test_v5(oas·oas_code 283), 3 seed, 기본 디코딩(greedy, 256 토큰, 배치 8). base 14B zero-shot(어댑터 없음, 6작업)은 조기 판정 통과 시에만 s44 뒤 마지막에 1회이며 채택 판정에 쓰지 않는다. test_v6 추론 금지.
- 순서(`runpod/run_v6c.sh`, 자동 정지): 0 해시 → 1 setup.sh → 2 preflight → 3 s42 학습·평가 → pack → 조기 판정(early_gate.json, 재pack) → (통과 시) 4 s43 → 5 s44 → 6 base zero-shot → 7 전체 tar → `runpodctl stop pod`. seed마다 `export/blade_v6c_lora_v6c_s<seed>_results.tar.gz`·`_adapter.tar.gz`(+ RETRIEVE_CMD 회수), 학습 체크포인트(30 step)·예측 행 단위 resume. 어느 단계든 실패하면 있는 결과를 묶고 Pod를 정지한다.
- 번들 `export/blade_v6c_20261104.tgz` SHA-256 `7ff028004fc43b242ea6d72409bcf0b220c3ba00c5d43f2021c0631e577a8b16`(633,841 bytes): data_v5 8파일(동결본과 바이트 동일: train_sft_v5·val_sft_v5·test_v30_inputs·test_v31_supp_inputs·test_v5_inputs·test_v5_manifest.json·policy_label_v3.0.1.md·data_v5_hashes.json) + runpod 5파일(run_train_v6c.py·run_v6c.sh·early_gate_v6c.py·setup.sh·README_v6c.md, LF, `bash -n`·py_compile 통과) + baseline 1파일 + SHA256SUMS_bundle. 실행 절차 `training/lora/runpod/README_v6c.md`. test_v31_supp_inputs.jsonl(Flowise 코드 포함)이 들어 있으므로 번들은 공개·커밋하지 않는다.
- 3단계: 전 결과 회수 후 reports/eval/lora_v6c/report.md(v5 병기, scripts/eval_v30.py·eval_v31_supp.py·eval_test_v5.py 같은 채점기, 실측 시간·메모리, 조기 판정 기록, GGUF 병합 Pod 요건) 보고 후 정지. 커밋 없음.
