# BLADE demo

## 대시보드·알림·공격 시뮬레이션

대시보드: **http://localhost:3000**. React/Vite를 빌드해 Nginx로 제공하며 `/api`로 기존 admin-api에 연결합니다.
정책 상태 필터·승인/거절/롤백·YAML 편집, 최근 탐지 100건의 verdict 필터와 5초 갱신,
수동 검토 정책 및 최근 100건 내 해당 OBSERVE 수를 제공합니다. YAML의 id/created_at/status는 유지해야 합니다.

기존 검증 프로젝트에 추가/갱신:

```bash
docker compose -p blade-verify-20260910 up -d --build dashboard alerts
```

기존 프록시 및 admin-api 파일은 변경하지 않았습니다. 새 `admin_api/alerts.py`가 별도 컨테이너에서
읽기 전용 SQLite를 1초마다 확인합니다. `.env`의 `BLADE_SLACK_WEBHOOK` / `BLADE_DISCORD_WEBHOOK`을 설정하고
alerts를 재생성하면 이후 BLOCK 로그를 전송합니다. 최초 시작은 과거 로그를 건너뛰고, 재시작은 저장된 커서부터 이어갑니다.
전송 실패는 로그만 남기고 다음 이벤트로 넘어갑니다. 외부 Slack 전송·스크린샷은 사용자 요청으로 이번 검증에서 제외했습니다.

7 label × 정상/공격 × 5회 시뮬레이션:

```bash
docker compose -p blade-verify-20260910 exec -T admin-api python /app/scripts/attack_sim.py --prepare-demo -n 5 --proxy http://proxy:8080 --admin http://localhost:8100
```

먼저 정책을 승인하세요. `--prepare-demo`는 공유된 `/users/{userId}` 경로를 두 label로 시험하기 위해
해당 ACTIVE 정책을 관리 API로 일시 변경하고 종료 시 원본을 복원합니다. 시뮬레이션 중에는 다른 정책 편집을 피하세요.
public의 공격 형태 요청은 허용 대상(TN), manual review의 타인 조회 통과는 미탐(FN)으로 계산합니다.
HTTP 200/403 이외의 응답과 연결 실패는 오류로 별도 집계하며, 지연은 정책 준비 시간을 제외한 순차 GET의 왕복 시간입니다.

[화면·브라우저 검증·결과표](verification/2026-09-10-dashboard-alerts.md): 70회, TP 25 / FN 5 / FP 0 / TN 40,
탐지율 83.3%, 오탐율 0%, p50 3.81ms / p95 4.96ms.

Docker Engine/Desktop와 Compose v2, Bash가 필요합니다. `.env`에 JWT 시크릿과 사용 가능한 LLM 제공자·모델을 설정한 뒤 설치·기동은 한 줄입니다:

```bash
docker compose up -d
```

최초 환경 파일은 `cp .env.example .env`로 준비하고 값을 확인하세요. 이미 있는 `.env`는 유지하세요.
demo-backend(9000), admin-api(8100), proxy(8080), dashboard(3000), 별도 alerts 워커가 실행됩니다.
SQLite 데이터는 Compose 프로젝트별 named volume에 보관하며 프록시는 데모 DB를 읽기 전용으로 마운트합니다.

데모 실행:

```bash
docker compose up -d && bash scripts/demo.sh
```

7개 정책 생성 → 전체 승인 → 타인 조회 403 → 소유자 조회 200 → 타인 삭제 403 및 DB 행 유지 →
BLOCK 로그 2건 → 롤백 후 200/OBSERVE를 순서대로 확인합니다. 실패하면 0이 아닌 코드로 종료합니다.
승인·롤백 반영 시간은 `BLADE_POLICY_POLL_SEC` 이내인지 측정합니다.
비동기 탐지 로그는 해당 요청 ID로 확인하며 최대 10초 기다립니다.

빈 정책 저장소에서 실행해야 합니다. 기존 볼륨을 지우지 않고 새 실험을 하려면
`COMPOSE_PROJECT_NAME=blade-demo-new`를 export한 뒤 위 명령을 실행하세요. 기존 서비스와 포트가 겹치면 먼저 기존 서비스를 중지해야 합니다.
LLM은 실제로 호출합니다. Ollama는 호스트에 모델이 설치되어 있고 컨테이너에서 접근 가능하도록 리슨해야 합니다
(예: 호스트에서 `OLLAMA_HOST=0.0.0.0:11434` 설정 후 서버 재시작).
주문 정책이 `owner_match`로 생성되지 않으면 자동으로 바꾸지 않고 데모를 실패 처리합니다.

| 환경변수 | 기본값/용도 |
| --- | --- |
| `BLADE_JWT_SECRET` | 필수, HS256 서명 시크릿 |
| `BLADE_LLM_PROVIDER` | `openai`, `anthropic`, `ollama` 중 선택, 생성 시 필수 |
| `BLADE_LLM_MODEL` | 제공자의 실제 모델명, 생성 시 필수 |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | 해당 제공자 사용 시 필요 |
| `BLADE_DOCKER_OLLAMA_URL` | Compose용 `http://host.docker.internal:11434` |
| `BLADE_OLLAMA_URL` | 로컬 실행용 `http://127.0.0.1:11434`; Compose에서는 위 값으로 대체 |
| `BLADE_POLICY_POLL_SEC` | 정책 갱신 주기, 기본 `5`초 |
| `BLADE_CACHE_TTL` | 조회 캐시 TTL, 기본 `60`초 |
| `BLADE_FAIL_MODE` | 조회 장애 시 `open`(OBSERVE) / `closed`(BLOCK), 기본 `open` |
| `BLADE_TARGET_URL` | Compose에서는 `http://demo-backend:9000`으로 고정 |
| `BLADE_ADMIN_URL` | Compose에서는 `http://admin-api:8100`으로 고정 |
| `BLADE_DB_DSN` | Compose에서는 `sqlite:///file:/data/demo.db?mode=ro`로 고정 |
| `BLADE_PROXY_HOST` | 로컬 `127.0.0.1`, Compose `0.0.0.0` |

정책 스키마: [AGENT.md](AGENT.md#정책-yaml), [Pydantic 모델](common/schema.py).
통합 검증 상태: [Compose·데모 기록](verification/2026-09-09-compose.md).
2026-09-10 Docker Desktop 설치 후 실제 Ollama를 사용한 컨테이너 7단계 검증을 완료했습니다.
[실행 결과](verification/2026-09-10-docker-live.md): 승인 1.694초, 롤백 4.924초로 설정한 5초 이내에 반영됐습니다.
Windows에서는 Git Bash로 실행하세요. 검증 컨테이너의 Compose 프로젝트명은 `blade-verify-20260910`입니다.

> 현재 프록시는 **ACTIVE 정책으로 전달 전에 인가를 평가**합니다. BLOCK은 403으로 차단합니다.
> 검증 기록: [인가 평가·캐시·E2E](verification/2026-09-09-proxy-enforcement.md).
> 검증 명령: `pytest tests/test_evaluator.py tests/test_proxy_e2e.py` — 28 passed.
> 매칭 정책은 `X-Blade-Policy`, 요청 ID는 `X-Blade-Request-Id` 응답 헤더로 확인합니다.
> `BLADE_JWT_SECRET`을 설정한 후 `python -m proxy.mktoken user_99`로 데모 토큰을 발급합니다.

실험 이력은 [verification/README.md](verification/README.md)에 모아두었습니다.

## 새로운 사례 평가 및 성능 측정

```powershell
$env:BLADE_LLM_PROVIDER='ollama'
$env:BLADE_LLM_MODEL='qwen2.5:7b'
python -m pipeline.classifier.evaluate verification/classifier-holdout-v1.json --output verification/new-evaluation-run.json
python -m tests.benchmark_proxy --output verification/new-latency-run.json --samples 50
```

평가 파일은 덮어쓰지 않으며 매 실행마다 새로운 출력 경로를 지정합니다.
14개 합성 사례의 정답과 rationale은 LLM 입력에서 제외합니다. 결과에는 정책 필드 정확도,
수동 검토율, 혼동행렬, 호출 시간과 데이터·소스 해시가 포함됩니다.
이번 결과는 13/14이며 [실험 기록](verification/2026-09-09-evaluation.md)에 한계와 오답을 기록했습니다.
지연 측정은 LLM 실행이 끝난 뒤 진행하세요. 단일 로컬 순차 호출 측정이며 부하 테스트는 아닙니다.

## 전체 서비스 회귀 검증

```powershell
.\.python\python.exe -m pytest tests/test_e2e.py
```

관리 API·데모 백엔드·프록시를 임시 포트와 DB로 실행해 7개 인가 패턴,
정책 검토·승인·롤백, DELETE 차단과 로그 저장을 검증합니다.
기존 정책 파일과 DB는 변경하지 않으며 실제 LLM 호출도 하지 않습니다.
기존 Ollama 결과를 테스트 입력으로 사용하고 사용자 조회 정책의 수동 검토 과정을 재현합니다.
`BLADE_E2E_REPORT`에 JSON 출력 경로를 설정하면 항목별 결과를 저장합니다.

Python 3.11 환경에서:

현재 작업 공간에는 Python 3.11.9와 의존성이 `.python/`에 설치되어 있습니다.
새 PowerShell 터미널에서 아래 설정을 먼저 실행하면 기존 명령을 그대로 사용할 수 있습니다.

```powershell
$env:PATH = "C:\BLADE\.python;C:\BLADE\.python\Scripts;" + $env:PATH
```

```powershell
python -m pip install -e .
pytest tests/test_demo_backend.py
uvicorn demo_backend.main:app --port 9000
```

다른 터미널에서 실행 중인 서버의 OAS를 저장합니다:

```powershell
python -m demo_backend.export_openapi --url http://127.0.0.1:9000
```

서버 없이도 `python -m demo_backend.export_openapi`로 생성할 수 있습니다.
결과는 `demo_backend/openapi.json`입니다. DDL은 `demo_backend/schema.sql`이며,
서버 시작 시 현재 작업 디렉터리의 `demo.db`에 테이블과 없는 시드 행을 생성합니다.
삭제한 시드 주문은 서버를 재시작하면 복구됩니다.

이 백엔드는 BOLA 재현을 위해 **의도적으로 인증·인가 검사를 하지 않습니다**.
JWT 헤더도 검사하지 않으며 관리자·조직·등급 제한도 적용하지 않습니다.
OpenAPI의 정책 설명은 향후 프록시에서 적용할 정책을 나타냅니다.
테스트는 매번 별도 임시 SQLite DB를 사용합니다.

`CLAUDE.md`가 없어 `AGENT.md`의 스키마와 레이아웃을 따릅니다.
`proxy/`는 aiohttp 런타임 프록시입니다. 생성 정책 YAML은 `policies/`에 저장합니다.

## 런타임 프록시

데모(9000), 관리 API(8100)를 실행하고 필요한 정책을 승인한 다음 실행합니다.

```powershell
$env:BLADE_JWT_SECRET = "로컬에서 지정한 JWT 서명 시크릿"
$env:BLADE_DB_DSN = "sqlite:///file:demo.db?mode=ro&uri=true"
$env:BLADE_FAIL_MODE = "closed"
python -m proxy.server
```

프록시는 `127.0.0.1:8080`에 바인딩합니다. 보호된 API는 HS256 Bearer JWT가 필요합니다.
JWT 누락·서명/만료 오류와 인가 불일치는 403입니다. public은 JWT 없이 통과하며
manual_review_required는 유효한 JWT가 있으면 OBSERVE로 통과합니다. HEAD는 GET 정책도 적용합니다.
읽기 전용 SQLite 조회는 작업 스레드에서 수행하고 런타임에 LLM을 호출하지 않습니다.

ACTIVE 정책을 `BLADE_POLICY_POLL_SEC`(기본 5초)마다 갱신합니다.
조회 결과를 `(table, id)` 키로 `BLADE_CACHE_TTL`(기본 60초) 동안 캐시합니다.
정책 갱신 실패 시 마지막 정상 정책을 유지합니다. 정책 변경과 전달된 쓰기 요청은 조회 캐시를 비웁니다.
정책 없음은 항상 OBSERVE `no_policy`로 전달합니다. DB 조회 실패는
`BLADE_FAIL_MODE=open`이면 OBSERVE, closed이면 403이며 이유는 `lookup_failed`입니다.
조회 행 없음은 PASS `object_not_found`로 전달하여 백엔드가 404를 반환합니다.
정책 롤백은 다음 갱신부터 반영됩니다.

탐지 로그는 제한된 메모리 큐에서 관리 API로 비동기 전송합니다. 전송 실패나 큐 포화는
서버 로그에 남기며 현재 버전은 영구 재전송 큐를 제공하지 않습니다.
요청·응답은 메모리에 버퍼링합니다. WebSocket/스트리밍 중계와 SQLite 외 DB는 미지원입니다.
타깃 30x는 자동으로 따라가지 않고 그대로 전달합니다.

## 정책 생성 및 관리 API

```powershell
$env:BLADE_LLM_PROVIDER = "ollama"
$env:BLADE_LLM_MODEL = "qwen2.5:7b"
uvicorn admin_api.main:app --port 8100
```

다른 터미널에서:

```powershell
curl.exe -F "oas=@demo_backend/openapi.json" -F "erd=@demo_backend/schema.sql" http://127.0.0.1:8100/generate
curl.exe "http://127.0.0.1:8100/policies?status=PENDING"
```

`-F "controller=@demo_backend/main.py"`로 선택적 코드를 전달할 수 있습니다.
분류는 엔드포인트별로 순차 실행하며 이벤트 루프 밖에서 처리합니다.
전체 생성 묶음을 SQLite `blade.db`와 `policies/*.yaml`에 저장합니다.
기존 ID 또는 생성 묶음 안의 ID 충돌은 409이며 기존 정책을 덮어쓰지 않습니다.
ID는 정적 경로 조각을 resource로 사용하고 파라미터 표기를 보존합니다.
예: `pol_orders_get_by_orderId`, `pol_public_health_get`.

승인 `PENDING → ACTIVE`, 롤백 `ACTIVE → PENDING`, 거절 `PENDING → REJECTED`만
허용하며 나머지 상태 전이는 409입니다. `PUT /policies/{id}`는 전체 정책 JSON에서
status를 제외한 내용을 받습니다. id와 created_at은 보존해야 합니다.
`POST /detections`는 탐지 로그 JSON을 받아 DB와 `detections.jsonl`에 저장합니다.
`GET /detections?limit=100`은 최근 삽입 순서대로 조회합니다.
관리 API는 내부 서비스 용도이며 기본 실행 주소는 loopback입니다.
SQLite와 파일은 하나의 OS 트랜잭션이 아니므로 갑작스러운 프로세스 종료 시
파일 미러가 DB와 어긋날 수 있습니다. 단일 프로세스 실행을 기준으로 구현했습니다.

## 오프라인 분류기

`pipeline/parsers/`와 `pipeline/classifier/`는 구현되어 있습니다.
`from pipeline.classifier import classify`로 `classify(endpoint, erd, controller_text=None)`를 호출합니다.
Fine-tuning 및 RAG 단계는 없습니다. LLM 호출은 오프라인 분류 과정에서만 수행합니다.

프로세스 환경변수에 `BLADE_LLM_PROVIDER`와 `BLADE_LLM_MODEL`을 설정합니다.
OpenAI는 `OPENAI_API_KEY`, Anthropic은 `ANTHROPIC_API_KEY`도 필요합니다.
현재 검증 설정은 `BLADE_LLM_PROVIDER=ollama`, `BLADE_LLM_MODEL=qwen2.5:7b`입니다.
`BLADE_LLM_PROVIDER=ollama`로 로컬 Ollama를 사용할 수 있습니다. API 키는 필요하지 않습니다.
`BLADE_LLM_MODEL`은 설치된 Ollama 모델명으로 지정합니다.
서버 주소는 `BLADE_OLLAMA_URL`로 변경하며 기본값은 `http://127.0.0.1:11434`입니다.
모델명은 기본값 없이 명시적으로 지정합니다. `.env`는 자동 로드하지 않습니다.

```powershell
$env:BLADE_LLM_PROVIDER = "ollama"
$env:BLADE_LLM_MODEL = "qwen2.5:7b"
pytest tests/test_classifier.py
python -m pipeline.classifier.run demo_backend/openapi.json demo_backend/schema.sql
```

현재 PC에는 Ollama가 `C:\BLADE\.ollama`에 설치되어 있고 `qwen2.5:7b` 모델이 준비되어 있습니다.
서버가 종료되어 있으면 `.\.ollama\ollama.exe serve`로 실행합니다.
Ollama에는 분류 결과 JSON Schema를 전달해 객체 label 선택 시 owner_lookup 누락을 방지합니다.
프롬프트에는 원래 결정 트리, 일반적인 예시와 경로·ERD의 구조적 연결을 사용합니다.

제공자 환경변수가 없으면 실제 LLM 테스트만 skip합니다. 설정되어 있으면 실제 호출하며
잘못된 설정이나 호출 실패는 성공으로 처리하지 않습니다.
CLI는 엔드포인트별 기대 label, 실제 label, 신뢰도와 일치 여부를 표로 출력합니다.
데모 7개 중 6개 이상 일치하면 종료 코드 0, 기준 미달은 1, 설정 오류는 2입니다.
`--controller demo_backend/main.py`로 코드 문맥을 추가할 수 있으며,
`--output verification/classifier-live.json`으로 실제 결과를 JSON에 저장할 수 있습니다.

요청당 HTTPX connect/read/write/pool 타임아웃은 각각 60초입니다.
네트워크 오류·HTTP 429·5xx는 최초 시도 이후 최대 2회 재시도합니다(1초, 2초 대기).
60초는 전체 재시도 합계의 제한이 아닙니다.
잘못된 JSON·스키마, 미지 label, 신뢰도 0.7 미만 및 조회 컬럼 불일치는
`manual_review_required`로 처리합니다.

## Phase 2 진행 및 실행

진행 순서와 완료 여부는 [Phase 2 검증 기록](verification/phase2/SUMMARY.md)을 참고합니다.
전체 Phase 2 완료를 뜻하지 않습니다. 기존 Phase 1 테스트는 수정하지 않습니다.

Phase 2 전체 서비스는 아래의 `docker-compose.phase2.yml` override로 시작합니다.
기본값 `BLADE_PHASE2_ENABLED=false`는 기존 Phase 1 차단 동작을 유지합니다.
호스트에서 직접 실행할 때는 각 프로세스의 환경변수에 설정해야 합니다.

| 환경변수 | 기본값 | 의미 |
|---|---|---|
| BLADE_PHASE2_ENABLED | false | Phase 2 전체 활성화 |
| BLADE_MODE_ENABLED | true | 전체 활성화 시 observe/enforce 적용 |
| BLADE_OBSERVABILITY_ENABLED | true | 최근 60초 관측률, 백그라운드 전송 |
| BLADE_CONTROLLER_ENABLED | true | 업로드한 Controller의 구조화된 인가 신호 |
| BLADE_REDIS_ENABLED | true | 전체 활성화 및 Redis URL 설정 시 Redis 캐시·pub/sub |
| BLADE_REDIS_URL | 빈 값 | 비어 있으면 인메모리 캐시·정책 폴링 |
| BLADE_RAG_ENABLED | true | 전체 활성화 시 생성 과정에 검색 근거 주입 |
| BLADE_RAG_KINDS | code,idiom,policy,cve | 현재 .env는 사용자 선택 code,idiom 적용 |
| BLADE_EMBED_MODEL | intfloat/multilingual-e5-small | 로컬 임베딩 모델 |
| BLADE_CHROMA_PATH | .chroma | Chroma 저장 경로 |
| BLADE_MODEL_CACHE | .cache/models | 모델 다운로드 캐시 |
| BLADE_CVE_CORPUS | corpus/cve.jsonl | 선택 CVE 코퍼스, 없으면 제외 |
| BLADE_ALERTS_ENABLED | true | observe 위반·enforce 차단의 비동기 알림 |
| BLADE_EXPLAIN_ENABLED | true | 탐지 설명 LLM 워커 |
| BLADE_CVE_ENABLED | true | 명시적으로 실행한 NVD 수집 CLI 허용 |
| BLADE_REANALYSIS_ENABLED | true | 제안 생성 워커·제안 API |
| BLADE_REANALYSIS_OBSERVE_THRESHOLD | 20 | manual_review OBSERVE 누적 건수 |
| BLADE_REANALYSIS_MIN_REQUESTS | 5 | 주체별 비율 판단 최소 요청 수 |
| BLADE_REANALYSIS_MIN_SUBJECTS | 3 | 높은 would_block 비율을 보인 최소 주체 수 |
| BLADE_REANALYSIS_WOULD_BLOCK_RATIO | 0.8 | 주체별 would_block 비율 임계값 |
| BLADE_REANALYSIS_POLL_SEC | 5 | 재분석 워커 스캔 간격 |

Phase 2 승인 정책은 **observe로 시작**합니다. 차단할 정책은 다음처럼 명시적으로 전환합니다.

```powershell
curl.exe -X POST http://localhost:8100/policies/pol_orders_get_by_orderId/mode -H "Content-Type: application/json" --data-raw '{"mode":"enforce"}'
curl.exe http://localhost:8100/metrics/observability
```

`observe`는 위반 요청도 포워딩하며 `OBSERVE`, `would_block=true`로 기록합니다.
`enforce`는 해당 요청을 403으로 차단합니다. 롤백 후 재승인하면 observe로 돌아갑니다.
관측률 `rate`는 최근 60초 전체 요청 중 정책이 매칭된 비율(0~1)입니다.
소유권 조회 성공 수(`lookup_ok`)는 캐시 적중과 조회 결과 행 없음을 포함하고 조회 예외를 제외합니다.

Controller 분석의 JS/TS AST 의존성은 `pip install '.[controller]'`로 설치합니다.
설치하지 못하면 Express/Nest 정규식 힌트로 폴백하며 경고를 남깁니다. Python은 표준 `ast`를 사용합니다.

Redis를 포함한 Phase 2 구성은 다음 명령으로 시작합니다. 기본 Compose 파일은 Phase 1 구성을 유지합니다.

```powershell
docker compose -f docker-compose.yml -f docker-compose.phase2.yml up -d --build
```

이 override는 admin-api·proxy의 Phase 2와 독립 알림·설명·재분석 워커를 활성화합니다. Redis가 끊기면 인메모리 캐시와
admin-api 폴링으로 돌아가며, 정책은 마지막 유효 스냅샷을 유지합니다.
[장애별 동작 명세](docs/failure-modes.md)를 참고하세요.

RAG를 호스트에서 실행할 때는 `python -m pip install '.[controller,rag]'`로 추가 의존성을 설치합니다.
Phase 2 Compose의 admin-api 이미지는 해당 의존성을 포함하며, 임베딩 모델은 최초 생성 시 다운로드합니다.
모델과 Chroma 데이터는 전용 볼륨에 보관됩니다. 임베딩과 검색은 정책 생성 과정에서만 실행합니다.

`POST /generate`는 기존 oas·erd·controller 외에 `code`라는 선택 ZIP 파일을 받습니다.
ZIP을 디스크에 풀거나 실행하지 않고 함수별 코드 청크로 읽습니다. 승인된 ACTIVE 정책만 예시로 검색합니다.
`GET /evidence/{policy_id}`로 모델이 사용했다고 명시한 검증된 근거를 조회합니다.
RAG를 끄면 검색·임베딩 호출과 근거 프롬프트가 사라집니다. Controller도 끄면 Phase 1 프롬프트와 바이트 단위로 같습니다.

`python -m scripts.rag_ablation`은 동일 Controller 조건에서 5가지 검색 조합을 실제 LLM으로 비교합니다.
결과가 낮아지는 조합과 비어 있는 코퍼스도 그대로 기록하며, 운영 조합을 자동 선택하지 않습니다.

2026-10-12 선택된 검색 조합은 **code+idiom**입니다. 이번 데모에서 off 3/7, RAG 조합들은 6/7이었습니다.
승인 정책과 데모 소스의 정답 설명이 포함된 실험이므로 일반화 정확도로 해석하지 않습니다.
자세한 조건은 [RAG 결과](verification/phase2/STAGE4.md)에 기록합니다.

재분석은 원본 정책을 바꾸지 않고 제안으로 저장합니다. 대시보드의 **YAML 보기·편집 → 제안**에서
변경 줄과 사유를 확인한 뒤 수락/기각합니다. 수락하면 version+1, source=reanalysis, mode=observe가 되며
현재 PENDING/ACTIVE 상태는 유지합니다. 제안 이후 원본이 바뀌었거나 거절된 정책이면 409로 거부합니다.
Phase 1에서 생성된 정책에 OAS/ERD/Controller context가 없으면 워커는 추측하지 않고 경고를 남깁니다.

알림은 같은 (sub, policy_id)의 요청을 60초 동안 합칩니다. 설명은 비동기로 SQLite에 추가되며,
최초 JSONL 레코드를 다시 쓰거나 이미 보낸 알림을 수정하지 않습니다. **알림 설정**의 테스트 버튼은
실제 설정 채널로 메시지를 전송합니다. 현재 검증에서는 사용자 요청대로 실제 Slack을 제외하고 로컬 수신 서버를 사용했습니다.

`python -m pipeline.rag.cve_collector --max-pages 1`은 NVD 자료를 명시적으로 수집합니다.
`NVD_API_KEY`가 없으면 요청 간 7초 간격을 둡니다. RAG가 활성화돼 있으면 CVE 컬렉션에도 적재하지만,
검색에 사용하려면 `BLADE_RAG_KINDS`에 cve를 포함해야 합니다. 현재 선택한 code+idiom에는 사용하지 않습니다.

프록시의 외부 호출 순서와 워커 분리는 [critical path 감사](docs/critical-path.md)를 참고하세요.
`python -m scripts.load_test`는 격리된 로컬 HTTP 환경에서 동시 요청 50/100/200, 각 30초의
Phase 1/2 비교를 수행합니다. 개발 환경 회귀 검사이며 운영 최대 처리량 측정이 아닙니다.
