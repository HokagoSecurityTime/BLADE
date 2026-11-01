# 제출 설계 정렬: 그룹 구성원 라벨 실험

최종 라벨은 OpenAI gpt-4o-mini가 선택했다. 조건 코드는 입력 근거이며 정답·검사 결과는 모델에 제공하지 않았다. 모델 출력을 규칙으로 덮어쓰지 않았다.

| 사례 | 새 기준 계약 | v2.8 | v2.9 |
|---|---|---|---|
| group_access | membership_required | manual_review_required | membership_required |
| tenant_access | tenant_match | tenant_match | tenant_match |
| role_access | role_required | role_required | role_required |
| owner_access | owner_match | owner_match | owner_match |
| owner_admin_access | owner_or_admin | owner_or_admin | owner_or_admin |
| public_access | public | public | public |
| group_tenant_access | manual_review_required | tenant_match | membership_required |
| subscription_access | manual_review_required | membership_required | manual_review_required |

{"2.8": {"agreement": 5, "n": 8, "errors": 0, "evidence_invalid": 0}, "2.9": {"agreement": 7, "n": 8, "errors": 0, "evidence_invalid": 0}}

## 의미와 한계

v2.9의 membership_required는 특정 요청 대상 그룹에 요청자가 속하는 관계다. 같은 tenant, 구독 등급, 객체 소유와 별개다. 구독만 요구하는 사례는 새 6종 중 표현할 라벨이 없어 보류한다. 그룹과 tenant가 동시에 필수인 경우도 단일 라벨로 조건을 버리지 않고 보류한다. v2.8은 다른 정의를 사용하므로 새 기준 일치도이며 기존 기준 정확도 하락을 뜻하지 않는다.

합성 경계 사례 8건, 접근 함수 40건 및 익명 public 1건 검증이다. 함수 단위 검사이며 실제 서버 인증·DB 통합 검증이 아니다. 각 라벨의 표본이 매우 작고 같은 제작자가 계약과 코드를 만들었으므로 일반 성능을 주장하지 않는다.

## 런타임 호환성: 자동 적용 금지

현재 proxy/evaluator.py는 claims.membership이 policy.params.allowed_membership 목록에 있는지 비교한다. 이는 요청 대상 group_id와 요청자 사이의 구성원 관계 조회가 아니다. 새 의미의 membership 예측을 현재 런타임 정책으로 자동 배포하면 안 된다. 이번 변경은 실험 프롬프트와 보고서에 한정되며 runtime·정책 스키마·고정 test·기존 학습 라벨은 보존한다. runtime 변경에는 별도 설계가 필요하다.
