# 보충 입력 이후 모델 오판 추적

기존 분석에서 모델 오판으로 분류한 9건을 최신 API 응답으로 대조했다. 이 범주 역시 분석 가설이며 새 정답 판정이 아니다.

| id | 사람 라벨 | 기존 입력 응답 | 보충 입력 응답 | 최신 rationale | 이전 진단 |
|---|---|---|---|---|---|
| apisguru:amazonaws.com:get:/workspaces/{workspaceId}/alertmanager/definition | tenant_match | manual_review_required | manual_review_required | security_state: declared; description: Describes an alert manager definition. | /workspaces/{workspaceId}가 프롬프트 tenant 단서에 명시되지만 모델은 짧은 description만 인용해 보류했다. |
| apisguru:api2cart.com:get:/account.cart.list.json | owner_match | manual_review_required | manual_review_required | security_state: declared; description: Get list of carts; path: /account.cart.list.json | /account.cart.list.json이라는 개인 계정 단서를 단순 세그먼트가 아니라 점 구분 경로에서도 읽어야 한다. 모델은 설명만 보고 보류했다. |
| apisguru:appwrite.io:put:/teams/{teamId} | owner_match | role_required | role_required | description: Only team owners have write access for this resource; security_state: declared | Only team owners have write access라고 명시되는데 모델은 같은 문장을 인용해 role_required를 출력했다. |
| apisguru:billingo.hu:post:/documents/{id}/create-from-proforma | tenant_match | membership_required | membership_required | tenant_cols: organization; security_state: declared | tenant_cols=organization 및 organization.address 등 응답 필드를 인용하면서 membership을 출력했다. plan/tier 요구는 없다. |
| apisguru:openbanking.org.uk:get:/accounts/{AccountId}/product | owner_match | owner_match | membership_required | path: /accounts/{AccountId}/product; security: [{"PSUOAuth2Security": ["accounts"]}]; security_state: declared | /accounts/{AccountId}, PSUOAuth2Security scope accounts, 응답 AccountId가 있는데 전무/모순 설명 없이 confidence=0 보류. |
| apisguru:slmonitor.com:post:/api/v2.1/companies/{companyId}/users/{uniqueUserId}/checkin-audio | tenant_match | membership_required | membership_required | path: /api/v2.1/companies/{companyId}/users/{uniqueUserId}/checkin-audio; description: This operation checks the worker in for a default time or a custom time if the optional interval is provided; security_state: declared | companies/{companyId}, tenant_cols=company, 응답 company가 일치하는데 membership 선택. plan/tier 요구는 없다. |
| apisguru:trakt.tv:post:/users/{id}/lists/{list_id}/items/reorder | owner_match | role_required | role_required | security: [{"oauth2": []}]; description: OAuth Required; path: /users/{id}/lists/{list_id}/items/reorder | /users/{id}/lists와 OAuth Required만 있는데 role_required를 선택했다. 프롬프트는 OAuth와 역할 요구를 분리한다. |
| apisguru:velopayments.com:get:/v1/webhooks | tenant_match | public | membership_required | path: /v1/webhooks; description: List the details about the webhooks for the given payor; security_state: declared | description에 given payor, query payorId, 응답 payorId가 있으며 OAuth 선언도 있다. 모델은 GET·path만으로 public을 출력했다. |
| apisguru:illumidesk.com:get:/v1/teams/{team}/billing/invoices/{id}/ | tenant_match | owner_match | owner_match | path: /v1/teams/{team}/billing/invoices/{id}/; description: Get an invoice; security_state: declared | 경로 /teams/{team}/billing/invoices는 조직 단서인데 모델은 customer 컬럼만 근거로 개인 소유를 골랐다. |

보충 입력 응답 분포: {'manual_review_required': 2, 'role_required': 2, 'membership_required': 4, 'owner_match': 1}. 사람 라벨 일치 0/9.

## 다음 비교 실험에 필요한 조건

- OAuth/API key 요구를 role_required로 판정하는 오류: 인증과 역할 제한을 구분하는 명시 근거 검증이 필요하다.
- 회사·조직·payor 단서를 membership_required로 판정하는 오류: 모델이 인용한 근거가 선택한 라벨 정의를 실제로 지지하는지 확인해야 한다.
- 개인·조직 스코프 혼동 및 근거가 있어도 보류하는 사례: 필드 존재 검증만으로 잡을 수 없다.
- 자동 사후 라벨 교체는 하지 않는다. 정답 라벨을 모델 입력에 주는 수정도 하지 않는다.
- 먼저 label_decisions.md의 의미 충돌을 확정한 뒤, 고정 프롬프트·입력에서 다른 모델과 비교하거나 별도 승인된 프롬프트 실험을 설계한다. 현재 결과만으로 학습/전체 재라벨링을 재개하지 않는다.
