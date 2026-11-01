# Presentation verification

코드 수정 없이 실제 LLM·새 검증 DB로 실행했다. 아래 11개 항목은 모두 PASS다.
서비스 기동을 추가한 이유: step1~7(7개) + break1~2(2개) + 백엔드 미도달(1개)는 총 10개다.
기존 시크릿 경고와 실행 도구 exit_code=1 표시는 [ISSUES.md](ISSUES.md)에 별도로 기록했다.

Run UTC: 2026-09-13T12:18:56.720913+00:00

The requested list has 10 checks; service startup/log capture is the 11th item.

| Item | Expected | Actual | Result |
|---|---|---|---|
| services | 9000/8100/8080 listening; stdout/stderr logs | ready=True, logs=True | PASS |
| step1 | 7 PENDING policies | HTTP 200; policies=7 | PASS |
| step2 | 7 approvals HTTP 200; ACTIVE list has 7 | approvals=[200, 200, 200, 200, 200, 200, 200]; ACTIVE=7 | PASS |
| step3 | user_99 GET -> 403 | 403 | PASS |
| backend_untouched | step3 403; backend log line delta=0 | HTTP 403; 4 -> 4 lines | PASS |
| step4 | user_77 GET -> 200 | 200 | PASS |
| step5 | DELETE 403; owner GET 200 | 403; 200 | PASS |
| step6 | no Authorization -> 403 | 403 | PASS |
| step7 | BLOCK >=3; step3/5/6 request IDs match | BLOCK=3; matched=True | PASS |
| break1 | tampered sub with original signature -> 403 | 403 | PASS |
| break2 | non-5xx response; OBSERVE log | HTTP 404; OBSERVE=True | PASS |

Source files changed: []

Services remain running. PIDs: presentation-processes.json. Logs: logs/*.log.
Runtime data: presentation-runtime/ (fresh SQLite and generated policies). Existing Docker volumes are unchanged; previous containers are stopped.
HTTP evidence contains complete request/response headers and bodies, including the requested demo Bearer tokens.
Backend non-arrival is supported by unchanged access-log lines; this is not a packet capture. No health requests run against the backend during step3.

## 직접 재현

- [COMMANDS.md](COMMANDS.md): Git Bash에서 복사할 curl 명령 및 실제 테스트 토큰.
- 토큰 유효기간은 발급 후 48시간이며 정확한 만료 시각은 COMMANDS.md에 기록했다.
- 생성과 승인은 이미 완료됐다. 현재 상태에서 step1/step2를 다시 실행하면 409가 날 수 있으므로 녹화는 step3부터 진행하면 된다.
- 이번에는 로컬 백그라운드 프로세스로 실행했다. 기존 Docker 컨테이너(대시보드·알림 포함)는 중지했고 데이터/볼륨은 보존했다. 현재 localhost:3000 대시보드는 실행하지 않는다.
- 9000/8100/8080의 검증 서비스는 계속 실행 중이다. 재부팅하면 자동 재시작되지는 않는다.
