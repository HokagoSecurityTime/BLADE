# 프록시 인가 평가 검증 — 2026-09-09

## 구현

`proxy/evaluator.py`, `lookup.py`, `cache.py`, `server.py`에 평가와 차단을 연결했다.
CLAUDE.md가 없어 AGENT.md의 스키마를 따르고 이번 사용자 요청의 동작 규칙을 적용했다.

- public은 PASS. 나머지 label의 claims=None은 BLOCK `no_token` (manual review 포함).
- 인증된 manual review는 OBSERVE. 미매칭 경로는 OBSERVE `no_policy`.
- 조회 행 없음은 PASS `object_not_found`, 백엔드가 404 처리.
- 조회 실패는 open에서 OBSERVE, closed에서 BLOCK. 이유는 `lookup_failed`.
- BLOCK은 GET/DELETE 모두 전달 전에 403 JSON으로 반환.
- SQLite mode=ro, query_only, 식별자 화이트리스트와 값 바인딩을 적용했다. 소유자·테넌트 컬럼만 SELECT하며 작업 스레드에서 실행한다.
- TTL 캐시는 (table, id)를 키로 사용한다. 조회 스키마 서명도 저장하여 다른 정책 조회와 혼용하지 않는다. 없는 행도 캐시한다.
- 정책 변경 및 전달된 쓰기 요청은 캐시를 비운다.
- verdict는 메모리 큐에 즉시 등록하고 별도 task가 POST /detections로 전송한다.

## 검증 결과

로컬 Python 3.11에서 외부 LLM 호출 없이 실행했다.

```text
.python/python.exe -m pytest tests/test_evaluator.py tests/test_proxy_e2e.py -q
28 passed in 1.49s

BLADE_LLM_PROVIDER 미설정
.python/python.exe -m pytest -q
123 passed, 1 skipped, 2 warnings in 4.60s
```

skip은 실제 LLM 테스트다. 경고 2개는 설치된 Starlette/AnyIO의 deprecation 경고다.
이전 회귀 테스트의 401/503 및 forward-only 기대값을 이번 규칙에 맞춰 갱신했다.

## 실제 HTTP E2E

fixture에서 임시 DB로 demo_backend와 admin_api를 uvicorn으로 실행했다.
PENDING 정책을 저장하고 POST /policies/{id}/approve로 승인한 뒤 프록시가 ACTIVE 목록을 HTTP로 가져왔다.
기존 데모 DB·정책은 변경하지 않았다.

| 호출자 | 요청 | 실제 결과 |
| --- | --- | --- |
| user_99 | GET /orders/1042 | 403 |
| user_77 | GET /orders/1042 | 200 |
| user_99 | DELETE /orders/1042 | 403, SQL로 원본 행 유지 확인 |
| admin_1 | GET /users/user_99 | 200 |
| user_99 | GET /admin/reports | 403 |
| user_99 | GET /orders/9999 | 404 (조회 행 없음은 전달) |

403 본문의 error/policy_id/request_id 및 응답 헤더 일치를 확인했다.
프록시 종료 후 JSONL에서 요청 6개, BLOCK 3개, 고유 request_id 6개를 확인했다.
전체 회귀 E2E는 SQLite/JSONL 로그 일치와 정책 승인/롤백도 검증한다.

평가기 테스트는 7 label × 정상/위반 14개, label별 토큰 없음 7개,
fail mode 2개, 없는 행 캐싱, 관리자 우회/중복 query, TTL 만료/clear,
읽기 전용 조회 및 SQL 식별자 검증을 포함한다. 이미지 자료는 없다.

## 운용 범위

관리 API 장애 동안 마지막 정상 ACTIVE 정책을 유지한다. TTL은 소유권 조회 결과에 적용된다.
백엔드를 직접 수정하면 소유권 변경 반영이 TTL 만료까지 지연될 수 있다.
탐지 전송 실패·큐 포화는 서버 로그에 남기며 영구 재전송 큐는 제공하지 않는다.
이전 forward-only 기록은 당시 실행 이력이며 현재 동작은 이 문서 기준이다.
