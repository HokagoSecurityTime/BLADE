# 정책 라벨 정의 v3.1 — 초안 (S1-4, 2026-11-03; 사용자 지시 반영 2차 수정 2026-11-03)

상태: **초안. 프롬프트 파일에 반영하지 않았다.** 2차 수정 3건: (1) G4-c vs G6-b 구분 문장(설정이 본인 분기 자체를 켜고 끄면 보류 5, 본인 대상의 설정 제한만 우회하면 owner_match), (2) G3-b/G6-c 경계를 "모든 사용자 역할(스태프 역할)이 보유한 권한"으로 수정하고 통합·API 키 주체 제외·모델 재정의 반영을 명시(정합성 확인 절), (3) 변경 요약표에 반영 시 안전 가드 추가. 계획: S4는 v3.0.1 유지, S5에서 v3.1 반영(AGENTS.md "S1-4 후속 계획" 절). training/data/prompts/policy_label_v3.0.1.md(SHA `d0913c27…`)는 그대로이며, 이 문서는 "## 고정 라벨"·"## 보류가 필수인 경우"·"## 판단 절차"·"## 보안과 근거" 네 절의 교체 후보다. 예시·출력 절은 v3.0.1 그대로 둔다는 전제(예시 6종은 v3.1 정의와 충돌하지 않음). 반영 여부·시점은 사용자 결정 사항이며, 반영 시 test_v5·test_v30 정답은 바꾸지 않는다(정답은 이미 G1~G8 기준).

표기: 각 줄 끝 `[Gn]`은 근거 검수 규약, `[v3.0.1]`은 기존 문장 유지, `[변경]`은 v3.0.1 문장을 고친 곳, `[신설]`은 v3.0.1에 없던 문장.

## 고정 라벨

- public: 해당 요청은 인증 없이 누구나 접근 가능하다는 긍정 근거가 있다(익명 허용 코드, AllowAny, 로그인·토큰 갱신·회원가입·비밀번호 재설정 같은 인증 획득용 엔드포인트, 무인증 개발용 엔드포인트). [v3.0.1 + G7-a 신설] 코드 일부에 검사가 없거나 security가 unknown이라는 이유만으로 선택하지 않는다. 인증이 필요하면 public이 아니다. [v3.0.1] 익명이 web-public·공개 설정 등 조건부로만 허용되면 public이 아니라 manual_review_required다. [G7-b 신설] security 선언은 public을 막는 근거가 아니다: 코드가 인증 없이 처리함을 보이면 security 선언·mutation 여부와 무관하게 public이다. 코드 없이 OAS만 있을 때는 security 선언·mutation 제한을 그대로 적용한다. [변경 — v3.0.1 "security가 선언됐거나 … public 금지"와 "mutation 제한"을 OAS-only 조건으로 한정; G7-a]
- role_required: 특정 역할 보유가 실제 접근 조건이다. 인증 성공이나 API 키 요구만으로 선택하지 않는다. [v3.0.1] 역할은 전역 역할(admin, staff)뿐 아니라 그룹 안 역할(계정 administrator, 방 owner·moderator, 강좌 교사)을 포함한다. 그룹 안 역할 검사에 앞서 그룹 구성원 확인이 있어도 이는 AND 결합이 아니라 역할 검사의 전제이므로 role_required다. [G3-a 신설] 객체가 없는 기능에 RBAC 권한(permission) 검사만 있는 경우도 role_required다. 단, 그 권한을 모든 사용자 역할(스태프 역할)이 보유하면 역할 조건이 아니므로 manual_review_required다. 이 판단에서 통합·API 키·봇 같은 비사용자 주체는 제외한다. 역할 권한표만이 아니라 모델 수준 재정의(permissible 등)까지 합쳐 일부 역할이 실제로 거부되면 "모든 역할 보유"가 아니다. [G3-b + G6-c 경계 신설, 2026-11-03 수정]
- membership_required: 요청자가 해당 요청 대상 그룹·팀·방·계정·워크스페이스의 구성원이어야 한다. (requester_id, target_group_id) 관계나 동등한 구성원 조회가 근거다. 유료 플랜, 구독 등급, 같은 tenant, 팀 이름만으로는 선택하지 않는다. [v3.0.1] 대상 그룹은 요청(경로·본문·쿼리)이 지정해야 한다. [G2 신설] 구성원 OR 전역 관리자 우회가 있어도 membership_required다(owner_or_admin의 구성원 판 라벨은 없다). [G2-b 신설] 구성원 확인 뒤 그룹 안 역할이 결정 조건이면 role_required다. [G3-a 신설]
- tenant_match: 요청자 tenant와 대상 자원의 tenant가 같아야 한다. 특정 그룹 구성원 여부와 구분한다. 같은 tenant라도 그룹 비구성원일 수 있고, 그룹 구성원은 다른 tenant에 있을 수도 있다. [v3.0.1] 서버가 자원의 조직·워크스페이스·테넌트를 요청자의 현재 테넌트(세션·토큰의 active organization, API 키 tenant)와 비교하거나 그것으로 필터하며 경로·본문에 대상 테넌트 ID가 없는 경우다. [G1 신설] 라우트 RBAC 권한(checkPermission 등)이 함께 있어도 기능 권한으로 보고 tenant_match다. [G1-b 신설] 생성 요청에서 자원 테넌트를 요청자 테넌트로 강제하는 것도 포함한다. [G1-c 신설]
- owner_match: 요청자가 대상 객체 소유자 본인이어야 하거나, 처리 대상이 인증 사용자 본인으로 고정돼야 한다(/me, request.user, 본인 목록·설정·플래그·기기, 본인 명의 생성). [v3.0.1 + G4 신설] 반환 데이터에 owner 필드가 있다는 사실만으로 선택하지 않는다. [v3.0.1] 관리자 조건이 타인 대상 우회가 아니라 본인 대상의 설정 제한만 우회하면 owner_match다. 설정이 본인 분기 자체를 켜고 끄면(꺼지면 관리자만 가능) owner_match가 아니라 보류 5(manual_review_required)다. [G4-c·G6-b 구분 신설, 2026-11-03 수정] 본인 구독·본인 행만 변경하고 방 접근 판단이 없으면 owner_match, 방 비구성원을 거부하면 membership_required다. [정지 지점 1 신설]
- owner_or_admin: 소유자·당사자(작성자, 발신자/수신자, 관계 당사자) 허용 OR 관리자 우회가 실제 조건이다. 관리자도 소유자여야 하는 AND 조건은 이 패턴이 아니다. [v3.0.1 + G5 변경] 관리자 우회가 없으면 owner_match다. [G5 신설]
- manual_review_required: 근거 부족·모순·지원하지 않는 의미·독립 필수 조건 결합으로 6종 중 하나를 타당하게 선택할 수 없다. 자동 적용 제외·관리자 검토 대기다. [v3.0.1]

## 보류가 필수인 경우

다음에 해당하면 구체 라벨을 추측하지 않고 manual_review_required를 선택한다.

1. 구독·플랜·등급(premium, pro, paid tier 등)만 요구하는 조건. 이는 그룹 구성원 관계가 아니므로 6종으로 표현하지 못한다. [v3.0.1]
2. OAS(명세)만 있고 요청자와 대상 객체의 관계나 실제 접근 조건을 확인할 수 없는 경우. path에 객체 ID가 있다는 사실, 응답에 owner·tenant 필드가 있다는 사실, 자원 이름(my, me, admin 등)만으로 관계를 단정하지 않는다. 설명에 접근 조건이 명시돼 있으면 그 문장을 근거로 선택할 수 있다. [v3.0.1]
3. 서로 다른 유형의 두 독립 필수 조건이 AND로 결합된 경우(예: 같은 tenant AND 특정 그룹 구성원, 소유자 AND 특정 역할). 하나를 버려야 단일 라벨이 되면 보류한다. 다음은 AND 결합으로 보지 않는다: 그룹 구성원 확인 뒤 그룹 안 역할(→ role_required), tenant 필터와 기능 RBAC 권한(→ tenant_match), 인증과 하나의 객체 접근 조건. [변경 — G3-a·G1-b 예외 추가]
4. 서로 다른 유형의 조건이 OR로 분기하는 경우(공개/비공개 가시성에 따라 조건이 달라짐, 방 종류별로 다른 접근 함수, 쿼리 모드별·action별로 다른 정책). 소유자 OR 관리자(owner_or_admin), 구성원 OR 관리자(membership_required)는 예외다. [G6-a 신설]
5. 서버·조직 설정에 따라 허용 주체가 바뀌는 경우. 설정이 본인 분기 자체를 켜고 끄면(꺼지면 관리자만 가능) 여기에 해당해 manual이다. 관리자 조건이 본인 대상의 설정 제한만 우회하면 owner_match다(G4-c). [G6-b 신설, 2026-11-03 수정]
6. 코드 구현과 명시 정책 의도가 충돌하는 경우. [v3.0.1]
7. 코드가 모든 요청을 거부하거나, 접근 조건이 불완전·미확정으로 남아 있는 경우. [v3.0.1]
8. 인증만 확인하고 요청자-객체 관계나 역할 검사가 확인되지 않는 경우(객체 없는 기능 포함, 모든 사용자 역할이 보유한 권한 검사 포함; 통합·API 키 주체는 제외). [v3.0.1 + G6-c 변경, 2026-11-03 수정]

## 판단 절차

1. 해당 method와 대상 자원을 확인한다. 다른 엔드포인트의 정책을 가져오지 않는다. [v3.0.1]
2. 실제 허용·거부를 결정하는 조건을 찾는다. 입력 필드의 존재나 반환값은 검사 자체가 아니다. [v3.0.1]
3. 인증과 인가를 분리한다. 인증 + 하나의 객체 접근 조건은 인증 때문에 복합 인가로 취급하지 않는다. [v3.0.1]
4. OR와 AND를 그대로 보존한다. 두 독립 조건을 버려야 단일 라벨을 만들 수 있으면 보류한다. 예외는 보류 3·4에 적은 결합뿐이다. [변경]
5. 생성 요청(기존 객체 없음)은 대상이 본인 명의면 owner_match, 요청자 테넌트로 강제되면 tenant_match, 대상 그룹을 지정하고 구성원을 확인하면 membership_required, 역할·권한만 확인하면 role_required다. 그 외는 보류한다. [G1-c·G4-b 신설]
6. 코드의 구현과 명시적 정책의 의도를 구분한다. 서로 충돌하면 rationale에 적고 보류한다. 코드가 미확보되면 검사 누락이라고 단정하지 않는다. [v3.0.1]
7. 조건의 의미가 충분하면 고정 라벨을 선택하고, 부족하면 보류한다. confidence가 낮다는 이유만으로 사후 변환하지 않는다. [v3.0.1]

## 보안과 근거

security_state=declared는 인증 선언이지 특정 인가 라벨이 아니다. unknown은 공개 근거가 아니다. explicitly_anonymous는 현재 수집 규약의 명시 익명 상태다. public은 익명 허용 코드·명시 설명 등의 긍정 근거가 필요하다. [v3.0.1] mutation 제한은 코드가 없을 때 유지한다: 코드 없이 OAS만 있는 PUT/POST/PATCH/DELETE는 explicitly_anonymous일 때만 public을 허용한다. 코드가 인증 없이 처리함을 보이면 method·security 선언과 무관하게 public이다. [변경 — G7-a]

(이하 "schema_fields와 owner_cols/tenant_cols…", "코드가 description에 포함된 경우…" 두 문단은 v3.0.1 그대로.)

## 반영하지 않은 규약

- G8(test 제외 규칙)은 test 구성 절차이므로 라벨 정의에 넣지 않는다. 모델에는 보류 6(의도·구현 충돌)·7(미확정)로 manual을 요구하고, test에서는 그런 건을 제외하므로 두 문서는 역할이 다르다.
- 정지 지점 1의 Ghost POST /posts·/pages EXCLUDE(생성 요청)는 절차 5(생성 요청 라벨링)와 긴장이 있다. 절차 5를 채택하면 S3 재검수에서 해당 2건의 제외 사유를 다시 볼 필요가 있다(정답 변경은 별도 승인).

## v3.0.1 대비 변경 요약

| 항목 | v3.0.1 | v3.1 초안 | 근거 |
|---|---|---|---|
| 그룹 안 역할 | 구성원 AND 역할 → 보류 3 | role_required | G3-a |
| 객체 없는 RBAC 권한 | 미정(보류 6 가능) | role_required. 모든 사용자 역할(스태프 역할)이 보유한 권한은 manual(통합·API 키 주체 제외, permissible 등 모델 재정의 반영) | G3-b, G6-c |
| tenant 필터 + 기능 권한 | 보류 3 | tenant_match | G1-b |
| 구성원 OR 관리자 | 미정 | membership_required | G2-b |
| 당사자 OR 관리자 | 소유자만 | owner_or_admin | G5 |
| 설정 우회인 관리자 조건 | 미정 | owner_match | G4-c |
| 설정 의존 허용 주체 | 보류 5(간접) | 보류 5 명문 | G6-b |
| 다른 유형 OR 분기 | manual 정의(간접) | 보류 4 명문 | G6-a |
| 생성 요청 | 미언급 | 절차 5 | G1-c, G4-b |
| declared mutation public | 금지 | 코드 근거 있으면 허용, OAS-only는 금지 유지 | G7-a |
| 조건부 익명 | public 정의(간접) | manual 명문 | G7-b |
| 설정 의존 본인 분기 | 미정 | 설정이 본인 분기 자체를 켜고 끄면 보류 5(manual), 본인 대상의 설정 제한만 우회하는 관리자 조건은 owner_match | G4-c·G6-b 구분(2026-11-03) |
| **반영 시 안전 가드** | - | v3.1 반영 모델의 public 오판(test_v30 oas_code 합성 제외 207건, 분모 35)이 v5 3 seed 평균 2.0건을 넘으면 v3.1을 채택하지 않는다 | 사용자 지시 2026-11-03 |

## 정합성 확인: G3-b/G6-c 경계 vs test_v5 Ghost 정답 (2026-11-03)

test_v5 Ghost 69건의 controller_text에 든 rolePermissions 표(스태프 역할 Administrator·Super Editor·Editor·Author·Contributor)와 검수 시트 auth_summary로 "모든 사용자 역할이 보유한 권한 → manual, 아니면 role_required" 규칙을 대조했다. 통합(Admin/DB Backup/Scheduler Integration)·API 키는 제외.

| 정답 | 엔드포인트 | 권한 | 스태프 5역할 보유 | 모델 재정의 | 규칙 결과 | 일치 |
|---|---|---|---|---|---|---|
| manual | GET /posts/ | post:browse | 전부 | 없음(authors.permissible은 edit/add/destroy만) | manual | ○ |
| manual | GET /tags/ | tag:browse | 전부 | 없음 | manual | ○ |
| manual | GET /posts/{id}/ | post:read | 전부 | 없음 | manual | ○ |
| manual | GET /users/, GET /roles/, GET /slugs/… | browse | 전부 | 없음 | manual | ○ |
| role_required | POST /posts/{id}/copy/, POST /pages/{id}/copy/ | post:add | 전부(권한표상) | authors.permissible: unsafeAttrs 부재로 Author·Contributor isOwner() false → 거부 | role_required(재정의로 일부 역할 거부) | ○ |
| role_required | DELETE /posts/ (bulk) | post:destroy | 전부(권한표상) | authors.permissible: 대상 모델 없어 Author·Contributor 거부 | role_required | ○ |
| role_required | DELETE /users/{id}/ | user:destroy | Author·Contributor 미보유 | User.permissible 추가 제한 | role_required | ○ |
| role_required | PUT /settings/, PUT /tags/{id}/, POST /tags/ 등 | edit/add | 일부 역할만 | - | role_required | ○ |

결론: "모든 사용자 역할 보유" 판단에 모델 수준 재정의(permissible)를 포함해야 GET posts·GET tags(manual)와 copy·bulkDestroy(role_required)가 모두 정답과 일치한다. 권한표만 보면 copy·bulkDestroy 3건이 manual로 뒤집히므로 role_required 정의에 그 문장을 넣었다. 통합 주체를 제외한 것은 GET posts(Scheduler Integration은 browse 미보유)에서 "모든 주체"로 하면 manual이 아니게 되는 문제를 피한다.
