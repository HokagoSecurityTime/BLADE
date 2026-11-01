# LoRA v2 과보류(over-abstention) 원인 분석 — final 어댑터 seed 42·43·44, test_v30, 기존 예측 파일만 사용

data-v1·data-v2 해시 assert 통과(시작·종료). 학습·API 호출 없음. test_v30 불변. '과보류' = 예측 manual_review_required ∧ 정답이 구체 label. 코드 인가 검사 판정은 controller_text 정규식(403/Forbidden·owner/user id 비교·role/admin 검사; 인증만 있는 패턴은 '인증만'으로 분리)이며 Gitea 미들웨어 이름(reqAdmin·reqOrgOwnership 등)은 role/admin으로, reqToken은 인증만으로 센다. Gitea 발췌의 설명 주석(sudo 403 문구 등)은 제거 후 판정. 정규식은 scripts/abstain_analysis_v2.py PAT. '보류율' = 교집합 보류 건수 / 그 범주의 정답 구체 모집단(해당 조건 채점 대상).

## oas: 과보류 건수

| 집합 | 건수 | 정답 구체 대비 | 주지표 구간 내 |
|---|---:|---:|---:|
| seed 42 | 176 | 69.3% | 69 |
| seed 43 | 180 | 70.9% | 74 |
| seed 44 | 183 | 72.0% | 75 |
| 교집합(3 seed 모두) | 171 | 67.3% | 65 |
| 합집합(1개 이상) | 187 | 73.6% | 79 |

정답 구체 label 건수 254(채점 대상 269). 주지표 구간: oas는 route_only 제외 160건, oas_code는 265건 전체. 교집합/합집합 = 91%.

### oas: 교집합 171건 교차표 (보류율 = 범주별 교집합/모집단)

**구간별**

| 구간 | 교집합 보류 | 모집단(정답 구체) | 보류율 |
|---|---:|---:|---:|
| route_only | 106 | 108 | 98% |
| repository_spec | 65 | 102 | 64% |
| synthetic | 0 | 44 | 0% |

**서비스별**

| service | 교집합 보류 | 모집단(정답 구체) | 보류율 |
|---|---:|---:|---:|
| juice-shop | 68 | 68 | 100% |
| crAPI | 37 | 53 | 70% |
| Pixi | 37 | 52 | 71% |
| DVWS-node | 25 | 25 | 100% |
| summit_club | 0 | 14 | 0% |
| VAmPI | 4 | 12 | 33% |
| quill_blog | 0 | 10 | 0% |
| folio_wiki | 0 | 10 | 0% |
| beacon_iot | 0 | 10 | 0% |

**정답 label별**

| 정답 label | 교집합 보류 | 모집단(정답 구체) | 보류율 |
|---|---:|---:|---:|
| public | 41 | 66 | 62% |
| role_required | 37 | 51 | 73% |
| membership_required | 0 | 4 | 0% |
| tenant_match | 0 | 8 | 0% |
| owner_match | 90 | 114 | 79% |
| owner_or_admin | 3 | 11 | 27% |

**코드 인가 검사 유무별** (oas 조건에서는 모델이 코드를 보지 않음; 레코드 성격 참고용)

| 코드 상태 | 교집합 보류 | 모집단(정답 구체) | 보류율 |
|---|---:|---:|---:|
| 인가 검사 있음 | 40 | 67 | 60% |
| 인증만 | 28 | 30 | 93% |
| 인가·인증 없음 | 102 | 153 | 67% |
| 코드 없음 | 1 | 4 | 25% |

**구간 × 코드 인가 검사** (교집합 건수 / 모집단)

| 구간 | 인가 검사 있음 | 인증만 | 인가·인증 없음 | 코드 없음 |
|---|---:|---:|---:|---:|
| route_only | 27 / 27 | 23 / 23 | 56 / 58 | 0 / 0 |
| repository_spec | 13 / 22 | 5 / 7 | 46 / 69 | 1 / 4 |
| synthetic | 0 / 18 | 0 / 0 | 0 / 26 | 0 / 0 |

**정답 label × 코드 인가 검사** (교집합 건수 / 모집단; 패턴 열은 교집합 내 건수)

| 정답 label | 인가 검사 있음 | 인증만 | 인가·인증 없음 | owner/user id 비교 | role/admin | 403/Forbidden |
|---|---:|---:|---:|---:|---:|---:|
| public | 7 / 10 | 5 / 5 | 29 / 51 | 3 | 3 | 1 |
| role_required | 13 / 19 | 0 / 0 | 23 / 28 | 3 | 13 | 3 |
| membership_required | 0 / 2 | 0 / 0 | 0 / 2 | 0 | 0 | 0 |
| tenant_match | 0 / 4 | 0 / 0 | 0 / 4 | 0 | 0 | 0 |
| owner_match | 20 / 28 | 23 / 25 | 47 / 61 | 6 | 7 | 7 |
| owner_or_admin | 0 / 4 | 0 / 0 | 3 / 7 | 0 | 0 | 0 |

**추출 시그널(controller_signals.has_auth_check) 대조(교집합)**: has_auth_check=False ∧ 정규식 인가=False: 129, has_auth_check=False ∧ 정규식 인가=True: 34, has_auth_check=True ∧ 정규식 인가=True: 6, has_auth_check=True ∧ 정규식 인가=False: 2

**모델 rationale 유형(교집합, seed 42 기준)**

| 유형 | 건수 |
|---|---:|
| relation_unspecified | 122 |
| other | 42 |
| condition_unclear | 6 |
| auth_only_noted | 1 |

### oas: 유형별 대표 5건 (구간 × 인가 검사 유무; id 정렬 상위 5)

**route_only · 인가 검사 있음 (27건)**

- `0cd1ae74896420dd9abe` juice-shop POST /api/Users — 정답 **public** · 패턴 ['role_admin']
  - 코드: `export const registerAdminChallenge = () => (req: Request, res: Response, next: NextFunction) => { challengeUtils.solveIf(challenges.registerAdminChallenge, () => { return req.body && req.body.role === security.roles.admin }) next() } export const passwordRepe…`
  - 모델 rationale(seed 42): path: /api/Users; 판단: 요청자와 대상 객체의 관계나 접근 조건이 명시되지 않아 관계를 확정할 수 없음
- `0e1637db083f68e499d4` Pixi GET /api/admin/total_money — 정답 **role_required** · 패턴 ['role_admin']
  - 코드: `app.get('/api/admin/total_money', api_token_check, function(req, res){ mongo.connect('mongodb://pixidb:27017/Pixidb', function(err, db){ db.collection('loves').find().toArray(function(err, loves){ if (err) { return err } if(loves) { var total = loves.length * …`
  - 모델 rationale(seed 42): path: /api/admin/total_money; 판단: 요청자와 대상 객체의 관계나 접근 조건이 명시되지 않아 관계를 확정할 수 없음
- `1e7e10e8d4827df5e28a` Pixi POST /admin/money — 정답 **role_required** · 패턴 ['owner_cmp', 'role_admin']
  - 코드: `app.post('/admin/money', function(req, res){ console.log(req.body.userid) mongo.connect(dbname, function(err, db){ //db.collection('users').find({ $text : { $search: req.query.search} }) .toArray(function(err, search){ //db.collection('users').find( {email : r…`
  - 모델 rationale(seed 42): path: /admin/money; 판단: 요청자와 대상 객체의 관계나 접근 조건이 명시되지 않아 관계를 확정할 수 없음
- `2168150bddc48ce3a0c8` Pixi GET /admin — 정답 **role_required** · 패턴 ['role_admin']
  - 코드: `app.get('/admin/', function(req, res){ res.sendFile('./admin.html', {root: __dirname}); });`
  - 모델 rationale(seed 42): path: /admin; 판단: 요청자와 대상 객체의 관계나 접근 조건이 명시되지 않아 관계를 확정할 수 없음
- `28fa5fab6338ef186954` Pixi GET /user_likes — 정답 **owner_match** · 패턴 ['owner_cmp']
  - 코드: `app.get('/user_likes', login_check, function(req, res){ mongo.connect(dbname, function(err, db){ db.collection('likes').find({ user_id : req.session.user._id}).toArray(function(err, likes){ if(err) { return err }; if(likes) { //console.log(likes); res.json(lik…`
  - 모델 rationale(seed 42): path: /user_likes; 판단: 요청자와 대상 객체의 관계나 접근 조건이 명시되지 않아 관계를 확정할 수 없음

**route_only · 인가 검사 없음 (79건)**

- `0293603d276a2bdbefe0` Pixi GET /user_delete_photo — 정답 **owner_match** · 패턴 없음
  - 코드: `app.get('/user_delete_photo/', function(req, res) { console.log('in delete' + req.query.picture_id); if(!req.query.picture_id) { res.json('NO PICTURE SPECIFIED TO DELETE'); } else { mongo.connect('mongodb://pixidb:27017/Pixidb', function(err, db){ db.collectio…`
  - 모델 rationale(seed 42): path: /user_delete_photo; 판단: 요청자와 객체 간의 관계나 접근 조건이 명시되지 않아 관계를 확정할 수 없음
- `063fa7598db37c095700` juice-shop POST /api/Quantitys — 정답 **role_required** · 패턴 없음
  - 코드: `export const denyAll = () => expressJwt({ secret: '' + Math.random() } as any)`
  - 모델 rationale(seed 42): path: /api/Quantitys; 판단: 요청자와 대상 객체의 관계나 접근 조건을 확인할 수 있는 정보가 부족하여 보류
- `0a3ece0464909469b61e` juice-shop GET /rest/track-order/{id} — 정답 **owner_match** · 패턴 없음
  - 코드: `export function trackOrder () { return (req: Request, res: Response) => { // Truncate id to avoid unintentional RCE const id = !utils.isChallengeEnabled(challenges.reflectedXssChallenge) ? String(req.params.id).replace(/[^\w-]+/g, '') : utils.trunc(req.params.…`
  - 모델 rationale(seed 42): path_params:id; 판단: 요청자와 대상 객체의 관계를 확인할 수 있는 정보가 부족하여 접근 조건을 확정할 수 없음
- `0aa2fbdb066b3d771316` crAPI POST /identity/management/user/apikey — 정답 **role_required** · 패턴 없음
  - 코드: `@PostMapping("/user/apikey") public ResponseEntity<ApiKeyResponse> generateApiKey( @RequestBody LoginForm loginForm, HttpServletRequest request) throws UnsupportedEncodingException { ApiKeyResponse response = userService.generateApiKey(request, loginForm); ret…`
  - 모델 rationale(seed 42): path: /identity/management/user/apikey; 판단: 요청자와 객체의 관계나 접근 조건이 명시되지 않아 관계를 확정할 수 없음
- `0f5b4d569c99d8d9c870` Pixi GET /love_photo/{picture_id} — 정답 **public** · 패턴 없음
  - 코드: `app.get('/love_photo/:picture_id', login_check, function(req, res){ console.log('in love ' + JSON.stringify(req.params.picture_id)); if(!req.params.picture_id) { res.json('NO PICTURE SPECIFIED TO LOVE PUT ON GET') } else { //db call- if like exists, delete it,…`
  - 모델 rationale(seed 42): path_params:picture_id; 판단: 요청자와 대상 객체의 관계를 확인할 수 있는 정보가 부족하여 접근 조건을 확정할 수 없음

**repository_spec · 인가 검사 있음 (13건)**

- `1d45c0e2ac7bb00728b3` DVWS-node POST /api/v2/users/profile/import/xml — 정답 **owner_match** · 패턴 ['role_admin']
  - 코드: `importProfileXml: async (req, res) => { // Scenario: User imports profile from XML. // Vulnerability: The endpoint blindly accepts fields from the XML. // Mass Assignment: If XML contains <admin>true</admin>, user becomes admin. const xmlData = req.body.xml; i…`
  - 모델 rationale(seed 42): path: /api/v2/users/profile/import/xml; 판단: 요청자와 대상 객체의 관계나 접근 조건이 명시되지 않아 관계를 확정할 수 없음
- `208819689993254cc920` DVWS-node POST /api/v2/login — 정답 **public** · 패턴 ['role_admin']
  - 코드: `login: async (req, res) => { const { username, password } = req.body; //set_cors(req,res); res.set('Cache-Control', 'no-store, no-cache, must-revalidate, private') let result = {}; let status = 200; // Vulnerability: Log Pollution via CRLF Injection // We log …`
  - 모델 rationale(seed 42): security_state: unknown; 판단: 인증 요구는 있지만 접근 조건이 명시되지 않아 보류
- `4d8caf213fb70649fc0f` DVWS-node GET /api/v2/users/profile/export/xml — 정답 **owner_match** · 패턴 ['role_admin']
  - 코드: `exportProfileXml: async (req, res) => { // Scenario: User exports their profile to XML. // Vulnerability: The 'bio' and 'username' fields are user-controlled and concatenated directly. const username = req.body.username || "guest"; const bio = req.body.bio || …`
  - 모델 rationale(seed 42): path: /api/v2/users/profile/export/xml; 판단: 요청자와 대상 객체의 관계나 접근 조건이 명시되지 않아 관계를 확정할 수 없음
- `7093260288fd7266a210` DVWS-node GET /api/v2/users/checkadmin — 정답 **owner_match** · 패턴 ['role_admin']
  - 코드: `checkadmin: (req, res) => { res.set('Cache-Control', 'no-store, no-cache, must-revalidate, private') const token = req.headers.authorization.split(' ')[1]; // Bearer <token> const options = { expiresIn: '2d', issuer: 'https://github.com/snoopysecurity', permis…`
  - 모델 rationale(seed 42): path: /api/v2/users/checkadmin; 판단: 요청자와 객체의 관계나 접근 조건이 명시되지 않아 관계를 확정할 수 없음
- `7292860512c06eed2ffd` Pixi PUT /api/user/edit_info — 정답 **owner_match** · 패턴 ['role_admin']
  - 코드: `app.put('/api/user/edit_info', api_token_check, function(req, res){ console.log('in user put ' + req.user.user._id); var objForUpdate = {}; ///console.log('BODY ' + JSON.stringify(req.body)); if (req.body.email) { objForUpdate.email = req.body.email; } if (req…`
  - 모델 rationale(seed 42): description: 사용자가 유효한 토큰을 제공하면 모든 사용자 정보를 받는다; 판단: 인증이 필요하지만 요청자와 객체 간의 관계가 명시되지 않아 접근 조건을 확정할 수 없음

**repository_spec · 인가 검사 없음 (52건)**

- `06ba24e97fdcb059ad92` DVWS-node GET /api/v2/notes — 정답 **owner_match** · 패턴 없음
  - 코드: `list_all_notes: async (req, res) => { res = set_cors(req, res) res.set('Cache-Control', 'no-store, no-cache, must-revalidate, private') let result = {} const token = req.headers.authorization.split(' ')[1]; result = jwt.verify(token, process.env.JWT_SECRET, op…`
  - 모델 rationale(seed 42): path: /api/v2/notes; 판단: 요청자와 대상 객체의 관계나 접근 조건을 확인할 수 있는 정보가 부족하여 보류
- `0797f5bb072770d50159` crAPI POST /community/api/v2/coupon/new-coupon — 정답 **role_required** · 패턴 없음
  - 코드: `func (s *Server) AddNewCoupon(w http.ResponseWriter, r *http.Request) { body, err := io.ReadAll(r.Body) defer func() { if err := r.Body.Close(); err != nil { log.Println("Error closing request body:", err) } }() if err != nil { responses.ERROR(w, http.StatusBa…`
  - 모델 rationale(seed 42): description: 새로운 쿠폰을 추가하는 요청; 판단: 인증이 필요하지만 요청자와 객체 간의 관계가 명시되지 않아 접근 조건을 확정할 수 없음
- `0a8fb9b5c84b26b19826` DVWS-node POST /api/download — 정답 **owner_match** · 패턴 없음
  - 코드: `fetch: (req, res) => { const token = req.headers.authorization.split(' ')[1]; // Bearer <token> result = jwt.verify(token, process.env.JWT_SECRET, options); var filename = path.resolve(process.cwd() + '/public/uploads/' + result.user + "/" + req.body.filename)…`
  - 모델 rationale(seed 42): path: /api/download; 판단: 요청자와 대상 객체의 관계나 접근 조건이 명시되지 않아 관계를 확정할 수 없음
- `0b0918598294090d14c3` crAPI PUT /identity/api/v2/user/videos/{video_id} — 정답 **owner_match** · 패턴 없음
  - 코드: `@PutMapping("/api/v2/user/videos/{video_id}") public ResponseEntity<?> updateProfileVideo( @PathVariable("video_id") Long videoId, @RequestBody VideoForm videoForm, HttpServletRequest request) { ProfileVideo profileVideo = profileService.updateProfileVideo(vid…`
  - 모델 rationale(seed 42): description: 사용자의 프로필 비디오를 업데이트하는 요청; 판단: 인증이 필요하지만 요청자와 객체 간의 관계가 명시되지 않아 접근 조건을 확정할 수 없음
- `0f7af84126bd72a56bd5` DVWS-node POST /api/upload — 정답 **owner_match** · 패턴 없음
  - 코드: `post: (req, res) => { let sampleFile; let uploadPath; let result = {} const token = req.headers.authorization.split(' ')[1]; result = jwt.verify(token, process.env.JWT_SECRET, options); if (req.body.metadata) { try { const metadata = JSON.parse(req.body.metada…`
  - 모델 rationale(seed 42): path: /api/upload; 판단: 요청자와 대상 객체의 관계나 접근 조건을 확인할 수 있는 정보가 부족하여 보류

seed별로만 보류된 건(합집합−교집합 16건): seed 42 5, seed 43 9, seed 44 12.

## oas_code: 과보류 건수

| 집합 | 건수 | 정답 구체 대비 | 주지표 구간 내 |
|---|---:|---:|---:|
| seed 42 | 75 | 30.0% | 75 |
| seed 43 | 100 | 40.0% | 100 |
| seed 44 | 105 | 42.0% | 105 |
| 교집합(3 seed 모두) | 66 | 26.4% | 66 |
| 합집합(1개 이상) | 118 | 47.2% | 118 |

정답 구체 label 건수 250(채점 대상 265). 주지표 구간: oas는 route_only 제외 160건, oas_code는 265건 전체. 교집합/합집합 = 56%.

### oas_code: 교집합 66건 교차표 (보류율 = 범주별 교집합/모집단)

**구간별**

| 구간 | 교집합 보류 | 모집단(정답 구체) | 보류율 |
|---|---:|---:|---:|
| route_only | 47 | 108 | 44% |
| repository_spec | 19 | 98 | 19% |
| synthetic | 0 | 44 | 0% |

**서비스별**

| service | 교집합 보류 | 모집단(정답 구체) | 보류율 |
|---|---:|---:|---:|
| juice-shop | 32 | 68 | 47% |
| crAPI | 16 | 53 | 30% |
| Pixi | 8 | 48 | 17% |
| DVWS-node | 10 | 25 | 40% |
| summit_club | 0 | 14 | 0% |
| VAmPI | 0 | 12 | 0% |
| quill_blog | 0 | 10 | 0% |
| folio_wiki | 0 | 10 | 0% |
| beacon_iot | 0 | 10 | 0% |

**정답 label별**

| 정답 label | 교집합 보류 | 모집단(정답 구체) | 보류율 |
|---|---:|---:|---:|
| public | 14 | 66 | 21% |
| role_required | 20 | 47 | 43% |
| membership_required | 0 | 4 | 0% |
| tenant_match | 0 | 8 | 0% |
| owner_match | 29 | 114 | 25% |
| owner_or_admin | 3 | 11 | 27% |

**코드 인가 검사 유무별** (oas 조건에서는 모델이 코드를 보지 않음; 레코드 성격 참고용)

| 코드 상태 | 교집합 보류 | 모집단(정답 구체) | 보류율 |
|---|---:|---:|---:|
| 인가 검사 있음 | 17 | 67 | 25% |
| 인증만 | 6 | 30 | 20% |
| 인가·인증 없음 | 43 | 153 | 28% |

**구간 × 코드 인가 검사** (교집합 건수 / 모집단)

| 구간 | 인가 검사 있음 | 인증만 | 인가·인증 없음 | 코드 없음 |
|---|---:|---:|---:|---:|
| route_only | 9 / 27 | 6 / 23 | 32 / 58 | 0 / 0 |
| repository_spec | 8 / 22 | 0 / 7 | 11 / 69 | 0 / 0 |
| synthetic | 0 / 18 | 0 / 0 | 0 / 26 | 0 / 0 |

**정답 label × 코드 인가 검사** (교집합 건수 / 모집단; 패턴 열은 교집합 내 건수)

| 정답 label | 인가 검사 있음 | 인증만 | 인가·인증 없음 | owner/user id 비교 | role/admin | 403/Forbidden |
|---|---:|---:|---:|---:|---:|---:|
| public | 1 / 10 | 4 / 5 | 9 / 51 | 0 | 1 | 0 |
| role_required | 4 / 19 | 0 / 0 | 16 / 28 | 2 | 4 | 0 |
| membership_required | 0 / 2 | 0 / 0 | 0 / 2 | 0 | 0 | 0 |
| tenant_match | 0 / 4 | 0 / 0 | 0 / 4 | 0 | 0 | 0 |
| owner_match | 12 / 28 | 2 / 25 | 15 / 61 | 3 | 3 | 6 |
| owner_or_admin | 0 / 4 | 0 / 0 | 3 / 7 | 0 | 0 | 0 |

**추출 시그널(controller_signals.has_auth_check) 대조(교집합)**: has_auth_check=False ∧ 정규식 인가=False: 48, has_auth_check=False ∧ 정규식 인가=True: 17, has_auth_check=True ∧ 정규식 인가=False: 1

**모델 rationale 유형(교집합, seed 42 기준)**

| 유형 | 건수 |
|---|---:|
| condition_unclear | 28 |
| relation_unspecified | 17 |
| memorized_synthetic | 16 |
| auth_only_noted | 2 |
| multi_condition | 2 |
| other | 1 |

### oas_code: 유형별 대표 5건 (구간 × 인가 검사 유무; id 정렬 상위 5)

**route_only · 인가 검사 있음 (9건)**

- `2c0c5b01954059e821bf` crAPI POST /identity/api/v2/vehicle/register_vehicle — 정답 **owner_match** · 패턴 ['status_403']
  - 코드: `@PostMapping("/vehicle/register_vehicle") public ResponseEntity<CRAPIResponse> registerVehicle(HttpServletRequest request) { CRAPIResponse registerVehicleResponse = vehicleService.registerVehicle(request); if (registerVehicleResponse != null && registerVehicle…`
  - 모델 rationale(seed 42): description: 핸들러에 인가 관련 코드가 포함되어 있으나, 요청자와 객체 간의 관계가 명시되지 않음; 판단: 접근 조건이 확정되지 않아 보류
- `4033e696c5dc2d5b3aa2` juice-shop POST /api/Feedbacks — 정답 **owner_match** · 패턴 ['owner_cmp', 'auth_only']
  - 코드: `export const forgedFeedbackChallenge = () => (req: Request, res: Response, next: NextFunction) => { challengeUtils.solveIf(challenges.forgedFeedbackChallenge, () => { const user = security.authenticatedUsers.from(req) const userId = user?.data ? user.data.id :…`
  - 모델 rationale(seed 42): description: 다양한 인가 검사가 포함되어 있으나, 특정 접근 조건이 명확히 정의되지 않음; 판단: 여러 독립 조건이 결합되어 있어 단일 라벨로 표현할 수 없으므로 보류
- `580f801a0d75c34f1331` crAPI POST /identity/management/admin/lockUser — 정답 **role_required** · 패턴 ['role_admin']
  - 코드: `@PostMapping("/admin/lockUser") public ResponseEntity<CRAPIResponse> lockAccount( @RequestBody LockAccountForm lockAccountForm, HttpServletRequest request) throws UnsupportedEncodingException { CRAPIResponse response = userService.lockAccount(request, lockAcco…`
  - 모델 rationale(seed 42): description: 인가 관련 코드가 포함되어 있으나, 요청자와 객체 간의 관계가 명시되지 않음; 판단: 접근 조건이 확정되지 않아 보류
- `93b3678d43a24b94f1c3` Pixi GET /user_profile/{userid} — 정답 **owner_match** · 패턴 ['owner_cmp']
  - 코드: `app.get('/user_profile/:userid', login_check, function(req, res){ if(!req.params.userid) { res.sendFile('./profile.html', {root: __dirname}); } else { console.log('in here'); res.sendFile('./user_profile.html', {root: __dirname}); } });`
  - 모델 rationale(seed 42): description: 요청자가 userid를 제공하지 않으면 인덱스 페이지를 반환; 판단: 접근 조건이 명확히 정의되지 않아 보류
- `a1be3b47f9420231f409` Pixi GET /admin/likes/search — 정답 **role_required** · 패턴 ['owner_cmp', 'role_admin']
  - 코드: `app.get('/admin/likes/search', function(req, res){ console.log(req.query.search); mongo.connect(dbname, function(err, db){ //db.collection('users').find({ $text : { $search: req.query.search} }) .toArray(function(err, search){ db.collection('likes').find( {$or…`
  - 모델 rationale(seed 42): description: 요청자가 검색어에 따라 likes를 조회하지만, 인증 및 인가 조건이 명시되지 않음; 판단: 접근 조건이 불확실하여 보류

**route_only · 인가 검사 없음 (38건)**

- `0293603d276a2bdbefe0` Pixi GET /user_delete_photo — 정답 **owner_match** · 패턴 없음
  - 코드: `app.get('/user_delete_photo/', function(req, res) { console.log('in delete' + req.query.picture_id); if(!req.query.picture_id) { res.json('NO PICTURE SPECIFIED TO DELETE'); } else { mongo.connect('mongodb://pixidb:27017/Pixidb', function(err, db){ db.collectio…`
  - 모델 rationale(seed 42): description: 인증 후 접근 조건이 명확하지 않음; 판단: 여러 조건이 결합되어 있어 단일 라벨로 표현할 수 없으므로 보류
- `063fa7598db37c095700` juice-shop POST /api/Quantitys — 정답 **role_required** · 패턴 없음
  - 코드: `export const denyAll = () => expressJwt({ secret: '' + Math.random() } as any)`
  - 모델 rationale(seed 42): Conflicting owner and tenant requirements are deliberately unresolved; denyAll() blocks all requests.
- `0a3ece0464909469b61e` juice-shop GET /rest/track-order/{id} — 정답 **owner_match** · 패턴 없음
  - 코드: `export function trackOrder () { return (req: Request, res: Response) => { // Truncate id to avoid unintentional RCE const id = !utils.isChallengeEnabled(challenges.reflectedXssChallenge) ? String(req.params.id).replace(/[^\w-]+/g, '') : utils.trunc(req.params.…`
  - 모델 rationale(seed 42): description: 요청자가 전송된 id에 대한 검사 조건이 명시되어 있으나, 인가 관련 코드가 포함되어 있지 않음; 판단: 접근 조건이 확정되지 않아 보류
- `0aa2fbdb066b3d771316` crAPI POST /identity/management/user/apikey — 정답 **role_required** · 패턴 없음
  - 코드: `@PostMapping("/user/apikey") public ResponseEntity<ApiKeyResponse> generateApiKey( @RequestBody LoginForm loginForm, HttpServletRequest request) throws UnsupportedEncodingException { ApiKeyResponse response = userService.generateApiKey(request, loginForm); ret…`
  - 모델 rationale(seed 42): description: 인가 관련 코드가 포함되어 있으나, 요청자와 객체 간의 관계나 접근 조건이 명시되지 않음; 판단: 접근 조건이 확정되지 않아 보류
- `0f5b4d569c99d8d9c870` Pixi GET /love_photo/{picture_id} — 정답 **public** · 패턴 없음
  - 코드: `app.get('/love_photo/:picture_id', login_check, function(req, res){ console.log('in love ' + JSON.stringify(req.params.picture_id)); if(!req.params.picture_id) { res.json('NO PICTURE SPECIFIED TO LOVE PUT ON GET') } else { //db call- if like exists, delete it,…`
  - 모델 rationale(seed 42): description: 다양한 조건이 결합되어 있으며, 특정 역할이나 소유자 관계가 명시되지 않음; 판단: 접근 조건이 복합적이며 단일 라벨로 표현할 수 없어 보류

**repository_spec · 인가 검사 있음 (8건)**

- `1d45c0e2ac7bb00728b3` DVWS-node POST /api/v2/users/profile/import/xml — 정답 **owner_match** · 패턴 ['role_admin']
  - 코드: `importProfileXml: async (req, res) => { // Scenario: User imports profile from XML. // Vulnerability: The endpoint blindly accepts fields from the XML. // Mass Assignment: If XML contains <admin>true</admin>, user becomes admin. const xmlData = req.body.xml; i…`
  - 모델 rationale(seed 42): description: XML에서 admin 플래그가 포함될 수 있으며, 이는 인가를 우회할 수 있는 취약점으로 확인됨; 판단: 접근 조건이 명확히 정의되지 않아 보류
- `208819689993254cc920` DVWS-node POST /api/v2/login — 정답 **public** · 패턴 ['role_admin']
  - 코드: `login: async (req, res) => { const { username, password } = req.body; //set_cors(req,res); res.set('Cache-Control', 'no-store, no-cache, must-revalidate, private') let result = {}; let status = 200; // Vulnerability: Log Pollution via CRLF Injection // We log …`
  - 모델 rationale(seed 42): description: 다양한 권한이 포함되어 있으나, 실제 접근 조건이 명확히 정의되지 않음; 판단: 여러 독립 조건이 결합되어 있어 단일 라벨로 표현할 수 없으므로 보류
- `4d8caf213fb70649fc0f` DVWS-node GET /api/v2/users/profile/export/xml — 정답 **owner_match** · 패턴 ['role_admin']
  - 코드: `exportProfileXml: async (req, res) => { // Scenario: User exports their profile to XML. // Vulnerability: The 'bio' and 'username' fields are user-controlled and concatenated directly. const username = req.body.username || "guest"; const bio = req.body.bio || …`
  - 모델 rationale(seed 42): description: 요청자가 인증을 요구하지만, 접근 조건이 명확히 정의되지 않음; 판단: 인증만 확인되고 요청자-객체 관계가 불확실하여 보류
- `90e39b6520bac57f8f52` DVWS-node POST /api/v2/users/profile/export/xml — 정답 **owner_match** · 패턴 ['role_admin']
  - 코드: `exportProfileXml: async (req, res) => { // Scenario: User exports their profile to XML. // Vulnerability: The 'bio' and 'username' fields are user-controlled and concatenated directly. const username = req.body.username || "guest"; const bio = req.body.bio || …`
  - 모델 rationale(seed 42): description: 요청자가 username과 bio를 직접 조합하여 XML을 생성; 판단: 인증 없이 사용자 제어 필드가 포함되어 있어 보안 취약점이 존재하며, 접근 조건이 명확하지 않음
- `97abea85e395e6649df4` crAPI POST /identity/api/v2/vehicle/add_vehicle — 정답 **owner_match** · 패턴 ['status_403']
  - 코드: `@PostMapping("/vehicle/add_vehicle") public ResponseEntity<CRAPIResponse> addVehicle( @Valid @RequestBody VehicleForm vehicleDetails, HttpServletRequest request) { CRAPIResponse checkVehicleResponse = vehicleService.checkVehicle(vehicleDetails, request); if (c…`
  - 모델 rationale(seed 42): description: 핸들러에 인가 관련 코드가 포함되어 있으나, 요청자와 객체 간의 관계가 명확히 정의되지 않음; 판단: 접근 조건이 확정되지 않아 보류

**repository_spec · 인가 검사 없음 (11건)**

- `0a8fb9b5c84b26b19826` DVWS-node POST /api/download — 정답 **owner_match** · 패턴 없음
  - 코드: `fetch: (req, res) => { const token = req.headers.authorization.split(' ')[1]; // Bearer <token> result = jwt.verify(token, process.env.JWT_SECRET, options); var filename = path.resolve(process.cwd() + '/public/uploads/' + result.user + "/" + req.body.filename)…`
  - 모델 rationale(seed 42): description: 인증 과정이 포함되어 있으나, 요청자와 객체 간의 관계가 명시되지 않음; 판단: 접근 조건이 확정되지 않아 보류
- `0f7af84126bd72a56bd5` DVWS-node POST /api/upload — 정답 **owner_match** · 패턴 없음
  - 코드: `post: (req, res) => { let sampleFile; let uploadPath; let result = {} const token = req.headers.authorization.split(' ')[1]; result = jwt.verify(token, process.env.JWT_SECRET, options); if (req.body.metadata) { try { const metadata = JSON.parse(req.body.metada…`
  - 모델 rationale(seed 42): description: 인증 후 파일 업로드를 요구하지만, 요청자와 객체 간의 관계가 명시되지 않음; 판단: 접근 조건이 확정되지 않아 보류
- `2e45bdad0431b35cfbf5` DVWS-node POST /api/v2/users — 정답 **public** · 패턴 없음
  - 코드: `add: async (req, res) => { let result = {}; let status = 201; res.set('Cache-Control', 'no-store, no-cache, must-revalidate, private') const { username, password } = req.body; try { const obj = await User.findOne({username}); if (obj != null) { if (obj.usernam…`
  - 모델 rationale(seed 42): description: 요청자가 사용자 이름이 중복되지 않도록 확인하고, 이미 존재하는 경우 409 반환; 판단: 접근 조건이 명확하지 않으며, 인증 및 인가 과정이 포함되어 있어 보류
- `324601a8dc9e9ea969bb` crAPI POST /community/api/v2/community/posts/{postId}/comment — 정답 **public** · 패턴 없음
  - 코드: `func (s *Server) Comment(w http.ResponseWriter, r *http.Request) { vars := mux.Vars(r) body, err := io.ReadAll(r.Body) defer func() { if err := r.Body.Close(); err != nil { log.Println("Error closing request body:", err) } }() if err != nil { responses.ERROR(w…`
  - 모델 rationale(seed 42): description: 인증이 필요하지만 요청자와 객체의 관계가 명시되지 않음; 판단: 접근 조건이 확정되지 않아 보류
- `4de2f44349d88f3d6b3a` crAPI POST /identity/api/v2/user/videos — 정답 **owner_match** · 패턴 없음
  - 코드: `@PostMapping(value = "/api/v2/user/videos") public ResponseEntity<?> uploadProfileVideo( @RequestPart("file") MultipartFile file, HttpServletRequest request) { ProfileVideo profileVideoLink = profileService.uploadProfileVideo(file, request); if (profileVideoLi…`
  - 모델 rationale(seed 42): description: 인증이 필요하지만 요청자와 객체 간의 관계가 명시되지 않음; 판단: 접근 조건이 확정되지 않아 보류

seed별로만 보류된 건(합집합−교집합 52건): seed 42 9, seed 43 34, seed 44 39.

## test_v30 전체: 코드 인가 검사 × 정답 (코드 있는 265건)

| 구간 | 인가 검사 있음 (정답 manual) | 인증만 (정답 manual) | 인가·인증 없음 (정답 manual) |
|---|---:|---:|---:|
| route_only | 27 (manual 0) | 23 (manual 0) | 59 (manual 1) |
| repository_spec | 22 (manual 0) | 7 (manual 0) | 69 (manual 0) |
| synthetic | 29 (manual 11) | 0 (manual 0) | 29 (manual 3) |

## train_v2 대조: 코드 있는 train 레코드 388건(gitea 217 + 합성 171) — 코드 상태별 manual 비율

| 출처 | 건수 | 인가 검사 있음: manual / 전체 | 인증만: manual / 전체 | 인가·인증 없음: manual / 전체 |
|---|---:|---:|---:|---:|
| gitea | 217 | 41 / 132 (31%) | 12 / 69 (17%) | 4 / 16 (25%) |
| synthetic | 171 | 32 / 110 (29%) | 7 / 34 (21%) | 0 / 27 (0%) |
| 합계 | 388 | 73 / 242 (30%) | 19 / 103 (18%) | 4 / 43 (9%) |
| test_v30 정답(코드 265건) | 265 | 11 / 78 (14%) | 0 / 30 (0%) | 4 / 157 (3%) |

**train_v2 "인가·인증 없음 또는 인증만 + manual" 사유별**

| (출처, 코드 상태, 사유) | 건수 |
|---|---:|
| ('gitea', '인증만', 'model_v301/intended') | 10 |
| ('synthetic', '인증만', 'model_v301/intended') | 4 |
| ('synthetic', '인증만', 'subscription_relabel') | 3 |
| ('gitea', '인증만', 'human_review_v2') | 2 |
| ('gitea', '인가·인증 없음', 'model_v301/intended') | 2 |
| ('gitea', '인가·인증 없음', 'visibility_dependent') | 2 |

**train_v2 "인가 검사 있음 + manual" 사유별**

| (출처, 사유) | 건수 |
|---|---:|
| ('synthetic', 'model_v301/intended') | 29 |
| ('gitea', 'model_v301/intended') | 28 |
| ('gitea', 'visibility_dependent') | 10 |
| ('synthetic', 'subscription_relabel') | 3 |
| ('gitea', 'human_review_v2') | 3 |

**train_v2 코드 상태 × label**

| 코드 상태 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| 인가 검사 있음 | 3 | 49 | 22 | 14 | 58 | 23 | 73 |
| 인증만 | 0 | 6 | 4 | 6 | 58 | 10 | 19 |
| 인가·인증 없음 | 24 | 3 | 4 | 2 | 2 | 4 | 4 |

**test_v30 코드 상태 × 정답 label (코드 265건)**

| 코드 상태 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| 인가 검사 있음 | 10 | 19 | 2 | 4 | 28 | 4 | 11 |
| 인증만 | 5 | 0 | 0 | 0 | 25 | 0 | 0 |
| 인가·인증 없음 | 51 | 28 | 2 | 4 | 61 | 7 | 4 |

## 해석 (계산값 기준)

- **oas**: 교집합 171/254 중 route_only 106/108 (98%)는 명세가 없어 모델 입력에 정보가 없는 구간이며 eval-def v2에서는 주지표 제외·보조지표에서 manual을 인정한다. 문제는 repository_spec 65/102 (64%)이다. 합성은 0/44 (0%)로 보류가 없다(템플릿 공유).
- **oas_code**: 교집합 66/250. 코드 상태별 보류율은 인가 검사 있음 17/67 (25%), 인증만 6/30 (20%), 인가·인증 없음 43/153 (28%)로, 인가 검사 유무는 보류를 구분하는 축이 아니다. 구분 축은 서비스(juice-shop 32/68 (47%), DVWS-node 10/25 (40%), crAPI 16/53 (30%), Pixi 8/48 (17%), folio_wiki 0/10 (0%), summit_club 0/14 (0%), VAmPI 0/12 (0%), quill_blog 0/10 (0%), beacon_iot 0/10 (0%))와 정답 label(role_required 20/47 (43%), owner_match 29/114 (25%), public 14/66 (21%), owner_or_admin 3/11 (27%))이다. 합성은 보류 0.
- **train 대조**: train_v2 코드 레코드의 manual 비율은 인가 검사 있음 73/242 (30%), 인증만 19/103 (18%), 인가·인증 없음 4/43 (9%); test_v30 정답은 각각 11/78 (14%), 0/30 (0%), 4/157 (3%). '인가 검사 없는 코드 → manual'을 train이 가르쳤다는 가설은 빈도상 뒷받침되지 않는다(train에서도 그 유형의 대부분은 구체 label). 오히려 train manual은 '인가 코드가 있으나 단일 라벨로 안 떨어지는' Gitea VIS·합성 disputed/extauth에 몰려 있고, 교집합 rationale 유형도 condition_unclear 28, relation_unspecified 17, memorized_synthetic 16, auth_only_noted 2로 '인가 코드는 있으나 요청자-객체 관계가 명시되지 않음/조건 불확정' 서술이 지배적이다. 즉 모델은 test 코드에서 관계 조건을 읽어내지 못할 때 train의 보류 서술 패턴으로 수렴한다.
- **분포 불일치**: train_v2 '인가·인증 없음' 코드는 43건뿐이고 label은 public 24, owner_or_admin 4, membership_required 4, manual_review_required 4(R4 public 중심). test_v30 같은 유형 157건의 정답은 owner_match 61, public 51, role_required 28, owner_or_admin 7. 인증·인가 코드가 보이지 않는 핸들러에서 경로·스키마로 owner_match·role_required를 읽는 사례가 train에 거의 없다(합성 variant 27건 외). 이 유형은 oas_code 교집합의 43/66건을 차지한다.
- rationale 중 'Conflicting owner and tenant requirements are deliberately unresolved; denyAll()…'은 합성 train(campus_records_disputed) rationale의 축자 재생이다. 합성 rationale 템플릿이 test 취약 API 코드에까지 전이되므로 합성 manual 레코드의 rationale 다양성·비중을 점검할 필요가 있다.
- 과보류는 seed 간 공통(교집합/합집합 oas 91%, oas_code 56%)으로 체계적이다. 다음 단계는 (2부) label 조건부 로그확률에 manual 감점 b를 적용하는 사후 문턱 조정으로, b는 val_v2 oas_code에서만 고른다(training/lora/lora_v2_abstain_calib.ipynb, scripts/calib_abstain.py). 데이터 측 조치(manual 쿼터·합성 manual rationale)는 별도 승인 사항이다.

## 2부 준비 상태 (문턱 조정)

- training/lora/lora_v2_abstain_calib.ipynb(생성: build_notebook_calib.py): seed별 final 어댑터 × val_v2(oas 52·oas_code 46) + test_v30(oas 269·oas_code 265)에서 7 label 조건부 로그확률을 teacher forcing으로 계산해 `runs/lora_v2_seed<N>/calib/scores_*.jsonl`에 저장. 생성·학습 없음. Colab **미실행**(사용자 실행 필요, README_colab_calib.md).
- scripts/calib_abstain.py: 감점 b 스윕(0~40, 0.25), val_v2 지표, 선택 규칙(val_v2 oas_code에서 public 오판 0 유지 범위 안 구체 재현율 최대, 동률은 최소 b; seed별 선택), 선택 b를 test_v30에 1회 적용해 eval-def v2 채점, test b 곡선은 참고용 표기. 스크래치패드의 가짜 점수로 실행 경로만 검증했고(산출물은 저장소 밖), 실제 점수 파일이 오기 전까지 결과는 없다.
- 검증 포인트: 점수 파일의 b=0 argmax가 기존 생성 예측 label과 얼마나 일치하는지(스코어링 타당성)를 보고서에 포함한다.
- **1차 Colab 실행(2026-10-24 회수) 결과: 무효.** 회수 파일은 s43 4개·s44 4개(중복 2벌)이고 s42가 없음(다운로드 폴더 이름과 파일 tag 불일치). 모두 mode=full(왼쪽 패딩)이며 최고 label 로그확률 중앙값 −19.5~−21.9 nat(정상은 0 근처), test oas_code에서 b=0 argmax와 생성 예측 일치율 55~62%(oas는 89~92%). val oas_code b=0에서 public 오판>0이라 선택 규칙도 적용 불가. 잠정 보고서 reports/eval/lora_v2/abstain_calib_provisional_s43_s44.md는 참고용이며 결정에 쓰지 않는다. 노트북을 rev 2(for_inference, 오른쪽 패딩, greedy 일치 자가 검증·중단)로 수정했고 재실행이 필요하다.

원자료: reports/eval/lora_v2/abstain_intersection.csv(교집합 전체, 조건별, rationale 유형 포함), lora_v2_seed*/eval/predictions_*_final.jsonl. 해시 가드: data-v1 a99d30da2d29907e…, 62bdadb29cae7aaf…, 9bd47216575afc60…, d0913c27b5de185e… / data-v2 f26c368d051e1ec2…, d0e216dd1267ba7f…, 32e23716422f43dc…, 9bd47216575afc60…, d0913c27b5de185e….
