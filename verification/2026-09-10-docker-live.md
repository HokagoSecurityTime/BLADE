# Docker 설치 및 실제 컨테이너 검증 — 2026-09-10

Docker Desktop 4.90.0을 winget의 Docker.DockerDesktop 패키지로 설치했다.
설치 프로그램 해시 검증과 설치 성공을 확인한 뒤 Docker Desktop을 실행했다.
Docker Engine/CLI 29.7.2, Compose v5.5.1을 사용했다.
공식 설치 참고: https://docs.docker.com/desktop/setup/install/windows-install/

기존 bash.exe는 배포판 없는 WSL 실행 별칭이었다. 스크립트 실행을 위해 Git 2.55.0.3의 Git Bash를 설치했다.
Git Bash의 컨테이너 경로 자동 변환을 방지하도록 scripts/demo.sh에 MSYS_NO_PATHCONV=1을 적용했다.

## 실행 환경

- 새 Compose 프로젝트: `blade-verify-20260910`.
- 새 named volume: 프로젝트의 admin-data, demo-data. 기존 로컬 DB·정책은 유지했다.
- 기존 .env.example에서 없는 .env를 생성했다. 비밀 값은 기록에 포함하지 않았다.
- 기존 호스트 Ollama 모델 qwen2.5:7b를 실제로 호출했다. mock이나 라벨 강제 교체는 없었다.
- 컨테이너에서 host.docker.internal:11434 연결과 모델 로드를 확인했다.
- demo-backend 9000, admin-api 8100, proxy 8080 모두 healthy.

Git Bash에서 다음 명령을 실행했다 (먼저 새 프로젝트의 이미지를 빌드했다):

```bash
export COMPOSE_PROJECT_NAME=blade-verify-20260910
docker compose up -d && bash scripts/demo.sh
```

종료 코드 0.

## 7단계 결과

| 단계 | 결과 |
| --- | --- |
| 1 | 실제 /generate로 PENDING 정책 7개 생성 |
| 2 | 7개 모두 approve |
| 3 | user_99 GET /orders/1042 → 403, 승인 반영 1.694초 |
| 4 | user_77 GET /orders/1042 → 200 |
| 5 | user_99 DELETE /orders/1042 → 403, SQLite의 user_77 주문 행 유지 |
| 6 | 조회·삭제 요청 ID 각각의 BLOCK 로그 2건 확인 |
| 7 | 주문 GET 정책 rollback 후 user_99 요청 → 200, OBSERVE/no_policy, 반영 4.924초 |

승인·롤백 모두 BLADE_POLICY_POLL_SEC=5초 이내였다. 핫리로드 재시도 요청도 로그에 기록되므로
전체 탐지 로그 수는 304건이다. 단계 6은 전체 BLOCK 개수가 아닌 대상 요청 ID 두 건을 확인한다.
최종 정책은 ACTIVE 6개, 주문 GET PENDING 1개다.
사용자 조회 정책은 모델이 manual_review_required로 분류했으며 그대로 유지했다.

## 증거 및 현재 상태

- [명령 출력](compose-live-2026-09-10.log)
- [실제 정책·탐지 로그 JSON](compose-live-2026-09-10.json)

명령 출력 첫 부분의 PowerShell NativeCommandError 표시는 Docker 진행 메시지를 stderr에서 수집하며 붙은 표시다.
실제 명령은 종료 코드 0으로 성공했다. PyJWT의 기존 데모 시크릿 길이 경고도 출력됐으며 시크릿 자체는 기록하지 않았다.
컨테이너는 실행 상태로 남겼다. 검증 종료 시 주문 GET 정책은 롤백 상태다.

```bash
docker compose -p blade-verify-20260910 ps
docker compose -p blade-verify-20260910 stop
```

스크립트는 빈 정책 저장소를 요구한다. 재실험 시 기존 서비스를 중지하고 새 프로젝트명을 사용하면 기존 결과를 보존할 수 있다.
