# 개발용 라벨 결정 v1

기존 파일 보존. 승인된 처리 방향과 최종 라벨 확정을 분리한다. 유지 확정 3건, 조건부 검수 5건, GET 근거 확인 1건.

| id | 기존 사람 label | 상태 | 조건부 후보 | 확정 label | 사유 |
|---|---|---|---|---|---|
| apisguru:appcenter.ms:patch:/v0.1/apps/{owner_name}/{app_name}/builds/{build_id} | membership_required | conditional_review | manual_review_required |  | 사용자 승인: 협업 멤버십/ACL만으로 기존 라벨을 확정하지 않음. 다른 정책 근거가 없으면 보류. 추가 근거 확인은 미완료 |
| apisguru:appwrite.io:put:/storage/files/{fileId} | owner_match | conditional_review | manual_review_required |  | 사용자 승인: 협업 멤버십/ACL만으로 기존 라벨을 확정하지 않음. 다른 정책 근거가 없으면 보류. 추가 근거 확인은 미완료 |
| apisguru:bitbucket.org:put:/repositories/{workspace}/{repo_slug}/commit/{commit}/reports/{reportId}/annotations/{annotationId} | membership_required | conditional_review | manual_review_required |  | 사용자 승인: 협업 멤버십/ACL만으로 기존 라벨을 확정하지 않음. 다른 정책 근거가 없으면 보류. 추가 근거 확인은 미완료 |
| apisguru:circuitsandbox.net:put:/conversations/community/{convId} | membership_required | conditional_review | manual_review_required |  | 사용자 승인: 협업 멤버십/ACL만으로 기존 라벨을 확정하지 않음. 다른 정책 근거가 없으면 보류. 추가 근거 확인은 미완료 |
| apisguru:gerermesaffaires.com:patch:/spaces/{id} | manual_review_required | confirmed_retained | manual_review_required | manual_review_required | 사용자 승인: 기존 보류 유지 |
| apisguru:microsoft.com:post:/{projectId}/classify/iterations/{publishedName}/image | manual_review_required | confirmed_retained | manual_review_required | manual_review_required | 사용자 승인: 기존 보류 유지 |
| apisguru:microsoft.com:post:/{projectId}/classify/iterations/{publishedName}/url | manual_review_required | confirmed_retained | manual_review_required | manual_review_required | 사용자 승인: 기존 보류 유지 |
| apisguru:shutterstock.com:patch:/v2/catalog/collections/{collection_id} | owner_match | conditional_review | manual_review_required |  | 사용자 승인: 협업 멤버십/ACL만으로 기존 라벨을 확정하지 않음. 다른 정책 근거가 없으면 보류. 추가 근거 확인은 미완료 |
| apisguru:zoom.us:get:/accounts/{accountId}/lock_settings | role_required | needs_get_policy_evidence |  |  | GET 자체에 적용되는 역할 및 플랜 조건을 추가 확인해야 함 |
