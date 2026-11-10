# test_v5 라벨 상한 측정 (60건 표본) — AI 검수자(Claude) 간 일치도 — 사람 일치도 아님

**주의: 이 보고서의 검수자는 검수자 Claude-A / Claude-B (AI 대리 검수, 사람 아님)이다.** 사람 간 일치도가 아니며, 사람 검수본이 회수되면 같은 스크립트로 다시 채점한다.

- 표본: test_v5 283건(동결 SHA `7b8e4a940967ec47…`) 중 60건, label support 비례 층화(seed 42), reports/eval/human_agreement_v5/sample_60.json
- 입력: A = review/human_agreement_v5_A_AI대리검수.xlsx (`c2fab0951a71ec84…`), B = review/human_agreement_v5_B_AI대리검수.xlsx (`164c39883983940d…`). 두 시트는 현재 정답·AI 1차 판정·모델 예측 없이 엔드포인트·OAS·핸들러 코드·v3.0.1 라벨 정의만 제공했다.
- 검수 규약 G1~G8은 시트에 넣지 않았다(지시의 "label 정의표(v3.0.1)"만 제공). 현재 정답은 G1~G8까지 적용해 확정한 것이므로 정답 대비 일치율은 보수적으로 읽는다.
- v5 수치는 reports/eval/lora_v5/lora_v5_s{42,43,44}/eval의 기존 oas_code 예측을 같은 60건으로 재채점한 것이다(재추론 없음). 학습·추론 없음, 커밋 없음.
- macro-F1은 기준(reference) 쪽 support>0인 label 평균(tenant_match는 정답 0건이라 제외; A/B가 tenant_match를 고른 경우 해당 label의 FP로만 반영). kappa는 7 label Cohen's kappa.

## 1. 요약 (AI 검수자(Claude) 간 일치도, 사람 일치도 아님)

| 비교 | n | 일치율 | Cohen's κ | macro-F1 | 비고 |
|---|---:|---:|---:|---:|---|
| A vs B | 60 | 0.917 | 0.894 | 0.914 | A를 기준으로 둔 B |
| A vs 현재 정답 | 60 | 0.833 | 0.783 | 0.870 | 정답 기준 |
| B vs 현재 정답 | 60 | 0.850 | 0.805 | 0.880 | 정답 기준 |
| v5 3 seed vs 현재 정답 (oas_code) | 60 | 0.711 ± 0.038 | - | 0.700 ± 0.052 | seed별 s42 0.641 / s43 0.722 / s44 0.737 |

세 쪽(A·B·정답) 모두 같은 건: 48/60. 불일치 12건 유형: A=B≠정답 7, B=정답≠A 3, A=정답≠B 2.

불일치 쌍 집계(정답 → A / B, 프로젝트별 건수):

- role_required → A manual_review_required / B manual_review_required: rocketchat 5건
- manual_review_required → A membership_required / B manual_review_required: rocketchat 3건
- manual_review_required → A manual_review_required / B owner_or_admin: umami 2건
- manual_review_required → A owner_or_admin / B owner_or_admin: rocketchat 1건
- manual_review_required → A role_required / B role_required: ghost 1건

## 2. label 분포 (60건)

| label | 정답 | A | B | v5 s42 | v5 s43 | v5 s44 |
|---|---:|---:|---:|---:|---:|---:|
| public | 4 | 4 | 4 | 3 | 3 | 3 |
| role_required | 24 | 20 | 20 | 21 | 23 | 22 |
| membership_required | 7 | 10 | 7 | 8 | 9 | 6 |
| tenant_match | 0 | 0 | 0 | 0 | 0 | 0 |
| owner_match | 7 | 7 | 7 | 10 | 8 | 9 |
| owner_or_admin | 4 | 5 | 7 | 5 | 5 | 7 |
| manual_review_required | 14 | 14 | 15 | 13 | 12 | 13 |

## 3. label별 일치 (A vs B, A 기준)

| label | A가 고른 수 | B가 고른 수 | 둘 다(tp) | P | R | F1 |
|---|---:|---:|---:|---:|---:|---:|
| public | 4 | 4 | 4 | 1.000 | 1.000 | 1.000 |
| role_required | 20 | 20 | 20 | 1.000 | 1.000 | 1.000 |
| membership_required | 10 | 7 | 7 | 1.000 | 0.700 | 0.824 |
| tenant_match | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 |
| owner_match | 7 | 7 | 7 | 1.000 | 1.000 | 1.000 |
| owner_or_admin | 5 | 7 | 5 | 0.714 | 1.000 | 0.833 |
| manual_review_required | 14 | 15 | 12 | 0.800 | 0.857 | 0.828 |

### A vs B 혼동표 (행 = A, 열 = B)

| A \ B | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| role_required | 0 | 20 | 0 | 0 | 0 | 0 | 0 |
| membership_required | 0 | 0 | 7 | 0 | 0 | 0 | 3 |
| tenant_match | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| owner_match | 0 | 0 | 0 | 0 | 7 | 0 | 0 |
| owner_or_admin | 0 | 0 | 0 | 0 | 0 | 5 | 0 |
| manual_review_required | 0 | 0 | 0 | 0 | 0 | 2 | 12 |

## 4. label별 F1 — 현재 정답 기준 (support = 정답 건수)

| label | support | A F1 | B F1 | v5 s42 | v5 s43 | v5 s44 | v5 평균 |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 4 | 1.000 | 1.000 | 0.857 | 0.857 | 0.857 | 0.857 |
| role_required | 24 | 0.864 | 0.864 | 0.756 | 0.808 | 0.783 | 0.782 |
| membership_required | 7 | 0.824 | 1.000 | 0.667 | 0.750 | 0.769 | 0.729 |
| tenant_match | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| owner_match | 7 | 1.000 | 1.000 | 0.824 | 0.933 | 0.875 | 0.877 |
| owner_or_admin | 4 | 0.889 | 0.727 | 0.222 | 0.444 | 0.545 | 0.404 |
| manual_review_required | 14 | 0.643 | 0.690 | 0.518 | 0.538 | 0.593 | 0.550 |

### 정답 vs A 혼동표 (행 = 정답, 열 = A)

| 정답 \ A | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| role_required | 0 | 19 | 0 | 0 | 0 | 0 | 5 |
| membership_required | 0 | 0 | 7 | 0 | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| owner_match | 0 | 0 | 0 | 0 | 7 | 0 | 0 |
| owner_or_admin | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| manual_review_required | 0 | 1 | 3 | 0 | 0 | 1 | 9 |

### 정답 vs B 혼동표 (행 = 정답, 열 = B)

| 정답 \ B | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| role_required | 0 | 19 | 0 | 0 | 0 | 0 | 5 |
| membership_required | 0 | 0 | 7 | 0 | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| owner_match | 0 | 0 | 0 | 0 | 7 | 0 | 0 |
| owner_or_admin | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| manual_review_required | 0 | 1 | 0 | 0 | 0 | 3 | 10 |

## 5. 확신도별 정답 일치

| 확신도 | A n | A 일치 | B n | B 일치 |
|---|---:|---:|---:|---:|
| 상 | 33 | 32 (97%) | 23 | 23 (100%) |
| 중 | 24 | 18 (75%) | 36 | 28 (78%) |
| 하 | 3 | 0 (0%) | 1 | 0 (0%) |

## 6. 불일치 목록 (12건; A·B·정답 중 하나라도 다른 건)

| id | project | method path | 정답 | A (확신) | B (확신) | v5 s42/43/44 | 유형 |
|---|---|---|---|---|---|---|---|
| v5t-ghost-924636cc9d | ghost | GET /ghost/api/admin/posts/ | manual_review_required | role_required (중) | role_required (중) | role_required / role_required / role_required | A=B≠정답 |
| v5t-rocketchat-0398a2f985 | rocketchat | GET /api/v1/rooms.membersOrderedByRole | manual_review_required | membership_required (하) | manual_review_required (중) | manual_review_required / manual_review_required / manual_review_required | B=정답≠A |
| v5t-rocketchat-0780c8e386 | rocketchat | POST /api/v1/groups.addOwner | role_required | manual_review_required (중) | manual_review_required (중) | role_required / role_required / role_required | A=B≠정답 |
| v5t-rocketchat-09c0e4be92 | rocketchat | POST /api/v1/groups.invite | role_required | manual_review_required (중) | manual_review_required (중) | role_required / role_required / manual_review_required | A=B≠정답 |
| v5t-rocketchat-0d896bf7fc | rocketchat | POST /api/v1/groups.setType | role_required | manual_review_required (중) | manual_review_required (중) | membership_required / membership_required / role_required | A=B≠정답 |
| v5t-rocketchat-23a530da4b | rocketchat | POST /api/v1/users.resetAvatar | manual_review_required | owner_or_admin (상) | owner_or_admin (중) | owner_or_admin / owner_or_admin / owner_or_admin | A=B≠정답 |
| v5t-rocketchat-7508165c03 | rocketchat | POST /api/v1/groups.rename | role_required | manual_review_required (중) | manual_review_required (중) | membership_required / membership_required / membership_required | A=B≠정답 |
| v5t-rocketchat-d83dae7c4e | rocketchat | GET /api/v1/rooms.roles | manual_review_required | membership_required (하) | manual_review_required (중) | manual_review_required / manual_review_required / manual_review_required | B=정답≠A |
| v5t-rocketchat-ec189eb0b4 | rocketchat | POST /api/v1/e2e.resetRoomKey | role_required | manual_review_required (중) | manual_review_required (중) | manual_review_required / role_required / manual_review_required | A=B≠정답 |
| v5t-rocketchat-f7c14cc85e | rocketchat | GET /api/v1/rooms.info | manual_review_required | membership_required (하) | manual_review_required (중) | manual_review_required / manual_review_required / manual_review_required | B=정답≠A |
| v5t-umami-bf7e66056f | umami | GET /api/websites/{websiteId}/shares | manual_review_required | manual_review_required (중) | owner_or_admin (중) | manual_review_required / manual_review_required / manual_review_required | A=정답≠B |
| v5t-umami-dd7523bace | umami | DELETE /api/share/id/{shareId} | manual_review_required | manual_review_required (중) | owner_or_admin (하) | owner_or_admin / owner_or_admin / owner_or_admin | A=정답≠B |

### 불일치 건 근거 메모 (시트 원문)

- **v5t-ghost-924636cc9d** GET /ghost/api/admin/posts/ — 정답 manual_review_required / A role_required / B role_required
  - A: posts browse는 rolePermissions 표의 post browse 보유 역할에만 허용(Scheduler Integration 제외)
  - B: permissions 사용, rolePermissions에서 post browse 역할별 부여
- **v5t-rocketchat-0398a2f985** GET /api/v1/rooms.membersOrderedByRole — 정답 manual_review_required / A membership_required / B manual_review_required
  - A: canAccessRoomAsync로 비공개 방은 Subscriptions 구독 확인, 공개 방은 view-c-room 권한만으로 접근
  - B: canAccessRoomAsync 공개방(view-c-room)/비공개방(구독) 경로 혼재
- **v5t-rocketchat-0780c8e386** POST /api/v1/groups.addOwner — 정답 role_required / A manual_review_required / B manual_review_required
  - A: canAccessRoomAsync 구성원 확인 AND hasPermissionAsync(fromUserId,'set-owner',rid) 역할 조건 결합
  - B: 비공개 그룹 구성원 AND 'set-owner' 권한 독립 조건 결합
- **v5t-rocketchat-09c0e4be92** POST /api/v1/groups.invite — 정답 role_required / A manual_review_required / B manual_review_required
  - A: userInRoom AND add-user-to-joined-room 또는 add-user-to-any-p-room 전역 권한 등 복합 조건
  - B: addUsersToRoomMethod: 구성원 AND add-user-to-joined-room OR add-user-to-any-p-room 혼합 조건
- **v5t-rocketchat-0d896bf7fc** POST /api/v1/groups.setType — 정답 role_required / A manual_review_required / B manual_review_required
  - A: canAccessRoomAsync 구성원 확인 AND saveRoomSettings의 'edit-room' 권한 결합
  - B: 비공개 그룹 구성원 AND saveRoomSettings 'edit-room' 권한 독립 조건 결합
- **v5t-rocketchat-23a530da4b** POST /api/v1/users.resetAvatar — 정답 manual_review_required / A owner_or_admin / B owner_or_admin
  - A: user._id === this.userId이면 본인 리셋, 아니면 edit-other-user-avatar 권한으로 우회
  - B: user._id === this.userId 본인 OR 'edit-other-user-avatar'/'manage-moderation-actions' 권한
- **v5t-rocketchat-7508165c03** POST /api/v1/groups.rename — 정답 role_required / A manual_review_required / B manual_review_required
  - A: canAccessRoomAsync 구성원 확인 AND hasPermissionAsync(userId,'edit-room',rid) 결합
  - B: 비공개 그룹 구성원(canAccessRoomAsync) AND 'edit-room' 권한 독립 조건 결합
- **v5t-rocketchat-d83dae7c4e** GET /api/v1/rooms.roles — 정답 manual_review_required / A membership_required / B manual_review_required
  - A: canAccessRoomAsync로 비공개 방은 구독 확인, 공개 방은 view-c-room 권한으로 접근
  - B: executeGetRoomRoles: 익명 읽기 설정·공개방/구독 경로 혼재로 단일 조건 불가
- **v5t-rocketchat-ec189eb0b4** POST /api/v1/e2e.resetRoomKey — 정답 role_required / A manual_review_required / B manual_review_required
  - A: hasPermissionAsync('toggle-room-e2e-encryption',rid) AND canAccessRoomIdAsync 구성원 조건 결합
  - B: hasPermissionAsync('toggle-room-e2e-encryption', rid) AND canAccessRoomIdAsync 독립 조건 결합
- **v5t-rocketchat-f7c14cc85e** GET /api/v1/rooms.info — 정답 manual_review_required / A membership_required / B manual_review_required
  - A: canAccessRoomAsync로 비공개 방은 구독 확인, 공개 방은 view-c-room 권한으로 접근
  - B: canAccessRoomAsync: 공개방은 view-c-room 권한, 비공개방은 구독 확인으로 조건이 방 유형별로 상이
- **v5t-umami-bf7e66056f** GET /api/websites/{websiteId}/shares — 정답 manual_review_required / A manual_review_required / B owner_or_admin
  - A: canViewWebsite가 admin OR 소유자 OR 팀 구성원 복합 조건
  - B: canViewWebsite: isAdmin 우회 OR user.id===entity.userId (팀 엔티티는 getTeamUser 분기)
- **v5t-umami-dd7523bace** DELETE /api/share/id/{shareId} — 정답 manual_review_required / A manual_review_required / B owner_or_admin
  - A: canDeleteEntity가 admin OR 소유자 OR (팀 구성원 AND websiteDelete 팀 역할) 복합 조건
  - B: canDeleteEntity: isAdmin 우회 OR entity.userId===user.id (팀 엔티티는 websiteDelete 권한 추가 분기)

## 7. 해석 한계

- AI 검수자(Claude) 간 일치도, 사람 일치도 아님. 두 검수자가 같은 모델(Claude)이라 독립 검수가 아니며, 같은 오류를 공유할 수 있어 A-B 일치율은 사람 간 일치율의 대체가 아니다. 사람 상한 측정은 사람 검수본 회수 후 별도 채점한다.
- 60건 표본이라 label별 support가 작다(owner_or_admin 4, public 4). label별 F1은 건수 변화 한두 건에 크게 움직인다.
- 현재 정답은 AI 1차 판정 + 사람 확인으로 확정됐고(검수 규약 G1~G8 적용), 이 시트는 v3.0.1 정의만 제공했다. 규약 차이에서 오는 불일치(예: 그룹 안 역할 role_required, 구성원 OR 관리자 우회 membership_required)는 라벨 오류가 아니라 기준 차이일 수 있다.
- v5 수치는 비교용 보조 지표이며 주지표·발표 수치(reports/eval/lora_v5/presentation_numbers_v5.md)는 바꾸지 않는다.
