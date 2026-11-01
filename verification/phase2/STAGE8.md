# [8] UI·통합 검증 (2026-10-12 재개)

최신 개선 이미지 배포와 설정 보존·로그 저장 확인 완료: [배포 결과](deployment-improved-result.json), [최종 상태](FINAL_STATUS.md). 기존 전체 LLM 통합 9/9 기록을 보존하며, 이번 배포에서는 해당 전체 루프를 재실행하지 않았다.

후속 실제 Slack 검증 완료: #blade-alert에서 observe/enforce 두 메시지를 사용자가 확인했다. [실제 전송 결과](slack-live-20261012-184110/results.json), [최신 개선 보고서](IMPROVEMENTS.md). 아래의 Slack 보류 및 설명 모순 기록은 개선 전 상태다.

## 브라우저 UI: PASS

현재 소스로 `blade-dashboard:phase2-resumed` 이미지를 빌드하고 정적 파일을 추출해 격리된 로컬 HTTP 서버와 Edge headless에서 검증했다. 실행 중인 대시보드는 교체하지 않았다.

- observe → enforce 전환 후 실제 프록시 응답 403.
- 명시적인 UI용 제안 fixture의 YAML diff 표시, 수락 후 version=2 / observe / 응답 200.
- 별도 제안 기각, CVE 근거 없는 상태, would_block 필터, 모바일 화면 확인.
- 브라우저 JavaScript 오류 0건. [결과](stage8-browser.json), [diff 화면](stage8-proposal-diff.png), [탐지 화면](stage8-detections.png), [모바일](stage8-mobile.png).

이전 정적 파일과 컨테이너 이미지 모두 최신 소스보다 오래되어 CVE 탭 검증이 실패했다. 새 빌드 후 해당 단계가 통과했다. 메뉴 아이콘이 접근성 이름에 포함되므로 검증 스크립트의 탐지 로그 선택자를 nav 내부 부분 일치로 수정했다. 실패 로그도 보존했다.

## 회귀: PASS

[resumed-pytest.txt](resumed-pytest.txt): **179 passed, 1 skipped**, 경고 2건. 실제 LLM을 호출하는 테스트 1개는 provider 미설정으로 건너뛰었다. Phase 1 원본 테스트 17개의 SHA-256이 시작 전 기록과 모두 일치했다.

[Phase 1 demo 7단계](phase1-demo-resumed.json)는 실제 로컬 HTTP 서버와 저장된 분류 응답을 사용하는 기존 테스트로 통과했다. 이는 새 실제 LLM/Docker demo 실행을 뜻하지 않는다.

## 실제 LLM 통합: 9/9 PASS (외부 Slack 보류)

`scripts/phase2_e2e.py`를 새 DB 디렉터리 `e2e-20261012-resumed`에서 실행했다. Ollama qwen2.5:7b, E5/Chroma code+idiom, 실제 HTTP/SQLite/Redis와 로컬 Slack 형식 수신기를 사용한다. 외부 Slack 도착 확인은 기존 보류 사항이다. manual-review 시작 상태는 명시적인 fixture이고 실제 생성 결과를 별도 보존한다.

전용 Redis: `blade-phase2-e2e-20261012`, `127.0.0.1:16382`, 라벨 `blade.verification=phase2-e2e`. 스크립트는 컨테이너와 URL을 필수로 받고 라벨/포트를 검사한 뒤 고정된 컨테이너 ID만 중단·복구한다. 기존 Redis 기본값을 제거했다.

최종 결과: [9단계 요약](e2e-20261012-resumed/SUMMARY.md), [결과 JSON](e2e-20261012-resumed/results.json), [통합 로그](e2e-20261012-resumed.log), [Redis 중단·복구 기록](e2e-20261012-resumed/redis.txt). 관측률은 1.0이었다. Redis 중단 중 200 / OBSERVE / would_block를 확인했고 재시작 후 PING=PONG을 확인했다. 종료 후 Docker 조회에서 기존 검증·시연 서비스와 기존 Redis의 실행 시간이 유지되고 healthy 상태임을 확인했다. 이번 전용 Redis는 복구된 실행 상태로 남겼다.

검증 한계: 4단계는 설명의 생성·저장을 검사하며 의미 정확성을 검사하지 않는다. 실제 설명문에 차단 여부 모순이 있어 [ISSUES.md](ISSUES.md)에 추가했다. 외부 Slack 도착은 보류되어 로컬 수신기만 검증했다. 이전 부하 측정의 성능 기준 미달도 그대로 유지한다.

실행 래퍼 참고: `*>`로 Python stderr를 합친 Windows PowerShell 호출은 예상된 Redis 장애 경고를 NativeCommandError로 기록하고 종료 코드 1을 반환했다. Python 자체 종료 코드는 별도 보존하지 않았다. 로그에는 traceback이 없고, 9개 PASS 결과·최종 요약·복구 PONG이 모두 남았다. 따라서 셸 종료 코드 0을 주장하지 않으며 저장된 검증 결과로 9단계 통과를 보고한다.

이번 재개 작업에서 수정한 실행 소스는 `scripts/phase2_e2e.py`(전용 Redis 필수 지정·라벨/포트 검사·ID 고정·복구 PING)와 `verification/phase2/verify_phase2_ui.py`(메뉴 선택자·enum fixture)다. 제품 소스는 수정하지 않았다. 현재 UI 소스를 새 이미지로 빌드했으며 기존 서비스에 배포하지 않았다.
