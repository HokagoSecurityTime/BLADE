# S4 정지 지점 1: 권한 문맥 분석기 — test_v5 10건 입력 샘플 (2026-11-03)

프롬프트 v3.0.1, 학습·추론 없음. 진입점은 핸들러 위치(source_locations[0])와 controller_text뿐이며 정답·근거·초안 열은 읽지 않았다. 토큰은 Qwen2.5 토크나이저로 system+user 채팅 프롬프트 전체를 센 값(상한 4096).

## 프로젝트별 권한 정의 포함 건수 (test_v5 283 전체 빌드 기준)

| project | n | 권한표 신규 추가 | 권한표 기존 입력에 이미 있음 | 권한 흐름 신규 / 기존 | permissible 신규 / 기존 | 권한 정의 1종 이상(신규+기존) | 헬퍼 정의 추가 | 블록 1개 이상 | 권한표 찾았으나 예산 탈락 | 잘림(탈락·절단) 건수 | 블록 발견/유지 평균 | 토큰 전/후 평균 | 토큰 후 최대 |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---|---|---:|
| ghost | 69 | 61 | 0 | 12 / 46 | 18 / 3 | 65 | 60 | 69 | 0 | 63 | 15.57 / 5.71 | 3315 / 4002 | 4086 |
| rocketchat | 157 | 109 | 0 | 54 / 5 | 0 / 0 | 111 | 71 | 129 | 2 | 94 | 8.31 / 3.33 | 3580 / 3848 | 4089 |
| umami | 57 | 38 | 5 | 1 / 0 | 0 / 0 | 39 | 44 | 56 | 0 | 43 | 10.84 / 5.81 | 3462 / 3996 | 4090 |

perm_table = Ghost rolePermissions 행·Rocket.Chat 권한명→역할·Umami ROLE_PERMISSIONS, perm_flow = Ghost canThis 핵심·Rocket.Chat roomAccessValidators+validator 본문·permissionsRequired 처리, permissible = Ghost 모델 permissible, helper = 이름 패턴으로 추적한 함수 정의(깊이≤2).

## 10건 샘플 (seed 42: Ghost 3 · Rocket.Chat 4 · Umami 3)

### v5t-ghost-244db7151d — ghost DELETE /ghost/api/admin/pages/{id}/

블록 발견 19 / 유지 2 / 탈락 17 / 절단 True · 토큰 3566 → 4012

유지 블록: perm_table:rolePermissions[post](permissions-data.ts:1-235), permissible:post.permissible(authors.js:340-453, clipped)

```
[관련 권한 코드]
FILE ghost/core/server/services/permissions/permissions-data.ts:1-235 [perm_table rolePermissions[post]]
permissions.post: ['browse', 'read', 'edit', 'add', 'destroy', 'publish'],
rolePermissions.Administrator.post: 'all',
rolePermissions.DB Backup Integration.post: ['browse'],
rolePermissions.Scheduler Integration.post: ['publish'],
rolePermissions.Admin Integration.post: 'all',
rolePermissions.Super Editor.post: 'all',
rolePermissions.Editor.post: 'all',
rolePermissions.Author.post: ['browse', 'read', 'edit', 'add', 'destroy'],
rolePermissions.Contributor.post: ['browse', 'read', 'edit', 'add', 'destroy'],

FILE ghost/core/server/models/relations/authors.js:340-453 [permissible post.permissible]
      permissible: function permissible(
        postModelOrId,
        action,
        context,
        unsafeAttrs,
        loadedPermissions,
        hasUserPermission,
        hasApiKeyPermission,
      ) {
        const self = this;
        const postModel = postModelOrId;
        let origArgs;
        const { isContributor, isAuthor } = setIsRoles(loadedPermissions);
        if (_.isNumber(postModelOrId) || _.isString(postModelOrId)) {
          origArgs = _.toArray(arguments).slice(1);
          return this.findOne(
            { id: postModelOrId, status: 'all' },
            { withRelated: ['authors'] },
          ).then(function then(foundPostModel) {
            if (!foundPostModel) {
              throw new errors.NotFoundError({
                message: tpl(messages.postNotFound),
              });
            }
            const newArgs = [foundPostModel].concat(origArgs);
            return self.permissible.apply(self, newArgs);
          });
        }
        const isEdit = action === 'edit';
        const isAdd = action === 'add';
        const isDestroy = action === 'destroy';
        function isChangingAuthors() {
      ...
        return Promise.reject(
          new errors.NoPermissionError({
            message: tpl(messages.notEnoughPermission),
          }),
        );
      },
```

### v5t-ghost-05ee24e847 — ghost GET /ghost/api/admin/posts/{id}/gift_links/

블록 발견 15 / 유지 6 / 탈락 9 / 절단 True · 토큰 3314 → 4084

유지 블록: helper:authenticate(admin.js:48-67), helper:authenticate(authenticate.js:5-13), helper:authorize(authorize.js:12-45), helper:authorize(index.js:2-4), helper:authorizeAdminApi(authorize.js:30-44), helper:tokenPermissionCheck(middleware.js:17-101, clipped)

```
[관련 권한 코드]
FILE ghost/core/server/auth/api-key/admin.js:48-67 [helper authenticate]
const authenticate = function apiKeyAdminAuth(req, res, next) {
  if (!req.headers || !req.headers.authorization) {
    req.api_key = null;
    return next();
  }
  const token = _extractTokenFromHeader(req.headers.authorization);
  if (!token) {
    return next(
      new errors.UnauthorizedError({
        message: tpl(messages.incorrectAuthHeaderFormat),
        code: 'INVALID_AUTH_HEADER',
      }),
    );
  }
  return wrappedAuthenticateWithToken(req, res, next, { token });
};

FILE ghost/core/server/auth/authenticate.js:5-13 [helper authenticate]
const authenticate = {
  authenticateAdminApi: [apiKeyAuth.admin.authenticate, session.authenticate],
  authenticateAdminApiWithUrl: [apiKeyAuth.admin.authenticateWithUrl],
  authenticateContentApi: [
    apiKeyAuth.content.authenticateContentApiKey,
    members.authenticateMembersToken,
  ],
};

FILE ghost/core/server/auth/authorize.js:12-45 [helper authorize]
const authorize = {
  authorizeContentApi(req, res, next) {
    const hasApiKey = req.api_key && req.api_key.id;
    const hasMember = req.member;
    if (hasApiKey) {
      return next();
    }
    if (hasMember) {
      return next();
    }
    return next(
      new errors.NoPermissionError({
        message: tpl(messages.authorizationFailed),
        context: tpl(messages.missingContentMemberOrIntegration),
      }),
    );
  },
  authorizeAdminApi(req, res, next) {
    const hasUser = req.user && req.user.id;
    const hasApiKey = req.api_key && req.api_key.id;
    if (hasUser || hasApiKey) {
      return next();
    } else {
      return next(
        new errors.NoPermissionError({
          message: tpl(messages.authorizationFailed),
          context: tpl(messages.missingAdminUserOrIntegration),
        }),
      );
    }
  },
};

FILE ghost/core/server/auth/index.js:2-4 [helper authorize]
  get authorize() {
    return require('./authorize');
  },

FILE ghost/core/server/auth/authorize.js:30-44 [helper authorizeAdminApi]
  authorizeAdminApi(req, res, next) {
    const hasUser = req.user && req.user.id;
    const hasApiKey = req.api_key && req.api_key.id;
    if (hasUser || hasApiKey) {
      return next();
    } else {
      return next(
        new errors.NoPermissionError({
          message: tpl(messages.authorizationFailed),
          context: tpl(messages.missingAdminUserOrIntegration),
        }),
      );
    }
  },

FILE ghost/core/server/web/api/endpoints/admin/middleware.js:17-101 [helper tokenPermissionCheck]
const tokenPermissionCheck = function tokenPermissionCheck(req, res, next) {
  if (!req.api_key) {
    return next();
  }
  if (req.api_key?.get('user_id')) {
    const path = req.path.toLowerCase();
    const isDeleteAllContent = req.method === 'DELETE' && (path === '/db/' || path === '/db');
    const isTransferOwnership =
      req.method === 'PUT' && (path === '/users/owner/' || path === '/users/owner');
    const isResetAuthentication =
      req.method === 'POST' &&
      (path === '/authentication/reset/' || path === '/authentication/reset');
    if (isDeleteAllContent || isTransferOwnership || isResetAuthentication) {
      return next(
        new errors.NoPermissionError({
          message: tpl(messages.staffTokenBlocked),
        }),
      );
    }
      ...
```

### v5t-ghost-6e1dca8d3d — ghost PUT /ghost/api/admin/authentication/password_reset/

블록 발견 4 / 유지 4 / 탈락 0 / 절단 False · 토큰 3173 → 3584

유지 블록: perm_table:rolePermissions[authentication](permissions-data.ts:1-235), perm_flow:canThis(core)(can-this.js:35-121, clipped), helper:authentication(index.js:34-36), helper:authentication(index.js:27-29)

```
[관련 권한 코드]
FILE ghost/core/server/services/permissions/permissions-data.ts:1-235 [perm_table rolePermissions[authentication]]
permissions.authentication: ['reset'],
rolePermissions.Administrator.authentication: ['reset'],

FILE ghost/core/server/services/permissions/can-this.js:35-121 [perm_flow canThis(core)]
  const { isOwner } = setIsRoles(loadedPermissions);
  if (isOwner) {
    hasUserPermission = true;
  } else if (!_.isEmpty(userPermissions)) {
    hasUserPermission = _.some(userPermissions, checkPermission);
  }
  hasApiKeyPermission = true;
  if (!_.isNull(apiKeyPermissions)) {
    if (loadedPermissions.user) {
      hasApiKeyPermission = true; // Allow API key check to pass
    } else {
      hasUserPermission = true;
      hasApiKeyPermission = _.some(apiKeyPermissions, checkPermission);
    }
  }
  return { hasUserPermission, hasApiKeyPermission };
}
class CanThisResult {
  buildObjectTypeHandlers(objTypes, actType, context, permissionLoad) {
    const objectTypeModelMap = {
      post: models.Post,
      role: models.Role,
      user: models.User,
      setting: models.Settings,
      invite: models.Invite,
      integration: models.Integration,
      comment: models.Comment,
    };
    return _.reduce(
      objTypes,
      function (objTypeHandlers, objType) {
        const TargetModel = objectTypeModelMap[objType];
      ...
                unsafeAttrs,
                permissionsForModel,
                hasUserPermission,
                hasApiKeyPermission,
              );
            }

FILE ghost/core/server/api/endpoints/index.js:34-36 [helper authentication]
  get authentication() {
    return apiFramework.pipeline(require('./authentication'), localUtils);
  },

FILE ghost/core/server/api/endpoints/utils/serializers/output/index.js:27-29 [helper authentication]
  get authentication() {
    return require('./authentication');
  },
```

### v5t-rocketchat-6aebdee592 — rocketchat GET /api/v1/groups.list

블록 발견 0 / 유지 0 / 탈락 0 / 절단 False · 토큰 3275 → 3286

유지 블록: 

```
[관련 권한 코드]
(없음)
```

### v5t-rocketchat-63107638c6 — rocketchat POST /api/v1/rooms.leave

블록 발견 16 / 유지 3 / 탈락 13 / 절단 True · 토큰 3831 → 4076

유지 블록: perm_table:permission→roles(permissions.ts:1-242), helper:allowMemberAction(roomCoordinator.ts:15-17), helper:allowMemberAction(direct.ts:40-53, clipped)

```
[관련 권한 코드]
FILE apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 [perm_table permission→roles]
{ _id: 'leave-c', roles: ['admin', 'user', 'federated-external', 'bot', 'anonymous', 'app'] },
{ _id: 'leave-p', roles: ['admin', 'user', 'federated-external', 'bot', 'anonymous', 'app'] },

FILE apps/meteor/server/lib/rooms/roomCoordinator.ts:15-17 [helper allowMemberAction]
			async allowMemberAction(_room: IRoom, _action: ValueOf<typeof RoomMemberActions>, _userId?: IUser['_id']): Promise<boolean> {
				return false;
			},

FILE apps/meteor/server/lib/rooms/roomTypes/direct.ts:40-53 [helper allowMemberAction]
	async allowMemberAction(room, action, _userId) {
		if (isRoomFederated(room)) {
			if (isRoomNativeFederated(room) && isFederationEnabled()) {
				return true;
			}
			return false;
		}
      ...
```

### v5t-rocketchat-3c6f0d2295 — rocketchat POST /api/v1/groups.unarchive

블록 발견 14 / 유지 4 / 탈락 10 / 절단 True · 토큰 3716 → 4046

유지 블록: perm_table:permission→roles(permissions.ts:1-242), perm_flow:canAccessRoom(roomAccessValidator.internalService.ts:12-20), perm_flow:hasPermission(createAuthorizationFunctions.ts:24-24), perm_flow:roomAccessValidators(canAccessRoom.ts:24-106, clipped)

```
[관련 권한 코드]
FILE apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 [perm_table permission→roles]
{ _id: 'unarchive-room', roles: ['admin'] },

FILE apps/meteor/server/lib/omnichannel/roomAccessValidator.internalService.ts:12-20 [perm_flow canAccessRoom]
	async canAccessRoom(room: IOmnichannelRoom, user?: Pick<IUser, '_id'>, extraData?: object): Promise<boolean> {
		for (const validator of validators) {
			if (await validator(room, user, extraData)) {
				return true;
			}
		}
		return false;
	}

FILE apps/meteor/app/authorization/lib/createAuthorizationFunctions.ts:24-24 [perm_flow hasPermission]
	hasPermission: (permissions: IPermission['_id'] | IPermission['_id'][], scope?: string, scopedRoles?: IRole['_id'][]) => boolean;

FILE packages/authorization/src/canAccessRoom.ts:24-106 [perm_flow roomAccessValidators]
const roomAccessValidators: RoomAccessValidatorConverted[] = [
	async function _validateAccessToPublicRoomsInTeams(room, user): Promise<boolean> {
		if (!room) {
			return false;
		}
		if (!room._id || !room.teamId || room.t !== 'c') {
			return false;
		}
		if (user?._id && (await Subscriptions.findOneBannedSubscription(room._id, user._id))) {
			return false;
      ...
```

### v5t-rocketchat-26b775fea8 — rocketchat POST /api/v1/integrations.remove

블록 발견 14 / 유지 1 / 탈락 13 / 절단 False · 토큰 3824 → 3992

유지 블록: perm_table:permission→roles(permissions.ts:1-242)

```
[관련 권한 코드]
FILE apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 [perm_table permission→roles]
{ _id: 'manage-outgoing-integrations', roles: ['admin'] },
{ _id: 'manage-own-outgoing-integrations', roles: ['admin'] },
{ _id: 'manage-incoming-integrations', roles: ['admin'] },
{ _id: 'manage-own-incoming-integrations', roles: ['admin'] },
{ _id: 'view-c-room', roles: ['admin', 'user', 'federated-external', 'bot', 'app', 'anonymous'] },
{ _id: 'view-joined-room', roles: ['guest', 'bot', 'app', 'anonymous'] },
```

### v5t-umami-b89ee084f9 — umami GET /api/websites

블록 발견 12 / 유지 8 / 탈락 4 / 절단 False · 토큰 3343 → 4032

유지 블록: helper:getAllUserWebsitesIncludingTeamAccess(website.ts:122-147), helper:isApiKeyEnabled(api-key.ts:40-42), helper:isApiKey(api-key.ts:32-34), helper:checkApiKeyAuth(auth.ts:32-69), helper:ROLES(constants.ts:174-182), helper:authKey(auth.ts:150-150), helper:members(route.ts:28-37), helper:members(route.ts:43-47)

```
[관련 권한 코드]
FILE src/queries/prisma/website.ts:122-147 [helper getAllUserWebsitesIncludingTeamAccess]
export async function getAllUserWebsitesIncludingTeamAccess(
  userId: string,
  filters?: QueryFilters,
) {
  return getWebsites(
    {
      where: {
        OR: [
          { userId },
          {
            team: {
              deletedAt: null,
              members: {
                some: {
                  role: { in: [ROLES.teamOwner, ROLES.teamManager] },
                  userId,
                },
              },
            },
          },
        ],
      },
    },
    sanitizeSortFilters(filters, WEBSITE_SORT_FIELDS, { orderBy: 'name' }),
  );
}

FILE src/lib/api-key.ts:40-42 [helper isApiKeyEnabled]
export function isApiKeyEnabled() {
  return !process.env.CLOUD_MODE;
}

FILE src/lib/api-key.ts:32-34 [helper isApiKey]
export function isApiKey(token?: string | null): token is string {
  return typeof token === 'string' && token.startsWith(API_KEY_PREFIX);
}

FILE src/lib/auth.ts:32-69 [helper checkApiKeyAuth]
export async function checkApiKeyAuth(request: Request, token: string) {
  const { pathname } = new URL(request.url);
  if (isApiKeyBlockedPath(pathname)) {
    log('API key not allowed for path', pathname);
    return null;
  }
  const apiKey = await getApiKeyByHash(hashApiKey(token));
  if (!apiKey) {
    log('API key not found');
    return null;
  }
  const user: any = await getUser(apiKey.userId);
  if (!user?.id) {
    log('API key user not found');
    return null;
  }
  const lastUsedAt = apiKey.lastUsedAt?.getTime() ?? 0;
  if (Date.now() - lastUsedAt > API_KEY_LAST_USED_INTERVAL) {
    updateApiKeyLastUsed(apiKey.id).catch(e => log(e));
  }
  delete user.password;
  user.isAdmin = user.role === ROLES.admin;
  return {
    token,
    user,
    authType: 'api-key' as const,
    apiKey: { id: apiKey.id, name: apiKey.name },
  };
}

FILE src/lib/constants.ts:174-182 [helper ROLES]
export const ROLES = {
  admin: 'admin',
  user: 'user',
  viewOnly: 'view-only',
  teamOwner: 'team-owner',
  teamManager: 'team-manager',
  teamMember: 'team-member',
  teamViewOnly: 'team-view-only',
} as const;

FILE src/lib/auth.ts:150-150 [helper authKey]
  const authKey = `auth:${createAuthKey()}`;

FILE src/app/api/admin/teams/route.ts:28-37 [helper members]
        members: {
          include: {
            user: {
              select: {
                id: true,
                username: true,
              },
            },
          },
        },

FILE src/app/api/admin/teams/route.ts:43-47 [helper members]
            members: {
              where: {
                user: { deletedAt: null },
              },
            },
```

### v5t-umami-d334436440 — umami POST /api/teams/{teamId}/users/{userId}

블록 발견 15 / 유지 3 / 탈락 12 / 절단 True · 토큰 3713 → 4042

유지 블록: perm_table:ROLES(constants.ts:174-182), perm_table:PERMISSIONS(constants.ts:191-201), perm_table:ROLE_PERMISSIONS(constants.ts:203-234, clipped)

```
[관련 권한 코드]
FILE src/lib/constants.ts:174-182 [perm_table ROLES]
export const ROLES = {
  admin: 'admin',
  user: 'user',
  viewOnly: 'view-only',
  teamOwner: 'team-owner',
  teamManager: 'team-manager',
  teamMember: 'team-member',
  teamViewOnly: 'team-view-only',
} as const;

FILE src/lib/constants.ts:191-201 [perm_table PERMISSIONS]
export const PERMISSIONS = {
  all: 'all',
  websiteCreate: 'website:create',
  websiteUpdate: 'website:update',
  websiteDelete: 'website:delete',
  websiteTransferToTeam: 'website:transfer-to-team',
  websiteTransferToUser: 'website:transfer-to-user',
  teamCreate: 'team:create',
  teamUpdate: 'team:update',
  teamDelete: 'team:delete',
} as const;

FILE src/lib/constants.ts:203-234 [perm_table ROLE_PERMISSIONS]
export const ROLE_PERMISSIONS = {
  [ROLES.admin]: [PERMISSIONS.all],
  [ROLES.user]: [
    PERMISSIONS.websiteCreate,
    PERMISSIONS.websiteUpdate,
    PERMISSIONS.websiteDelete,
    PERMISSIONS.teamCreate,
  ],
  [ROLES.viewOnly]: [],
  [ROLES.teamOwner]: [
    PERMISSIONS.teamUpdate,
    PERMISSIONS.teamDelete,
    PERMISSIONS.websiteCreate,
    PERMISSIONS.websiteUpdate,
    PERMISSIONS.websiteDelete,
    PERMISSIONS.websiteTransferToTeam,
      ...
```

### v5t-umami-a8feaa9ffc — umami GET /api/me

블록 발견 9 / 유지 9 / 탈락 0 / 절단 False · 토큰 3334 → 3975

유지 블록: helper:isApiKeyEnabled(api-key.ts:40-42), helper:isApiKey(api-key.ts:32-34), helper:checkApiKeyAuth(auth.ts:32-69), helper:authKey(auth.ts:150-150), helper:ROLES(constants.ts:174-182), helper:isApiKeyBlockedPath(api-key.ts:36-38), helper:hashApiKey(api-key.ts:24-26), helper:createAuthKey(crypto.ts:68-70), helper:teamOwner(route.ts:21-29)

```
[관련 권한 코드]
FILE src/lib/api-key.ts:40-42 [helper isApiKeyEnabled]
export function isApiKeyEnabled() {
  return !process.env.CLOUD_MODE;
}

FILE src/lib/api-key.ts:32-34 [helper isApiKey]
export function isApiKey(token?: string | null): token is string {
  return typeof token === 'string' && token.startsWith(API_KEY_PREFIX);
}

FILE src/lib/auth.ts:32-69 [helper checkApiKeyAuth]
export async function checkApiKeyAuth(request: Request, token: string) {
  const { pathname } = new URL(request.url);
  if (isApiKeyBlockedPath(pathname)) {
    log('API key not allowed for path', pathname);
    return null;
  }
  const apiKey = await getApiKeyByHash(hashApiKey(token));
  if (!apiKey) {
    log('API key not found');
    return null;
  }
  const user: any = await getUser(apiKey.userId);
  if (!user?.id) {
    log('API key user not found');
    return null;
  }
  const lastUsedAt = apiKey.lastUsedAt?.getTime() ?? 0;
  if (Date.now() - lastUsedAt > API_KEY_LAST_USED_INTERVAL) {
    updateApiKeyLastUsed(apiKey.id).catch(e => log(e));
  }
  delete user.password;
  user.isAdmin = user.role === ROLES.admin;
  return {
    token,
    user,
    authType: 'api-key' as const,
    apiKey: { id: apiKey.id, name: apiKey.name },
  };
}

FILE src/lib/auth.ts:150-150 [helper authKey]
  const authKey = `auth:${createAuthKey()}`;

FILE src/lib/constants.ts:174-182 [helper ROLES]
export const ROLES = {
  admin: 'admin',
  user: 'user',
  viewOnly: 'view-only',
  teamOwner: 'team-owner',
  teamManager: 'team-manager',
  teamMember: 'team-member',
  teamViewOnly: 'team-view-only',
} as const;

FILE src/lib/api-key.ts:36-38 [helper isApiKeyBlockedPath]
export function isApiKeyBlockedPath(pathname: string) {
  return API_KEY_BLOCKED_PATHS.some(path => pathname === path || pathname.startsWith(`${path}/`));
}

FILE src/lib/api-key.ts:24-26 [helper hashApiKey]
export function hashApiKey(key: string) {
  return hash(key);
}

FILE src/lib/crypto.ts:68-70 [helper createAuthKey]
export function createAuthKey() {
  return crypto.randomBytes(16).toString('hex');
}

FILE src/app/api/share/[slug]/route.ts:21-29 [helper teamOwner]
    const teamOwner = await prisma.client.teamUser.findFirst({
      where: {
        teamId: entity.teamId,
        role: ROLES.teamOwner,
      },
      select: {
        userId: true,
      },
    });
```

