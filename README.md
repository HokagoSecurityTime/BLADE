# BLADE — API 인가 정책 자동 생성·런타임 집행

BLADE는 OpenAPI 명세·DB 스키마·(선택) 컨트롤러 코드로부터 엔드포인트별 **인가 정책(7종 라벨)** 을 LLM으로 생성하고, 사람이 승인한 정책을 **런타임 프록시**가 요청 단위로 집행해 BOLA/IDOR류 인가 결함을 차단하는 연구 프로토타입입니다.

> 이 저장소는 코드·평가 보고서·검증 기록을 담습니다. 학습·평가 데이터셋은 별도 저장소 **[BLADE-dataset](https://github.com/HokagoSecurityTime/BLADE-dataset)** 에 있습니다. 최종 모델 **LoRA v7**의 어댑터(seed 42·43·44)와 배포용 GGUF Q4_K_M은 [Release `lora-v7`](https://github.com/HokagoSecurityTime/BLADE/releases/tag/lora-v7)에 있습니다.

## 동작 개요

```
 OpenAPI(oas) + DDL(erd) [+ controller 코드]
          │  POST /generate (admin_api)
          ▼
 pipeline/parsers ─► pipeline/classifier (llm | lora) ─► pipeline/generator
          │           7종 라벨 + confidence + rationale        정책 YAML (PENDING)
          ▼
 사람 검토·승인 (dashboard / admin_api)  ─►  ACTIVE 정책
          │
          ▼
 proxy/ (aiohttp)  : JWT 검증 → 정책 매칭 → 소유자·역할·테넌트 조회 → PASS / OBSERVE / BLOCK(403)
```

정책 라벨 7종: `public`, `role_required`, `membership_required`, `tenant_match`, `owner_match`, `owner_or_admin`, `manual_review_required`(보류). 정의는 데이터셋 저장소의 프롬프트 v3.0.1(`training/data/prompts/policy_label_v3.0.1.md`)과 검수 규약 G1~G8(DATA_CARD)을 따릅니다.

## 저장소 구조

```
BLADE/
├─ pipeline/            오프라인 정책 생성: parsers(OAS·ERD·controller) → classifier(llm|lora) → generator, rag/
├─ admin_api/           정책 관리 API(FastAPI): /generate, /policies, /detections, 워커(alerts·explain·reanalysis)
├─ proxy/               런타임 인가 프록시(aiohttp): JWT 검증, ACTIVE 정책 평가, 조회 캐시, 탐지 로그
├─ common/              정책 스키마(Pydantic)·라벨 정의·Redis 유틸
├─ dashboard/           React/Vite 대시보드(정책 승인·롤백·YAML 편집·탐지 조회)
├─ demo_backend/        인가 검사가 없는 데모 백엔드(BOLA 재현용) + openapi.json·schema.sql
├─ prompts/             런타임 분류 프롬프트 v2.0·v2.1
├─ policies/            데모 정책 YAML 7개
├─ training/lora/       LoRA 학습·평가·GGUF 변환 스크립트, Ollama Modelfile(v4·v5·v7), RunPod 실행 스크립트, README_serve_v7.md
├─ training/experiments/ 정책 조건 추출·어댑터 실험 스크립트
├─ scripts/             데이터 구성·평가(eval_v30.py 등)·데모(demo.sh)·부하 테스트·공개 사본 빌드
├─ tests/               pytest (2026-11-10 기준 397 passed · 1 skipped)
├─ reports/eval/        베이스라인·LoRA v1~v7 평가 보고서·예측·점수(JSON), 불채택 실험(context_aug_v5·lora_v6a·v6c·v6d), lora_v7_gguf(배포 변환 동등성)
├─ reports/presentation_support/  발표 근거(프록시 재측정, 사례 분석)
├─ verification/        Phase 1·2 검증 기록(측정값·로그·스크린샷·METRICS.md)
├─ docs/                USAGE.md(상세 사용법·환경변수 전체), failure-modes.md, critical-path.md
└─ AGENTS.md / AGENT.md 작업 규약(데이터 동결 해시 포함) / 정책 YAML 스키마
```

## 빠른 실행 (로컬 uvicorn + Ollama)

요구 사항: Python 3.11, [Ollama](https://ollama.com) (분류용 LLM), Git Bash 또는 PowerShell. Docker Compose 한 줄 실행(`docker compose up -d && bash scripts/demo.sh`)은 [docs/USAGE.md](docs/USAGE.md)를 보세요.

```bash
# 0. 설치
python -m venv .venv && source .venv/Scripts/activate      # PowerShell: .venv\Scripts\Activate.ps1
pip install -e .
ollama pull qwen2.5:7b                                      # 분류기 기본 모델 (베이스라인)

# 1. 데모 백엔드 (인가 검사 없음, 포트 9000)
uvicorn demo_backend.main:app --port 9000

# 2. 정책 관리 API (포트 8100) — 다른 터미널
export BLADE_LLM_PROVIDER=ollama BLADE_LLM_MODEL=qwen2.5:7b
uvicorn admin_api.main:app --port 8100

# 3. 정책 생성 → 검토 → 승인
curl -F "oas=@demo_backend/openapi.json" -F "erd=@demo_backend/schema.sql" \
     -F "controller=@demo_backend/main.py" http://127.0.0.1:8100/generate
curl "http://127.0.0.1:8100/policies?status=PENDING"
curl -X POST http://127.0.0.1:8100/policies/pol_orders_get_by_orderId/approve

# 4. 런타임 프록시 (포트 8080) — 다른 터미널
export BLADE_JWT_SECRET='로컬에서 정한 32바이트 이상 시크릿' BLADE_DB_DSN='sqlite:///file:demo.db?mode=ro&uri=true'
python -m proxy.server
TOKEN=$(python -m proxy.mktoken user_1)
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8080/orders/1     # 소유자 → 200
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8080/orders/2     # 타인 → 403 BLOCK
```

LoRA 분류기(최종 모델 **LoRA v7**)로 전환하려면 Release `lora-v7`의 GGUF를 받아 Ollama에 등록한 뒤 환경변수만 바꿉니다. 런타임 코드 수정은 없습니다.

```bash
# Release 자산: GGUF는 GitHub 자산 2 GiB 제한 때문에 3조각(.part00~02)으로 나눠 있다 — 이어 붙인 뒤 해시를 확인한다
cat blade-qwen-lora-v7-s42-Q4_K_M.gguf.part00 blade-qwen-lora-v7-s42-Q4_K_M.gguf.part01 blade-qwen-lora-v7-s42-Q4_K_M.gguf.part02 > blade-qwen-lora-v7-s42-Q4_K_M.gguf
sha256sum blade-qwen-lora-v7-s42-Q4_K_M.gguf   # 1dd24dcdff60619d055277591b134f133a24a4cd62a9b51f3cec8abcdc88144d (4,683,073,504 bytes)
cp training/lora/Modelfile.blade-qwen-lora-v7 . && ollama create blade-qwen-lora-v7 -f Modelfile.blade-qwen-lora-v7
export BLADE_CLASSIFIER=lora BLADE_LORA_MODEL=blade-qwen-lora-v7 BLADE_LORA_MIN_CONFIDENCE=0.9
```

절차는 [training/lora/README_serve_v7.md](training/lora/README_serve_v7.md), Modelfile은 [training/lora/Modelfile.blade-qwen-lora-v7](training/lora/Modelfile.blade-qwen-lora-v7)입니다. 어댑터(PEFT, seed 42·43·44)는 `unsloth/Qwen2.5-7B-Instruct-bnb-4bit` 위에 그대로 로드해 HF로 평가할 수 있습니다(RunPod 스크립트 `training/lora/runpod/run_train_v7.py --eval-only`). 이전 모델 v5(`Modelfile.blade-qwen-lora-v5`)는 롤백용 기록입니다.

## 테스트

```bash
pytest                      # 전체 (LLM 호출 테스트는 BLADE_LLM_PROVIDER 미설정 시 skip)
pytest tests/test_evaluator.py tests/test_proxy_e2e.py
```

일부 테스트(`tests/test_dataset.py`, `tests/test_label_data.py`, `tests/test_synthetic_services.py`, `tests/test_vuln_review.py`, `tests/test_candidate_analysis.py`, `tests/test_eval_context.py`, `tests/test_lora_classifier.py`)는 데이터셋 저장소의 `datasets/` 경로를 읽습니다. 두 저장소를 같은 상위 폴더에 두고 `datasets/`·`training/lora/data_v*`를 링크하거나 복사하면 통과합니다.

## 평가 결과 요약 (최종 모델 LoRA v7, 3 seed 평균 ± sd, 기본 디코딩, 입력 oas_code)

| 평가셋 | 지표 | Base (Qwen2.5-7B-Instruct, 미학습) | LoRA v5 | **LoRA v7** |
|---|---|---:|---:|---:|
| **test_v6** (289, hold-out, v7 판정셋) | macro-F1 / 정확도 | 0.214 / 0.304 | 0.586 ± 0.006 / 0.606 ± 0.006 | **0.650 ± 0.016 / 0.661 ± 0.012** |
| test_v6 | 구체 정밀도 / public 오판(/265) | 0.425 / 36 | 0.688 ± 0.012 / 1.0 | **0.758 ± 0.038 / 0.3 ± 0.6** |
| test_v30 (207, 합성 제외; 회귀·안전 지표, 학습 미포함) | 구체 정밀도 / macro-F1 | 0.353 / 0.197 | 0.796 ± 0.025 / 0.374 ± 0.010 | **0.824 ± 0.020 / 0.398 ± 0.019** |
| test_v30 (207) | 정확도 / public 오판(/35) | 0.319 / 17 | 0.568 ± 0.010 / 2.0 ± 1.0 | **0.630 ± 0.015 / 1.3 ± 0.6** |

- v7 채택 근거(사전 등록 기준, v5 대비): test_v6 macro-F1 +0.064(기준 ≥ +0.016), test_v30 구체 정밀도 +0.028(기준 하락 ≤ 0.025), test_v30 public 오판 1.33(기준 ≤ 2.0). 발표 표와 근거 파일: [reports/eval/lora_v7/presentation_numbers_v7.md](reports/eval/lora_v7/presentation_numbers_v7.md), 보고서 [reports/eval/lora_v7/report.md](reports/eval/lora_v7/report.md)(1단계)·[reports/eval/lora_v7/s9/report.md](reports/eval/lora_v7/s9/report.md)(S9 판정). 이전 모델 v5의 test_v5·test_v31_supp 수치는 [reports/eval/lora_v5/presentation_numbers_v5.md](reports/eval/lora_v5/presentation_numbers_v5.md)에 보존(두 셋은 data-v7부터 학습 데이터라 v7 수치 없음).
- 불채택 실험(모두 사전 기준 미달): S4 문맥 보강(`reports/eval/context_aug_v5/`), S5 v3.1 프롬프트 + 근거 먼저 출력 + 토큰 확률 confidence(`lora_v6a/`), S8 14B 베이스(`lora_v6c/`), C′ 학습 정답 36건 교정(`lora_v6d/`).
- 프록시 집행 성능(현재 코드, Docker): 탐지 5종 100%·6종 83.33%, 오탐 0/140, p95 추가 지연 +2.0 ms — [verification/METRICS.md](verification/METRICS.md).
- 평가 정의(eval-def v2)는 `scripts/eval_v30.py`, hold-out 채점은 `scripts/eval_test_v6.py`(`BLADE_TESTV6_STAGE=S9` 가드)·`scripts/eval_test_v5.py`. 채점에 필요한 정답 파일은 데이터셋 저장소에 있습니다.

## 데이터셋·모델

- 데이터셋 저장소: **[BLADE-dataset](https://github.com/HokagoSecurityTime/BLADE-dataset)** — data-v1~v7 학습 데이터(공개 사본), test_v30·test_v31_supp·test_v5·test_v6 평가셋, 프롬프트 v3.0.1, 라벨링 규약(G1~G8), 공개 사본과 복원 스크립트. 동결 파일 SHA-256은 [AGENTS.md](AGENTS.md)와 DATA_CARD에 있습니다.
- 모델 가중치: **[Release `lora-v7`](https://github.com/HokagoSecurityTime/BLADE/releases/tag/lora-v7)** — LoRA v7 어댑터 3개(seed 42·43·44, PEFT safetensors, 각 ≈ 152 MB; SHA-256은 [reports/eval/lora_v7/SHA256SUMS_blade_v7](reports/eval/lora_v7/SHA256SUMS_blade_v7)) + 배포용 GGUF Q4_K_M(s42 병합, 3조각, SHA-256 `1dd24dcd…`; 변환 기록 [reports/eval/lora_v7_gguf/](reports/eval/lora_v7_gguf/)). 베이스 Qwen2.5-7B-Instruct(Apache-2.0)의 고지는 Release 노트에 있습니다. v4·v5 가중치는 공개하지 않습니다(기록만 `reports/eval/lora_v5_gguf/`).
- **평가는 HF 어댑터 기준, 배포는 Q4_K_M GGUF**: 배포 GGUF는 같은 어댑터 HF s42 대비 test_v30 207 구체 정밀도 −0.03, public 오판 +2(crAPI owner_match 2건)이며 사전 허용 폭을 벗어나 조건부 수용(2026-11-10). GGUF 경로의 confidence는 265건 중 261건이 0.9 고정이라 `BLADE_LORA_MIN_CONFIDENCE=0.9`가 실질적으로 거르는 행은 0건입니다 — [reports/eval/lora_v7_gguf/equivalence_check.md](reports/eval/lora_v7_gguf/equivalence_check.md).

## 알려진 한계

- 정책 생성은 엔드포인트별 순차 LLM 호출이며 CPU Ollama 기준 1건 수십 초가 걸립니다(비동기 작업 큐 없음).
- 프록시는 SQLite 읽기 전용 조회와 HS256 JWT만 지원하며, `membership_required`의 그룹 구성원 조회는 런타임에 집행하지 않습니다(manual 처리).
- test_v30에서 security 선언이 있는 엔드포인트를 public으로 오판하는 사례가 남아 있습니다(v7 3 seed 1/1/2 건, 배포 GGUF 3건). 운영에서는 public 판정 정책을 승인 시 우선 검토합니다. 상세는 reports/eval/lora_v7/report.md 6절.
- test_v6 정답의 75%(217/289)는 AI 단독 판정이고 사람 확정은 5건입니다(A안, 마감 사유). 모델 간 상대 비교는 같은 정답·입력·환경이라 유효하지만 절대 수치에는 정답 오류가 포함됩니다. Redash G1-b 경계 18건은 모든 모델이 0/18(tenant_match → role_required 예측).
- data-v7 학습 라벨의 AI 재판정(615행 중 변경 45)과 추가 505행 rationale은 사람 확인 시트를 회수하지 못한 상태로 학습했습니다(DATA_CARD data-v7 절).

## 적용 요구사항 (현재 버전)

- 인증: JWT 기반 서비스. claim 이름은 `user_id` / `role` / `tenant` 고정 (매핑 설정 예정)
- 소유자 확인: 프록시가 서비스 DB를 읽기 전용으로 조회할 수 있어야 함
- 배포: 백엔드는 프록시를 통해서만 접근 가능하도록 네트워크 구성 필요
- 권장 절차: 관측 모드로 운영해 오차단 확인 후 차단 모드 전환

## 로드맵

- claim 이름 매핑 설정 / JWKS 기반 서명 검증
- 그룹 구성원(membership) DB 조회
- 세션 쿠키 기반 서비스 지원

## 라이선스

이 저장소의 코드와 문서는 [Apache License 2.0](LICENSE)입니다. 데이터셋은 별도 저장소의 LICENSE(CC BY 4.0)와 NOTICE(출처별 코드 라이선스)를 따릅니다.
