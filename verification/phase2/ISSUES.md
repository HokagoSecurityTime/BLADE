# Phase 2 미해결 항목

**최신 미해결 목록은 [FINAL_STATUS.md](FINAL_STATUS.md)의 '남은 작업·제한'을 우선한다.** warm 100/200 성능, RAG 조직 경로 수동 검토, 복합 장애·강제 종료의 로그 내구성 제한이 남는다. Docker 배포와 로그 전용 AOF Redis 추가는 완료됐고 Slack 설정도 유지됐다. 아래는 과거 기록이다.

최신 상태는 [IMPROVEMENTS.md](IMPROVEMENTS.md)를 우선한다. 아래는 최초 검증 당시 기록이다. 실제 Slack 수신은 사용자 확인 완료, 설명 모순은 판정 기반 대체 문구로 방어, Phase 2 부하 테스트 탐지 로그는 전량 저장됐다. 성능은 6개 중 4개 기준 통과로 개선됐지만 warm 100/200은 아직 미달이다. Redis persistence 및 프로세스 강제 종료 시 로그 내구성은 별도 제한으로 남는다.

| 항목 | 근거 | 상태 |
|---|---|---|
| 고부하 p95 증가 | load-results.md: 6개 조건 중 5개가 +5ms 초과 | 요청대로 프로파일만 수행, 미수정 |
| 탐지 로그 큐 초과 | load-run.log의 Detection queue full | 고부하 로그 누락 가능, 미수정 |
| 실제 Slack 도착 확인 | 사용자가 실제 webhook 검증을 보류 | 로컬 webhook 검증만 완료 |
| 데모 조직 경로의 RAG 분류 | rag-ablation.json: tenant_match 대신 manual_review_required | 수동 검토 필요; 자동 정답 처리하지 않음 |
| LLM 설명의 차단 여부 모순 | e2e-20261012-resumed/results.json 4단계: enforce/BLOCK에 "차단되었습니다"와 "실제 차단이 아닙니다" 동시 출력 | 설명 생성·저장 검증은 통과했지만 의미 정확성은 미달; 미수정 |

해결된 과정상 문제: 재분석 출력 시간 초과/근거 ID 오타는 짧은 출력과 실제 근거 ID 제한 후 실제 LLM 검증을 통과했다. 측정 도구의 Windows 임시 DB 정리 오류는 연결 닫기로 수정했고 원본 측정값은 유지했다. stage6-attempt* 및 load-run.log에 실패 기록을 보존했다.
