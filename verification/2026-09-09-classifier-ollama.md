# Ollama 7B 분류기 검증

- 날짜: 2026-09-09 (Asia/Seoul)
- 결과: **pytest 37개 통과, 별도 CLI 6/7 정답(85.7%), 종료 코드 0**
- 제공자: Ollama 0.33.3, 모델: `qwen2.5:7b` (7.6B, Q4_K_M)
- 모델 digest: `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`
- 하드웨어: RAM 약 32GB, Intel UHD Graphics 630. Ollama API에서 VRAM 사용량 0으로 CPU 실행 확인.
- Python 3.11.9 / pytest 9.1.1. API 키와 클라우드 호출 없이 검증.

## 실행 명령과 결과

Ollama 설치 위치는 `C:\BLADE\.ollama`이며, 모델 다운로드 완료와 SHA256 검증 성공을 확인했습니다.
기본 로컬 API는 `http://127.0.0.1:11434`입니다.

```powershell
$env:BLADE_LLM_PROVIDER = 'ollama'
$env:BLADE_LLM_MODEL = 'qwen2.5:7b'
$env:PYTHONIOENCODING = 'utf-8'
.\.python\python.exe -m pytest tests/test_classifier.py -s
```

```text
37 passed in 177.54s (0:02:57)
```

실제 모델 테스트도 실행됐으며 skip이나 실패가 없습니다.
테스트 통과 후 별도로 다음 CLI를 실행했습니다.

```powershell
.\.python\python.exe -m pipeline.classifier.run demo_backend/openapi.json demo_backend/schema.sql --output verification/classifier-ollama-live.json
```

```text
Correct: 6/7
```

## 최종 CLI 결과

| 엔드포인트 | 기대 label | 실제 label | 신뢰도 | 일치 |
| --- | --- | --- | --- | --- |
| GET /public/health | public | public | 1.00 | O |
| GET /orders/{orderId} | owner_match | owner_match | 1.00 | O |
| DELETE /orders/{orderId} | owner_match | owner_match | 1.00 | O |
| GET /users/{userId} | owner_or_admin | manual_review_required | 0.00 | X |
| GET /admin/reports | role_required | role_required | 1.00 | O |
| GET /orgs/{orgId}/docs | tenant_match | tenant_match | 0.90 | O |
| GET /premium/content | membership_required | membership_required | 0.80 | O |

사용자 조회는 `Cannot identify ownership column in ERD` 사유로 탈출했습니다.
표의 신뢰도는 검증·탈출 처리를 적용한 최종 결과값이며, 0.00은 탈출 기본값입니다.
controller 코드는 전달하지 않았습니다. 이 결과는 위 데모 7개에 대한 검증 결과입니다.

전체 evidence와 조회 컬럼: [classifier-ollama-live.json](classifier-ollama-live.json)

## 적용한 변경

- Ollama `/api/chat` 어댑터를 구현했습니다. `stream=false`, `temperature=0`이며 API 키를 요구하지 않습니다.
- 기존 HTTPX I/O 타임아웃 60초와 최대 재시도 2회를 유지했습니다.
- 정확한 JSON Schema를 전달하며, 객체 label을 선택하면 object_param과 owner_lookup을 필수로 출력하도록 분기합니다.
- 요청된 결정 트리 원문을 유지하고 역할·소유권·등급 구분 설명과 일반 예시를 추가했습니다.
- path/query ID와 단일 PK의 이름이 대응하면 구조적 object_bindings를 입력에 포함합니다.
  이 정보는 파라미터·테이블·컬럼만 포함하며 정답 label은 포함하지 않습니다.
- Windows cp949에서 모델 evidence 출력이 실패하던 테스트 로그를 ASCII 이스케이프로 보완했습니다.
- `.env.example` 및 README의 현재 실행 설정을 Ollama 7B로 갱신했습니다.
- Fine-tuning, RAG는 추가하지 않았으며 기존 정책·JWT·탐지 로그 스키마는 변경하지 않았습니다.

## 보완 과정

초기 실제 평가는 1/7이었습니다. JSON Schema 및 결정 트리 보충 설명 적용 후 3/7,
구조적 객체 정보와 일반 예시 추가 후 5/7이었습니다.
이후 주문 조회의 원문에서 `owner_match`를 선택하고도 `owner_lookup: null`을 반환한 것을 확인했습니다.
객체 label의 조회 정보 필수 조건을 JSON Schema에 반영한 후 6/7에 도달했습니다.
진단 원문: [ollama-order-diagnostic.json](ollama-order-diagnostic.json)

이전 OpenAI 검증의 크레딧 부족 기록은 [기존 문서](2026-09-09-classifier.md)에 보존했습니다.
이미지 자료는 없습니다. 모델과 Ollama 설치는 재사용할 수 있도록 유지했습니다.

참고: [Ollama Chat API](https://docs.ollama.com/api/chat), [qwen2.5:7b](https://ollama.com/library/qwen2.5:7b)
