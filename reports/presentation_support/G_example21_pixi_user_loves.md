# 21번 예시 — Pixi GET /user_loves (test_v30 id 7ab0a0779b998f445f3c)

근거: datasets/blade/processed/test_v30.jsonl(SHA `9bd47216…`), 예측 파일 reports/eval/lora_v4/base_qwen_runpod/eval/predictions_oas_code_base_qwen_runpod.jsonl, reports/eval/lora_v5/lora_v5_s{42,43,44}/eval/predictions_oas_code_lora_v5_s*_final.jsonl(참고로 v4 3 seed도 병기). 조건 oas_code, 정답 owner_match(사람 확정 2026-10-20).

## 레코드

| 항목 | 값 |
|---|---|
| 서비스 / 출처 | Pixi (DevSlop, Apache-2.0), 커밋 `cb716a94…`, app/server.js 1285–1297행 (file_sha256 `e932ba6b…`) |
| method / path | GET /user_loves |
| oas_status | route_only — 저장소 명세에 이 경로가 없어 라우트에서 생성한 operation(parameters·responses만 있음, summary·description 없음) |
| **security 선언** | **없음(unknown)**: operation에도 문서 전체에도 `security`·securitySchemes가 없다. 즉 명세만으로는 인증조차 드러나지 않고, 코드 입력(oas_code)에서만 `login_check`가 보인다. |
| 정답 label | owner_match (요청자 세션 사용자 id로 범위를 고정한 본인 목록 조회) |

## 핸들러 핵심 2줄 (app/server.js)

```js
app.get('/user_loves', login_check, function(req, res){
    db.collection('loves').find({ user_id : req.session.user._id}).toArray(function(err, loves){
```

1행: 라우트에 `login_check` 미들웨어(인증). 2행: 조회 조건이 `user_id : req.session.user._id`로 고정돼 요청자 본인 행만 반환 — 경로에 객체 id 파라미터가 없고 세션 사용자로 범위가 결정되는 "본인 목록" 패턴(검수 규약 G4).

발췌 전문(13줄):

```js
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

## 예측과 rationale 원문

| 모델 | label | confidence | evidence_fields | rationale (원문 그대로) |
|---|---|---:|---|---|
| base (Qwen2.5-7B-Instruct, 프롬프트 v3.0.1) | **public** | 0.9 | ["description"] | description: 인증 검사는 있지만, 요청자 id와 객체 user_id가 일치하는 조건이 없으며, 403이 아닌 loves 배열을 반환; 판단: 익명 접근이 허용되는 것으로 보임 |
| LoRA v5 s42 | **owner_match** | 0.9 | ["description", "path_params"] | description: 핸들러 원문 — 요청자 id와 객체 소유자 id(req.session.user._id)를 비교해 다르면 거부; 판단: owner_match |
| LoRA v5 s43 | **owner_match** | 0.9 | ["description", "path_params"] | description: 핸들러 원문 — 요청자 id와 객체 소유자 id를 비교해 다르면 거부; 판단: owner_match |
| LoRA v5 s44 | **owner_match** | 0.9 | ["description", "path_params"] | description: 핸들러 원문 — 요청자 id와 객체 소유자 id를 비교해 다르면 거부; 판단: owner_match |
| (참고) LoRA v4 s42 | owner_match | 0.9 | ["description", "path_params"] | description: req.session.user._id와 loves.user_id를 비교해 다르면 거부; 판단: 소유자 본인만 허용하는 조건이므로 owner_match |
| (참고) LoRA v4 s43 | owner_match | 0.9 | ["description", "path_params"] | description: 핸들러 원문 — 요청자 id와 객체 소유자 id(req.session.user._id)를 비교해 다르면 거부; 판단: owner_match |
| (참고) LoRA v4 s44 | owner_match | 0.9 | ["description", "path_params"] | description: 핸들러 원문 — 요청자 id와 객체 소유자 id를 비교해 다르면 거부; 판단: owner_match |

## 장표·발표 문구 (사용자 확정 2026-11-01)

> **"세션 사용자 id로만 조회하는 코드를 근거로 owner_match 판단"**

- 장표와 발표에서는 위 문구를 쓴다. v5 rationale 원문의 "요청자 id와 객체 소유자 id를 비교해 다르면 거부"는 학습 템플릿 문장이며 실제 코드(`find({ user_id : req.session.user._id })`)는 비교·거부가 아니라 **본인 id로만 조회**하는 형태다. rationale 원문을 장표에 그대로 싣지 않는다. 라벨(owner_match)은 정답과 일치한다.

## 발표에서 말할 때 주의

- base의 rationale은 "인증 검사는 있다"고 인식하고도 "익명 접근 허용"으로 결론을 내 자기모순이 있다(프롬프트 v3.0.1의 public 정의는 "조건 없는 익명 허용"). v5는 세 seed 모두 owner_match이고 confidence 0.9(MIN_CONFIDENCE 0.9 문턱을 넘어 런타임에서도 구체 정책으로 채택됨).
- v4도 이 건은 맞혔으므로 "v4 → v5 개선 예시"가 아니라 "base → LoRA(코드 입력) 개선 예시"로 쓴다. v4·v5 차이를 보이려면 test_v5의 owner_or_admin·membership_required 사례(reports/eval/lora_v5/eval_test_v5.md)를 쓴다.
- security 선언이 없는(unknown) 건이므로 "명세(oas)만 보면 보류/오판, 코드가 있으면 정답"의 예시로 적합하다. 같은 id의 oas 조건 예측은 predictions_oas_*.jsonl에 있다(이 문서에는 싣지 않음).
