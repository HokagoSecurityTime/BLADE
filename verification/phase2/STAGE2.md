# [2] Redis·실패 분기 검증

2026-10-08. **164 passed, 1 skipped, 2 warnings in 15.35s**.
[전체 테스트 로그](stage2-pytest.txt). 기존 Phase 1 테스트 소스는 수정하지 않았다.

| 실제 검증 | 결과 |
|---|---|
| Redis pub/sub로 enforce 반영 | PASS, 약 62ms (폴링 간격은 3초) |
| rollback → 매칭 해제, 재승인 → observe 매칭 | PASS |
| Redis 컨테이너 kill 후 타인 주문 GET | PASS, HTTP 200 / OBSERVE / would_block=true |
| Redis 중단 중 enforce 변경 | PASS, admin 폴링으로 반영, HTTP 403 |
| Redis 재시작 후 observe 변경·요청 | PASS, HTTP 200 |

검증용 프로젝트 `blade-phase2-redis`의 Redis 컨테이너만 kill/start했다. Redis는 Docker `redis:7-alpine`, demo/admin/proxy는 임시 SQLite를 사용하는 로컬 실제 HTTP 서버다. 3개 앱 전체가 Docker 안에서 실행된 검증은 아니다. 기존 `blade-recording-01` 컨테이너·데이터는 변경하지 않았다.

- [요청·응답 및 Docker 명령 출력](stage2-http.txt)
- [기계 판독 결과](stage2-live-result.json)
- 재현 스크립트: `verification/phase2/verify_stage2.py`
- [실패 동작 명세](../../docs/failure-modes.md)
- 신규 실패 테스트 18개: Redis 단절·TTL·복구·비활성화, DB 타임아웃/예외와 mode/fail_mode 조합, 잘못된 정책, admin 다운, 백엔드 다운, JWT 시크릿 누락.

Phase 1 Compose 서비스 목록을 고정 검증하는 기존 테스트를 유지하기 위해 Redis 추가는 `docker-compose.phase2.yml`에 분리했다. 두 파일을 함께 사용하는 실제 Compose 명령으로 Redis 서비스를 기동했다. 호스트 검증용 `redis-host.yml`은 포트 16379를 loopback에만 노출한다. 일반 Phase 2 구성은 Redis 포트를 호스트에 노출하지 않는다.
