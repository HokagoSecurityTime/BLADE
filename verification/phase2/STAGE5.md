# [5] 알림·설명·CVE 검증

2026-10-11. 실제 Slack 채널 발송과 스크린샷은 사용자의 기존 요청대로 보류했다. 아래 webhook 증거는 로컬 수신 서버이며 Slack 도착 증거가 아니다.

| 검증 | 결과 | 증거 |
|---|---|---|
| 전체 회귀 | 173 passed, 1 skipped | stage5-pytest.txt |
| enforce / observe, 두 provider, 중복 억제, 재시도 | PASS | test_phase2_alerts.py, stage5-webhooks.json |
| 설명 LLM mock → 실제 HTTP API → SQLite | PASS | test_explain.py |
| 설명 off → LLM 호출 없음, 입력 마스킹 | PASS | test_explain.py |
| NVD 응답 파싱 | PASS | test_cve_collector.py |
| 실제 NVD 수집 (키 없이 요청 간 7초) | 235개 | cve-sample.jsonl, cve-collector.log |
| 알림 설정 화면 | Docker Vite build + 실제 Edge 브라우저 저장·로컬 테스트 발송 PASS | stage5-settings.png, stage5-browser.json |
| 실제 Slack 도착 / 실제 LLM 설명 | 보류 / 통합 단계에서 확인 | mock 결과와 구분 |

알림과 설명은 `python -m admin_api.workers`의 독립 코루틴으로 동작한다. 최초 시작은 과거 탐지를 건너뛰고 이후 SQLite rowid 커서를 저장한다. 설명은 SQLite에 비동기 보강되며 최초 JSONL 이벤트는 원본 그대로 유지한다. 알림은 설명을 기다리지 않고, 이미 설명이 있을 때만 붙인다. 같은 (sub, policy_id)의 observe→enforce도 60초 중복 억제 범위다.

설정 API는 기존 admin-api와 동일한 내부망 전제다. webhook은 SQLite에 저장되고 API로 읽히므로 외부 공개 서비스로 노출하지 않는다. UI는 입력 값을 password 필드로 표시한다.

NVD 참고: https://nvd.nist.gov/developers/start-here , https://nvd.nist.gov/developers/vulnerabilities . 수집 결과는 ablation 실행 중인 인덱스에 넣지 않아 조합 비교 입력을 보존했다.
