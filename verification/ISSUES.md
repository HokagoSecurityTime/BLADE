# Issues

## 2026-09-14 녹화 검토

- 영상 약 01:22의 소유자 조회가 `/orders/1042` 대신 `/orders/104`여서 404였다. 원인: URL 끝의 `2` 누락. 후속 정확한 `/orders/1042` 조회는 200이었다. 코드 수정 없음.
- 생성/승인 409 구간은 이미 완료된 작업 재실행 때문이며 새 생성/승인 성공 장면으로 사용할 수 없다.
- 탐지 JSON이 길어 이번 요청과 BLOCK/OBSERVE의 연결이 영상에서 명확하지 않다. DB 읽기 전용 조회에서는 request_id로 실제 기록을 확인했다.
- 상세: [영상 검토](VIDEO_REVIEW_2026-09-14.md).

요청한 11개 검증 항목에서 FAIL은 발견되지 않았다. 아래 관찰 사항은 기록만 하고 수정하지 않았다.

- JWT 경고: 기존 HS256 시크릿이 19바이트여서 PyJWT의 InsecureKeyLengthWarning이 발생했다. 원인 추정: 기존 데모 환경변수의 짧은 시크릿. 시크릿·코드 모두 변경하지 않았다.
- 실행 도구 종료 코드: PowerShell 리다이렉션 명령은 exit_code=1로 보고됐지만, 검증 스크립트는 SUMMARY/ISSUES를 저장하고 `COMPLETE: 11/11 PASS`까지 출력했다. 원인 추정: stderr의 위 경고를 PowerShell이 NativeCommandError로 취급한 영향. 이 실행 도구 결과를 exit 0으로 표기하지 않았다.
- 사용자 조회 정책은 실제 LLM이 manual_review_required로 생성했다. 이번 step1의 기대값은 정책 7개 생성이므로 PASS지만, 해당 경로가 owner_or_admin으로 강제 차단된다고 해석하면 안 된다. 정책 수정은 하지 않았다.
