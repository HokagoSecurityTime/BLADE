# S4 정지 지점 1-2: 10건 입력 샘플 재출력 (개선 후) — 2026-11-03

같은 10건(seed 42: Ghost 3 · Rocket.Chat 4 · Umami 3). 각 건에 ctx4096 블록 원문과 ctx6144에서 추가로 유지된 블록 이름을 적었다.

### v5t-ghost-244db7151d — ghost DELETE /ghost/api/admin/pages/{id}/

ctx4096: 발견 6 / 유지 2 / 탈락 4 / 절단 True · 토큰 3566 → 4034 · 미해석 28: authors [unresolved], rolePermissions [unresolved], Administrator [unresolved], Admin [unresolved], Author [unresolved], permissible [unresolved]
ctx6144: 유지 6 / 탈락 0 · 토큰 → 5055 · 추가 유지: permissible:post.permissible, perm_flow:canThis(core), helper:mw.authAdminApi, helper:tokenPermissionCheck

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

FILE ghost/core/server/models/post.js:1530-1600 [permissible post.permissible]
    permissible: async function permissible(
      postModel,
      action,
      context,
      unsafeAttrs,
      loadedPermissions,
      hasUserPermission,
      hasApiKeyPermission,
    ) {
      const { isContributor, isOwner, isAdmin, isEitherEditor } = setIsRoles(loadedPermissions);
      function isChanging(attr) {
        return unsafeAttrs[attr] && unsafeAttrs[attr] !== postModel.get(attr);
      }
      function isPublished() {
        return unsafeAttrs.status && unsafeAttrs.status !== 'draft';
      }
      function isDraft() {
        return postModel.get('status') === 'draft';
      }
      const isIntegration =
        loadedPermissions.apiKey &&
        _.some(loadedPermissions.apiKey.roles, { name: 'Admin Integration' });
      const isEdit = action === 'edit';
      const isAdd = action === 'add';
      const isDestroy = action === 'destroy';
      if (limitService.isLimited('members')) {
        if ((isEdit && isChanging('status') && isDraft()) || (isAdd && isPublished())) {
          await limitService.errorIfIsOverLimit('members');
        }
      }
      if (isContributor && isEdit) {
        hasUserPermission = !isChanging('status') && isDraft();
      ...
      return Promise.reject(
        new errors.NoPermissionError({
          message: tpl(messages.notEnoughPermission),
        }),
      );
    },
```

### v5t-ghost-05ee24e847 — ghost GET /ghost/api/admin/posts/{id}/gift_links/

ctx4096: 발견 4 / 유지 3 / 탈락 1 / 절단 True · 토큰 3314 → 4016 · 미해석 16: module.exports.authAdminApi [unresolved], auth.authenticate.authenticateAdminApi [unresolved], shared.middleware.urlRedirects.adminSSLAndHostRedirect [unresolved], permissionsService.canThis [unresolved], isOwner [unresolved], setIsRoles [unresolved]
ctx6144: 유지 4 / 탈락 0 · 토큰 → 4483 · 추가 유지: helper:tokenPermissionCheck

```
[관련 권한 코드]
FILE ghost/core/server/services/permissions/permissions-data.ts:1-235 [perm_table rolePermissions[gift_link,post]]
permissions.gift_link: ['manage', 'removeAll'],
rolePermissions.Administrator.gift_link: 'all',
rolePermissions.Admin Integration.gift_link: ['manage'],
rolePermissions.Super Editor.gift_link: ['manage'],
rolePermissions.Editor.gift_link: ['manage'],
permissions.post: ['browse', 'read', 'edit', 'add', 'destroy', 'publish'],
rolePermissions.Administrator.post: 'all',
rolePermissions.DB Backup Integration.post: ['browse'],
rolePermissions.Scheduler Integration.post: ['publish'],
rolePermissions.Admin Integration.post: 'all',
rolePermissions.Super Editor.post: 'all',
rolePermissions.Editor.post: 'all',
rolePermissions.Author.post: ['browse', 'read', 'edit', 'add', 'destroy'],
rolePermissions.Contributor.post: ['browse', 'read', 'edit', 'add', 'destroy'],

FILE ghost/core/server/models/post.js:1530-1600 [permissible post.permissible]
    permissible: async function permissible(
      postModel,
      action,
      context,
      unsafeAttrs,
      loadedPermissions,
      hasUserPermission,
      hasApiKeyPermission,
    ) {
      const { isContributor, isOwner, isAdmin, isEitherEditor } = setIsRoles(loadedPermissions);
      function isChanging(attr) {
        return unsafeAttrs[attr] && unsafeAttrs[attr] !== postModel.get(attr);
      }
      function isPublished() {
        return unsafeAttrs.status && unsafeAttrs.status !== 'draft';
      }
      function isDraft() {
        return postModel.get('status') === 'draft';
      }
      const isIntegration =
        loadedPermissions.apiKey &&
        _.some(loadedPermissions.apiKey.roles, { name: 'Admin Integration' });
      const isEdit = action === 'edit';
      const isAdd = action === 'add';
      const isDestroy = action === 'destroy';
      if (limitService.isLimited('members')) {
        if ((isEdit && isChanging('status') && isDraft()) || (isAdd && isPublished())) {
          await limitService.errorIfIsOverLimit('members');
        }
      }
      if (isContributor && isEdit) {
        hasUserPermission = !isChanging('status') && isDraft();
      ...
      return Promise.reject(
        new errors.NoPermissionError({
          message: tpl(messages.notEnoughPermission),
        }),
      );
    },

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
      ...
```

### v5t-ghost-6e1dca8d3d — ghost PUT /ghost/api/admin/authentication/password_reset/

ctx4096: 발견 0 / 유지 0 / 탈락 0 / 절단 False · 토큰 3173 → 3184 · 미해석 2: authentication [unresolved], api.authentication.resetPassword [unresolved]
ctx6144: 유지 0 / 탈락 0 · 토큰 → 3184 · 추가 유지: (없음)

```
[관련 권한 코드]
(없음)
```

### v5t-rocketchat-6aebdee592 — rocketchat GET /api/v1/groups.list

ctx4096: 발견 0 / 유지 0 / 탈락 0 / 절단 False · 토큰 3275 → 3286 · 미해석 0: 
ctx6144: 유지 0 / 탈락 0 · 토큰 → 3286 · 추가 유지: (없음)

```
[관련 권한 코드]
(없음)
```

### v5t-rocketchat-63107638c6 — rocketchat POST /api/v1/rooms.leave

ctx4096: 발견 4 / 유지 2 / 탈락 2 / 절단 True · 토큰 3831 → 4006 · 미해석 11: checkedArchived [unresolved], allowMemberAction [unresolved], RoomMemberActions.LEAVE [unresolved], owners [unresolved], Roles.countUsersInRole [unresolved], UserWithRoles (depth2 in hasPermission.ts) [external:@rocket.chat/core-services]
ctx6144: 유지 4 / 탈락 0 · 토큰 → 4212 · 추가 유지: helper:hasRoleAsync, helper:hasAnyRoleAsync

```
[관련 권한 코드]
FILE apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 [perm_table permission→roles]
{ _id: 'leave-c', roles: ['admin', 'user', 'federated-external', 'bot', 'anonymous', 'app'] },
{ _id: 'leave-p', roles: ['admin', 'user', 'federated-external', 'bot', 'anonymous', 'app'] },

FILE apps/meteor/server/lib/authorization/hasPermission.ts:15-19 [helper hasPermissionAsync]
export const hasPermissionAsync = async (
	user: IUser['_id'] | UserWithRoles,
	permissionId: IPermission['_id'],
	scope?: IRoom['_id'],
): Promise<boolean> => Authorization.hasPermission(toSubject(user), permissionId, scope);
```

### v5t-rocketchat-3c6f0d2295 — rocketchat POST /api/v1/groups.unarchive

ctx4096: 발견 6 / 유지 2 / 탈락 4 / 절단 True · 토큰 3716 → 3961 · 미해석 6: checkedArchived [unresolved], isRegisterUser [unresolved], UserWithRoles (depth2 in hasPermission.ts) [external:@rocket.chat/core-services], permissionId (depth2 in hasPermission.ts) [not imported / not defined in file], IPermission (depth2 in hasPermission.ts) [external:@rocket.chat/core-typings], Authorization.hasPermission (depth2 in hasPermission.ts) [external:@rocket.chat/core-services]
ctx6144: 유지 6 / 탈락 0 · 토큰 → 4580 · 추가 유지: perm_flow:canAccessPublicRoom, perm_flow:canAccessRoom, perm_flow:canAccessRoomLivechat, helper:hasPermissionAsync

```
[관련 권한 코드]
FILE apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 [perm_table permission→roles]
{ _id: 'unarchive-room', roles: ['admin'] },

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
		}
		const team = await Team.findOneById<Pick<ITeam, 'type'>>(room.teamId, {
			projection: { type: 1 },
		});
		if (team?.type === TeamType.PUBLIC) {
			return canAccessPublicRoom(user);
		}
		const membership =
			user?._id &&
      ...
```

### v5t-rocketchat-26b775fea8 — rocketchat POST /api/v1/integrations.remove

ctx4096: 발견 4 / 유지 2 / 탈락 2 / 절단 True · 토큰 3824 → 4048 · 미해석 8: hasAny [unresolved], not_authorized [unresolved], Unauthorized [unresolved], hasAny (depth2 in integrations.ts) [not imported / not defined in file], UserWithRoles (depth2 in hasPermission.ts) [external:@rocket.chat/core-services], permissionId (depth2 in hasPermission.ts) [not imported / not defined in file]
ctx6144: 유지 4 / 탈락 0 · 토큰 → 4268 · 추가 유지: helper:permissionsRequired, helper:hasPermissionAsync

```
[관련 권한 코드]
FILE apps/meteor/server/lib/authorization/constant/permissions.ts:1-242 [perm_table permission→roles]
{ _id: 'manage-outgoing-integrations', roles: ['admin'] },
{ _id: 'manage-own-outgoing-integrations', roles: ['admin'] },
{ _id: 'manage-incoming-integrations', roles: ['admin'] },
{ _id: 'manage-own-incoming-integrations', roles: ['admin'] },

FILE apps/meteor/server/api/api.helpers.ts:75-110 [perm_flow checkPermissions(permissionsRequired)]
export function checkPermissions(options: { permissionsRequired?: PermissionsRequiredKey }) {
	if (!options.permissionsRequired) {
		return false;
	}
	if (isPermissionsPayload(options.permissionsRequired)) {
		return true;
	}
	if (isLegacyPermissionsPayload(options.permissionsRequired)) {
		options.permissionsRequired = {
			'*': {
				operation: 'hasAll',
				permissions: options.permissionsRequired,
			},
		};
      ...
```

### v5t-umami-b89ee084f9 — umami GET /api/websites

ctx4096: 발견 1 / 유지 1 / 탈락 0 / 절단 False · 토큰 3343 → 3497 · 미해석 8: isApiKeyEnabled [unresolved], isApiKey [unresolved], checkApiKeyAuth [unresolved], user.isAdmin [unresolved], ROLES.admin [unresolved], authKey [unresolved]
ctx6144: 유지 1 / 탈락 0 · 토큰 → 3497 · 추가 유지: (없음)

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
```

### v5t-umami-d334436440 — umami POST /api/teams/{teamId}/users/{userId}

ctx4096: 발견 4 / 유지 2 / 탈락 2 / 절단 False · 토큰 3713 → 4022 · 미해석 31: auth.user.isAdmin [unresolved], isApiKeyEnabled [unresolved], isApiKey [unresolved], checkApiKeyAuth [unresolved], user.isAdmin [unresolved], ROLES.admin [unresolved]
ctx6144: 유지 4 / 탈락 0 · 토큰 → 4210 · 추가 유지: perm_table:PERMISSIONS, helper:TEAM_ROLE_RANK

```
[관련 권한 코드]
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
    PERMISSIONS.websiteTransferToUser,
  ],
  [ROLES.teamManager]: [
    PERMISSIONS.teamUpdate,
    PERMISSIONS.websiteCreate,
    PERMISSIONS.websiteUpdate,
    PERMISSIONS.websiteDelete,
    PERMISSIONS.websiteTransferToTeam,
  ],
  [ROLES.teamMember]: [
    PERMISSIONS.websiteCreate,
    PERMISSIONS.websiteUpdate,
    PERMISSIONS.websiteDelete,
  ],
  [ROLES.teamViewOnly]: [],
} as const;

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
```

### v5t-umami-a8feaa9ffc — umami GET /api/me

ctx4096: 발견 0 / 유지 0 / 탈락 0 / 절단 False · 토큰 3334 → 3345 · 미해석 7: Auth [unresolved], isApiKeyEnabled [unresolved], isApiKey [unresolved], checkApiKeyAuth [unresolved], authKey [unresolved], user.isAdmin [unresolved]
ctx6144: 유지 0 / 탈락 0 · 토큰 → 3345 · 추가 유지: (없음)

```
[관련 권한 코드]
(없음)
```

