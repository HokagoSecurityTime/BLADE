# [7] 트리거·성능 검증

최신 [30초 결과](load-packed-final-30s.md): 4/6 PASS, warm 100 +10.63ms / warm 200 +11.00ms로 미달. 로그 120,276건 전량 저장. [배포·남은 제한](FINAL_STATUS.md)을 함께 참고한다.

후속 사용자 요청으로 최적화했다. 최신 [개선 보고서](IMPROVEMENTS.md)와 [별도 프로세스 30초 결과](load-final-process-30s.md)를 우선한다. 6개 중 4개 PASS, warm 100/200 FAIL. Phase 2 탐지 로그는 전량 저장됐다. 아래는 변경 전 기록이다.

[critical path 감사](../../docs/critical-path.md), [30초 부하 표](load-results.md), [원본 측정](load-results.json), [진단 프로파일](load-profile.json).

50/100/200 동시 요청 × cold/warm × Phase 1/2의 12개 측정을 모두 실행했다. HTTP 오류는 모든 조건에서 0건이다. **p95 +5ms 기준은 6개 비교 중 5개에서 FAIL**이다. warm 200에서 +1293.27ms로 가장 큰 증가가 관찰됐다. 이 결과는 같은 프로세스에서 client/admin/backend/proxy를 실행한 Windows 개발 환경의 회귀 검사이며 운영 서버의 용량 수치가 아니다. cold는 서로 다른 실제 주문 행을 조회했고 warm은 동일 주문을 미리 조회했다.

별도 5초 warm 200 진단에서 Redis cache.get 실행 p95는 48.12ms, thread 대기까지 포함한 evaluate p95는 886.35ms였다. Phase 1의 evaluate p95는 0.036ms였다. 두 조건 모두 owner DB 조회는 초기 1회만 발생했다. 따라서 Redis 접근의 직렬화/스레드 풀 대기를 포함한 경로가 주요 병목이라는 근거가 있다. Redis cache.get 내부 RLock이 네트워크 왕복 동안 유지되는 구조도 코드에서 확인했다. 지연 분포는 합산 가능한 값이 아니며, 짧은 진단과 30초 원본 측정을 동일 수치로 취급하지 않는다.

높은 요청량에서는 `Detection queue full`도 발생했다. HTTP 오류 0건은 탐지 로그가 모두 저장됐다는 뜻이 아니다. 큐 초과 시 해당 이벤트를 버리는 기존 동작과 종료 시 5초 드레인 제한 때문에 탐지 로그 손실이 가능하다. 요청에 따라 성능/큐 코드는 수정하지 않았다. 원본 로그: load-run.log.

측정 스크립트 첫 실행은 12개 결과를 JSON에 저장한 뒤 Windows에서 임시 DB 정리 오류로 종료됐다. 시드용 sqlite3 연결을 명시적으로 닫도록 **측정 도구만 수정**하고, 이미 저장된 12개 측정으로 Markdown 표를 생성했다. 프록시 최적화나 측정치 재작성은 하지 않았다. 수정 후 프로파일 실행은 종료 코드 0으로 완료했다.

프록시 would_block → 저장소 → 재분석 트리거, admin rollback → 저장 이벤트 → 재분석 경로는 test_phase2_triggers.py에서 실제 HTTP와 mock LLM으로 검증한다. 실제 LLM과 OBSERVE 20건 연결은 [6]에서 따로 검증했다.
