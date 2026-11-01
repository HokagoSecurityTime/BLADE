# 라벨 기준 결정 및 재검수

자동 라벨 수정 없음. 아래 권고는 확정 라벨이 아니다. 모델 응답은 이번 보충 입력 측정 결과다.

| id | 쟁점 | 기존 사람 라벨 | 최신 모델 라벨 | 결정할 질문 | 권고 | 확정 라벨 | 사유 |
|---|---|---|---|---|---|---|---|
| apisguru:appcenter.ms:patch:/v0.1/apps/{owner_name}/{app_name}/builds/{build_id} | membership 의미 | membership_required | role_required | 구독 등급과 리소스 참여·멤버십을 같은 라벨로 볼지 결정 | 현재 plan/tier 중심 정의와 사람의 협업 멤버십 해석을 먼저 일치시킬 것. 근거가 없는 멤버십은 자동 추론하지 않음 |  |  |
| apisguru:appwrite.io:put:/storage/files/{fileId} | ACL과 소유권 | owner_match | role_required | 편집 권한 보유자를 소유자라고 볼 수 있는지 재검수 | ACL write/edit 권한만으로 owner_match를 확정하지 않음. 역할 또는 리소스별 ACL 중 무엇인지 소스 근거 확인 |  |  |
| apisguru:bitbucket.org:put:/repositories/{workspace}/{repo_slug}/commit/{commit}/reports/{reportId}/annotations/{annotationId} | membership 의미 | membership_required | manual_review_required | 구독 등급과 리소스 참여·멤버십을 같은 라벨로 볼지 결정 | 현재 plan/tier 중심 정의와 사람의 협업 멤버십 해석을 먼저 일치시킬 것. 근거가 없는 멤버십은 자동 추론하지 않음 |  |  |
| apisguru:circuitsandbox.net:put:/conversations/community/{convId} | membership 의미 | membership_required | role_required | 구독 등급과 리소스 참여·멤버십을 같은 라벨로 볼지 결정 | 현재 plan/tier 중심 정의와 사람의 협업 멤버십 해석을 먼저 일치시킬 것. 근거가 없는 멤버십은 자동 추론하지 않음 |  |  |
| apisguru:gerermesaffaires.com:patch:/spaces/{id} | manual 허용 범위 | manual_review_required | role_required | 역할/프로젝트 단서는 있지만 정책을 특정할 수 없는 경우 보류를 허용할지 결정 | 정책을 구분할 근거가 부족한 경우 보류 허용을 권고. 객체 ID 존재만으로 구체 라벨을 강제하지 않음 |  |  |
| apisguru:microsoft.com:post:/{projectId}/classify/iterations/{publishedName}/image | manual 허용 범위 | manual_review_required | membership_required | 역할/프로젝트 단서는 있지만 정책을 특정할 수 없는 경우 보류를 허용할지 결정 | 정책을 구분할 근거가 부족한 경우 보류 허용을 권고. 객체 ID 존재만으로 구체 라벨을 강제하지 않음 |  |  |
| apisguru:microsoft.com:post:/{projectId}/classify/iterations/{publishedName}/url | manual 허용 범위 | manual_review_required | membership_required | 역할/프로젝트 단서는 있지만 정책을 특정할 수 없는 경우 보류를 허용할지 결정 | 정책을 구분할 근거가 부족한 경우 보류 허용을 권고. 객체 ID 존재만으로 구체 라벨을 강제하지 않음 |  |  |
| apisguru:shutterstock.com:patch:/v2/catalog/collections/{collection_id} | ACL과 소유권 | owner_match | role_required | 편집 권한 보유자를 소유자라고 볼 수 있는지 재검수 | ACL write/edit 권한만으로 owner_match를 확정하지 않음. 역할 또는 리소스별 ACL 중 무엇인지 소스 근거 확인 |  |  |
| apisguru:zoom.us:get:/accounts/{accountId}/lock_settings | 복수 정책 단일 라벨 | role_required | owner_or_admin | 계정 관리자·계정 소유자·유료 플랜이 함께 있는 요청의 대표 라벨 결정 | 계정 owner를 개인 객체 owner와 동일시하지 않음. 역할 제한이 핵심이라는 해석은 가능하나 사람 확정 필요 |  |  |

## 검수 원칙

- 서비스 이름만으로 접근 정책을 가정하지 않는다. 기존 사람 라벨도 검토 대상이며 모델의 불일치가 항상 모델 오류라는 뜻은 아니다.
- 한 요청에 여러 조건이 있으면 실제 근거와 대표 라벨 선택 이유를 함께 기록한다. 모든 API에 일률적인 우선순위를 적용하지 않는다.
- 기준이 확정되면 개발 예제와 라벨 지침에 반영하고, 기존에 분석하지 않은 사람 검수 표본에서 평가한다. 이번 31건은 진단용 회귀 표본이다.
