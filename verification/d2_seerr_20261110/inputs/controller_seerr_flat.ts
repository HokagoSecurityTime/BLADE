// Seerr v3.5.1 (564bfb08) handlers flattened for BLADE (see build_inputs.py header for the two transformations).
// Sources: server/routes/{request,issue,issueComment}.ts, server/routes/user/index.ts, server/routes/settings/index.ts

// --- GET /api/v1/request/{requestId}  (from server/routes/request.ts route '/:requestId')
requestRoutes.get('/api/v1/request/{requestId}', async (req, res, next) => {
  const requestRepository = getRepository(MediaRequest);

  try {
    const request = await requestRepository.findOneOrFail({
      where: { id: Number(req.params.requestId) },
      relations: { requestedBy: true, modifiedBy: true },
    });

    if (
      request.requestedBy.id !== req.user?.id &&
      !req.user?.hasPermission(
        [Permission.MANAGE_REQUESTS, Permission.REQUEST_VIEW],
        { type: 'or' }
      )
    ) {
      return next({
        status: 403,
        message: 'You do not have permission to view this request.',
      });
    }

    return res.status(200).json(request);
  } catch (e) {
    logger.debug('Failed to retrieve request.', {
      label: 'API',
      errorMessage: e.message,
    });
    next({ status: 404, message: 'Request not found.' });
  }
});

// --- PUT /api/v1/request/{requestId}  (from server/routes/request.ts route '/:requestId')
requestRoutes.put('/api/v1/request/{requestId}',
  async (req, res, next) => {
    const requestRepository = getRepository(MediaRequest);
    const userRepository = getRepository(User);
    const requestId = Number(req.params.requestId);
    try {
      // Ordering is request then owner here, user then media on create, so no cycle
      return await requestLock.dispatch(requestKey(requestId), async () => {
        const request = await requestRepository.findOne({
          where: {
            id: requestId,
          },
        });

        if (!request) {
          return next({ status: 404, message: 'Request not found.' });
        }

        if (
          (request.requestedBy.id !== req.user?.id ||
            (req.body.mediaType !== 'tv' &&
              !req.user?.hasPermission(Permission.REQUEST_ADVANCED))) &&
          !req.user?.hasPermission(Permission.MANAGE_REQUESTS)
        ) {
          return next({
            status: 403,
            message: 'You do not have permission to modify this request.',
          });
        }

        if (request.status !== MediaRequestStatus.PENDING) {
          return next({
            status: 409,
            message: 'Only pending requests can be modified.',
          });
        }

        const previousOwnerId = request.requestedBy.id;
        let requestUser = request.requestedBy;

        if (
          req.body.userId &&
          req.body.userId !== request.requestedBy.id &&
          !req.user?.hasPermission([
            Permission.MANAGE_USERS,
            Permission.MANAGE_REQUESTS,
          ])
        ) {
          return next({
            status: 403,
            message: 'You do not have permission to modify the request user.',
          });
        } else if (req.body.userId) {
          requestUser = await userRepository.findOneOrFail({
            where: { id: req.body.userId },
          });
        }

        // Reassignment moves every season on the request onto the new owner's
        // quota, so it is charged in full rather than as a delta
        const ownerChanging = requestUser.id !== previousOwnerId;

        return requestLock.dispatch(userKey(requestUser.id), async () => {
          if (req.body.mediaType === MediaType.MOVIE) {
            if (ownerChanging && !request.ignoreQuota) {
              const quotas = await requestUser.getQuota();

              if (quotas.movie.restricted) {
                return next({
                  status: 403,
                  message: 'Movie Quota exceeded.',
                });
              }
            }

            request.serverId = req.body.serverId;
            request.profileId = req.body.profileId;
            request.rootFolder = req.body.rootFolder;
            request.tags = req.body.tags;
            request.requestedBy = requestUser as User;

            await requestRepository.save(request);
          } else if (req.body.mediaType === MediaType.TV) {
            const mediaRepository = getRepository(Media);
            request.serverId = req.body.serverId;
            request.profileId = req.body.profileId;
            request.rootFolder = req.body.rootFolder;
            request.languageProfileId = req.body.languageProfileId;
            request.tags = req.body.tags;
            request.requestedBy = requestUser as User;

            const requestedSeasons = req.body.seasons as number[] | undefined;

            if (!requestedSeasons || requestedSeasons.length === 0) {
              throw new Error(
                'Missing seasons. If you want to cancel a series request, use the DELETE method.'
              );
            }

            // Same key as create, so an edit cannot claim a season that a new
            // request is taking at the same moment
            return mediaLock.dispatch(
              mediaKey(MediaType.TV, request.media.tmdbId),
              async () => {
                // Get existing media so we can work with all the requests
                const media = await mediaRepository.findOneOrFail({
                  where: {
                    tmdbId: request.media.tmdbId,
                    mediaType: MediaType.TV,
                  },
                  relations: { requests: true },
                });

                // Get all requested seasons that are not part of this request we are editing
                const existingSeasons = media.requests
                  .filter(
                    (r) =>
                      r.is4k === request.is4k &&
                      r.id !== request.id &&
                      r.status !== MediaRequestStatus.DECLINED &&
                      r.status !== MediaRequestStatus.COMPLETED
                  )
                  .reduce((seasons, r) => {
                    const combinedSeasons = r.seasons.map(
                      (season) => season.seasonNumber
                    );

                    return [...seasons, ...combinedSeasons];
                  }, [] as number[]);

                const currentSeasons = request.seasons.map(
                  (s) => s.seasonNumber
                );

                // Seasons the media already covers cannot be requested again, while
                // the ones this request holds stay on it
                const coveredSeasons = (media.seasons ?? [])
                  .filter(
                    (season) =>
                      season[request.is4k ? 'status4k' : 'status'] !==
                        MediaStatus.UNKNOWN &&
                      season[request.is4k ? 'status4k' : 'status'] !==
                        MediaStatus.DELETED
                  )
                  .map((season) => season.seasonNumber)
                  .filter((sn) => !currentSeasons.includes(sn));

                const filteredSeasons = requestedSeasons.filter(
                  (rs) => !existingSeasons.includes(rs)
                );

                const keptSeasons = filteredSeasons.filter((sn) =>
                  currentSeasons.includes(sn)
                );

                const newSeasons = filteredSeasons.filter(
                  (sn) =>
                    !currentSeasons.includes(sn) && !coveredSeasons.includes(sn)
                );

                const resultingSeasonCount =
                  keptSeasons.length + newSeasons.length;

                if (resultingSeasonCount === 0) {
                  return next({
                    status: 202,
                    message: 'No seasons available to request',
                  });
                }

                if (!request.ignoreQuota) {
                  const quotas = await requestUser.getQuota();

                  // Only the seasons getQuota already counted for this owner are
                  // paid for, so the edit is charged for everything it left out
                  const quotaWindowStart = new Date();
                  if (quotas.tv.days) {
                    quotaWindowStart.setDate(
                      quotaWindowStart.getDate() - quotas.tv.days
                    );
                  }

                  const countedAlready =
                    !ownerChanging &&
                    (!quotas.tv.days || request.createdAt > quotaWindowStart);

                  const priorSeasonCount = countedAlready
                    ? request.seasons.length
                    : 0;
                  const requiredSeasons =
                    resultingSeasonCount - priorSeasonCount;

                  if (
                    quotas.tv.limit &&
                    requiredSeasons > (quotas.tv.remaining ?? 0)
                  ) {
                    return next({
                      status: 403,
                      message: 'Series Quota exceeded.',
                    });
                  }
                }

                request.seasons = request.seasons.filter((rs) =>
                  keptSeasons.includes(rs.seasonNumber)
                );

                if (newSeasons.length > 0) {
                  logger.debug('Adding new seasons to request', {
                    label: 'Media Request',
                    newSeasons,
                  });
                  request.seasons.push(
                    ...newSeasons.map(
                      (ns) =>
                        new SeasonRequest({
                          seasonNumber: ns,
                          status: MediaRequestStatus.PENDING,
                        })
                    )
                  );
                }

                await requestRepository.save(request);

                return res.status(200).json(request);
              }
            );
          }

          return res.status(200).json(request);
        });
      });
    } catch (e) {
      next({ status: 500, message: e.message });
    }
  }
);

// --- DELETE /api/v1/request/{requestId}  (from server/routes/request.ts route '/:requestId')
requestRoutes.delete('/api/v1/request/{requestId}', async (req, res, next) => {
  const requestRepository = getRepository(MediaRequest);
  const requestId = Number(req.params.requestId);

  try {
    return await requestLock.dispatch(requestKey(requestId), async () => {
      const request = await requestRepository.findOneOrFail({
        where: { id: requestId },
        relations: { requestedBy: true, modifiedBy: true },
      });

      if (
        !req.user?.hasPermission(Permission.MANAGE_REQUESTS) &&
        (request.requestedBy.id !== req.user?.id ||
          request.status !== MediaRequestStatus.PENDING)
      ) {
        return next({
          status: 401,
          message: 'You do not have permission to delete this request.',
        });
      }

      await requestRepository.remove(request);

      return res.status(204).send();
    });
  } catch (e) {
    logger.error('Something went wrong deleting a request.', {
      label: 'API',
      errorMessage: e.message,
    });
    next({ status: 404, message: 'Request not found.' });
  }
});

// --- GET /api/v1/issue/{issueId}  (from server/routes/issue.ts route '/:issueId')
issueRoutes.get('/api/v1/issue/{issueId}',
  isAuthenticated(
    [
      Permission.MANAGE_ISSUES,
      Permission.VIEW_ISSUES,
      Permission.CREATE_ISSUES,
    ],
    { type: 'or' }
  ),
  async (req, res, next) => {
    const issueRepository = getRepository(Issue);
    // Satisfy typescript here. User is set, we assure you!
    if (!req.user) {
      return next({ status: 500, message: 'User missing from request.' });
    }

    try {
      const issue = await issueRepository
        .createQueryBuilder('issue')
        .leftJoinAndSelect('issue.comments', 'comments')
        .leftJoinAndSelect('issue.createdBy', 'createdBy')
        .leftJoinAndSelect('comments.user', 'user')
        .leftJoinAndSelect('issue.media', 'media')
        .where('issue.id = :issueId', { issueId: Number(req.params.issueId) })
        .getOneOrFail();

      if (
        issue.createdBy.id !== req.user.id &&
        !req.user.hasPermission(
          [Permission.MANAGE_ISSUES, Permission.VIEW_ISSUES],
          { type: 'or' }
        )
      ) {
        return next({
          status: 403,
          message: 'You do not have permission to view this issue.',
        });
      }

      return res.status(200).json(issue);
    } catch (e) {
      logger.debug('Failed to retrieve issue.', {
        label: 'API',
        errorMessage: e.message,
      });
      next({ status: 500, message: 'Issue not found.' });
    }
  }
);

// --- POST /api/v1/issue/{issueId}/comment  (from server/routes/issue.ts route '/:issueId/comment')
issueRoutes.post('/api/v1/issue/{issueId}/comment',
  isAuthenticated([Permission.MANAGE_ISSUES, Permission.CREATE_ISSUES], {
    type: 'or',
  }),
  async (req, res, next) => {
    const issueRepository = getRepository(Issue);
    // Satisfy typescript here. User is set, we assure you!
    if (!req.user) {
      return next({ status: 500, message: 'User missing from request.' });
    }

    try {
      const issue = await issueRepository.findOneOrFail({
        where: { id: Number(req.params.issueId) },
      });

      if (
        issue.createdBy.id !== req.user.id &&
        !req.user.hasPermission(Permission.MANAGE_ISSUES)
      ) {
        return next({
          status: 403,
          message: 'You do not have permission to comment on this issue.',
        });
      }

      const comment = new IssueComment({
        message: req.body.message,
        user: req.user,
      });

      issue.comments = [...issue.comments, comment];
      issue.updatedAt = new Date();
      await issueRepository.save(issue);

      return res.status(200).json(issue);
    } catch (e) {
      logger.debug('Something went wrong creating an issue comment.', {
        label: 'API',
        errorMessage: e.message,
      });
      next({ status: 500, message: 'Issue not found.' });
    }
  }
);

// --- DELETE /api/v1/issue/{issueId}  (from server/routes/issue.ts route '/:issueId')
issueRoutes.delete('/api/v1/issue/{issueId}',
  isAuthenticated([Permission.MANAGE_ISSUES, Permission.CREATE_ISSUES], {
    type: 'or',
  }),
  async (req, res, next) => {
    const issueRepository = getRepository(Issue);

    try {
      const issue = await issueRepository.findOneOrFail({
        where: { id: Number(req.params.issueId) },
        relations: { createdBy: true },
      });

      if (
        !req.user?.hasPermission(Permission.MANAGE_ISSUES) &&
        (issue.createdBy.id !== req.user?.id || issue.comments.length > 1)
      ) {
        return next({
          status: 401,
          message: 'You do not have permission to delete this issue.',
        });
      }

      await issueRepository.remove(issue);

      return res.status(204).send();
    } catch (e) {
      logger.error('Something went wrong deleting an issue.', {
        label: 'API',
        errorMessage: e.message,
      });
      next({ status: 404, message: 'Issue not found.' });
    }
  }
);

// --- PUT /api/v1/issueComment/{commentId}  (from server/routes/issueComment.ts route '/:commentId')
issueCommentRoutes.put('/api/v1/issueComment/{commentId}',
  isAuthenticated([Permission.MANAGE_ISSUES, Permission.CREATE_ISSUES], {
    type: 'or',
  }),
  async (req, res, next) => {
    const issueCommentRepository = getRepository(IssueComment);

    try {
      const comment = await issueCommentRepository.findOneOrFail({
        where: { id: Number(req.params.commentId) },
      });

      if (comment.user.id !== req.user?.id) {
        return next({
          status: 403,
          message: 'You can only edit your own comments.',
        });
      }

      comment.message = req.body.message;

      await issueCommentRepository.save(comment);

      return res.status(200).json(comment);
    } catch (e) {
      logger.debug('Put request for issue comment failed', {
        label: 'API',
        errorMessage: e.message,
      });
      next({ status: 404, message: 'Issue comment not found.' });
    }
  }
);

// --- GET /api/v1/user/{userId}  (from server/routes/user_index.ts route '/:id')
router.get('/api/v1/user/{userId}', async (req, res, next) => {
  try {
    const userRepository = getRepository(User);
    const user = await userRepository.findOneOrFail({
      where: { id: Number(req.params.id) },
    });

    const isOwnProfile = req.user?.id === user.id;
    const isAdmin = req.user?.hasPermission(Permission.MANAGE_USERS);

    return res.status(200).json(user.filter(isOwnProfile || isAdmin));
  } catch {
    next({ status: 404, message: 'User not found.' });
  }
});

// --- GET /api/v1/user/{userId}/quota  (from server/routes/user_index.ts route '/:id/quota')
router.get('/api/v1/user/{userId}/quota',
  async (req, res, next) => {
    try {
      const userRepository = getRepository(User);

      if (
        Number(req.params.id) !== req.user?.id &&
        !req.user?.hasPermission(
          [Permission.MANAGE_USERS, Permission.MANAGE_REQUESTS],
          { type: 'and' }
        )
      ) {
        return next({
          status: 403,
          message:
            "You do not have permission to view this user's request limits.",
        });
      }

      const user = await userRepository.findOneOrFail({
        where: { id: Number(req.params.id) },
      });

      const quotas = await user.getQuota();

      return res.status(200).json(quotas);
    } catch (e) {
      next({ status: 404, message: e.message });
    }
  }
);

// --- GET /api/v1/settings/main  (from server/routes/settings_index.ts route '/main')
settingsRoutes.get('/api/v1/settings/main', (req, res, next) => {
  const settings = getSettings();

  if (!req.user) {
    return next({ status: 400, message: 'User missing from request.' });
  }

  res.status(200).json(filteredMainSettings(req.user, settings.main));
});

// --- helpers referenced above, verbatim ---
// server/utils/profileMiddleware.ts
import { Permission } from '@server/lib/permissions';

export const isOwnProfile = (): Middleware => {
  return (req, res, next) => {
    if (req.user?.id !== Number(req.params.id)) {
      return next({
        status: 403,
        message: "You do not have permission to view this user's settings.",
      });
    }
    next();
  };
};

export const isOwnProfileOrAdmin = (): Middleware => {
  const authMiddleware: Middleware = (req, res, next) => {
    if (
      !req.user?.hasPermission(Permission.MANAGE_USERS) &&
      req.user?.id !== Number(req.params.id)
    ) {
      return next({
        status: 403,
        message: "You do not have permission to view this user's settings.",
      });
    }

    next();
  };
  return authMiddleware;
};

// server/middleware/auth.ts
import { getRepository } from '@server/datasource';
import { User } from '@server/entity/User';
import type {
  Permission,
  PermissionCheckOptions,
} from '@server/lib/permissions';
import { getSettings } from '@server/lib/settings';

export const checkUser: Middleware = async (req, _res, next) => {
  const settings = getSettings();
  let user: User | undefined | null;

  if (req.header('X-API-Key') === settings.main.apiKey) {
    const userRepository = getRepository(User);

    let userId = 1; // Work on original administrator account

    // If a User ID is provided, we will act on that user's behalf
    if (req.header('X-API-User')) {
      userId = Number(req.header('X-API-User'));
    }

    user = await userRepository.findOne({ where: { id: userId } });
  } else if (req.session?.userId) {
    const userRepository = getRepository(User);

    user = await userRepository.findOne({
      where: { id: req.session.userId },
    });
  }

  if (user) {
    req.user = user;
  }

  req.locale = user?.settings?.locale
    ? user.settings.locale
    : settings.main.locale;

  next();
};

export const isAuthenticated = (
  permissions?: Permission | Permission[],
  options?: PermissionCheckOptions
): Middleware => {
  const authMiddleware: Middleware = (req, res, next) => {
    if (!req.user || !req.user.hasPermission(permissions ?? 0, options)) {
      res.status(403).json({
        status: 403,
        error: 'You do not have permission to access this endpoint',
      });
    } else {
      next();
    }
  };
  return authMiddleware;
};
