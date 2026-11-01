# BLADE — LLM 기반 BOLA 자동 탐지 리버스 프록시

## 프로젝트 개요
BLADE는 두 단계로 동작한다.
- **Setup(오프라인)**: OAS + ERD(+Controller 코드)를 입력받아 LLM이 엔드포인트별 인가 패턴을 분류하고 정책(YAML)을 생성한다. 관리자가 검토·승인하면 ACTIVE가 된다.
- **Runtime(온라인)**: aiohttp 리버스 프록시가 요청을 가로채 JWT 클레임과 ACTIVE 정책 시그니처만으로 소유권을 평가한다. **런타임에는 LLM을 절대 호출하지 않는다.**

## 절대 규칙
1. 인가 패턴 label은 아래 6종 + 탈출 1종만 존재한다. 새 label을 만들지 않는다.
2. 아래 인터페이스 스키마(정책 YAML, JWT 클레임, 탐지 로그, 저장소 API)는 변경하지 않는다. 변경이 필요하면 작업을 멈추고 이유를 보고한다.
3. 프록시 요청 경로(critical path)에 LLM 호출, 동기 외부 API 호출을 넣지 않는다.
4. 각 단계는 지정된 검증 명령이 통과해야 완료다. 통과 전에는 다음 단계 코드를 작성하지 않는다.
5. 파일 구조는 아래 레이아웃을 따른다. 임의로 디렉토리를 추가하지 않는다.
6. Python 3.11, 타입힌트 필수, 테스트는 pytest.

## 인가 패턴 label
| label | 의미 | 프록시 평가 |
|---|---|---|
| public | 인가 대상 아님 | 항상 통과 |
| role_required | 역할 필요 | claims.roles ∩ policy.params.roles ≠ ∅ |
| membership_required | 소속/등급 필요 | claims.membership ∈ policy.params.allowed_membership |
| tenant_match | 조직 소유 객체 | claims.tenant_id == owner_lookup(id).tenant_col |
| owner_match | 개인 소유 객체 | claims.sub == owner_lookup(id).owner_col |
| owner_or_admin | 개인 소유 + 관리자 우회 | owner_match OR "admin" ∈ claims.roles |
| manual_review_required | 탈출 | 통과시키고 verdict=OBSERVE로 로그만 기록 |

## 인터페이스 스키마

### 정책 YAML
```yaml
id: pol_orders_get_by_id           # pol_<resource>_<method>_<qualifier>
endpoint:
  method: GET
  path: /orders/{orderId}
label: owner_match
params:
  object_param: orderId            # path 또는 query 파라미터명, public/role/membership이면 null
  owner_lookup:                    # tenant_match/owner_match/owner_or_admin일 때만
    table: orders
    id_col: id
    owner_col: user_id
    tenant_col: null
  roles: []                        # role_required, owner_or_admin
  allowed_membership: []           # membership_required
confidence: 0.91                   # 0.0~1.0
evidence: "ERD orders.user_id FK → users.id; controller 소유권 검사 없음"
status: PENDING                    # PENDING | ACTIVE | REJECTED
created_at: "2026-09-08T10:00:00Z"
```

### JWT 클레임 (HS256, 시크릿은 env BLADE_JWT_SECRET)
```json
{ "sub": "user_99", "roles": ["user"], "tenant_id": "org_1", "membership": "basic", "exp": 0 }
```

### 탐지 로그 레코드 (JSONL + SQLite 테이블 detections)
```json
{ "ts": "...", "request_id": "...", "sub": "user_99", "method": "GET", "path": "/orders/1042",
  "policy_id": "pol_orders_get_by_id", "label": "owner_match",
  "verdict": "BLOCK", "reason": "sub=user_99 != owner=user_77" }
```
verdict ∈ PASS | BLOCK | OBSERVE

### 정책 저장소 API (admin-api, FastAPI, 포트 8100)
- GET  /policies?status=PENDING|ACTIVE|REJECTED
- GET  /policies/{id}
- PUT  /policies/{id}                       # 내용 수정 (status 제외)
- POST /policies/{id}/approve               # PENDING → ACTIVE
- POST /policies/{id}/reject                # PENDING → REJECTED
- POST /policies/{id}/rollback              # ACTIVE → PENDING
- POST /generate  (multipart: oas, erd, controller?)  # → PENDING 정책 N개 생성
- GET  /detections?limit=100

## 레이아웃
blade/ demo_backend/ # C3: 데모 타깃 서비스 (FastAPI, 포트 9000) pipeline/ # B: 파서·LLM 분류·정책 생성 parsers/ # oas.py, erd.py classifier/ # prompt.py, llm.py, schema.py generator.py admin_api/ # 정책 저장소 + /generate + /detections (포트 8100) proxy/ # A: aiohttp 리버스 프록시 (포트 8080) jwt_auth.py, router.py, evaluator.py, lookup.py, cache.py, server.py common/ # 스키마 dataclass/pydantic, label 상수, 로그 유틸 tests/ policies/ # 생성된 YAML 저장 위치 docker-compose.yml


## 환경변수
BLADE_JWT_SECRET, BLADE_TARGET_URL, BLADE_DB_DSN(읽기 전용), BLADE_ADMIN_URL,
BLADE_LLM_PROVIDER(openai|anthropic|ollama), BLADE_LLM_MODEL, BLADE_FAIL_MODE(open|closed, 기본 open),
BLADE_CACHE_TTL(기본 60), BLADE_POLICY_POLL_SEC(기본 5)

## Phase 2 스키마 확장 (기존 필드 변경 금지, 추가만)

### 정책 YAML 추가 필드
mode: observe            # observe | enforce. 승인 시 기본 observe. enforce에서만 BLOCK, observe는 위반도 OBSERVE로 기록
version: 1               # 정수. 수정·재분석 제안으로 교체될 때 +1
source: llm              # llm | manual | reanalysis
evidence_refs: []        # RAG 근거 목록 [{kind: code|idiom|policy|cve, ref: "...", snippet: "..."}]

### 탐지 로그 추가 필드
mode: observe            # 판정 시점의 정책 mode
explanation: null        # LLM 탐지 설명(한국어), 비동기로 채워짐
would_block: false       # observe 모드에서 enforce였다면 BLOCK이었을지

### 저장소 API 추가
- POST /policies/{id}/mode            body {mode: observe|enforce}   ACTIVE 정책만
- GET  /policies/{id}/proposals       재분석 제안 목록
- POST /proposals/{pid}/accept        제안을 정책에 반영 (version+1, source=reanalysis)
- POST /proposals/{pid}/dismiss
- GET  /metrics/observability         {total, with_policy, lookup_ok, rate}
- POST /detections/{id}/explanation   내부용, 설명문 채움
- GET  /evidence/{policy_id}          evidence_refs 상세
- GET/PUT /settings/alerts            {slack_webhook, discord_webhook, min_severity}

### 추가 환경변수
BLADE_REDIS_URL (없으면 인메모리 폴백), BLADE_SLACK_WEBHOOK, BLADE_DISCORD_WEBHOOK,
BLADE_EXPLAIN_ENABLED(기본 true), BLADE_REANALYSIS_OBSERVE_THRESHOLD(기본 20),
BLADE_RAG_ENABLED(기본 true), BLADE_CHROMA_PATH

### 추가 규칙
7. 프록시 critical path에 Redis 외 외부 호출 금지. 설명 생성·알림·재분석은 전부 비동기 워커.
8. Phase 1 테스트 전부 그대로 통과해야 한다. 기존 테스트를 수정해야 통과한다면 멈추고 보고.
9. 새 기능은 전부 환경변수로 끌 수 있어야 하고, 꺼진 상태 = Phase 1 동작과 동일.

### Phase 2 적용 범위
사용자 지시에 따라 [0] 확장을 반영한다. 기존 필드는 유지하며 위 추가 필드·API와 Phase2.md에 지정된 새 디렉토리는 허용한다.
실행 순서는 [1] → [3] → [2] → [4] → [5] → [6] → [7] → [8]이다.
`BLADE_PHASE2_ENABLED=false`(기본값)이면 Phase 1 판정 동작을 유지한다. true일 때 개별 기능 스위치를 적용한다.


## Phase 3 확장

### 모델 역할 및 데이터 라벨링 (2026-10-15 사용자 확정)
- BLADE_LOCAL_MODEL=qwen2.5:7b: 베이스라인·파인튜닝 대상 베이스 모델. 라벨 생성에는 사용하지 않는다.
- 라벨링 기본 모델: openai / gpt-4o-mini. 대안 anthropic / claude-sonnet-4-5는 명시적으로 선택한다.
- 라벨러는 --provider/--model 또는 BLADE_LABEL_PROVIDER/BLADE_LABEL_MODEL만 사용한다. BLADE_LLM_*와 역할을 섞지 않고 .env를 자동 수정하지 않는다.
- API 키는 OPENAI_API_KEY / ANTHROPIC_API_KEY에서 읽되 출력하지 않는다. 단가는 training/configs/pricing.yaml에 사용자가 입력한다.
- 공유 프롬프트는 루트 prompts/v2.0.md에 SHA-256·스냅샷 일시와 함께 고정한다. BLADE_PROMPT_VERSION 기본값 v2.0. 변경은 v2.1.md 등 새 버전으로만 한다.
- B 다음 C는 API 호출 없는 dry-run까지만. D 라벨링 실행은 사용자의 별도 명시 승인 전 금지한다.
- 2026-10-19 프롬프트 보완: 라벨러는 prompts/v2.1.md를 사용한다. OAS security 원문·scope·익명 대안 여부 및 추정 ERD 출처를 전달한다. 런타임 기본 버전은 v2.0으로 유지하며 v2.1은 BLADE_PROMPT_VERSION으로 선택한다. classify의 security_context 인자로 근거를 전달할 수 있으며 미제공 시 unknown이다. v2.0 파일은 변경하지 않는다.
- 2026-10-19 프롬프트 보완: 라벨러는 prompts/v2.1.md를 사용한다. OAS security 원문·scope·익명 대안 여부 및 추정 ERD 출처를 전달한다. 런타임 기본 버전은 v2.0으로 유지하며 v2.1은 BLADE_PROMPT_VERSION으로 선택한다. classify의 security_context 인자로 근거를 전달할 수 있으며 미제공 시 unknown이다. v2.0 파일은 변경하지 않는다.

### 모델 추상화
- pipeline/classifier/llm.py의 provider에 `local` 추가: HuggingFace transformers 로컬 모델(+LoRA 어댑터) 로드. 인터페이스 complete(system, user) 동일.
- 환경변수: BLADE_LLM_PROVIDER=local, BLADE_LOCAL_MODEL(기본 모델 경로/HF id), BLADE_LORA_ADAPTER(없으면 베이스만), BLADE_LOCAL_DEVICE(cuda|cpu|mps)
- 분류 결과에 model_id, prompt_version 필드 추가 (정책 YAML evidence 옆). 어느 모델·프롬프트로 생성됐는지 추적.

### 데이터셋 규약
- 2026-10-19 사용자 변경 승인: 별도 API 결제 대신 대화형 Codex 에이전트가 직접 후보를 검토해 라벨링한다. 이번 실행은 API 0회이며, 기존 gpt-4o-mini 실행과 섞지 않고 `apisguru_agent_labeled.jsonl`로 저장한다. model_id는 실제 API 모델명을 추측하지 않고 `codex-agent-unreported`, meta.label_source는 `interactive_codex_agent`로 기록한다. v2.1은 검토 지침이며 API 호출 프롬프트의 정확한 재현 실행이 아님을 명시한다. confidence는 보정되지 않은 주관적 추정이다. 사람 검수 전 분할·학습은 수행하지 않는다.
- datasets/blade/ 아래: raw/ (원본), processed/ (train.jsonl, val.jsonl, test.jsonl), DATA_CARD.md
- 1레코드 = {id, service, method, path, oas_snippet, erd_snippet, controller_signals, label, rationale}
- label은 7종(6 + manual_review_required)만. 다른 값은 검수 단계에서 제거.
- **분할은 service 단위**: 같은 service의 엔드포인트가 train/test에 섞이면 안 된다.
- test.jsonl은 [2] 베이스라인 측정 이후 **절대 수정 금지**. 수정이 필요하면 멈추고 보고.

### 평가 규약
- 모든 분류 평가는 scripts/eval_classifier.py 하나로. 출력: label별 P/R/F1, macro-F1, confusion matrix, manual_review 비율, 평균 추론 시간.
- 결과는 reports/eval/{model_id}_{prompt_version}_{date}.json + .md 로 저장. 덮어쓰지 않는다.
- 베이스라인과 파인튜닝 비교는 **같은 프롬프트, 같은 test.jsonl, 같은 RAG 설정**으로만.

### 추가 규칙
10. Phase 1·2 테스트 전부 통과 유지. 깨지면 멈추고 보고.
11. 학습 코드는 training/ 아래에 격리. 프록시·admin_api·pipeline 런타임 코드는 training/을 import하지 않는다.
12. 모델 가중치·데이터셋 raw는 git에 올리지 않는다 (.gitignore). 경로와 해시만 기록.
