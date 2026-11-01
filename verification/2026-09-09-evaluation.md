# 신규 합성 사례 평가·장애 검증·프록시 지연 측정

## 결과

| 항목 | 결과 |
| --- | --- |
| 신규 사례 label 정확도 | 13/14, 92.9% |
| label과 정책 필드 모두 일치 | 13/14, 92.9% |
| 수동 검토 비율 | 2/14, 14.3% |
| 자동 분류된 사례의 정확도 | 11/12, 91.7% |
| 최종 제공자 호출 실패 | 0건 |
| 전체 테스트 | 87 passed, 1 skipped, 2 warnings in 3.71s |

실제 모델은 Ollama qwen2.5:7b입니다. label별 2건씩 직접 작성한 합성 사례에 controller 텍스트를
포함했습니다. 기존 프롬프트를 수정하지 않고 사례별로 한 번씩 순차 평가했습니다.
데이터셋과 분류 소스의 SHA256이 실행 전후 동일함을 확인했습니다.
이는 독립적인 실서비스 데이터셋 평가가 아니며, controller 없는 기존 데모 6/7과 직접 비교할 수 없습니다.

## 사례별 결과

| 사례 | 기대 | 실제 | label/필드 일치 |
| --- | --- | --- | --- |
| public-version | public | public | O |
| public-catalog | public | public | O |
| role-audit | role_required | role_required | O |
| role-moderation | role_required | role_required | O |
| membership-gold | membership_required | membership_required | O |
| membership-enterprise | membership_required | membership_required | O |
| owner-booking | owner_match | owner_match | O |
| owner-query-fk | owner_match | owner_match | O |
| tenant-project | tenant_match | tenant_match | O |
| tenant-query-fk | tenant_match | tenant_match | O |
| owner-admin-draft | owner_or_admin | owner_or_admin | O |
| owner-admin-query | owner_or_admin | owner_match | X |
| review-unknown-owner | manual_review_required | manual_review_required | O |
| review-conflicting-fk | manual_review_required | manual_review_required | O |

오답은 `/tickets?ticket_key=...`의 비표준 사용자 FK와 명시적 admin 우회를 함께 처리하는 사례입니다.
개인 소유권은 선택했지만 관리자 우회를 누락했습니다. 이 정책을 그대로 승인하면 정당한 관리자 접근을
차단할 수 있습니다. 실제 공격 요청의 오탐·미탐률을 측정한 것은 아닙니다.
결과를 본 뒤 이 데이터셋에 맞춰 프롬프트를 조정하거나 실패 사례만 재실행하지 않았습니다.

분류 시간은 평균 25.90초, p50 22.82초, p95 81.86초였습니다.
14건의 최근접 순위 p95는 최댓값이며 첫 요청 81.86초의 영향을 받습니다.
시간에는 로딩·HTTP 재시도가 포함될 수 있으나 내부 성공 재시도 횟수는 계측하지 않았습니다.
60초는 개별 I/O 타임아웃이므로 전체 classify 시간과 다릅니다.

자료: [데이터셋](classifier-holdout-v1.json), [사전 절차](classifier-holdout-v1-protocol.md),
[전체 결과·혼동행렬·해시](classifier-holdout-v1-run1.json).

## 프록시 지연

LLM 평가 종료 후 별도로 실행했습니다. 실제 uvicorn/aiohttp/SQLite를 같은 Python 프로세스에서
loopback HTTP로 연결하고 5쌍 워밍업 후 직접/프록시 각 50회 순차 측정했습니다.
측정 순서는 쌍마다 교대로 바꿨으며 동시성은 1입니다.

| 경로 | 평균 ms | p50 ms | p95 ms |
| --- | ---: | ---: | ---: |
| 직접 호출 | 2.415 | 2.128 | 3.125 |
| 프록시 | 4.661 | 4.257 | 5.971 |

평균 차이는 **2.246ms**입니다. JWT 검증·매 요청 읽기 전용 DB 조회·로그 큐 삽입을 포함합니다.
비동기 로그 영구 저장 완료 시간은 응답 시간에 포함하지 않습니다.
단일 로컬 실행 결과이며 부하 처리량·운영 SLA·통계적 신뢰구간을 의미하지 않습니다.

```powershell
python -m tests.benchmark_proxy --output verification/proxy-latency-run1.json --samples 50
```

자료: [측정 원본](proxy-latency-run1.json).

## 장애 검증

`tests/test_proxy_failures.py`: **4 passed in 1.18s**.

- 관리 정책 API 503 → TTL 만료 후 open은 전달, closed는 503.
- 정책 API 복구 → 다시 정상 정책을 적용해 비인가 사용자는 403.
- 읽기 전용 DB 누락 → open/closed 설정에 따른 동작, 빈 DB를 생성하지 않음.
- 로그 API가 503이어도 요청 처리는 계속됨. 기존 설계상 실패 로그의 영구 재전송은 보장하지 않음.
- JWT 누락은 fail-open에서도 401.

## 전체 회귀

```powershell
$env:BLADE_LLM_PROVIDER=''
python -m pytest tests
```

87개 통과, 실제 LLM 데모 테스트 1개 skip. 실제 신규 데이터셋 평가는 위 별도 실행으로 완료했습니다.
경고 2건은 기존 Starlette/httpx 및 anyio deprecated 경고입니다.
기존 실험 DB·정책은 변경하지 않았고 프롬프트도 고정했습니다. 이미지 자료는 없습니다.
