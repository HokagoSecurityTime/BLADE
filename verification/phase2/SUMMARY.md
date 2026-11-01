# Phase 2 진행 기록

**최신: [FINAL_STATUS.md](FINAL_STATUS.md).** 개선 코드 Docker 적용 완료, 실제 Slack 설정 보존, 192 passed / 1 skipped, 원본 테스트 17개 해시 일치. 최종 부하에서 Phase 2 로그 120,276건 전량 저장, 성능 4/6 PASS(warm 100/200 미달). 로그 전용 AOF Redis 재시작 보존 검증 완료. 아래는 이전 회차 기록이며 최신 상태와 구분한다.

최신 후속 개선은 [IMPROVEMENTS.md](IMPROVEMENTS.md)를 참고한다. 실제 Slack 수신 확인 완료, 설명 모순 방어 추가, 회귀 **191 passed / 1 skipped**, 전용 Redis 장애 검증 5/5 PASS. 별도 프로세스 부하는 6개 중 4개 기준 통과, Phase 2 로그 129,572건 모두 저장. **warm 100/200 성능은 여전히 미달**이고 실행 중인 Docker 이미지 재배포는 하지 않았다. 아래는 최초 단계 검증 당시 기록이다.

2026-10-08 시작, 2026-10-12 갱신. 기존 Phase 1 서비스 데이터는 유지하며 격리된 DB로 검증한다.

| 순서 | 단계 | 상태 | 근거 |
|---|---|---|---|
| 1 | [0] AGENT.md 확장 | 반영 | 기존 필드를 유지하고 Phase2.md의 추가 스키마·규칙 반영 |
| 2 | [1] 모드·관측률 | PASS | [STAGE1.md](STAGE1.md), 136 passed / 1 skipped |
| 3 | [3] Controller AST | PASS | [STAGE3.md](STAGE3.md), 실제 사용자 조회 owner_or_admin, 전체 146 passed / 1 skipped |
| 4 | [2] Redis·실패 분기 | PASS | [STAGE2.md](STAGE2.md), 실제 Redis kill·복구, 전체 164 passed / 1 skipped |
| 5 | [4] RAG | PASS | [STAGE4.md](STAGE4.md), off 3/7, RAG 6/7; 사용자 선택 code+idiom 반영 |
| 6 | [5] 알림·설명·CVE | 로컬 검증 PASS / 실제 Slack 보류 | [STAGE5.md](STAGE5.md), 173 passed / 1 skipped, 브라우저 설정 저장·로컬 webhook 수신, NVD 235건 |
| 7 | [6] 재분석 | PASS | [STAGE6.md](STAGE6.md), 실제 LLM owner_or_admin 제안, 이전 실패 기록 보존 |
| 8 | [7] 트리거·성능 | 트리거 PASS / 성능 FAIL | [STAGE7.md](STAGE7.md), p95 +5ms 기준 6개 중 5개 미달; 요청에 따라 프로파일만 수행 |
| 9 | [8] UI·통합 | UI PASS / 통합 9/9 PASS (로컬 알림) | [STAGE8.md](STAGE8.md), 전용 Redis 중단·복구 PONG; 실제 Slack 보류·설명문 모순 별도 기록 |

Phase 1 테스트 원본 SHA-256은 [phase1-test-hashes.json](phase1-test-hashes.json)에 보관했다. 기존 테스트는 수정하지 않는다. 실제 LLM을 사용하지 않는 회귀 테스트 실행에서는 provider 환경변수를 비워 해당 테스트 1개를 명시적으로 건너뛴다.

2026-10-12 재개 검증: [179 passed / 1 skipped](resumed-pytest.txt), 원본 테스트 17개 해시 일치. [Phase 1 demo 7단계](phase1-demo-resumed.json)는 실제 로컬 HTTP + 저장된 분류 fixture로 통과했다. 실제 Slack 보류, 고부하 지연과 탐지 큐 초과는 [ISSUES.md](ISSUES.md)에 유지한다.
