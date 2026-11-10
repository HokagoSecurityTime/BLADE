# S4 정지 지점 1-2: 분석기 정밀도 점검 (test_v5 30건, 개선 전/후) — 2026-11-03

분류는 유지 블록(ctx4096 기준, 개선 후) / 개선 전 분석기(전역 이름 검색, 스크래치 보존본)의 유지 블록에 대해 규칙으로 1차 분류한 뒤 Claude(AI)가 블록 본문을 읽고 수정했다(stop12_manual_overrides.json에 수정 내역·사유). 정답 열은 읽지 않았다. 사람 확인은 아직 없다.
직접 = 해당 엔드포인트의 인가 판단 조건(권한표·permissible·canAccessRoom·역할/소유자 검사)을 담은 블록. 간접 = 인가 흐름의 일부지만 결정 조건이 아닌 블록(깊이 2 호출, 권한 프레임워크 공통 코드). 무관 = 인증·검증·유틸 등 인가 조건이 없는 블록. 잘못된 구현 = 동명 다른 함수·다른 방 종류·omnichannel 파일 등 이 핸들러가 실제로 호출하지 않는 정의.

표본 30건(seed 42): Ghost 8 · Rocket.Chat 14 · Umami 8 — v5t-ghost-244db7151d, v5t-ghost-05ee24e847, v5t-ghost-6e1dca8d3d, v5t-ghost-5f25be85a3, v5t-ghost-56bc478d48, v5t-ghost-3904cb1077, v5t-ghost-a322c4eaaa, v5t-ghost-0cbaf4100c, v5t-rocketchat-e880661365, v5t-rocketchat-258c4c7f6e, v5t-rocketchat-f5874fe2eb, v5t-rocketchat-b29bfcff96, v5t-rocketchat-0d4fa14e85, v5t-rocketchat-0b84024de3, v5t-rocketchat-25c4e3c534, v5t-rocketchat-61d5e55ae2, v5t-rocketchat-64704a55de, v5t-rocketchat-cdf09d2caa, v5t-rocketchat-fd924826e6, v5t-rocketchat-0a75eb9b8b, v5t-rocketchat-ecefcc9d2c, v5t-rocketchat-5b6c0ebf4d, v5t-umami-bdd6ebb218, v5t-umami-b5fb9b9198, v5t-umami-bd9e54d1f1, v5t-umami-a8feaa9ffc, v5t-umami-640719b3b2, v5t-umami-29da074b3f, v5t-umami-6eb1dd711f, v5t-umami-ad293dc85a

## 개선 후 (import 경로 해석, 인증 제외, 권한표 행 필터)

| project | 블록 수 | 직접 관련 | 간접 | 무관 | 잘못된 구현 | 직접+간접 비율 |
|---|---:|---:|---:|---:|---:|---:|
| ghost | 13 | 9 | 3 | 1 | 0 | 92% |
| rocketchat | 30 | 20 | 10 | 0 | 0 | 100% |
| umami | 15 | 3 | 9 | 3 | 0 | 80% |
| 전체 | 58 | 32 | 22 | 4 | 0 | 93% |

## 개선 전 (전역 이름 매칭)

| project | 블록 수 | 직접 관련 | 간접 | 무관 | 잘못된 구현 | 직접+간접 비율 |
|---|---:|---:|---:|---:|---:|---:|
| ghost | 102 | 8 | 4 | 5 | 85 | 12% |
| rocketchat | 147 | 34 | 11 | 9 | 93 | 31% |
| umami | 88 | 5 | 9 | 9 | 65 | 16% |
| 전체 | 337 | 47 | 24 | 23 | 243 | 21% |

## 프로젝트별 집계 (test_v5 283 전체, 개선 후)

### ctx4096

| project | n | 권한표 신규 / 기존 | 권한 흐름 신규 / 기존 | permissible 신규 / 기존 | 권한 정의 1종 이상 | 헬퍼 추가 | 블록 1개 이상 | 잘림 건수 | 블록 발견/유지 평균 | 미해석 이름(건수/이름 수) | 제외 사유 | 토큰 전/후 평균 | 후 최대 |
|---|---:|---|---|---|---:|---:|---:|---:|---|---|---|---|---:|
| ghost | 69 | 60 / 0 | 4 / 49 | 19 / 3 | 60 | 54 | 65 | 17 | 2.54 / 2.09 | 69 / 1100 | authentication 63, duplicate 157, ghost_permissions_false 7, helper_cap 0, no_authz_signal 1 | 3315 / 3753 | 4089 |
| rocketchat | 157 | 109 / 0 | 70 / 5 | 0 / 0 | 111 | 56 | 116 | 69 | 3.26 / 1.74 | 139 / 1003 | duplicate 6, helper_cap 0, no_authz_signal 7, type_signature 95 | 3580 / 3768 | 4087 |
| umami | 57 | 38 / 5 | 0 / 0 | 0 / 0 | 38 | 9 | 45 | 8 | 2.16 / 2.12 | 56 / 619 | authentication 23, duplicate 8, helper_cap 0, no_authz_signal 8, type_signature 9 | 3462 / 3760 | 4090 |

### ctx6144

| project | n | 권한표 신규 / 기존 | 권한 흐름 신규 / 기존 | permissible 신규 / 기존 | 권한 정의 1종 이상 | 헬퍼 추가 | 블록 1개 이상 | 잘림 건수 | 블록 발견/유지 평균 | 미해석 이름(건수/이름 수) | 제외 사유 | 토큰 전/후 평균 | 후 최대 |
|---|---:|---|---|---|---:|---:|---:|---:|---|---|---|---|---:|
| ghost | 69 | 60 / 0 | 11 / 49 | 19 / 3 | 60 | 64 | 65 | 0 | 2.54 / 2.54 | 69 / 1100 | authentication 63, duplicate 157, ghost_permissions_false 7, helper_cap 0, no_authz_signal 1 | 3315 / 3903 | 5179 |
| rocketchat | 157 | 111 / 0 | 73 / 5 | 0 / 0 | 113 | 97 | 118 | 0 | 3.26 / 3.26 | 139 / 1003 | duplicate 6, helper_cap 0, no_authz_signal 7, type_signature 95 | 3580 / 4015 | 5583 |
| umami | 57 | 38 / 5 | 0 / 0 | 0 / 0 | 38 | 10 | 45 | 0 | 2.16 / 2.16 | 56 / 619 | authentication 23, duplicate 8, helper_cap 0, no_authz_signal 8, type_signature 9 | 3462 / 3776 | 4214 |

## Ghost docName 탐지

docName 확인 69/69 (발췌 또는 엔드포인트 파일). 권한표 미포함 Ghost 건: v5t-ghost-833ad427ba(POST /ghost/api/admin/images/upload/), v5t-ghost-a1ea7c67cd(GET /ghost/api/admin/config/), v5t-ghost-00fb8d537d(POST /ghost/api/admin/authentication/invitation/), v5t-ghost-0cbaf4100c(GET /ghost/api/admin/authentication/setup/), v5t-ghost-6e1dca8d3d(PUT /ghost/api/admin/authentication/password_reset/), v5t-ghost-81aa11ba50(GET /ghost/api/admin/authentication/invitation/), v5t-ghost-a322c4eaaa(POST /ghost/api/admin/session/), v5t-ghost-bae2ea5162(GET /ghost/api/admin/site/), v5t-ghost-d1a626ce9d(PUT /ghost/api/admin/schedules/{resource}/{id}/).
원인: gift_links는 엔드포인트가 docName 없이 `permissions(frame)` 함수에서 canThis(context).manage.gift_link / edit.post를 직접 호출한다 → canThis 체인에서 객체(gift_link, post)를 읽어 권한표를 만들도록 변경. 나머지 미포함 건은 permissions 설정이 없는 엔드포인트(인증 전용 라우트·authentication 계열)다.

## 30건 블록 목록 (개선 후, ctx4096 유지 블록)

| id | method path | kind | name | 위치 | depth | 1차 | 최종 | 비고 |
|---|---|---|---|---|---:|---|---|---|
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | perm_table | rolePermissions[post] | ghost/core/server/services/permissions/permissions-data.ts:1-235 | 1 | direct | direct |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | permissible | post.permissible | ghost/core/server/models/post.js:1530-1600 | 1 | direct | direct |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | perm_table | rolePermissions[gift_link,post] | ghost/core/server/services/permissions/permissions-data.ts:1-235 | 1 | direct | direct |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | permissible | post.permissible | ghost/core/server/models/post.js:1530-1600 | 1 | direct | direct |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | permissible | post.permissible | ghost/core/server/models/relations/authors.js:340-453 | 1 | direct | direct |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | perm_table | rolePermissions[theme] | ghost/core/server/services/permissions/permissions-data.ts:1-235 | 1 | direct | direct |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | tokenPermissionCheck | ghost/core/server/web/api/endpoints/admin/middleware.js:17-101 | 1 | indirect | indirect |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | perm_table | rolePermissions[upgrade] | ghost/core/server/services/permissions/permissions-data.ts:1-235 | 1 | direct | direct |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | tokenPermissionCheck | ghost/core/server/web/api/endpoints/admin/middleware.js:17-101 | 1 | indirect | indirect |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | perm_table | rolePermissions[user] | ghost/core/server/services/permissions/permissions-data.ts:1-235 | 1 | direct | direct |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | permissible | user.permissible | ghost/core/server/models/user.js:876-1083 | 1 | direct | direct |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | mw.authAdminApi | ghost/core/server/web/api/endpoints/admin/middleware.js:110-118 | 1 | indirect | indirect |  |
| v5t-ghost-0cbaf4100c | GET /ghost/api/admin/authentication/setup/ | helper | isSetup | ghost/core/server/api/endpoints/authentication.js:120-141 | 1 | direct | irrelevant | 핸들러 자신(isSetup) 재수록, 인가 조건 없음 |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | perm_flow | roomAccessValidators | packages/authorization/src/canAccessRoom.ts:24-106 | 1 | direct | direct |  |
| v5t-rocketchat-f5874fe2eb | GET /api/v1/groups.online | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-f5874fe2eb | GET /api/v1/groups.online | perm_flow | roomAccessValidators | packages/authorization/src/canAccessRoom.ts:24-106 | 1 | direct | direct |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | perm_flow | roomAccessValidators | packages/authorization/src/canAccessRoom.ts:24-106 | 1 | direct | direct |  |
| v5t-rocketchat-0d4fa14e85 | POST /api/v1/teams.addMembers | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-0d4fa14e85 | POST /api/v1/teams.addMembers | helper | hasAtLeastOnePermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:20-24 | 1 | indirect | indirect |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | perm_flow | roomAccessValidators | packages/authorization/src/canAccessRoom.ts:24-106 | 1 | direct | direct |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | perm_flow | roomAccessValidators | packages/authorization/src/canAccessRoom.ts:24-106 | 1 | direct | direct |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | perm_flow | roomAccessValidators | packages/authorization/src/canAccessRoom.ts:24-106 | 1 | direct | direct |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | perm_flow | checkPermissions(permissionsRequired) | apps/meteor/server/api/api.helpers.ts:75-110 | 1 | indirect | indirect |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | helper | hasAllPermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:10-14 | 1 | indirect | indirect |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | helper | hasAtLeastOnePermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:20-24 | 1 | indirect | indirect |  |
| v5t-rocketchat-fd924826e6 | GET /api/v1/channels.info | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-fd924826e6 | GET /api/v1/channels.info | perm_flow | roomAccessValidators | packages/authorization/src/canAccessRoom.ts:24-106 | 1 | direct | direct |  |
| v5t-rocketchat-0a75eb9b8b | POST /api/v1/channels.addModerator | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-0a75eb9b8b | POST /api/v1/channels.addModerator | helper | hasPermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:15-19 | 1 | indirect | indirect |  |
| v5t-rocketchat-ecefcc9d2c | GET /api/v1/integrations.history | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-ecefcc9d2c | GET /api/v1/integrations.history | perm_flow | checkPermissions(permissionsRequired) | apps/meteor/server/api/api.helpers.ts:75-110 | 1 | indirect | indirect |  |
| v5t-rocketchat-ecefcc9d2c | GET /api/v1/integrations.history | helper | hasPermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:15-19 | 1 | indirect | indirect |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | perm_flow | checkPermissions(permissionsRequired) | apps/meteor/server/api/api.helpers.ts:75-110 | 1 | indirect | indirect |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | hasAllPermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:10-14 | 1 | indirect | indirect |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | hasAtLeastOnePermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:20-24 | 1 | indirect | indirect |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | oauthAppsEndpoints | apps/meteor/server/api/v1/oauthapps.ts:120-164 | 1 | direct | direct |  |
| v5t-umami-bdd6ebb218 | GET /api/share/id/{shareId} | perm_table | ROLES | src/lib/constants.ts:174-182 | 2 | indirect | indirect |  |
| v5t-umami-bdd6ebb218 | GET /api/share/id/{shareId} | perm_table | PERMISSIONS | src/lib/constants.ts:191-201 | 2 | indirect | indirect |  |
| v5t-umami-bdd6ebb218 | GET /api/share/id/{shareId} | perm_table | ROLE_PERMISSIONS | src/lib/constants.ts:203-234 | 2 | direct | direct |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | perm_table | ROLES | src/lib/constants.ts:174-182 | 2 | indirect | indirect |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | perm_table | PERMISSIONS | src/lib/constants.ts:191-201 | 2 | indirect | indirect |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | perm_table | ROLE_PERMISSIONS | src/lib/constants.ts:203-234 | 2 | direct | direct |  |
| v5t-umami-640719b3b2 | GET /api/websites/{websiteId}/recorder | helper | checkAuth | src/lib/auth.ts:71-147 | 1 | irrelevant | irrelevant | checkAuth: 토큰·세션 파싱(인증) |
| v5t-umami-640719b3b2 | GET /api/websites/{websiteId}/recorder | helper | checkApiKeyAuth | src/lib/auth.ts:32-69 | 2 | indirect | irrelevant | checkApiKeyAuth: API 키 인증 |
| v5t-umami-29da074b3f | POST /api/teams | perm_table | ROLES | src/lib/constants.ts:174-182 | 2 | indirect | indirect |  |
| v5t-umami-29da074b3f | POST /api/teams | perm_table | PERMISSIONS | src/lib/constants.ts:191-201 | 2 | indirect | indirect |  |
| v5t-umami-6eb1dd711f | GET /api/users/{userId}/websites | helper | getAllUserWebsitesIncludingTeamAccess | src/queries/prisma/website.ts:122-147 | 1 | direct | indirect | 팀 접근 포함 웹사이트 조회 쿼리 — 데이터 범위이지 결정 조건은 아님 |
| v5t-umami-ad293dc85a | GET /api/admin/websites | perm_table | ROLES | src/lib/constants.ts:174-182 | 2 | indirect | indirect |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | perm_table | PERMISSIONS | src/lib/constants.ts:191-201 | 2 | indirect | indirect |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | perm_table | ROLE_PERMISSIONS | src/lib/constants.ts:203-234 | 2 | direct | direct |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | helper | members | src/app/api/admin/websites/route.ts:43-47 | 1 | direct | irrelevant | prisma include 객체(members where role)이지 인가 검사가 아님 |

## 30건 블록 목록 (개선 전)

| id | method path | kind | name | 위치 | depth | 1차 | 최종 | 비고 |
|---|---|---|---|---|---:|---|---|---|
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | perm_table | rolePermissions[post] | ghost/core/server/services/permissions/permissions-data.ts:1-235 | 1 | direct | direct |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | permissible | post.permissible | ghost/core/server/models/relations/authors.js:340-453 | 1 | direct | direct |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | permissible | post.permissible | ghost/core/server/models/post.js:1530-1600 | 1 | direct | direct |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | perm_flow | canThis(core) | ghost/core/server/services/permissions/can-this.js:35-121 | 1 | indirect | indirect |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | authors | ghost/core/server/models/relations/authors.js:192-192 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | authors | ghost/core/server/api/endpoints/utils/serializers/input/index.js:34-36 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | rolePermissions | ghost/core/server/services/permissions/index.js:5-5 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | Administrator | ghost/core/server/services/permissions/permissions-data.ts:66-109 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | Author | ghost/core/server/models/author.js:4-9 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | permissible | ghost/core/server/models/role.js:47-116 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | setIsRoles | ghost/core/server/models/role-utils.ts:34-58 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | isEdit | ghost/core/server/models/relations/authors.js:377-377 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | isEdit | ghost/core/server/models/post.js:1557-1557 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | isAdd | ghost/core/server/models/relations/authors.js:378-378 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | isAdd | ghost/core/server/models/integration.js:105-105 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | isDestroy | ghost/core/server/models/relations/authors.js:379-379 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | isDestroy | ghost/core/server/models/post.js:1559-1559 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | isChangingAuthors | ghost/core/server/models/relations/authors.js:381-391 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-244db7151d | DELETE /ghost/api/admin/pages/{id}/ | helper | isCoAuthor | ghost/core/server/models/relations/authors.js:404-409 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | authenticate | ghost/core/server/auth/api-key/admin.js:48-67 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | authenticate | ghost/core/server/auth/authenticate.js:5-13 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | authorize | ghost/core/server/auth/authorize.js:12-45 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | authorize | ghost/core/server/auth/index.js:2-4 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | authorizeAdminApi | ghost/core/server/auth/authorize.js:30-44 | 1 | irrelevant | irrelevant |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | tokenPermissionCheck | ghost/core/server/web/api/endpoints/admin/middleware.js:17-101 | 1 | indirect | indirect |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | permissionsService | ghost/core/server/api/endpoints/gift-links.ts:4-4 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | permissionsService | ghost/core/server/api/endpoints/member-metafields.ts:5-5 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | canThis | ghost/core/server/api/endpoints/utils/serializers/output/roles.js:2-2 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | isOwner | ghost/core/server/models/relations/authors.js:393-398 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | setIsRoles | ghost/core/server/models/role-utils.ts:34-58 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | userPermissions | ghost/core/server/services/permissions/can-this.js:21-21 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | checkPermission | ghost/core/server/services/permissions/can-this.js:27-34 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | permissible | ghost/core/server/models/relations/authors.js:340-453 | 1 | direct | direct |  |
| v5t-ghost-05ee24e847 | GET /ghost/api/admin/posts/{id}/gift_links/ | helper | permissible | ghost/core/server/models/role.js:47-116 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-6e1dca8d3d | PUT /ghost/api/admin/authentication/password_reset/ | perm_table | rolePermissions[authentication] | ghost/core/server/services/permissions/permissions-data.ts:1-235 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-6e1dca8d3d | PUT /ghost/api/admin/authentication/password_reset/ | perm_flow | canThis(core) | ghost/core/server/services/permissions/can-this.js:35-121 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-6e1dca8d3d | PUT /ghost/api/admin/authentication/password_reset/ | helper | authentication | ghost/core/server/api/endpoints/index.js:34-36 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-6e1dca8d3d | PUT /ghost/api/admin/authentication/password_reset/ | helper | authentication | ghost/core/server/api/endpoints/utils/serializers/output/index.js:27-29 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | perm_table | rolePermissions[theme] | ghost/core/server/services/permissions/permissions-data.ts:1-235 | 1 | direct | direct |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | authenticate | ghost/core/server/auth/api-key/admin.js:48-67 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | authenticate | ghost/core/server/auth/authenticate.js:5-13 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | authorize | ghost/core/server/auth/authorize.js:12-45 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | authorize | ghost/core/server/auth/index.js:2-4 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | authorizeAdminApi | ghost/core/server/auth/authorize.js:30-44 | 1 | irrelevant | irrelevant |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | tokenPermissionCheck | ghost/core/server/web/api/endpoints/admin/middleware.js:17-101 | 1 | indirect | indirect |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | isOwner | ghost/core/server/models/relations/authors.js:393-398 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | setIsRoles | ghost/core/server/models/role-utils.ts:34-58 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | userPermissions | ghost/core/server/services/permissions/can-this.js:21-21 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | checkPermission | ghost/core/server/services/permissions/can-this.js:27-34 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | permissible | ghost/core/server/models/relations/authors.js:340-453 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | permissible | ghost/core/server/models/role.js:47-116 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | rolePermissions | ghost/core/server/services/permissions/index.js:5-5 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | Administrator | ghost/core/server/services/permissions/permissions-data.ts:66-109 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-5f25be85a3 | POST /ghost/api/admin/themes/upload/ | helper | Author | ghost/core/server/models/author.js:4-9 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | authenticate | ghost/core/server/auth/api-key/admin.js:48-67 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | authenticate | ghost/core/server/auth/authenticate.js:5-13 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | authorize | ghost/core/server/auth/authorize.js:12-45 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | authorize | ghost/core/server/auth/index.js:2-4 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | authorizeAdminApi | ghost/core/server/auth/authorize.js:30-44 | 1 | irrelevant | irrelevant |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | tokenPermissionCheck | ghost/core/server/web/api/endpoints/admin/middleware.js:17-101 | 1 | indirect | indirect |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | isOwner | ghost/core/server/models/relations/authors.js:393-398 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | setIsRoles | ghost/core/server/models/role-utils.ts:34-58 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | userPermissions | ghost/core/server/services/permissions/can-this.js:21-21 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | checkPermission | ghost/core/server/services/permissions/can-this.js:27-34 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | permissible | ghost/core/server/models/relations/authors.js:340-453 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | permissible | ghost/core/server/models/role.js:47-116 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | rolePermissions | ghost/core/server/services/permissions/index.js:5-5 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | Administrator | ghost/core/server/services/permissions/permissions-data.ts:66-109 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-56bc478d48 | POST /ghost/api/admin/upgrades/ | helper | wrappedAuthenticateWithToken | ghost/core/server/auth/api-key/admin.js:83-96 | 2 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | perm_table | rolePermissions[user] | ghost/core/server/services/permissions/permissions-data.ts:1-235 | 1 | direct | direct |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | permissible | user.permissible | ghost/core/server/models/user.js:876-1083 | 1 | direct | direct |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | isOwner | ghost/core/server/models/relations/authors.js:393-398 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | setIsRoles | ghost/core/server/models/role-utils.ts:34-58 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | userPermissions | ghost/core/server/services/permissions/can-this.js:21-21 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | checkPermission | ghost/core/server/services/permissions/can-this.js:27-34 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | permissible | ghost/core/server/models/relations/authors.js:340-453 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | permissible | ghost/core/server/models/role.js:47-116 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | rolePermissions | ghost/core/server/services/permissions/index.js:5-5 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | Administrator | ghost/core/server/services/permissions/permissions-data.ts:66-109 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | Author | ghost/core/server/models/author.js:4-9 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | Author | ghost/core/server/services/permissions/permissions-data.ts:204-220 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | hasRole | ghost/core/server/models/user.js:358-364 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | roleId | ghost/core/server/models/user.js:612-612 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | roleId | ghost/core/server/models/user.js:985-985 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | contextRoleId | ghost/core/server/models/user.js:988-988 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-3904cb1077 | PUT /ghost/api/admin/users/{id}/ | helper | authors | ghost/core/server/models/relations/authors.js:192-192 | 2 | wrong_impl | wrong_impl |  |
| v5t-ghost-a322c4eaaa | POST /ghost/api/admin/session/ | helper | hasLoggedIn | ghost/core/server/models/user.js:371-373 | 1 | wrong_impl | irrelevant | user.hasLoggedIn(): 핸들러가 실제 호출하는 메서드이나 로그인 여부 플래그(인증) |
| v5t-ghost-a322c4eaaa | POST /ghost/api/admin/session/ | helper | check | ghost/core/server/api/endpoints/recommendations.js:47-60 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-a322c4eaaa | POST /ghost/api/admin/session/ | helper | check | ghost/core/server/models/user.js:1087-1130 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-a322c4eaaa | POST /ghost/api/admin/session/ | helper | authentication | ghost/core/server/api/endpoints/index.js:34-36 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-a322c4eaaa | POST /ghost/api/admin/session/ | helper | authentication | ghost/core/server/api/endpoints/utils/serializers/output/index.js:27-29 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-a322c4eaaa | POST /ghost/api/admin/session/ | helper | isLocked | ghost/core/server/models/user.js:195-197 | 2 | wrong_impl | wrong_impl |  |
| v5t-ghost-a322c4eaaa | POST /ghost/api/admin/session/ | helper | isInactive | ghost/core/server/models/user.js:218-220 | 2 | wrong_impl | wrong_impl |  |
| v5t-ghost-a322c4eaaa | POST /ghost/api/admin/session/ | helper | isPasswordCorrect | ghost/core/server/models/user.js:1132-1158 | 2 | wrong_impl | wrong_impl |  |
| v5t-ghost-a322c4eaaa | POST /ghost/api/admin/session/ | helper | hashedPassword | ghost/core/server/models/user.js:1134-1134 | 2 | wrong_impl | wrong_impl |  |
| v5t-ghost-0cbaf4100c | GET /ghost/api/admin/authentication/setup/ | perm_table | rolePermissions[authentication] | ghost/core/server/services/permissions/permissions-data.ts:1-235 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-0cbaf4100c | GET /ghost/api/admin/authentication/setup/ | perm_flow | canThis(core) | ghost/core/server/services/permissions/can-this.js:35-121 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-0cbaf4100c | GET /ghost/api/admin/authentication/setup/ | helper | authentication | ghost/core/server/api/endpoints/index.js:34-36 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-0cbaf4100c | GET /ghost/api/admin/authentication/setup/ | helper | authentication | ghost/core/server/api/endpoints/utils/serializers/output/index.js:27-29 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-0cbaf4100c | GET /ghost/api/admin/authentication/setup/ | helper | isSetup | ghost/core/server/api/endpoints/authentication.js:120-141 | 1 | direct | direct |  |
| v5t-ghost-0cbaf4100c | GET /ghost/api/admin/authentication/setup/ | helper | isSetup | ghost/core/server/api/endpoints/authentication.js:126-126 | 1 | wrong_impl | wrong_impl |  |
| v5t-ghost-0cbaf4100c | GET /ghost/api/admin/authentication/setup/ | helper | checkIsSetup | ghost/core/server/auth/setup.js:32-34 | 1 | irrelevant | irrelevant |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | perm_flow | canAccessRoom | apps/meteor/server/lib/omnichannel/roomAccessValidator.internalService.ts:12-20 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | perm_flow | hasPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:24-24 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | perm_flow | roomAccessValidators | packages/authorization/src/canAccessRoom.ts:24-106 | 1 | direct | direct |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | perm_flow | canAccessPublicRoom | packages/authorization/src/canAccessRoom.ts:9-16 | 2 | direct | direct |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | perm_flow | canAccessRoomLivechat | packages/authorization/src/canAccessRoomLivechat.ts:8-31 | 2 | direct | direct |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | helper | removeRoomOwner | apps/meteor/server/meteor-methods/rooms/removeRoomOwner.ts:109-120 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | helper | canAccessRoomAsync | apps/meteor/server/lib/authorization/canAccessRoom.ts:3-3 | 1 | irrelevant | irrelevant |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | helper | check | apps/meteor/server/lib/utils/functions/isDocker.ts:20-22 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | helper | hasPermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:15-19 | 1 | indirect | indirect |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | helper | canAccessRoom | packages/authorization/src/Authorization.ts:83-85 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | helper | hasDockerEnv | apps/meteor/server/lib/utils/functions/isDocker.ts:3-10 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | helper | hasDockerCGroup | apps/meteor/server/lib/utils/functions/isDocker.ts:12-18 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | helper | permissionId | apps/meteor/server/lib/authorization/upsertPermissions.ts:51-51 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-258c4c7f6e | POST /api/v1/groups.removeOwner | helper | hasPermission | packages/authorization/src/Authorization.ts:69-74 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-f5874fe2eb | GET /api/v1/groups.online | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-f5874fe2eb | GET /api/v1/groups.online | perm_flow | hasPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:24-24 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-f5874fe2eb | GET /api/v1/groups.online | perm_flow | canAccessRoom | apps/meteor/server/lib/omnichannel/roomAccessValidator.internalService.ts:12-20 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-f5874fe2eb | GET /api/v1/groups.online | perm_flow | roomAccessValidators | packages/authorization/src/canAccessRoom.ts:24-106 | 1 | direct | direct |  |
| v5t-rocketchat-f5874fe2eb | GET /api/v1/groups.online | perm_flow | canAccessPublicRoom | packages/authorization/src/canAccessRoom.ts:9-16 | 2 | direct | direct |  |
| v5t-rocketchat-f5874fe2eb | GET /api/v1/groups.online | perm_flow | canAccessRoomLivechat | packages/authorization/src/canAccessRoomLivechat.ts:8-31 | 2 | direct | direct |  |
| v5t-rocketchat-f5874fe2eb | GET /api/v1/groups.online | helper | canAccessRoomAsync | apps/meteor/server/lib/authorization/canAccessRoom.ts:3-3 | 1 | irrelevant | irrelevant |  |
| v5t-rocketchat-f5874fe2eb | GET /api/v1/groups.online | helper | hasPermission | packages/authorization/src/Authorization.ts:69-74 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-f5874fe2eb | GET /api/v1/groups.online | helper | canAccessRoom | packages/authorization/src/Authorization.ts:83-85 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-f5874fe2eb | GET /api/v1/groups.online | helper | permissionId | apps/meteor/server/lib/authorization/upsertPermissions.ts:51-51 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | perm_flow | canAccessRoom | apps/meteor/server/lib/omnichannel/roomAccessValidator.internalService.ts:12-20 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | perm_flow | hasPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:24-24 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | perm_flow | roomAccessValidators | packages/authorization/src/canAccessRoom.ts:24-106 | 1 | direct | direct |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | perm_flow | canAccessPublicRoom | packages/authorization/src/canAccessRoom.ts:9-16 | 2 | direct | direct |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | perm_flow | canAccessRoomLivechat | packages/authorization/src/canAccessRoomLivechat.ts:8-31 | 2 | direct | direct |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | helper | check | apps/meteor/server/lib/utils/functions/isDocker.ts:20-22 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | helper | canReadRoom | packages/authorization/src/Authorization.ts:87-89 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | helper | isPartialUser | packages/authorization/src/canAccessRoom.ts:108-110 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | helper | canAccessRoom | packages/authorization/src/Authorization.ts:83-85 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | helper | hasPermission | packages/authorization/src/Authorization.ts:69-74 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | helper | hasDockerEnv | apps/meteor/server/lib/utils/functions/isDocker.ts:3-10 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | helper | hasDockerCGroup | apps/meteor/server/lib/utils/functions/isDocker.ts:12-18 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-b29bfcff96 | GET /api/v1/channels.history | helper | permissionId | apps/meteor/server/lib/authorization/upsertPermissions.ts:51-51 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0d4fa14e85 | POST /api/v1/teams.addMembers | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-0d4fa14e85 | POST /api/v1/teams.addMembers | helper | addMembers | apps/meteor/server/services/team/service.ts:702-737 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0d4fa14e85 | POST /api/v1/teams.addMembers | helper | members | apps/meteor/server/api/v1/channels.ts:809-809 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0d4fa14e85 | POST /api/v1/teams.addMembers | helper | members | apps/meteor/server/api/v1/channels.ts:961-961 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0d4fa14e85 | POST /api/v1/teams.addMembers | helper | hasAtLeastOnePermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:20-24 | 1 | indirect | indirect |  |
| v5t-rocketchat-0d4fa14e85 | POST /api/v1/teams.addMembers | helper | isRoleAddedToTeam | apps/meteor/server/services/team/service.ts:720-720 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0d4fa14e85 | POST /api/v1/teams.addMembers | helper | addRolesToMember | apps/meteor/server/services/team/service.ts:935-939 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0d4fa14e85 | POST /api/v1/teams.addMembers | helper | isRoleAddedToSubscription | apps/meteor/server/services/team/service.ts:721-721 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0d4fa14e85 | POST /api/v1/teams.addMembers | helper | addRolesToSubscription | apps/meteor/server/services/team/service.ts:941-945 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0d4fa14e85 | POST /api/v1/teams.addMembers | helper | hasAtLeastOnePermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:22-22 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0d4fa14e85 | POST /api/v1/teams.addMembers | helper | hasAtLeastOnePermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:87-87 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | perm_flow | hasPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:24-24 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | perm_flow | roomAccessValidators | packages/authorization/src/canAccessRoom.ts:24-106 | 1 | direct | direct |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | perm_flow | canAccessPublicRoom | packages/authorization/src/canAccessRoom.ts:9-16 | 2 | direct | direct |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | perm_flow | canAccessRoom | apps/meteor/server/lib/omnichannel/roomAccessValidator.internalService.ts:12-20 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | perm_flow | canAccessRoomLivechat | packages/authorization/src/canAccessRoomLivechat.ts:8-31 | 2 | direct | direct |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | helper | hasPermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:15-19 | 1 | indirect | indirect |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | helper | members | apps/meteor/server/api/v1/channels.ts:809-809 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | helper | members | apps/meteor/server/api/v1/channels.ts:961-961 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | helper | canAccess | apps/meteor/server/api/v1/im.ts:177-178 | 1 | direct | direct |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | helper | canAccess | apps/meteor/server/api/v1/im.ts:207-207 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | helper | canAccessRoomIdAsync | apps/meteor/server/lib/authorization/canAccessRoom.ts:4-4 | 1 | irrelevant | irrelevant |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | helper | permissionId | apps/meteor/server/lib/authorization/upsertPermissions.ts:51-51 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | helper | hasPermission | packages/authorization/src/Authorization.ts:69-74 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-25c4e3c534 | GET /api/v1/im.counters | helper | canAccessRoomId | packages/authorization/src/Authorization.ts:91-107 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | perm_flow | hasPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:24-24 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | perm_flow | roomAccessValidators | packages/authorization/src/canAccessRoom.ts:24-106 | 1 | direct | direct |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | perm_flow | canAccessPublicRoom | packages/authorization/src/canAccessRoom.ts:9-16 | 2 | direct | direct |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | perm_flow | canAccessRoom | apps/meteor/server/lib/omnichannel/roomAccessValidator.internalService.ts:12-20 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | perm_flow | canAccessRoomLivechat | packages/authorization/src/canAccessRoomLivechat.ts:8-31 | 2 | direct | direct |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | helper | canAccess | apps/meteor/server/api/v1/im.ts:207-207 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | helper | canAccessRoomIdAsync | apps/meteor/server/lib/authorization/canAccessRoom.ts:4-4 | 1 | irrelevant | irrelevant |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | helper | hasPermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:15-19 | 1 | indirect | indirect |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | helper | permissionId | apps/meteor/server/lib/authorization/upsertPermissions.ts:51-51 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | helper | hasPermission | packages/authorization/src/Authorization.ts:69-74 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | helper | canAccessRoomId | packages/authorization/src/Authorization.ts:91-107 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-61d5e55ae2 | POST /api/v1/im.delete | helper | getSettingPermissionId | apps/meteor/app/authorization/lib/index.ts:3-6 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | perm_flow | canAccessRoom | apps/meteor/server/lib/omnichannel/roomAccessValidator.internalService.ts:12-20 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | perm_flow | roomAccessValidators | packages/authorization/src/canAccessRoom.ts:24-106 | 1 | direct | direct |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | perm_flow | canAccessPublicRoom | packages/authorization/src/canAccessRoom.ts:9-16 | 2 | direct | direct |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | perm_flow | hasPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:24-24 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | perm_flow | canAccessRoomLivechat | packages/authorization/src/canAccessRoomLivechat.ts:8-31 | 2 | direct | direct |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | helper | hasAllPermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:10-14 | 1 | indirect | indirect |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | helper | members | apps/meteor/server/api/v1/channels.ts:809-809 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | helper | members | apps/meteor/server/api/v1/channels.ts:961-961 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | helper | canAccessRoomAsync | apps/meteor/server/lib/authorization/canAccessRoom.ts:3-3 | 1 | irrelevant | irrelevant |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | helper | hasAllPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:21-21 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | helper | hasAllPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:84-84 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-64704a55de | POST /api/v1/groups.convertToTeam | helper | canAccessRoom | packages/authorization/src/Authorization.ts:83-85 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | helper | permissionsRequired | apps/meteor/server/api/v1/channels.ts:1276-1286 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | helper | permissionsRequired | apps/meteor/server/api/v1/channels.ts:1433-1435 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | helper | members | apps/meteor/server/api/v1/channels.ts:809-809 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | helper | members | apps/meteor/server/api/v1/channels.ts:961-961 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | helper | hasAllPermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:10-14 | 1 | indirect | indirect |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | helper | hasAny | apps/meteor/server/lib/users/setUsername.ts:26-26 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | helper | hasAtLeastOnePermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:20-24 | 1 | indirect | indirect |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | helper | hasAllPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:21-21 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | helper | hasAllPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:84-84 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | helper | hasAtLeastOnePermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:22-22 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-cdf09d2caa | POST /api/v1/teams.create | helper | hasAtLeastOnePermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:87-87 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-fd924826e6 | GET /api/v1/channels.info | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-fd924826e6 | GET /api/v1/channels.info | perm_flow | hasPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:24-24 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-fd924826e6 | GET /api/v1/channels.info | perm_flow | canAccessRoom | apps/meteor/server/lib/omnichannel/roomAccessValidator.internalService.ts:12-20 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-fd924826e6 | GET /api/v1/channels.info | perm_flow | roomAccessValidators | packages/authorization/src/canAccessRoom.ts:24-106 | 1 | direct | direct |  |
| v5t-rocketchat-fd924826e6 | GET /api/v1/channels.info | perm_flow | canAccessRoomLivechat | packages/authorization/src/canAccessRoomLivechat.ts:8-31 | 2 | direct | direct |  |
| v5t-rocketchat-fd924826e6 | GET /api/v1/channels.info | helper | canAccessRoomAsync | apps/meteor/server/lib/authorization/canAccessRoom.ts:3-3 | 1 | irrelevant | irrelevant |  |
| v5t-rocketchat-fd924826e6 | GET /api/v1/channels.info | helper | hasPermission | packages/authorization/src/Authorization.ts:69-74 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-fd924826e6 | GET /api/v1/channels.info | helper | canAccessRoom | packages/authorization/src/Authorization.ts:83-85 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-fd924826e6 | GET /api/v1/channels.info | helper | permissionId | apps/meteor/server/lib/authorization/upsertPermissions.ts:51-51 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0a75eb9b8b | POST /api/v1/channels.addModerator | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-0a75eb9b8b | POST /api/v1/channels.addModerator | helper | check | apps/meteor/server/lib/utils/functions/isDocker.ts:20-22 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0a75eb9b8b | POST /api/v1/channels.addModerator | helper | isFederated | apps/meteor/server/meteor-methods/rooms/addRoomModerator.ts:35-35 | 1 | irrelevant | irrelevant |  |
| v5t-rocketchat-0a75eb9b8b | POST /api/v1/channels.addModerator | helper | isFederated | apps/meteor/server/meteor-methods/rooms/addRoomOwner.ts:35-35 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0a75eb9b8b | POST /api/v1/channels.addModerator | helper | hasPermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:15-19 | 1 | indirect | indirect |  |
| v5t-rocketchat-0a75eb9b8b | POST /api/v1/channels.addModerator | helper | hasDockerEnv | apps/meteor/server/lib/utils/functions/isDocker.ts:3-10 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0a75eb9b8b | POST /api/v1/channels.addModerator | helper | hasDockerCGroup | apps/meteor/server/lib/utils/functions/isDocker.ts:12-18 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0a75eb9b8b | POST /api/v1/channels.addModerator | helper | permissionId | apps/meteor/server/lib/authorization/upsertPermissions.ts:51-51 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0a75eb9b8b | POST /api/v1/channels.addModerator | helper | hasPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:24-24 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-0a75eb9b8b | POST /api/v1/channels.addModerator | helper | hasPermission | packages/authorization/src/Authorization.ts:69-74 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-ecefcc9d2c | GET /api/v1/integrations.history | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-ecefcc9d2c | GET /api/v1/integrations.history | helper | permissionsRequired | apps/meteor/server/api/v1/channels.ts:1433-1435 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-ecefcc9d2c | GET /api/v1/integrations.history | helper | hasAny | apps/meteor/server/lib/users/setUsername.ts:26-26 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-ecefcc9d2c | GET /api/v1/integrations.history | helper | canViewOnlyOwnOutgoingIntegrations | apps/meteor/server/lib/integrations/lib/mountQueriesBasedOnPermission.ts:13-13 | 1 | irrelevant | irrelevant |  |
| v5t-rocketchat-ecefcc9d2c | GET /api/v1/integrations.history | helper | canViewOnlyOwnOutgoingIntegrations | apps/meteor/server/lib/integrations/lib/mountQueriesBasedOnPermission.ts:49-49 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-ecefcc9d2c | GET /api/v1/integrations.history | helper | hasPermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:15-19 | 1 | indirect | indirect |  |
| v5t-rocketchat-ecefcc9d2c | GET /api/v1/integrations.history | helper | canViewAllOutgoingIntegrations | apps/meteor/server/lib/integrations/lib/mountQueriesBasedOnPermission.ts:11-11 | 1 | irrelevant | irrelevant |  |
| v5t-rocketchat-ecefcc9d2c | GET /api/v1/integrations.history | helper | canViewAllOutgoingIntegrations | apps/meteor/server/lib/integrations/lib/mountQueriesBasedOnPermission.ts:50-50 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-ecefcc9d2c | GET /api/v1/integrations.history | helper | permissionId | apps/meteor/server/lib/authorization/upsertPermissions.ts:51-51 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-ecefcc9d2c | GET /api/v1/integrations.history | helper | hasPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:24-24 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-ecefcc9d2c | GET /api/v1/integrations.history | helper | hasPermission | packages/authorization/src/Authorization.ts:69-74 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | perm_table | permission→roles | apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 | 1 | direct | direct |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | oauth | apps/meteor/server/lib/statistics/lib/getServicesStatistics.ts:87-141 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | permissionsRequired | apps/meteor/server/api/v1/channels.ts:1276-1286 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | permissionsRequired | apps/meteor/server/api/v1/channels.ts:1433-1435 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | OAuthApps | packages/models/src/index.ts:175-175 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | hasAllPermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:10-14 | 1 | indirect | indirect |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | hasAny | apps/meteor/server/lib/users/setUsername.ts:26-26 | 1 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | hasAtLeastOnePermissionAsync | apps/meteor/server/lib/authorization/hasPermission.ts:20-24 | 1 | indirect | indirect |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | oauthAppsEndpoints | apps/meteor/server/api/v1/oauthapps.ts:120-164 | 1 | direct | direct |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | getCustomOAuthServices | apps/meteor/server/lib/statistics/lib/getServicesStatistics.ts:9-16 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | hasAllPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:21-21 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | hasAllPermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:84-84 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | hasAtLeastOnePermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:22-22 | 2 | wrong_impl | wrong_impl |  |
| v5t-rocketchat-5b6c0ebf4d | GET /api/v1/oauth-apps.list | helper | hasAtLeastOnePermission | apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:87-87 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-bdd6ebb218 | GET /api/share/id/{shareId} | perm_table | ROLES | src/lib/constants.ts:174-182 | 1 | indirect | indirect |  |
| v5t-umami-bdd6ebb218 | GET /api/share/id/{shareId} | perm_table | PERMISSIONS | src/lib/constants.ts:191-201 | 2 | indirect | indirect |  |
| v5t-umami-bdd6ebb218 | GET /api/share/id/{shareId} | perm_table | ROLE_PERMISSIONS | src/lib/constants.ts:203-234 | 2 | direct | direct |  |
| v5t-umami-bdd6ebb218 | GET /api/share/id/{shareId} | helper | isApiKeyEnabled | src/lib/api-key.ts:40-42 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-bdd6ebb218 | GET /api/share/id/{shareId} | helper | isApiKey | src/lib/api-key.ts:32-34 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-bdd6ebb218 | GET /api/share/id/{shareId} | helper | checkApiKeyAuth | src/lib/auth.ts:32-69 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-bdd6ebb218 | GET /api/share/id/{shareId} | helper | authKey | src/lib/auth.ts:150-150 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-bdd6ebb218 | GET /api/share/id/{shareId} | helper | isApiKeyBlockedPath | src/lib/api-key.ts:36-38 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-bdd6ebb218 | GET /api/share/id/{shareId} | helper | hashApiKey | src/lib/api-key.ts:24-26 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-bdd6ebb218 | GET /api/share/id/{shareId} | helper | teamOwner | src/app/api/share/[slug]/route.ts:21-29 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-bdd6ebb218 | GET /api/share/id/{shareId} | helper | createAuthKey | src/lib/crypto.ts:68-70 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | perm_table | ROLES | src/lib/constants.ts:174-182 | 1 | indirect | indirect |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | perm_table | PERMISSIONS | src/lib/constants.ts:191-201 | 2 | indirect | indirect |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | perm_table | ROLE_PERMISSIONS | src/lib/constants.ts:203-234 | 2 | direct | direct |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | perm_flow | canViewWebsite | src/permissions/website.ts:8-41 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | helper | isApiKeyEnabled | src/lib/api-key.ts:40-42 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | helper | isApiKey | src/lib/api-key.ts:32-34 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | helper | checkApiKeyAuth | src/lib/auth.ts:32-69 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | helper | authKey | src/lib/auth.ts:150-150 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | helper | isApiKeyBlockedPath | src/lib/api-key.ts:36-38 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | helper | hashApiKey | src/lib/api-key.ts:24-26 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | helper | teamOwner | src/app/api/share/[slug]/route.ts:21-29 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-b5fb9b9198 | GET /api/websites/{websiteId}/goals/{goalId} | helper | createAuthKey | src/lib/crypto.ts:68-70 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-bd9e54d1f1 | POST /api/me/password | helper | checkPassword | src/lib/password.ts:9-11 | 1 | irrelevant | irrelevant |  |
| v5t-umami-bd9e54d1f1 | POST /api/me/password | helper | hashPassword | src/lib/password.ts:5-7 | 1 | irrelevant | irrelevant |  |
| v5t-umami-bd9e54d1f1 | POST /api/me/password | helper | isApiKeyEnabled | src/lib/api-key.ts:40-42 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-bd9e54d1f1 | POST /api/me/password | helper | isApiKey | src/lib/api-key.ts:32-34 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-bd9e54d1f1 | POST /api/me/password | helper | checkApiKeyAuth | src/lib/auth.ts:32-69 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-bd9e54d1f1 | POST /api/me/password | helper | ROLES | src/lib/constants.ts:174-182 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-bd9e54d1f1 | POST /api/me/password | helper | authKey | src/lib/auth.ts:150-150 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-bd9e54d1f1 | POST /api/me/password | helper | isApiKeyBlockedPath | src/lib/api-key.ts:36-38 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-bd9e54d1f1 | POST /api/me/password | helper | hashApiKey | src/lib/api-key.ts:24-26 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-bd9e54d1f1 | POST /api/me/password | helper | teamOwner | src/app/api/share/[slug]/route.ts:21-29 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-bd9e54d1f1 | POST /api/me/password | helper | createAuthKey | src/lib/crypto.ts:68-70 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-a8feaa9ffc | GET /api/me | helper | isApiKeyEnabled | src/lib/api-key.ts:40-42 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-a8feaa9ffc | GET /api/me | helper | isApiKey | src/lib/api-key.ts:32-34 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-a8feaa9ffc | GET /api/me | helper | checkApiKeyAuth | src/lib/auth.ts:32-69 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-a8feaa9ffc | GET /api/me | helper | authKey | src/lib/auth.ts:150-150 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-a8feaa9ffc | GET /api/me | helper | ROLES | src/lib/constants.ts:174-182 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-a8feaa9ffc | GET /api/me | helper | isApiKeyBlockedPath | src/lib/api-key.ts:36-38 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-a8feaa9ffc | GET /api/me | helper | hashApiKey | src/lib/api-key.ts:24-26 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-a8feaa9ffc | GET /api/me | helper | createAuthKey | src/lib/crypto.ts:68-70 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-a8feaa9ffc | GET /api/me | helper | teamOwner | src/app/api/share/[slug]/route.ts:21-29 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-640719b3b2 | GET /api/websites/{websiteId}/recorder | helper | checkAuth | src/lib/auth.ts:71-147 | 1 | irrelevant | irrelevant |  |
| v5t-umami-640719b3b2 | GET /api/websites/{websiteId}/recorder | helper | isApiKeyEnabled | src/lib/api-key.ts:40-42 | 2 | irrelevant | irrelevant |  |
| v5t-umami-640719b3b2 | GET /api/websites/{websiteId}/recorder | helper | isApiKey | src/lib/api-key.ts:32-34 | 2 | irrelevant | irrelevant |  |
| v5t-umami-640719b3b2 | GET /api/websites/{websiteId}/recorder | helper | checkApiKeyAuth | src/lib/auth.ts:32-69 | 2 | indirect | indirect |  |
| v5t-umami-640719b3b2 | GET /api/websites/{websiteId}/recorder | helper | PARTIAL_AUTH_TOKEN_TYPE | src/lib/constants.ts:15-15 | 2 | irrelevant | irrelevant |  |
| v5t-umami-640719b3b2 | GET /api/websites/{websiteId}/recorder | helper | authKey | src/lib/auth.ts:150-150 | 2 | irrelevant | irrelevant |  |
| v5t-umami-640719b3b2 | GET /api/websites/{websiteId}/recorder | helper | hash | src/lib/crypto.ts:48-50 | 2 | irrelevant | irrelevant |  |
| v5t-umami-640719b3b2 | GET /api/websites/{websiteId}/recorder | helper | hash | src/lib/format.ts:76-76 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-29da074b3f | POST /api/teams | perm_table | ROLES | src/lib/constants.ts:174-182 | 1 | indirect | indirect |  |
| v5t-umami-29da074b3f | POST /api/teams | perm_table | PERMISSIONS | src/lib/constants.ts:191-201 | 1 | indirect | indirect |  |
| v5t-umami-29da074b3f | POST /api/teams | helper | teamOwnerId | src/app/api/teams/route.ts:51-51 | 1 | irrelevant | irrelevant |  |
| v5t-umami-29da074b3f | POST /api/teams | helper | isApiKeyEnabled | src/lib/api-key.ts:40-42 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-29da074b3f | POST /api/teams | helper | isApiKey | src/lib/api-key.ts:32-34 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-29da074b3f | POST /api/teams | helper | checkApiKeyAuth | src/lib/auth.ts:32-69 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-29da074b3f | POST /api/teams | helper | authKey | src/lib/auth.ts:150-150 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-29da074b3f | POST /api/teams | helper | ensureArray | src/lib/utils.ts:42-46 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-29da074b3f | POST /api/teams | helper | teamOwner | src/app/api/share/[slug]/route.ts:21-29 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-29da074b3f | POST /api/teams | helper | isApiKeyBlockedPath | src/lib/api-key.ts:36-38 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-29da074b3f | POST /api/teams | helper | hashApiKey | src/lib/api-key.ts:24-26 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-29da074b3f | POST /api/teams | helper | createAuthKey | src/lib/crypto.ts:68-70 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-6eb1dd711f | GET /api/users/{userId}/websites | helper | getAllUserWebsitesIncludingTeamAccess | src/queries/prisma/website.ts:122-147 | 1 | direct | direct |  |
| v5t-umami-6eb1dd711f | GET /api/users/{userId}/websites | helper | isApiKeyEnabled | src/lib/api-key.ts:40-42 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-6eb1dd711f | GET /api/users/{userId}/websites | helper | isApiKey | src/lib/api-key.ts:32-34 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-6eb1dd711f | GET /api/users/{userId}/websites | helper | checkApiKeyAuth | src/lib/auth.ts:32-69 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-6eb1dd711f | GET /api/users/{userId}/websites | helper | ROLES | src/lib/constants.ts:174-182 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-6eb1dd711f | GET /api/users/{userId}/websites | helper | authKey | src/lib/auth.ts:150-150 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-6eb1dd711f | GET /api/users/{userId}/websites | helper | members | src/app/api/admin/teams/route.ts:28-37 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-6eb1dd711f | GET /api/users/{userId}/websites | helper | members | src/app/api/admin/teams/route.ts:43-47 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-6eb1dd711f | GET /api/users/{userId}/websites | helper | teamOwner | src/app/api/share/[slug]/route.ts:21-29 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-6eb1dd711f | GET /api/users/{userId}/websites | helper | isApiKeyBlockedPath | src/lib/api-key.ts:36-38 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-6eb1dd711f | GET /api/users/{userId}/websites | helper | hashApiKey | src/lib/api-key.ts:24-26 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-6eb1dd711f | GET /api/users/{userId}/websites | helper | createAuthKey | src/lib/crypto.ts:68-70 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | perm_table | ROLES | src/lib/constants.ts:174-182 | 1 | indirect | indirect |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | perm_table | PERMISSIONS | src/lib/constants.ts:191-201 | 2 | indirect | indirect |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | perm_table | ROLE_PERMISSIONS | src/lib/constants.ts:203-234 | 2 | direct | direct |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | helper | isApiKeyEnabled | src/lib/api-key.ts:40-42 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | helper | isApiKey | src/lib/api-key.ts:32-34 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | helper | checkApiKeyAuth | src/lib/auth.ts:32-69 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | helper | authKey | src/lib/auth.ts:150-150 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | helper | members | src/app/api/admin/websites/route.ts:43-47 | 1 | direct | direct |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | helper | members | src/app/api/admin/teams/route.ts:28-37 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | helper | teamOwner | src/app/api/share/[slug]/route.ts:21-29 | 1 | wrong_impl | wrong_impl |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | helper | isApiKeyBlockedPath | src/lib/api-key.ts:36-38 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | helper | hashApiKey | src/lib/api-key.ts:24-26 | 2 | wrong_impl | wrong_impl |  |
| v5t-umami-ad293dc85a | GET /api/admin/websites | helper | createAuthKey | src/lib/crypto.ts:68-70 | 2 | wrong_impl | wrong_impl |  |
