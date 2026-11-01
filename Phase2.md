BLADE Phase 2 — 에이전트 실행 명령 세트
사용법은 Phase 1과 동일: [0]을 먼저 반영하고, 한 번에 하나씩 붙여넣고, 검증 통과 후 다음으로. 병렬 실행 시 축 분리: A(프록시) = [1][2][7] · B(파이프라인) = [3][4][6] · C(대시보드·알림) = [5][8]. [0]은 사람이 직접 AGENTS.md를 고친 뒤 시작.

[0] AGENTS.md 추가분 (사람이 직접 반영)
AGENTS.md의 "인터페이스 스키마" 아래에 다음을 추가. 기존 필드는 삭제·변경하지 않는다.
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


[1] A — 관측/집행 모드 + 관측률 지표
AGENTS.md의 Phase 2 확장을 먼저 읽어. 이 단계는 정책 mode와 관측률이다.

1. common/schema.py에 mode, version, source, evidence_refs 필드 추가 (기본값 있음, 기존 YAML 파싱 깨지면 안 됨).
2. admin_api: 승인 시 mode=observe로 저장. POST /policies/{id}/mode 구현 (ACTIVE만, 아니면 409). 기존 정책 마이그레이션: mode 없으면 observe로 취급.
3. proxy/evaluator.py: 평가 결과가 BLOCK인데 정책 mode=observe면 verdict=OBSERVE, would_block=true로 기록하고 포워딩. enforce면 기존대로 403.
4. 탐지 로그에 mode, would_block 추가.
5. proxy에 관측률 카운터: 전체 요청 / 정책 매칭된 요청 / owner_lookup 성공 요청. 1분 윈도우 누적을 admin_api POST로 전송, GET /metrics/observability 로 조회.
6. tests/test_mode.py: observe에서 위반 → 200 + OBSERVE + would_block=true, enforce 전환 후 같은 요청 → 403, 롤백 → PENDING, 재승인 → observe로 리셋. 관측률 계산 케이스 3개.

검증: Phase 1 테스트 전체 + test_mode.py 통과. demo.py 7단계가 "approve 후 enforce 전환" 단계 추가로 여전히 통과.


[2] A — Redis 전환 + 실패 분기 명세
1. proxy/cache.py를 Redis 백엔드로 교체. BLADE_REDIS_URL 없으면 기존 인메모리로 폴백. 인터페이스(get/set/clear) 유지.
2. 정책 캐시도 Redis에: admin_api가 approve/rollback/mode 변경 시 Redis pub/sub 채널 "blade:policy"로 알림 → 프록시는 폴링 대신 구독으로 즉시 리로드 (폴링은 Redis 없을 때 폴백).
3. docs/failure-modes.md 작성: 아래 각 상황별 동작을 표로. 
   - Redis 연결 끊김 / DB 조회 타임아웃 / DB 조회 예외 / 정책 YAML 파싱 오류 / admin_api 다운 / JWT 시크릿 미설정 / 백엔드 다운
   각 행: 프록시 동작(BLADE_FAIL_MODE open·closed별), 로그 verdict·reason, 알림 여부, 복구 조건.
4. tests/test_failure_modes.py: 표의 각 행을 테스트로 (mock·monkeypatch). 특히 "Redis 죽어도 프록시가 죽지 않고 인메모리로 계속 동작"을 반드시.

검증: docker-compose에 redis 서비스 추가 후 Phase 1 전체 + test_mode + test_failure_modes 통과. Redis 컨테이너 kill 후 요청이 계속 처리되는지 수동 확인해서 보고.


[3] B — Controller AST 분석
pipeline/parsers/controller.py 구현. Phase 1의 "텍스트 첨부"를 구조화된 신호로 바꾼다.

1. Python: ast 모듈로 라우트 데코레이터(@app.get, @router.delete 등) → 핸들러 함수 매핑. 핸들러 본문에서 다음 신호 추출:
   - 인가 검사 존재: current_user / Depends(get_current_user) / user.id == / owner_id == / HTTPException(403) 패턴
   - 관리자 분기: "admin" in roles / is_admin / role == 
   - 테넌트 분기: tenant_id == 
   - 쿼리 필터: .filter(..user_id==..) / WHERE user_id 문자열
2. JS/TS: tree-sitter로 Express/Nest 라우트 → 핸들러. 같은 신호 세트. tree-sitter 설치 실패 시 정규식 폴백 + 경고.
3. 출력: {route: {has_auth_check, admin_bypass, tenant_check, owner_filter, raw_snippet}}. 프레임워크 못 알아보면 빈 dict + 경고, 예외는 밖으로 안 새게.
4. classifier/prompt.py: 신호를 프롬프트의 "Controller 신호" 섹션에 구조화해 주입. 결정 트리 Q4(관리자 우회)는 admin_bypass 신호를 우선 근거로 쓰도록 프롬프트 수정.
5. tests/test_controller_parser.py: demo_backend 핸들러 7개 전부 has_auth_check=false(의도적 취약)인지. 추가로 tests/fixtures/controllers/에 인가 검사 있는 FastAPI 핸들러 3개 + Express 핸들러 2개를 손으로 작성해 신호 추출 정확도 확인.

검증: 테스트 통과. demo_backend에 /users/{userId} 핸들러를 "admin이면 통과" 분기가 있는 버전으로 바꾼 fixture로 /generate 실행 → 이번엔 owner_or_admin이 나오는지 확인해서 보고 (Phase 1에서 manual_review였던 케이스).


[4] B — RAG (코퍼스 + ChromaDB + 프롬프트 주입)
pipeline/rag/ 구현. BLADE_RAG_ENABLED=false면 Phase 1과 완전히 동일하게 동작해야 한다.

1. corpus/ 4종 로더, 우선순위 순:
   a. code: 대상 서비스 소스(controller·ORM 모델·미들웨어) — /generate에 선택 업로드되는 zip
   b. idiom: 프레임워크별 인가 관용구 문서 — pipeline/rag/idioms/*.md를 직접 작성 (FastAPI Depends, Django get_queryset/permissions, Spring @PreAuthorize, NestJS Guard, Express middleware, Rails current_user 스코프). 각 파일: 패턴 설명 + 코드 예시 + 어느 label 신호인지
   c. policy: 저장소의 ACTIVE 정책 (승인된 것만, few-shot용)
   d. cve: [5]의 CVE 수집기 출력 (없으면 스킵)
2. 임베딩: sentence-transformers 로컬 모델 1개 고정 (BLADE_EMBED_MODEL, 기본 multilingual-e5-small 류). ChromaDB persistent (BLADE_CHROMA_PATH). 컬렉션은 코퍼스 종류별 4개.
3. 청킹: 코드는 함수 단위, md는 헤딩 단위, 정책은 1건 1청크.
4. retrieve(endpoint, erd_info) → top-k(기본 5), 종류별 가중치(code 1.0, idiom 0.8, policy 0.8, cve 0.4). 결과를 프롬프트 "참고 근거" 섹션에 주입하고, 분류 출력의 evidence_refs에 어떤 청크를 썼는지 기록.
5. admin_api GET /evidence/{policy_id} 구현.
6. tests/test_rag.py: 코퍼스 로더 4종, 검색 결과에 idiom 문서가 포함되는지, RAG off일 때 프롬프트가 Phase 1과 바이트 동일한지.
7. scripts/rag_ablation.py: demo OAS 7개로 {off, code만, +idiom, +policy, +cve} 5가지 설정 분류 실행 → label 정답률 표 출력.

검증: 테스트 통과. ablation 표를 보고하고, 정답률이 off보다 떨어지는 조합이 있으면 그 사실도 적어. 조합은 내가 고른다.


[5] C — Slack/Discord 알림 + 탐지 설명 LLM + CVE 수집기
전부 비동기 워커. 프록시 코드는 건드리지 않는다.

1. admin_api/workers/alerts.py: detections에 BLOCK(enforce) 또는 would_block=true(observe) 레코드가 들어오면 BLADE_SLACK_WEBHOOK / BLADE_DISCORD_WEBHOOK으로 발송. 실패 시 로그만, 재시도 1회. 메시지: "[BLADE {mode}] {sub} → {method} {path} · 정책 {policy_id}({label}) · {reason}". 같은 (sub, policy_id) 1분 내 중복은 1건으로 합침.
2. GET/PUT /settings/alerts 구현, 대시보드에 알림 설정 화면 추가 (webhook 입력 + 테스트 발송 버튼).
3. admin_api/workers/explain.py: BLOCK/would_block 레코드에 대해 LLM 호출로 한국어 설명 1~2문장 생성 → POST /detections/{id}/explanation. 입력은 값 마스킹(sub·id는 그대로, 바디는 안 보냄). BLADE_EXPLAIN_ENABLED=false면 스킵. 알림 메시지에 설명이 있으면 붙임(없으면 설명 없이 먼저 발송, 나중에 채우지 않음).
4. pipeline/rag/cve_collector.py: NVD API 2.0에서 키워드(IDOR, "object level authorization", "insecure direct object")로 수집 → {cve_id, summary, cwe, published, refs}를 JSONL로 저장 + [4]의 cve 컬렉션에 적재. NVD_API_KEY 없으면 rate limit 맞춰 느리게. 대시보드 정책 상세에 "근거 CVE" 탭.
5. tests/test_alerts.py (webhook mock, 중복 합침), tests/test_explain.py (LLM mock, off 시 호출 0회), tests/test_cve_collector.py (응답 fixture 파싱).

검증: 테스트 통과. 실제 Slack 테스트 채널에 enforce 차단 1건 + observe would_block 1건 도착 스크린샷. 설명문 포함된 메시지 예시 1건.


[6] B — Background LLM 재분석 루프
admin_api/workers/reanalysis.py + 저장소 API.

1. 트리거 3종 (BLADE_REANALYSIS_* 환경변수로 임계값):
   a. label=manual_review_required 정책에 OBSERVE 로그가 THRESHOLD(기본 20)건 누적
   b. 정책 롤백(ACTIVE→PENDING) 발생
   c. observe 모드 정책의 would_block 비율이 같은 sub 다수에서 높음 (정상 사용자를 막을 가능성 → 오탐 의심)
2. 재분석 입력: 정책 원본 + 해당 엔드포인트의 OBSERVE/would_block 로그를 fingerprint로 중복 제거한 요약 (sub·id 값은 마스킹, 패턴만: "서로 다른 sub 12명이 각자 다른 id 접근", "admin 역할 sub가 타인 id 접근 후 would_block") + [3] controller 신호 + [4] RAG 근거.
3. LLM 출력: 새 분류 결과 → proposals 테이블에 저장 (policy_id, proposed_yaml, diff_summary, reason, created_at). 원본 정책은 건드리지 않는다.
4. API: GET /policies/{id}/proposals, POST /proposals/{pid}/accept (정책 교체, version+1, source=reanalysis, mode=observe로 리셋), POST /proposals/{pid}/dismiss.
5. 같은 정책에 대기 중 제안이 있으면 새로 만들지 않음.
6. tests/test_reanalysis.py: 트리거 3종 각각, fingerprint 중복 제거, accept 후 version 증가·mode 리셋, 대기 제안 있으면 스킵.

검증: 테스트 통과. demo에서 /users/{userId}(manual_review) 정책에 OBSERVE 20건 넣고 워커 실행 → 제안이 생기고 label이 owner_or_admin인지 보고.


[7] A — 재분석 트리거 연동 + 성능 가드
1. proxy에서 롤백·would_block 이벤트를 admin_api로 보내는 경로가 [6]의 트리거와 연결되는지 확인. 프록시는 이벤트만 쏘고 판단은 admin_api 워커.
2. 프록시 critical path 감사: 요청 1건 처리 중 외부 호출이 Redis·DB lookup·백엔드 포워딩 3개뿐인지 코드로 확인하고 docs/critical-path.md에 호출 순서 적어. 알림·설명·관측률 전송이 전부 fire-and-forget인지.
3. 부하 테스트 스크립트 scripts/load_test.py: 동시 50/100/200, 30초, p50/p95/p99·에러율. 캐시 콜드/웜 각각.
4. 결과가 Phase 1 대비 p95 +5ms 넘으면 원인 프로파일링해서 보고 (수정은 하지 말고).

검증: critical-path.md + 부하 테스트 결과표.


[8] C — 정책 diff 뷰 + Phase 2 통합 테스트
1. 대시보드: 정책 상세에 "제안" 탭 — 현재 YAML vs 제안 YAML 나란히 diff(변경 줄 하이라이트), reason 표시, accept/dismiss 버튼. 정책 목록에 mode 뱃지(observe/enforce)와 enforce 전환 토글. 관측률 위젯(GET /metrics/observability). 탐지 로그에 would_block 필터와 explanation 컬럼.
2. scripts/phase2_e2e.py — 전체 루프 1회 완주, 각 단계 PASS/FAIL 출력:
   1) /generate (RAG on, controller 신호 포함) → 7 PENDING
   2) 전부 approve → 전부 mode=observe
   3) user_99 → GET /orders/1042 → 200 + OBSERVE + would_block=true
   4) orders 정책 enforce 전환 → 같은 요청 403 + Slack 알림 + explanation 채워짐
   5) /users/{userId}(manual_review)에 OBSERVE 20건 → 재분석 제안 생성
   6) 대시보드 API로 제안 accept → version 2, label owner_or_admin, mode observe
   7) 롤백 → 재분석 트리거 b 발동 확인
   8) GET /metrics/observability rate > 0
   9) Redis 중단 후 3) 재실행 → 여전히 200 + OBSERVE
3. verification/phase2/ 에 Phase 1과 같은 형식으로 요청·응답 전문 + SUMMARY.md 저장.

검증: phase2_e2e.py 9단계 전부 PASS. Phase 1 demo.py도 여전히 PASS. 수정한 소스 파일 목록 보고.


실행 순서와 우선순위
순서
명령
축
우선
비고
1
[0]
사람
-
AGENTS.md 직접 수정
2
[1] 모드·관측률
A
P0
[5][6][8]의 전제
3
[3] Controller AST
B
P0
[1]과 병렬 가능
4
[2] Redis·실패분기
A
P1


5
[4] RAG
B
P0
[3] 뒤
6
[5] 알림·설명·CVE
C
P0
[1] 뒤. CVE 부분은 P2라 밀리면 빼도 됨
7
[6] 재분석
B
P0
[3][4] 뒤
8
[7] 트리거·성능
A
P1
[6] 뒤
9
[8] diff뷰·통합
C
P0
마지막

드롭 순서 (일정 밀리면): [5]의 CVE 수집기 → [7]의 부하 테스트 → [2]의 pub/sub(폴링 유지) → SMS(이 세트에 애초에 없음).
Phase 3 착수 조건: [8] 통합 PASS. 그 전에 Fine-tuning 시작하지 말 것 — 베이스라인 측정이 RAG·Controller 신호 포함 프롬프트로 이루어져야 비교가 성립한다.

