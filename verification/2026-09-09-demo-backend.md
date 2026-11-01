# 데모 백엔드 검증 결과

- 검증일: 2026-09-09 (Asia/Seoul)
- 작업 경로: `C:\BLADE`
- 결과: 요청된 검증 완료
- 실행 환경: Windows PowerShell, Python 3.11.9, pytest 9.1.1
- Python 위치: `C:\BLADE\.python\python.exe`

이 문서는 앞선 검증에서 확인한 실제 실행 결과를 기록한 것입니다. 문서 작성 시 테스트를 다시 실행하지 않았습니다.

## 테스트 실행

PowerShell 세션에서 실행 경로를 설정했습니다.

```powershell
$env:PATH = "C:\BLADE\.python;C:\BLADE\.python\Scripts;" + $env:PATH
pytest tests/test_demo_backend.py
pytest tests/test_schema.py
```

| 대상 | 결과 | 실행 시간 |
| --- | --- | --- |
| `tests/test_demo_backend.py` | 8 passed, 2 warnings | 1.10초 |
| `tests/test_schema.py` | 2 passed | 0.18초 |

데모 테스트에서 다음 7개 요청의 HTTP 200 응답을 확인했습니다. 각 테스트는 독립된 임시 SQLite DB를 사용했습니다.

| 메서드 | 경로 |
| --- | --- |
| GET | `/public/health` |
| GET | `/orders/1042` |
| DELETE | `/orders/1042` |
| GET | `/users/user_77` |
| GET | `/admin/reports` |
| GET | `/orgs/org_1/docs` |
| GET | `/premium/content` |

추가로 DELETE 이후 같은 주문을 조회하면 404가 반환되는 것을 확인했습니다.
`user_99`의 HS256 JWT를 Authorization 헤더에 담아 `/orders/1042`를 조회했을 때 HTTP 200과 아래 응답을 확인했습니다. 이는 의도적으로 인가 검사를 생략한 백엔드의 BOLA 취약성 재현 결과입니다.

```json
{"id": 1042, "user_id": "user_77"}
```

공통 스키마 테스트에서는 정책 YAML과 모델의 왕복 변환, confidence 범위 위반 거부, 문서화된 JWT 클레임 구조, Label 7종을 확인했습니다.

## 서버 기동 및 OpenAPI 생성

```powershell
.\.python\Scripts\uvicorn.exe demo_backend.main:app --port 9000
.\.python\python.exe -m demo_backend.export_openapi --url http://127.0.0.1:9000
```

서버 출력:

```text
INFO:     Started server process [8876]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:9000 (Press CTRL+C to quit)
```

- 실행 중인 서버의 `/openapi.json`에서 HTTP 200으로 문서를 받아 [demo_backend/openapi.json](../demo_backend/openapi.json)에 저장했습니다.
- 저장된 문서를 JSON으로 읽어 `app.openapi()`와 동일함을 확인했습니다.
- 문서에 HTTP 메서드 기준 API 작업 7개가 포함되어 있음을 확인했습니다.
- 실제 서버의 `/public/health` HTTP 200 응답을 확인했습니다.
- 검증 완료 후 검증용 서버를 종료했습니다.

## SQLite 시드 확인

서버 시작으로 생성된 `demo.db`를 직접 조회하여 다음 데이터를 확인했습니다.

| 테이블 | 확인한 데이터 |
| --- | --- |
| orgs | `org_1`, `org_2` |
| users | `user_77 / org_1 / user / basic` |
| users | `user_99 / org_2 / user / basic` |
| users | `admin_1 / org_1 / admin / premium` |
| orders | `1042 → user_77`, `2001 → user_99` |

DDL: [demo_backend/schema.sql](../demo_backend/schema.sql)

OpenAPI·실서버 health·시드 데이터 검사 스크립트의 최종 출력:

```text
Verified: live health 200, OpenAPI 7 operations matches app, SQLite seeds correct
```

## 경고 및 자료

데모 테스트에서 의존성 관련 deprecated 경고 2건이 발생했으며, 테스트 실패는 없었습니다.

1. Starlette TestClient에서 `httpx` 사용이 deprecated라는 경고.
2. `anyio.abc.BlockingPortal` 별칭 대신 `anyio.from_thread.BlockingPortal`을 사용하라는 경고.

검증 당시 캡처한 이미지 자료는 없습니다. 위 실행 결과는 터미널 출력에서 옮긴 기록이며, 별도 원본 로그 파일은 저장하지 않았습니다.
