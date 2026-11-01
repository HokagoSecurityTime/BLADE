# 강제 선택 제거 실험

동일 보충 입력·gpt-4o-mini·temperature 0, 기존 31건. before는 직전 supplemented 실행을 재사용했다.

| 조건 | 일치 | 보류 | 구체 선택률 | 구체 선택 정확도 | evidence_invalid |
|---|---:|---:|---:|---:|---:|
| before | 3/31 (9.68%) | 9/31 | 70.97% | 13.64% (3/22) | 0 |
| after | 3/31 (9.68%) | 14/31 | 54.84% | 11.76% (2/17) | 0 |

이 표본은 v5 오류에서 선정됐고 분석에 사용됐다. 일반 성능 추정이나 독립 검증이 아니다. 보류 증가만으로 개선이라고 판단하지 않는다. 단일 실행 및 이전 대조군 재사용으로 출력 변동의 영향이 남는다.

| id | 사람 label | before | after | rationale |
|---|---|---|---|---|
| apisguru:deutschebahn.com:get:/providernetworks/{providernetworkUID}/rentalobjects/{rentalObjectUID} | public | manual_review_required | manual_review_required | path: /providernetworks/{providernetworkUID}/rentalobjects/{rentalObjectUID}; security_state: unknown |
| apisguru:illumidesk.com:get:/v1/teams/{team}/billing/invoices/{id}/ | tenant_match | owner_match | owner_match | path: /v1/teams/{team}/billing/invoices/{id}/; description: Get an invoice; owner_cols: customer |
| apisguru:zoom.us:get:/accounts/{accountId}/lock_settings | role_required | owner_or_admin | membership_required | path: /accounts/{accountId}/lock_settings; description: Account Locked Settings allow you turn settings on or off for all users in your account. No user except the account admin or account owner can change these settings; security_state: declared |
| apisguru:gerermesaffaires.com:patch:/spaces/{id} | manual_review_required | role_required | role_required | security: [{"gma_auth": ["collaborator", "owner", "robot"]}]; description: Modify a Space (except private); security_state: declared |
| apisguru:slack.com:get:/admin.conversations.getConversationPrefs | role_required | role_required | role_required | security: [{"slackAuth": ["admin.conversations:read"]}]; security_state: declared |
| apisguru:billingo.hu:post:/documents/{id}/create-from-proforma | tenant_match | membership_required | membership_required | path: /documents/{id}/create-from-proforma; description: Create a new document from proforma; tenant_cols: organization |
| apisguru:nebl.io:get:/ntp1/transactioninfo/{txid} | public | manual_review_required | manual_review_required | security_state: unknown; path: /ntp1/transactioninfo/{txid} |
| apisguru:trakt.tv:post:/users/{id}/lists/{list_id}/items/reorder | owner_match | role_required | role_required | method: POST; path: /users/{id}/lists/{list_id}/items/reorder; security_state: declared |
| apisguru:openbanking.org.uk:get:/accounts/{AccountId}/product | owner_match | membership_required | membership_required | path: /accounts/{AccountId}/product; security: [{"PSUOAuth2Security": ["accounts"]}]; security_state: declared |
| apisguru:microsoft.com:post:/{projectId}/classify/iterations/{publishedName}/image | manual_review_required | membership_required | membership_required | path: /{projectId}/classify/iterations/{publishedName}/image; security_state: declared; tenant_cols: project |
| apisguru:velopayments.com:get:/v1/webhooks | tenant_match | membership_required | manual_review_required | security: [{"OAuth2": []}]; security_state: declared; description: List the details about the webhooks for the given payor. |
| apisguru:bitbucket.org:put:/repositories/{workspace}/{repo_slug}/commit/{commit}/reports/{reportId}/annotations/{annotationId} | membership_required | manual_review_required | manual_review_required | path: /repositories/{workspace}/{repo_slug}/commit/{commit}/reports/{reportId}/annotations/{annotationId}; security_state: unknown |
| apisguru:slmonitor.com:post:/api/v2.1/companies/{companyId}/users/{uniqueUserId}/checkin-audio | tenant_match | membership_required | membership_required | path: /api/v2.1/companies/{companyId}/users/{uniqueUserId}/checkin-audio; tenant_cols: company; security_state: declared |
| apisguru:vtex.local:post:/api/catalog/pvt/collection/{collectionId}/position | role_required | role_required | role_required | security: [{"appKey": [], "appToken": []}]; security_state: declared |
| apisguru:amazonaws.com:get:/workspaces/{workspaceId}/alertmanager/definition | tenant_match | manual_review_required | manual_review_required | security_state: declared; description: Describes an alert manager definition. |
| apisguru:hetzner.cloud:get:/datacenters/{id} | public | manual_review_required | manual_review_required | security_state: unknown; path: /datacenters/{id}; description: Returns a specific Datacenter object. |
| apisguru:netboxdemo.com:put:/circuits/circuit-terminations/{id}/ | role_required | manual_review_required | manual_review_required | security_state: declared; tenant_cols: site |
| apisguru:api2cart.com:get:/account.cart.list.json | owner_match | manual_review_required | manual_review_required | security_state: declared; description: Get list of carts; security: [{"api_key": []}] |
| apisguru:microsoft.com:post:/{projectId}/classify/iterations/{publishedName}/url | manual_review_required | membership_required | manual_review_required | security_state: declared; tenant_cols: project; description: Supplemental source OAS context indicates service information. |
| apisguru:twinehealth.com:get:/oauth/token/{id}/groups | manual_review_required | membership_required | membership_required | security: [{"OAuth2": ["group", "organization"]}]; security_state: declared |
| apisguru:rebilly.com:get:/credentials/{id} | tenant_match | role_required | owner_match | owner_cols: customerId; path: /credentials/{id}; security_state: declared |
| apisguru:appcenter.ms:patch:/v0.1/apps/{owner_name}/{app_name}/builds/{build_id} | membership_required | role_required | manual_review_required | security_state: declared; description: Cancels a build; path: /v0.1/apps/{owner_name}/{app_name}/builds/{build_id} |
| apisguru:visma.net:get:/api/v3/SalesOrders/{type}/{orderId}/discounts | tenant_match | manual_review_required | manual_review_required | security_state: declared; security: [{"oauth2": ["read"]}] |
| apisguru:appwrite.io:put:/teams/{teamId} | owner_match | role_required | role_required | description: Only team owners have write access for this resource; security: [{"JWT": [], "Project": []}]; security_state: declared |
| apisguru:circuitsandbox.net:put:/conversations/community/{convId} | membership_required | role_required | role_required | path: /conversations/community/{convId}; description: Updates the information of the given community; security: [{"oauth": ["ALL", "WRITE_CONVERSATIONS", "MANAGE_CONVERSATIONS"]}]; owner_cols: [creatorId] |
| apisguru:clicksend.com:post:/lists/{list_id}/contacts | owner_match | membership_required | membership_required | path: /lists/{list_id}/contacts; description: at least one of them must be specified; tenant_cols: organization_name |
| apisguru:configcat.com:post:/v1/environments/{environmentId}/settings/{settingId}/integrationLinks/{integrationLinkType}/{key} | tenant_match | role_required | manual_review_required | security_state: declared; description: Supplemental source OAS context; path: /v1/environments/{environmentId}/settings/{settingId}/integrationLinks/{integrationLinkType}/{key} |
| apisguru:shutterstock.com:patch:/v2/catalog/collections/{collection_id} | owner_match | role_required | role_required | security: [{"customer_accessCode": ["collections.view", "collections.edit"]}]; security_state: declared |
| apisguru:aiception.com:get:/face/{taskId} | owner_match | owner_match | manual_review_required | security_state: declared; path: /face/{taskId}; description: Gets the face task. |
| apisguru:appwrite.io:put:/storage/files/{fileId} | owner_match | role_required | role_required | description: Only users with write permissions have access to update this resource; security: [{"JWT": [], "Project": []}]; security_state: declared |
| apisguru:parliament.uk:get:/api/v1/Bills/{billId}/NewsArticles | public | manual_review_required | manual_review_required | security_state: unknown; path: /api/v1/Bills/{billId}/NewsArticles; description: Returns a list of news articles for a Bill. |
