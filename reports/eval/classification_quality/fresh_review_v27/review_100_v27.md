# v2.7 사람 검수표 100건

기준: training/data/LABEL_STANDARD_V2.7.md. 아래 입력 근거만 보고 확정 라벨과 사유를 작성한다. 정보가 부족하면 manual_review_required를 사용할 수 있다.

기존 모델 라벨은 숨겼다. signal_class 균형·service 최대 3건·seed 42 표본이며 모집단 분포를 대표하는 무작위 표본은 아니다.

미사용은 저장된 검수·pilot·분석·예시 파일의 ID와 겹치지 않음을 뜻한다. APIs.guru 전량이 이전 자동 라벨링을 거쳤으므로 모델 호출 이력이 없는 데이터라는 뜻은 아니다.

| 번호 | id | service | method | path | 확정 label | 검수 사유 |
|---:|---|---|---|---|---|---|
| 1 | apisguru:ably.net:get:/apps/{app_id}/rules | ably.net | GET | /apps/{app_id}/rules | | |
| 2 | apisguru:adafruit.com:put:/{username}/dashboards/{dashboard_id}/blocks/{id} | adafruit.com | PUT | /{username}/dashboards/{dashboard_id}/blocks/{id} | | |
| 3 | apisguru:amazonaws.com:post:/workspaces/{workspaceId}/rulegroupsnamespaces | amazonaws.com | POST | /workspaces/{workspaceId}/rulegroupsnamespaces | | |
| 4 | apisguru:amazonaws.com:put:/workspaces/{workspaceId}/rulegroupsnamespaces/{name} | amazonaws.com | PUT | /workspaces/{workspaceId}/rulegroupsnamespaces/{name} | | |
| 5 | apisguru:apacta.com:get:/cities/{city_id} | apacta.com | GET | /cities/{city_id} | | |
| 6 | apisguru:apacta.com:get:/clocking_records/{clocking_record_id} | apacta.com | GET | /clocking_records/{clocking_record_id} | | |
| 7 | apisguru:api.video:get:/live-streams/{liveStreamId} | api.video | GET | /live-streams/{liveStreamId} | | |
| 8 | apisguru:apigee.net:get:/dealer/rv/{id} | apigee.net | GET | /dealer/rv/{id} | | |
| 9 | apisguru:appcenter.ms:patch:/v0.1/apps/{owner_name}/{app_name}/crash_groups/{crash_group_id} | appcenter.ms | PATCH | /v0.1/apps/{owner_name}/{app_name}/crash_groups/{crash_group_id} | | |
| 10 | apisguru:appveyor.com:get:/deployments/{deploymentId} | appveyor.com | GET | /deployments/{deploymentId} | | |
| 11 | apisguru:appwrite.io:get:/teams/{teamId} | appwrite.io | GET | /teams/{teamId} | | |
| 12 | apisguru:authentiq.io:put:/client/{client_id} | authentiq.io | PUT | /client/{client_id} | | |
| 13 | apisguru:bbc.com:get:/master_brands | bbc.com | GET | /master_brands | | |
| 14 | apisguru:bbc.com:get:/programmes | bbc.com | GET | /programmes | | |
| 15 | apisguru:bbc.com:get:/promotions | bbc.com | GET | /promotions | | |
| 16 | apisguru:beezup.com:get:/orders/v3/{marketplaceTechnicalCode}/{accountId}/{beezUPOrderId} | beezup.com | GET | /orders/v3/{marketplaceTechnicalCode}/{accountId}/{beezUPOrderId} | | |
| 17 | apisguru:bigredcloud.com:get:/v1/bankAccounts/{id} | bigredcloud.com | GET | /v1/bankAccounts/{id} | | |
| 18 | apisguru:bigredcloud.com:put:/v1/customers/{id} | bigredcloud.com | PUT | /v1/customers/{id} | | |
| 19 | apisguru:box.com:get:/collections/{collection_id}/items | box.com | GET | /collections/{collection_id}/items | | |
| 20 | apisguru:browshot.com:get:/browser/info | browshot.com | GET | /browser/info | | |
| 21 | apisguru:chaingateway.io:get:/v2/ethereum/nfts/{contract}/uri/{token_id} | chaingateway.io | GET | /v2/ethereum/nfts/{contract}/uri/{token_id} | | |
| 22 | apisguru:clever-cloud.com:post:/organisations/{id}/addonproviders/{providerId}/features | clever-cloud.com | POST | /organisations/{id}/addonproviders/{providerId}/features | | |
| 23 | apisguru:clicksend.com:put:/lists/{list_id}/contacts/{contact_id} | clicksend.com | PUT | /lists/{list_id}/contacts/{contact_id} | | |
| 24 | apisguru:configcat.com:get:/v1/configs/{configId}/settings | configcat.com | GET | /v1/configs/{configId}/settings | | |
| 25 | apisguru:contribly.com:get:/users/{id} | contribly.com | GET | /users/{id} | | |
| 26 | apisguru:cpy.re:get:/api/v1/users/{id} | cpy.re | GET | /api/v1/users/{id} | | |
| 27 | apisguru:deutschebahn.com:get:/providernetworks/{uid} | deutschebahn.com | GET | /providernetworks/{uid} | | |
| 28 | apisguru:discourse.local:get:/admin/users/{id}.json | discourse.local | GET | /admin/users/{id}.json | | |
| 29 | apisguru:dracoon.team:get:/v4/nodes/files/uploads/{upload_id} | dracoon.team | GET | /v4/nodes/files/uploads/{upload_id} | | |
| 30 | apisguru:evetech.net:get:/characters/{character_id}/calendar/{event_id}/ | evetech.net | GET | /characters/{character_id}/calendar/{event_id}/ | | |
| 31 | apisguru:files.com:get:/api_keys | files.com | GET | /api_keys | | |
| 32 | apisguru:files.com:get:/automation_runs | files.com | GET | /automation_runs | | |
| 33 | apisguru:flat.io:post:/scores/{score}/fork | flat.io | POST | /scores/{score}/fork | | |
| 34 | apisguru:gitea.io:get:/repos/{owner}/{repo}/hooks/{id} | gitea.io | GET | /repos/{owner}/{repo}/hooks/{id} | | |
| 35 | apisguru:gitea.io:patch:/orgs/{org}/hooks/{id} | gitea.io | PATCH | /orgs/{org}/hooks/{id} | | |
| 36 | apisguru:googleapis.com:put:/billinginfo/{accountId}/{billingId} | googleapis.com | PUT | /billinginfo/{accountId}/{billingId} | | |
| 37 | apisguru:gsmtasks.com:patch:/accounts/{id}/ | gsmtasks.com | PATCH | /accounts/{id}/ | | |
| 38 | apisguru:gsmtasks.com:post:/accounts/{id}/managers/ | gsmtasks.com | POST | /accounts/{id}/managers/ | | |
| 39 | apisguru:hetras-certification.net:get:/api/booking/v0/bookings/{confirmationId}/reservations/{reservationNumber} | hetras-certification.net | GET | /api/booking/v0/bookings/{confirmationId}/reservations/{reservationNumber} | | |
| 40 | apisguru:i-cue.solutions:get:/report/performance/sku-rationalization/{planningLevelId} | i-cue.solutions | GET | /report/performance/sku-rationalization/{planningLevelId} | | |
| 41 | apisguru:increase.com:get:/account_transfers/{account_transfer_id} | increase.com | GET | /account_transfers/{account_transfer_id} | | |
| 42 | apisguru:increase.com:patch:/account_numbers/{account_number_id} | increase.com | PATCH | /account_numbers/{account_number_id} | | |
| 43 | apisguru:influxdata.com:patch:/authorizations/{authID} | influxdata.com | PATCH | /authorizations/{authID} | | |
| 44 | apisguru:izettle.com:get:/organizations/{organizationUuid}/categories/v2 | izettle.com | GET | /organizations/{organizationUuid}/categories/v2 | | |
| 45 | apisguru:izettle.com:put:/organizations/{organizationUuid}/discounts/{discountUuid} | izettle.com | PUT | /organizations/{organizationUuid}/discounts/{discountUuid} | | |
| 46 | apisguru:keycloak.local:put:/{realm}/authentication/flows/{id} | keycloak.local | PUT | /{realm}/authentication/flows/{id} | | |
| 47 | apisguru:letmc.com:get:/v2/tier2/{shortName}/branch/branches/{branchID} | letmc.com | GET | /v2/tier2/{shortName}/branch/branches/{branchID} | | |
| 48 | apisguru:lyft.com:get:/rides/{id}/receipt | lyft.com | GET | /rides/{id}/receipt | | |
| 49 | apisguru:medium.com:get:/user/{user_id}/articles | medium.com | GET | /user/{user_id}/articles | | |
| 50 | apisguru:meshery.local:get:/api/application/{id} | meshery.local | GET | /api/application/{id} | | |
| 51 | apisguru:meteosource.com:get:/nearest_place | meteosource.com | GET | /nearest_place | | |
| 52 | apisguru:microsoft.com:post:/{projectId}/url | microsoft.com | POST | /{projectId}/url | | |
| 53 | apisguru:n-auth.com:get:/servers/{serverid}/users/{userid}/accounts | n-auth.com | GET | /servers/{serverid}/users/{userid}/accounts | | |
| 54 | apisguru:naviplancentral.com:post:/api/Accounts/{accountId}/Holdings | naviplancentral.com | POST | /api/Accounts/{accountId}/Holdings | | |
| 55 | apisguru:netbox.dev:get:/circuits/provider-networks/{id}/ | netbox.dev | GET | /circuits/provider-networks/{id}/ | | |
| 56 | apisguru:netboxdemo.com:put:/circuits/providers/{id}/ | netboxdemo.com | PUT | /circuits/providers/{id}/ | | |
| 57 | apisguru:nordigen.com:get:/api/v2/institutions/{id}/ | nordigen.com | GET | /api/v2/institutions/{id}/ | | |
| 58 | apisguru:nordigen.com:post:/api/v2/payments/{id}/submit/ | nordigen.com | POST | /api/v2/payments/{id}/submit/ | | |
| 59 | apisguru:onsched.com:get:/consumer/v1/appointments/{id} | onsched.com | GET | /consumer/v1/appointments/{id} | | |
| 60 | apisguru:onsched.com:put:/consumer/v1/appointments/{id}/cancel | onsched.com | PUT | /consumer/v1/appointments/{id}/cancel | | |
| 61 | apisguru:openchannel.io:patch:/apps/{appId}/versions/{version} | openchannel.io | PATCH | /apps/{appId}/versions/{version} | | |
| 62 | apisguru:openfintech.io:get:/exchangers/{id} | openfintech.io | GET | /exchangers/{id} | | |
| 63 | apisguru:orbit.love:put:/{workspace_slug}/members/{member_slug}/activities/{id} | orbit.love | PUT | /{workspace_slug}/members/{member_slug}/activities/{id} | | |
| 64 | apisguru:osf.io:get:/files/{file_id}/ | osf.io | GET | /files/{file_id}/ | | |
| 65 | apisguru:osf.io:get:/institutions/{institution_id}/users/ | osf.io | GET | /institutions/{institution_id}/users/ | | |
| 66 | apisguru:osf.io:post:/draft_registrations/{draft_id}/contributors/ | osf.io | POST | /draft_registrations/{draft_id}/contributors/ | | |
| 67 | apisguru:patientview.org:get:/user/{userId}/availableobservationheadings | patientview.org | GET | /user/{userId}/availableobservationheadings | | |
| 68 | apisguru:payrun.io:put:/Employer/{EmployerId}/CisLineType/{CisLineTypeId}/Tag/{TagId} | payrun.io | PUT | /Employer/{EmployerId}/CisLineType/{CisLineTypeId}/Tag/{TagId} | | |
| 69 | apisguru:pocketsmith.com:get:/accounts/{id} | pocketsmith.com | GET | /accounts/{id} | | |
| 70 | apisguru:probely.com:get:/events/{id}/ | probely.com | GET | /events/{id}/ | | |
| 71 | apisguru:probely.com:get:/integrations/jira-cloud/projects/{project_id}/issue_types/{issue_type_id}/status/ | probely.com | GET | /integrations/jira-cloud/projects/{project_id}/issue_types/{issue_type_id}/status/ | | |
| 72 | apisguru:probely.com:patch:/targets/{id}/ | probely.com | PATCH | /targets/{id}/ | | |
| 73 | apisguru:prss.org:get:/api/v2/episodes | prss.org | GET | /api/v2/episodes | | |
| 74 | apisguru:rebilly.com:get:/attachments/{id} | rebilly.com | GET | /attachments/{id} | | |
| 75 | apisguru:rebilly.com:get:/bank-accounts/{id} | rebilly.com | GET | /bank-accounts/{id} | | |
| 76 | apisguru:reverb.com:post:/my/orders/selling/{id}/ship | reverb.com | POST | /my/orders/selling/{id}/ship | | |
| 77 | apisguru:runscope.com:get:/teams/{teamId}/integrations | runscope.com | GET | /teams/{teamId}/integrations | | |
| 78 | apisguru:signl4.com:get:/alerts/{alertId}/annotations | signl4.com | GET | /alerts/{alertId}/annotations | | |
| 79 | apisguru:simplyrets.com:get:/properties/{mlsId} | simplyrets.com | GET | /properties/{mlsId} | | |
| 80 | apisguru:slmonitor.com:put:/api/v2.1/companies/{companyId}/users/{uniqueUserId}/itinerary-file | slmonitor.com | PUT | /api/v2.1/companies/{companyId}/users/{uniqueUserId}/itinerary-file | | |
| 81 | apisguru:soundcloud.com:get:/playlists/{playlist_id} | soundcloud.com | GET | /playlists/{playlist_id} | | |
| 82 | apisguru:spoonacular.com:get:/mealplanner/{username}/templates/{id} | spoonacular.com | GET | /mealplanner/{username}/templates/{id} | | |
| 83 | apisguru:stackexchange.com:get:/users/{id}/inbox | stackexchange.com | GET | /users/{id}/inbox | | |
| 84 | apisguru:storecove.com:patch:/legal_entities/{id} | storecove.com | PATCH | /legal_entities/{id} | | |
| 85 | apisguru:stripe.com:get:/v1/accounts/{account}/bank_accounts/{id} | stripe.com | GET | /v1/accounts/{account}/bank_accounts/{id} | | |
| 86 | apisguru:telnyx.com:get:/authentication_providers/{id} | telnyx.com | GET | /authentication_providers/{id} | | |
| 87 | apisguru:telnyx.com:patch:/billing_groups/{id} | telnyx.com | PATCH | /billing_groups/{id} | | |
| 88 | apisguru:tokenjay.app:get:/cancelbabel/{boxId} | tokenjay.app | GET | /cancelbabel/{boxId} | | |
| 89 | apisguru:twilio.com:get:/2010-04-01/Accounts/{AccountSid}/AuthorizedConnectApps.json | twilio.com | GET | /2010-04-01/Accounts/{AccountSid}/AuthorizedConnectApps.json | | |
| 90 | apisguru:vestorly.com:get:/advisors/{id} | vestorly.com | GET | /advisors/{id} | | |
| 91 | apisguru:visma.com:delete:/v1/activities/{guid} | visma.com | DELETE | /v1/activities/{guid} | | |
| 92 | apisguru:visma.com:get:/v1/activities/{guid} | visma.com | GET | /v1/activities/{guid} | | |
| 93 | apisguru:watchful.li:get:/sites/{id}/extensions | watchful.li | GET | /sites/{id}/extensions | | |
| 94 | apisguru:watchful.li:post:/sites/{id}/backupstart | watchful.li | POST | /sites/{id}/backupstart | | |
| 95 | apisguru:webflow.com:get:/deploymentEnvironments/{deploymentEnvironmentId} | webflow.com | GET | /deploymentEnvironments/{deploymentEnvironmentId} | | |
| 96 | apisguru:xero.com:get:/Connections | xero.com | GET | /Connections | | |
| 97 | apisguru:yodlee.com:get:/providers | yodlee.com | GET | /providers | | |
| 98 | apisguru:yodlee.com:get:/providers/{providerId} | yodlee.com | GET | /providers/{providerId} | | |
| 99 | apisguru:zuora.com:get:/notifications/notification-definitions/{id} | zuora.com | GET | /notifications/notification-definitions/{id} | | |
| 100 | apisguru:zuora.com:get:/objects/records/default/{object}/{id} | zuora.com | GET | /objects/records/default/{object}/{id} | | |

## 1. apisguru:ably.net:get:/apps/{app_id}/rules

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/apps/{app_id}/rules",
  "path_params": [
    "app_id"
  ],
  "query_params": [],
  "summary": "Lists Reactor rules",
  "description": "Lists the rules for the application specified by the application ID.",
  "security": [
    {
      "bearer_auth": []
    }
  ],
  "schema_fields": [
    "[]._links",
    "[].appId",
    "[].created",
    "[].id",
    "[].modified",
    "[].requestMode",
    "[].ruleType",
    "[].source",
    "[].source.channelFilter",
    "[].source.type",
    "[].status",
    "[].target",
    "[].target.enveloped",
    "[].target.format",
    "[].target.headers",
    "[].target.headers.[].name",
    "[].target.headers.[].value",
    "[].target.signingKeyId",
    "[].target.url",
    "[].version",
    "[].target.eventName",
    "[].target.webhookKey",
    "[].target.azureAppId",
    "[].target.azureFunctionName",
    "[].target.functionName",
    "[].target.projectId",
    "[].target.region",
    "[].target.authentication",
    "[].target.authentication.accessKeyId",
    "[].target.authentication.authenticationMode",
    "[].target.authentication.assumeRoleArn",
    "[].target.partitionKey",
    "[].target.streamName",
    "[].target.awsAccountId",
    "[].target.queueName",
    "[].target.queueId",
    "[].target.mandatoryRoute",
    "[].target.messageTtl",
    "[].target.persistentMessages",
    "[].target.routingKey"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "projectId"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "bearer_auth": []
      }
    ],
    "schemes": {
      "bearer_auth": {
        "description": "Control API uses bearer authentication. You need to generate an access token for use with this API. More details can be found in the <a href=\"https://ably.com/documentation/control-api/#authentication\">Ably documentation</a>.",
        "scheme": "bearer",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 2. apisguru:adafruit.com:put:/{username}/dashboards/{dashboard_id}/blocks/{id}

입력 근거 전문:

```json
{
  "method": "PUT",
  "path": "/{username}/dashboards/{dashboard_id}/blocks/{id}",
  "path_params": [
    "username",
    "dashboard_id",
    "id"
  ],
  "query_params": [],
  "summary": "Replace an existing Block",
  "description": "",
  "security": [
    {
      "HeaderKey": []
    },
    {
      "HeaderSignature": []
    },
    {
      "QueryKey": []
    }
  ],
  "schema_fields": [
    "block_feeds",
    "block_feeds.[].feed",
    "block_feeds.[].feed.created_at",
    "block_feeds.[].feed.description",
    "block_feeds.[].feed.details",
    "block_feeds.[].feed.details.data",
    "block_feeds.[].feed.details.data.count",
    "block_feeds.[].feed.details.data.first",
    "block_feeds.[].feed.details.data.last",
    "block_feeds.[].feed.details.shared_with",
    "block_feeds.[].feed.enabled",
    "block_feeds.[].feed.group",
    "block_feeds.[].feed.groups",
    "block_feeds.[].feed.groups.[].created_at",
    "block_feeds.[].feed.groups.[].description",
    "block_feeds.[].feed.groups.[].id",
    "block_feeds.[].feed.groups.[].name",
    "block_feeds.[].feed.groups.[].updated_at",
    "block_feeds.[].feed.history",
    "block_feeds.[].feed.id",
    "block_feeds.[].feed.key",
    "block_feeds.[].feed.last_value",
    "block_feeds.[].feed.license",
    "block_feeds.[].feed.name",
    "block_feeds.[].feed.status",
    "block_feeds.[].feed.status_notify",
    "block_feeds.[].feed.status_timeout",
    "block_feeds.[].feed.unit_symbol",
    "block_feeds.[].feed.unit_type",
    "block_feeds.[].feed.updated_at",
    "block_feeds.[].feed.visibility",
    "block_feeds.[].group",
    "block_feeds.[].group.created_at",
    "block_feeds.[].group.description",
    "block_feeds.[].group.feeds",
    "block_feeds.[].group.feeds.[].created_at",
    "block_feeds.[].group.feeds.[].description",
    "block_feeds.[].group.feeds.[].details",
    "block_feeds.[].group.feeds.[].details.data",
    "block_feeds.[].group.feeds.[].details.data.count"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "HeaderKey": []
      },
      {
        "HeaderSignature": []
      },
      {
        "QueryKey": []
      }
    ],
    "schemes": {
      "HeaderKey": {
        "description": "The AIO Key is used to restrict or grant access to your data. The key is unique, and you can generate a key per feed, and control it in many different ways. The easiest process is to just use your automatically generated master key. You can access this key right from the right-hand side of your dashboard or from an individual feed page.",
        "in": "header",
        "name": "X-AIO-Key",
        "type": "apiKey"
      },
      "HeaderSignature": {
        "description": "The AIO Signature is an AWS inspired request signature.",
        "in": "header",
        "name": "X-AIO-Signature",
        "type": "apiKey"
      },
      "QueryKey": {
        "description": "The AIO Key is used to restrict or grant access to your data. The key is unique, and you can generate a key per feed, and control it in many different ways. The easiest process is to just use your automatically generated master key. You can access this key right from the right-hand side of your dashboard or from an individual feed page.",
        "in": "query",
        "name": "X-AIO-Key",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 3. apisguru:amazonaws.com:post:/workspaces/{workspaceId}/rulegroupsnamespaces

입력 근거 전문:

```json
{
  "method": "POST",
  "path": "/workspaces/{workspaceId}/rulegroupsnamespaces",
  "path_params": [
    "workspaceId"
  ],
  "query_params": [],
  "summary": "",
  "description": "Create a rule group namespace.",
  "security": [
    {
      "hmac": []
    }
  ],
  "schema_fields": [
    "name",
    "arn",
    "status",
    "status.statusCode",
    "status.statusReason",
    "tags"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "hmac": []
      }
    ],
    "schemes": {
      "hmac": {
        "type": "apiKey",
        "name": "Authorization",
        "in": "header",
        "description": "Amazon Signature authorization v4",
        "x-amazon-apigateway-authtype": "awsSigv4"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 4. apisguru:amazonaws.com:put:/workspaces/{workspaceId}/rulegroupsnamespaces/{name}

입력 근거 전문:

```json
{
  "method": "PUT",
  "path": "/workspaces/{workspaceId}/rulegroupsnamespaces/{name}",
  "path_params": [
    "workspaceId",
    "name"
  ],
  "query_params": [],
  "summary": "",
  "description": "Update a rule groups namespace.",
  "security": [
    {
      "hmac": []
    }
  ],
  "schema_fields": [
    "name",
    "arn",
    "status",
    "status.statusCode",
    "status.statusReason",
    "tags"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "hmac": []
      }
    ],
    "schemes": {
      "hmac": {
        "type": "apiKey",
        "name": "Authorization",
        "in": "header",
        "description": "Amazon Signature authorization v4",
        "x-amazon-apigateway-authtype": "awsSigv4"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 5. apisguru:apacta.com:get:/cities/{city_id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/cities/{city_id}",
  "path_params": [
    "city_id"
  ],
  "query_params": [],
  "summary": "Get details about one city",
  "description": "",
  "security": [
    {
      "X-Auth-Token": []
    },
    {
      "api_key": []
    }
  ],
  "schema_fields": [
    "data",
    "data.created",
    "data.deleted",
    "data.id",
    "data.modified",
    "data.name",
    "data.zip_code",
    "success"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "X-Auth-Token": []
      },
      {
        "api_key": []
      }
    ],
    "schemes": {
      "X-Auth-Token": {
        "in": "header",
        "name": "X-Auth-Token",
        "type": "apiKey"
      },
      "api_key": {
        "description": "Uses the user's API token found from within the control panel in \"settings\" -> \"additional settings\"",
        "in": "query",
        "name": "api_token",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 6. apisguru:apacta.com:get:/clocking_records/{clocking_record_id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/clocking_records/{clocking_record_id}",
  "path_params": [
    "clocking_record_id"
  ],
  "query_params": [],
  "summary": "Details of 1 clocking_record",
  "description": "",
  "security": [
    {
      "X-Auth-Token": []
    },
    {
      "api_key": []
    }
  ],
  "schema_fields": [
    "data",
    "data.checked_in",
    "data.checked_out",
    "data.checkin_latitude",
    "data.checkin_longitude",
    "data.checkout_latitude",
    "data.checkout_longitude",
    "data.created",
    "data.created_by_id",
    "data.deleted",
    "data.id",
    "data.modified",
    "data.modified_by_id",
    "data.project_id",
    "data.user_id",
    "success"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "created_by_id",
    "user_id"
  ],
  "tenant_cols": [
    "project_id"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "X-Auth-Token": []
      },
      {
        "api_key": []
      }
    ],
    "schemes": {
      "X-Auth-Token": {
        "in": "header",
        "name": "X-Auth-Token",
        "type": "apiKey"
      },
      "api_key": {
        "description": "Uses the user's API token found from within the control panel in \"settings\" -> \"additional settings\"",
        "in": "query",
        "name": "api_token",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 7. apisguru:api.video:get:/live-streams/{liveStreamId}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/live-streams/{liveStreamId}",
  "path_params": [
    "liveStreamId"
  ],
  "query_params": [],
  "summary": "Show live stream",
  "description": "Supply a LivestreamId, and you'll get all the details for streaming into, and watching the livestream. Tutorials that use the [show livestream endpoint](https://api.video/blog/endpoints/live-stream-status).",
  "security": [
    {
      "bearerAuth": []
    }
  ],
  "schema_fields": [
    "assets",
    "assets.hls",
    "assets.iframe",
    "assets.player",
    "assets.thumbnail",
    "broadcasting",
    "liveStreamId",
    "name",
    "playerId",
    "public",
    "record",
    "streamKey"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "bearerAuth": []
      }
    ],
    "schemes": {
      "bearerAuth": {
        "scheme": "bearer",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 8. apisguru:apigee.net:get:/dealer/rv/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/dealer/rv/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [
    "provider"
  ],
  "summary": "Dealer by id",
  "description": "Get a particular dealer's information by its id",
  "security": [
    {
      "authorizeEndpoint": []
    }
  ],
  "schema_fields": [
    "city",
    "country",
    "data_source",
    "dealer_type",
    "dealership_group_name",
    "distance",
    "id",
    "inventory_url",
    "latitude",
    "listing_count",
    "location_ll",
    "longitude",
    "seller_email",
    "seller_name",
    "seller_phone",
    "state",
    "status",
    "street",
    "zip"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "authorizeEndpoint": []
      }
    ],
    "schemes": {
      "authorizeEndpoint": {
        "scheme": "basic",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 9. apisguru:appcenter.ms:patch:/v0.1/apps/{owner_name}/{app_name}/crash_groups/{crash_group_id}

입력 근거 전문:

```json
{
  "method": "PATCH",
  "path": "/v0.1/apps/{owner_name}/{app_name}/crash_groups/{crash_group_id}",
  "path_params": [
    "owner_name",
    "app_name",
    "crash_group_id"
  ],
  "query_params": [],
  "summary": "",
  "description": "Updates a group.",
  "security": [
    {
      "APIToken": []
    }
  ],
  "schema_fields": [
    "annotation",
    "app_version",
    "build",
    "count",
    "crash_group_id",
    "crash_reason",
    "display_id",
    "exception",
    "fatal",
    "first_occurrence",
    "impacted_users",
    "last_occurrence",
    "new_crash_group_id",
    "reason_frame",
    "reason_frame.app_code",
    "reason_frame.class_method",
    "reason_frame.class_name",
    "reason_frame.code_formatted",
    "reason_frame.code_raw",
    "reason_frame.exception_type",
    "reason_frame.file",
    "reason_frame.framework_name",
    "reason_frame.language",
    "reason_frame.line",
    "reason_frame.method",
    "reason_frame.method_params",
    "reason_frame.os_exception_type",
    "status"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "APIToken": []
      }
    ],
    "schemes": {
      "APIToken": {
        "in": "header",
        "name": "X-API-Token",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 10. apisguru:appveyor.com:get:/deployments/{deploymentId}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/deployments/{deploymentId}",
  "path_params": [
    "deploymentId"
  ],
  "query_params": [],
  "summary": "Get deployment",
  "description": "",
  "security": [
    {
      "apiToken": []
    }
  ],
  "schema_fields": [
    "deployment",
    "deployment.build",
    "deployment.build.branch",
    "deployment.build.buildId",
    "deployment.build.message",
    "deployment.build.version",
    "deployment.deploymentId",
    "deployment.finished",
    "deployment.started",
    "deployment.status",
    "deployment.created",
    "deployment.updated",
    "deployment.build.created",
    "deployment.build.updated",
    "deployment.build.authorName",
    "deployment.build.authorUsername",
    "deployment.build.buildNumber",
    "deployment.build.commitId",
    "deployment.build.committed",
    "deployment.build.committerName",
    "deployment.build.committerUsername",
    "deployment.build.finished",
    "deployment.build.isTag",
    "deployment.build.jobs",
    "deployment.build.jobs.[].created",
    "deployment.build.jobs.[].updated",
    "deployment.build.jobs.[].finished",
    "deployment.build.jobs.[].jobId",
    "deployment.build.jobs.[].name",
    "deployment.build.jobs.[].started",
    "deployment.build.jobs.[].status",
    "deployment.build.jobs.[].allowFailure",
    "deployment.build.jobs.[].artifactsCount",
    "deployment.build.jobs.[].compilationErrorsCount",
    "deployment.build.jobs.[].compilationMessagesCount",
    "deployment.build.jobs.[].compilationWarningsCount",
    "deployment.build.jobs.[].failedTestsCount",
    "deployment.build.jobs.[].messagesCount",
    "deployment.build.jobs.[].osType",
    "deployment.build.jobs.[].passedTestsCount"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "project"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "apiToken": []
      }
    ],
    "schemes": {
      "apiToken": {
        "description": "API token can be acquired from https://ci.appveyor.com/api-keys\nThis value must be passed to the server in the `Authorization` header as `\"Bearer <token>\"`.  Since [bearer token authentication support is not explicitly supported in OpenAPI 2.0](https://github.com/OAI/OpenAPI-Specification/issues/583), client code will vary.  Clients created with [swagger-codegen](https://github.com/swagger-api/swagger-codegen) should set `apiKeyPrefix` to `\"Bearer\"` and set `apiKey` to the token.  Other clients may need to set `apiKey` to the string `\"Bearer <token>\"`.\nNote that this should be [fixed in OpenAPI 3.0](https://github.com/OAI/OpenAPI-Specification/pull/807)), whenever that becomes available and supported.\n#### User-Level API Keys\nTo use a user-level API key (prefixed with \"v2.\"), `basePath` must be changed to `/api/account/{accountName}` where `{accountName}` is the name of the account for which requests will be made.",
        "in": "header",
        "name": "Authorization",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 11. apisguru:appwrite.io:get:/teams/{teamId}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/teams/{teamId}",
  "path_params": [
    "teamId"
  ],
  "query_params": [],
  "summary": "Get Team",
  "description": "Get a team by its unique ID. All team members have read access for this resource.",
  "security": [
    {
      "JWT": [],
      "Project": []
    }
  ],
  "schema_fields": [
    "$id",
    "dateCreated",
    "name",
    "sum"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "JWT": [],
        "Project": []
      }
    ],
    "schemes": {
      "JWT": {
        "description": "Your secret JSON Web Token",
        "in": "header",
        "name": "X-Appwrite-JWT",
        "type": "apiKey"
      },
      "Project": {
        "description": "Your project ID",
        "in": "header",
        "name": "X-Appwrite-Project",
        "type": "apiKey",
        "x-appwrite": {
          "demo": "5df5acd0d48c2"
        }
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 12. apisguru:authentiq.io:put:/client/{client_id}

입력 근거 전문:

```json
{
  "method": "PUT",
  "path": "/client/{client_id}",
  "path_params": [
    "client_id"
  ],
  "query_params": [],
  "summary": "Update a client",
  "description": "Update the configuration of a previously registered client.\n",
  "security": [
    {
      "client_registration_token": []
    },
    {
      "oauth_code": []
    },
    {
      "oauth_implicit": []
    }
  ],
  "schema_fields": [
    "application_type",
    "client_id",
    "client_name",
    "client_uri",
    "contacts",
    "default_max_age",
    "default_scopes",
    "grant_types",
    "logo_uri",
    "policy_uri",
    "redirect_uris",
    "response_types",
    "tos_uri"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "client_registration_token": []
      },
      {
        "oauth_code": []
      },
      {
        "oauth_implicit": []
      }
    ],
    "schemes": {
      "client_registration_token": {
        "description": "Client management via registration token.",
        "in": "header",
        "name": "Authorization",
        "type": "apiKey"
      },
      "oauth_code": {
        "description": "End-user authentication.",
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "https://connect.authentiq.io/authorize",
            "scopes": {
              "address": "The user's postal address",
              "aq:location": "The user's current location",
              "aq:name": "The user's full name",
              "aq:push": "Enable *One click sign-in*",
              "email": "The user's email address",
              "oidc": "Enable OIDC flow",
              "phone": "The user's phone number"
            },
            "tokenUrl": "https://connect.authentiq.io/token"
          }
        },
        "type": "oauth2"
      },
      "oauth_implicit": {
        "description": "End-user authentication.",
        "flows": {
          "implicit": {
            "authorizationUrl": "https://connect.authentiq.io/authorize",
            "scopes": {
              "address": "The user's postal address",
              "aq:location": "The user's current location",
              "aq:name": "The user's full name",
              "aq:push": "Enable *One click sign-in*",
              "email": "The user's email address",
              "oidc": "Enable OIDC flow",
              "phone": "The user's phone number"
            }
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 13. apisguru:bbc.com:get:/master_brands

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/master_brands",
  "path_params": [],
  "query_params": [
    "sort",
    "sort_direction",
    "mixin",
    "mid",
    "page",
    "page_size",
    "partner_id",
    "partner_pid",
    "q"
  ],
  "summary": "List all Master Brands",
  "description": "List all Master Brands",
  "security": [
    {
      "api_key": []
    }
  ],
  "schema_fields": [
    "deprecations",
    "deprecations.deprecated",
    "deprecations.deprecated.[].deprecated_since",
    "deprecations.deprecated.[].name",
    "deprecations.deprecated.[].replaced_by",
    "deprecations.deprecated.[].replacement_type",
    "deprecations.deprecated.[].type",
    "filters",
    "filters.filter",
    "filters.filter.[].default",
    "filters.filter.[].depends_on",
    "filters.filter.[].deprecated",
    "filters.filter.[].deprecated_since",
    "filters.filter.[].guaranteed_until",
    "filters.filter.[].max_value",
    "filters.filter.[].min_value",
    "filters.filter.[].multiple_values",
    "filters.filter.[].name",
    "filters.filter.[].option",
    "filters.filter.[].option.[].href",
    "filters.filter.[].option.[].release_status",
    "filters.filter.[].option.[].title",
    "filters.filter.[].option.[].value",
    "filters.filter.[].prefer",
    "filters.filter.[].prohibits",
    "filters.filter.[].prohibits.[].filter",
    "filters.filter.[].prohibits.[].filter.[].name",
    "filters.filter.[].prohibits.[].mixin",
    "filters.filter.[].prohibits.[].mixin.[].filter",
    "filters.filter.[].prohibits.[].mixin.[].filter.[].name",
    "filters.filter.[].prohibits.[].mixin.[].mixin",
    "filters.filter.[].prohibits.[].mixin.[].mixin.[].name",
    "filters.filter.[].prohibits.[].mixin.[].name",
    "filters.filter.[].release_status",
    "filters.filter.[].replaced_by",
    "filters.filter.[].required",
    "filters.filter.[].title",
    "filters.filter.[].type",
    "filters.unstable_filters",
    "filters.unstable_filters.filter"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "author"
  ],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "api_key": []
      }
    ],
    "schemes": {
      "api_key": {
        "in": "query",
        "name": "api_key",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 14. apisguru:bbc.com:get:/programmes

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/programmes",
  "path_params": [],
  "query_params": [
    "sort",
    "sort_direction",
    "mixin",
    "audio_described",
    "availability",
    "availability_entity_type",
    "availability_from",
    "availability_type",
    "children_of",
    "descendants_of",
    "duration",
    "entity_type",
    "format",
    "genre",
    "group",
    "initial_letter",
    "initial_letter_end",
    "initial_letter_start",
    "initial_letter_strict",
    "item",
    "master_brand",
    "media_set",
    "media_type",
    "page",
    "page_size",
    "partner_id",
    "partner_pid",
    "payment_type",
    "people",
    "pid",
    "promoted_for",
    "q",
    "signed",
    "tag_name",
    "tag_scheme",
    "tleo",
    "version",
    "embargoed"
  ],
  "summary": "Start here for programmes metadata: Brands, Series, Episodes and Clips",
  "description": "Fetch metadata about Programmes (brands, series, episodes, clips). By applying different filter restrictions this feed can be used in many ways, for example to retrieve all series belonging to a brand, all the episodes and/or clips for a specific series, or any TLEO objects for a masterbrand. Other filters permit restricting to specific formats and/or genres, and you can request specific versions (for example Signed or Audio-Described). Parameters may be combined in any way suitable for your application.",
  "security": [
    {
      "api_key": []
    }
  ],
  "schema_fields": [
    "deprecations",
    "deprecations.deprecated",
    "deprecations.deprecated.[].deprecated_since",
    "deprecations.deprecated.[].name",
    "deprecations.deprecated.[].replaced_by",
    "deprecations.deprecated.[].replacement_type",
    "deprecations.deprecated.[].type",
    "filters",
    "filters.filter",
    "filters.filter.[].default",
    "filters.filter.[].depends_on",
    "filters.filter.[].deprecated",
    "filters.filter.[].deprecated_since",
    "filters.filter.[].guaranteed_until",
    "filters.filter.[].max_value",
    "filters.filter.[].min_value",
    "filters.filter.[].multiple_values",
    "filters.filter.[].name",
    "filters.filter.[].option",
    "filters.filter.[].option.[].href",
    "filters.filter.[].option.[].release_status",
    "filters.filter.[].option.[].title",
    "filters.filter.[].option.[].value",
    "filters.filter.[].prefer",
    "filters.filter.[].prohibits",
    "filters.filter.[].prohibits.[].filter",
    "filters.filter.[].prohibits.[].filter.[].name",
    "filters.filter.[].prohibits.[].mixin",
    "filters.filter.[].prohibits.[].mixin.[].filter",
    "filters.filter.[].prohibits.[].mixin.[].filter.[].name",
    "filters.filter.[].prohibits.[].mixin.[].mixin",
    "filters.filter.[].prohibits.[].mixin.[].mixin.[].name",
    "filters.filter.[].prohibits.[].mixin.[].name",
    "filters.filter.[].release_status",
    "filters.filter.[].replaced_by",
    "filters.filter.[].required",
    "filters.filter.[].title",
    "filters.filter.[].type",
    "filters.unstable_filters",
    "filters.unstable_filters.filter"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "author"
  ],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "api_key": []
      }
    ],
    "schemes": {
      "api_key": {
        "in": "query",
        "name": "api_key",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 15. apisguru:bbc.com:get:/promotions

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/promotions",
  "path_params": [],
  "query_params": [
    "mixin",
    "context",
    "page",
    "page_size",
    "partner_id",
    "partner_pid",
    "pid",
    "promoted_by",
    "promoted_for",
    "q",
    "status"
  ],
  "summary": "Discover metadata for content promotions",
  "description": "Details of short-term editorially curated \"promotions\", for instance those programmes featured on iPlayer today",
  "security": [
    {
      "api_key": []
    }
  ],
  "schema_fields": [
    "deprecations",
    "deprecations.deprecated",
    "deprecations.deprecated.[].deprecated_since",
    "deprecations.deprecated.[].name",
    "deprecations.deprecated.[].replaced_by",
    "deprecations.deprecated.[].replacement_type",
    "deprecations.deprecated.[].type",
    "filters",
    "filters.filter",
    "filters.filter.[].default",
    "filters.filter.[].depends_on",
    "filters.filter.[].deprecated",
    "filters.filter.[].deprecated_since",
    "filters.filter.[].guaranteed_until",
    "filters.filter.[].max_value",
    "filters.filter.[].min_value",
    "filters.filter.[].multiple_values",
    "filters.filter.[].name",
    "filters.filter.[].option",
    "filters.filter.[].option.[].href",
    "filters.filter.[].option.[].release_status",
    "filters.filter.[].option.[].title",
    "filters.filter.[].option.[].value",
    "filters.filter.[].prefer",
    "filters.filter.[].prohibits",
    "filters.filter.[].prohibits.[].filter",
    "filters.filter.[].prohibits.[].filter.[].name",
    "filters.filter.[].prohibits.[].mixin",
    "filters.filter.[].prohibits.[].mixin.[].filter",
    "filters.filter.[].prohibits.[].mixin.[].filter.[].name",
    "filters.filter.[].prohibits.[].mixin.[].mixin",
    "filters.filter.[].prohibits.[].mixin.[].mixin.[].name",
    "filters.filter.[].prohibits.[].mixin.[].name",
    "filters.filter.[].release_status",
    "filters.filter.[].replaced_by",
    "filters.filter.[].required",
    "filters.filter.[].title",
    "filters.filter.[].type",
    "filters.unstable_filters",
    "filters.unstable_filters.filter"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "author"
  ],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "api_key": []
      }
    ],
    "schemes": {
      "api_key": {
        "in": "query",
        "name": "api_key",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 16. apisguru:beezup.com:get:/orders/v3/{marketplaceTechnicalCode}/{accountId}/{beezUPOrderId}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/orders/v3/{marketplaceTechnicalCode}/{accountId}/{beezUPOrderId}",
  "path_params": [
    "marketplaceTechnicalCode",
    "accountId",
    "beezUPOrderId"
  ],
  "query_params": [],
  "summary": "Get full Order and Order Item(s) properties",
  "description": "",
  "security": null,
  "schema_fields": [
    "accountId",
    "beezUPOrderId",
    "beezUPOrderUrl",
    "etag",
    "links",
    "links.self",
    "links.self.allOptionalParamsProvided",
    "links.self.allRequiredParamsProvided",
    "links.self.description",
    "links.self.docUrl",
    "links.self.href",
    "links.self.info",
    "links.self.info.errors",
    "links.self.info.errors.[].errorArguments",
    "links.self.info.errors.[].errorCode",
    "links.self.info.errors.[].errorGuid",
    "links.self.info.errors.[].errorMessage",
    "links.self.info.errors.[].exceptionDetail",
    "links.self.info.errors.[].exceptionDetail.helpLink",
    "links.self.info.errors.[].exceptionDetail.message",
    "links.self.info.errors.[].exceptionDetail.stackTrace",
    "links.self.info.errors.[].exceptionDetail.type",
    "links.self.info.errors.[].objectName",
    "links.self.info.errors.[].propertyName",
    "links.self.info.errors.[].propertyValue",
    "links.self.info.errors.[].source",
    "links.self.info.errors.[].technicalErrorMessage",
    "links.self.info.errors.[].utcDate",
    "links.self.info.informations",
    "links.self.info.informations.[].informationArguments",
    "links.self.info.informations.[].informationCode",
    "links.self.info.informations.[].informationMessage",
    "links.self.info.informations.[].objectName",
    "links.self.info.informations.[].propertyName",
    "links.self.info.informations.[].propertyValue",
    "links.self.info.successes",
    "links.self.info.successes.[].objectName",
    "links.self.info.successes.[].propertyName",
    "links.self.info.successes.[].propertyValue",
    "links.self.info.successes.[].successArguments"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "accountId"
  ],
  "tenant_cols": [
    "accountId"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 17. apisguru:bigredcloud.com:get:/v1/bankAccounts/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/v1/bankAccounts/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Returns information about a single Bank Account.",
  "description": "",
  "security": null,
  "schema_fields": [
    "acCode",
    "accountName",
    "accountNumber",
    "address",
    "bankFeedSource",
    "businessIdentifierCodes",
    "categoryId",
    "creditorScheme",
    "details",
    "id",
    "internationalBankAccountNumber",
    "isDefaultBank",
    "lastChq",
    "nominalAcCode",
    "oBalance",
    "sortCode",
    "timestamp"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "accountName"
  ],
  "tenant_cols": [
    "accountName"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 18. apisguru:bigredcloud.com:put:/v1/customers/{id}

입력 근거 전문:

```json
{
  "method": "PUT",
  "path": "/v1/customers/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Updates an existing Customer.",
  "description": "",
  "security": null,
  "schema_fields": [],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "accountName"
  ],
  "tenant_cols": [
    "accountName"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 19. apisguru:box.com:get:/collections/{collection_id}/items

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/collections/{collection_id}/items",
  "path_params": [
    "collection_id"
  ],
  "query_params": [
    "fields",
    "offset",
    "limit"
  ],
  "summary": "List collection items",
  "description": "Retrieves the files and/or folders contained within\nthis collection.",
  "security": [
    {
      "OAuth2Security": []
    }
  ],
  "schema_fields": [
    "limit",
    "offset",
    "order",
    "order.[].by",
    "order.[].direction",
    "total_count",
    "entries",
    "entries.[].etag",
    "entries.[].id",
    "entries.[].type",
    "entries.[].file_version",
    "entries.[].file_version.id",
    "entries.[].file_version.type",
    "entries.[].file_version.sha1",
    "entries.[].name",
    "entries.[].sequence_id",
    "entries.[].sha1",
    "entries.[].url"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "OAuth2Security": []
      }
    ],
    "schemes": {
      "OAuth2Security": {
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "https://account.box.com/api/oauth2/authorize",
            "scopes": {
              "manage_app_users": "Provision and manage app users",
              "manage_data_retention": "Manage data retention polices",
              "manage_enterprise_properties": "Manage enterprise properties",
              "manage_groups": "Manage an enterprise's groups",
              "manage_legal_hold": "Manage Legal Holds",
              "manage_managed_users": "Provision and manage managed users",
              "manage_webhook": "Create webhooks programmatically through the API",
              "root_readonly": "Read all files and folders stored in Box",
              "root_readwrite": "Read and write all files and folders stored in Box"
            },
            "tokenUrl": "https://api.box.com/oauth2/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 20. apisguru:browshot.com:get:/browser/info

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/browser/info",
  "path_params": [],
  "query_params": [
    "id"
  ],
  "summary": "Get information about a browser",
  "description": "Get information about a browser.",
  "security": [
    {
      "apiKeyQuery": []
    }
  ],
  "schema_fields": [
    "flash",
    "id",
    "javascript",
    "mobile",
    "name"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "apiKeyQuery": []
      }
    ],
    "schemes": {
      "apiKeyQuery": {
        "in": "query",
        "name": "key",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 21. apisguru:chaingateway.io:get:/v2/ethereum/nfts/{contract}/uri/{token_id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/v2/ethereum/nfts/{contract}/uri/{token_id}",
  "path_params": [
    "contract",
    "token_id"
  ],
  "query_params": [],
  "summary": "getNFTUri",
  "description": "Get the URI of an NFT",
  "security": null,
  "schema_fields": [
    "data",
    "data.uri",
    "message",
    "ok",
    "status"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 22. apisguru:clever-cloud.com:post:/organisations/{id}/addonproviders/{providerId}/features

입력 근거 전문:

```json
{
  "method": "POST",
  "path": "/organisations/{id}/addonproviders/{providerId}/features",
  "path_params": [
    "id",
    "providerId"
  ],
  "query_params": [],
  "summary": "",
  "description": "",
  "security": null,
  "schema_fields": [
    "name",
    "type",
    "value"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 23. apisguru:clicksend.com:put:/lists/{list_id}/contacts/{contact_id}

입력 근거 전문:

```json
{
  "method": "PUT",
  "path": "/lists/{list_id}/contacts/{contact_id}",
  "path_params": [
    "list_id",
    "contact_id"
  ],
  "query_params": [],
  "summary": "Update a specific contact",
  "description": "",
  "security": [
    {
      "basic": []
    }
  ],
  "schema_fields": [],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "organization_name"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "basic": []
      }
    ],
    "schemes": {
      "basic": {
        "scheme": "basic",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 24. apisguru:configcat.com:get:/v1/configs/{configId}/settings

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/v1/configs/{configId}/settings",
  "path_params": [
    "configId"
  ],
  "query_params": [],
  "summary": "List Flags",
  "description": "This endpoint returns the list of the Feature Flags and Settings defined in a \nspecified Config, identified by the `configId` parameter.",
  "security": [
    {
      "Basic": []
    }
  ],
  "schema_fields": [
    "[]._embedded",
    "[]._embedded.tags",
    "[]._embedded.tags.[]._embedded",
    "[]._embedded.tags.[]._embedded.product",
    "[]._embedded.tags.[]._embedded.product._embedded",
    "[]._embedded.tags.[]._embedded.product._embedded.organization",
    "[]._embedded.tags.[]._embedded.product._embedded.organization._links",
    "[]._embedded.tags.[]._embedded.product._embedded.organization._links.members",
    "[]._embedded.tags.[]._embedded.product._embedded.organization._links.products",
    "[]._embedded.tags.[]._embedded.product._embedded.organization.name",
    "[]._embedded.tags.[]._embedded.product._embedded.organization.organizationId",
    "[]._embedded.tags.[]._embedded.product._links",
    "[]._embedded.tags.[]._embedded.product._links.configs",
    "[]._embedded.tags.[]._embedded.product._links.environments",
    "[]._embedded.tags.[]._embedded.product._links.members",
    "[]._embedded.tags.[]._embedded.product._links.permission-groups",
    "[]._embedded.tags.[]._embedded.product._links.segments",
    "[]._embedded.tags.[]._embedded.product._links.self",
    "[]._embedded.tags.[]._embedded.product._links.tags",
    "[]._embedded.tags.[]._embedded.product.description",
    "[]._embedded.tags.[]._embedded.product.name",
    "[]._embedded.tags.[]._embedded.product.order",
    "[]._embedded.tags.[]._embedded.product.productId",
    "[]._embedded.tags.[]._embedded.product.reasonRequired",
    "[]._embedded.tags.[]._links",
    "[]._embedded.tags.[]._links.self",
    "[]._embedded.tags.[].color",
    "[]._embedded.tags.[].name",
    "[]._embedded.tags.[].tagId",
    "[]._links",
    "[]._links.self",
    "[].configId",
    "[].configName",
    "[].hint",
    "[].key",
    "[].name",
    "[].order",
    "[].settingId",
    "[].settingType",
    "[].tags"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "Basic": []
      }
    ],
    "schemes": {
      "Basic": {
        "description": "To authenticate with the API you have to fill the `Authorization` HTTP request header with your Public API credentials.\n\nYou can create your credentials on the <a target=\"_blank\" href=\"https://app.configcat.com/my-account/public-api-credentials\">Public API credentials management page</a>.",
        "scheme": "basic",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 25. apisguru:contribly.com:get:/users/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/users/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Retrieve a single user by id",
  "description": "",
  "security": null,
  "schema_fields": [
    "bio",
    "displayName",
    "id",
    "registered",
    "username"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "username"
  ],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 26. apisguru:cpy.re:get:/api/v1/users/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/api/v1/users/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [
    "withStats"
  ],
  "summary": "Get a user",
  "description": "",
  "security": [
    {
      "OAuth2": []
    }
  ],
  "schema_fields": [
    "account",
    "account.createdAt",
    "account.followersCount",
    "account.followingCount",
    "account.host",
    "account.hostRedundancyAllowed",
    "account.id",
    "account.name",
    "account.updatedAt",
    "account.url",
    "account.description",
    "account.displayName",
    "account.userId",
    "autoPlayNextVideo",
    "autoPlayNextVideoPlaylist",
    "autoPlayVideo",
    "blocked",
    "blockedReason",
    "createdAt",
    "email",
    "emailVerified",
    "id",
    "lastLoginDate",
    "noAccountSetupWarningModal",
    "noInstanceConfigWarningModal",
    "noWelcomeModal",
    "nsfwPolicy",
    "p2pEnabled",
    "pluginAuth",
    "role",
    "role.id",
    "role.label",
    "theme",
    "username",
    "videoChannels",
    "videoChannels.[].createdAt",
    "videoChannels.[].followersCount",
    "videoChannels.[].followingCount",
    "videoChannels.[].host",
    "videoChannels.[].hostRedundancyAllowed"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "account",
    "username"
  ],
  "tenant_cols": [
    "account"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "OAuth2": []
      }
    ],
    "schemes": {
      "OAuth2": {
        "description": "Authenticating via OAuth requires the following steps:\n- Have an activated account\n- [Generate] an access token for that account at `/api/v1/users/token`.\n- Make requests with the *Authorization: Bearer <token\\>* header\n- Profit, depending on the role assigned to the account\n\nNote that the __access token is valid for 1 day__ and is given\nalong with a __refresh token valid for 2 weeks__.\n\n[Generate]: https://docs.joinpeertube.org/api/rest-getting-started\n",
        "flows": {
          "password": {
            "scopes": {
              "admin": "Admin scope",
              "moderator": "Moderator scope",
              "user": "User scope"
            },
            "tokenUrl": "/api/v1/users/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 27. apisguru:deutschebahn.com:get:/providernetworks/{uid}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/providernetworks/{uid}",
  "path_params": [
    "uid"
  ],
  "query_params": [],
  "summary": "Get information about the ProviderNetworkResources.",
  "description": "Get information about the ProviderNetworkResources.\n",
  "security": null,
  "schema_fields": [
    "_links",
    "_links.[].href",
    "_links.[].rel",
    "_links.[].verb",
    "attributes",
    "category",
    "category._links",
    "category._links.[].href",
    "category._links.[].rel",
    "category._links.[].verb",
    "category.attributes",
    "category.description",
    "category.expand",
    "category.href",
    "category.name",
    "category.price",
    "category.price.[]._links",
    "category.price.[]._links.[].href",
    "category.price.[]._links.[].rel",
    "category.price.[]._links.[].verb",
    "category.price.[].attributes",
    "category.price.[].currency",
    "category.price.[].description",
    "category.price.[].expand",
    "category.price.[].grossamount",
    "category.price.[].href",
    "category.price.[].interval",
    "category.price.[].name",
    "category.price.[].preferredprice",
    "category.price.[].taxrate",
    "category.price.[].type",
    "category.price.[].uid",
    "category.uid",
    "description",
    "expand",
    "href",
    "name",
    "provider",
    "provider._links",
    "provider._links.[].href"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "provider"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 28. apisguru:discourse.local:get:/admin/users/{id}.json

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/admin/users/{id}.json",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Get a user by id",
  "description": "",
  "security": null,
  "schema_fields": [
    "active",
    "admin",
    "api_key_count",
    "approved_by",
    "approved_by.avatar_template",
    "approved_by.id",
    "approved_by.name",
    "approved_by.username",
    "associated_accounts",
    "avatar_template",
    "badge_count",
    "bounce_score",
    "can_activate",
    "can_be_anonymized",
    "can_be_deleted",
    "can_be_merged",
    "can_deactivate",
    "can_delete_all_posts",
    "can_delete_sso_record",
    "can_disable_second_factor",
    "can_grant_admin",
    "can_grant_moderation",
    "can_impersonate",
    "can_revoke_admin",
    "can_revoke_moderation",
    "can_send_activation_email",
    "can_view_action_logs",
    "created_at",
    "created_at_age",
    "days_visited",
    "external_ids",
    "flag_level",
    "flags_given_count",
    "flags_received_count",
    "full_suspend_reason",
    "groups",
    "groups.[].allow_membership_requests",
    "groups.[].automatic",
    "groups.[].bio_cooked",
    "groups.[].bio_excerpt"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "username"
  ],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 29. apisguru:dracoon.team:get:/v4/nodes/files/uploads/{upload_id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/v4/nodes/files/uploads/{upload_id}",
  "path_params": [
    "upload_id"
  ],
  "query_params": [],
  "summary": "Request status of S3 file upload",
  "description": "<h3 style='padding: 5px; background-color: #F6F7F8; border: 1px solid #AAA; border-radius: 5px; display: table-cell;'>&#128640; Since v4.15.0</h3>\n\n### Description:\nRequest status of a S3 file upload.\n\n### Precondition:\nAn upload channel has been created and user has to be the creator of the upload channel.\n\n### Postcondition:\nStatus of S3 multipart upload request is returned.\n\n### Further Information:\nNone.\n\n### Possible errors:\n<details style=\"padding: 10px; background-color: #F6F7F8; border: 1px solid #AAA; border-radius: 5px;\">\n<summary style=\"cursor: pointer; outline: none\"><strong>Expand</strong></summary>\n\n| Http Status | Error Code | Description |\n| :--- | :--- | :--- |\n| `400 Bad Request` | `-80000` | Mandatory fields cannot be empty |\n| `400 Bad Request` | `-80001` | Invalid positive number |\n| `400 Bad Request` | `-80002` | Invalid number |\n| `400 Bad Request` | `-40001` | (Target) room is not encrypted |\n| `400 Bad Request` | `-40755` | Bad file name |\n| `400 Bad Request` | `-40763` | File key must be set for an upload into encrypted room |\n| `400 Bad Request` | `-50506` | Exceeds the number of files for this Upload Share |\n| `403 Forbidden` |  | Access denied |\n| `404 Not Found` | `-20501` | Upload not found |\n| `404 Not Found` | `-40000` | Container not found |\n| `404 Not Found` | `-41000` | Node not found |\n| `404 Not Found` | `-70501` | User not found |\n| `409 Conflict` | `-40010` | Container cannot be overwritten |\n| `409 Conflict` |  | File cannot be overwritten |\n| `500 Internal Server Error` |  | System Error |\n| `502 Bad Gateway` |  | S3 Error |\n| `502 Insufficient Storage` | `-50504` | Exceeds the quota for this Upload Share |\n| `502 Insufficient Storage` | `-40200` | Exceeds the free node quota in room |\n| `502 Insufficient Storage` | `-90200` | Exceeds the free customer quota |\n| `502 Insufficient Storage` | `-90201` | Exceeds the free customer physical disk space |\n\n</details>",
  "security": [
    {
      "oauth2": []
    }
  ],
  "schema_fields": [
    "errorDetails",
    "errorDetails.code",
    "errorDetails.debugInfo",
    "errorDetails.errorCode",
    "errorDetails.message",
    "node",
    "node.authParentId",
    "node.branchVersion",
    "node.children",
    "node.classification",
    "node.cntChildren",
    "node.cntComments",
    "node.cntDeletedVersions",
    "node.cntDownloadShares",
    "node.cntFiles",
    "node.cntFolders",
    "node.cntRooms",
    "node.cntUploadShares",
    "node.createdAt",
    "node.createdBy",
    "node.createdBy.avatarUuid",
    "node.createdBy.displayName",
    "node.createdBy.email",
    "node.createdBy.firstName",
    "node.createdBy.id",
    "node.createdBy.lastName",
    "node.createdBy.title",
    "node.createdBy.userName",
    "node.createdBy.userType",
    "node.encryptionInfo",
    "node.encryptionInfo.dataSpaceKeyState",
    "node.encryptionInfo.roomKeyState",
    "node.encryptionInfo.userKeyState",
    "node.expireAt",
    "node.fileType",
    "node.hasActivitiesLog",
    "node.hash",
    "node.id",
    "node.inheritPermissions",
    "node.isBrowsable"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "createdBy",
    "userName"
  ],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "oauth2": []
      }
    ],
    "schemes": {
      "oauth2": {
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "/oauth/authorize",
            "scopes": {
              "all": "every operation is allowed"
            },
            "tokenUrl": "/oauth/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 30. apisguru:evetech.net:get:/characters/{character_id}/calendar/{event_id}/

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/characters/{character_id}/calendar/{event_id}/",
  "path_params": [
    "character_id",
    "event_id"
  ],
  "query_params": [],
  "summary": "Get an event",
  "description": "Get all the information for a specific event\n\n---\nAlternate route: `/dev/characters/{character_id}/calendar/{event_id}/`\n\nAlternate route: `/v3/characters/{character_id}/calendar/{event_id}/`\n\n---\nThis route is cached for up to 5 seconds",
  "security": [
    {
      "evesso": [
        "esi-calendar.read_calendar_events.v1"
      ]
    }
  ],
  "schema_fields": [
    "date",
    "duration",
    "event_id",
    "importance",
    "owner_id",
    "owner_name",
    "owner_type",
    "response",
    "text",
    "title"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "owner_id",
    "owner_name"
  ],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "evesso": [
          "esi-calendar.read_calendar_events.v1"
        ]
      }
    ],
    "schemes": {
      "evesso": {
        "authorizationUrl": "https://login.eveonline.com/v2/oauth/authorize",
        "flow": "implicit",
        "scopes": {
          "esi-alliances.read_contacts.v1": "EVE SSO scope esi-alliances.read_contacts.v1",
          "esi-assets.read_assets.v1": "EVE SSO scope esi-assets.read_assets.v1",
          "esi-assets.read_corporation_assets.v1": "EVE SSO scope esi-assets.read_corporation_assets.v1",
          "esi-bookmarks.read_character_bookmarks.v1": "EVE SSO scope esi-bookmarks.read_character_bookmarks.v1",
          "esi-bookmarks.read_corporation_bookmarks.v1": "EVE SSO scope esi-bookmarks.read_corporation_bookmarks.v1",
          "esi-calendar.read_calendar_events.v1": "EVE SSO scope esi-calendar.read_calendar_events.v1",
          "esi-calendar.respond_calendar_events.v1": "EVE SSO scope esi-calendar.respond_calendar_events.v1",
          "esi-characters.read_agents_research.v1": "EVE SSO scope esi-characters.read_agents_research.v1",
          "esi-characters.read_blueprints.v1": "EVE SSO scope esi-characters.read_blueprints.v1",
          "esi-characters.read_contacts.v1": "EVE SSO scope esi-characters.read_contacts.v1",
          "esi-characters.read_corporation_roles.v1": "EVE SSO scope esi-characters.read_corporation_roles.v1",
          "esi-characters.read_fatigue.v1": "EVE SSO scope esi-characters.read_fatigue.v1",
          "esi-characters.read_fw_stats.v1": "EVE SSO scope esi-characters.read_fw_stats.v1",
          "esi-characters.read_loyalty.v1": "EVE SSO scope esi-characters.read_loyalty.v1",
          "esi-characters.read_medals.v1": "EVE SSO scope esi-characters.read_medals.v1",
          "esi-characters.read_notifications.v1": "EVE SSO scope esi-characters.read_notifications.v1",
          "esi-characters.read_opportunities.v1": "EVE SSO scope esi-characters.read_opportunities.v1",
          "esi-characters.read_standings.v1": "EVE SSO scope esi-characters.read_standings.v1",
          "esi-characters.read_titles.v1": "EVE SSO scope esi-characters.read_titles.v1",
          "esi-characters.write_contacts.v1": "EVE SSO scope esi-characters.write_contacts.v1",
          "esi-characterstats.read.v1": "EVE SSO scope esi-characterstats.read.v1",
          "esi-clones.read_clones.v1": "EVE SSO scope esi-clones.read_clones.v1",
          "esi-clones.read_implants.v1": "EVE SSO scope esi-clones.read_implants.v1",
          "esi-contracts.read_character_contracts.v1": "EVE SSO scope esi-contracts.read_character_contracts.v1",
          "esi-contracts.read_corporation_contracts.v1": "EVE SSO scope esi-contracts.read_corporation_contracts.v1",
          "esi-corporations.read_blueprints.v1": "EVE SSO scope esi-corporations.read_blueprints.v1",
          "esi-corporations.read_contacts.v1": "EVE SSO scope esi-corporations.read_contacts.v1",
          "esi-corporations.read_container_logs.v1": "EVE SSO scope esi-corporations.read_container_logs.v1",
          "esi-corporations.read_corporation_membership.v1": "EVE SSO scope esi-corporations.read_corporation_membership.v1",
          "esi-corporations.read_divisions.v1": "EVE SSO scope esi-corporations.read_divisions.v1",
          "esi-corporations.read_facilities.v1": "EVE SSO scope esi-corporations.read_facilities.v1",
          "esi-corporations.read_fw_stats.v1": "EVE SSO scope esi-corporations.read_fw_stats.v1",
          "esi-corporations.read_medals.v1": "EVE SSO scope esi-corporations.read_medals.v1",
          "esi-corporations.read_standings.v1": "EVE SSO scope esi-corporations.read_standings.v1",
          "esi-corporations.read_starbases.v1": "EVE SSO scope esi-corporations.read_starbases.v1",
          "esi-corporations.read_structures.v1": "EVE SSO scope esi-corporations.read_structures.v1",
          "esi-corporations.read_titles.v1": "EVE SSO scope esi-corporations.read_titles.v1",
          "esi-corporations.track_members.v1": "EVE SSO scope esi-corporations.track_members.v1",
          "esi-fittings.read_fittings.v1": "EVE SSO scope esi-fittings.read_fittings.v1",
          "esi-fittings.write_fittings.v1": "EVE SSO scope esi-fittings.write_fittings.v1",
          "esi-fleets.read_fleet.v1": "EVE SSO scope esi-fleets.read_fleet.v1",
          "esi-fleets.write_fleet.v1": "EVE SSO scope esi-fleets.write_fleet.v1",
          "esi-industry.read_character_jobs.v1": "EVE SSO scope esi-industry.read_character_jobs.v1",
          "esi-industry.read_character_mining.v1": "EVE SSO scope esi-industry.read_character_mining.v1",
          "esi-industry.read_corporation_jobs.v1": "EVE SSO scope esi-industry.read_corporation_jobs.v1",
          "esi-industry.read_corporation_mining.v1": "EVE SSO scope esi-industry.read_corporation_mining.v1",
          "esi-killmails.read_corporation_killmails.v1": "EVE SSO scope esi-killmails.read_corporation_killmails.v1",
          "esi-killmails.read_killmails.v1": "EVE SSO scope esi-killmails.read_killmails.v1",
          "esi-location.read_location.v1": "EVE SSO scope esi-location.read_location.v1",
          "esi-location.read_online.v1": "EVE SSO scope esi-location.read_online.v1",
          "esi-location.read_ship_type.v1": "EVE SSO scope esi-location.read_ship_type.v1",
          "esi-mail.organize_mail.v1": "EVE SSO scope esi-mail.organize_mail.v1",
          "esi-mail.read_mail.v1": "EVE SSO scope esi-mail.read_mail.v1",
          "esi-mail.send_mail.v1": "EVE SSO scope esi-mail.send_mail.v1",
          "esi-markets.read_character_orders.v1": "EVE SSO scope esi-markets.read_character_orders.v1",
          "esi-markets.read_corporation_orders.v1": "EVE SSO scope esi-markets.read_corporation_orders.v1",
          "esi-markets.structure_markets.v1": "EVE SSO scope esi-markets.structure_markets.v1",
          "esi-planets.manage_planets.v1": "EVE SSO scope esi-planets.manage_planets.v1",
          "esi-planets.read_customs_offices.v1": "EVE SSO scope esi-planets.read_customs_offices.v1",
          "esi-search.search_structures.v1": "EVE SSO scope esi-search.search_structures.v1",
          "esi-skills.read_skillqueue.v1": "EVE SSO scope esi-skills.read_skillqueue.v1",
          "esi-skills.read_skills.v1": "EVE SSO scope esi-skills.read_skills.v1",
          "esi-ui.open_window.v1": "EVE SSO scope esi-ui.open_window.v1",
          "esi-ui.write_waypoint.v1": "EVE SSO scope esi-ui.write_waypoint.v1",
          "esi-universe.read_structures.v1": "EVE SSO scope esi-universe.read_structures.v1",
          "esi-wallet.read_character_wallet.v1": "EVE SSO scope esi-wallet.read_character_wallet.v1",
          "esi-wallet.read_corporation_wallets.v1": "EVE SSO scope esi-wallet.read_corporation_wallets.v1"
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 31. apisguru:files.com:get:/api_keys

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/api_keys",
  "path_params": [],
  "query_params": [
    "user_id",
    "cursor",
    "per_page",
    "sort_by",
    "filter",
    "filter_gt",
    "filter_gteq",
    "filter_lt",
    "filter_lteq"
  ],
  "summary": "List Api Keys",
  "description": "List Api Keys",
  "security": null,
  "schema_fields": [
    "[].created_at",
    "[].description",
    "[].descriptive_label",
    "[].expires_at",
    "[].id",
    "[].key",
    "[].last_use_at",
    "[].name",
    "[].path",
    "[].permission_set",
    "[].platform",
    "[].url",
    "[].user_id"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "user_id"
  ],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 32. apisguru:files.com:get:/automation_runs

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/automation_runs",
  "path_params": [],
  "query_params": [
    "user_id",
    "cursor",
    "per_page",
    "sort_by",
    "filter",
    "automation_id"
  ],
  "summary": "List Automation Runs",
  "description": "List Automation Runs",
  "security": null,
  "schema_fields": [
    "[].automation_id",
    "[].completed_at",
    "[].created_at",
    "[].id",
    "[].status",
    "[].status_messages_url"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 33. apisguru:flat.io:post:/scores/{score}/fork

입력 근거 전문:

```json
{
  "method": "POST",
  "path": "/scores/{score}/fork",
  "path_params": [
    "score"
  ],
  "query_params": [
    "sharingKey"
  ],
  "summary": "Fork a score",
  "description": "This API call will make a copy of the last revision of the specified score and create a new score. The copy of the score will have a privacy set to `private`.\n\nWhen using a [Flat for Education](https://flat.io/edu) account, the inline and contextualized comments will be accessible in the child document.\n",
  "security": [
    {
      "OAuth2": [
        "scores"
      ]
    }
  ],
  "schema_fields": [
    "htmlUrl",
    "id",
    "privacy",
    "sharingKey",
    "title",
    "user",
    "user.firstname",
    "user.id",
    "user.isFlatTeam",
    "user.isPowerUser",
    "user.lastname",
    "user.name",
    "user.picture",
    "user.printableName",
    "user.type",
    "user.username",
    "user.classRole",
    "user.htmlUrl",
    "user.organization",
    "user.organizationRole",
    "arranger",
    "collaborators",
    "collaborators.[].aclAdmin",
    "collaborators.[].aclRead",
    "collaborators.[].aclWrite",
    "collaborators.[].isCollaborator",
    "collaborators.[].collection",
    "collaborators.[].group",
    "collaborators.[].group.creationDate",
    "collaborators.[].group.id",
    "collaborators.[].group.name",
    "collaborators.[].group.organization",
    "collaborators.[].group.readOnly",
    "collaborators.[].group.type",
    "collaborators.[].group.usersCount",
    "collaborators.[].id",
    "collaborators.[].invited",
    "collaborators.[].score",
    "collaborators.[].user",
    "collaborators.[].user.firstname"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "user"
  ],
  "tenant_cols": [
    "organization"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "OAuth2": [
          "scores"
        ]
      }
    ],
    "schemes": {
      "OAuth2": {
        "description": "OAuth 2.0 authentication for your app or. Please only request the most restrictive and needed scopes. Using some of the scopes may require an additional review from our team. The Flat API supports **authorization code** and **implicit** flows.\n",
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "https://flat.io/auth/oauth",
            "scopes": {
              "account.education_profile": "Provides access to the basic person's education profile and public organization information.\n",
              "account.email": "Provices access to the person's email.\n",
              "account.public_profile": "Provides access to the basic person's public profile. Education profiles may be anonymized with this scope, you can request the scope `education_profile` to access to the a basic education account profile.\n",
              "collections": "Full, permissive scope to access all of a user's collections.",
              "collections.add_scores": "Allow to add scores to a user's collections.",
              "collections.readonly": "Allow read-only access to a user's collections.",
              "edu.admin": "Full, permissive scope to manage all the admin of an organization.",
              "edu.admin.lti": "Access and manage the LTI Credentials for an organization.",
              "edu.admin.lti.readonly": "Read-only access to the LTI Credentials of an organization.",
              "edu.admin.users": "Access and manage the users and invitations of the organization.",
              "edu.admin.users.readonly": "Read-only access to the users and invitations of the organization.",
              "edu.assignments": "Read-write access to the assignments and submissions.",
              "edu.assignments.readonly": "Read-only access to the assignments and submissions.",
              "edu.classes": "Full, permissive scope to manage the classes.",
              "edu.classes.readonly": "Read-only access to the classes.",
              "scores": "Full, permissive scope to access all of a user's scores.\n",
              "scores.readonly": "Allows read-only access to all a user's scores. You won't need this scope to read public scores.\n",
              "scores.social": "Allow to post comments and like scores\n"
            },
            "tokenUrl": "https://api.flat.io/oauth/access_token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 34. apisguru:gitea.io:get:/repos/{owner}/{repo}/hooks/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/repos/{owner}/{repo}/hooks/{id}",
  "path_params": [
    "owner",
    "repo",
    "id"
  ],
  "query_params": [],
  "summary": "Get a hook",
  "description": "",
  "security": [
    {
      "BasicAuth": []
    },
    {
      "Token": []
    },
    {
      "AccessToken": []
    },
    {
      "AuthorizationHeaderToken": []
    },
    {
      "SudoParam": []
    },
    {
      "SudoHeader": []
    },
    {
      "TOTPHeader": []
    }
  ],
  "schema_fields": [
    "active",
    "authorization_header",
    "config",
    "created_at",
    "events",
    "id",
    "type",
    "updated_at"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "BasicAuth": []
      },
      {
        "Token": []
      },
      {
        "AccessToken": []
      },
      {
        "AuthorizationHeaderToken": []
      },
      {
        "SudoParam": []
      },
      {
        "SudoHeader": []
      },
      {
        "TOTPHeader": []
      }
    ],
    "schemes": {
      "AccessToken": {
        "in": "query",
        "name": "access_token",
        "type": "apiKey"
      },
      "AuthorizationHeaderToken": {
        "description": "API tokens must be prepended with \"token\" followed by a space.",
        "in": "header",
        "name": "Authorization",
        "type": "apiKey"
      },
      "BasicAuth": {
        "scheme": "basic",
        "type": "http"
      },
      "SudoHeader": {
        "description": "Sudo API request as the user provided as the key. Admin privileges are required.",
        "in": "header",
        "name": "Sudo",
        "type": "apiKey"
      },
      "SudoParam": {
        "description": "Sudo API request as the user provided as the key. Admin privileges are required.",
        "in": "query",
        "name": "sudo",
        "type": "apiKey"
      },
      "TOTPHeader": {
        "description": "Must be used in combination with BasicAuth if two-factor authentication is enabled.",
        "in": "header",
        "name": "X-GITEA-OTP",
        "type": "apiKey"
      },
      "Token": {
        "in": "query",
        "name": "token",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 35. apisguru:gitea.io:patch:/orgs/{org}/hooks/{id}

입력 근거 전문:

```json
{
  "method": "PATCH",
  "path": "/orgs/{org}/hooks/{id}",
  "path_params": [
    "org",
    "id"
  ],
  "query_params": [],
  "summary": "Update a hook",
  "description": "",
  "security": [
    {
      "BasicAuth": []
    },
    {
      "Token": []
    },
    {
      "AccessToken": []
    },
    {
      "AuthorizationHeaderToken": []
    },
    {
      "SudoParam": []
    },
    {
      "SudoHeader": []
    },
    {
      "TOTPHeader": []
    }
  ],
  "schema_fields": [
    "active",
    "authorization_header",
    "config",
    "created_at",
    "events",
    "id",
    "type",
    "updated_at"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "BasicAuth": []
      },
      {
        "Token": []
      },
      {
        "AccessToken": []
      },
      {
        "AuthorizationHeaderToken": []
      },
      {
        "SudoParam": []
      },
      {
        "SudoHeader": []
      },
      {
        "TOTPHeader": []
      }
    ],
    "schemes": {
      "AccessToken": {
        "in": "query",
        "name": "access_token",
        "type": "apiKey"
      },
      "AuthorizationHeaderToken": {
        "description": "API tokens must be prepended with \"token\" followed by a space.",
        "in": "header",
        "name": "Authorization",
        "type": "apiKey"
      },
      "BasicAuth": {
        "scheme": "basic",
        "type": "http"
      },
      "SudoHeader": {
        "description": "Sudo API request as the user provided as the key. Admin privileges are required.",
        "in": "header",
        "name": "Sudo",
        "type": "apiKey"
      },
      "SudoParam": {
        "description": "Sudo API request as the user provided as the key. Admin privileges are required.",
        "in": "query",
        "name": "sudo",
        "type": "apiKey"
      },
      "TOTPHeader": {
        "description": "Must be used in combination with BasicAuth if two-factor authentication is enabled.",
        "in": "header",
        "name": "X-GITEA-OTP",
        "type": "apiKey"
      },
      "Token": {
        "in": "query",
        "name": "token",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 36. apisguru:googleapis.com:put:/billinginfo/{accountId}/{billingId}

입력 근거 전문:

```json
{
  "method": "PUT",
  "path": "/billinginfo/{accountId}/{billingId}",
  "path_params": [
    "accountId",
    "billingId"
  ],
  "query_params": [],
  "summary": "",
  "description": "Updates the budget amount for the budget of the adgroup specified by the accountId and billingId, with the budget amount in the request.",
  "security": [
    {
      "Oauth2": [
        "https://www.googleapis.com/auth/adexchange.buyer"
      ],
      "Oauth2c": [
        "https://www.googleapis.com/auth/adexchange.buyer"
      ]
    }
  ],
  "schema_fields": [
    "accountId",
    "billingId",
    "budgetAmount",
    "currencyCode",
    "id",
    "kind"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "accountId"
  ],
  "tenant_cols": [
    "accountId"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "Oauth2": [
          "https://www.googleapis.com/auth/adexchange.buyer"
        ],
        "Oauth2c": [
          "https://www.googleapis.com/auth/adexchange.buyer"
        ]
      }
    ],
    "schemes": {
      "Oauth2": {
        "description": "Oauth 2.0 implicit authentication",
        "flows": {
          "implicit": {
            "authorizationUrl": "https://accounts.google.com/o/oauth2/auth",
            "scopes": {
              "https://www.googleapis.com/auth/adexchange.buyer": "Manage your Ad Exchange buyer account configuration"
            }
          }
        },
        "type": "oauth2"
      },
      "Oauth2c": {
        "description": "Oauth 2.0 authorizationCode authentication",
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "https://accounts.google.com/o/oauth2/auth",
            "scopes": {
              "https://www.googleapis.com/auth/adexchange.buyer": "Manage your Ad Exchange buyer account configuration"
            },
            "tokenUrl": "https://accounts.google.com/o/oauth2/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 37. apisguru:gsmtasks.com:patch:/accounts/{id}/

입력 근거 전문:

```json
{
  "method": "PATCH",
  "path": "/accounts/{id}/",
  "path_params": [
    "id"
  ],
  "query_params": [
    "format"
  ],
  "summary": "",
  "description": "",
  "security": [
    {
      "tokenAuth": []
    }
  ],
  "schema_fields": [
    "address",
    "address.apartment_number",
    "address.city",
    "address.country",
    "address.country_code",
    "address.formatted_address",
    "address.geocode_failed_at",
    "address.geocoded_at",
    "address.google_place_id",
    "address.house_number",
    "address.location",
    "address.location.coordinates",
    "address.location.type",
    "address.point_of_interest",
    "address.postal_code",
    "address.raw_address",
    "address.state",
    "address.street",
    "assignee_proximity_radius",
    "auto_assign_max_distance",
    "auto_assign_max_tasks",
    "auto_assign_optimize",
    "auto_assign_orders",
    "auto_assign_rotate",
    "auto_assign_time_before",
    "billing_address",
    "billing_company",
    "billing_country",
    "billing_email",
    "billing_method",
    "billing_name",
    "billing_phone",
    "billing_vatin",
    "calendar_task_template",
    "country_code",
    "custom_integration_url",
    "dashboard_task_template",
    "dashboard_worker_limit",
    "date_format",
    "distance_units"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "owner"
  ],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "tokenAuth": []
      }
    ],
    "schemes": {
      "tokenAuth": {
        "description": "Token-based authentication with required prefix \"Token\"",
        "in": "header",
        "name": "Authorization",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 38. apisguru:gsmtasks.com:post:/accounts/{id}/managers/

입력 근거 전문:

```json
{
  "method": "POST",
  "path": "/accounts/{id}/managers/",
  "path_params": [
    "id"
  ],
  "query_params": [
    "format"
  ],
  "summary": "",
  "description": "",
  "security": [
    {
      "tokenAuth": []
    }
  ],
  "schema_fields": [
    "display_name",
    "email",
    "first_name",
    "id",
    "is_on_duty",
    "last_name",
    "phone",
    "url"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "tokenAuth": []
      }
    ],
    "schemes": {
      "tokenAuth": {
        "description": "Token-based authentication with required prefix \"Token\"",
        "in": "header",
        "name": "Authorization",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 39. apisguru:hetras-certification.net:get:/api/booking/v0/bookings/{confirmationId}/reservations/{reservationNumber}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/api/booking/v0/bookings/{confirmationId}/reservations/{reservationNumber}",
  "path_params": [
    "confirmationId",
    "reservationNumber"
  ],
  "query_params": [
    "expand",
    "exclude"
  ],
  "summary": "Load a specific reservation from a booking.",
  "description": "With this request you can load one specific reservation done with one booking request.",
  "security": null,
  "schema_fields": [
    "_warnings",
    "addon_services",
    "adults",
    "arrival_date",
    "balance",
    "block",
    "block._links",
    "block.code",
    "block.name",
    "cancellation_id",
    "cancellation_policies",
    "cancellation_policies.[].description",
    "cancellation_policies.[].fee",
    "cancellation_policies.[].fee_date",
    "channel_code",
    "checkin_time",
    "checkout_time",
    "comment",
    "company",
    "company.company_id",
    "confirmation_id",
    "contact",
    "contact._links",
    "contact.customer_id",
    "created",
    "currency",
    "departure_date",
    "external_id",
    "general_policies",
    "general_policies.[].description",
    "general_policies.[].name",
    "guarantee",
    "guarantee.guarantee_type",
    "guarantee.valid_token",
    "guests",
    "guests.[]._links",
    "guests.[].customer_id",
    "guests.[].email",
    "guests.[].first_name",
    "guests.[].gender"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "customer_id"
  ],
  "tenant_cols": [
    "company",
    "company_id"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 40. apisguru:i-cue.solutions:get:/report/performance/sku-rationalization/{planningLevelId}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/report/performance/sku-rationalization/{planningLevelId}",
  "path_params": [
    "planningLevelId"
  ],
  "query_params": [],
  "summary": "SKU rationalization report",
  "description": "SKU rationalization report",
  "security": null,
  "schema_fields": [
    "[].abc12",
    "[].abc12Value",
    "[].abc6",
    "[].abc6Value",
    "[].abc9",
    "[].abc9Value",
    "[].id",
    "[].thresholdA",
    "[].thresholdB",
    "[].thresholdC",
    "[].thresholdX",
    "[].thresholdY",
    "[].thresholdZ",
    "[].xyz12",
    "[].xyz12Value",
    "[].xyz6",
    "[].xyz6Value",
    "[].xyz9",
    "[].xyz9Value"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 41. apisguru:increase.com:get:/account_transfers/{account_transfer_id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/account_transfers/{account_transfer_id}",
  "path_params": [
    "account_transfer_id"
  ],
  "query_params": [],
  "summary": "Retrieve an Account Transfer",
  "description": "",
  "security": [
    {
      "bearerAuth": []
    }
  ],
  "schema_fields": [
    "account_id",
    "amount",
    "approval",
    "approval.approved_at",
    "approval.approved_by",
    "cancellation",
    "cancellation.canceled_at",
    "cancellation.canceled_by",
    "created_at",
    "currency",
    "description",
    "destination_account_id",
    "destination_transaction_id",
    "id",
    "network",
    "status",
    "transaction_id",
    "type"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "account_id"
  ],
  "tenant_cols": [
    "account_id"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "bearerAuth": []
      }
    ],
    "schemes": {
      "bearerAuth": {
        "scheme": "bearer",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 42. apisguru:increase.com:patch:/account_numbers/{account_number_id}

입력 근거 전문:

```json
{
  "method": "PATCH",
  "path": "/account_numbers/{account_number_id}",
  "path_params": [
    "account_number_id"
  ],
  "query_params": [],
  "summary": "Update an Account Number",
  "description": "",
  "security": [
    {
      "bearerAuth": []
    }
  ],
  "schema_fields": [
    "account_id",
    "account_number",
    "created_at",
    "id",
    "name",
    "routing_number",
    "status",
    "type"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "account_id"
  ],
  "tenant_cols": [
    "account_id"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "bearerAuth": []
      }
    ],
    "schemes": {
      "bearerAuth": {
        "scheme": "bearer",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 43. apisguru:influxdata.com:patch:/authorizations/{authID}

입력 근거 전문:

```json
{
  "method": "PATCH",
  "path": "/authorizations/{authID}",
  "path_params": [
    "authID"
  ],
  "query_params": [],
  "summary": "Update an authorization to be active or inactive",
  "description": "",
  "security": null,
  "schema_fields": [
    "description",
    "status",
    "createdAt",
    "id",
    "links",
    "links.self",
    "links.user",
    "org",
    "orgID",
    "permissions",
    "permissions.[].action",
    "permissions.[].resource",
    "permissions.[].resource.id",
    "permissions.[].resource.name",
    "permissions.[].resource.org",
    "permissions.[].resource.orgID",
    "permissions.[].resource.type",
    "token",
    "updatedAt",
    "user",
    "userID"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "user",
    "userID"
  ],
  "tenant_cols": [
    "org",
    "orgID"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 44. apisguru:izettle.com:get:/organizations/{organizationUuid}/categories/v2

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/organizations/{organizationUuid}/categories/v2",
  "path_params": [
    "organizationUuid"
  ],
  "query_params": [],
  "summary": "Retrieve all categories",
  "description": "",
  "security": [
    {
      "ZettleOauth": [
        "READ:PRODUCT"
      ]
    }
  ],
  "schema_fields": [
    "categories",
    "categories.[].name",
    "categories.[].uuid"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "ZettleOauth": [
          "READ:PRODUCT"
        ]
      }
    ],
    "schemes": {
      "ZettleOauth": {
        "description": "For more information about authorization API visit: https://developer.zettle.com/docs/api/oauth/overview",
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "https://oauth.zettle.com/authorize",
            "scopes": {
              "READ:PRODUCT": "Access to read product library data",
              "WRITE:PRODUCT": "Access to write product library data"
            },
            "tokenUrl": "https://oauth.zettle.com/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 45. apisguru:izettle.com:put:/organizations/{organizationUuid}/discounts/{discountUuid}

입력 근거 전문:

```json
{
  "method": "PUT",
  "path": "/organizations/{organizationUuid}/discounts/{discountUuid}",
  "path_params": [
    "organizationUuid",
    "discountUuid"
  ],
  "query_params": [],
  "summary": "Update a single discount",
  "description": "Updates a discount entity using JSON merge patch (https://tools.ietf.org/html/rfc7386). This means that only included fields will be changed: null values removes the field on the target entity, and other values updates the field. Conditional updates are supported through the HttpHeaders.IF_MATCH header. If the conditional prerequisite is fullfilled, the discount is updated: otherwise a 412 precondition failed will be returned with an empty body.",
  "security": [
    {
      "ZettleOauth": [
        "WRITE:PRODUCT"
      ]
    }
  ],
  "schema_fields": [],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "ZettleOauth": [
          "WRITE:PRODUCT"
        ]
      }
    ],
    "schemes": {
      "ZettleOauth": {
        "description": "For more information about authorization API visit: https://developer.zettle.com/docs/api/oauth/overview",
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "https://oauth.zettle.com/authorize",
            "scopes": {
              "READ:PRODUCT": "Access to read product library data",
              "WRITE:PRODUCT": "Access to write product library data"
            },
            "tokenUrl": "https://oauth.zettle.com/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 46. apisguru:keycloak.local:put:/{realm}/authentication/flows/{id}

입력 근거 전문:

```json
{
  "method": "PUT",
  "path": "/{realm}/authentication/flows/{id}",
  "path_params": [
    "realm",
    "id"
  ],
  "query_params": [],
  "summary": "Update an authentication flow",
  "description": "",
  "security": [
    {
      "access_token": []
    }
  ],
  "schema_fields": [],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "providerId"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "access_token": []
      }
    ],
    "schemes": {
      "access_token": {
        "scheme": "bearer",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 47. apisguru:letmc.com:get:/v2/tier2/{shortName}/branch/branches/{branchID}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/v2/tier2/{shortName}/branch/branches/{branchID}",
  "path_params": [
    "shortName",
    "branchID"
  ],
  "query_params": [],
  "summary": "Get a specific branch given its unique Object ID (OID)",
  "description": "",
  "security": null,
  "schema_fields": [
    "Address1",
    "Address2",
    "Address3",
    "Address4",
    "CompanyName",
    "County",
    "EMailAddress",
    "ETag",
    "FaxPhone",
    "LandPhone",
    "Name",
    "OID",
    "Postcode",
    "WebAddress"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "CompanyName"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 48. apisguru:lyft.com:get:/rides/{id}/receipt

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/rides/{id}/receipt",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Get the receipt of the rides.",
  "description": "Get the receipt information of a processed ride by providing the ride id. Receipts will only be available to view once the payment has been processed. In the case of canceled ride, cancellation penalty is included if applicable.\n",
  "security": [
    {
      "User Authentication": [
        "rides.read"
      ]
    }
  ],
  "schema_fields": [
    "charges",
    "charges.[].amount",
    "charges.[].currency",
    "charges.[].payment_method",
    "line_items",
    "line_items.[].amount",
    "line_items.[].currency",
    "line_items.[].type",
    "price",
    "price.amount",
    "price.currency",
    "price.description",
    "requested_at",
    "ride_id",
    "ride_profile"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "User Authentication": [
          "rides.read"
        ]
      }
    ],
    "schemes": {
      "User Authentication": {
        "authorizationUrl": "https://api.lyft.com/oauth/authorize",
        "description": "OAuth 2.0 - User Credentials",
        "flow": "accessCode",
        "scopes": {
          "profile": "Access profile information about the user",
          "public": "Access public information such as ETAs and cost estimates",
          "rides.read": "Access information about the user's current and past rides",
          "rides.request": "Request a ride for the user. Cancel an existing request.\n"
        },
        "tokenUrl": "https://api.lyft.com/oauth/token",
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 49. apisguru:medium.com:get:/user/{user_id}/articles

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/user/{user_id}/articles",
  "path_params": [
    "user_id"
  ],
  "query_params": [],
  "summary": "Get User's Articles",
  "description": "Returns the list of articles (`article_ids`) written by the user.\n",
  "security": null,
  "schema_fields": [
    "associated_articles"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 50. apisguru:meshery.local:get:/api/application/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/api/application/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Handle GET request for Meshery Application with the given id",
  "description": "Fetches the list of all applications saved by the current user",
  "security": [
    {
      "token": []
    }
  ],
  "schema_fields": [
    "application_file",
    "created_at",
    "id",
    "location",
    "name",
    "updated_at",
    "user_id"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "user_id"
  ],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "token": []
      }
    ],
    "schemes": {
      "token": {
        "in": "cookie",
        "name": "token",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 51. apisguru:meteosource.com:get:/nearest_place

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/nearest_place",
  "path_params": [],
  "query_params": [
    "lat",
    "lon",
    "language",
    "key"
  ],
  "summary": "Returns the nearest named location for a given GPS coordinates.",
  "description": "## Search for nearest place by coordinates\n\nYou can use this endpoint to find the nearest place from given coordinates.\n\n*Note: If you specify coordinates of a secluded place (e.g. middle of the ocean), the nearest point can be very far from the coordinates.*",
  "security": [
    {
      "APIKeyHeader": []
    }
  ],
  "schema_fields": [
    "adm_area1",
    "adm_area2",
    "country",
    "lat",
    "lon",
    "name",
    "place_id",
    "timezone",
    "type"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "APIKeyHeader": []
      }
    ],
    "schemes": {
      "APIKeyHeader": {
        "in": "header",
        "name": "X-API-Key",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 52. apisguru:microsoft.com:post:/{projectId}/url

입력 근거 전문:

```json
{
  "method": "POST",
  "path": "/{projectId}/url",
  "path_params": [
    "projectId"
  ],
  "query_params": [
    "iterationId",
    "application"
  ],
  "summary": "Predict an image url and saves the result",
  "description": "",
  "security": null,
  "schema_fields": [
    "Created",
    "Id",
    "Iteration",
    "Predictions",
    "Predictions.[].Probability",
    "Predictions.[].Tag",
    "Predictions.[].TagId",
    "Project"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "Project"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 53. apisguru:n-auth.com:get:/servers/{serverid}/users/{userid}/accounts

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/servers/{serverid}/users/{userid}/accounts",
  "path_params": [
    "serverid",
    "userid"
  ],
  "query_params": [
    "limit",
    "marker",
    "sort"
  ],
  "summary": "Get all accounts of a specific user",
  "description": "Returns an array containing all accounts corresponding to this user. Required permission: 'sessions' or 'users'.",
  "security": [
    {
      "api_key": []
    },
    {
      "api_key": [],
      "role_id": []
    }
  ],
  "schema_fields": [
    "accounts",
    "accounts.[].blocked",
    "accounts.[].clientVersion",
    "accounts.[].created",
    "accounts.[].description",
    "accounts.[].id",
    "accounts.[].lastlogin",
    "accounts.[].lastprovoke",
    "accounts.[].userid",
    "totalnumber"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "api_key": []
      },
      {
        "api_key": [],
        "role_id": []
      }
    ],
    "schemes": {
      "api_key": {
        "description": "API Key for a specific (virtual) server.",
        "in": "header",
        "name": "X-apikey",
        "type": "apiKey"
      },
      "role_id": {
        "description": "ID of the role you want to impersonate (requires that the role associated with the API key passed in the header above has global 'root' or global 'setrid' permissions).",
        "in": "header",
        "name": "X-su",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 54. apisguru:naviplancentral.com:post:/api/Accounts/{accountId}/Holdings

입력 근거 전문:

```json
{
  "method": "POST",
  "path": "/api/Accounts/{accountId}/Holdings",
  "path_params": [
    "accountId"
  ],
  "query_params": [],
  "summary": "",
  "description": "Creates a holding and adds it to an existing Account.",
  "security": null,
  "schema_fields": [
    "accountHoldingId",
    "accountId",
    "costBasis",
    "cusip",
    "description",
    "externalDestinationId",
    "links",
    "links.[].href",
    "links.[].rel",
    "marketValue",
    "symbol",
    "valuationDate"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "accountId"
  ],
  "tenant_cols": [
    "accountId"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 55. apisguru:netbox.dev:get:/circuits/provider-networks/{id}/

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/circuits/provider-networks/{id}/",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "",
  "description": "",
  "security": [
    {
      "Bearer": []
    }
  ],
  "schema_fields": [
    "comments",
    "created",
    "custom_fields",
    "description",
    "display",
    "id",
    "last_updated",
    "name",
    "provider",
    "provider.circuit_count",
    "provider.display",
    "provider.id",
    "provider.name",
    "provider.slug",
    "provider.url",
    "service_id",
    "tags",
    "tags.[].color",
    "tags.[].display",
    "tags.[].id",
    "tags.[].name",
    "tags.[].slug",
    "tags.[].url",
    "url"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "provider"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "Bearer": []
      }
    ],
    "schemes": {
      "Bearer": {
        "in": "header",
        "name": "Authorization",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 56. apisguru:netboxdemo.com:put:/circuits/providers/{id}/

입력 근거 전문:

```json
{
  "method": "PUT",
  "path": "/circuits/providers/{id}/",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "",
  "description": "",
  "security": [
    {
      "Bearer": []
    }
  ],
  "schema_fields": [
    "account",
    "admin_contact",
    "asn",
    "comments",
    "created",
    "custom_fields",
    "id",
    "last_updated",
    "name",
    "noc_contact",
    "portal_url",
    "slug",
    "tags"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "account"
  ],
  "tenant_cols": [
    "account"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "Bearer": []
      }
    ],
    "schemes": {
      "Bearer": {
        "in": "header",
        "name": "Authorization",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 57. apisguru:nordigen.com:get:/api/v2/institutions/{id}/

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/api/v2/institutions/{id}/",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "",
  "description": "Get details about a specific Institution",
  "security": [
    {
      "jwtAuth": []
    }
  ],
  "schema_fields": [
    "bic",
    "countries",
    "id",
    "logo",
    "name",
    "supported_features",
    "supported_payments",
    "transaction_total_days"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "jwtAuth": []
      }
    ],
    "schemes": {
      "jwtAuth": {
        "bearerFormat": "JWT",
        "scheme": "bearer",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 58. apisguru:nordigen.com:post:/api/v2/payments/{id}/submit/

입력 근거 전문:

```json
{
  "method": "POST",
  "path": "/api/v2/payments/{id}/submit/",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "",
  "description": "Initiate the payment on bank's side.\n\nComplete the payment and return payment details as a response.",
  "security": [
    {
      "jwtAuth": []
    }
  ],
  "schema_fields": [
    "creditor_account",
    "creditor_object",
    "creditor_object.account",
    "creditor_object.address_country",
    "creditor_object.address_street",
    "creditor_object.agent",
    "creditor_object.agent_name",
    "creditor_object.currency",
    "creditor_object.id",
    "creditor_object.institution_id",
    "creditor_object.name",
    "creditor_object.post_code",
    "creditor_object.type",
    "custom_payment_id",
    "debtor_account",
    "debtor_account.account",
    "debtor_account.address_country",
    "debtor_account.address_street",
    "debtor_account.currency",
    "debtor_account.name",
    "debtor_account.post_code",
    "debtor_account.type",
    "debtor_account.type_number",
    "description",
    "instructed_amount",
    "instructed_amount.amount",
    "instructed_amount.currency",
    "payment_id",
    "payment_product",
    "payment_status",
    "payment_type",
    "redirect"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "account"
  ],
  "tenant_cols": [
    "account"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "jwtAuth": []
      }
    ],
    "schemes": {
      "jwtAuth": {
        "bearerFormat": "JWT",
        "scheme": "bearer",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 59. apisguru:onsched.com:get:/consumer/v1/appointments/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/consumer/v1/appointments/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Get Appointment",
  "description": "<p>Use this endpoint to return an <b>Appointment</b> object. A valid <b>appointment id</b> is required. For more information: <a href=\"https://onsched.readme.io/docs/appointments-overview\">Appointments Overview</a></p>",
  "security": [
    {
      "oauth2": [
        "OnSchedApi"
      ]
    }
  ],
  "schema_fields": [
    "auditTrail",
    "auditTrail.[].appointmentId",
    "auditTrail.[].id",
    "auditTrail.[].modificationType",
    "auditTrail.[].modifiedBy",
    "auditTrail.[].modifiedOn",
    "auditTrail.[].notesAfter",
    "auditTrail.[].notesBefore",
    "auditTrail.[].statusAfter",
    "auditTrail.[].statusBefore",
    "bookedBy",
    "businessName",
    "calendarId",
    "confirmationNumber",
    "confirmed",
    "createDate",
    "customFields",
    "customerId",
    "customerMessage",
    "customers",
    "customers.[].appointmentId",
    "customers.[].customerId",
    "date",
    "dateInternational",
    "downloadIcsUrl",
    "duration",
    "email",
    "emailConfirmationSent",
    "emailReminderSent",
    "endDateTime",
    "firstname",
    "groupSize",
    "id",
    "ipAddress",
    "lastModifiedBy",
    "lastModifiedOn",
    "lastname",
    "latitude",
    "location",
    "locationId"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "customerId"
  ],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "oauth2": [
          "OnSchedApi"
        ]
      }
    ],
    "schemes": {
      "oauth2": {
        "flows": {
          "clientCredentials": {
            "scopes": {
              "OnSchedApi": "Consumer and Setup Interface",
              "distance": "Travel and Distance calculations"
            },
            "tokenUrl": "https://sandbox-identity.onsched.com/connect/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 60. apisguru:onsched.com:put:/consumer/v1/appointments/{id}/cancel

입력 근거 전문:

```json
{
  "method": "PUT",
  "path": "/consumer/v1/appointments/{id}/cancel",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Cancel Appointment",
  "description": "<p>Use this endpoint to <b>Cancel</b> an appointment booking or reservation. Only appointments with a \"BK\", booked or \"RS\", reserved status can be cancelled. Past dated appointments cannot be cancelled. A valid <b>appointment id</b> is required. For more information: <a href=\"https://onsched.readme.io/docs/appointments-overview\">Appointment Overview</a></p>",
  "security": [
    {
      "oauth2": [
        "OnSchedApi"
      ]
    }
  ],
  "schema_fields": [
    "auditTrail",
    "auditTrail.[].appointmentId",
    "auditTrail.[].id",
    "auditTrail.[].modificationType",
    "auditTrail.[].modifiedBy",
    "auditTrail.[].modifiedOn",
    "auditTrail.[].notesAfter",
    "auditTrail.[].notesBefore",
    "auditTrail.[].statusAfter",
    "auditTrail.[].statusBefore",
    "bookedBy",
    "businessName",
    "calendarId",
    "confirmationNumber",
    "confirmed",
    "createDate",
    "customFields",
    "customerId",
    "customerMessage",
    "customers",
    "customers.[].appointmentId",
    "customers.[].customerId",
    "date",
    "dateInternational",
    "downloadIcsUrl",
    "duration",
    "email",
    "emailConfirmationSent",
    "emailReminderSent",
    "endDateTime",
    "firstname",
    "groupSize",
    "id",
    "ipAddress",
    "lastModifiedBy",
    "lastModifiedOn",
    "lastname",
    "latitude",
    "location",
    "locationId"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "customerId"
  ],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "oauth2": [
          "OnSchedApi"
        ]
      }
    ],
    "schemes": {
      "oauth2": {
        "flows": {
          "clientCredentials": {
            "scopes": {
              "OnSchedApi": "Consumer and Setup Interface",
              "distance": "Travel and Distance calculations"
            },
            "tokenUrl": "https://sandbox-identity.onsched.com/connect/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 61. apisguru:openchannel.io:patch:/apps/{appId}/versions/{version}

입력 근거 전문:

```json
{
  "method": "PATCH",
  "path": "/apps/{appId}/versions/{version}",
  "path_params": [
    "appId",
    "version"
  ],
  "query_params": [
    "developerId",
    "name",
    "type",
    "model",
    "customData",
    "attributes",
    "restrict",
    "allow",
    "access",
    "approvalRequired"
  ],
  "summary": "Updates the app fields or creates a new version",
  "description": "- This method is called on behalf of a developer.\n- Price and is required if the model is 'single' or 'recurring'\n- Returns the newly updated app\n- This endpoint updates only the fields provided in the request (relative update). In contrast, the POST version of this method replaces the entire object to match the request (absolute update). \n",
  "security": [
    {
      "basicAuth": []
    }
  ],
  "schema_fields": [],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "basicAuth": []
      }
    ],
    "schemes": {
      "basicAuth": {
        "scheme": "basic",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 62. apisguru:openfintech.io:get:/exchangers/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/exchangers/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Exchanger by ID",
  "description": "Returns exchanger with specific ID.\n",
  "security": null,
  "schema_fields": [
    "data",
    "data.attributes",
    "data.attributes.name",
    "data.attributes.rates_export_standard",
    "data.attributes.rates_export_url",
    "data.attributes.status",
    "data.attributes.wmid",
    "data.id",
    "data.links",
    "data.links.self",
    "data.relationships",
    "data.relationships.organization",
    "data.relationships.organization.data",
    "data.relationships.organization.data.id",
    "data.relationships.organization.data.type",
    "data.relationships.organization.links",
    "data.relationships.organization.links.related",
    "data.type"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "organization"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 63. apisguru:orbit.love:put:/{workspace_slug}/members/{member_slug}/activities/{id}

입력 근거 전문:

```json
{
  "method": "PUT",
  "path": "/{workspace_slug}/members/{member_slug}/activities/{id}",
  "path_params": [
    "workspace_slug",
    "member_slug",
    "id"
  ],
  "query_params": [],
  "summary": "Update a custom activity for a member",
  "description": "",
  "security": [
    {
      "bearer": []
    }
  ],
  "schema_fields": [],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "bearer": []
      }
    ],
    "schemes": {
      "bearer": {
        "description": "Provide a Authorization header with format 'Bearer <api_key>'. This is the recommended approach. Make sure to include the 'Bearer' part in the text box here.",
        "scheme": "bearer",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 64. apisguru:osf.io:get:/files/{file_id}/

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/files/{file_id}/",
  "path_params": [
    "file_id"
  ],
  "query_params": [],
  "summary": "Retrieve a file",
  "description": "Retrieves the details of a file (or folder)\n#### Returns\nReturns a JSON object with a `data` key containing the representation of the requested file, if the request was successful.\n\nIf the request is unsuccessful, an `errors` key containing information about the failure will be returned. Refer to the [list of error codes](#tag/Errors-and-Error-Codes) to understand why this request may have failed.\n### Waterbutler API actions\n\nFiles can be modified through the Waterbutler API routes found in `links` (`new_folder`, `move`, `upload`, `download`, and `delete`).\n\n#### Download (files)\n\nTo download a file, issue a GET request against the download link. The response will have the Content-Disposition header set, which will will trigger a download in a browser.\n\n#### Create Subfolder (folders)\n\nYou can create a subfolder of an existing folder by issuing a PUT request against the new_folder link. The ?kind=folder portion of the query parameter is already included in the new_folder link. The name of the new subfolder should be provided in the name query parameter. The response will contain a WaterButler folder entity. If a folder with that name already exists in the parent directory, the server will return a 409 Conflict error response.\n\n#### Upload New File (folders)\n\n\n  To upload a file to a folder, issue a PUT request to the folder's upload link with the raw file data in the request body, and the kind and name query parameters set to 'file' and the desired name of the file. The response will contain a WaterButler file entity that describes the new file. If a file with the same name already exists in the folder, the server will return a 409 Conflict error response.\n\n\n#### Update Existing File (file)\n\nTo update an existing file, issue a PUT request to the file's upload link with the raw file data in the request body and the kind query parameter set to \"file\". The update action will create a new version of the file. The response will contain a WaterButler file entity that describes the updated file.\n\n#### Rename (files, folders)\n\nTo rename a file or folder, issue a POST request to the move link with the action body parameter set to \"rename\" and the rename body parameter set to the desired name. The response will contain either a folder entity or file entity with the new name.\n\n#### Move & Copy (files, folders)\n\nMove and copy actions both use the same request structure, a POST to the move url, but with different values for the action body parameters. The path parameter is also required and should be the OSF path attribute of the folder being written to. The rename and conflict parameters are optional. If you wish to change the name of the file or folder at its destination, set the rename parameter to the new name. The conflict param governs how name clashes are resolved. Possible values are replace and keep. replace is the default and will overwrite the file that already exists in the target folder. keep will attempt to keep both by adding a suffix to the new file's name until it no longer conflicts. The suffix will be ' (x)' where x is a increasing integer starting from 1. This behavior is intended to mimic that of the OS X Finder. The response will contain either a folder entity or file entity with the new name.\nFiles and folders can also be moved between nodes and providers. The resource parameter is the id of the node under which the file/folder should be moved. It must agree with the path parameter, that is the path must identify a valid folder under the node identified by resource. Likewise, the provider parameter may be used to move the file/folder to another storage provider, but both the resource and path parameters must belong to a node and folder already extant on that provider. Both resource and provider default to the current node and providers.\nIf a moved/copied file is overwriting an existing file, a 200 OK response will be returned. Otherwise, a 201 Created will be returned.\n\n#### Delete (file, folders)\n\nTo delete a file or folder send a DELETE request to the delete link. Nothing will be returned in the response body.",
  "security": null,
  "schema_fields": [
    "[].attributes",
    "[].attributes.checkout",
    "[].attributes.current_user_can_comment",
    "[].attributes.current_version",
    "[].attributes.date_created",
    "[].attributes.date_modified",
    "[].attributes.delete_allowed",
    "[].attributes.extra",
    "[].attributes.guid",
    "[].attributes.kind",
    "[].attributes.last_touched",
    "[].attributes.materialized_path",
    "[].attributes.name",
    "[].attributes.path",
    "[].attributes.provider",
    "[].attributes.size",
    "[].attributes.tags",
    "[].id",
    "[].links",
    "[].links.delete",
    "[].links.download",
    "[].links.info",
    "[].links.move",
    "[].links.new_folder",
    "[].links.self",
    "[].links.upload",
    "[].relationships",
    "[].relationships.checkout",
    "[].relationships.comments",
    "[].relationships.node",
    "[].relationships.versions",
    "[].type"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "provider"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 65. apisguru:osf.io:get:/institutions/{institution_id}/users/

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/institutions/{institution_id}/users/",
  "path_params": [
    "institution_id"
  ],
  "query_params": [],
  "summary": "List all affiliated users",
  "description": "A paginated list of all users affiliated with an institution.\n#### Returns\nReturns a JSON object containing `data` and `links` keys.\n\nThe `data` key contains an array of 10 users. Each resource in the array is a separate users object.\n\nThe `links` key contains a dictionary of links that can be used for [pagination](#tag/Pagination).\n\nIf the request is unsuccessful, an `errors` key containing information about the failure will be returned. Refer to the [list of error codes](#tag/Errors-and-Error-Codes) to understand why this request may have failed.\n#### Filtering\nYou can optionally request that the response only include users that match your filters by utilizing the `filter` query parameter, e.g. https://api.osf.io/v2/institutions/cos/users?filter[family_name]=Nosek.\n\nUsers may be filtered by their `id`, `full_name`, `given_name`, `middle_names`, and `family_name`",
  "security": null,
  "schema_fields": [
    "[].attributes",
    "[].attributes.active",
    "[].attributes.date_registered",
    "[].attributes.family_name",
    "[].attributes.full_name",
    "[].attributes.given_name",
    "[].attributes.locale",
    "[].attributes.middle_names",
    "[].attributes.suffix",
    "[].attributes.timezone",
    "[].id",
    "[].links",
    "[].links.html",
    "[].links.profile_image",
    "[].relationships",
    "[].relationships.institutions",
    "[].relationships.nodes",
    "[].type"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 66. apisguru:osf.io:post:/draft_registrations/{draft_id}/contributors/

입력 근거 전문:

```json
{
  "method": "POST",
  "path": "/draft_registrations/{draft_id}/contributors/",
  "path_params": [
    "draft_id"
  ],
  "query_params": [],
  "summary": "Add a contributor to a Draft Registration",
  "description": "Adds a contributor to a Draft Registration, contributors can view, edit, register or delete a Draft Registration depending on their permissions.\nContributors are categorized as either \"bibliographic\" or \"non-bibliographic\" contributors. From a permissions standpoint, both are the same, but bibliographic contributors are included in citations and are listed on the project overview page on the OSF, while non-bibliographic contributors are not.\n#### Permissions\nOnly project administrators can add contributors to a Draft Registration.\n#### Required\nA relationship object with a `data` key, containing the `users` type and valid user ID is required.\nAll attributes describing the relationship between the node and the user are optional.\n#### Returns\nReturns a JSON object with a `data` key containing the representation of the new contributor, if the request is successful.\nIf the request is unsuccessful, an `errors` key containing information about the failure will be returned. Refer to the [list of error codes](#tag/Errors-and-Error-Codes) to understand why this request may have failed.",
  "security": null,
  "schema_fields": [],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "user"
  ],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 67. apisguru:patientview.org:get:/user/{userId}/availableobservationheadings

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/user/{userId}/availableobservationheadings",
  "path_params": [
    "userId"
  ],
  "query_params": [],
  "summary": "Get Available Observations Types For a User",
  "description": "Given a User ID retrieve a list of available observation types for that user (where they have observation data).",
  "security": null,
  "schema_fields": [
    "[].code",
    "[].created",
    "[].decimalPlaces",
    "[].defaultPanel",
    "[].defaultPanelOrder",
    "[].heading",
    "[].id",
    "[].infoLink",
    "[].lastUpdate",
    "[].maxGraph",
    "[].minGraph",
    "[].name",
    "[].normalRange",
    "[].observationHeadingGroups",
    "[].observationHeadingGroups.[].created",
    "[].observationHeadingGroups.[].group",
    "[].observationHeadingGroups.[].group.address1",
    "[].observationHeadingGroups.[].group.address2",
    "[].observationHeadingGroups.[].group.address3",
    "[].observationHeadingGroups.[].group.childGroups",
    "[].observationHeadingGroups.[].group.code",
    "[].observationHeadingGroups.[].group.contactPoints",
    "[].observationHeadingGroups.[].group.contactPoints.[].contactPointType",
    "[].observationHeadingGroups.[].group.contactPoints.[].contactPointType.description",
    "[].observationHeadingGroups.[].group.contactPoints.[].contactPointType.id",
    "[].observationHeadingGroups.[].group.contactPoints.[].contactPointType.lookupType",
    "[].observationHeadingGroups.[].group.contactPoints.[].contactPointType.lookupType.created",
    "[].observationHeadingGroups.[].group.contactPoints.[].contactPointType.lookupType.description",
    "[].observationHeadingGroups.[].group.contactPoints.[].contactPointType.lookupType.id",
    "[].observationHeadingGroups.[].group.contactPoints.[].contactPointType.lookupType.lastUpdate",
    "[].observationHeadingGroups.[].group.contactPoints.[].contactPointType.lookupType.type",
    "[].observationHeadingGroups.[].group.contactPoints.[].contactPointType.value",
    "[].observationHeadingGroups.[].group.contactPoints.[].content",
    "[].observationHeadingGroups.[].group.contactPoints.[].created",
    "[].observationHeadingGroups.[].group.contactPoints.[].id",
    "[].observationHeadingGroups.[].group.contactPoints.[].lastUpdate",
    "[].observationHeadingGroups.[].group.created",
    "[].observationHeadingGroups.[].group.fhirResourceId",
    "[].observationHeadingGroups.[].group.groupFeatures",
    "[].observationHeadingGroups.[].group.groupFeatures.[].created"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 68. apisguru:payrun.io:put:/Employer/{EmployerId}/CisLineType/{CisLineTypeId}/Tag/{TagId}

입력 근거 전문:

```json
{
  "method": "PUT",
  "path": "/Employer/{EmployerId}/CisLineType/{CisLineTypeId}/Tag/{TagId}",
  "path_params": [
    "EmployerId",
    "CisLineTypeId",
    "TagId"
  ],
  "query_params": [],
  "summary": "Insert CIS line type tag",
  "description": "Inserts a new tag on the CIS line type",
  "security": null,
  "schema_fields": [
    "Tag",
    "Tag.Created",
    "Tag.TaggedItem",
    "Tag.TaggedItem.@href",
    "Tag.TaggedItem.@rel",
    "Tag.TaggedItem.@title",
    "Tag.Text"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 69. apisguru:pocketsmith.com:get:/accounts/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/accounts/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Get account",
  "description": "Gets an account by its ID.",
  "security": [
    {
      "developerKey": []
    }
  ],
  "schema_fields": [
    "created_at",
    "currency_code",
    "current_balance",
    "current_balance_date",
    "current_balance_exchange_rate",
    "current_balance_in_base_currency",
    "id",
    "is_net_worth",
    "primary_scenario",
    "primary_scenario.achieve_date",
    "primary_scenario.closing_balance",
    "primary_scenario.closing_balance_date",
    "primary_scenario.created_at",
    "primary_scenario.current_balance",
    "primary_scenario.current_balance_date",
    "primary_scenario.current_balance_exchange_rate",
    "primary_scenario.current_balance_in_base_currency",
    "primary_scenario.description",
    "primary_scenario.id",
    "primary_scenario.interest_rate",
    "primary_scenario.interest_rate_repeat_id",
    "primary_scenario.maximum-value",
    "primary_scenario.minimum-value",
    "primary_scenario.safe_balance",
    "primary_scenario.safe_balance_in_base_currency",
    "primary_scenario.starting_balance",
    "primary_scenario.starting_balance_date",
    "primary_scenario.title",
    "primary_scenario.type",
    "primary_scenario.updated_at",
    "primary_transaction_account",
    "primary_transaction_account.created_at",
    "primary_transaction_account.currency_code",
    "primary_transaction_account.current_balance",
    "primary_transaction_account.current_balance_date",
    "primary_transaction_account.current_balance_exchange_rate",
    "primary_transaction_account.current_balance_in_base_currency",
    "primary_transaction_account.id",
    "primary_transaction_account.institution",
    "primary_transaction_account.institution.created_at"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "developerKey": []
      }
    ],
    "schemes": {
      "developerKey": {
        "description": "If you want to build a tool just for yourself, be it a desktop widget to display your balances or a tool to import transactions from a bank without a bank feed, you can use our developer keys feature. You can issue yourself a key which will give you persistent API access to just your account. You should rotate your keys regularly.",
        "in": "header",
        "name": "X-Developer-Key",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 70. apisguru:probely.com:get:/events/{id}/

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/events/{id}/",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Retrieve account event",
  "description": "",
  "security": [
    {
      "jwtAuth": []
    }
  ],
  "schema_fields": [
    "content",
    "content.changed",
    "content.changed_by",
    "content.changed_by.email",
    "content.changed_by.id",
    "content.changed_by.name",
    "content.email",
    "content.id",
    "content.is_active",
    "content.is_admin",
    "content.is_billing_admin",
    "content.name",
    "content.title",
    "content.allowed_scan_profiles",
    "content.allowed_scan_profiles.[].id",
    "content.allowed_scan_profiles.[].name",
    "content.assets",
    "content.assets.[].changed",
    "content.assets.[].changed_by",
    "content.assets.[].changed_by.email",
    "content.assets.[].changed_by.id",
    "content.assets.[].changed_by.name",
    "content.assets.[].cookies",
    "content.assets.[].cookies.[].name",
    "content.assets.[].cookies.[].value",
    "content.assets.[].desc",
    "content.assets.[].headers",
    "content.assets.[].headers.[].name",
    "content.assets.[].headers.[].value",
    "content.assets.[].host",
    "content.assets.[].id",
    "content.assets.[].include",
    "content.assets.[].name",
    "content.assets.[].stack",
    "content.assets.[].verification_date",
    "content.assets.[].verification_last_error",
    "content.assets.[].verification_method",
    "content.assets.[].verification_token",
    "content.assets.[].verified",
    "content.connected_target"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "created_by",
    "assignee",
    "reporter"
  ],
  "tenant_cols": [
    "site"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "jwtAuth": []
      }
    ],
    "schemes": {
      "jwtAuth": {
        "bearerFormat": "JWT",
        "scheme": "bearer",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 71. apisguru:probely.com:get:/integrations/jira-cloud/projects/{project_id}/issue_types/{issue_type_id}/status/

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/integrations/jira-cloud/projects/{project_id}/issue_types/{issue_type_id}/status/",
  "path_params": [
    "project_id",
    "issue_type_id"
  ],
  "query_params": [],
  "summary": "Retrieve issue statuses",
  "description": "",
  "security": [
    {
      "jwtAuth": []
    }
  ],
  "schema_fields": [
    "[].id",
    "[].name"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "jwtAuth": []
      }
    ],
    "schemes": {
      "jwtAuth": {
        "bearerFormat": "JWT",
        "scheme": "bearer",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 72. apisguru:probely.com:patch:/targets/{id}/

입력 근거 전문:

```json
{
  "method": "PATCH",
  "path": "/targets/{id}/",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Partial update target",
  "description": "",
  "security": [
    {
      "jwtAuth": []
    }
  ],
  "schema_fields": [
    "allowed_scan_profiles",
    "allowed_scan_profiles.[].id",
    "allowed_scan_profiles.[].name",
    "assets",
    "assets.[].changed",
    "assets.[].changed_by",
    "assets.[].changed_by.email",
    "assets.[].changed_by.id",
    "assets.[].changed_by.name",
    "assets.[].cookies",
    "assets.[].cookies.[].name",
    "assets.[].cookies.[].value",
    "assets.[].desc",
    "assets.[].headers",
    "assets.[].headers.[].name",
    "assets.[].headers.[].value",
    "assets.[].host",
    "assets.[].id",
    "assets.[].include",
    "assets.[].name",
    "assets.[].stack",
    "assets.[].verification_date",
    "assets.[].verification_last_error",
    "assets.[].verification_method",
    "assets.[].verification_token",
    "assets.[].verified",
    "changed",
    "changed_by",
    "changed_by.email",
    "changed_by.id",
    "changed_by.name",
    "connected_target",
    "enabled",
    "environment",
    "id",
    "labels",
    "name",
    "report_type",
    "scan_profile",
    "site"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "username"
  ],
  "tenant_cols": [
    "site"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "jwtAuth": []
      }
    ],
    "schemes": {
      "jwtAuth": {
        "bearerFormat": "JWT",
        "scheme": "bearer",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 73. apisguru:prss.org:get:/api/v2/episodes

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/api/v2/episodes",
  "path_params": [],
  "query_params": [
    "id",
    "beginAirDateAfter",
    "endAirDateBefore",
    "programId",
    "pageStart",
    "pageSize",
    "orderById"
  ],
  "summary": "Gets episodes matching the given criteria.",
  "description": "",
  "security": [
    {
      "cd_oauth2": [
        "cd:full"
      ]
    }
  ],
  "schema_fields": [
    "[].beginAirDate",
    "[].beginTransmissionDate",
    "[].createdDate",
    "[].customerId",
    "[].endAirDate",
    "[].endTransmissionDate",
    "[].id",
    "[].lastModifiedDate",
    "[].programId",
    "[].title"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "customerId"
  ],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "cd_oauth2": [
          "cd:full"
        ]
      }
    ],
    "schemes": {
      "cd_oauth2": {
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "/api/oauth2/authorize",
            "scopes": {
              "cd:full": "Full access to the ContentDepot account"
            },
            "tokenUrl": "/api/oauth2/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 74. apisguru:rebilly.com:get:/attachments/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/attachments/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Retrieve an Attachment",
  "description": "Retrieve a Attachment with specified identifier string.\n",
  "security": [
    {
      "SecretApiKey": []
    },
    {
      "JWT": []
    }
  ],
  "schema_fields": [
    "_embedded",
    "_embedded.[].file",
    "_embedded.[].file._links",
    "_embedded.[].file._links.[].rel",
    "_embedded.[].file._links.[].href",
    "_embedded.[].file.createdTime",
    "_embedded.[].file.description",
    "_embedded.[].file.extension",
    "_embedded.[].file.height",
    "_embedded.[].file.id",
    "_embedded.[].file.isPublic",
    "_embedded.[].file.mime",
    "_embedded.[].file.name",
    "_embedded.[].file.sha1",
    "_embedded.[].file.size",
    "_embedded.[].file.tags",
    "_embedded.[].file.updatedTime",
    "_embedded.[].file.width",
    "_links",
    "_links.[].rel",
    "_links.[].href",
    "createdTime",
    "description",
    "fileId",
    "id",
    "name",
    "relatedId",
    "relatedType",
    "updatedTime"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "SecretApiKey": []
      },
      {
        "JWT": []
      }
    ],
    "schemes": {
      "JWT": {
        "bearerFormat": "JWT",
        "description": "You can create a JSON Web Token (JWT) via our [JWT Session resource](https://user-api-docs.rebilly.com/#operation/PostSigninRequest).\nUsage format: `Bearer &lt;JWT&gt;`.\n",
        "scheme": "bearer",
        "type": "http"
      },
      "SecretApiKey": {
        "description": "When you sign up for an account, you are given your first secret API key.\nTo do so please [follow this link.](https://app.rebilly.com/signup)\nAlso you can generate additional API keys, and delete API keys (as you may\nneed to rotate your keys in the future). All API keys can be restricted to a\nsmall set of permissions (restricted API keys).\n",
        "in": "header",
        "name": "REB-APIKEY",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 75. apisguru:rebilly.com:get:/bank-accounts/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/bank-accounts/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Retrieve a Bank Account",
  "description": "Retrieve a Bank Account with specified identifier string.\n",
  "security": [
    {
      "SecretApiKey": []
    },
    {
      "JWT": []
    }
  ],
  "schema_fields": [
    "accountNumberType",
    "accountType",
    "bankName",
    "bic",
    "billingAddress",
    "billingAddress.address",
    "billingAddress.address2",
    "billingAddress.city",
    "billingAddress.country",
    "billingAddress.emails",
    "billingAddress.emails.[].label",
    "billingAddress.emails.[].primary",
    "billingAddress.emails.[].value",
    "billingAddress.firstName",
    "billingAddress.hash",
    "billingAddress.lastName",
    "billingAddress.organization",
    "billingAddress.phoneNumbers",
    "billingAddress.phoneNumbers.[].label",
    "billingAddress.phoneNumbers.[].primary",
    "billingAddress.phoneNumbers.[].value",
    "billingAddress.postalCode",
    "billingAddress.region",
    "createdTime",
    "customFields",
    "customerId",
    "fingerprint",
    "id",
    "last4",
    "method",
    "riskMetadata",
    "riskMetadata.accuracyRadius",
    "riskMetadata.browserData",
    "riskMetadata.browserData.colorDepth",
    "riskMetadata.browserData.isJavaEnabled",
    "riskMetadata.browserData.language",
    "riskMetadata.browserData.screenHeight",
    "riskMetadata.browserData.screenWidth",
    "riskMetadata.browserData.timeZoneOffset",
    "riskMetadata.city"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "customerId"
  ],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "SecretApiKey": []
      },
      {
        "JWT": []
      }
    ],
    "schemes": {
      "JWT": {
        "bearerFormat": "JWT",
        "description": "You can create a JSON Web Token (JWT) via our [JWT Session resource](https://user-api-docs.rebilly.com/#operation/PostSigninRequest).\nUsage format: `Bearer &lt;JWT&gt;`.\n",
        "scheme": "bearer",
        "type": "http"
      },
      "SecretApiKey": {
        "description": "When you sign up for an account, you are given your first secret API key.\nTo do so please [follow this link.](https://app.rebilly.com/signup)\nAlso you can generate additional API keys, and delete API keys (as you may\nneed to rotate your keys in the future). All API keys can be restricted to a\nsmall set of permissions (restricted API keys).\n",
        "in": "header",
        "name": "REB-APIKEY",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 76. apisguru:reverb.com:post:/my/orders/selling/{id}/ship

입력 근거 전문:

```json
{
  "method": "POST",
  "path": "/my/orders/selling/{id}/ship",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Marks an order as shipped",
  "description": "Marks an order as shipped",
  "security": [
    {
      "oauth2": [
        "write_orders"
      ]
    }
  ],
  "schema_fields": [],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "provider"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "oauth2": [
          "write_orders"
        ]
      }
    ],
    "schemes": {
      "oauth2": {
        "flows": {
          "clientCredentials": {
            "scopes": {
              "public": "",
              "read_feedback": "*Originally missing*",
              "read_listings": "*Originally missing*",
              "read_lists": "*Originally missing*",
              "read_messages": "*Originally missing*",
              "read_offers": "*Originally missing*",
              "read_orders": "*Originally missing*",
              "read_payouts": "*Originally missing*",
              "read_profile": "*Originally missing*",
              "write_feedback": "*Originally missing*",
              "write_listings": "*Originally missing*",
              "write_listings_for_others": "*Originally missing*",
              "write_lists": "*Originally missing*",
              "write_messages": "*Originally missing*",
              "write_offers": "*Originally missing*",
              "write_orders": "*Originally missing*",
              "write_profile": "*Originally missing*",
              "write_reviews": "*Originally missing*"
            },
            "tokenUrl": "https://reverb.com/oauth/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 77. apisguru:runscope.com:get:/teams/{teamId}/integrations

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/teams/{teamId}/integrations",
  "path_params": [
    "teamId"
  ],
  "query_params": [],
  "summary": "Team integrations list",
  "description": "Returns a list of integrations configured for the team.",
  "security": [
    {
      "runscope_auth": [
        "api:read",
        "team:read"
      ]
    }
  ],
  "schema_fields": [
    "data",
    "data.[].description",
    "data.[].id",
    "data.[].type",
    "data.[].uuid",
    "meta",
    "meta.status"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "runscope_auth": [
          "api:read",
          "team:read"
        ]
      }
    ],
    "schemes": {
      "runscope_auth": {
        "authorizationUrl": "https://www.runscope.com/signin/oauth/authorize",
        "flow": "accessCode",
        "scopes": {
          "account:email": "Allows you to read the email addresses of user accounts.",
          "api:read": "Default read access.",
          "bucket:auth_token": "Allows you to read all bucket information, including Authenticated Buckets.",
          "bucket:write": "Allows you to create new buckets on behalf of the user (up to their plan limit).",
          "message:write": "Allows you to create new messages on behalf of the user (up to their plan limit).",
          "team:read": "Allows you to read team details such as lists of team members and external service integrations.",
          "test:read": "Allows you to read the details of API tests.",
          "test:write": "Allows you to create, update and delete details of API tests."
        },
        "tokenUrl": "https://www.runscope.com/signin/oauth/access_token",
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 78. apisguru:signl4.com:get:/alerts/{alertId}/annotations

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/alerts/{alertId}/annotations",
  "path_params": [
    "alertId"
  ],
  "query_params": [],
  "summary": "Get annotations of an alert",
  "description": "Get annotations of an alert by id.",
  "security": [
    {
      "oauth2": [
        "public_api_write",
        "public_api_read",
        "offline_access"
      ]
    }
  ],
  "schema_fields": [
    "[].annotationType",
    "[].id",
    "[].text",
    "[].timestamp",
    "[].userId"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "userId"
  ],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "oauth2": [
          "public_api_write",
          "public_api_read",
          "offline_access"
        ]
      }
    ],
    "schemes": {
      "oauth2": {
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "https://connect.signl4.com/identity/connect/authorize",
            "refreshUrl": "https://connect.signl4.com/identity/connect/token",
            "scopes": {
              "offline_access": "Access write operations",
              "public_api_read": "Access write operations",
              "public_api_write": "Access read operations"
            },
            "tokenUrl": "https://connect.signl4.com/identity/connect/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 79. apisguru:simplyrets.com:get:/properties/{mlsId}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/properties/{mlsId}",
  "path_params": [
    "mlsId"
  ],
  "query_params": [
    "include"
  ],
  "summary": "Single Listing Endpoint",
  "description": "Use this endpoint for accessing a single listing. When you\nmake a search to the `/properties` endpoint, each listing in\nthe response will contain a unique `mlsId` field which should\nbe used to request that listing on this route.\n\nThe `mlsId` field is a unique identifier for a listing which\nis specific to the SimplyRETS API only.  It is different from\nthe `listingId` field is the public number given to a listing\nby the MLS and is not used here.\n",
  "security": [
    {
      "basicAuth": []
    }
  ],
  "schema_fields": [
    "address",
    "address.city",
    "address.country",
    "address.crossStreet",
    "address.full",
    "address.postalCode",
    "address.state",
    "address.streetName",
    "address.streetNumber",
    "address.streetNumberText",
    "agent",
    "agent.contact",
    "agent.contact.cell",
    "agent.contact.email",
    "agent.contact.office",
    "agent.firstName",
    "agent.id",
    "agent.lastName",
    "association",
    "association.amenities",
    "association.fee",
    "association.name",
    "coAgent",
    "coAgent.contact",
    "coAgent.contact.cell",
    "coAgent.contact.email",
    "coAgent.contact.office",
    "coAgent.firstName",
    "coAgent.id",
    "coAgent.lastName",
    "disclaimer",
    "geo",
    "geo.county",
    "geo.directions",
    "geo.lat",
    "geo.lng",
    "geo.marketArea",
    "leaseTerm",
    "leaseType",
    "listDate"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "ownerName"
  ],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "basicAuth": []
      }
    ],
    "schemes": {
      "basicAuth": {
        "description": "HTTP Basic Authentication. Works over `HTTPS` only",
        "type": "basic"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 80. apisguru:slmonitor.com:put:/api/v2.1/companies/{companyId}/users/{uniqueUserId}/itinerary-file

입력 근거 전문:

```json
{
  "method": "PUT",
  "path": "/api/v2.1/companies/{companyId}/users/{uniqueUserId}/itinerary-file",
  "path_params": [
    "companyId",
    "uniqueUserId"
  ],
  "query_params": [],
  "summary": "Update the itinerary file",
  "description": "This operation updates the worker's itinerary.",
  "security": [
    {
      "EmailLogin": [
        "CompanyMonitor"
      ]
    },
    {
      "MicrosoftLogin": [
        "CompanyMonitor"
      ]
    },
    {
      "Pin": []
    }
  ],
  "schema_fields": [
    "address",
    "cell",
    "comments",
    "company",
    "company.login",
    "company.name",
    "firstName",
    "fullName",
    "group",
    "group.name",
    "language",
    "lastName",
    "notificationEmails",
    "notificationPhones",
    "notificationPhones.[].order",
    "notificationPhones.[].phoneNumber",
    "phone",
    "priveleges",
    "satelliteDeviceId",
    "uniqueUserId",
    "vehicle",
    "vehicle.color",
    "vehicle.plate",
    "vehicle.type",
    "workerInformation",
    "workerInformation.actions",
    "workerInformation.actions.[].instructions",
    "workerInformation.actions.[].order",
    "workerInformation.itinerary",
    "workerInformation.lastLocation",
    "workerInformation.lastLocation.accuracy",
    "workerInformation.lastLocation.address",
    "workerInformation.lastLocation.altitude",
    "workerInformation.lastLocation.altitudeAccuracy",
    "workerInformation.lastLocation.battery",
    "workerInformation.lastLocation.device",
    "workerInformation.lastLocation.deviceName",
    "workerInformation.lastLocation.heading",
    "workerInformation.lastLocation.latitude",
    "workerInformation.lastLocation.longitude"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "company"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "EmailLogin": [
          "CompanyMonitor"
        ]
      },
      {
        "MicrosoftLogin": [
          "CompanyMonitor"
        ]
      },
      {
        "Pin": []
      }
    ],
    "schemes": {
      "EmailLogin": {
        "description": "",
        "flows": {
          "implicit": {
            "authorizationUrl": "https://prodsafetyline.b2clogin.com/prodsafetyline.onmicrosoft.com/B2C_1_si/oauth2/v2.0/authorize",
            "scopes": {
              "CompanyAdministrator": "This scope can only be set within SafetyLine.",
              "CompanyMonitor": "This scope can only be set within SafetyLine.",
              "https://prodsafetyline.onmicrosoft.com/e22f72d0-b056-4155-a2db-da02bc226023/access_as_user": "Access the API as the signed-in user"
            }
          }
        },
        "type": "oauth2"
      },
      "MicrosoftLogin": {
        "description": "",
        "flows": {
          "implicit": {
            "authorizationUrl": "https://login.microsoftonline.com/organizations/oauth2/v2.0/authorize",
            "scopes": {
              "CompanyAdministrator": "This scope can only be set within SafetyLine.",
              "CompanyMonitor": "This scope can only be set within SafetyLine.",
              "https://prodsafetyline.onmicrosoft.com/e22f72d0-b056-4155-a2db-da02bc226023/.default": "Use the default scopes"
            }
          }
        },
        "type": "oauth2"
      },
      "Pin": {
        "description": "",
        "scheme": "basic",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 81. apisguru:soundcloud.com:get:/playlists/{playlist_id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/playlists/{playlist_id}",
  "path_params": [
    "playlist_id"
  ],
  "query_params": [],
  "summary": "Returns a playlist.",
  "description": "",
  "security": [
    {
      "AuthHeader": [],
      "ClientId": []
    }
  ],
  "schema_fields": [
    "artwork_url",
    "created_at",
    "description",
    "downloadable",
    "duration",
    "ean",
    "embeddable_by",
    "genre",
    "id",
    "kind",
    "label",
    "label.avatar_url",
    "label.created_at",
    "label.id",
    "label.kind",
    "label.last_modified",
    "label.permalink",
    "label.permalink_url",
    "label.uri",
    "label.username",
    "label_id",
    "label_name",
    "last_modified",
    "license",
    "likes_count",
    "permalink",
    "permalink_url",
    "playlist_type",
    "purchase_title",
    "purchase_url",
    "release",
    "release_day",
    "release_month",
    "release_year",
    "sharing",
    "streamable",
    "tag_list",
    "tags",
    "title",
    "track_count"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "username",
    "user",
    "user_id"
  ],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "AuthHeader": [],
        "ClientId": []
      }
    ],
    "schemes": {
      "AuthHeader": {
        "description": "The string \"OAuth\" followed by the user’s token: OAuth ACCESS_TOKEN",
        "in": "header",
        "name": "Authorization",
        "type": "apiKey"
      },
      "ClientId": {
        "description": "Your product key. This is not the same as the API key used for most requests",
        "in": "query",
        "name": "client_id",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 82. apisguru:spoonacular.com:get:/mealplanner/{username}/templates/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/mealplanner/{username}/templates/{id}",
  "path_params": [
    "username",
    "id"
  ],
  "query_params": [],
  "summary": "Get Meal Plan Template",
  "description": "Get information about a meal plan template.",
  "security": [
    {
      "apiKeyScheme": []
    }
  ],
  "schema_fields": [
    "days",
    "days.[].day",
    "days.[].items",
    "days.[].items.[].id",
    "days.[].items.[].position",
    "days.[].items.[].slot",
    "days.[].items.[].type",
    "days.[].items.[].value",
    "days.[].items.[].value.id",
    "days.[].items.[].value.imageType",
    "days.[].items.[].value.title",
    "days.[].nutritionSummary",
    "days.[].nutritionSummary.nutrients",
    "days.[].nutritionSummary.nutrients.[].amount",
    "days.[].nutritionSummary.nutrients.[].name",
    "days.[].nutritionSummary.nutrients.[].percentDailyNeeds",
    "days.[].nutritionSummary.nutrients.[].unit",
    "days.[].nutritionSummaryBreakfast",
    "days.[].nutritionSummaryBreakfast.nutrients",
    "days.[].nutritionSummaryBreakfast.nutrients.[].amount",
    "days.[].nutritionSummaryBreakfast.nutrients.[].name",
    "days.[].nutritionSummaryBreakfast.nutrients.[].percentDailyNeeds",
    "days.[].nutritionSummaryBreakfast.nutrients.[].unit",
    "days.[].nutritionSummaryDinner",
    "days.[].nutritionSummaryDinner.nutrients",
    "days.[].nutritionSummaryDinner.nutrients.[].amount",
    "days.[].nutritionSummaryDinner.nutrients.[].name",
    "days.[].nutritionSummaryDinner.nutrients.[].percentDailyNeeds",
    "days.[].nutritionSummaryDinner.nutrients.[].unit",
    "days.[].nutritionSummaryLunch",
    "days.[].nutritionSummaryLunch.nutrients",
    "days.[].nutritionSummaryLunch.nutrients.[].amount",
    "days.[].nutritionSummaryLunch.nutrients.[].name",
    "days.[].nutritionSummaryLunch.nutrients.[].percentDailyNeeds",
    "days.[].nutritionSummaryLunch.nutrients.[].unit",
    "id",
    "name"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "apiKeyScheme": []
      }
    ],
    "schemes": {
      "apiKeyScheme": {
        "in": "header",
        "name": "x-api-key",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 83. apisguru:stackexchange.com:get:/users/{id}/inbox

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/users/{id}/inbox",
  "path_params": [
    "id"
  ],
  "query_params": [
    "pagesize",
    "page",
    "filter",
    "callback",
    "site"
  ],
  "summary": "",
  "description": "Returns a user's inbox.\n \nThis method requires an access_token, with a scope containing \"read_inbox\".\n \nThis method is effectively an alias for /inbox. It is provided for consumers who make strong assumptions about operating within the context of a single site rather than the Stack Exchange network as a whole.\n \n{id} can contain a single id, to find it programatically look for user_id on user or shallow_user objects.\n \nThis method returns a list of inbox items.\n",
  "security": null,
  "schema_fields": [
    "[].answer_id",
    "[].body",
    "[].comment_id",
    "[].creation_date",
    "[].is_unread",
    "[].item_type",
    "[].link",
    "[].question_id",
    "[].site",
    "[].site.aliases",
    "[].site.api_site_parameter",
    "[].site.audience",
    "[].site.closed_beta_date",
    "[].site.favicon_url",
    "[].site.high_resolution_icon_url",
    "[].site.icon_url",
    "[].site.launch_date",
    "[].site.logo_url",
    "[].site.markdown_extensions",
    "[].site.name",
    "[].site.open_beta_date",
    "[].site.related_sites",
    "[].site.site_state",
    "[].site.site_type",
    "[].site.site_url",
    "[].site.styling",
    "[].site.styling.link_color",
    "[].site.styling.tag_background_color",
    "[].site.styling.tag_foreground_color",
    "[].site.twitter_account",
    "[].title"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "site"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 84. apisguru:storecove.com:patch:/legal_entities/{id}

입력 근거 전문:

```json
{
  "method": "PATCH",
  "path": "/legal_entities/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Update LegalEntity",
  "description": "Update a specific LegalEntity.",
  "security": [
    {
      "Bearer": []
    }
  ],
  "schema_fields": [
    "advertisements",
    "city",
    "country",
    "county",
    "id",
    "line1",
    "line2",
    "party_name",
    "public",
    "rea",
    "rea.capital",
    "rea.identifier",
    "rea.liquidation_status",
    "rea.partners",
    "rea.province",
    "smart_inbox",
    "tenant_id",
    "third_party_password",
    "third_party_username",
    "zip",
    "peppol_identifiers",
    "peppol_identifiers.[].corppass",
    "peppol_identifiers.[].corppass.client_redirect_fail_url",
    "peppol_identifiers.[].corppass.client_redirect_success_url",
    "peppol_identifiers.[].corppass.corppass_url",
    "peppol_identifiers.[].corppass.enabled",
    "peppol_identifiers.[].corppass.flow_type",
    "peppol_identifiers.[].corppass.signer_email",
    "peppol_identifiers.[].corppass.signer_name",
    "peppol_identifiers.[].corppass.simulate_corppass",
    "peppol_identifiers.[].corppass.status",
    "peppol_identifiers.[].identifier",
    "peppol_identifiers.[].scheme",
    "peppol_identifiers.[].superscheme",
    "additional_tax_identifiers",
    "additional_tax_identifiers.[].country",
    "additional_tax_identifiers.[].county",
    "additional_tax_identifiers.[].id",
    "additional_tax_identifiers.[].identifier",
    "additional_tax_identifiers.[].scheme"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "tenant_id"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "Bearer": []
      }
    ],
    "schemes": {
      "Bearer": {
        "in": "header",
        "name": "Authorization",
        "type": "apiKey"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 85. apisguru:stripe.com:get:/v1/accounts/{account}/bank_accounts/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/v1/accounts/{account}/bank_accounts/{id}",
  "path_params": [
    "account",
    "id"
  ],
  "query_params": [
    "expand"
  ],
  "summary": "",
  "description": "<p>Retrieve a specified external account for a given account.</p>",
  "security": [
    {
      "basicAuth": []
    },
    {
      "bearerAuth": []
    }
  ],
  "schema_fields": [
    "account",
    "account.business_profile",
    "account.business_profile.mcc",
    "account.business_profile.name",
    "account.business_profile.product_description",
    "account.business_profile.support_address",
    "account.business_profile.support_address.city",
    "account.business_profile.support_address.country",
    "account.business_profile.support_address.line1",
    "account.business_profile.support_address.line2",
    "account.business_profile.support_address.postal_code",
    "account.business_profile.support_address.state",
    "account.business_profile.support_email",
    "account.business_profile.support_phone",
    "account.business_profile.support_url",
    "account.business_profile.url",
    "account.business_type",
    "account.capabilities",
    "account.capabilities.acss_debit_payments",
    "account.capabilities.affirm_payments",
    "account.capabilities.afterpay_clearpay_payments",
    "account.capabilities.au_becs_debit_payments",
    "account.capabilities.bacs_debit_payments",
    "account.capabilities.bancontact_payments",
    "account.capabilities.bank_transfer_payments",
    "account.capabilities.blik_payments",
    "account.capabilities.boleto_payments",
    "account.capabilities.card_issuing",
    "account.capabilities.card_payments",
    "account.capabilities.cartes_bancaires_payments",
    "account.capabilities.cashapp_payments",
    "account.capabilities.eps_payments",
    "account.capabilities.fpx_payments",
    "account.capabilities.giropay_payments",
    "account.capabilities.grabpay_payments",
    "account.capabilities.ideal_payments",
    "account.capabilities.india_international_payments",
    "account.capabilities.jcb_payments",
    "account.capabilities.klarna_payments",
    "account.capabilities.konbini_payments"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "account",
    "customer"
  ],
  "tenant_cols": [
    "account"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "basicAuth": []
      },
      {
        "bearerAuth": []
      }
    ],
    "schemes": {
      "basicAuth": {
        "description": "Basic HTTP authentication. Allowed headers-- Authorization: Basic <api_key> | Authorization: Basic <base64 hash of `api_key:`>",
        "scheme": "basic",
        "type": "http"
      },
      "bearerAuth": {
        "bearerFormat": "auth-scheme",
        "description": "Bearer HTTP authentication. Allowed headers-- Authorization: Bearer <api_key>",
        "scheme": "bearer",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 86. apisguru:telnyx.com:get:/authentication_providers/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/authentication_providers/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Retrieve an authentication provider",
  "description": "Retrieves the details of an existing authentication provider.",
  "security": [
    {
      "BearerAuth": []
    }
  ],
  "schema_fields": [
    "data",
    "data.active",
    "data.created_at",
    "data.id",
    "data.name",
    "data.organization_id",
    "data.record_type",
    "data.settings",
    "data.settings.assertion_consumer_service_url",
    "data.settings.idp_cert_fingerprint",
    "data.settings.idp_cert_fingerprint_algorithm",
    "data.settings.idp_entity_id",
    "data.settings.idp_sso_target_url",
    "data.settings.name_identifier_format",
    "data.settings.service_provider_entity_id",
    "data.short_name",
    "data.updated_at"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "organization_id"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "BearerAuth": []
      }
    ],
    "schemes": {
      "BearerAuth": {
        "scheme": "bearer",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 87. apisguru:telnyx.com:patch:/billing_groups/{id}

입력 근거 전문:

```json
{
  "method": "PATCH",
  "path": "/billing_groups/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Update a billing group",
  "description": "",
  "security": [
    {
      "BearerAuth": []
    }
  ],
  "schema_fields": [
    "data",
    "data.created_at",
    "data.deleted_at",
    "data.id",
    "data.name",
    "data.organization_id",
    "data.record_type",
    "data.updated_at"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "organization_id"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "global",
    "effective": [
      {
        "BearerAuth": []
      }
    ],
    "schemes": {
      "BearerAuth": {
        "scheme": "bearer",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 88. apisguru:tokenjay.app:get:/cancelbabel/{boxId}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/cancelbabel/{boxId}",
  "path_params": [
    "boxId"
  ],
  "query_params": [],
  "summary": "",
  "description": "",
  "security": null,
  "schema_fields": [
    "address",
    "addresses",
    "message",
    "messageSeverity",
    "reducedTx",
    "reducedTxList",
    "replyTo"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 89. apisguru:twilio.com:get:/2010-04-01/Accounts/{AccountSid}/AuthorizedConnectApps.json

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/2010-04-01/Accounts/{AccountSid}/AuthorizedConnectApps.json",
  "path_params": [
    "AccountSid"
  ],
  "query_params": [
    "PageSize",
    "Page",
    "PageToken"
  ],
  "summary": "",
  "description": "Retrieve a list of authorized-connect-apps belonging to the account used to make the request",
  "security": [
    {
      "accountSid_authToken": []
    }
  ],
  "schema_fields": [
    "authorized_connect_apps",
    "authorized_connect_apps.[].account_sid",
    "authorized_connect_apps.[].connect_app_company_name",
    "authorized_connect_apps.[].connect_app_description",
    "authorized_connect_apps.[].connect_app_friendly_name",
    "authorized_connect_apps.[].connect_app_homepage_url",
    "authorized_connect_apps.[].connect_app_sid",
    "authorized_connect_apps.[].permissions",
    "authorized_connect_apps.[].uri",
    "end",
    "first_page_uri",
    "next_page_uri",
    "page",
    "page_size",
    "previous_page_uri",
    "start",
    "uri"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "accountSid_authToken": []
      }
    ],
    "schemes": {
      "accountSid_authToken": {
        "scheme": "basic",
        "type": "http"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 90. apisguru:vestorly.com:get:/advisors/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/advisors/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [
    "vestorly_auth",
    "access_token"
  ],
  "summary": "",
  "description": "Returns a single advisor given their ID",
  "security": [
    {
      "access_token": [
        "default"
      ]
    }
  ],
  "schema_fields": [
    "about",
    "account_type",
    "address",
    "adv_brochure",
    "api_key",
    "city",
    "company",
    "compliance_bcc_email_address",
    "dashboard_url",
    "disclosure",
    "email_report_blast",
    "external_options",
    "first_name",
    "id",
    "last_name",
    "linkedin",
    "logo",
    "name",
    "plan",
    "profile_picture",
    "reg_number",
    "state",
    "tag",
    "twitter_handle",
    "website",
    "zip"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "company"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "access_token": [
          "default"
        ]
      }
    ],
    "schemes": {
      "access_token": {
        "authorizationUrl": "https://dev.vestorly.com/oauth/authorize",
        "flow": "implicit",
        "scopes": {
          "default": "read and write data to your account"
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 91. apisguru:visma.com:delete:/v1/activities/{guid}

입력 근거 전문:

```json
{
  "method": "DELETE",
  "path": "/v1/activities/{guid}",
  "path_params": [
    "guid"
  ],
  "query_params": [],
  "summary": "Delete an activity",
  "description": "Returns: No Content (204) if succeeded. Not found (404) if activity can't be found.",
  "security": [
    {
      "ClientIdAuth": [],
      "OAuth2": [
        "activities:delete"
      ]
    }
  ],
  "schema_fields": [],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "ClientIdAuth": [],
        "OAuth2": [
          "activities:delete"
        ]
      }
    ],
    "schemes": {
      "ClientIdAuth": {
        "description": "Client_Id header",
        "in": "header",
        "name": "Client_Id",
        "type": "apiKey"
      },
      "OAuth2": {
        "description": "This API uses OAuth 2 with the Client Credentials flow",
        "flows": {
          "clientCredentials": {
            "refreshUrl": "/refreshtoken",
            "scopes": {
              "activities:delete": "Delete access to activity resources",
              "activities:read": "Read-only access to activity resources",
              "activities:write": "Write access to activity resources",
              "customers:delete": "Delete access to customer resources",
              "customers:read": "Read-only access to customer resources",
              "customers:write": "Write access to customer resources",
              "fees:delete": "Delete access to project fee related resources",
              "fees:read": "Read-only access to project fee related resources",
              "fees:write": "Write access to project fee related resources",
              "files:delete": "Delete access to files",
              "files:read": "Read-only access to files",
              "files:write": "Write access to files",
              "hours:delete": "Delete access to work hour resources",
              "hours:read": "Read-only access to work hour resources",
              "hours:write": "Write access to work hour resources",
              "invoices:delete": "Delete access to invoice resources",
              "invoices:read": "Read-only access to invoice resources",
              "invoices:write": "Write access to invoice resources",
              "organization:read": "Read-only access to organization-level resources",
              "organization:write": "Write access to organization-level resources",
              "projects:delete": "Delete access to project resources",
              "projects:read": "Read-only access to project resources",
              "projects:write": "Write access to project resources",
              "resourceallocations:delete": "Delete access to resource allocations",
              "resourceallocations:read": "Read-only access to resource allocations",
              "resourceallocations:write": "Write access to resource allocations",
              "settings:delete": "Delete access to settings resources",
              "settings:read": "Read-only access to settings resources",
              "settings:write": "Write access to settings resources",
              "travels:delete": "Delete access to travel expense related resources",
              "travels:read": "Read-only access to travel expense related resources",
              "travels:write": "Write access to travel expense related resources",
              "users:delete": "Delete access to user resources",
              "users:read": "Read-only access to user resources",
              "users:write": "Write access to user resources"
            },
            "tokenUrl": "/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 92. apisguru:visma.com:get:/v1/activities/{guid}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/v1/activities/{guid}",
  "path_params": [
    "guid"
  ],
  "query_params": [],
  "summary": "Get activity by ID",
  "description": "",
  "security": [
    {
      "ClientIdAuth": [],
      "OAuth2": [
        "activities:read"
      ]
    }
  ],
  "schema_fields": [
    "activityType",
    "activityType.category",
    "activityType.guid",
    "activityType.name",
    "createdBy",
    "createdBy.code",
    "createdBy.firstName",
    "createdBy.guid",
    "createdBy.lastName",
    "createdBy.name",
    "createdDateTime",
    "customer",
    "customer.guid",
    "customer.name",
    "customer.number",
    "endDateTime",
    "guid",
    "hasDuration",
    "hasHours",
    "isAllDay",
    "isClosed",
    "isUnassigned",
    "lastUpdatedBy",
    "lastUpdatedBy.code",
    "lastUpdatedBy.firstName",
    "lastUpdatedBy.guid",
    "lastUpdatedBy.lastName",
    "lastUpdatedBy.name",
    "lastUpdatedDateTime",
    "location",
    "name",
    "notes",
    "ownerUser",
    "ownerUser.code",
    "ownerUser.guid",
    "ownerUser.keywords",
    "ownerUser.keywords.[].guid",
    "ownerUser.keywords.[].value",
    "ownerUser.name",
    "phase"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "createdBy",
    "customer"
  ],
  "tenant_cols": [
    "projectName"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "ClientIdAuth": [],
        "OAuth2": [
          "activities:read"
        ]
      }
    ],
    "schemes": {
      "ClientIdAuth": {
        "description": "Client_Id header",
        "in": "header",
        "name": "Client_Id",
        "type": "apiKey"
      },
      "OAuth2": {
        "description": "This API uses OAuth 2 with the Client Credentials flow",
        "flows": {
          "clientCredentials": {
            "refreshUrl": "/refreshtoken",
            "scopes": {
              "activities:delete": "Delete access to activity resources",
              "activities:read": "Read-only access to activity resources",
              "activities:write": "Write access to activity resources",
              "customers:delete": "Delete access to customer resources",
              "customers:read": "Read-only access to customer resources",
              "customers:write": "Write access to customer resources",
              "fees:delete": "Delete access to project fee related resources",
              "fees:read": "Read-only access to project fee related resources",
              "fees:write": "Write access to project fee related resources",
              "files:delete": "Delete access to files",
              "files:read": "Read-only access to files",
              "files:write": "Write access to files",
              "hours:delete": "Delete access to work hour resources",
              "hours:read": "Read-only access to work hour resources",
              "hours:write": "Write access to work hour resources",
              "invoices:delete": "Delete access to invoice resources",
              "invoices:read": "Read-only access to invoice resources",
              "invoices:write": "Write access to invoice resources",
              "organization:read": "Read-only access to organization-level resources",
              "organization:write": "Write access to organization-level resources",
              "projects:delete": "Delete access to project resources",
              "projects:read": "Read-only access to project resources",
              "projects:write": "Write access to project resources",
              "resourceallocations:delete": "Delete access to resource allocations",
              "resourceallocations:read": "Read-only access to resource allocations",
              "resourceallocations:write": "Write access to resource allocations",
              "settings:delete": "Delete access to settings resources",
              "settings:read": "Read-only access to settings resources",
              "settings:write": "Write access to settings resources",
              "travels:delete": "Delete access to travel expense related resources",
              "travels:read": "Read-only access to travel expense related resources",
              "travels:write": "Write access to travel expense related resources",
              "users:delete": "Delete access to user resources",
              "users:read": "Read-only access to user resources",
              "users:write": "Write access to user resources"
            },
            "tokenUrl": "/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 93. apisguru:watchful.li:get:/sites/{id}/extensions

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/sites/{id}/extensions",
  "path_params": [
    "id"
  ],
  "query_params": [
    "fields",
    "limit",
    "limitstart",
    "order"
  ],
  "summary": "Get extensions for a site",
  "description": "Get extensions for a site",
  "security": null,
  "schema_fields": [
    "date",
    "ext_name",
    "idx_site",
    "newVersion",
    "type",
    "url",
    "vUpdate",
    "version"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 94. apisguru:watchful.li:post:/sites/{id}/backupstart

입력 근거 전문:

```json
{
  "method": "POST",
  "path": "/sites/{id}/backupstart",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Start a remote backup for the site",
  "description": "Start a remote backup for the site",
  "security": null,
  "schema_fields": [
    "access_url",
    "admin_url",
    "akeebaProfile",
    "backupSchedule",
    "canBackup",
    "canUpdate",
    "dateBackup",
    "date_last_check",
    "error",
    "ip",
    "jUpdate",
    "j_version",
    "monitorid",
    "name",
    "nbUpdates",
    "new_j_version",
    "notes",
    "published",
    "secret_word",
    "siteid",
    "tags",
    "up",
    "word_akeeba",
    "word_check"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "siteid"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 95. apisguru:webflow.com:get:/deploymentEnvironments/{deploymentEnvironmentId}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/deploymentEnvironments/{deploymentEnvironmentId}",
  "path_params": [
    "deploymentEnvironmentId"
  ],
  "query_params": [],
  "summary": "",
  "description": "",
  "security": [
    {
      "OAuth2": [
        "api.lucidtech.ai/organizations:read"
      ]
    }
  ],
  "schema_fields": [
    "deploymentEnvironmentId",
    "description",
    "modelDeploymentUnits",
    "name",
    "organizationId",
    "status"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "organizationId"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "OAuth2": [
          "api.lucidtech.ai/organizations:read"
        ]
      }
    ],
    "schemes": {
      "OAuth2": {
        "flows": {
          "clientCredentials": {
            "scopes": {
              "api.lucidtech.ai/appclients:read": "Read permissions",
              "api.lucidtech.ai/appclients:write": "Write permissions",
              "api.lucidtech.ai/assets:read": "Read permissions",
              "api.lucidtech.ai/assets:write": "Write permissions",
              "api.lucidtech.ai/databundles:read": "Read permissions",
              "api.lucidtech.ai/databundles:write": "Write permissions",
              "api.lucidtech.ai/datasets:read": "Read permissions",
              "api.lucidtech.ai/datasets:write": "Write permissions",
              "api.lucidtech.ai/deploymentenvironments:read": "Read permissions",
              "api.lucidtech.ai/documents:read": "Read permissions",
              "api.lucidtech.ai/documents:write": "Write permissions",
              "api.lucidtech.ai/logs:read": "Read permissions",
              "api.lucidtech.ai/models:read": "Read permissions",
              "api.lucidtech.ai/models:write": "Write permissions",
              "api.lucidtech.ai/organizations:read": "Read permissions",
              "api.lucidtech.ai/organizations:write": "Write permissions",
              "api.lucidtech.ai/paymentmethods:read": "Read permissions",
              "api.lucidtech.ai/paymentmethods:write": "Write permissions",
              "api.lucidtech.ai/plans:read": "Read permissions",
              "api.lucidtech.ai/predictions:read": "Read permissions",
              "api.lucidtech.ai/predictions:write": "Write permissions",
              "api.lucidtech.ai/profiles:read": "Read permissions",
              "api.lucidtech.ai/profiles:write": "Write permissions",
              "api.lucidtech.ai/secrets:read": "Read permissions",
              "api.lucidtech.ai/secrets:write": "Write permissions",
              "api.lucidtech.ai/trainings:read": "Read permissions",
              "api.lucidtech.ai/trainings:write": "Write permissions",
              "api.lucidtech.ai/transitions.executions.heartbeats:write": "Write permissions",
              "api.lucidtech.ai/transitions.executions:read": "Read permissions",
              "api.lucidtech.ai/transitions.executions:write": "Write permissions",
              "api.lucidtech.ai/transitions:read": "Read permissions",
              "api.lucidtech.ai/transitions:write": "Write permissions",
              "api.lucidtech.ai/users:read": "Read permissions",
              "api.lucidtech.ai/users:write": "Write permissions",
              "api.lucidtech.ai/workflows.executions:read": "Read permissions",
              "api.lucidtech.ai/workflows.executions:write": "Write permissions",
              "api.lucidtech.ai/workflows:read": "Read permissions",
              "api.lucidtech.ai/workflows:write": "Write permissions"
            },
            "tokenUrl": "https://auth.lucidtech.ai/oauth2/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 96. apisguru:xero.com:get:/Connections

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/Connections",
  "path_params": [],
  "query_params": [
    "authEventId"
  ],
  "summary": "Retrieves the connections for this user",
  "description": "Override the base server url that include version",
  "security": [
    {
      "OAuth2": []
    }
  ],
  "schema_fields": [
    "[].authEventId",
    "[].createdDateUtc",
    "[].id",
    "[].tenantId",
    "[].tenantName",
    "[].tenantType",
    "[].updatedDateUtc"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "tenantId",
    "tenantName"
  ],
  "security_state": "declared",
  "security_details": {
    "origin": "operation",
    "effective": [
      {
        "OAuth2": []
      }
    ],
    "schemes": {
      "OAuth2": {
        "description": "For more information",
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "https://login.xero.com/identity/connect/authorize",
            "scopes": {
              "accounting.attachments": "Grant read-write access to",
              "accounting.attachments.read": "Grant read-only access to",
              "accounting.contacts": "Grant read-write access to",
              "accounting.contacts.read": "Grant read-only access to",
              "accounting.journals.read": "Grant read-only access to journals",
              "accounting.reports.read": "Grant read-only access to accounting reports",
              "accounting.settings": "Grant read-write access to organisation and account settings",
              "accounting.settings.read": "Grant read-only access to organisation and account settings",
              "accounting.transactions": "Grant read-write access to bank transactions, credit notes, invoices, repeating invoices",
              "accounting.transactions.read": "Grant read-only access to invoices",
              "assets assets.read": "Grant read-only access to",
              "email": "Grant read-only access to your email",
              "files": "Grant read-write access to",
              "files.read": "Grant read-only access to",
              "openid": "Grant read-only access to your open id",
              "payroll": "Grant read-write access to",
              "payroll.employees": "Grant read-write access to",
              "payroll.employees.read": "Grant read-only access to",
              "payroll.leaveapplications": "Grant read-write access to",
              "payroll.leaveapplications.read": "Grant read-only access to",
              "payroll.payitems": "Grant read-write access to",
              "payroll.payitems.read": "Grant read-only access to",
              "payroll.payrollcalendars": "Grant read-write access to",
              "payroll.payrollcalendars.read": "Grant read-only access to",
              "payroll.payruns": "Grant read-write access to",
              "payroll.payruns.read": "Grant read-only access to",
              "payroll.payslip": "Grant read-write access to",
              "payroll.payslip.read": "Grant read-only access to",
              "payroll.read": "Grant read-only access to",
              "payroll.settings.read": "Grant read-only access to",
              "payroll.superfundproducts.read": "Grant read-only access to",
              "payroll.superfunds": "Grant read-write access to",
              "payroll.superfunds.read": "Grant read-only access to",
              "payroll.timesheets": "Grant read-write access to",
              "payroll.timesheets.read": "Grant read-only access to",
              "profile": "your profile information",
              "projects": "Grant read-write access to projects",
              "projects.read": "Grant read-only access to projects"
            },
            "tokenUrl": "https://identity.xero.com/connect/token"
          }
        },
        "type": "oauth2"
      }
    },
    "missing_schemes": [],
    "anonymous_alternative": false
  }
}
```

## 97. apisguru:yodlee.com:get:/providers

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/providers",
  "path_params": [],
  "query_params": [
    "capability",
    "dataset$filter",
    "fullAccountNumberFields",
    "institutionId",
    "name",
    "priority",
    "providerId",
    "skip",
    "top"
  ],
  "summary": "Get Providers",
  "description": "The get provider service is used to get all the providers that are enabled, search a provider service by name or routing number and get popular sites of a region. <br>Searching for a provider using a routing number is applicable only to the USA and Canada regions.<br>The valid values for priority are: <br>   1. cobrand: Returns providers enabled for the cobrand (Default priority)<br>   2. popular: Returns providers popular among users of the customer<br><br>Only the datasets, attributes, and containers that are enabled for the customer will be returned in the response.<br>Input for the dataset$filter should adhere to the following expression:<br><dataset.name>[<attribute.name>.container[<container> OR <container>] OR <attribute.name>.container[<container>]] <br>OR <dataset.name>[<attribute.name> OR <attribute.name>]<br><b>dataset$filter value examples:</b><br>ACCT_PROFILE[FULL_ACCT_NUMBER.container[bank OR investment OR creditCard]]<br>ACCT_PROFILE[FULL_ACCT_NUMBER.container[bank]]<br>BASIC_AGG_DATA[ACCOUNT_DETAILS.container[bank OR investment] OR HOLDINGS.container[bank]] OR ACCT_PROFILE[FULL_ACCT_NUMBER.container[bank]]<br>BASIC_AGG_DATA<br>BASIC_AGG_DATA OR ACCT_PROFILE<br>BASIC_AGG_DATA [ ACCOUNT_DETAILS OR HOLDINGS ]<br>BASIC_AGG_DATA [ ACCOUNT_DETAILS] OR DOCUMENT <br>BASIC_AGG_DATA [ BASIC_ACCOUNT_INFO OR ACCOUNT_DETAILS ] <br><br>The fullAcountNumberFields is specified to filter the providers that have paymentAccountNumber or unmaskedAccountNumber support in the FULL_ACCT_NUMBER dataset attribute.<br><b>Examples for usage of fullAccountNumberFields </b><br>dataset$filter=ACCT_PROFILE[ FULL_ACCT_NUMBER.container [ bank ]] &amp; fullAccountNumberFields=paymentAccountNumber<br>dataset$filter=ACCT_PROFILE[ FULL_ACCT_NUMBER.container [ bank ]] &amp; fullAccountNumberFields=unmaskedAccountNumber<br>dataset$filter=ACCT_PROFILE[ FULL_ACCT_NUMBER.container [ bank ]] &amp; fullAccountNumberFields=unmaskedAccountNumber,paymentAccountNumber<br><br>The skip and top parameters are used for pagination. In the skip and top parameters, pass the number of records to be skipped and retrieved, respectively.<br>The response header provides the links to retrieve the next and previous set of transactions.<br><br><b>Note:</b> <ol><li>In a product flow involving user interaction, Yodlee recommends invoking this service with filters.<li>Without filters, the service may perform slowly as it takes a few minutes to return data in the response.<li>The AuthParameter appears in the response only in case of token-based aggregation sites.<li>The pagination feature only applies when the priority parameter is set as cobrand. If no values are provided in the skip and top parameters, the API will only return the first 500 records.<li>This service supports the localization feature and accepts locale as a header parameter.<li>The capability has been deprecated in query parameter and response.</li></ol>",
  "security": null,
  "schema_fields": [
    "provider",
    "provider.[].PRIORITY",
    "provider.[].accountType",
    "provider.[].associatedProviderIds",
    "provider.[].authParameter",
    "provider.[].authType",
    "provider.[].baseUrl",
    "provider.[].capability",
    "provider.[].capability.[].container",
    "provider.[].capability.[].name",
    "provider.[].countryISOCode",
    "provider.[].dataset",
    "provider.[].dataset.[].attribute",
    "provider.[].dataset.[].attribute.[].container",
    "provider.[].dataset.[].attribute.[].containerAttributes",
    "provider.[].dataset.[].attribute.[].containerAttributes.BANK",
    "provider.[].dataset.[].attribute.[].containerAttributes.BANK.fullAccountNumberFields",
    "provider.[].dataset.[].attribute.[].containerAttributes.BANK.numberOfTransactionDays",
    "provider.[].dataset.[].attribute.[].containerAttributes.CREDITCARD",
    "provider.[].dataset.[].attribute.[].containerAttributes.CREDITCARD.fullAccountNumberFields",
    "provider.[].dataset.[].attribute.[].containerAttributes.CREDITCARD.numberOfTransactionDays",
    "provider.[].dataset.[].attribute.[].containerAttributes.INSURANCE",
    "provider.[].dataset.[].attribute.[].containerAttributes.INSURANCE.fullAccountNumberFields",
    "provider.[].dataset.[].attribute.[].containerAttributes.INSURANCE.numberOfTransactionDays",
    "provider.[].dataset.[].attribute.[].containerAttributes.INVESTMENT",
    "provider.[].dataset.[].attribute.[].containerAttributes.INVESTMENT.fullAccountNumberFields",
    "provider.[].dataset.[].attribute.[].containerAttributes.INVESTMENT.numberOfTransactionDays",
    "provider.[].dataset.[].attribute.[].containerAttributes.LOAN",
    "provider.[].dataset.[].attribute.[].containerAttributes.LOAN.fullAccountNumberFields",
    "provider.[].dataset.[].attribute.[].containerAttributes.LOAN.numberOfTransactionDays",
    "provider.[].dataset.[].attribute.[].fromDate",
    "provider.[].dataset.[].attribute.[].fromFinYear",
    "provider.[].dataset.[].attribute.[].name",
    "provider.[].dataset.[].attribute.[].toDate",
    "provider.[].dataset.[].attribute.[].toFinYear",
    "provider.[].dataset.[].name",
    "provider.[].favicon",
    "provider.[].forgetPasswordUrl",
    "provider.[].help",
    "provider.[].id"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "provider"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 98. apisguru:yodlee.com:get:/providers/{providerId}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/providers/{providerId}",
  "path_params": [
    "providerId"
  ],
  "query_params": [],
  "summary": "Get Provider Details",
  "description": "The get provider detail service is used to get detailed information including the login form for a provider.<br>The response is a provider object that includes information such as name of the provider, <br>provider's base URL, a list of containers supported by the provider, the login form details of the provider, etc.<br>Only enabled datasets, attributes and containers gets returned in the response.<br><br><b>Note:</b><li>This service supports the localization feature and accepts locale as a header parameter.<li>The capability has been deprecated in the response.",
  "security": null,
  "schema_fields": [
    "provider",
    "provider.[].PRIORITY",
    "provider.[].accountType",
    "provider.[].associatedProviderIds",
    "provider.[].authParameter",
    "provider.[].authType",
    "provider.[].baseUrl",
    "provider.[].capability",
    "provider.[].capability.[].container",
    "provider.[].capability.[].name",
    "provider.[].countryISOCode",
    "provider.[].dataset",
    "provider.[].dataset.[].attribute",
    "provider.[].dataset.[].attribute.[].container",
    "provider.[].dataset.[].attribute.[].containerAttributes",
    "provider.[].dataset.[].attribute.[].containerAttributes.BANK",
    "provider.[].dataset.[].attribute.[].containerAttributes.BANK.fullAccountNumberFields",
    "provider.[].dataset.[].attribute.[].containerAttributes.BANK.numberOfTransactionDays",
    "provider.[].dataset.[].attribute.[].containerAttributes.CREDITCARD",
    "provider.[].dataset.[].attribute.[].containerAttributes.CREDITCARD.fullAccountNumberFields",
    "provider.[].dataset.[].attribute.[].containerAttributes.CREDITCARD.numberOfTransactionDays",
    "provider.[].dataset.[].attribute.[].containerAttributes.INSURANCE",
    "provider.[].dataset.[].attribute.[].containerAttributes.INSURANCE.fullAccountNumberFields",
    "provider.[].dataset.[].attribute.[].containerAttributes.INSURANCE.numberOfTransactionDays",
    "provider.[].dataset.[].attribute.[].containerAttributes.INVESTMENT",
    "provider.[].dataset.[].attribute.[].containerAttributes.INVESTMENT.fullAccountNumberFields",
    "provider.[].dataset.[].attribute.[].containerAttributes.INVESTMENT.numberOfTransactionDays",
    "provider.[].dataset.[].attribute.[].containerAttributes.LOAN",
    "provider.[].dataset.[].attribute.[].containerAttributes.LOAN.fullAccountNumberFields",
    "provider.[].dataset.[].attribute.[].containerAttributes.LOAN.numberOfTransactionDays",
    "provider.[].dataset.[].attribute.[].fromDate",
    "provider.[].dataset.[].attribute.[].fromFinYear",
    "provider.[].dataset.[].attribute.[].name",
    "provider.[].dataset.[].attribute.[].toDate",
    "provider.[].dataset.[].attribute.[].toFinYear",
    "provider.[].dataset.[].name",
    "provider.[].favicon",
    "provider.[].help",
    "provider.[].id",
    "provider.[].isAddedByUser"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [],
  "tenant_cols": [
    "provider"
  ],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 99. apisguru:zuora.com:get:/notifications/notification-definitions/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/notifications/notification-definitions/{id}",
  "path_params": [
    "id"
  ],
  "query_params": [],
  "summary": "Retrieve a notification definition",
  "description": "Queries the notification definition of the given ID.\n\n**Note**: This operation is only applicable to notifications for custom events.\n",
  "security": null,
  "schema_fields": [
    "active",
    "callout",
    "callout.active",
    "callout.calloutAuth",
    "callout.calloutAuth.domain",
    "callout.calloutAuth.password",
    "callout.calloutAuth.preemptive",
    "callout.calloutAuth.username",
    "callout.calloutBaseurl",
    "callout.calloutParams",
    "callout.calloutRetry",
    "callout.description",
    "callout.eventTypeName",
    "callout.httpMethod",
    "callout.id",
    "callout.name",
    "callout.requiredAuth",
    "calloutActive",
    "communicationProfileId",
    "createdBy",
    "createdOn",
    "description",
    "emailActive",
    "emailTemplateId",
    "eventTypeName",
    "eventTypeNamespace",
    "filterRule",
    "filterRule.condition",
    "filterRule.description",
    "filterRule.eventTypeName",
    "filterRule.id",
    "filterRule.parameters",
    "filterRuleParams",
    "id",
    "name",
    "updatedBy",
    "updatedOn"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "username",
    "createdBy"
  ],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```

## 100. apisguru:zuora.com:get:/objects/records/default/{object}/{id}

입력 근거 전문:

```json
{
  "method": "GET",
  "path": "/objects/records/default/{object}/{id}",
  "path_params": [
    "object",
    "id"
  ],
  "query_params": [],
  "summary": "Retrieve a custom object record",
  "description": "Retrieves a record of a given type by ID.\n",
  "security": null,
  "schema_fields": [
    "CreatedById",
    "CreatedDate",
    "Id",
    "UpdatedById",
    "UpdatedDate",
    "type"
  ],
  "schema_provenance": "Fields extracted from API response schema; not a verified database ERD",
  "owner_cols": [
    "CreatedById"
  ],
  "tenant_cols": [],
  "security_state": "unknown",
  "security_details": {
    "origin": "unspecified",
    "effective": null,
    "schemes": {},
    "missing_schemes": [],
    "anonymous_alternative": null
  }
}
```
