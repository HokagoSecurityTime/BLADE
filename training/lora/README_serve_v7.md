# LoRA v7 서빙 (Ollama, blade-qwen-lora-v7) — 작업 D1 배포 전환 (C-5 절차 그대로, 2026-11-10 준비)

LoRA v7 s42 final 어댑터를 unquantized Qwen2.5-7B-Instruct에 병합하고 GGUF Q4_K_M으로 변환해 Ollama에 등록한다. v5(README_serve_v5.md)·v4와 같은 구성이며 학습은 하지 않는다. **v5 모델(blade-qwen-lora-v5)은 롤백용으로 남긴다.** 커밋 금지(결과 보고 후 정지).

| 항목 | 값 |
|---|---|
| 어댑터 | lora_v7_s42 final (`blade_v7_lora_v7_s42_adapter.tar.gz` SHA-256 `9dc03740ab13352e18ff955ad92f40ab0b1dfc4c808481082261621f4c2560ff`; adapter_model.safetensors SHA-256 `66c68a58b81a859ea77b9ccfe7d88716c3223f78a8a050754955d70e25184777`; r16·α16·7모듈, base_model unsloth/Qwen2.5-7B-Instruct-bnb-4bit) |
| 베이스(병합용) | `Qwen/Qwen2.5-7B-Instruct` 리비전 `a09a35458c702b33eeacc393d103063234e8bc28` (bf16, 4bit 아님) — v4·v5와 동일 |
| 병합 | 196개 텐서(28층 × 7모듈), fp32 `W + (alpha/r)·B·A` → fp16 체크포인트 → f16 GGUF → llama.cpp b11693 Q4_K_M (runpod/merge_gguf_v7.sh, 컨테이너 디스크) |
| 데이터(해시 게이트) | data_v7/data_v7_hashes.json `bd33f1bc…`, test_v30_inputs.jsonl `d65f25b9…`(265 oas_code), val_sft_v7.jsonl `2173171e…`(159), policy_label_v3.0.1.md `d0913c27…` |
| 토크나이저·템플릿 | 어댑터의 tokenizer.json, tokenizer_config.json, chat_template.jinja (7B와 동일) |
| Modelfile | training/lora/Modelfile.blade-qwen-lora-v7 — TEMPLATE·PARAMETER는 v5·v4와 바이트 동일(FROM 파일명만 다름) |
| 결과 기록 위치 | reports/eval/lora_v7_gguf/ (merge_manifest_v7_s42.json, SHA256SUMS_gguf_v7_s42, merge.log, quantize.log, c7.log, predictions·val_predictions, template_check.log, scores_test_v30.json, equivalence_numbers.json, equivalence_check.md, threshold_val_v7.json, pipeline_compare.*) |

## 사전 기록 (GGUF 결과를 보기 전에 고정, 2026-11-10)

- **변환 동등성 판정**: 같은 어댑터(s42) HF final 예측(reports/eval/lora_v7/lora_v7_s42/eval/predictions_oas_code_lora_v7_s42_final.jsonl)과 비교. 지표는 v5 때와 같은 3개 — 주지표 macro-F1 합성 제외 207, 합성 제외 구체 정밀도 207, 구체 정밀도 265. **허용 폭은 "v5 때와 같은 허용 폭"(사용자 지시)을 v5 검사에 실제 적용했던 수치, 즉 LoRA v4 3-seed sd(0.0454 / 0.0255 / 0.0175)로 읽는다.** v5 3-seed sd(0.0104 / 0.0252 / 0.0197)와 v7 3-seed sd(0.0187 / 0.0200 / 0.0150)는 병기한다(두 해석이 갈리면 사용자 확인). 세 지표 모두 폭 안이면 "수용 제안", 아니면 v4·v5 때처럼 보류 비율 이동 여부를 보고 "조건부 수용 제안". 채점 scripts/eval_v30.py → scripts/equivalence_check_v7.py.
- **MIN_CONFIDENCE**: val_sft_v7(159)만 사용, `choose_threshold_v4.py --rule precision`(v5·v4와 같은 규칙: val 구체 정밀도 최대, 동률이면 낮은 문턱, 기존 바닥 0.7). test로 고르지 않는다.
- **런타임 코드 수정 없음**: 모델명·문턱은 `BLADE_LORA_MODEL`·`BLADE_LORA_MIN_CONFIDENCE` 환경변수로만 전환. pipeline/classifier/lora.py 기본값(blade-qwen-lora-v4, 0.9)은 그대로.
- 발표·보고서 성능 수치는 LoRA v7 3-seed(HF) 평가(reports/eval/lora_v7/presentation_numbers_v7.md)를 유지하고, GGUF 수치는 "배포 모델 변환 동등성 확인"으로만 표기한다.

## 1. Pod (사용자 실행) — GGUF + 동등성·문턱 추론

Pod 사양(사용자 지시 2026-11-10): GPU 1개, **RAM ≥ 64 GB**(fp32 병합; C-5 때 20 GB Pod에서 양자화 중 사망), **컨테이너 디스크 ≥ 80 GB**(임시 30 GB + llama.cpp 빌드 + Ollama blob), 볼륨은 `/workspace`(사용자 확인 2026-11-10: `/workspace-2` 아님; 스크립트는 둘 다 받아들이고 `BASE=<경로>`로 임의 지정도 가능). **번들 하나만 있으면 되고 기존 스토리지 내용은 필요 없다** — 베이스 모델(HF)·llama.cpp·패키지·Ollama는 스크립트가 받는다. run_c7.sh가 시작 시 RAM(≥ 60 GB 표시값)·컨테이너 디스크(≥ 70 GB 여유)·볼륨 경로·어댑터/데이터 해시를 검사하고 미달이면 멈춘다.

번들 `export/blade_c7_v7_20261110.tgz`(SHA-256은 export/blade_c7_v7_20261110.tgz.sha256): `runs/lora_v7_s42/adapter/`(어댑터 6파일), `data_v7/`(hashes·test_v30_inputs·val_sft_v7·prompt), `runpod/{setup_c5.sh, merge_gguf_v7.sh, run_c7.sh}`, `eval_ollama_v7.py`, `Modelfile.blade-qwen-lora-v7`, `README_serve_v7.md`, `SHA256SUMS_bundle`.

```bash
# 새 볼륨(/workspace): 번들 전체를 푼다 — 다른 파일 불필요
mkdir -p /workspace/blade_c7 && cd /workspace/blade_c7 && tar -xzf /path/to/blade_c7_v7_20261110.tgz
# (참고) v7 학습 볼륨(blade_lora_v3)이 붙은 Pod라면 그 디렉터리에서 --exclude='runs/*' --exclude='data_v7/*'로 스크립트만 덮어써도 된다(해시로 검증됨)
sha256sum -c SHA256SUMS_bundle | tail -3          # 모두 OK
bash runpod/setup_c5.sh                           # pip(transformers·peft·httpx·cmake)·tmux·Ollama 설치 — Pod 시작 때마다
tmux new -d -s c7 "BASE=$PWD bash $PWD/runpod/run_c7.sh"
tail -f $PWD/export/c7.log
```

순서: 게이트(RAM·디스크·경로·해시) → a) 병합·f16·Q4_K_M(컨테이너 디스크 `/root/c7`, DROP_HF_CACHE=1) → `ollama create blade-qwen-lora-v7` → b) `--check-template 3`(HF 템플릿 토큰 수 = Ollama prompt_eval_count assert) + test_v30 oas_code 265건 → c) val_sft_v7 159건 → 결과 tar → 60초 뒤 Pod 자동 정지(STOP_POD=0이면 유지). 예상 약 40~50분(설치 5, 베이스 다운로드 3~5, 병합 5, f16 3, Q4 5~10, 추론 10~15). 양자화 중 죽으면 quantize_resume_c5.sh를 v7 경로로 바꿔 재개(f16은 `/root/c7/work`에 남음; 컨테이너 재시작이면 소실되어 처음부터).

가져올 파일: `export/gguf/blade-qwen-lora-v7-s42-Q4_K_M.gguf`(약 4.7 GB — zip으로 싸지 말고 **원본 파일 그대로** 받는다, 아래 로컬 디스크 제약), `export/blade_c7_v7_results.tar.gz`(manifest·SHA256SUMS_gguf_v7_s42·merge.log·quantize.log·gguf_eval/*·c7.log), `export/SHA256SUMS_c7`.

## 2. 로컬 (C:\BLADE) — 채점·문턱·등록·검증

### 2.0-결과 (2026-11-10): GGUF 조건부 수용 확정 · MIN_CONFIDENCE 0.9 · blade-qwen-lora-v7 등록

- 동등성: macro-F1 207 −0.007(폭 안), 구체 정밀도 207 −0.032(폭 0.0255 이탈), 265 −0.025(폭 0.0175 이탈), public 오판 1 → 3, manual 22.6% → 23.4%, 행 일치 229/265. v5·v7 sd로 읽어도 같은 1/3. **사용자 조건부 수용 확정** — 조건과 한계 기록은 reports/eval/lora_v7_gguf/equivalence_check.md 머리글, reports/eval/lora_v7/report.md 6절, presentation_numbers_v7.md. GGUF 경로 confidence는 test 261/265가 0.9라 문턱이 실질적으로 거르는 행 0건(한계로 명시). 운영 조건: public 판정 정책은 승인 시 우선 검토.
- 문턱: val_v7 `--rule precision` → 0.9(threshold_val_v7.json). 등록: GGUF를 `<USERPROFILE>\.ollama\models\blobs\sha256-1dd24dcd…`로 이동 후 `ollama create blade-qwen-lora-v7 -f training/lora/Modelfile.blade-qwen-lora-v7.local`(복사 없음, 응답 "OK" 9 s). ollama list: blade-qwen-lora-v7 · blade-qwen-lora-v5(롤백) · qwen2.5:7b. C: 여유 6.1 GB.
- 2.2·2.3의 `/generate` 입력은 v5 데모와 같은 `openapi_clean.json`(Intended 힌트 제거본, H_demo_runbook 1-7)을 쓴다. 작업 폴더 `verification/demo_v7_runtime/`(env.sh = v5 env.sh에서 폴더·모델명만 변경, demo.db 바이트 동일 `80b4882d…`).

### 2.0 사전 조건 (2026-11-10 확인)

- **디스크**: C: 여유 7.6 GB. 필요: v7 GGUF 4.7 GB + `qwen2.5:7b` 4.7 GB(2-b 파라미터·roles 추출용, verify_lora_pipeline·admin /generate에 필수인데 **현재 로컬 Ollama에 없음**; 등록된 모델은 blade-qwen-lora-v5 하나) = 9.4 GB → **약 2 GB 이상 비워야 한다.** 후보: `<USERPROFILE>\Downloads\GGUF_v5.zip`(4.6 GB; 내용물은 이미 Ollama blob `sha256-29350296…`로 등록된 v5 GGUF와 같은 파일이라 중복) — 삭제는 사용자 결정.
- GGUF는 Ollama blob 이름으로 두면 `ollama create`가 복사 없이 재사용한다(v5와 같은 방법): `<USERPROFILE>\.ollama\models\blobs\sha256-<Q4 SHA-256>`.

```powershell
# 받은 파일 배치
# results tar → reports\eval\lora_v7_gguf\ 에 풀기 (gguf\merge_manifest_v7_s42.json 등은 디렉터리 평탄화해 두기)
certutil -hashfile <다운로드>\blade-qwen-lora-v7-s42-Q4_K_M.gguf SHA256        # SHA256SUMS_gguf_v7_s42와 일치 확인
move <다운로드>\blade-qwen-lora-v7-s42-Q4_K_M.gguf $env:USERPROFILE\.ollama\models\blobs\sha256-<Q4 SHA-256>
# Modelfile 복사본의 FROM을 그 blob 경로로 바꿔 등록 (TEMPLATE·PARAMETER는 training\lora\Modelfile.blade-qwen-lora-v7 그대로)
ollama create blade-qwen-lora-v7 -f training\lora\Modelfile.blade-qwen-lora-v7.local
ollama pull qwen2.5:7b                                                            # roles/파라미터 추출 모델(없으면 lora 경로 roles 추출 실패)
ollama list                                                                       # blade-qwen-lora-v7, blade-qwen-lora-v5(유지), qwen2.5:7b

# 채점 (test_v30 oas_code: GGUF vs 같은 어댑터 HF s42)
.python\python.exe -X utf8 scripts\eval_v30.py --pred reports\eval\lora_v7_gguf\predictions_oas_code_lora_v7_s42_gguf_q4km.jsonl reports\eval\lora_v7\lora_v7_s42\eval\predictions_oas_code_lora_v7_s42_final.jsonl --out reports\eval\lora_v7_gguf\scores_test_v30.json --md reports\eval\lora_v7_gguf\eval_v30.md
.python\python.exe -X utf8 scripts\equivalence_check_v7.py --scores reports\eval\lora_v7_gguf\scores_test_v30.json --gguf reports\eval\lora_v7_gguf\predictions_oas_code_lora_v7_s42_gguf_q4km.jsonl --hf reports\eval\lora_v7\lora_v7_s42\eval\predictions_oas_code_lora_v7_s42_final.jsonl --template reports\eval\lora_v7_gguf\template_check.log
# 문턱 (val_v7만)
.python\python.exe -X utf8 training\lora\choose_threshold_v4.py --rule precision --pred reports\eval\lora_v7_gguf\val_predictions_lora_v7_s42_gguf_q4km.jsonl --out reports\eval\lora_v7_gguf\threshold_val_v7.json
```

### 2.1 파이프라인 전환 (환경변수만)

```powershell
$env:BLADE_CLASSIFIER = 'lora'
$env:BLADE_LORA_MODEL = 'blade-qwen-lora-v7'            # 롤백: 'blade-qwen-lora-v5'
$env:BLADE_LORA_MIN_CONFIDENCE = '<threshold_val_v7.json chosen>'
$env:BLADE_LLM_PROVIDER = 'ollama'; $env:BLADE_LLM_MODEL = 'qwen2.5:7b'   # 빠지면 roles 추출 실패(v5 때 재현)
# 종단간 검증(정책 생성 → 승인 → 프록시 요청) + 전체 테스트
$env:BLADE_VERIFY_OUT = 'reports/eval/lora_v7_gguf'
.python\python.exe -X utf8 scripts\verify_lora_pipeline.py        # → reports/eval/lora_v7_gguf/pipeline_compare.{json,md}; v5 기록(lora_v5_gguf)은 불변
.python\python.exe -m pytest tests                                   # 2026-11-10 전환 전 기준선: 397 passed, 1 skipped (34.7 s)
```

### 2.2 attack_sim 재측정 (탐지율·오탐율·p95)

로컬 프로세스 3개를 띄우고(verification/demo_v5_runtime/env.sh의 변수에 BLADE_LORA_MODEL만 v7로) 데모 정책을 v7로 생성·승인한 뒤 기존 CLI를 같은 인자로 돌린다. 결과는 METRICS.md를 덮어쓰지 않고 `verification/remeasure_v7_<date>/`에 쓴다.

```bash
# bash (Git Bash), C:/BLADE — 터미널 3개 또는 백그라운드
source verification/demo_v5_runtime/env.sh; export BLADE_LORA_MODEL=blade-qwen-lora-v7; export BLADE_LORA_MIN_CONFIDENCE=<chosen>
.python/python.exe -m uvicorn demo_backend.main:app --port 9000 &      # 데모 백엔드(인가 없음)
.python/python.exe -m uvicorn admin_api.main:app --port 8100 &         # 관리 API(정책 생성·승인)
.python/python.exe -m proxy.server &                                   # 프록시 8080 (BLADE_TARGET_URL·BLADE_ADMIN_URL·BLADE_DB_DSN·BLADE_JWT_SECRET는 env.sh)
curl -s -X POST http://127.0.0.1:8100/generate -F oas=@demo_backend/openapi.json -F erd=@demo_backend/schema.sql -F controller=@demo_backend/main.py   # 7건, CPU 약 10분
for id in $(curl -s http://127.0.0.1:8100/policies | .python/python.exe -c "import json,sys;print(' '.join(p['id'] for p in json.load(sys.stdin)))"); do curl -s -X POST http://127.0.0.1:8100/policies/$id/approve >/dev/null; done
.python/python.exe -X utf8 scripts/d1_remeasure_v7.py -n 20            # attack_sim --prepare-demo -n 20 + 백엔드 직접 280건 → verification/remeasure_v7_<date>/METRICS_v7.md
```

### 2.3 데모 사전 생성 정책 — v5 생성본이므로 D1 후 v7로 재생성 (2026-11-10 확인)

- `verification/demo_v5_runtime/policies/*.yaml` 7건은 **blade-qwen-lora-v5**가 생성했다(각 YAML `evidence` 첫머리 `[blade-qwen-lora-v5 policy-label-v3.0.1 …]`, env.sh `BLADE_LORA_MODEL=blade-qwen-lora-v5`). `demo_backend/portal_policies/*.yaml` 4건(다른 세션의 포털 데모)은 `source: manual`이라 모델 생성본이 아니며 그대로 둔다.
- 재생성 절차(2.2의 `/generate`가 이 역할): v7 환경변수(2.1)로 admin_api를 띄운 뒤 `/generate` → 전부 `approve` → `GET /policies`를 `verification/demo_v7_runtime/policies/`에 YAML로 저장하고 `verification/demo_v7_runtime/env.sh`(v5 env.sh에서 모델·문턱만 변경)를 둔다. v5 생성본 디렉터리는 기록으로 보존하고 수정하지 않는다. 생성된 label이 v5와 다른 엔드포인트는 `pipeline_compare.md`와 `METRICS_v7.md`에 표로 남긴다.
- **2.3 결과(2026-11-10 11:15–11:18 UTC, 사용자 확정: v7 생성본 사용, v5 생성본·힌트 입력으로 바꾸지 않음)**: 7건 전부 승인(regen.log). v5 생성본 대비 2/7 변경 — `GET /admin/reports` role_required → manual, `GET /orders/{orderId}` owner_match → manual(보류 방향). 나머지 5건(DELETE /orders owner_match·orgs tenant_match·users tenant_match·public·premium manual) 동일. 2.2 attack_sim 재측정은 생략(사용자 결정; 발표는 Phase 1 프록시 집행 / test_v6 모델 판정 분리 표기).
- **재현성(2026-11-10 11:48–11:51 UTC, repro/rerun_2.sh)**: 바뀐 2건(GET /admin/reports, GET /orders/{orderId})만 같은 ERD·핸들러·OAS 항목(부분 파일 openapi_clean_2.json)으로 새 저장소(admin 8103)에서 재생성 → 2/2 같은 label(manual_review_required 0.9), rationale 문구도 동일(repro/rerun_2.log).
- **데모 시나리오 확인(2026-11-10 11:25 UTC, scenario_manual_to_owner.sh, 저장소 복사본에서 실행)**: ACTIVE manual 정책에서 BOLA `GET /orders/1042`(user_99)가 200 통과(OBSERVE) → `POST /policies/{id}/rollback`(ACTIVE→PENDING) → `PUT /policies/{id}`(label owner_match + params.object_param orderId + owner_lookup orders.id/user_id, source manual) 200 → `approve` 200 ACTIVE → 폴링(5 s) 뒤 같은 요청 **403**, 소유자 user_77 200, 무토큰 403. 현재 코드로 동작한다. 비고: 관리자 웹 화면은 저장소에 없고(admin_api는 API만) 수정은 PUT 전체 본문(PolicyUpdate, extra 금지)으로 한다. Phase 2 비활성이라 version은 1 유지(증가는 BLADE_PHASE2_ENABLED=true일 때만). 로그 scenario_manual_to_owner.log.
- **포트 선점 주의(2026-11-10 확인)**: 127.0.0.1:8080·8100·9000이 다른 세션의 포털 데모 프로세스(admin_api에 portal 정책 4건 ACTIVE)로 이미 점유돼 있다. 2.2 실행 전 그 프로세스를 멈추거나(사용자 확인), 세 서비스를 다른 포트(예: 9001·8101·8081)로 띄우고 `d1_remeasure_v7.py --proxy/--admin/--backend`에 같은 포트를 넘긴다. 포털 데모의 admin_api(8100)에 `/generate`를 보내면 그쪽 정책 저장소가 섞이므로 금지.

비교 기준: verification/METRICS.md(2026-10-31 Docker: 탐지율 83.33%(6종)·오탐 0%·p95 +2.0 ms), remeasure_20261031.md(Phase 1 로컬 프로세스 +1.6 ms). 이번은 로컬 프로세스 측정이므로 Phase 1 조건과 비교한다. 프록시 지연은 정책 집행 경로의 비용이라 모델 버전과 무관하고, 탐지율·오탐율은 v7이 생성한 정책 label(특히 GET /users/{userId} owner_or_admin, GET /premium/content)에 따라 달라질 수 있다.

## 3. 롤백

`BLADE_LORA_MODEL=blade-qwen-lora-v5`(문턱 0.9)로 되돌린다. blade-qwen-lora-v5 blob(`sha256-29350296…`, 4.68 GB)은 지우지 않는다.
