# 분류 품질 개선: 개발 근거 복구

외부 API 호출 0회. 학습·라벨 변경·프롬프트 변경 없음. 고정 test를 읽거나 개선 규칙 선정에 사용하지 않았다.

- 사람 교정 개발 30건 및 기존 검증 31건: 총 61건의 보충 입력 생성.
- 서비스 설명 복구: 50건.
- 상세 security schemes 존재: 52건.
- 원본 해시 일치: 61/61.
- API key/JWT/OAuth 존재는 역할 제한의 증거가 아니다. 서비스가 공개 OAS를 제공한다는 것 또한 endpoint가 public이라는 증거가 아니다.
- 서비스 설명·보안 정의·파라미터 정의는 보충 입력 파일에만 기록하며 사람 정답·교정 사유는 포함하지 않는다.
- 이 보충 입력을 실제 모델이 사용한 효과는 아직 측정하지 않았다. 파일 생성만으로 품질 향상을 주장하지 않는다.
- 기존 검증 31건은 오류 분석에 이미 사용됐다. 이후 튜닝 결과를 독립 일반화 성능으로 보고하지 않는다. 별도 미사용 사람 검수 표본이 필요하다.

## 기준 재검수 대상

기존 28건 분석의 범주 분류는 가설이며 사람 확정이 아니다. 아래 사례의 라벨은 자동 변경하지 않았다.

| id | 범주 | 사람 label | 모델 label | 진단 | 확인 |
|---|---|---|---|---|---|
| apisguru:appcenter.ms:patch:/v0.1/apps/{owner_name}/{app_name}/builds/{build_id} | 규칙·라벨 기준 충돌 | membership_required | role_required | 사람은 app collaborator를 membership으로 매핑하지만 입력에는 APIToken과 Cancels a build만 있다. collaborator는 입력 밖이고 구독형 membership 정의와도 다르다. | |
| apisguru:appwrite.io:put:/storage/files/{fileId} | 사람 라벨 재확인 | owner_match | role_required | Only users with write permissions와 $permissions.write는 ACL이다. ACL 쓰기 권한 보유자는 소유자와 동치가 아니다. | |
| apisguru:bitbucket.org:put:/repositories/{workspace}/{repo_slug}/commit/{commit}/reports/{reportId}/annotations/{annotationId} | 규칙·라벨 기준 충돌 | membership_required | manual_review_required | 사람 membership은 workspace/repository 구성원 쓰기 권한을 뜻하지만 프롬프트 membership은 plan/premium/subscription/tier 중심이다. 경로 workspace는 tenant 단서다. | |
| apisguru:circuitsandbox.net:put:/conversations/community/{convId} | 규칙·라벨 기준 충돌 | membership_required | role_required | WRITE_CONVERSATIONS/MANAGE_CONVERSATIONS는 OAuth 작업 권한이고 description에 구성원/관리자 관계는 없다. 사람 membership은 구독 중심 정의와 다르다. | |
| apisguru:gerermesaffaires.com:patch:/spaces/{id} | 규칙·라벨 기준 충돌 | manual_review_required | role_required | 실제 scope에 collaborator/owner/robot가 있다. 사람은 주체 불명확을 보류했지만 프롬프트는 단서 부족만으로 보류하지 말라고 한다. | |
| apisguru:microsoft.com:post:/{projectId}/classify/iterations/{publishedName}/image | 규칙·라벨 기준 충돌 | manual_review_required | membership_required | 사람은 prediction key의 7종 매핑 불명확을 보류한다. 프롬프트는 project를 tenant 단서로 규정하고 단서 부족 보류를 금지한다. 모델 membership에도 plan 근거가 없다. | |
| apisguru:microsoft.com:post:/{projectId}/classify/iterations/{publishedName}/url | 규칙·라벨 기준 충돌 | manual_review_required | membership_required | image 변형과 동일하게 project/키 기반 정책의 인간 보류와 강제 6종 제안 규칙이 충돌한다. membership 근거도 없다. | |
| apisguru:shutterstock.com:patch:/v2/catalog/collections/{collection_id} | 사람 라벨 재확인 | owner_match | role_required | 응답에 role_assignments.roles.editors/owners/viewers가 함께 있다. customer_accessCode와 collections.edit만으로 수정 권한을 owner 단독으로 확정할 수 없다. | |
| apisguru:zoom.us:get:/accounts/{accountId}/lock_settings | 규칙·라벨 기준 충돌 | role_required | membership_required | description에 account:read:admin과 Pro 이상 prerequisite가 동시에 명시돼 있다. 역할과 구독의 동시 조건 중 단일 label 우선순위가 불명확하다. | |
