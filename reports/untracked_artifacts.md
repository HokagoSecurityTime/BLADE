# Git 미추적 산출물 기록 (2026-10-21, Codex → Claude 인수 시점)

`.gitignore`로 제외했지만 재현·검증에 필요한 파일의 경로와 SHA-256을 기록한다.
원격 저장소에는 올라가지 않으므로 로컬 `C:\BLADE` 또는 별도 백업에서만 확보 가능하다.

## 1. 대용량 LLM 원시 응답·중간 산출물 (datasets/blade/processed/)

| 파일 | 크기(bytes) | 수정일 | SHA-256 |
|---|---:|---|---|
| apisguru_labeled_v3_openai.jsonl | 53,901,340 | 2026-10-19 | 52e41e56b06f1bc2d116070a254b5caca43a30e5d0e5f2e2ae70a1aae9daf796 |
| apisguru_labeled_v5_openai.jsonl | 54,255,005 | 2026-10-19 | 1c3c6d38fc31c8e9274024f5a60f0dcd03007099684debbb6f4ccf1feffb108e |
| apisguru_v3_openai.partial.jsonl | 53,899,313 | 2026-10-19 | bef96a8b29594e6a48d7225a08bb7ab30a5a4e312a49f14bb5f186bbe2745222 |
| apisguru_v5_openai.partial.jsonl | 54,252,978 | 2026-10-19 | d30a504e62a1bfea707de009d0d941beefc5794b6ff66bc2e686d3f099f5fbc9 |
| apisguru_enriched_v2.jsonl | 52,338,006 | 2026-10-19 | ed6e2b2d36f0edc57ceb8878e0e2b67bf8b7a5f7a57a11499aba132bb56dd0f5 |
| train_before_v6.jsonl | 27,332,056 | 2026-10-19 | bc011f12a457209fad187eef7e65fad532623bbef47b143210c2cccad935894d |
| apisguru_manual_pool.jsonl | 26,889,093 | 2026-10-20 | 9216db8fcb99ffd1c3a2cea905f9c5d5bce36894bea2e2df273f37824e4822e1 |

참고(추적 대상, 대조용):

| 파일 | 크기(bytes) | SHA-256 |
|---|---:|---|
| test.jsonl (frozen) | 519,594 | bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa |
| train.jsonl | 10,009,907 | 890278f9556b6ee7f17211790d294baafada52765219fdd7d9496e2a38a6d879 |
| val.jsonl | 10,162,161 | d077bea7abe00407ae61b6f858b8f786a470c2eb280b4bcbf4e8b12cb02b3181 |

## 2. 외부 Git 클론 (datasets/blade/raw/) — 경로와 HEAD 커밋

| 경로 | 원본 | HEAD |
|---|---|---|
| datasets/blade/raw/openapi-directory | https://github.com/APIs-guru/openapi-directory.git | f04b8d0bcd39c52e1cf3ad7a5fe744709832ae49 |
| datasets/blade/raw/vuln_apis/DVWS-node | https://github.com/snoopysecurity/dvws-node.git | eb6e2886f2206b88bf709fe1fa311adc3ae3c34f |
| datasets/blade/raw/vuln_apis/Pixi | https://github.com/DevSlop/Pixi.git | cb716a94fa368acade96e9bdb8b25c1a68703e60 |
| datasets/blade/raw/vuln_apis/VAmPI | https://github.com/erev0s/VAmPI.git | f16052dce83f05847133ec98f01c5193a41de7d8 |
| datasets/blade/raw/vuln_apis/crAPI | https://github.com/OWASP/crAPI.git | b5fc307f3e5f875809b095b771108ef342a33724 |
| datasets/blade/raw/vuln_apis/juice-shop | https://github.com/juice-shop/juice-shop.git | 399fba76194305a312693eee44f4df64bdf0c3ce |

소규모 raw 하위 폴더(synthetic, adapter_v3_holdout, external_paired_v29, external_conditions_v1, paired_policy_v1, self_account_sql_v1, source_pilot_wfd, apisguru_candidates.jsonl)는 추적 대상에 포함했다.

## 3. 모델 가중치·LoRA 어댑터

- **LoRA 어댑터 파일(adapter_config.json, adapter_model.*, *.safetensors, *.gguf, Modelfile)은 2026-10-21 기준 `C:\BLADE` 어디에서도 발견되지 않았다.** `training/checkpoints/`, `training/models/` 디렉토리도 존재하지 않는다. 프로젝트 내 "어댑터 v3"는 `training/experiments/adapter_v3.py` 등 코드 기반 조건 추출 어댑터를 가리킨다(2단계 인수인계 확인에서 상세 보고).
- 임베딩 모델 캐시: `.cache/models/models--intfloat--multilingual-e5-small/` (HF 스냅샷 614241f622f53c4eeff9890bdc4f31cfecc418b3, model.safetensors 470,641,600 bytes). 재다운로드 가능하므로 해시 생략.
- `.ollama/`는 Ollama 런타임 바이너리 디렉토리(모델 매니페스트 없음).

## 4. 벡터 인덱스·DB·런타임 산출물 (재생성 가능, 경로만 기록)

- reports/eval/.rag_a, reports/eval/.rag_b, reports/eval/recorded/.rag_a, reports/eval/enriched_recorded/.rag_a (Chroma)
- verification/phase2/ablation-index, embedding-index, stage6-index, e2e-20261012-resumed/chroma (Chroma)
- verification/phase2/**/blade.db, demo.db, verification/presentation-runtime/*.db, 루트 blade.db·demo.db
- verification/video_tools/ (vendored av 패키지), verification/video-review/ (영상 프레임 PNG), verification/2026-09-14 11-28-25.mp4
- 설치 파일: OllamaSetup.exe, python-installer.exe, python311-setup.exe; 로컬 Python: .python/

## 5. 비밀정보

- `.env`는 제외. `.env.example`은 템플릿으로 추적 대상이나 인수 시점에 실제 키 값이 포함되어 있어 커밋 전 정리 필요(1단계 보고 참조). 값은 어디에도 기록하지 않는다.

## 6. 프롬프트 v3.x 전체 라벨링 원시 응답 (2026-10-21 추가, 추적 제외)

| 파일 | 크기(bytes) | SHA-256 |
|---|---:|---|
| reports/eval/classification_quality/prompt_v301_full/raw_responses.jsonl | 25801369 | 07434fb76972222511bc97f66c2384c7f9966b4c324d96bd278635f60ee3aa77 |

커밋 940045e에 한 번 포함된 뒤 다음 커밋에서 인덱스 제거(히스토리 재작성·force push는 금지 규칙이라 blob은 히스토리에 남음). 요약본은 datasets/blade/processed/apisguru_labeled_v301.jsonl(추적)에 있다.

## 7. 삭제한 로컬 클론 (2026-10-21, 발췌 완료 후 삭제; 재현은 각 manifest의 reproduce 참조)

| 경로 | 원본 | 커밋 | 레코드 |
|---|---|---|---|
| datasets/blade/raw/opensource/gitea | go-gitea/gitea v28.2.0 | 829b49c1ae96015e345f9d2a0eb1ea7acd5f31e1 | processed/opensource/gitea_v28.2.0_endpoints.jsonl |
| datasets/blade/raw/opensource/netbox | netbox-community/netbox v4.7.3 | 3cd2c1d6469caed6c50e80eddd4cde863e0e2cf5 | processed/opensource/netbox_v4.7.3_endpoints.jsonl |
| datasets/blade/raw/vuln_apis/vAPI | roottusk/vapi | 67152695b0acf13dd424905729080fbc80d5a593 | processed/test_v2_extra_candidates.jsonl |
| datasets/blade/raw/vuln_apis/DVRestaurant | theowni/Damn-Vulnerable-RESTaurant-API-Game | d32d09972aec7830f5f1d4a5d274cac7aae7eb82 | processed/test_v2_extra_candidates.jsonl |

## 8. LoRA v1 어댑터 (Drive에만 존재, 2026-10-22)

- 경로: Google Drive `MyDrive/blade_lora_v1/runs/lora_v1_run1/adapter/` (+ `checkpoints/`). 로컬·git 미보관, SHA-256 미확인.
- 학습 입력 해시: reports/eval/lora_v1/hashes.json (data-v1과 일치). 재현: 같은 노트북(training/lora/lora_v1_colab.ipynb)·data-v1·seed 42.

## 9. LoRA v2 어댑터·체크포인트 (Drive에만 존재, 2026-10-24)

- 경로: Google Drive `MyDrive/blade_lora_v2/runs/lora_v2_seed{42,43,44}/adapter/` (+ `checkpoints/checkpoint-30…300`, `config.json`, `hashes.json`). 로컬·git 미보관, SHA-256 미확인(다운로드 폴더에 포함되지 않음).
- 로컬·git 보관: `reports/eval/lora_v2/lora_v2_seed*/eval/predictions_*.jsonl`(24개), `logs/train_log.jsonl`, `logs/train_result.json`. 채점 결과 `reports/eval/lora_v2/{scores.json,eval_v30.md,lora_v2_report.md}`.
- 학습 입력: `training/lora/data_v2/`(해시 data_v2_hashes.json, data-v2와 일치). 재현: `training/lora/lora_v2.ipynb`, seed 42·43·44.
