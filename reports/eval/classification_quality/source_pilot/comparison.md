# 코드·스펙 기반 새 표본: 세 버전 비교

WFD(구 EMB)의 서로 다른 서비스 3개에서 정적으로 추출했다. 기존 APIs.guru 표본과 다른 개발 실험이며 정확도 비교가 아니다.
저장소 커밋: `915859080da033fc36feae54bab3ad4a7b04e872`. 소스 파일 해시 및 기존 고정 test 해시 검증 완료.

| 서비스 | 건수 |
|---|---:|
| blogapi | 20 |
| features-service | 10 |
| user-management | 20 |

핸들러 매핑 미확정으로 제외한 후보: 8건.
서비스당 최대 20건, seed 42. features-service는 매핑된 10건을 사용했다.

## 비교 조건

- OpenAI gpt-4o-mini 계열, temperature 0, 동일 50개 ID와 동일 입력 해시.
- 실제 OAS의 method·path·설명·보안 선언에 핸들러 전체 파일, 연결된 프로젝트 타입·서비스 구현, 확보된 전역 보안 설정을 description으로 추가했다.
- 코드 위치는 파일별 줄번호와 SHA-256을 보존했다. 완전한 호출 그래프 분석이나 실제 인가 동작 검증은 아니다.
- OAS에서 보안 선언이 없다는 이유로 explicitly_anonymous를 만들지 않았다. 코드를 실행하지 않았다.
- 실제 DB ERD를 생성했다고 주장하지 않는다. schema_fields와 후보 컬럼은 빈 배열이며 모델 코드는 소스 문맥에 포함될 수 있다.
- 학습 정답이나 AI 제안 라벨을 입력에 넣지 않았다. 동일 파일의 다른 핸들러도 포함되므로 method별 근거 적용 여부는 후속 검토 대상이다.
- 이번 범위는 B 유형의 WFD 파일럿이다. RealWorld·SwaggerHub·Postman·gapbench 전체 수집은 하지 않았다.

## 라벨 분포

| label | v2.6 | v2.7 | v2.8 |
|---|---:|---:|---:|
| public | 0 | 14 | 17 |
| role_required | 4 | 14 | 2 |
| membership_required | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 |
| owner_match | 2 | 7 | 10 |
| owner_or_admin | 2 | 3 | 11 |
| manual_review_required | 42 | 12 | 10 |

| 항목 | v2.6 | v2.7 | v2.8 |
|---|---:|---:|---:|
| errors | 0 | 0 | 0 |
| evidence_invalid | 0 | 1 | 0 |
| flag_review | 0 | 2 | 2 |
| input_tokens | 1190945 | 990191 | 926138 |
| output_tokens | 3059 | 4802 | 4796 |
| response_count | 51 | 66 | 58 |

## 서비스별 분포

| 서비스 | 버전 | label 건수 |
|---|---|---|
| blogapi | v2.6 | {'manual_review_required': 17, 'owner_or_admin': 1, 'role_required': 1, 'owner_match': 1} |
| blogapi | v2.7 | {'public': 7, 'role_required': 7, 'manual_review_required': 3, 'owner_match': 2, 'owner_or_admin': 1} |
| blogapi | v2.8 | {'public': 9, 'owner_or_admin': 5, 'owner_match': 4, 'role_required': 2} |
| features-service | v2.6 | {'manual_review_required': 10} |
| features-service | v2.7 | {'manual_review_required': 6, 'owner_or_admin': 1, 'public': 1, 'owner_match': 2} |
| features-service | v2.8 | {'public': 2, 'owner_match': 4, 'manual_review_required': 2, 'owner_or_admin': 2} |
| user-management | v2.6 | {'manual_review_required': 15, 'role_required': 3, 'owner_or_admin': 1, 'owner_match': 1} |
| user-management | v2.7 | {'role_required': 7, 'public': 6, 'owner_or_admin': 1, 'owner_match': 3, 'manual_review_required': 3} |
| user-management | v2.8 | {'owner_or_admin': 4, 'public': 6, 'manual_review_required': 8, 'owner_match': 2} |

API 응답의 실제 토큰 사용량이다. 청구 비용은 별도로 확인해야 하며 단가를 임의 적용하지 않았다.

## 해석과 다음 확인

코드가 있어도 검사 미발견은 의도된 public 정책의 증명이 아니다. 사용자 관리 서비스의 RBAC 객체 관리 기능과 호출자 역할 검사를 구분해야 한다.
기존 OAS-only 100건과는 서비스·표본·입력이 모두 달라 점수나 분포 차이를 코드 추가의 인과 효과로 해석할 수 없다.
이 표본의 독립 정답 또는 AI 코드 검수 기준은 아직 생성하지 않았다. 따라서 현재 가장 정확한 버전을 선정하지 않는다.

## 요청별 결과

| service | method | path | v2.6 | v2.7 | v2.8 | 핸들러 |
|---|---|---|---|---|---|---|
| blogapi | GET | /api/categories/{id} | manual_review_required | manual_review_required | public | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/CategoryController.java |
| blogapi | GET | /api/posts/{postId}/comments | manual_review_required | public | public | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/CommentController.java |
| blogapi | DELETE | /api/posts/{postId}/comments/{id} | owner_or_admin | role_required | owner_or_admin | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/CommentController.java |
| blogapi | GET | /api/albums/{id} | manual_review_required | public | public | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/AlbumController.java |
| blogapi | GET | /api/posts/{id} | manual_review_required | owner_match | public | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/PostController.java |
| blogapi | PUT | /api/todos/{id}/complete | role_required | role_required | owner_match | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/TodoController.java |
| blogapi | GET | /api/posts | manual_review_required | public | public | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/PostController.java |
| blogapi | PUT | /api/todos/{id}/unComplete | manual_review_required | role_required | owner_match | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/TodoController.java |
| blogapi | GET | /api/posts/tag/{id} | manual_review_required | public | public | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/PostController.java |
| blogapi | GET | /api/photos | manual_review_required | public | public | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/PhotoController.java |
| blogapi | PUT | /api/users/{username} | manual_review_required | owner_or_admin | owner_or_admin | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/UserController.java |
| blogapi | POST | /api/posts/{postId}/comments | manual_review_required | role_required | role_required | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/CommentController.java |
| blogapi | GET | /api/todos | manual_review_required | manual_review_required | owner_or_admin | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/TodoController.java |
| blogapi | POST | /api/tags | manual_review_required | role_required | role_required | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/TagController.java |
| blogapi | GET | /api/tags/{id} | manual_review_required | public | public | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/TagController.java |
| blogapi | GET | /api/users/me | owner_match | owner_match | owner_match | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/UserController.java |
| blogapi | PUT | /api/albums/{id} | manual_review_required | role_required | owner_or_admin | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/AlbumController.java |
| blogapi | GET | /api/tags | manual_review_required | public | public | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/TagController.java |
| blogapi | PUT | /api/categories/{id} | manual_review_required | role_required | owner_or_admin | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/CategoryController.java |
| blogapi | GET | /api/posts/{postId}/comments/{id} | manual_review_required | manual_review_required | owner_match | jdk_8_maven/cs/rest/original/blogapi/src/main/java/com/sopromadze/blogapi/controller/CommentController.java |
| features-service | GET | /products/{productName} | manual_review_required | manual_review_required | public | jdk_8_maven/cs/rest/original/features-service/src/main/java/org/javiermf/features/services/rest/ProductsResource.java |
| features-service | POST | /products/{productName}/configurations/{configurationName} | manual_review_required | manual_review_required | owner_match | jdk_8_maven/cs/rest/original/features-service/src/main/java/org/javiermf/features/services/rest/ProductsConfigurationResource.java |
| features-service | GET | /products/{productName}/configurations/{configurationName} | manual_review_required | manual_review_required | manual_review_required | jdk_8_maven/cs/rest/original/features-service/src/main/java/org/javiermf/features/services/rest/ProductsConfigurationResource.java |
| features-service | POST | /products/{productName} | manual_review_required | manual_review_required | manual_review_required | jdk_8_maven/cs/rest/original/features-service/src/main/java/org/javiermf/features/services/rest/ProductsResource.java |
| features-service | DELETE | /products/{productName}/constraints/{constraintId} | manual_review_required | owner_or_admin | owner_or_admin | jdk_8_maven/cs/rest/original/features-service/src/main/java/org/javiermf/features/services/rest/ProductsConstraintsResource.java |
| features-service | GET | /products | manual_review_required | public | public | jdk_8_maven/cs/rest/original/features-service/src/main/java/org/javiermf/features/services/rest/ProductsResource.java |
| features-service | DELETE | /products/{productName} | manual_review_required | owner_match | owner_or_admin | jdk_8_maven/cs/rest/original/features-service/src/main/java/org/javiermf/features/services/rest/ProductsResource.java |
| features-service | DELETE | /products/{productName}/configurations/{configurationName} | manual_review_required | owner_match | owner_match | jdk_8_maven/cs/rest/original/features-service/src/main/java/org/javiermf/features/services/rest/ProductsConfigurationResource.java |
| features-service | POST | /products/{productName}/configurations/{configurationName}/features/{featureName} | manual_review_required | manual_review_required | owner_match | jdk_8_maven/cs/rest/original/features-service/src/main/java/org/javiermf/features/services/rest/ProductsConfigurationFeaturesResource.java |
| features-service | GET | /products/{productName}/configurations | manual_review_required | manual_review_required | owner_match | jdk_8_maven/cs/rest/original/features-service/src/main/java/org/javiermf/features/services/rest/ProductsConfigurationResource.java |
| user-management | POST | /users/{id}/roles/{roleId} | role_required | role_required | owner_or_admin | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/UserRestController.java |
| user-management | PUT | /users/rbac/permissions | manual_review_required | role_required | manual_review_required | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/RBACRestController.java |
| user-management | GET | /users/rbac/salt | manual_review_required | public | public | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/RBACRestController.java |
| user-management | POST | /users/rbac/permissions | manual_review_required | role_required | manual_review_required | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/RBACRestController.java |
| user-management | POST | /users/rbac/roles | manual_review_required | role_required | manual_review_required | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/RBACRestController.java |
| user-management | DELETE | /users/rbac/roles/{roleId}/permissions/{permissionKey} | role_required | owner_or_admin | owner_or_admin | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/RBACRestController.java |
| user-management | POST | /users/register | manual_review_required | public | public | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/RegisterRestController.java |
| user-management | DELETE | /users/{id} | owner_or_admin | owner_match | owner_or_admin | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/UserRestController.java |
| user-management | GET | /users/rbac/permissions/{permissionKey} | manual_review_required | manual_review_required | manual_review_required | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/RBACRestController.java |
| user-management | POST | /users/rbac/roles/{roleId}/permissions/{permissionKey} | role_required | role_required | manual_review_required | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/RBACRestController.java |
| user-management | PUT | /users/{id} | manual_review_required | owner_match | owner_match | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/UserRestController.java |
| user-management | GET | /users/rbac/roles/{roleId} | manual_review_required | manual_review_required | manual_review_required | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/RBACRestController.java |
| user-management | GET | /users | manual_review_required | public | public | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/UserRestController.java |
| user-management | DELETE | /users/rbac/roles/{roleId} | manual_review_required | manual_review_required | manual_review_required | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/RBACRestController.java |
| user-management | POST | /users | manual_review_required | role_required | manual_review_required | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/UserRestController.java |
| user-management | GET | /users/{id} | manual_review_required | owner_match | owner_match | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/UserRestController.java |
| user-management | DELETE | /users/rbac/permissions/{permissionKey} | manual_review_required | role_required | owner_or_admin | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/RBACRestController.java |
| user-management | GET | /users/rbac/roles | manual_review_required | public | public | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/RBACRestController.java |
| user-management | POST | /login | owner_match | public | public | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/LoginRestController.java |
| user-management | GET | /users/rbac/permissions | manual_review_required | public | public | jdk_8_maven/cs/rest/original/user-management/src/main/java/com/giassi/microservice/demo2/rest/RBACRestController.java |
