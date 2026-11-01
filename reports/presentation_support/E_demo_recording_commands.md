# E. 데모 녹화용 명령 순서 (로컬 uvicorn + Ollama, LoRA v5 경로)

근거: README.md(런타임 프록시·관리 API 절), training/lora/README_serve_v5.md, proxy/mktoken.py, demo_backend/main.py, admin_api/alerts.py, admin_api/workers/alerts.py, dashboard/src/main.jsx, verification/COMMANDS.md, verification/launch_presentation.py, reports/eval/lora_v5_gguf/pipeline_compare.md. 명령은 Git Bash(`/c/BLADE`) 기준이고 PowerShell이면 `$env:NAME='값'`으로 바꾼다. 런타임 코드는 수정하지 않으며 환경변수와 별도 작업 폴더만 쓴다.

## 0. 사전 준비 (녹화 전에 끝내 둔다)

### 0-1. 포트 비우기

현재 9000·8100·8080·3000은 Docker Desktop 컨테이너(com.docker.backend)가 쓰고 있다(2026-11-01 확인). 로컬 uvicorn으로 띄우려면 먼저 내린다. docker CLI가 응답하지 않으면 Docker Desktop을 종료한다.

```bash
docker compose down            # 또는 Docker Desktop 종료
netstat -ano | grep -E ":(9000|8100|8080|3000) " | grep LISTENING   # 비어 있어야 함
```

### 0-2. 모델 확인

```bash
ollama list      # blade-qwen-lora-v5:latest, blade-qwen-lora-v4:latest(롤백용), qwen2.5:7b 가 있어야 함 (2026-11-01 확인됨)
```

- blade-qwen-lora-v5 = LoRA v5 s42 병합 GGUF Q4_K_M(2-a label 분류). qwen2.5:7b = 2-b 파라미터 추출(roles 등)과 BLADE_CLASSIFIER=llm 경로. CPU 추론이라 정책 7건 생성에 약 8.5분(509.6 s, pipeline_compare.md) 걸린다.

### 0-3. 작업 폴더와 환경변수 (세 터미널 공통)

관리 API는 현재 작업 디렉터리의 `blade.db`·`policies/`에, 데모 백엔드는 `demo.db`에 쓴다. 저장소 루트의 기존 blade.db·policies/(정책 7건이 이미 있어 /generate가 409)를 건드리지 않도록 **새 폴더**에서 띄운다.

```bash
export PATH="/c/BLADE/.python:/c/BLADE/.python/Scripts:$PATH"
mkdir -p /c/BLADE/verification/demo_v5_runtime && cd /c/BLADE/verification/demo_v5_runtime
set -a; source /c/BLADE/.env; set +a                      # BLADE_JWT_SECRET 등 (값은 화면에 띄우지 않는다)
export PYTHONPATH=/c/BLADE
export BLADE_CLASSIFIER=lora
export BLADE_LORA_MODEL=blade-qwen-lora-v5
export BLADE_LORA_MIN_CONFIDENCE=0.9
export BLADE_LLM_PROVIDER=ollama
export BLADE_LLM_MODEL=qwen2.5:7b
export BLADE_OLLAMA_URL=http://127.0.0.1:11434
export BLADE_TARGET_URL=http://127.0.0.1:9000
export BLADE_ADMIN_URL=http://127.0.0.1:8100
export BLADE_DB_DSN="sqlite:///file:/c/BLADE/verification/demo_v5_runtime/demo.db?mode=ro&uri=true"
export BLADE_FAIL_MODE=closed
export BLADE_POLICY_POLL_SEC=5
export BLADE_PHASE2_ENABLED=false                          # Phase 1 동작(차단 403·OBSERVE) 그대로
```

`.env`의 BLADE_DB_DSN은 상대 경로(`demo.db`)라 위처럼 절대 경로로 덮어쓴다. JWT 시크릿 길이 경고(InsecureKeyLengthWarning)는 기존과 같이 발생하며 무시한다.

### 0-4. 세 서비스 기동 (터미널 3개, 모두 0-3 적용 후)

```bash
# T1 데모 백엔드(취약 서버, 인가 없음)
python -m uvicorn demo_backend.main:app --host 127.0.0.1 --port 9000
# T2 관리 API(정책 생성·승인, LoRA v5 호출)
python -m uvicorn admin_api.main:app --host 127.0.0.1 --port 8100
# T3 프록시(ACTIVE 정책 집행, 127.0.0.1:8080)
python -m proxy.server
```

대시보드(선택, 터미널 4):

```bash
cd /c/BLADE/dashboard && npm install && BLADE_ADMIN_URL=http://127.0.0.1:8100 npm run dev   # http://localhost:3000, /api → 8100 프록시(vite.config.js)
```

### 0-5. 시연용 사용자 토큰

`proxy/mktoken.py`는 데모 DB에 시드된 세 사용자만 발급한다: `user_77`(org_1, user, basic — 주문 1042 소유자), `user_99`(org_2, user, basic — 주문 2001 소유자, 공격자 역할), `admin_1`(org_1, admin, premium). 토큰은 HS256, 만료 기본 1시간(`--expires-in 86400`으로 하루).

```bash
cd /c/BLADE   # BLADE_JWT_SECRET이 환경에 있어야 함
export ALICE=$(python -m proxy.mktoken user_77 --expires-in 86400 2>/dev/null)   # alice = user_77 (주문 1042 주인)
export BOB=$(python -m proxy.mktoken user_99 --expires-in 86400 2>/dev/null)     # bob   = user_99 (타인, org_2)
export ADMIN=$(python -m proxy.mktoken admin_1 --expires-in 86400 2>/dev/null)
```

- 화면에는 "alice(user_77)", "bob(user_99)"로 자막을 붙인다. sub를 문자 그대로 `alice`로 바꾸면 orders.user_id(`user_77`)와 맞지 않아 owner_match가 403이 되므로, 이름을 바꾸려면 demo.db에 행을 추가해야 한다(백엔드 시작 후 `sqlite3 demo.db "INSERT INTO users VALUES('alice','org_1','user','basic'); INSERT INTO orders VALUES(3001,'alice');"` 뒤 PyJWT로 `sub=alice, roles=['user'], tenant_id='org_1', membership='basic', exp` 직접 서명). 녹화 단순화를 위해 user_77/user_99 매핑을 권장한다.
- 토큰은 로컬 데모 전용이며 API 키가 아니다. 녹화 화면에 .env 내용은 띄우지 않는다.

### 0-6. "Intended policy" 문구 없는 시연용 OAS 사본

`demo_backend/openapi.json`의 operation description 7개와 info.description에 정답 문구("Intended policy: owner_match; orders.user_id", "Intentionally performs no authentication…")가 들어 있다. 저장소 파일은 그대로 두고 사본을 만든다.

```bash
cd /c/BLADE && python -X utf8 - <<'EOF'
import json, pathlib
d = json.load(open('demo_backend/openapi.json', encoding='utf-8'))
d['info']['description'] = 'Order service API'
for path, ops in d['paths'].items():
    for method, op in ops.items():
        op.pop('description', None)          # 'Intended policy: …' 제거, summary(Get Order 등)·parameters·responses는 유지
out = pathlib.Path('verification/demo_v5_runtime/openapi_clean.json')
out.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(out, [op.get('description') for ops in d['paths'].values() for op in ops.values()])   # 전부 None이어야 함
EOF
grep -c "Intended" verification/demo_v5_runtime/openapi_clean.json   # 0
```

- 컨트롤러 파일(`demo_backend/main.py`)의 데코레이터 `description="Intended policy: …"`는 파서가 데코레이터를 제외하고 핸들러 본문만 발췌하므로(pipeline/parsers/controller.py "Exclude decorators") LLM 입력에 들어가지 않는다. 그래도 화면에 코드를 띄울 때는 해당 줄이 보이지 않게 한다.
- LoRA v5가 이 사본으로 내는 라벨은 pipeline_compare.md(2026-10-31, 원본 OAS + main.py 컨트롤러) 기준으로 public/owner_match/owner_match/owner_or_admin/role_required/tenant_match/manual(premium). 사본에서는 description이 빠지므로 결과가 달라질 수 있다. **녹화 전에 한 번 생성해 보고 라벨을 확인한다**(owner_match가 아니면 BOLA 장면이 403이 안 나온다).

## 1. 장면별 명령

### 장면 1. 공격 재현 (BLADE 없음) — 백엔드 9000 직접 호출

```bash
curl -i http://127.0.0.1:9000/orders/1042                                   # 토큰 없이도 200
curl -i -H "Authorization: Bearer $BOB" http://127.0.0.1:9000/orders/1042   # bob이 alice 주문 조회 → 200 (BOLA)
curl -i -H "Authorization: Bearer $BOB" http://127.0.0.1:9000/admin/reports # 일반 사용자가 관리자 API → 200
```

백엔드는 JWT를 검사하지 않는다(demo_backend/main.py 모듈 docstring). DELETE는 실제로 행을 지우므로 장면 1에서는 쓰지 않는다(지웠으면 T1 재시작으로 시드 복구).

### 장면 2. 정책 생성 (LoRA v5)

```bash
cd /c/BLADE/verification/demo_v5_runtime
time curl -s --max-time 1500 -X POST http://127.0.0.1:8100/generate \
  -F oas=@openapi_clean.json -F erd=@/c/BLADE/demo_backend/schema.sql -F controller=@/c/BLADE/demo_backend/main.py \
  | python -X utf8 -c "import json,sys; [print(p['id'], p['status'], p['label'], p['params'].get('owner_lookup')) for p in json.load(sys.stdin)]"
```

- 동기 호출 1건으로 7개 엔드포인트를 순차 분류한다(CPU 약 8~9분, Ollama 로그에 blade-qwen-lora-v5 로드가 보인다). 녹화에서는 (a) 시작 직후 컷 → 결과로 점프하거나, (b) 녹화 전에 생성해 두고 PENDING 목록만 보여 준다. 두 번째 /generate는 같은 ID가 있어 409다(새 폴더에서만 다시 가능).
- 결과 확인: `curl -s "http://127.0.0.1:8100/policies?status=PENDING"`; YAML은 `demo_v5_runtime/policies/*.yaml`. 정책 evidence 문자열에 `[blade-qwen-lora-v5 policy-label-v3.0.1 label=… confidence=…]`가 찍혀 LoRA 경로임을 보여 줄 수 있다.

### 장면 3. 대시보드 확인·승인

- 브라우저 http://localhost:3000 → 좌측 "정책 목록"(상태 필터 PENDING) → 각 행 "YAML 보기·편집"으로 label·owner_lookup 확인 → **승인** 버튼(PENDING→ACTIVE). 상단 카드에 전체 정책 / 활성 정책 / 차단 요청 / 검토 필요 수가 보인다. "수동 검토 큐" 탭에는 manual_review_required 정책(예: premium)이 들어간다.
- 터미널 대안(순서대로 7건):

```bash
for id in pol_public_health_get pol_orders_get_by_orderId pol_orders_delete_by_orderId pol_users_get_by_userId pol_admin_reports_get pol_orgs_docs_get_by_orgId pol_premium_content_get; do
  curl -s -o /dev/null -w "$id %{http_code}\n" -X POST http://127.0.0.1:8100/policies/$id/approve; done
curl -s "http://127.0.0.1:8100/policies?status=ACTIVE" | python -X utf8 -c "import json,sys; print(len(json.load(sys.stdin)), 'ACTIVE')"
sleep 6   # BLADE_POLICY_POLL_SEC=5: 프록시가 ACTIVE 정책을 읽어 올 때까지
```

### 장면 4. 정상 요청 200 — alice가 자기 주문 조회

```bash
curl -i -H "Authorization: Bearer $ALICE" http://127.0.0.1:8080/orders/1042   # 200, 헤더 X-Blade-Policy: pol_orders_get_by_orderId, X-Blade-Request-Id
```

### 장면 5. BOLA 공격 403 — bob이 alice 주문 조회·삭제

```bash
curl -i -H "Authorization: Bearer $BOB" http://127.0.0.1:8080/orders/1042               # 403 (owner_match: orders.user_id=user_77 ≠ user_99, reason policy_mismatch)
curl -i -X DELETE -H "Authorization: Bearer $BOB" http://127.0.0.1:8080/orders/1042     # 403, 행 유지
curl -i http://127.0.0.1:8080/orders/1042                                               # 토큰 없음 → 403 (no_token)
curl -i -H "Authorization: Bearer $ALICE" http://127.0.0.1:8080/orders/1042             # 다시 200 (삭제되지 않았음을 보여 줌)
```

### 장면 6. Slack 알림

Slack은 사용자 측 설정이 필요하다: Slack 앱 → Incoming Webhooks 활성화 → 알림 채널(예: #blade-alerts)에 webhook URL 발급. URL은 .env의 `BLADE_SLACK_WEBHOOK`에만 두고 화면에 띄우지 않는다.

**경로 A — Phase 1 독립 워처(권장, Redis 불필요)**: 관리 API의 SQLite(`blade.db`) detections 테이블을 1초마다 읽어 **verdict=BLOCK인 새 행만** 전송한다(admin_api/alerts.py). 승인·정책 생성·PASS·OBSERVE에는 보내지 않는다. 처음 시작하면 과거 행은 건너뛰고 그 뒤 행부터 보낸다(장면 5 **전에** 띄워 둔다). 실패는 로그만 남긴다.

```bash
# 터미널 5 (0-3 적용 후)
export BLADE_ALERT_DB=/c/BLADE/verification/demo_v5_runtime/blade.db
export BLADE_ALERT_CURSOR=/c/BLADE/verification/demo_v5_runtime/alert-cursor
python -m admin_api.alerts        # 로그: "No webhooks configured"가 뜨면 BLADE_SLACK_WEBHOOK이 비어 있는 것
```

메시지 형식(alerts.py `message()`), 장면 5·8에서 실제로 올 내용:

```
[BLADE] user_99가 GET /orders/1042에 접근 시도 — 정책 pol_orders_get_by_orderId(owner_match) 위반: policy_mismatch
[BLADE] user_99가 DELETE /orders/1042에 접근 시도 — 정책 pol_orders_delete_by_orderId(owner_match) 위반: policy_mismatch
[BLADE] 가 GET /orders/1042에 접근 시도 — 정책 pol_orders_get_by_orderId(owner_match) 위반: no_token      (토큰 없음: sub가 빈 문자열)
[BLADE] user_99가 GET /admin/reports에 접근 시도 — 정책 pol_admin_reports_get(role_required) 위반: policy_mismatch
```

**경로 B — Phase 2 워커·대시보드 알림 설정**: `BLADE_PHASE2_ENABLED=true BLADE_ALERTS_ENABLED=true`로 관리 API·프록시·`python -m admin_api.workers`(BLADE_ADMIN_DB=…/blade.db)를 띄우면 대시보드에 "알림 설정" 탭이 생겨 webhook 저장·테스트 전송(`POST /settings/alerts/test`)이 되고, 메시지는 `[BLADE enforce] user_99 → GET /orders/1042 · 정책 pol_orders_get_by_orderId(owner_match) · policy_mismatch` 형식이다. 조건: BLOCK이면서 정책 mode=enforce(Phase 2 정책 기본 mode는 observe라 승인 후 `POST /policies/{id}/mode {"mode":"enforce"}` 필요) 또는 would_block, 알림 기준(min_severity) 충족, 같은 (사용자, 정책)은 60초 동안 1회. Redis 스트림·RAG 등 다른 Phase 2 플래그도 함께 켜지므로 녹화에는 경로 A를 권한다.

### 장면 7. 탐지 로그

- 대시보드 "탐지 로그" 탭(verdict 필터 BLOCK, 5초 자동 갱신): 시간/요청 ID, 호출자(user_99·익명), 요청, 판단 배지, 정책/사유(policy_mismatch·no_token).
- 터미널:

```bash
curl -s "http://127.0.0.1:8100/detections?limit=20" | python -X utf8 -c "import json,sys; [print(d['ts'][11:19], d['verdict'], d['sub'] or '(anon)', d['method'], d['path'], d['policy_id'], d['reason']) for d in json.load(sys.stdin)]"
```

프록시는 탐지 로그를 비동기로 관리 API에 보내므로 요청 직후 1~2초 뒤에 조회한다. `demo_v5_runtime/detections.jsonl`에도 같은 행이 쌓인다.

### 장면 8. 역할 기반 차단 — /admin/reports

```bash
curl -i -H "Authorization: Bearer $BOB"   http://127.0.0.1:8080/admin/reports   # 403 (role_required roles=[admin], bob roles=[user])
curl -i -H "Authorization: Bearer $ADMIN" http://127.0.0.1:8080/admin/reports   # 200 {"order_count": 2}
```

추가로 보여 줄 수 있는 것: 테넌트(`$BOB`로 GET /orgs/org_1/docs → 403, `$ALICE` → 200), 관리자 우회(`$ADMIN`으로 GET /users/user_77 → 200 admin_bypass), 롤백(`POST /policies/pol_orders_get_by_orderId/rollback` → 5초 뒤 bob GET 200 + OBSERVE no_policy).

## 2. 녹화 후 정리

```bash
# T1~T5 Ctrl+C. 저장소 루트의 blade.db·policies/·demo.db는 건드리지 않았다.
rm -rf /c/BLADE/verification/demo_v5_runtime      # 또는 보존(untracked)
git status --short                                  # 변경 없음 확인
docker compose up -d                                # Docker 구성을 다시 쓸 때
```

## 3. 주의·한계

- LoRA v5 생성 시간(CPU ≈ 73 s/정책)은 녹화 연출이 필요하다. GPU가 없으므로 단축할 수 없다.
- premium/content는 LoRA v5가 manual_review_required로 보류(2026-10-31 결과)해 승인해도 OBSERVE 통과(200)한다. 장면 순서에는 없지만 질문이 나오면 "보류 → 사람 검토 큐"로 설명한다.
- Slack 실전송은 2026-09-10 검증에서 사용자 요청으로 제외됐고 이후 실제 전송 기록이 없다. 녹화 전에 `python -m admin_api.alerts`로 테스트 BLOCK 1건을 보내 채널에 뜨는지 확인한다.
- 정책 ID는 경로에서 만들어지므로(pol_orders_get_by_orderId 등) 사본 OAS로 생성해도 ID는 같다.
