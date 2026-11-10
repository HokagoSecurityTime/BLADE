# S5 1단계 — data-v6a 데이터 준비 보고 (2026-11-04, 학습·추론 없음)

## 1. 프롬프트 v3.1

- 새 파일 training/data/prompts/policy_label_v3.1.md SHA-256 `e8b6c506fda669ea89790e155c8ad1049d9089965ca537cef726ef4817b6343b`. v3.0.1(`d0913c27b5de…`)은 수정하지 않았다(확인).
- 반영: label_defs_v3.1_draft.md의 네 절(고정 라벨·보류가 필수인 경우·판단 절차·보안과 근거 첫 문단)을 근거 태그(`[Gn]`, `[v3.0.1]`, `[변경]`, `[신설]`) 없이 그대로 넣었다. 예시 8개는 내용 그대로 키 순서만 바꿨고, 출력 절에 키 순서 고정 문장을 넣었다. diff 72줄: reports/eval/lora_v6a/prompt_v31_diff.txt.
- 시스템 프롬프트 토큰: v3.0.1 2699 → v3.1 3798 (+1099; 바이트 10,323 → 14,450). 절별:

| 절 | v3.0.1 토큰 | v3.1 토큰 | 증가 |
|---|---:|---:|---:|
| (머리글) | 188 | 182 | -6 |
| 고정 라벨 | 380 | 1082 | +702 |
| 보류가 필수인 경우 | 294 | 545 | +251 |
| 판단 절차 | 228 | 317 | +89 |
| 보안과 근거 | 281 | 317 | +36 |
| 예시 | 1028 | 1020 | -8 |
| 출력 | 269 | 304 | +35 |

## 2. SFT train/val 재생성 (training/lora/data_v6a/)

| 파일 | 행 | SHA-256 |
|---|---:|---|
| train_sft_v6a.jsonl | 1274 | `63941b0c43a788546321ebcb237bcc4b288b6a7f46281a40f993736989a2d54a` |
| val_sft_v6a.jsonl | 179 | `1d6b223569c9af4fa9f139cac45eb67a9f6ae4215eee592268c23bf9f76e9bc1` |
| test_v30_inputs.jsonl | - | `d65f25b966f61131c0ba5a2341798e56dcd2d3b8da73e9f5d03eb3cd6b0f119a` |
| policy_label_v3.1.md | - | `e8b6c506fda669ea89790e155c8ad1049d9089965ca537cef726ef4817b6343b` |
| data_v6a_hashes.json | - | `c079b9f5735242b4bf2a340dce530236e6d5a2da806dad7c0b7e0d42ebaae288` |

- 원본 data-v5 SFT(train `2351afe93518…`, val `0df4642f439c…`)·data_v5_hashes.json(`39c302c5fb33…`) 해시 검증 뒤 assistant JSON만 키 순서 재직렬화. user 입력·label·rationale·evidence_fields·confidence 값 불변.
- test_v30_inputs.jsonl은 data_v5와 바이트 동일 사본, test_v5_inputs.jsonl은 사본이되 해시 목록에 넣지 않고 run_train_v6.py가 test_v5_manifest.json으로 별도 검증한다(v5와 같은 게이트).

### label 동일 확인

- train: 1274행, id·label·user·source·condition·security_state 필드 차이 0건, assistant 값(키 순서 무시) 차이 0건, 새 순서 전부 적용 True, assistant.label == label 필드 True. label 분포 {'owner_match': 447, 'tenant_match': 83, 'role_required': 326, 'manual_review_required': 163, 'public': 82, 'membership_required': 77, 'owner_or_admin': 96}.
- val: 179행, id·label·user·source·condition·security_state 필드 차이 0건, assistant 값(키 순서 무시) 차이 0건, 새 순서 전부 적용 True, assistant.label == label 필드 True. label 분포 {'public': 13, 'role_required': 50, 'owner_match': 45, 'manual_review_required': 42, 'tenant_match': 8, 'membership_required': 8, 'owner_or_admin': 13}.

### 토큰 길이 분포 (시스템 v3.1 + user + assistant, Qwen2.5 chat template)

| split | 행 | 평균 | 중앙값 | p95 | 최대 | v5 평균 | 증가 | 4096 초과 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| train | 1274 | 4385.9 | 4341.0 | 4850 | 5184 | 3287.0 | +1098.8 | 1125 |
| val | 179 | 4382.0 | 4303 | 4901 | 5114 | 3283.0 | +1099.0 | 157 |

히스토그램(512 구간): train: 3584-4095 148, 4096-4607 842; val: 3584-4095 20, 4096-4607 119
- **4096 초과: train 1125/1274, val 157/179** (id 목록 sft_stats.json). v3.1 시스템 프롬프트가 +1099 토큰이라 거의 모든 행이 기존 max_seq_len 4096을 넘는다. v5 전례(초과 행 제외)를 그대로 적용하면 학습 데이터가 거의 남지 않으므로 적용할 수 없고, SFTTrainer 절단은 assistant 목표를 잘라 부적합하다. **사용자 결정(2026-11-04): A안 승인.**
  - (A안, 승인) max_seq_len을 4096 → 6144로 올린다(학습·추론 동일). 최대 길이 5184로 6144 안에 들어 제외 0건. 하이퍼파라미터 중 이것만 v5와 달라지며(메모리·시간 약 1.4배, H100 80GB에서 QLoRA batch 2×4 가능), 추론 입력도 같은 상한을 쓴다. S4의 ctx6144 우려(학습 길이 밖)는 학습 자체를 6144로 하므로 해당 없다. 배포 시(S5 채택 → GGUF 변환 단계) 시스템 프롬프트 KV 캐시 확인이 필요하다(프롬프트 3,798 토큰).
  - (B안) v3.1 문구를 축약해 4096 안에 들어오게 한다. 늘어난 토큰의 대부분은 고정 라벨·보류 절의 규약 문장이라 축약하면 사용자가 확정한 v3.1 정의가 바뀐다. 축약본을 만들려면 별도 승인이 필요하다.
  - (C안) 4096 초과 행 제외 — 사실상 불가(위 건수).

추론 입력(시스템 v3.1 + user, 생성 프롬프트 포함, 출력 제외) 토큰:

| 입력 | n | 평균 | 최대 | 4096 초과 | 6144 초과 |
|---|---:|---:|---:|---:|---:|
| test_v5_inputs.jsonl|oas_code_user | 283 | 4590.2 | 5150 | 282 | 0 |
| test_v30_inputs.jsonl|oas_code_user | 265 | 4137.7 | 4940 | 135 | 0 |
| test_v30_inputs.jsonl|oas_user | 269 | 3915.8 | 4075 | 0 | 0 |

- 추론도 상한 4096이면 test_v5 oas_code 입력 대부분이 잘리므로(왼쪽 절단 = 시스템 프롬프트 손실) A안의 6144 상한은 추론에도 필요하다. 출력 512 토큰을 더해도 6144 + 512 < 32k 컨텍스트.


## 3. 채점기 파싱 — 키 순서 무관 확인

- run_train.parse()는 `{.*}` 정규식 + json.loads + label 7종 검사라 키 순서와 무관하다. v5 s42 test_v5 예측 282건의 raw를 새 순서로 재직렬화해 다시 parse한 결과 label 동일 282건.
- 표본: {"{\"evidence_fields\": [\"description\"], \"rationale\": \"x; 판단: y\", \"label\": \"owner_match\", \"confidence\": 0.9}": "owner_match", "{\"evidence_fields\":[\"description\"],\"rationale\":\"x\",\"label\":\"public\",\"confidence\":0.6}": "public", "{\"evidence_fields\": [\"description\"], \"rationale\": \"x\", \"label\": \"owner_match\"}": "owner_match", "{\"rationale\": \"x\", \"label\": \"not_a_label\", \"confidence\": 0.9}": null} (confidence 누락도 파싱되고, label이 7종 밖이면 출력 오류).
- 채점기(scripts/eval_test_v5.py, eval_v30.py, eval_combined_v5.py, score_ctx.py)는 prediction["label"]만 읽는다. v6a 예측 파일에는 추가 키(label_prob)가 붙지만 기존 키는 그대로라 기존 채점기를 그대로 쓴다.

## 4. label 토큰 확률 추출 방식 (run_train_v6.py)

JSON 문맥 `… "label": "` 다음에 오는 label 토큰(접두 토큰 `['label', '":', ' "']` 뒤). 토큰화는 접두-안정이다(접두를 먼저 토큰화한 결과가 전체 토큰화의 접두와 같음).

| label | 토큰열 | 구별 가능한 최소 접두 |
|---|---|---|
| public | ['public'] | 1 토큰 ['public'] |
| role_required | ['role', '_required'] | 1 토큰 ['role'] |
| membership_required | ['membership', '_required'] | 1 토큰 ['membership'] |
| tenant_match | ['tenant', '_match'] | 1 토큰 ['tenant'] |
| owner_match | ['owner', '_match'] | 2 토큰 ['owner', '_match'] |
| owner_or_admin | ['owner', '_or', '_admin'] | 2 토큰 ['owner', '_or'] |
| manual_review_required | ['manual', '_review', '_required'] | 1 토큰 ['manual'] |

- 첫 토큰이 겹치는 label: {'owner_match': 'owner', 'owner_or_admin': 'owner'} → 첫 토큰만으로는 owner_match와 owner_or_admin을 구별할 수 없다. 따라서 "첫 토큰 기준"을 **구별 가능한 최소 접두(prefix) 기준**으로 확장한다: 5종은 첫 토큰 1개, owner 2종은 2개(`owner`+`_match` / `owner`+`_or`).
- 추출: greedy 생성 시 `output_scores=True, return_dict_in_generate=True`로 각 생성 위치의 logits를 받는다(추가 forward 없음). 생성 토큰을 하나씩 디코드해 누적 문자열이 `"label": "`(공백 유무 모두)로 끝나는 위치 t를 찾고, 위치 t부터가 label 토큰이다. 기록값(예측 파일 `label_prob` 키):
  - `p_first`: 위치 t의 vocab 전체 softmax에서 선택 label 첫 토큰의 확률.
  - `p_prefix`: 구별 접두 토큰 확률의 곱(5종은 p_first와 같고, owner 2종은 p(owner)·p(_match|owner) 또는 p(owner)·p(_or|owner)).
  - `p_norm` (**판정·문턱·곡선에 쓰는 값**): p_prefix를 7종 후보 질량으로 정규화. 분모 = 첫 토큰이 다른 5종의 p_first 합 + owner 묶음 질량. 선택 label이 owner 계열이면 owner 묶음 = p(owner)·(p(_match|owner)+p(_or|owner))로 정확히 계산되고, 아니면 두 번째 토큰 분포가 없어 p(owner)를 상한으로 쓴다(분모가 커져 p_norm은 보수적으로 작아짐). 후보 밖 토큰 질량은 분모에 넣지 않는다.
  - `p_seq`: 선택 label 전체 토큰열 확률의 곱(참고), `candidates`: 7종 각각의 접두 확률(위 상한 규칙 포함), `label_token_pos`: t.
  - 생성된 `confidence` 필드는 그대로 두고 기록만 한다. 출력 오류(label 위치 없음·7종 밖)는 `label_prob=null`.
- 보류율 곡선: test_v5 283건에서 문턱 τ∈{0.5,0.55,…,0.95,0.99}에 대해 p_norm < τ인 구체 예측을 manual로 돌렸을 때의 정확도·구체 정밀도·보류율. 문턱 선택은 하지 않는다(곡선 보고만).

## 5. 손실 마스킹 (completion-only) 확인

- v5 학습 코드 training/lora/runpod/run_train.py 119행: `trainer = train_on_responses_only(trainer, instruction_part='<|im_start|>user\n', response_part='<|im_start|>assistant\n')` — unsloth의 completion-only 마스킹으로 assistant 구간 토큰에만 손실을 건다(시스템·user 토큰 label = -100). LoRA v2 노트북(training/lora/build_notebook_v2.py 108행)도 같은 호출이다. v5 s42 run.log 머리(`run lora_v5_s42_final data=v5`)로 이 스크립트가 쓰였음을 확인했고, 로그 자체에는 마스킹 문구가 찍히지 않는다(코드 줄이 근거).
- v6a(run_train_v6.py)도 같은 호출을 그대로 쓴다. 출력 순서가 바뀌어도 assistant 구간 전체(evidence_fields·rationale·label·confidence)가 손실 대상이라는 점은 같다.

## 6. 변경하지 않은 것

- data-v5·test_v30·test_v5·test_v31_supp 동결 파일, 프롬프트 v3.0.1, 하이퍼파라미터(LoRA r16·α16·3 epoch·lr 2e-4·batch 2×4·cosine·warmup 10·wd 0.01·seed 42/43/44). 변경은 max_seq_len 4096 → 6144(A안)와 max_new_tokens 256 → 512뿐.
- 학습·추론은 실행하지 않았다. test_v6은 읽지 않는다. 커밋 없음.

