# [1] 관찰·집행 모드 및 관측률

2026-10-08, Windows / Python 3.11. 기존 서비스 데이터와 운영 중 컨테이너는 변경하지 않았다.

## 결과

`BLADE_LLM_PROVIDER='' .python/python.exe -m pytest -q` (PowerShell에서는 환경변수를 별도로 설정)

**136 passed, 1 skipped, 2 warnings in 10.21s**

| 검증 | 결과 |
|---|---|
| 기존 Phase 1 테스트, 소스 변경 없이 실행 | 128 PASS, 실제 LLM 1 SKIP |
| observe 타인 주문 조회 | HTTP 200, OBSERVE, would_block=true |
| enforce 전환 후 같은 요청 | HTTP 403, BLOCK, would_block=false |
| rollback → PENDING → 재승인 | mode=observe |
| PENDING 정책 mode 전환 | HTTP 409 |
| 최근 60초 관측률: 빈 윈도우 / 매칭 없음 / 부분 매칭 | PASS |
| 여러 프록시 보고 합산 및 중복 snapshot 교체 | PASS |
| 구형 SQLite의 확장 필드 마이그레이션 | PASS |
| Phase 2 비활성화 시 기존 차단 및 로그 형식 유지 | PASS |
| demo.py 7단계, Phase 2 승인 후 enforce 전환 포함 | PASS |

HTTP 검증은 격리된 임시 SQLite와 실제 로컬 HTTP 서버를 사용했다. demo.py 검증의 분류기는 저장된 Phase 1 응답으로 대체했다. 실제 LLM 재분류나 Docker 검증은 이 결과에 포함하지 않는다.

## 사용 및 의미

- admin-api와 proxy 모두 `BLADE_PHASE2_ENABLED=true`로 시작하면 활성화된다. 기본값 false로 기존 Phase 1 판정 동작을 보존한다.
- 개별 비활성화: `BLADE_MODE_ENABLED=false`, `BLADE_OBSERVABILITY_ENABLED=false`.
- `POST /policies/{id}/mode`에 `{"mode":"enforce"}` 또는 `{"mode":"observe"}`를 보낸다. ACTIVE 정책에만 허용한다.
- 승인 시 항상 observe. 모드가 없는 기존 YAML도 observe로 읽는다. Phase 2를 끄면 mode 필드와 관계없이 Phase 1처럼 차단한다.
- `rate = with_policy / total` (0~1, 빈 윈도우는 0). `lookup_ok`는 오류 없이 끝난 소유권 조회 요청 수이며 캐시 적중과 행 없음도 포함한다. 조회를 생략하는 public/역할/관리자 우회는 포함하지 않는다.
- 프록시는 최근 60초 요청을 집계해 1초마다 백그라운드로 POST한다. admin은 프록시별 최신 snapshot을 합산하고 60초간 보고 없는 항목을 제외한다. 네트워크 지연만큼 조회 결과가 늦을 수 있다. 보고는 영속 저장하지 않는다.
- SQLite 확장은 Phase 2 활성화 시 적용한다. 이미 확장된 DB를 비활성화해도 컬럼을 삭제하지 않는다.

## 발견 및 해결

초기 회귀 검증에서 기존 알림 테스트의 9필드 고정 SQL과 로그 DB/JSONL 동일성 검증이 실패했다. 테스트는 수정하지 않고 비활성화 시 9필드 직렬화·기존 DB 형식 유지, 활성화 시 확장 마이그레이션으로 호환성을 보완했다.
