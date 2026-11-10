# S1-4 보고: 검수 규약 G1~G8 vs 프롬프트 v3.0.1 대조, v3.1 초안, 정답 근거 2건, v5 confidence 곡선

작성 2026-11-03. 학습·추론 없음. 프롬프트 파일(training/data/prompts/policy_label_v3.0.1.md, SHA `d0913c27…`)과 test_v5 정답은 수정하지 않았다.

- 1절: G1~G8(+ 정지 지점 1 통일 결정) 원문을 v3.0.1 "고정 라벨"·"보류가 필수인 경우"·"판단 절차"와 대조한 목록.
- 2절: v3.1 라벨 정의 초안 → 별도 파일 [label_defs_v3.1_draft.md](label_defs_v3.1_draft.md) (프롬프트에 반영하지 않음).
- 3절: v5t-rocketchat-23a530da4b(users.resetAvatar), v5t-ghost-924636cc9d(GET posts) 정답 manual의 근거(적용 규약·검수 메모). 정답 미수정(S3 블라인드 재검수에서 판정).
- 4절: v5 3 seed confidence 문턱별 정확도–보류율 → [confidence_curve_test_v5.md](confidence_curve_test_v5.md) (+.json, 생성 scripts/confidence_curve_test_v5.py).

## 1. 검수 규약 G1~G8 vs v3.0.1 라벨 정의 대조

출처: G1~G8 원문 = review/test_v5_review_reviewed.xlsx '검수 규약' 시트(= AGENTS.md "data-v4 검수 규약" 절), 정지 지점 1 통일 결정(2026-10-31). v3.0.1 = "## 고정 라벨"(7개 정의), "## 보류가 필수인 경우"(보류 1~6), "## 판단 절차"(절차 1~6), "## 보안과 근거".

판정 기호: **충돌** = 같은 입력에 v3.0.1과 G가 다른 label을 준다. **정의에 없음** = v3.0.1이 다루지 않는 상황을 G가 정한다(모델에는 지침이 없고 정답에는 적용됨). **일치** = 같은 결론.

| # | 규약 문구(요지) | v3.0.1 대응 문구 | 판정 | 영향(test_v5 예) |
|---|---|---|---|---|
| G3-a | 그룹 구성원 확인 뒤 그룹 안 역할(계정 administrator, 그룹 moderator, 강좌 교사, 방 owner)이 결정 조건이면 role_required. 2026-10-28 사용자 확인: "그룹 한정 모더레이터 → manual" 지시보다 G3 우선. | 보류 3 "두 개 이상의 독립 필수 조건이 AND로 결합(같은 tenant AND 그룹 구성원, 소유자 AND 특정 역할) → 보류". 절차 4 "AND 보존, 두 독립 조건을 버려야 단일 라벨이면 보류". | **충돌** (구성원 AND 그룹 안 역할 → v3.0.1은 manual, G3은 role_required) | S1-3 불일치 12건 중 5건: Rocket.Chat groups.addOwner·invite·setType·rename·e2e.resetRoomKey(정답 role_required, AI 검수자 A·B 모두 manual). test_v5 role_required 111건 중 방 범위 권한(hasPermission(…, room._id)) 건이 여기에 해당. |
| G3-b | 객체 없는 기능에 RBAC 권한(permission)만 있는 경우도 role_required. | role_required "특정 역할 보유가 실제 접근 조건. 인증 성공·API 키 요구만으로 선택하지 않음". 보류 6 "인증만 확인하고 요청자-객체 관계나 역할 검사가 확인되지 않으면 manual". v3.0.1은 '역할'과 '권한(permission)'을 구분하지 않음. | **정의에 없음** (권한 검사 = 역할 검사로 볼지 미정) | Ghost GET /posts(3절): 모든 스태프 역할이 post:browse 보유 → 정답 manual(G6 인증만). 같은 구조라도 일부 역할만 보유하면 role_required. 경계가 "권한을 전 역할이 갖는가"인데 v3.0.1에는 이 기준이 없다. |
| G1-b | 라우트 RBAC 권한(checkPermission 등)이 함께 있어도 기능 권한으로 보고 tenant_match. | 보류 3 (tenant AND 역할·권한 → 보류). | **충돌** (tenant 필터 AND 기능 권한 → v3.0.1 manual, G1 tenant_match) | test_v5에는 tenant_match 0건이라 영향 없음. test_v31_supp Flowise 52건·data-v4 Label Studio 33건 정답에 적용됨. |
| G1-c | 생성 시 자원 테넌트를 요청자 테넌트로 강제하는 것도 tenant_match. | 없음(v3.0.1은 기존 객체 접근 조건만 기술, 생성 요청 미언급). | **정의에 없음** | 정지 지점 1에서 Ghost POST /posts·/pages는 "생성 요청, 기존 객체 없음"으로 EXCLUDE — 생성 요청 처리가 라벨마다 다름(G1·G4는 라벨, Ghost는 제외). |
| G2-b | 구성원 OR 관리자 우회도 membership_required. | owner_or_admin만 "소유자 OR 관리자"를 라벨로 지원. 절차 4 "OR와 AND를 그대로 보존". manual "지원하지 않는 의미". | **정의에 없음**(OR 우회를 버리고 단일 라벨 — 절차 4와 긴장) | S1-3 불일치 중 Rocket.Chat rooms.info·rooms.roles·membersOrderedByRole 3건은 반대 방향(A가 membership, 정답 manual = canAccessRoom G6). G2-b 자체가 갈린 건은 60건 표본에 없음. |
| G4-b | 본인 명의 생성(POST, 대상 = 인증 사용자)도 owner_match. | 없음(생성 요청 미언급). | **정의에 없음** | — |
| G4-c | 관리자 조건이 타인 대상 우회가 아니라 설정 우회일 뿐이면 owner_match. | 없음. owner_or_admin "소유자 허용 OR 관리자 우회"만 있음. | **정의에 없음** (관리자 조건의 종류 구분) | 3절 users.resetAvatar: 본인 분기가 설정으로 켜지고 꺼짐 → 정답은 G6(설정에 따라 허용 주체 변동)으로 manual, AI 검수자·v5는 owner_or_admin. G4-c·G5·G6 사이 경계. |
| G5 | 소유자·**당사자**(작성자, 발신자/수신자, 관계 당사자) OR 관리자 우회. | owner_or_admin "소유자 허용 OR 관리자 우회". '당사자' 확장 없음. | **정의에 없음** (owner 범위 확장) | Chamilo·Zulip 메시지 당사자 건(test_v31_supp·data-v4). |
| G6-a | 서로 다른 유형의 조건이 OR로 분기(공개/비공개 가시성, 방 종류별 canAccessRoom, 쿼리 모드별·action별 정책) → manual. | manual "지원하지 않는 의미·독립 필수 조건 결합". 보류 5 "접근 조건이 불완전·미확정". OR 분기를 명시한 문장은 없음. | **일치**(manual 정의로 포섭 가능)·명문 없음 | canAccessRoom 17건 manual(정지 지점 1). AI 검수자 A는 3건을 membership으로 봄(확신도 하). |
| G6-b | 조직·서버 설정에 따라 허용 주체가 바뀜 → manual. | 보류 5(미확정)로 포섭 가능, 명문 없음. | **정의에 없음**(명문) | users.resetAvatar(3절). |
| G6-c | 인증만 확인(객체 없음 포함) → manual. | 보류 6 "인증만 확인 … manual". | **일치** | Ghost GET /posts(3절). 단 G3-b와의 경계(전 역할 보유 권한 = 인증만?)는 G에도 명문이 없고 검수 메모로만 정해짐. |
| G7-a | 조건 없는 익명 허용만 public(AllowAny, 로그인·토큰 갱신, 무인증 개발용). | public "인증 없이 누구나 접근 가능하다는 긍정 근거". "mutation 제한: POST/PUT/PATCH/DELETE는 explicitly_anonymous일 때만 public". | **충돌** (코드가 익명 허용이어도 security_state=declared인 mutation은 v3.0.1이 public 금지) | test_v5 public 19건 중 8건이 declared 상태의 POST/PUT: Ghost POST session·POST/PUT password_reset·POST invitation, Umami POST /api/auth/login·POST /api/send·POST /api/batch. v3.0.1 문구대로면 이 8건은 public 불가(manual)인데 정답은 G7-a로 public. Rocket.Chat 6건은 explicitly_anonymous라 충돌 없음. |
| G7-b | 익명이 web-public 등 조건부로만 허용되면 manual. | public "코드 일부에 검사가 없다는 이유만으로 선택하지 않음". | **일치** | — |
| G8 | test에서 경계·의도 미확정·의도-구현 충돌·근거 누락 건은 manual로 넣지 않고 제외. | 보류 4 "코드 구현과 명시 정책 의도가 충돌하면 manual". 보류 2 "근거 없으면 manual". | **충돌**(처리 방식: v3.0.1은 모델에게 manual 출력 요구, G8은 그런 건을 test에서 제거) | 평가에는 무해(제외됐으므로). 결과적으로 test의 manual 정답은 G6 유형만 남아 "보류 4·2 유형 manual" 성능은 측정되지 않는다. S3 재검수에서 "manual vs 제외"를 다시 가르는 기준이 필요. |
| 정지1-a | Rocket.Chat 본인 구독 변경: 방 비구성원 거부면 membership_required, 본인 행만 변경이면 owner_match, 애매하면 EXCLUDE. | owner_match "처리 대상이 인증 사용자 본인으로 고정". membership "요청 대상 그룹 구성원". 둘 다 맞을 때(본인 구독 AND 방 접근)의 우선순위 없음 → 보류 3이면 manual. | **정의에 없음**(우선순위) | Rocket.Chat channels.close/open·im.close/open·teams.leave 등. |
| 정지1-b | Umami 팀 관리(canUpdateTeam/canDeleteTeam) role_required(G3), 웹사이트 수정·삭제(canUpdateWebsite/canDeleteWebsite) manual. | 팀 관리 = 팀 구성원 AND 팀 역할 → G3-a와 같은 충돌. 웹사이트 = 소유자 OR 팀 역할 OR 관리자 → G6-a. | G3-a와 동일 **충돌** / G6-a **일치** | Umami 57건. |
| v3.0.1 보류 1 | 구독·플랜·등급만 요구 → manual. | G에 대응 문구 없음(G6 "인증만"·"설정"에 포함되지 않음). | v3.0.1에만 있음 | test_v30 summit_club 6건. |
| v3.0.1 보류 2 | OAS만 있고 조건 확인 불가 → manual. | G는 코드 입력 전제. | v3.0.1에만 있음 | oas 조건 평가. |
| v3.0.1 confidence 지침 | 0.9+/0.75/0.6/0.4 근거 강도. | G 없음. | v3.0.1에만 있음 | 4절: 모델은 사실상 0.9만 출력. |

요약: **충돌 4**(G3-a 그룹 안 역할, G1-b tenant+RBAC, G7-a declared mutation public, G8 처리 방식), **정의에 없음 8**(G3-b 권한=역할, G1-c·G4-b 생성 요청, G2-b 구성원 OR 관리자, G4-c 설정 우회, G5 당사자, G6-b 설정 의존, 정지1-a 우선순위), **일치 3**(G6-a, G6-c, G7-b). S1-3에서 AI 검수자 A·B가 함께 정답과 갈린 7건 중 5건은 G3-a 충돌, 1건은 G4-c/G6-b 경계(resetAvatar), 1건은 G3-b/G6-c 경계(GET posts)로, 모두 이 표의 항목이다.

## 2. v3.1 라벨 정의 초안

[label_defs_v3.1_draft.md](label_defs_v3.1_draft.md). 1절의 충돌·누락을 v3.0.1 문장 구조 위에 반영했고, 변경 줄마다 근거 규약 번호를 달았다. 프롬프트 파일은 수정하지 않았고 예시·출력 절은 v3.0.1 그대로 둔다는 전제다. G8은 test 구성 규칙이라 라벨 정의에 넣지 않았다.

## 3. 정답 근거 확인 2건 (정답 미수정)

출처: review/test_v5_review_reviewed.xlsx(동결본 SHA `6a6e1405…`) 해당 행의 '초안 label/근거', '근거(코드 줄·문서)', '확정 label', '확정 근거' 원문. 두 건 모두 담당자 열은 검수자C, 확정 근거 접두어는 `[1차:Claude]`(AI 1차 판정, 사람 확인 범위는 사용자 전달 대기 — AGENTS.md C-5 수용·마무리 절).

### 3.1 v5t-rocketchat-23a530da4b — POST /api/v1/users.resetAvatar

- 정답: manual_review_required. 초안: owner_or_admin(0.75).
- 확정 근거(원문): `[1차:Claude] 초안 변경: 본인 분기가 설정(Accounts_AllowUserAvatarChange)으로 켜지고 꺼짐 → 설정에 따라 허용 주체가 바뀜(G6)`
- 적용 규약: **G6**("조직 설정에 따라 허용 주체가 바뀜"). 초안의 owner_or_admin(G5)을 G6으로 변경.
- 근거 코드(시트 '근거' 열): apps/meteor/server/api/v1/users.ts:987 `if (settings.get('Accounts_AllowUserAvatarChange') && user._id === this.userId) {`, :990 `(await hasPermissionAsync(this.user, 'edit-other-user-avatar')) ||`. auth_summary: "본인 OR edit-other-user-avatar/manage-moderation-actions".
- 참고(판정 아님): 초안·AI 검수자 A(상)·B(중)·v5 3 seed 모두 owner_or_admin. 갈림은 "본인 분기가 서버 설정에 묶임"을 G4-c(설정 우회 → owner 계열)로 볼지 G6-b(설정 의존 → manual)로 볼지이며 1절 표의 G4-c/G6-b 항목이다.

### 3.2 v5t-ghost-924636cc9d — GET /ghost/api/admin/posts/

- 정답: manual_review_required. 초안: manual_review_required(0.6).
- 확정 근거(원문): `[1차:Claude] 초안 근거 확인, 동의`
- 초안 근거(원문): `post:browse는 Contributor를 포함한 모든 스태프 역할과 통합 키가 보유하고, 서버에서 본인 글로 제한하는 필터가 없다. 인증된 스태프면 누구나 가능해 특정 역할 조건이 아니므로 manual_review_required(인증 전용). 대안 role_required.`
- 적용 규약: **G6**("인증만 확인") = v3.0.1 보류 6. 확정 메모에 규약 번호는 없고 초안 근거를 그대로 승인.
- 근거 코드(시트 '근거' 열): ghost/core/server/api/endpoints/posts.js:79-81 `permissions: { unsafeAttrs }`, permissions-data.ts: Administrator post 'all'(66,71) · Super Editor 'all'(160,162) · Editor 'all'(184,186) · Author ['browse','read','edit','add','destroy'](204,205) · Contributor 동일(221,222) · Admin Integration 'all'(126,129) · DB Backup Integration ['browse'](110,113) · Scheduler Integration ['publish'](115,116). auth_summary: "post:browse 권한을 Administrator·Editor·Author·Contributor·모든 통합이 보유. 서버에 본인 글 필터 없음".
- 참고(판정 아님): 초안 자체가 "대안 role_required"를 적었고 AI 검수자 A·B·v5 3 seed 모두 role_required. 갈림은 "전 역할이 보유한 권한 검사"를 G3-b(RBAC 권한 → role_required)로 볼지 G6-c(인증만)로 볼지이며, 같은 Ghost 구조에서 GET /tags(v5t-ghost-3a4c4f64d4, 모든 역할 tag:browse)도 정답 manual로 같은 기준이 적용됐다. Scheduler Integration은 post:browse가 없어 "전 주체 보유"는 아니다(초안 문구 "모든 통합"과 차이).

## 4. v5 3 seed confidence 문턱별 정확도–보류율 (test_v5 283, oas_code)

상세 표 [confidence_curve_test_v5.md](confidence_curve_test_v5.md). 결론: **곡선이 평탄하다.** HF 평가 v5 3 seed의 confidence는 test_v5 전 건 0.9 단일값(출력 오류 s42 1·s44 2 제외)이라 t ≤ 0.9에서는 문턱과 무관하게 같고 t > 0.9에서는 전부 보류된다.

| t | 평균 보류율 | 평균 전체 정확도 | 평균 macro-F1 | 유지 건 정확도(s42/s43/s44) |
|---|---:|---:|---:|---|
| 0.50 ~ 0.90 (동일) | 0.170 | 0.693 | 0.683 | 0.712 / 0.700 / 0.729 |
| 0.95, 0.99 | 1.000 | 0.230 | 0.062 | - |

- 같은 현상이 test_v30·test_v31_supp HF 예측에도 있다(0.9가 98% 이상, s44 test_v30만 0.85 2건). GGUF Q4_K_M(Ollama) 경로는 val_v5에서 0.7~1.0 분포를 냈으므로(reports/eval/lora_v5_gguf/threshold_val_v5.json) test_v5 실곡선은 GGUF 추론이 있어야 그릴 수 있고 이번 작업 범위(추론 없음) 밖이다.
- 따라서 HF 평가 모델에서 confidence 문턱은 보류율 조절 수단이 못 된다. 주지표·발표 수치는 바꾸지 않는다.
