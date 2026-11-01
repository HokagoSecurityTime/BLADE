# 실험·검증 기록

| 단계 | 기록 | 주요 결과 |
| --- | --- | --- |
| 파란색 대시보드 디자인 | [기록](2026-09-13-dashboard-blue.md) | Docker 빌드, 세 화면·필터·YAML 창·모바일 검증 |
| 대시보드·알림·공격 시뮬레이션 | [기록](2026-09-10-dashboard-alerts.md) | 브라우저 승인/롤백 확인, 70회 탐지율 83.3%·오탐율 0%, Slack 실전송은 요청에 따라 제외 |
| Docker 실제 통합 | [기록](2026-09-10-docker-live.md) | 실제 Ollama·컨테이너 7단계 통과, 승인 1.694초 / 롤백 4.924초 |
| Compose·7단계 데모 | [기록](2026-09-09-compose.md) | 로컬 HTTP 7단계 통과, 전체 125 passed / 1 skipped; Docker 미실행 |
| 인가 평가·조회 캐시 | [기록](2026-09-09-proxy-enforcement.md) | 요청 테스트 28 passed, 전체 123 passed / 1 skipped |
| 데모 백엔드 | [기록](2026-09-09-demo-backend.md) | 7개 API 및 BOLA 재현 |
| OAS·ERD 파서 | [기록](2026-09-09-parsers.md) | 파서 테스트 13개 통과 |
| OpenAI 분류 | [기록](2026-09-09-classifier.md) | 크레딧 소진으로 실제 검증 중단 |
| Ollama 분류 | [기록](2026-09-09-classifier-ollama.md) | qwen2.5:7b 실제 6/7 |
| 관리 API·생성기 | [기록](2026-09-09-admin-api.md) | 실제 PENDING 정책 7개 생성 |
| 런타임 프록시 | [기록](2026-09-09-proxy.md) | 직접 200 → 타인 프록시 403 |
| 전체 서비스 E2E | [기록](2026-09-09-e2e.md) | 7 label·정책 전이·로그 검증, 전체 80 passed/1 skipped |
| 신규 사례·장애·지연 | [기록](2026-09-09-evaluation.md) | 13/14 정답, 로컬 평균 추가 지연 2.246ms, 전체 87 passed/1 skipped |

JSON 결과와 진단 로그는 해당 기록 문서에서 연결합니다. 각 문서의 결과는 당시 실행 기준입니다.
