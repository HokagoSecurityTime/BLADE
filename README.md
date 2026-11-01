# BLADE — API 인가 정책 자동 생성·런타임 집행

BLADE는 OpenAPI 명세·DB 스키마·(선택) 컨트롤러 코드로부터 엔드포인트별 **인가 정책(7종 라벨)** 을 LLM으로 생성하고, 사람이 승인한 정책을 **런타임 프록시**가 요청 단위로 집행해 BOLA/IDOR류 인가 결함을 차단하는 연구 프로토타입입니다.

> 이 저장소는 코드·평가 보고서·검증 기록을 담습니다. 학습·평가 데이터셋은 별도 저장소 **[BLADE-dataset](https://github.com/HokagoSecurityTime/BLADE-dataset)** 에 있습니다. LoRA 어댑터와 GGUF 가중치는 이번 공개에 포함하지 않으며 추후 공개 예정입니다.

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

정책 라벨 7종: `public`, `role_required`, `membership_required`, `tenant_match`, `owner_match`, `owner_or_admin`, `manual_review_required`(보류). 정의는 [training/lora/README_serve_v5.md](training/lora/README_serve_v5.md)와 데이터셋 저장소의 프롬프트 v3.0.1을 따릅니다.

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
├─ training/lora/       LoRA 학습·평가·GGUF 변환 스크립트, Ollama Modelfile(v4·v5), RunPod 실행 스크립트
├─ training/experiments/ 정책 조건 추출·어댑터 실험 스크립트
├─ scripts/             데이터 구성·평가(eval_v30.py 등)·데모(demo.sh)·부하 테스트·공개 사본 빌드
├─ tests/               pytest (2026-10-31 기준 397 passed · 1 skipped)
├─ reports/eval/        베이스라인·LoRA v1~v5 평가 보고서·예측·점수(JSON)
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

LoRA 분류기로 전환하려면 Ollama에 `blade-qwen-lora-v5`(GGUF Q4_K_M, 추후 공개)를 등록한 뒤 환경변수만 바꿉니다. 런타임 코드 수정은 없습니다.

```bash
export BLADE_CLASSIFIER=lora BLADE_LORA_MODEL=blade-qwen-lora-v5 BLADE_LORA_MIN_CONFIDENCE=0.9
```

절차는 [training/lora/README_serve_v5.md](training/lora/README_serve_v5.md), Modelfile은 [training/lora/Modelfile.blade-qwen-lora-v5](training/lora/Modelfile.blade-qwen-lora-v5)입니다.

## 테스트

```bash
pytest                      # 전체 (LLM 호출 테스트는 BLADE_LLM_PROVIDER 미설정 시 skip)
pytest tests/test_evaluator.py tests/test_proxy_e2e.py
```

일부 테스트(`tests/test_dataset.py`, `tests/test_label_data.py`, `tests/test_synthetic_services.py`, `tests/test_vuln_review.py`, `tests/test_candidate_analysis.py`, `tests/test_eval_context.py`, `tests/test_lora_classifier.py`)는 데이터셋 저장소의 `datasets/` 경로를 읽습니다. 두 저장소를 같은 상위 폴더에 두고 `datasets/`·`training/lora/data_v*`를 링크하거나 복사하면 통과합니다.

## 평가 결과 요약 (LoRA v5, 3 seed 평균, 기본 디코딩)

| 평가셋 | 조건 | 지표 | base(qwen2.5-7b) | LoRA v5 |
|---|---|---|---:|---:|
| test_v30 (207, 합성 제외) | oas_code | 구체 정밀도 / macro-F1 | 0.353 / 0.197 | 0.796 ± 0.025 / 0.374 ± 0.010 |
| test_v5 (283, hold-out) | oas_code | macro-F1 / 정확도 | 0.238 / 0.382 | 0.683 ± 0.016 / 0.691 ± 0.007 |
| test_v31_supp (222) | oas_code | macro-F1 / 정확도 | 0.048 / 0.099 | 0.485 ± 0.026 / 0.419 ± 0.039 |

- 전체 표와 근거 파일: [reports/eval/lora_v5/presentation_numbers_v5.md](reports/eval/lora_v5/presentation_numbers_v5.md), 보고서 [reports/eval/lora_v5/lora_v5_report.md](reports/eval/lora_v5/lora_v5_report.md).
- 프록시 집행 성능(현재 코드, Docker): 탐지 5종 100%·6종 83.33%, 오탐 0/140, p95 추가 지연 +2.0 ms — [verification/METRICS.md](verification/METRICS.md).
- 평가 정의(eval-def v2)는 `scripts/eval_v30.py`, hold-out 채점은 `scripts/eval_test_v5.py`. 채점에 필요한 정답 파일은 데이터셋 저장소에 있습니다.

## 데이터셋·모델

- 데이터셋 저장소: **[BLADE-dataset](https://github.com/HokagoSecurityTime/BLADE-dataset)** — data-v1~v5 학습 데이터, test_v30·test_v31_supp·test_v5 평가셋, 프롬프트 v3.0.1, 라벨링 규약, 공개 사본과 복원 스크립트. 동결 파일 SHA-256은 [AGENTS.md](AGENTS.md)에 있습니다.
- 모델 가중치(LoRA v4·v5 어댑터, GGUF Q4_K_M): **추후 공개**. 해시와 변환 기록은 [reports/eval/lora_v5_gguf/](reports/eval/lora_v5_gguf/)에 있습니다.

## 알려진 한계

- 정책 생성은 엔드포인트별 순차 LLM 호출이며 CPU Ollama 기준 1건 수십 초가 걸립니다(비동기 작업 큐 없음).
- 프록시는 SQLite 읽기 전용 조회와 HS256 JWT만 지원하며, `membership_required`의 그룹 구성원 조회는 런타임에 집행하지 않습니다(manual 처리).
- test_v30에서 security 선언이 있는 엔드포인트를 public으로 오판하는 사례가 남아 있습니다. 상세는 lora_v5_report.md 6절.

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
