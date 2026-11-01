# D. 학습 전후 예시 후보 — test_v30 oas_code 합성 제외 207건

- 조건: base(qwen2.5-7B-Instruct, RunPod 예측 reports/eval/lora_v4/base_qwen_runpod)가 **public으로 오판**(정답≠public)했고, LoRA v5 **3 seed(42·43·44) 모두 정답**을 맞힌 레코드. 예측 파일: reports/eval/lora_v5/lora_v5_s4X/eval/predictions_oas_code_lora_v5_s4X_final.jsonl. test_v30.jsonl 해시 확인(`9bd47216…`).
- 207건 중 base가 public으로 오판한 건 77건 → 그중 v5 3 seed 모두 정답 **28건**(1 seed 이상 정답 50건, 3 seed 모두 manual 보류 12건).
- 정답 label별: {'owner_match': 26, 'role_required': 2} · 서비스별: {'DVWS-node': 3, 'Pixi': 10, 'VAmPI': 3, 'crAPI': 8, 'juice-shop': 4}.
- "security 선언" = eval-def v2의 security_state(declared: OAS operation/global에 security 선언, unknown: 선언 없음, explicitly_anonymous: security: []). "소유자 비교/필터" = 핸들러 발췌에 소유자 비교 연산 또는 요청자(토큰 sub·세션 user)로 범위를 고정하는 조회 키가 보이는지(정규식, 참고용).
- 핵심 코드 줄은 인가 관련 키워드 밀도로 자동 선별한 2~3줄이며 발표용으로 쓰기 전에 원문(파일:줄)을 확인한다. 전체 열은 D_before_after_candidates.csv / .json.

## 1. 후보 목록 (추천 순: 소유자 비교 코드 있음 → owner_match → 짧은 경로 → 짧은 코드)

| 순위 | id | method | path | 정답 | base | v5 s42/s43/s44 | security | 소유자 비교 | 핵심 코드 줄 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | 759eb32d69ab1820e44d | GET | /me | owner_match | public | owner_match/owner_match/owner_match | declared | Y | resp = token_validator(request.headers.get('Authorization')) ⏎ return Response(error_message_helper(resp), 401, mimetype="application/json") ⏎ 'admin': user.admin |
| 2 | ff8c5eda79000fa6687f | POST | /books/v1 | owner_match | public | owner_match/owner_match/owner_match | declared | Y | resp = token_validator(request.headers.get('Authorization')) ⏎ return Response(error_message_helper(resp), 401, mimetype="application/json") ⏎ user_id=user.id) |
| 3 | bf900bef2d12400d0880 | GET | /user_info | owner_match | public | owner_match/owner_match/owner_match | unknown | Y | db.collection('users').find( { _id : req.session.user._id }).toArray(function(err, users){ |
| 4 | 7ab0a0779b998f445f3c | GET | /user_loves | owner_match | public | owner_match/owner_match/owner_match | unknown | Y | db.collection('loves').find({ user_id : req.session.user._id}).toArray(function(err, loves){ |
| 5 | e8437c5320794a594af6 | GET | /api/user/info | owner_match | public | owner_match/owner_match/owner_match | unknown | Y | app.get('/api/user/info', api_token_check, function(req, res){ ⏎ if (!req.user.user._id) { ⏎ console.log('user id ' + req.user.user._id); |
| 6 | 745151104eb860a9e9ec | POST | /rest/memories | owner_match | public | owner_match/owner_match/owner_match | unknown | Y | if (file != null) { ⏎ req.body.UserId = authenticatedUsers.tokenMap[utils.jwtFrom(req)].data.id ⏎ res.status(401).json({ status: 'error', message: utils.getErrorMessage(error) }) |
| 7 | bbfd5bfc671dc4af42c5 | GET | /api/user/loves | owner_match | public | owner_match/owner_match/owner_match | unknown | Y | app.get('/api/user/loves', api_token_check, function(req, res){ ⏎ db.collection('loves').find({ user_id : req.user.user._id}).toArray(function(err, loves){ ⏎ db.collection('loves').find({ user_id : req.user.user._id}).toArray(function(err, loves){ |
| 8 | 4014be5658e0ee17ea1e | GET | /rest/wallet/balance | owner_match | public | owner_match/owner_match/owner_match | unknown | Y | if (wallet != null) { ⏎ req.body.UserId = authenticatedUsers.tokenMap[utils.jwtFrom(req)].data.id ⏎ res.status(401).json({ status: 'error', message: utils.getErrorMessage(error) }) |
| 9 | 314ffc8290ffcff7031e | PUT | /rest/wallet/balance | owner_match | public | owner_match/owner_match/owner_match | unknown | Y | if (card != null) { ⏎ req.body.UserId = authenticatedUsers.tokenMap[utils.jwtFrom(req)].data.id ⏎ res.status(401).json({ status: 'error', message: utils.getErrorMessage(error) }) |
| 10 | f8fd9992a61819c2c4af | GET | /api/v2/users/profile | owner_match | public | owner_match/owner_match/owner_match | unknown | Y | (GPL-3.0 발췌 비공개 — https://github.com/snoopysecurity/dvws-node/blob/eb6e2886f2206b88bf709fe1fa311adc3ae3c34f/src/routes/controllers/users.js#L274-L290) |
| 11 | b3906a959a0b669047ba | PUT | /users/v1/{username}/email | owner_match | public | owner_match/owner_match/owner_match | declared | Y | resp = token_validator(request.headers.get('Authorization')) ⏎ return Response(error_message_helper(resp), 401, mimetype="application/json") ⏎ db.session.commit() |
| 12 | 963209fb55865d6f2acf | GET | /api/upload | owner_match | public | owner_match/owner_match/owner_match | unknown | N | (GPL-3.0 발췌 비공개 — https://github.com/snoopysecurity/dvws-node/blob/eb6e2886f2206b88bf709fe1fa311adc3ae3c34f/src/routes/controllers/files.js#L95-L119) |
| 13 | 0a8fb9b5c84b26b19826 | POST | /api/download | owner_match | public | owner_match/owner_match/owner_match | unknown | N | (GPL-3.0 발췌 비공개 — https://github.com/snoopysecurity/dvws-node/blob/eb6e2886f2206b88bf709fe1fa311adc3ae3c34f/src/routes/controllers/files.js#L87-L93) |
| 14 | bf2d1601b02281b85536 | POST | /upload_photo | owner_match | public | owner_match/owner_match/owner_match | unknown | N | 'creator_id': req.session.user._id, |
| 15 | f0ca27ba6aba3b33b9d2 | POST | /profile/image/url | owner_match | public | owner_match/owner_match/owner_match | unknown | N | if (req.body.imageUrl !== undefined) { ⏎ if (url.match(/(.)*solve\/challenges\/server-side(.)*/) !== null) req.app.locals.abused_ssrf_bug = true ⏎ const loggedInUser = security.authenticatedUsers.get(req.cookies.token) |
| 16 | 6309b77a47e9b994f9fe | PUT | /user_info/{userid} | owner_match | public | owner_match/owner_match/owner_match | unknown | N |  |
| 17 | 7292860512c06eed2ffd | PUT | /api/user/edit_info | owner_match | public | owner_match/owner_match/owner_match | unknown | N | app.put('/api/user/edit_info', api_token_check, function(req, res){ ⏎ if (req.body.is_admin) { objForUpdate.is_admin = true; } ⏎ if (req.body.is_admin) { objForUpdate.is_admin = true; } |
| 18 | ab9da003ee3dbde8e544 | POST | /api/picture/upload | owner_match | public | owner_match/owner_match/owner_match | unknown | N | app.post('/api/picture/upload', api_token_check, upload.single('file'), function(req, res, next){ ⏎ 'creator_id': req.user.user._id, ⏎ api.post('/api/picture/upload', api_token_check, upload.single('file'), function(req, res, next){ |
| 19 | 4de2f44349d88f3d6b3a | POST | /identity/api/v2/user/videos | owner_match | public | owner_match/owner_match/owner_match | declared | N | if (profileVideoLink != null) { |
| 20 | c917e3e10dce94cc245c | POST | /identity/api/v2/user/pictures | owner_match | public | owner_match/owner_match/owner_match | declared | N | if (profilePictureLink != null) { |
| 21 | 43e7d3752b50b3dfdd1b | DELETE | /user_delete_photo/{picture_id} | owner_match | public | owner_match/owner_match/owner_match | unknown | N |  |
| 22 | 5928631c56d36ced026a | GET | /identity/api/v2/vehicle/vehicles | owner_match | public | owner_match/owner_match/owner_match | declared | N | List<VehicleOwnership> vehicleOwnerships = vehicleOwnershipService.getPreviousOwners(vin); ⏎ if (vehicleOwnerships != null) { ⏎ vehicleDetail.setPreviousOwners(vehicleOwnerships); |
| 23 | aae57acca0e9317e81c1 | DELETE | /identity/api/v2/user/videos/{video_id} | owner_match | public | owner_match/owner_match/owner_match | declared | N | if (deleteProfileResponse != null && deleteProfileResponse.getStatus() == 200) { ⏎ return ResponseEntity.status(HttpStatus.FORBIDDEN).body(deleteProfileResponse); |
| 24 | d0afe4b052514b189dfa | GET | /identity/api/v2/user/videos/{video_id} | owner_match | public | owner_match/owner_match/owner_match | declared | N | if (profileVideo != null) { |
| 25 | 0b0918598294090d14c3 | PUT | /identity/api/v2/user/videos/{video_id} | owner_match | public | owner_match/owner_match/owner_match | declared | N | if (profileVideo != null) return ResponseEntity.status(HttpStatus.OK).body(profileVideo); |
| 26 | abbb3b1e9239779e76f2 | POST | /identity/api/v2/user/change-phone-number | owner_match | public | owner_match/owner_match/owner_match | unknown | N | if (changePhoneResponse != null && changePhoneResponse.getStatus() == 403) { ⏎ return ResponseEntity.status(HttpStatus.FORBIDDEN).body(changePhoneResponse); ⏎ } else if (changePhoneResponse != null && changePhoneResponse.getStatus() == 404) { |
| 27 | 0e1637db083f68e499d4 | GET | /api/admin/total_money | role_required | public | role_required/role_required/role_required | unknown | N | app.get('/api/admin/total_money', api_token_check, function(req, res){ ⏎ api.get('/api/admin/total_money', api_token_check, function(req, res){ |
| 28 | 580f801a0d75c34f1331 | POST | /identity/management/admin/lockUser | role_required | public | role_required/role_required/role_required | unknown | N | @PostMapping("/admin/lockUser") |

## 2. 발표용 추천 3건 (사람이 코드를 읽고 고름)

### 4. GET /user_loves (Pixi, 정답 owner_match, app/server.js:1285-1297)

- base: public → v5: owner_match/owner_match/owner_match · security 선언: unknown · 핸들러 11줄
- 핵심 줄:

```
db.collection('loves').find({ user_id : req.session.user._id}).toArray(function(err, loves){
```

<details><summary>핸들러 발췌 전문</summary>

```
app.get('/user_loves', login_check, function(req, res){
	mongo.connect(dbname, function(err, db){
	db.collection('loves').find({ user_id : req.session.user._id}).toArray(function(err, loves){
		if(err) { return err };

		if(loves) {
			//console.log(loves);
			res.json(loves);
			
			}
		})
	})
});
```

</details>

### 1. GET /me (VAmPI, 정답 owner_match, api_views/users.py:28-42)

- base: public → v5: owner_match/owner_match/owner_match · security 선언: declared · 핸들러 15줄
- 핵심 줄:

```
resp = token_validator(request.headers.get('Authorization'))
return Response(error_message_helper(resp), 401, mimetype="application/json")
'admin': user.admin
```

<details><summary>핸들러 발췌 전문</summary>

```
def me():
    resp = token_validator(request.headers.get('Authorization'))
    if "error" in resp:
        return Response(error_message_helper(resp), 401, mimetype="application/json")
    else:
        user = User.query.filter_by(username=resp['sub']).first()
        responseObject = {
            'status': 'success',
            'data': {
                'username': user.username,
                'email': user.email,
                'admin': user.admin
            }
        }
        return Response(json.dumps(responseObject), 200, mimetype="application/json")
```

</details>

### 8. GET /rest/wallet/balance (juice-shop, 정답 owner_match, routes/wallet.ts:10-19)

- base: public → v5: owner_match/owner_match/owner_match · security 선언: unknown · 핸들러 23줄
- 핵심 줄:

```
if (wallet != null) {
req.body.UserId = authenticatedUsers.tokenMap[utils.jwtFrom(req)].data.id
res.status(401).json({ status: 'error', message: utils.getErrorMessage(error) })
```

<details><summary>핸들러 발췌 전문</summary>

```
export function getWalletBalance () {
  return async (req: Request, res: Response, next: NextFunction) => {
    const wallet = await WalletModel.findOne({ where: { UserId: req.body.UserId } })
    if (wallet != null) {
      res.status(200).json({ status: 'success', data: wallet.balance })
    } else {
      res.status(404).json({ status: 'error' })
    }
  }
}

export const asyncHandler = (fn: (req: any, res: any, next: any) => Promise<any> | any) => (req: any, res: any, next: any) => {
  void Promise.resolve(fn(req, res, next)).catch(next)
}

export const appendUserId = () => {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      req.body.UserId = authenticatedUsers.tokenMap[utils.jwtFrom(req)].data.id
      next()
    } catch (error: unknown) {
      res.status(401).json({ status: 'error', message: utils.getErrorMessage(error) })
    }
  }
}
```

</details>

추천 사유: 세 건 모두 경로가 한 단어 수준으로 짧고, 발췌 안에 '요청자 본인으로 범위를 고정하는 줄'이 한 줄로 보인다 — Pixi는 find({ user_id : req.session.user._id }), VAmPI는 User.query.filter_by(username=resp["sub"])(토큰 sub → 본인 행), juice-shop은 appendUserId()가 토큰에서 UserId를 넣고 WalletModel.findOne({ where: { UserId: req.body.UserId } })로 조회한다. base는 이 줄이 있어도 public으로 답했고 v5는 3 seed 모두 owner_match다. VAmPI /me는 OAS security 선언(declared)까지 있어 '선언 + 코드'를 함께 보여 줄 수 있다.

대안: DVWS-node GET /api/v2/users/profile(owner_match, jwt.verify → decoded.user → findOne, security unknown), Pixi GET /user_info(10줄, `find({ _id : req.session.user._id })`). 후보 28건은 crAPI 8·Pixi 10·VAmPI 3·juice-shop 4·DVWS-node 3이며 crAPI 건은 인가가 서비스 계층(profileService 등)에 있어 발췌만으로는 소유자 비교가 보이지 않는다.

