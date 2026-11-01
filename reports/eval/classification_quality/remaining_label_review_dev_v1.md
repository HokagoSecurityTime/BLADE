# 남은 6건 원본 명세 검수

원본 로컬 OAS의 해당 operation과 security 정의를 확인했다. 6건 모두 저장된 추출 원본 해시와 일치한다. 최신 온라인 동작이나 서버 구현을 검증한 것은 아니다.

개발 기준 v1에 따른 에이전트 권고는 모두 manual_review_required이다. 사람이 확정한 새 정답이 아니며 confirmed_label은 비워 둔다. 이전 3건 보류 유지 확정과 이번 6건 권고는 구분한다.

| id | 기존 사람 label | 제안 label | 판단 근거 | 확정 label |
|---|---|---|---|---|
| apisguru:appcenter.ms:patch:/v0.1/apps/{owner_name}/{app_name}/builds/{build_id} | membership_required | manual_review_required | Cancels a build와 API token만으로 개인 소유·역할·구독·조직 일치 조건을 판별할 수 없다. owner_name 경로는 계정/조직 이름일 수 있으며 소유권 비교의 증거가 아니다. | |
| apisguru:appwrite.io:put:/storage/files/{fileId} | owner_match | manual_review_required | Only users with write permissions는 접근 권한 조건이다. 파일 소유자만 허용한다거나 특정 역할만 허용한다는 조건은 명시되지 않는다. Project 헤더도 조직 일치 검사 증거가 아니다. | |
| apisguru:bitbucket.org:put:/repositories/{workspace}/{repo_slug}/commit/{commit}/reports/{reportId}/annotations/{annotationId} | membership_required | manual_review_required | annotation 생성/수정 설명과 workspace/repository 경로가 있으나 이 요청의 접근 허용 조건은 명세에 특정되지 않는다. 협업 멤버십·tenant 일치·개인 소유를 경로만으로 확정하지 않는다. security 미선언도 public 근거가 아니다. | |
| apisguru:circuitsandbox.net:put:/conversations/community/{convId} | membership_required | manual_review_required | WRITE_CONVERSATIONS 설명은 authenticated user의 conversations를 명시한다. 그러나 사용자의 대화는 참여한 대화일 수도 있어 생성자/소유자 일치로 단정할 수 없다. MANAGE_CONVERSATIONS는 기능 권한이며 특정 관리자 역할 또는 구독 등급 조건은 아니다. | |
| apisguru:shutterstock.com:patch:/v2/catalog/collections/{collection_id} | owner_match | manual_review_required | collections.edit는 collection 수정 권한을 부여하지만 요청자가 소유자여야 한다는 조건은 없다. 편집 가능 사용자와 소유자는 동일하지 않으므로 owner_match로 확정하지 않는다. | |
| apisguru:zoom.us:get:/accounts/{accountId}/lock_settings | role_required | manual_review_required | 해당 GET 설명 자체에 account:read:admin scope와 Pro 이상 유료 계정 prerequisite가 모두 명시된다. 개발 기준 v1의 독립 필수 조건 규칙에 따라 role_required 또는 membership_required 하나로 축약하지 않고 보류를 제안한다. 계정 owner의 설정 변경 설명은 GET의 개인 소유권 근거로 사용하지 않는다. | |

## apisguru:appcenter.ms:patch:/v0.1/apps/{owner_name}/{app_name}/builds/{build_id}

원본: `datasets/blade/raw/openapi-directory/APIs/appcenter.ms/v0.1/openapi.yaml`

operation JSON pointer: `/paths/~1v0.1~1apps~1{owner_name}~1{app_name}~1builds~1{build_id}/patch`

해당 요청 설명:

Cancels a build

판단: Cancels a build와 API token만으로 개인 소유·역할·구독·조직 일치 조건을 판별할 수 없다. owner_name 경로는 계정/조직 이름일 수 있으며 소유권 비교의 증거가 아니다.

## apisguru:appwrite.io:put:/storage/files/{fileId}

원본: `datasets/blade/raw/openapi-directory/APIs/appwrite.io/client/0.9.3/openapi.yaml`

operation JSON pointer: `/paths/~1storage~1files~1{fileId}/put`

해당 요청 설명:

Update a file by its unique ID. Only users with write permissions have access to update this resource.

판단: Only users with write permissions는 접근 권한 조건이다. 파일 소유자만 허용한다거나 특정 역할만 허용한다는 조건은 명시되지 않는다. Project 헤더도 조직 일치 검사 증거가 아니다.

## apisguru:bitbucket.org:put:/repositories/{workspace}/{repo_slug}/commit/{commit}/reports/{reportId}/annotations/{annotationId}

원본: `datasets/blade/raw/openapi-directory/APIs/bitbucket.org/2.0/openapi.yaml`

operation JSON pointer: `/paths/~1repositories~1{workspace}~1{repo_slug}~1commit~1{commit}~1reports~1{reportId}~1annotations~1{annotationId}/put`

해당 요청 설명:

Creates or updates an individual annotation for the specified report.
Annotations are individual findings that have been identified as part of a report, for example, a line of code that represents a vulnerability. These annotations can be attached to a specific file and even a specific line in that file, however, that is optional. Annotations are not mandatory and a report can contain up to 1000 annotations.

Just as reports, annotation needs to be uploaded with a unique ID that can later be used to identify the report as an alternative to the generated [UUID](https://developer.atlassian.com/bitbucket/api/2/reference/meta/uri-uuid#uuid). If you want to use an existing id from your own system, we recommend prefixing it with your system's name to avoid collisions, for example, mySystem-annotation001.

### Sample cURL request:
```
curl --request PUT 'https://api.bitbucket.org/2.0/repositories/<username>/<reposity-name>/commit/<commit-hash>/reports/mySystem-001/annotations/mysystem-annotation001' \
--header 'Content-Type: application/json' \
--data-raw '{
    "title": "Security scan report",
    "annotation_type": "VULNERABILITY",
    "summary": "This line represents a security thread.",
    "severity": "HIGH",
    "path": "my-service/src/main/java/com/myCompany/mysystem/logic/Main.java",
    "line": 42
}'
```

### Possible field values:
annotation_type: VULNERABILITY, CODE_SMELL, BUG
result: PASSED, FAILED, IGNORED, SKIPPED
severity: HIGH, MEDIUM, LOW, CRITICAL

Please refer to the [Code Insights documentation](https://confluence.atlassian.com/bitbucket/code-insights-994316785.html) for more information.


판단: annotation 생성/수정 설명과 workspace/repository 경로가 있으나 이 요청의 접근 허용 조건은 명세에 특정되지 않는다. 협업 멤버십·tenant 일치·개인 소유를 경로만으로 확정하지 않는다. security 미선언도 public 근거가 아니다.

## apisguru:circuitsandbox.net:put:/conversations/community/{convId}

원본: `datasets/blade/raw/openapi-directory/APIs/circuitsandbox.net/2.9.235/openapi.yaml`

operation JSON pointer: `/paths/~1conversations~1community~1{convId}/put`

해당 요청 설명:

Updates the information of the given community.
OauthScopes: WRITE_CONVERSATIONS, MANAGE_CONVERSATIONS

판단: WRITE_CONVERSATIONS 설명은 authenticated user의 conversations를 명시한다. 그러나 사용자의 대화는 참여한 대화일 수도 있어 생성자/소유자 일치로 단정할 수 없다. MANAGE_CONVERSATIONS는 기능 권한이며 특정 관리자 역할 또는 구독 등급 조건은 아니다.

## apisguru:shutterstock.com:patch:/v2/catalog/collections/{collection_id}

원본: `datasets/blade/raw/openapi-directory/APIs/shutterstock.com/1.1.32/openapi.yaml`

operation JSON pointer: `/paths/~1v2~1catalog~1collections~1{collection_id}/patch`

해당 요청 설명:

This endpoint updates the metadata of a catalog collection.

판단: collections.edit는 collection 수정 권한을 부여하지만 요청자가 소유자여야 한다는 조건은 없다. 편집 가능 사용자와 소유자는 동일하지 않으므로 owner_match로 확정하지 않는다.

## apisguru:zoom.us:get:/accounts/{accountId}/lock_settings

원본: `datasets/blade/raw/openapi-directory/APIs/zoom.us/2.0.0/openapi.yaml`

operation JSON pointer: `/paths/~1accounts~1{accountId}~1lock_settings/get`

해당 요청 설명:

[Account Locked Settings](https://support.zoom.us/hc/en-us/articles/115005269866) allow you turn settings on or off for all users in your account. No user except the account admin or account owner can change these settings. With lock settings, you force the settings on for all users.
Use this API to retrieve an account's locked settings. 

**Note:** This API can be used by Zoom Accounts that are on a Pro or a higher plan as well accounts that have master and sub accounts options enabled. <br><br>
**Prerequisites:**
* Pro or a higher paid account. <br>

**Scope**: `account:read:admin`.
<br> **[Rate Limit Label](https://marketplace.zoom.us/docs/api-reference/rate-limits#rate-limits):** `Medium`<br>





**Scope:** account:read:admin

판단: 해당 GET 설명 자체에 account:read:admin scope와 Pro 이상 유료 계정 prerequisite가 모두 명시된다. 개발 기준 v1의 독립 필수 조건 규칙에 따라 role_required 또는 membership_required 하나로 축약하지 않고 보류를 제안한다. 계정 owner의 설정 변경 설명은 GET의 개인 소유권 근거로 사용하지 않는다.

## 평가 시 주의

이 6건은 충돌 사례를 의도적으로 모은 표본이다. 전부 보류라는 결과를 전체 데이터의 보류 정책으로 일반화하지 않는다. 변경된 기준으로 정답을 재정의해 생긴 점수 상승을 모델 성능 향상이라고 보고하지 않는다.
API 호출·학습·기존 라벨 수정은 수행하지 않았다. 원본 전체 operation과 보안 정의는 JSON 산출물에 보존했다.
