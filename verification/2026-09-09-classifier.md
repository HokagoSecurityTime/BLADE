# 오프라인 분류기 검증

후속 Ollama 검증에서 **pytest 37개 통과 및 실제 CLI 6/7**을 확인했습니다.
현재 완료 결과는 [Ollama 검증 기록](2026-09-09-classifier-ollama.md)을 참고하세요.
아래는 OpenAI 크레딧 소진 당시 기록입니다.

- 날짜: 2026-09-09 (Asia/Seoul)
- 환경: Windows, Python 3.11.9, pytest 9.1.1
- 최신 검증: **32 passed, 1 failed in 150.93s** (실제 LLM 테스트 실패)
- 실제 LLM 정확도: **미측정 — API 크레딧 소진**
- 이 단계의 전체 완료 조건인 실제 LLM 6/7 이상은 아직 확인하지 못했습니다.

## API 키 설정 후 재검증

사용자가 저장한 API 키를 출력하지 않고 검증 프로세스 환경으로 전달했습니다.
애플리케이션은 계속 환경변수만 읽습니다. 사용 모델은 `gpt-4o-mini`입니다.

첫 실제 호출에서 HTTP 400이 발생했습니다. JSON 모드가 사용자 입력에도 `json` 문자열을
요구했기 때문에 `prompt.py`의 입력에 `"output_format": "json"`을 추가했습니다.
mock 테스트에서도 해당 입력 필드를 검사하도록 보강했습니다.

수정 후 `pytest tests/test_classifier.py` 실행 결과:

```text
collected 33 items
tests\test_classifier.py ................................F               [100%]
FAILED tests/test_classifier.py::test_real_llm_demo
1 failed, 32 passed in 150.93s (0:02:30)
```

오류 원인을 확인하기 위한 단일 요청에서 다음 API 오류를 확인했습니다.

```json
{"status":429,"type":"insufficient_quota","code":"credit_balance_exhausted"}
```

제공자가 API 크레딧 잔액 소진을 명시했습니다. 7개 입력은 실제 모델 분류 결과를 받지 못해
`manual_review_required`로 탈출했고 테스트 기대값과의 일치는 0/7이었습니다.
이는 모델 정확도 0%라는 의미가 아니라 호출 실패입니다.
테스트 통과 후 실행하도록 요청된 별도 평가 CLI는 이번 재검증에서 실행하지 않았습니다.
추가 유료 호출을 반복하지 않았으며 실제 분류 JSON도 생성하지 않았습니다.
API 크레딧 복구 후 테스트 및 별도 CLI 검증을 재개해야 합니다.

| 엔드포인트 | 기대 label | 이번 결과 |
| --- | --- | --- |
| GET /public/health | public | manual_review_required — 호출 실패 |
| GET /orders/{orderId} | owner_match | manual_review_required — 호출 실패 |
| DELETE /orders/{orderId} | owner_match | manual_review_required — 호출 실패 |
| GET /users/{userId} | owner_or_admin | manual_review_required — 호출 실패 |
| GET /admin/reports | role_required | manual_review_required — 호출 실패 |
| GET /orgs/{orgId}/docs | tenant_match | manual_review_required — 호출 실패 |
| GET /premium/content | membership_required | manual_review_required — 호출 실패 |

## 구현

- `pipeline/classifier/llm.py`: OpenAI Responses, Anthropic Messages 호출.
  HTTPX 각 I/O 타임아웃 60초, 전송 오류·429·5xx에 최대 2회 재시도(총 3회).
- Phase 1 제공자/모델: 사용자 지정 `openai` / `gpt-4o-mini`.
  Ollama는 사용자 요청으로 구현을 유보하고 환경변수 선택값만 예약했습니다.
  선택하면 네트워크 요청 없이 미구현 오류를 반환합니다.
- `prompt.py`: 요청한 결정 트리 원문과 JSON 전용 출력 규칙. 엔드포인트·ERD·선택적 controller 입력.
- `schema.py`: Pydantic 검증, 미지 label 및 confidence < 0.7의 manual review 전환.
- `classify`: 잘못된 JSON, 호출 실패, 존재하지 않는 객체 파라미터·테이블·컬럼도 manual review 처리.
- `run.py`: 실제 제공자로 데모를 분류하고 기대값과 비교하는 표 및 선택적 JSON 출력.
  기대 label은 채점에만 사용하며 LLM 입력에는 넣지 않습니다.
- Fine-tuning, RAG, 런타임 프록시 호출은 추가하지 않았습니다.

## 이전 실행 결과 (API 키 설정 전)

```powershell
$env:PATH = "C:\BLADE\.python;C:\BLADE\.python\Scripts;" + $env:PATH
pytest tests/test_classifier.py
```

```text
collected 33 items
tests\test_classifier.py ................................s               [100%]
======================== 32 passed, 1 skipped in 0.34s ========================
```

검증 범위: 7개 엔드포인트의 mock 응답 처리, 잘못된 JSON·미지 label·저신뢰도·잘못된 자료형,
0.7 경계값, ERD에 없는 컬럼, 제공자 실패, OpenAI/Anthropic의 HTTP 요청/응답 형식,
60초 타임아웃 설정, 재시도 횟수, 재시도 후 복구, 불완전 응답 거부, Ollama 미구현 분기의 외부 호출 없음.
제공자가 설정되지 않아 실제 LLM 테스트 1개는 조건부 skip했습니다.

그 다음 요청된 명령을 실행했습니다.

```powershell
python -m pipeline.classifier.run demo_backend/openapi.json demo_backend/schema.sql
```

```text
Configuration error: Set BLADE_LLM_PROVIDER to openai, anthropic or ollama
```

프로세스 및 사용자·시스템 환경에 제공자, 모델, OpenAI/Anthropic API 키 설정이 없었습니다.
실제 네트워크 요청 전 설정 검사에서 중단되었습니다. API 키 값은 출력하지 않았습니다.

이후 사용자가 제공자를 OpenAI, 모델을 `gpt-4o-mini`로 지정했습니다.
이 두 값을 검증 프로세스 환경에 설정하고, `.env`가 존재하면 `OPENAI_API_KEY` 항목만
프로세스 환경으로 전달하는 방식으로 CLI를 다시 실행했습니다. 결과:

```text
Configuration error: Set OPENAI_API_KEY
```

당시 차단 요인은 API 키 미설정이었습니다. 실제 결과 JSON은 생성되지 않았습니다.

## 이전 mock 검증 결과

아래 mock 통과는 응답 처리 검증이며 실제 모델의 분류 정확도를 의미하지 않습니다.

| 엔드포인트 | 기대 label | Mock 검증 | 실제 LLM label |
| --- | --- | --- | --- |
| GET /public/health | public | 통과 | 미측정 |
| GET /orders/{orderId} | owner_match | 통과 | 미측정 |
| DELETE /orders/{orderId} | owner_match | 통과 | 미측정 |
| GET /users/{userId} | owner_or_admin | 통과 | 미측정 |
| GET /admin/reports | role_required | 통과 | 미측정 |
| GET /orgs/{orgId}/docs | tenant_match | 통과 | 미측정 |
| GET /premium/content | membership_required | 통과 | 미측정 |

## 실행 설정

`BLADE_LLM_PROVIDER`와 `BLADE_LLM_MODEL`, 선택한 클라우드 제공자의 API 키를 프로세스 환경에 설정해야 합니다.
Phase 1은 OpenAI `gpt-4o-mini`로 검증합니다. 애플리케이션은 `.env`를 자동 로드하지 않습니다.
설정 후 위 CLI를 실행하고 `--output verification/classifier-live.json`을 붙이면 실제 결과를 보존할 수 있습니다.

이미지 자료는 없으며 터미널 출력 기반 기록입니다.

## 구현 참고 공식 문서

- [OpenAI Responses API](https://developers.openai.com/api/reference/typescript/resources/beta/subresources/responses/methods/create)
- [Anthropic Messages API](https://platform.claude.com/docs/en/api/messages/create)
- [GPT-4o mini 공식 모델 문서](https://developers.openai.com/api/docs/models/gpt-4o-mini)
