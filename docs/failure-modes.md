# 장애 시 동작

아래 표는 Phase 2 활성화 및 정책 `mode=enforce` 기준이다. observe 정책은 BLOCK 판정을 OBSERVE / would_block=true로 바꿔 포워딩한다. `BLADE_FAIL_MODE`는 소유권 DB 조회 실패에만 적용한다.

| 상황 | fail_mode=open | fail_mode=closed | 탐지 verdict / reason | 알림 | 복구 조건 |
|---|---|---|---|---|---|
| Redis 연결 끊김 | TTL 인메모리 캐시 및 admin 폴링으로 계속 평가 | 동일 | 정상 평가 결과 유지; Redis 장애는 운영 warning | 장애 자체 알림 없음; 기존 BLOCK 알림은 별도 워커 설정에 따름 | 캐시는 5초 후 연결 재시도, 정책 구독은 0.5초 간격 재접속; 정책 폴링 간격에 갱신 |
| DB 조회 타임아웃 | 포워딩 | 403, 포워딩 안 함 | OBSERVE 또는 BLOCK / lookup_failed | BLOCK 알림 대상 | DB 복구 후 다음 캐시 미스 조회; SQLite 잠금 대기 제한 2초 |
| DB 조회 예외 | 포워딩 | 403, 포워딩 안 함 | OBSERVE 또는 BLOCK / lookup_failed | BLOCK 알림 대상 | DB 경로·권한·정책 컬럼 수정 후 다음 조회 |
| 정책 YAML/모델 파싱 오류 | 마지막 유효한 전체 스냅샷 유지 | 동일 | 유지한 정책의 기존 verdict / reason; 갱신 warning | 기존 BLOCK 알림만 | 올바른 정책으로 수정 후 폴링/구독 갱신. 최초 정상 스냅샷이 없으면 OBSERVE/no_policy |
| admin-api 다운 | 마지막 유효 스냅샷 유지 | 동일 | 기존 평가 verdict / reason. 탐지 전송 실패는 error 로그 | 해당 요청의 탐지 전달 실패 시 워커 알림도 불가 | admin 복구 후 폴링 또는 재접속; 실패한 탐지 전송은 재시도하지 않는 기존 동작 |
| JWT 시크릿 미설정 | 프록시 시작 거부 | 동일 | 요청을 받지 않으므로 탐지 없음; ValueError | 없음 | BLADE_JWT_SECRET 설정 후 재시작 |
| 백엔드 다운 | 허용 요청은 HTTP 502 | 동일 | 인가 평가는 PASS/OBSERVE 그대로 기록. 전송 실패는 HTTP 502 응답 | PASS 알림 없음 | 백엔드 복구; BLOCK 요청은 원래대로 403이며 백엔드 호출 없음 |

Redis 정책 키는 `blade:policies`(60초 TTL), pub/sub 채널은 `blade:policy`다. 승인·롤백·mode·정책 수정 시 스냅샷을 게시한다. 프록시는 구독 연결 중 알림으로 갱신하며, 유실된 게시를 복구하기 위한 60초 주기 admin 재조회도 유지한다. 구독이 끊기면 기존 `BLADE_POLICY_POLL_SEC` 폴링으로 돌아간다. 재접속 시에는 오래된 Redis 값으로 현재 정책을 덮지 않고 admin을 먼저 조회한다.

소유권 캐시는 DB DSN별 키 영역을 사용한다. Redis 연결 실패를 정책 위반으로 취급하지 않는다. 캐시 무효화 중 장애가 있었다면 재접속 시 해당 키 영역을 지운 뒤 다시 조회한다. Redis 호출은 타임아웃과 즉시 실패 설정을 사용하고 요청 이벤트 루프 밖에서 실행한다. 기존 인메모리 get/set/clear 인터페이스는 유지한다.

`BLADE_REDIS_URL`이 비어 있거나 `BLADE_REDIS_ENABLED=false`, 또는 전체 Phase 2가 꺼져 있으면 Redis를 호출하지 않는다. 장애 테스트는 `tests/test_failure_modes.py`, 기존 Phase 1의 `tests/test_proxy_failures.py`에 있다. 실제 Redis 중단 검증은 별도 검증 기록을 참고한다.
