# S4 고쳐진 건 · 새로 틀린 건 목록 (v5 → ctx4096, seed별 및 3 seed 일관)

열: id · 프로젝트 · 정답 · v5 예측(s42/s43/s44) · ctx4096 예측(s42/s43/s44) · 권한 블록 포함(블록 수·종류·cut) · 블록 이름

## test_v5

### 3 seed 모두 고쳐진 건 (4)

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|
| v5t-rocketchat-993879a33c | Rocket.Chat | manual | member/member/member | manual/manual/manual | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-d8e8746051 | Rocket.Chat | manual | owner/owner/owner | manual/manual/manual | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-a1a9b72abe | Rocket.Chat | member | manual/manual/manual | member/member/member | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-64704a55de | Rocket.Chat | role | member/member/member | role/role/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |

### 3 seed 모두 새로 틀린 건 (9)

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|
| v5t-ghost-39c04d77ae | Ghost | owner | owner/owner/owner | role/own+adm/role | 예 helper1,perm_flow1,perm_table1,permissible1 cut | rolePermissions[user]; user.permissible; canThis(core); tokenPermissionCheck |
| v5t-ghost-a4d27433a3 | Ghost | pub | pub/pub/pub | manual/role/manual | 예 perm_flow1,perm_table1 | rolePermissions[authentication]; canThis(core) |
| v5t-ghost-bae2ea5162 | Ghost | pub | pub/pub/pub | manual/manual/manual | 예 helper1 | tokenPermissionCheck |
| v5t-rocketchat-dfc8ce163b | Rocket.Chat | manual | manual/manual/manual | role/role/role | 예 helper2,perm_table1 | permission→roles; hasPermissionAsync; members |
| v5t-rocketchat-063a2e7907 | Rocket.Chat | own+adm | own+adm/own+adm/own+adm | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-d3c6acea99 | Rocket.Chat | own+adm | own+adm/own+adm/own+adm | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-umami-bdd6ebb218 | Umami | manual | manual/manual/manual | role/role/member | 예 perm_table3 | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-3dde1c334d | Umami | owner | owner/owner/owner | member/member/member | 예 helper1 | getAllUserWebsitesIncludingTeamAccess |
| v5t-umami-b89ee084f9 | Umami | owner | owner/owner/owner | member/member/member | 예 helper1 | getAllUserWebsitesIncludingTeamAccess |

### seed 42: 고쳐진 13 · 새로 틀린 26

고쳐진:

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|
| v5t-rocketchat-609098a14c | Rocket.Chat | manual | member/member/manual | manual/member/manual | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-993879a33c | Rocket.Chat | manual | member/member/member | manual/manual/manual | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-d8e8746051 | Rocket.Chat | manual | owner/owner/owner | manual/manual/manual | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-fc1513c9cb | Rocket.Chat | manual | member/manual/member | manual/manual/member | 아니오 |  |
| v5t-rocketchat-a1a9b72abe | Rocket.Chat | member | manual/manual/manual | member/member/member | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-0d896bf7fc | Rocket.Chat | role | member/member/role | role/member/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-2728fd39da | Rocket.Chat | role | member/member/role | role/member/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-61d5e55ae2 | Rocket.Chat | role | manual/manual/manual | role/manual/manual | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-64704a55de | Rocket.Chat | role | member/member/member | role/role/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-7508165c03 | Rocket.Chat | role | member/member/member | role/member/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-7cc51eccb8 | Rocket.Chat | role | ERR/role/role | role/role/role | 예 helper3,perm_flow1,perm_table1 | permission→roles; checkPermissions(permissionsRequired); permissionsRequired; hasAllPermis |
| v5t-rocketchat-a447ce62f1 | Rocket.Chat | role | own+adm/manual/role | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-ae3a073bb9 | Rocket.Chat | role | member/member/member | role/member/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |

새로 틀린:

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|
| v5t-ghost-39c04d77ae | Ghost | owner | owner/owner/owner | role/own+adm/role | 예 helper1,perm_flow1,perm_table1,permissible1 cut | rolePermissions[user]; user.permissible; canThis(core); tokenPermissionCheck |
| v5t-ghost-0771ec6e22 | Ghost | own+adm | own+adm/manual/own+adm | ERR/own+adm/own+adm | 예 perm_table1,permissible1 cut | rolePermissions[post]; post.permissible |
| v5t-ghost-0cbaf4100c | Ghost | pub | pub/pub/pub | manual/pub/manual | 예 helper1 | isSetup |
| v5t-ghost-a4d27433a3 | Ghost | pub | pub/pub/pub | manual/role/manual | 예 perm_flow1,perm_table1 | rolePermissions[authentication]; canThis(core) |
| v5t-ghost-bae2ea5162 | Ghost | pub | pub/pub/pub | manual/manual/manual | 예 helper1 | tokenPermissionCheck |
| v5t-rocketchat-1fbf39be09 | Rocket.Chat | manual | manual/own+adm/own+adm | role/role/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-4ef22bfc27 | Rocket.Chat | manual | manual/own+adm/own+adm | role/role/role | 예 helper2,perm_table1 | permission→roles; hasPermissionAsync; isEditingUserRoles |
| v5t-rocketchat-dfc8ce163b | Rocket.Chat | manual | manual/manual/manual | role/role/role | 예 helper2,perm_table1 | permission→roles; hasPermissionAsync; members |
| v5t-rocketchat-63107638c6 | Rocket.Chat | member | member/member/manual | manual/manual/manual | 예 helper1,perm_table1 cut | permission→roles; hasPermissionAsync |
| v5t-rocketchat-664e07d05b | Rocket.Chat | member | member/member/member | role/member/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-81879cc975 | Rocket.Chat | member | member/member/manual | manual/manual/manual | 예 helper2,perm_table1 cut | permission→roles; hasPermissionAsync; hasRoleAsync |
| v5t-rocketchat-063a2e7907 | Rocket.Chat | own+adm | own+adm/own+adm/own+adm | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-2663f8f241 | Rocket.Chat | own+adm | own+adm/own+adm/own+adm | role/own+adm/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-bb49c88371 | Rocket.Chat | own+adm | own+adm/own+adm/own+adm | role/own+adm/own+adm | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-d3c6acea99 | Rocket.Chat | own+adm | own+adm/own+adm/own+adm | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-52624474db | Rocket.Chat | role | role/manual/role | own+adm/own+adm/own+adm | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-umami-0a31680c6d | Umami | manual | manual/own+adm/manual | role/own+adm/role | 예 perm_table3 cut | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-8368db1fee | Umami | manual | manual/manual/manual | role/role/manual | 예 perm_table3 cut | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-bdd6ebb218 | Umami | manual | manual/manual/manual | role/role/member | 예 perm_table3 | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-3dde1c334d | Umami | owner | owner/owner/owner | member/member/member | 예 helper1 | getAllUserWebsitesIncludingTeamAccess |
| v5t-umami-b89ee084f9 | Umami | owner | owner/owner/owner | member/member/member | 예 helper1 | getAllUserWebsitesIncludingTeamAccess |
| v5t-umami-431f171df1 | Umami | own+adm | own+adm/role/own+adm | role/role/own+adm | 예 perm_table3 | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-6eb1dd711f | Umami | own+adm | own+adm/own+adm/own+adm | member/own+adm/own+adm | 예 helper1 | getAllUserWebsitesIncludingTeamAccess |
| v5t-umami-f6f0764144 | Umami | own+adm | own+adm/own+adm/own+adm | role/own+adm/own+adm | 예 perm_table3 | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-019432a060 | Umami | pub | pub/pub/pub | manual/pub/manual | 예 helper2 | checkAuth; checkApiKeyAuth |
| v5t-umami-640719b3b2 | Umami | pub | pub/pub/pub | manual/pub/manual | 예 helper2 | checkAuth; checkApiKeyAuth |

### seed 43: 고쳐진 16 · 새로 틀린 25

고쳐진:

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|
| v5t-ghost-0771ec6e22 | Ghost | own+adm | own+adm/manual/own+adm | ERR/own+adm/own+adm | 예 perm_table1,permissible1 cut | rolePermissions[post]; post.permissible |
| v5t-ghost-03a0ddc6dd | Ghost | role | owner/owner/owner | owner/role/role | 예 helper1,perm_flow1,perm_table1 | rolePermissions[authentication]; canThis(core); tokenPermissionCheck |
| v5t-ghost-1137a5840d | Ghost | role | role/manual/role | role/role/role | 예 helper1,perm_table1 | rolePermissions[integration]; tokenPermissionCheck |
| v5t-rocketchat-993879a33c | Rocket.Chat | manual | member/member/member | manual/manual/manual | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-d8e8746051 | Rocket.Chat | manual | owner/owner/owner | manual/manual/manual | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-35eb77dc38 | Rocket.Chat | member | member/owner/member | member/member/member | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-a1a9b72abe | Rocket.Chat | member | manual/manual/manual | member/member/member | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-5efea22347 | Rocket.Chat | role | role/manual/role | role/role/role | 예 helper5,perm_table1 | permission→roles; findAdminRoom; hasPermissionAsync; adminFields; scopeAdminRoomsForAbac;  |
| v5t-rocketchat-64704a55de | Rocket.Chat | role | member/member/member | role/role/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-70f72af62c | Rocket.Chat | role | role/manual/role | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-7fef853453 | Rocket.Chat | role | member/member/role | member/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-a447ce62f1 | Rocket.Chat | role | own+adm/manual/role | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-c2f1c961aa | Rocket.Chat | role | role/member/manual | role/role/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-ca047ea3cd | Rocket.Chat | role | role/manual/role | role/role/role | 예 helper2,perm_table1 | permission→roles; members; hasPermissionAsync |
| v5t-umami-2908d81714 | Umami | role | role/own+adm/role | role/role/role | 예 perm_table3 | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-9ae29e870f | Umami | role | role/own+adm/role | role/role/role | 예 perm_table2 | ROLES; PERMISSIONS |

새로 틀린:

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|
| v5t-ghost-39c04d77ae | Ghost | owner | owner/owner/owner | role/own+adm/role | 예 helper1,perm_flow1,perm_table1,permissible1 cut | rolePermissions[user]; user.permissible; canThis(core); tokenPermissionCheck |
| v5t-ghost-81aa11ba50 | Ghost | pub | manual/pub/pub | manual/manual/manual | 예 helper1 | isInvitation |
| v5t-ghost-a4d27433a3 | Ghost | pub | pub/pub/pub | manual/role/manual | 예 perm_flow1,perm_table1 | rolePermissions[authentication]; canThis(core) |
| v5t-ghost-bae2ea5162 | Ghost | pub | pub/pub/pub | manual/manual/manual | 예 helper1 | tokenPermissionCheck |
| v5t-rocketchat-6d967375a0 | Rocket.Chat | manual | role/manual/manual | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-bfa20a50ad | Rocket.Chat | manual | manual/manual/ERR | manual/pub/manual | 예 perm_table1 cut | permission→roles |
| v5t-rocketchat-dfc8ce163b | Rocket.Chat | manual | manual/manual/manual | role/role/role | 예 helper2,perm_table1 | permission→roles; hasPermissionAsync; members |
| v5t-rocketchat-ead569149d | Rocket.Chat | manual | role/manual/manual | role/role/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-f1492901da | Rocket.Chat | manual | member/manual/manual | member/member/manual | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-38a3cfd41a | Rocket.Chat | member | own+adm/member/manual | manual/own+adm/manual | 예 helper2,perm_table1 cut | permission→roles; hasPermissionAsync; hasRoleAsync |
| v5t-rocketchat-63107638c6 | Rocket.Chat | member | member/member/manual | manual/manual/manual | 예 helper1,perm_table1 cut | permission→roles; hasPermissionAsync |
| v5t-rocketchat-7346251579 | Rocket.Chat | member | manual/member/manual | manual/manual/manual | 아니오 |  |
| v5t-rocketchat-81879cc975 | Rocket.Chat | member | member/member/manual | manual/manual/manual | 예 helper2,perm_table1 cut | permission→roles; hasPermissionAsync; hasRoleAsync |
| v5t-rocketchat-ba4b8c9067 | Rocket.Chat | member | owner/member/manual | manual/manual/manual | 예 perm_flow3 cut | roomAccessValidators; canAccessPublicRoom; canAccessRoom |
| v5t-rocketchat-063a2e7907 | Rocket.Chat | own+adm | own+adm/own+adm/own+adm | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-ab6a857aaf | Rocket.Chat | own+adm | manual/own+adm/own+adm | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-d3c6acea99 | Rocket.Chat | own+adm | own+adm/own+adm/own+adm | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-63a1732919 | Rocket.Chat | role | manual/role/member | member/member/member | 예 perm_flow1 cut | roomAccessValidators |
| v5t-umami-189d97d3d0 | Umami | manual | manual/manual/manual | manual/role/manual | 예 perm_table3 cut | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-1d109a581c | Umami | manual | manual/manual/manual | manual/role/manual | 예 perm_table3 | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-8368db1fee | Umami | manual | manual/manual/manual | role/role/manual | 예 perm_table3 cut | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-bdd6ebb218 | Umami | manual | manual/manual/manual | role/role/member | 예 perm_table3 | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-56f66291b9 | Umami | member | member/member/member | member/role/member | 예 perm_table3 | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-3dde1c334d | Umami | owner | owner/owner/owner | member/member/member | 예 helper1 | getAllUserWebsitesIncludingTeamAccess |
| v5t-umami-b89ee084f9 | Umami | owner | owner/owner/owner | member/member/member | 예 helper1 | getAllUserWebsitesIncludingTeamAccess |

### seed 44: 고쳐진 22 · 새로 틀린 34

고쳐진:

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|
| v5t-ghost-03a0ddc6dd | Ghost | role | owner/owner/owner | owner/role/role | 예 helper1,perm_flow1,perm_table1 | rolePermissions[authentication]; canThis(core); tokenPermissionCheck |
| v5t-ghost-4bc909eaec | Ghost | role | role/role/own+adm | role/role/role | 예 helper1,perm_table1 | rolePermissions[theme]; tokenPermissionCheck |
| v5t-ghost-d991d035bb | Ghost | role | role/role/own+adm | role/role/role | 예 helper1,perm_table1 | rolePermissions[recommendation]; tokenPermissionCheck |
| v5t-rocketchat-17ffd71761 | Rocket.Chat | manual | manual/role/role | manual/role/manual | 예 helper2 | permissionsGetMethod; permissionsEndpoints |
| v5t-rocketchat-2b42fcece3 | Rocket.Chat | manual | owner/manual/own+adm | owner/manual/manual | 아니오 |  |
| v5t-rocketchat-993879a33c | Rocket.Chat | manual | member/member/member | manual/manual/manual | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-b5307adaa2 | Rocket.Chat | manual | member/member/member | member/member/manual | 아니오 |  |
| v5t-rocketchat-b830163cb8 | Rocket.Chat | manual | owner/owner/owner | owner/owner/manual | 아니오 |  |
| v5t-rocketchat-bfa20a50ad | Rocket.Chat | manual | manual/manual/ERR | manual/pub/manual | 예 perm_table1 cut | permission→roles |
| v5t-rocketchat-d8e8746051 | Rocket.Chat | manual | owner/owner/owner | manual/manual/manual | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-3944d8594e | Rocket.Chat | member | owner/member/owner | owner/member/member | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-a1a9b72abe | Rocket.Chat | member | manual/manual/manual | member/member/member | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-09c0e4be92 | Rocket.Chat | role | role/role/manual | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-3f15a8caba | Rocket.Chat | role | role/role/manual | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-64704a55de | Rocket.Chat | role | member/member/member | role/role/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-6a9ba0c552 | Rocket.Chat | role | role/role/ERR | role/role/role | 예 helper2,perm_flow1,perm_table1 | permission→roles; checkPermissions(permissionsRequired); permissionKeys; permissionsCount |
| v5t-rocketchat-7508165c03 | Rocket.Chat | role | member/member/member | role/member/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-951602c914 | Rocket.Chat | role | role/role/manual | role/role/role | 예 helper3,perm_flow1,perm_table1 | permission→roles; checkPermissions(permissionsRequired); permissionsRequired; hasAllPermis |
| v5t-rocketchat-ae3a073bb9 | Rocket.Chat | role | member/member/member | role/member/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-c2f1c961aa | Rocket.Chat | role | role/member/manual | role/role/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-c65d2bcd9d | Rocket.Chat | role | role/role/manual | role/role/role | 예 helper1 | hasPermissionAsync |
| v5t-umami-d334436440 | Umami | role | role/own+adm/own+adm | role/own+adm/role | 예 perm_table2 | ROLE_PERMISSIONS; ROLES |

새로 틀린:

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|
| v5t-ghost-39c04d77ae | Ghost | owner | owner/owner/owner | role/own+adm/role | 예 helper1,perm_flow1,perm_table1,permissible1 cut | rolePermissions[user]; user.permissible; canThis(core); tokenPermissionCheck |
| v5t-ghost-ffeb0a64b6 | Ghost | owner | owner/owner/owner | owner/owner/role | 예 helper1,perm_flow1,perm_table1,permissible1 cut | rolePermissions[user]; user.permissible; canThis(core); tokenPermissionCheck |
| v5t-ghost-0cbaf4100c | Ghost | pub | pub/pub/pub | manual/pub/manual | 예 helper1 | isSetup |
| v5t-ghost-81aa11ba50 | Ghost | pub | manual/pub/pub | manual/manual/manual | 예 helper1 | isInvitation |
| v5t-ghost-a4d27433a3 | Ghost | pub | pub/pub/pub | manual/role/manual | 예 perm_flow1,perm_table1 | rolePermissions[authentication]; canThis(core) |
| v5t-ghost-bae2ea5162 | Ghost | pub | pub/pub/pub | manual/manual/manual | 예 helper1 | tokenPermissionCheck |
| v5t-ghost-1dabb75c59 | Ghost | role | role/role/role | role/role/manual | 예 helper1,perm_table1 | rolePermissions[label]; tokenPermissionCheck |
| v5t-rocketchat-0398a2f985 | Rocket.Chat | manual | manual/manual/manual | manual/manual/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-25c4e3c534 | Rocket.Chat | manual | member/member/manual | role/role/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-29963cbc5b | Rocket.Chat | manual | owner/own+adm/manual | role/member/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-6d967375a0 | Rocket.Chat | manual | role/manual/manual | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-a7d7197ba0 | Rocket.Chat | manual | member/member/manual | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-dfc8ce163b | Rocket.Chat | manual | manual/manual/manual | role/role/role | 예 helper2,perm_table1 | permission→roles; hasPermissionAsync; members |
| v5t-rocketchat-ead569149d | Rocket.Chat | manual | role/manual/manual | role/role/role | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-301c3c9949 | Rocket.Chat | member | member/member/member | member/member/manual | 예 perm_table1 | permission→roles |
| v5t-rocketchat-52d02d65e4 | Rocket.Chat | member | member/member/member | member/member/manual | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-664e07d05b | Rocket.Chat | member | member/member/member | role/member/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-89ea440008 | Rocket.Chat | member | member/member/member | member/member/manual | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-ccf34d5fc7 | Rocket.Chat | member | member/member/member | member/member/manual | 예 perm_flow1,perm_table1 cut | permission→roles; roomAccessValidators |
| v5t-rocketchat-063a2e7907 | Rocket.Chat | own+adm | own+adm/own+adm/own+adm | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-2663f8f241 | Rocket.Chat | own+adm | own+adm/own+adm/own+adm | role/own+adm/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-ab6a857aaf | Rocket.Chat | own+adm | manual/own+adm/own+adm | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-d3c6acea99 | Rocket.Chat | own+adm | own+adm/own+adm/own+adm | role/role/role | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-52624474db | Rocket.Chat | role | role/manual/role | own+adm/own+adm/own+adm | 예 helper1,perm_table1 | permission→roles; hasPermissionAsync |
| v5t-rocketchat-ff636d6df7 | Rocket.Chat | role | manual/own+adm/role | manual/manual/manual | 예 perm_flow2,perm_table1 cut | permission→roles; roomAccessValidators; canAccessPublicRoom |
| v5t-umami-0a31680c6d | Umami | manual | manual/own+adm/manual | role/own+adm/role | 예 perm_table3 cut | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-1ac5a3d03d | Umami | manual | manual/manual/manual | manual/manual/member | 예 perm_table3 | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-bdd6ebb218 | Umami | manual | manual/manual/manual | role/role/member | 예 perm_table3 | ROLES; PERMISSIONS; ROLE_PERMISSIONS |
| v5t-umami-3dde1c334d | Umami | owner | owner/owner/owner | member/member/member | 예 helper1 | getAllUserWebsitesIncludingTeamAccess |
| v5t-umami-b89ee084f9 | Umami | owner | owner/owner/owner | member/member/member | 예 helper1 | getAllUserWebsitesIncludingTeamAccess |
| v5t-umami-019432a060 | Umami | pub | pub/pub/pub | manual/pub/manual | 예 helper2 | checkAuth; checkApiKeyAuth |
| v5t-umami-640719b3b2 | Umami | pub | pub/pub/pub | manual/pub/manual | 예 helper2 | checkAuth; checkApiKeyAuth |
| v5t-umami-8a66f9b00f | Umami | pub | manual/manual/pub | manual/manual/manual | 예 helper2 | checkAuth; checkApiKeyAuth |
| v5t-umami-9454ba34fd | Umami | pub | manual/manual/pub | manual/manual/manual | 예 helper2 | checkAuth; checkApiKeyAuth |

### 전이 (v5 예측 → ctx 예측 | 정답, 3 seed 합산, 상위 25)

- manual_review_required→role_required|truth=manual_review_required: 21
- public→manual_review_required|truth=public: 15
- owner_or_admin→role_required|truth=owner_or_admin: 13
- membership_required→role_required|truth=role_required: 11
- manual_review_required→role_required|truth=role_required: 11
- membership_required→manual_review_required|truth=membership_required: 10
- owner_or_admin→role_required|truth=manual_review_required: 9
- membership_required→role_required|truth=manual_review_required: 7
- membership_required→manual_review_required|truth=manual_review_required: 6
- owner_or_admin→role_required|truth=role_required: 6
- owner_match→membership_required|truth=owner_match: 6
- owner_match→manual_review_required|truth=manual_review_required: 4
- owner_match→role_required|truth=owner_match: 3
- membership_required→role_required|truth=membership_required: 3
- manual_review_required→membership_required|truth=membership_required: 3
- manual_review_required→membership_required|truth=manual_review_required: 3
- membership_required→role_required|truth=owner_or_admin: 2
- role_required→owner_or_admin|truth=role_required: 2
- output_error→role_required|truth=role_required: 2
- owner_match→role_required|truth=role_required: 2
- owner_match→membership_required|truth=membership_required: 2
- manual_review_required→owner_or_admin|truth=role_required: 2
- role_required→manual_review_required|truth=role_required: 2
- owner_or_admin→output_error|truth=owner_or_admin: 1
- owner_match→role_required|truth=manual_review_required: 1

## test_v30

### 3 seed 모두 고쳐진 건 (0)

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|

### 3 seed 모두 새로 틀린 건 (0)

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|

### seed 42: 고쳐진 5 · 새로 틀린 7

고쳐진:

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|
| 447fc0aa6c34613756ff | juice-shop | owner | manual/manual/owner | owner/manual/owner | 아니오 |  |
| 7364a223f5e100dd73b2 | juice-shop | owner | pub/owner/owner | owner/owner/owner | 아니오 |  |
| 905507d01b81ba5eb1f0 | juice-shop | owner | ERR/owner/manual | owner/owner/manual | 아니오 |  |
| 0f5b4d569c99d8d9c870 | Pixi | pub | owner/owner/manual | pub/manual/manual | 아니오 |  |
| a15a54f7818a6cf25d98 | DVWS-node | owner | ERR/owner/owner | owner/owner/ERR | 아니오 |  |

새로 틀린:

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|
| cd33a23103c412ea5651 | crAPI | owner | owner/owner/owner | manual/owner/manual | 아니오 |  |
| 79d4449bddc16ef5992f | crAPI | role | role/role/manual | manual/role/manual | 아니오 |  |
| ed50adacf184ba6ddcba | juice-shop | owner | owner/manual/owner | manual/manual/owner | 아니오 |  |
| e574b8ba6eacb5d7c83c | juice-shop | owner | owner/manual/owner | member/member/manual | 아니오 |  |
| 0e1637db083f68e499d4 | Pixi | role | role/role/role | manual/role/manual | 아니오 |  |
| 0293603d276a2bdbefe0 | Pixi | owner | owner/manual/owner | manual/manual/manual | 아니오 |  |
| a4f0cd98076a7ed61adf | DVWS-node | owner | owner/owner/ERR | ERR/owner/owner | 아니오 |  |

### seed 43: 고쳐진 3 · 새로 틀린 7

고쳐진:

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|
| bb8c80531d0fc1d9caed | juice-shop | pub | pub/manual/manual | pub/pub/manual | 아니오 |  |
| eed3687a2d41f8658232 | Pixi | pub | pub/manual/manual | pub/pub/manual | 아니오 |  |
| 93b3678d43a24b94f1c3 | Pixi | owner | manual/manual/owner | manual/owner/manual | 아니오 |  |

새로 틀린:

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|
| 4de2f44349d88f3d6b3a | crAPI | owner | owner/owner/owner | owner/manual/manual | 아니오 |  |
| e502084b4f925dbf28e4 | juice-shop | owner | owner/owner/owner | owner/manual/manual | 예 helper1 | isAuthorized |
| cd10794910422bd9dcf8 | juice-shop | owner | manual/owner/owner | manual/manual/manual | 아니오 |  |
| 2787243a5db7dfb178b4 | juice-shop | owner | manual/owner/owner | manual/manual/owner | 아니오 |  |
| 7b6e2731e933a52a9070 | juice-shop | owner | owner/owner/owner | owner/own+adm/member | 아니오 |  |
| ffe188e6f24418c23676 | DVWS-node | owner | pub/owner/pub | pub/ERR/pub | 아니오 |  |
| 208819689993254cc920 | DVWS-node | pub | manual/pub/pub | manual/manual/pub | 아니오 |  |

### seed 44: 고쳐진 2 · 새로 틀린 23

고쳐진:

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|
| 680ac46b983584d4552d | Pixi | pub | pub/pub/manual | pub/pub/pub | 아니오 |  |
| a4f0cd98076a7ed61adf | DVWS-node | owner | owner/owner/ERR | ERR/owner/owner | 아니오 |  |

새로 틀린:

| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |
|---|---|---|---|---|---|---|
| d93acb187b6c273464f0 | crAPI | owner | manual/manual/owner | manual/manual/manual | 아니오 |  |
| d0afe4b052514b189dfa | crAPI | owner | owner/owner/owner | owner/owner/manual | 아니오 |  |
| c3203410c4072686beaa | crAPI | owner | owner/manual/owner | owner/manual/manual | 아니오 |  |
| 6bca6097b26cf226f405 | crAPI | owner | manual/manual/owner | manual/manual/manual | 아니오 |  |
| cd33a23103c412ea5651 | crAPI | owner | owner/owner/owner | manual/owner/manual | 아니오 |  |
| dcc8f1be82d40ee3d5cf | crAPI | owner | manual/manual/owner | manual/manual/manual | 아니오 |  |
| abbb3b1e9239779e76f2 | crAPI | owner | owner/owner/owner | owner/owner/manual | 아니오 |  |
| 4de2f44349d88f3d6b3a | crAPI | owner | owner/owner/owner | owner/manual/manual | 아니오 |  |
| d553cdd9276767f1b1bc | crAPI | pub | pub/pub/pub | pub/pub/manual | 아니오 |  |
| e502084b4f925dbf28e4 | juice-shop | owner | owner/owner/owner | owner/manual/manual | 예 helper1 | isAuthorized |
| e574b8ba6eacb5d7c83c | juice-shop | owner | owner/manual/owner | member/member/manual | 아니오 |  |
| cd10794910422bd9dcf8 | juice-shop | owner | manual/owner/owner | manual/manual/manual | 아니오 |  |
| 745151104eb860a9e9ec | juice-shop | owner | owner/owner/owner | owner/owner/manual | 아니오 |  |
| 7b6e2731e933a52a9070 | juice-shop | owner | owner/owner/owner | owner/own+adm/member | 아니오 |  |
| 5cb15a9c2cc08fcaa9f2 | Pixi | role | pub/role/role | pub/role/manual | 아니오 |  |
| 0e1637db083f68e499d4 | Pixi | role | role/role/role | manual/role/manual | 아니오 |  |
| 0293603d276a2bdbefe0 | Pixi | owner | owner/manual/owner | manual/manual/manual | 아니오 |  |
| 93b3678d43a24b94f1c3 | Pixi | owner | manual/manual/owner | manual/owner/manual | 아니오 |  |
| bf2d1601b02281b85536 | Pixi | owner | owner/owner/owner | owner/owner/manual | 아니오 |  |
| a15a54f7818a6cf25d98 | DVWS-node | owner | ERR/owner/owner | owner/owner/ERR | 아니오 |  |
| 963209fb55865d6f2acf | DVWS-node | owner | owner/owner/owner | owner/owner/manual | 아니오 |  |
| 0a8fb9b5c84b26b19826 | DVWS-node | owner | owner/owner/owner | owner/owner/manual | 아니오 |  |
| 3f37f7f30c7bc18f180a | DVWS-node | owner | owner/manual/owner | owner/manual/manual | 아니오 |  |

### 전이 (v5 예측 → ctx 예측 | 정답, 3 seed 합산, 상위 25)

- owner_match→manual_review_required|truth=owner_match: 25
- owner_match→manual_review_required|truth=public: 10
- role_required→manual_review_required|truth=role_required: 4
- membership_required→manual_review_required|truth=public: 4
- output_error→owner_match|truth=owner_match: 3
- owner_match→output_error|truth=owner_match: 3
- manual_review_required→public|truth=public: 3
- manual_review_required→owner_match|truth=owner_match: 2
- manual_review_required→role_required|truth=owner_match: 2
- owner_match→membership_required|truth=owner_match: 2
- manual_review_required→public|truth=role_required: 2
- public→manual_review_required|truth=role_required: 2
- owner_match→manual_review_required|truth=role_required: 2
- public→manual_review_required|truth=public: 2
- output_error→manual_review_required|truth=role_required: 1
- membership_required→manual_review_required|truth=owner_match: 1
- public→owner_match|truth=owner_match: 1
- manual_review_required→owner_match|truth=public: 1
- owner_match→public|truth=public: 1
- membership_required→manual_review_required|truth=role_required: 1
- manual_review_required→public|truth=owner_match: 1
- owner_match→owner_or_admin|truth=public: 1
- manual_review_required→membership_required|truth=owner_match: 1
- owner_match→owner_or_admin|truth=owner_match: 1
- role_required→manual_review_required|truth=owner_match: 1

