# BLADE 작업 규약

기존 프로젝트·인터페이스 규약은 [AGENT.md](AGENT.md)를 함께 읽는다. 아래는 사용자 확정 최신 Phase 3 규약이며, 과거 라벨링 방식과 충돌하면 아래를 따른다.

## Phase 3 — 학습 적격 규약 (v2.5)

- APIs.guru 구체 label 6종의 train/val 포함 조건: `confidence >= 0.6 AND meta.evidence_invalid == false AND meta.flag_review == false`.
- manual_review_required는 사용자 승인에 따라 실제 train 레코드의 25%에 가장 가까운 정수 건수로 seed 42 샘플링한다. 합성 manual도 비율에 포함한다. 남은 APIs.guru manual은 `processed/apisguru_manual_pool.jsonl`에 보존한다.
- 합성은 seed 42로 FastAPI 1개·Express 1개·Spring/Django 중 1개를 선택해 intended_labels를 사용한다. 나머지 합성 3개와 공개 취약 API 5개는 test 전용이다. train 구성 코드는 test 전용 서비스의 데이터·소스를 읽지 않는다. 배정은 `training/data/synthetic_partition.json`에 고정한다.
- service 단위 9:1 분할(seed 42)과 demo_backend 경로 패턴 제거를 수행한다. 구체 label 중 낮은 confidence는 `processed/apisguru_lowconf_pool.jsonl`에 보존한다.
- confidence 0.4 구간(집계상 `0 <= confidence <= 0.5`)은 train에서 제외하되 원본 라벨링 결과 파일에는 보존한다. DATA_CARD에 해당 건수와 제외 사유를 기록한다. 나머지 `confidence < 0.6`도 포함 조건을 충족하지 못한다.
- 사람 검수에서 오라벨률이 20%를 초과한 label은 해당 label의 0.6 구간(`0.5 < confidence < 0.7`)도 train에서 제외한다. 검수 전 오라벨률을 추정해 적용하지 않는다.
- 현재 단계에서 train/val 파일 구성은 승인되었다. 모델 학습은 실행하지 않는다.
- train 라벨은 OpenAI API 모델 `gpt-4o-mini`로 생성하며, `BLADE_LABEL_*` 설정을 사용한다. `qwen2.5:7b`는 베이스라인·파인튜닝 베이스이고 라벨 생성에 사용하지 않는다. API 키를 출력하지 않는다.
- v2.5는 모델이 반환한 label과 confidence를 그대로 보존한다. 낮은 confidence를 이유로 label을 사후 변환하지 않는다.
- 사용자가 v2.5 파일럿의 67% 보류율을 수용하고 전체 2,027건 실행을 승인했다. manual_review 비율 중단 조건은 제거한다. 명시적 익명이 아닌 mutation public은 중단 대신 `meta.flag_review=true`로 표시한다. 다른 파일럿 조건(evidence_invalid >10%, 한 confidence 구간 >=70%)은 유지한다.
- 완료된 파일럿 200건은 해시 검증 후 재사용한다. 이전 데이터와 프롬프트는 보존하며 추가 프롬프트 수정은 하지 않는다.
- test 후보의 제안과 사람 확정은 분리한다. 사용자 승인한 검수 엑셀과 합성 intended_labels로 아래 test 253건을 고정했다. 이후 변경하지 않는다. 공개 취약 API 저장소는 정적 분석만 하고 수정·실행하지 않는다.
- 런타임 `pipeline/`, `proxy/`, `admin_api/` 코드를 수정하지 않는다.

## Frozen human-reviewed test set (2026-10-20)

- `datasets/blade/processed/test.jsonl`: 253 records (vuln 211 + synthetic 42).
- SHA-256: `bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa`.
- Human-confirmed test set is frozen. Do not modify or regenerate it.
- Provenance: `verification/test_frozen_manifest.json`.

## v2.6 검수 반영 (2026-10-20 사용자 승인)

- 실제 검수는 137건 중 교정 61건이며 사용자가 이 수치를 수용했다. seed 42로 few-shot 30건 / 검증 31건을 분리한다. 검증 31건은 프롬프트 예시에 포함하지 않는다.
- v2.6은 v2.5 규칙 본문을 유지하고 가상 few-shot 11개만 사람 교정 30개로 교체한다. 프롬프트 변경은 이 범위에서 승인되었다.
- APIs.guru의 public+security_state=declared, membership_required+confidence<0.9, owner_or_admin을 기계 필터로 제외하고 수정 대상 풀에 보존한다. 합성 라벨은 그대로 유지한다.
- v2.6 파일럿 200건(검증 31 + 같은 원 label/구간에서 추가 169)의 검증 일치율이 60% 미만이면 전체 실행을 중단한다. 60% 이상이면 전체 2,027건 재라벨링과 train/val 재구성을 수행한다.
- review_sample_v6은 기존 검수 137개 ID와 겹치지 않는 train 표본으로 label별 최대 15건이다. 모델 학습은 금지한다.

## 제출 설계 정렬 실험 v2.9 (사용자 승인)

- 새 실험의 `membership_required` 의미는 요청 대상 그룹·팀의 구성원 관계다. 기존 구독·등급 기반 v2.8 이하 결과를 덮어쓰거나 새 의미의 정답으로 간주하지 않는다.
- 최종 고정 라벨은 LLM이 선택한다. 코드 조건 추출은 입력 근거·검증 보조이며 모델 예측을 규칙 라벨로 덮어쓰지 않는다.
- 새 실험은 `training/data/prompts/policy_label_v2.9.md`와 `reports/eval/classification_quality/group_policy_v29/`에 격리한다. 기존 test·train·런타임·정책 스키마를 변경하지 않는다.
- 현재 런타임의 claims.membership/allowed_membership 비교는 대상 그룹 구성원 조회가 아니다. 새 의미의 membership 라벨은 현재 런타임으로 자동 적용하지 않는다. 집행 지원은 별도 설계가 필요하다.

## v3.0 산출물 고정 (2026-10-21 사용자 결정 반영)

- 프롬프트 v3.0.1: `training/data/prompts/policy_label_v3.0.1.md` SHA-256 `d0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef`. 사람 교정 61건 미사용. 프롬프트는 이 버전으로 고정한다.
- 전체 라벨 결과: `datasets/blade/processed/apisguru_labeled_v301.jsonl` SHA-256 `ac34bd1ec3c2eeafe584e09026a5dfd2dc0fbce9b4e045dd5e1e55326905b827` (2,027건, manual 75.48%). 원본은 수정하지 않는다. train 구성 override(declared public 150·비익명 mutation public 5 → manual, 합성 subscription 6 → manual)는 build_train_v30.py에서만 적용한다.
- `datasets/blade/processed/test_v30.jsonl`: 269건 (frozen test 253건 + summit_club 16건). SHA-256 `9bd47216575afc602b03afa20e617308dd9a97476c94e67a117eb17009afd5e2`. 기존 test.jsonl(`bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa`)은 그대로 유지하며 별도 항목이다. test_v30에서 바뀐 것은 구독 membership 6건의 label(→ manual_review_required, meta.v30_relabel_reason)뿐이고 나머지 라인은 바이트 동일. 수정·재생성 금지. 출처: `verification/test_v30_manifest.json`.
- 합성 서비스 추가(`training/data/sources/synthetic_v30.py`, `training/data/synthetic_partition_v30.json`): `summit_club`은 test 전용, `relay_forum`은 train 전용. membership_required는 (caller_id, record.group_id) ∈ memberships의 v3.0 의미다. train 구성 코드는 summit_club 데이터·소스를 읽지 않는다.
- `train_v30.jsonl` 471건 SHA-256 `a99d30da2d29907e8e3fc2d1b8ef313c3d2aa24b1539251130bd08cf96b829e2`, `val_v30.jsonl` 52건 SHA-256 `62bdadb29cae7aaf814007ad8adec40115e8612d70f2911693219399c82b595c` (seed 42, service 단위 분할, manual 쿼터 25%, 기존 train/val/test 불변). `review_sample_v30.md`는 사람 검수 전까지 라벨 확정 자료가 아니며 검수 결과를 학습·프롬프트 예시에 쓰려면 별도 승인이 필요하다.
- 알려진 한계: (1) 코드 입력 시 인증만 있고 인가 검사 없는 핸들러를 public으로 오판(6/15). (2) security 선언에도 public 판정 150건(train에서는 override). 모델 학습은 실행하지 않았다.

## data-v1 동결 (2026-10-21)

데이터셋 버전 이름: **data-v1** = train_v30 + val_v30 (평가: test_v30). 프롬프트 v3.0.1 고정. 아래 파일은 이후 수정·재생성 금지. git tag `data-v1`.

| 파일 | 건수 | SHA-256 |
|---|---:|---|
| datasets/blade/processed/train_v30.jsonl | 471 | `a99d30da2d29907e8e3fc2d1b8ef313c3d2aa24b1539251130bd08cf96b829e2` |
| datasets/blade/processed/val_v30.jsonl | 52 | `62bdadb29cae7aaf814007ad8adec40115e8612d70f2911693219399c82b595c` |
| datasets/blade/processed/test_v30.jsonl | 269 | `9bd47216575afc602b03afa20e617308dd9a97476c94e67a117eb17009afd5e2` |
| training/data/prompts/policy_label_v3.0.1.md | - | `d0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef` |

- data-v2 = data-v1 + 변형 샘플 + 실제 오픈소스 프로젝트 + (확인 후) 추가 취약 API. 평가셋은 test_v30 + data-v2 단계에서 추가하는 실제 프로젝트 held-out test. 동결 목표 2026-10-26, git tag `data-v2`.

## 평가 정의 (2026-10-23)

- **eval-def v1 (구)**: test_v30 전체 269건을 한 정답으로 채점. public 오판 = security_state=declared ∧ 예측 public. 2026-10-22 LoRA v1 보고서(reports/eval/lora_v1/lora_v1_report.md)는 이 정의다.
- **eval-def v2 (신, scripts/eval_v30.py)**:
  1. oas 조건 주지표는 취약 API route_only 109건(명세 없음)을 제외한 160건(repository_spec 102 + 합성 58).
  2. oas 조건 보조지표: route_only 109건에서 manual 예측을 정답으로 인정한 정확도·macro-F1을 별도 표기.
  3. public 오판 = declared ∧ 예측 public ∧ 정답≠public, 분모는 declared ∧ 정답≠public. 구 정의 수치는 "구 정의"로 병기.
  4. 합성 58건은 별도 구간으로만 보고(train 합성과 템플릿 중복 56/58). 주지표 macro-F1은 합성 포함/제외 둘 다 제시.
  5. oas_code 조건의 정답은 변경 없음(3·4만 적용).
- 구간 id 목록: reports/eval_v30_redef/segments.json. test_v30.jsonl은 그대로이며 정답을 바꾸지 않는다. 이후 LoRA v2·로컬 베이스라인 채점은 scripts/eval_v30.py로 한다.

## data-v2 라벨 기준 (2026-10-23, 검수_집계 시트 판정 기준 4줄 그대로)

- test_v30 정답은 "의도된 정책" 기준: 본인 리소스(/user/..., Doer 기준 처리)는 owner_match (test의 /user/dashboard·change-email 등과 동일)
- 저장소 권한 레벨(쓰기·admin)은 role_required, org/팀 멤버십은 membership_required로 처리
- 공개/비공개 저장소 분기(repoAssignment·reqRepoReader·reqAnyRepoReader)는 manual(VIS)
- reqToken만 있고 객체가 없는 엔드포인트는 7종에 맞는 label이 없어 manual(AUTH_ANY)

- VIS+SELF: 요청자가 데이터 범위(본인 star·watch·구독·stopwatch·알림)이면 owner_match, 요청자가 행위자(댓글·머지·리뷰·릴리스·이전·생성·실행)이면 manual
- 인가 검사가 코드에서 빠졌어도 경로·스키마로 의도된 정책이 드러나면 그 정책을 label로 한다(test_v30 취약 API와 동일). 외부 인가처럼 의도를 코드로 확인할 수 없는 경우만 manual.
- 적용 기록: reports/review_v2_r1.md, reports/review_v2_r2.md, reports/review_v2_r3.md, train_v2_draft_r1.jsonl(meta.v2_relabel). 검수 52건은 rule_id=human_review_v2.

## data-v2 동결 (2026-10-23)

데이터셋 버전 **data-v2** = train_v2 + val_v2 (평가: test_v30, eval-def v2). 프롬프트 v3.0.1 고정. 아래 파일은 이후 수정·재생성 금지. git tag `data-v2`.

| 파일 | 건수 | SHA-256 |
|---|---:|---|
| datasets/blade/processed/train_v2.jsonl | 799 | `f26c368d051e1ec2683a1f70ed52162808740d9b06540bbad1fe94988ed47ada` |
| datasets/blade/processed/val_v2.jsonl | 98 | `d0e216dd1267ba7f46eb08e5db955473b11bbd049d875e33eb8032504c0f3ac0` |
| datasets/blade/processed/train_v2_manual_pool.jsonl | 22 | `32e23716422f43dcb77b97bed03acdca5ec1fff9ece93c7794934d987798b32a` |
| datasets/blade/processed/test_v30.jsonl | 269 | `9bd47216575afc602b03afa20e617308dd9a97476c94e67a117eb17009afd5e2` |
| training/data/prompts/policy_label_v3.0.1.md | - | `d0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef` |

- 구성: train_v2_draft_r3(사람 검수 56 + 규칙 R1'·R4·variant_intended_policy + VIS cap 1) → val_v2 그룹 분리(코드 레코드 10%) → train 부분 manual 쿼터 25%. 상세 reports/data_v2_freeze.md, DATA_CARD data-v2 절.
- val_v2 = val_v30 52건(불변) + 코드 val. 사람 검수 레코드는 train에만 있다.

## data-v3 라벨 기준 (2026-10-26 사용자 확정)

- 출처: 실제 오픈소스 핸들러의 "검사 유지(원본) / 검사 제거(변형)" 쌍. 원본 label은 검사 내용으로 규칙 결정한다(rule_id, 근거 줄 기록). test_v30 출처 서비스와 그 포크는 쓰지 않는다. 학습·API 라벨링 없음.
- 변형은 경로·메서드·스키마·핸들러 본문으로 의도된 정책이 드러날 때만 유지하고(변형 label = 원본 label), 아니면 변형만 제외하고 원본은 유지한다. 변형을 manual로 바꾸지 않는다.
- 유지: RealWorld 게시글·댓글 수정/삭제(owner_match), petclinic 공용 기준 데이터(pettypes·specialties·vets) 생성/수정/삭제(role_required), 사용자 생성·전체 목록(petclinic POST /users, fastapi POST·GET /users/), 본인만(관리자 경로 없음, self_only) 쓰는 /users/{id} 하위 보안 자원(webhooks·personalAccessTokens·linkedIdentities 등, owner_match; keep_user_self_subresource — 1b 검수 반영 2026-10-26).
- 제외: owner_or_admin 전체(owner_or_superuser·self_or_superuser 포함 — 관리자 우회는 경로로 알 수 없음), petclinic owners·pets·visits, 기준 데이터 조회, /users/{id} 수정·삭제, owner_or_admin(self_or_admin)인 /users/{id} 하위 자원(drop_user_subresource는 owner_or_admin에만 적용), 경로로 관리자 의도를 알 수 없는 유틸 엔드포인트, 검사가 SQL 안에 있어 줄 단위로 지울 수 없는 경우.
- 1b 지시의 "owner_or_superuser·self_or_superuser 유지"와 "fastapi 사용자 관리 superuser 의존성 유지"는 0번(검수 반영)과 충돌해 사용자 확인 결과 0번을 따른다(둘 다 변형 제외).
- 규칙은 `training/data/build_data_v3_pairs_1b.py` VARIANT_RULES 상수이며 레코드마다 meta.variant_rule / variant_kept / variant_drop_reason을 기록한다. 1단계 검수 40건과 1b 검수본(`reports/data_v3/review_pairs_v3s1b_reviewed.xlsx`)의 variant_label_inferable_from_path_schema 판정이 규칙 결과와 일치해야 빌드가 통과한다. launchbadge/realworld-axum-sqlx(AGPL-3.0)는 제외한다.
- 산출: `datasets/blade/processed/data_v3_stage1b/pairs_{train,val}_v3s1b.jsonl`(1단계 `pairs_*_v3s1.jsonl`은 불변), `reports/data_v3/stage1b_report.md`, 검수 시트 `reports/data_v3/review_pairs_v3s1b.xlsx`. 동결 전이다.

## data-v3 실험 규칙 (학습 전 고정, 2026-10-26)

- 체크포인트: final 고정. val loss 최저 체크포인트를 고르지 않는다. 보류 문턱 조정(manual 감점 b)은 하지 않는다.
- 비교: v3a(train manual 쿼터 25%) vs v3b(쿼터 10%), 각 seed 42·43·44. 하이퍼파라미터·베이스 모델·프롬프트(v3.0.1)는 LoRA v2와 동일.
- 평가: test_v30, eval-def v2(scripts/eval_v30.py). 주지표는 oas_code 합성 제외 macro-F1, 구체 정밀도·재현율, manual 비율, public 오판(신 정의). 우열은 seed 표준편차보다 큰 차이만 인정한다.
- val은 학습 정상 여부(loss 발산·출력 형식) 확인용으로만 쓴다. val·test로 체크포인트·문턱·쿼터를 고르지 않는다.

## data-v3 동결 (2026-10-26, 재동결)

데이터셋 버전 **data-v3a**(train_v3a + val_v3, manual 쿼터 25%)와 **data-v3b**(train_v3b + val_v3, 쿼터 10%). 평가 test_v30(불변) + eval-def v2. 프롬프트 v3.0.1 고정. 아래 파일은 이후 수정·재생성 금지. git tag `data-v3a`, `data-v3b`(같은 커밋).

| 파일 | 건수 | SHA-256 |
|---|---:|---|
| datasets/blade/processed/train_v3a.jsonl | 930 | `1f5d1055ac3d8d407e555c774183acf4c52ceb03ea508391ee5d508484446e66` |
| datasets/blade/processed/train_v3b.jsonl | 787 | `723e3b3a784e624033379dce5e46b243c2c3444c34db7efb5032ea2436a696dd` |
| datasets/blade/processed/val_v3.jsonl | 126 | `69536f8b10e99538673a1beaf96411aba2b18f341e04f9429f717d9d84cbc109` |
| datasets/blade/processed/train_v3a_manual_pool.jsonl | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| datasets/blade/processed/train_v3b_manual_pool.jsonl | 143 | `b43ab0097e59adb9657a4d77d161185918681094e9cb6167f1f03ea1e16c01f3` |
| datasets/blade/processed/synthetic_neutralization_v3.jsonl | 189 | `91bb7aded5416dbd72b12de2690602f9ddcf5becc571fbc86dbfa8c2f6a86626` |
| datasets/blade/processed/rationale_rewrites_v3.jsonl | 242 | `f1c52fe5a4469cb8dfb4040f0e3373a380ea5d31941b877afd317ae576f101af` |
| datasets/blade/processed/data_v3_stage1b/pairs_train_v3s1b.jsonl | 109 | `cc34308a149dee2d92998087002e6f63ab771d083cae07f5604d6828fdfab303` |
| datasets/blade/processed/data_v3_stage1b/pairs_val_v3s1b.jsonl | 28 | `f1826e1c24957e42abbf4d60b6bc5aaeabbf99bd0b60893d1b9014bc8ccf7138` |
| datasets/blade/processed/test_v30.jsonl | 269 | `9bd47216575afc602b03afa20e617308dd9a97476c94e67a117eb17009afd5e2` |
| training/data/prompts/policy_label_v3.0.1.md | - | `d0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef` |
| training/lora/data_v3/train_sft_v3a.jsonl | 929 | `ff931f5e944e23ef7d9249465d174ab809f32c9a77d79dc93638b4353389e9d1` |
| training/lora/data_v3/train_sft_v3b.jsonl | 786 | `85e634a170c83a9bbe209514fa268dc35dc16b9842dbb58dc8aaa0dfac5f92ab` |
| training/lora/data_v3/val_sft_v3.jsonl | 126 | `4de0188e9e6fd73e8f4cefb7e931c9f09e66efb4d1a8e0e86b2843555515ab06` |
| training/lora/data_v3/data_v3_hashes.json | - | `100b8c732c5a60e4704a6ed54de8f18634f373d42abeb4854f6237ec026c1bf7` |

- 구성: data-v2 train 799 + 쿼터 pool_v2 22 + data-v3 코드 쌍 v3s1b train 109(1b 검수 반영) → 합성 정답 문장·해설 주석 제거(189건, 코드 변경 143) + 합성 변형 summary 접미사(Authonly·Extauth·Extguard) 삭제 57건 → label–rationale 정합성 템플릿 재작성 242건(학습 target 변경 157; 구체 label에 보류 표현 0, 빌드 assert) → manual 쿼터(구체/3 = 25%, 구체/9 = 10%; 사람 검수 manual 우선, 나머지 출처별 비례, seed 42). v3a는 manual 후보 222 < 목표 236이라 전부 유지(23.9%). v3b는 manual 79(10.0%), 제외 143은 pool. val_v3 = val_v2 98(합성 중립화) + v3s1b val 28. 상세 reports/data_v3/stage2_report.md.
- SFT 입력 training/lora/data_v3/: 4096 토큰 초과 1건(v3s1b-01a377f65a6b-orig, memos UpdateUser) 제외. 재작성·중립화하지 않은 data-v2 레코드는 data_v2 SFT와 바이트 동일(빌드 assert).
- 학습 스크립트 training/lora/runpod/(run_train.py, run_all.sh, setup.sh, README_runpod_v3.md). 실행 순서 v2-s42(RunPod 기준점, data-v2) → v3a ×3 → v3b ×3, 모든 run 종료 후 runpodctl로 Pod 정지. 학습은 아직 실행하지 않았다.
- 재동결: 첫 동결(train_v3a `7fa3bc54…`)은 rationale 정합성·summary 수정 전이며 태그 push 전에 폐기했다. 위 해시가 유효하다.

## data-v4 검수 규약 (2026-10-28, review/v4_train_review_reviewed.xlsx·test_v31_supp_review_reviewed.xlsx '검수 규약' 시트 원문)

- **G1** (tenant_match): 서버가 자원의 조직·워크스페이스·테넌트를 요청자의 현재 테넌트(세션·토큰의 active organization, activeWorkspaceId, API 키 tenant)와 비교하거나 그것으로 필터. 경로·본문에 대상 테넌트 ID 없음. 라우트 RBAC 권한(checkPermission 등)이 함께 있어도 기능 권한으로 보고 tenant_match. 생성 시 자원 테넌트를 요청자 테넌트로 강제하는 것도 포함.
- **G2** (membership_required): 요청(경로·본문·쿼리)이 대상 그룹(account, workspace, organization, 채널, 강좌, 사용자 그룹)을 지정하고 (요청자, 그룹) 구성원 행을 조회해 허용. 구성원 OR 관리자 우회도 membership_required.
- **G3** (role_required): 전역 역할, 또는 그룹 구성원 확인 뒤 그룹 안 역할(계정 administrator, 그룹 moderator, 강좌 교사)이 결정 조건이면 role_required(기존 추출 규격 유지). 객체 없는 기능에 RBAC 권한만 있는 경우도 포함.
- **G4** (owner_match): 처리 대상이 인증 사용자 본인으로 고정(/me, request.user, 본인 목록·설정·플래그·기기, 본인 명의 생성) 또는 객체 소유자 == 요청자. 관리자 조건이 타인 대상 우회가 아니라 설정 우회일 뿐이면 owner_match.
- **G5** (owner_or_admin): 소유자·당사자(작성자, 발신자/수신자, 관계 당사자) OR 관리자 우회가 실제 조건. 관리자 우회가 없으면 owner_match.
- **G6** (manual_review_required): 서로 다른 유형의 조건이 OR로 분기(공개/비공개 가시성, Zulip access_message·access_stream_by_id, 쿼리 모드별·action별 정책), 조직 설정에 따라 허용 주체가 바뀜, 인증만 확인(객체 없음 포함). Zulip 채널 접근 함수는 membership_required로 일괄 라벨링하지 않는다.
- **G7** (public): 조건 없는 익명 허용만 public(AllowAny, 로그인·토큰 갱신, 무인증 개발용). 익명이 web-public 등 조건부로만 허용되면 manual_review_required.
- **G8** ((test 제외)): test에서는 두 label 사이 경계, 의도 정책 미확정, 의도·구현 충돌, 근거 코드가 발췌에서 누락된 건을 manual로 넣지 않고 제외한다(제외 사유 기록). manual은 G6처럼 보류가 확실한 경우만 넣는다.
- 비고: None
- 그룹 안 역할(계정 administrator, 그룹 moderator, 강좌 교사)은 G3대로 role_required(사용자 확인 2026-10-28: 지시문의 "그룹 한정 모더레이터 → manual"보다 G3 우선).

## test_v31_supp 검수 규약 (2026-10-28 사용자 확정)

- Chatwoot account_id 경로 + account_users 확인 → membership_required
- Flowise 활성 워크스페이스 필터 → tenant_match. 워크스페이스 지정 + 구성원 확인 3건 중 쿼리 모드별 정책이 다른 GET /workspace·GET /workspaceuser 2건은 검수 결과대로 manual_review_required(사용자 확인), membership_required는 1건.
- 구성원 OR 관리자 우회 → membership_required
- 보낸이/받는이 검사: 관리자 우회 있으면 owner_or_admin, 없으면 owner_match
- 그룹 안 역할은 G3(role_required), 전역 역할 → role_required
- 의도 불명확·근거 약한 건은 manual로 넣지 말고 test에서 제외(G8). 제외 목록 datasets/blade/processed/data_v4/test_v31_supp_excluded.jsonl(41건, 사유 포함).
- 검수자: Claude(AI) — 근거 열(코드 발췌·advisory·수정 커밋)만으로 판단, 저장소 직접 확인 없음. 사람 표본 확인 시트 review/test_v31_supp_spotcheck.xlsx(CHANGED 6 + label별 무작위 4, seed 42)는 학습·평가를 막지 않는다.
- 평가: eval-def v2의 별도 조건(보조 구간). 주지표(test_v30 oas_code 합성 제외 207건)는 그대로다. 보고서에 label별 표와 프로젝트별 표를 함께 싣는다(label이 프로젝트에 몰려 있음).
- 코드 본문 비공개: Flowise(enterprise/ 상용 라이선스)·라이선스 미선언 출처(multitenant lab, Generic University)가 든 test 파일은 .gitignore. 공개 시 코드 본문 제외, 링크·커밋만 제공(test_v31_supp_manifest.json).

## data-v4 동결 (2026-10-28)

데이터셋 버전 **data-v4** = data-v3.1b(train_v31b + val_v31, manual 쿼터 10%, 검수 메타 문구 제거) + data-v4 코드 규칙 라벨 추가분(Zulip 12.3, Label Studio 1.23.2). 평가 test_v30(eval-def v2, 주지표 불변) + test_v31_supp(별도 조건). 프롬프트 v3.0.1 고정. 아래 파일은 이후 수정·재생성 금지(git 커밋·태그 `data-v4`는 사용자 승인 후).

| 파일 | 건수 | SHA-256 |
|---|---:|---|
| datasets/blade/processed/train_v4.jsonl | 981 | `1729f79dd1c06408846e4083b2e82fdace113166c0f92fea32e293441791966c` |
| datasets/blade/processed/val_v4.jsonl | 148 | `2b3362b6adcc6da13b0d1c71fcf671b9700f54fedcd57bb6f55010f3c63c9105` |
| datasets/blade/processed/data_v4/train_v4_rule_labeled.jsonl | 440 | `3ce32a737c71d9433b1c7ddf31a93a04328d783d3a4db8e92fff0d092e16ae2d` |
| training/lora/data_v4/train_sft_v4.jsonl | 978 | `5178c35e7c6bd66e7dfcc44ca603c26bb2319edc85b86abe4679646a3b93a593` |
| training/lora/data_v4/val_sft_v4.jsonl | 147 | `52d0187e8f1d048ddae8bbb2c24b39c14d2e1a65b2519cdb1b934b10b9884bff` |
| training/lora/data_v4/test_v30_inputs.jsonl | 269 | `d65f25b966f61131c0ba5a2341798e56dcd2d3b8da73e9f5d03eb3cd6b0f119a` |
| training/lora/data_v4/data_v4_hashes.json | - | `df24db709d1922fadf2a7e7f6f5931ff75ff4310208804cfa8fb70a117ad0867` |
| datasets/blade/processed/train_v31b.jsonl | 787 | `8ca09e29ec00d7816e933f5b6e6bf92a36743d4c41ac2c72a1f66e8639d26543` |
| datasets/blade/processed/val_v31.jsonl | 126 | `5b359e736f34edc176de62f4fea1f985aa7e09652bb3151b78a35e0c94f9d024` |
| training/lora/data_v31/train_sft_v31b.jsonl | 786 | `712efacacbff010fa4d2a10129a345c7cad43e8bcf4ca4633be64d155bbbe0ec` |
| training/lora/data_v31/val_sft_v31.jsonl | 126 | `0d6a1e58dc8d1a741bade9b92311170746b949fc16e50c5e5fc535495e9220cd` |
| training/lora/data_v31/data_v31_hashes.json | - | `6469540f443affdd85f1f55f06727c90ebbd6bde3af8d86a5e58de20507a9f1e` |
| datasets/blade/processed/data_v4/test_v31_supp.jsonl | 222 | `803d914902c7ca2042fd15d4a7852d42e71828e58d4ae4d3ac791fb868e63395` |
| datasets/blade/processed/data_v4/test_v31_supp_excluded.jsonl | 41 | `2c90527e4ffbb134fa95b0d34e02ad51fd65bf4f7ebd5d6f4451fc6c7b026e08` |
| training/lora/data_v4/test_v31_supp_inputs.jsonl | 222 | `97e618e770bbf9950d6846869901819db36fce486d8999d69eb73e286e2a056c` |
| datasets/blade/processed/data_v4/test_v31_supp_manifest.json | - | `8d0857d7f6707760d7e02ed94bcbea448946fa921f9d811b3419ad73391e6a9c` |
| datasets/blade/processed/test_v30.jsonl | 269 | `9bd47216575afc602b03afa20e617308dd9a97476c94e67a117eb17009afd5e2` |
| training/data/prompts/policy_label_v3.0.1.md | - | `d0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef` |

- 학습 출처: Mattermost·Plane은 AGPL이라 제외(사용자 결정 2026-10-27), 허용 라이선스 Zulip(Apache-2.0)·Label Studio(Apache-2.0)로 대체.
- 라벨: training/data/rule_label_v4.py 코드 규칙(G1~G7에서 도출, test·supp 미참조). gpt-4o-mini 1차 라벨은 쓰지 않음(검수 41건 중 일치 20). 검수 완료 71건과 비교 일치 69·불일치 0·규칙 미적용 2(생성 시 본문 조직 검증 미확인, 객체 없는 통화 생성). 440건 중 규칙 라벨 412, 미적용 28(학습 제외). 근거 줄 meta.rule_evidence.
- 선정: Label Studio 저장소 백엔드 변형 그룹당 1건(76 제외) → 프로젝트당 최대 150, 한 label 50% 이하, 목표 label 우선(seed 42): Zulip 150 {'public': 6, 'role_required': 38, 'owner_match': 49, 'owner_or_admin': 8, 'manual_review_required': 49}, Label Studio 66 {'public': 5, 'membership_required': 5, 'tenant_match': 33, 'owner_match': 10, 'manual_review_required': 13}.
- val: 핸들러(뷰 클래스·함수) 단위 그룹 분리, label별 약 10%(seed 42) → 추가분 train 194 / val 22. SFT train 978(manual 13.6%), val 147. 4096 토큰 초과 3건 제외.
- 정합성: 구체 label 보류 표현 0, 검수 메타 문구 0, 규칙 ID·파일 경로 0, test_v30·test_v31_supp와 (서비스, method, 정규화 path) 겹침 0(빌드 assert).
- 사람 표본 검수 시트 review/v4_rule_label_sample.xlsx(label별 최대 10, seed 42; membership 5·owner_or_admin 8은 전수). 상세 reports/data_v4/freeze_report.json, reports/data_v4_build.md.
- 한계: 추가분 membership_required 5건(전부 Label Studio 조직 API), owner_or_admin 8건(Zulip 봇·초대). test_v31_supp는 label이 프로젝트에 몰려 있다(membership 50/55 Chatwoot, tenant 52/55 Flowise, owner_or_admin 19/20 Chamilo).

## 작업 C: hold-out test_v5 · data-v5 · LoRA v5 (2026-10-31, 사전 고정 판정 기준)

- 순서: test_v5 동결 → 학습 보강분 수집 → data-v5 동결 → LoRA v5 학습·평가 → (개선 인정 + 사용자 승인 시) v5 전환. 정지 지점마다 멈추고 보고하며 사용자 승인 후 다음 단계로 간다.
- 사전 고정 판정 기준(작업 시작 전 기록): 새 hold-out test_v5에서 owner_or_admin·membership_required F1이 v4보다 seed 표준편차 이상 오르고, test_v30 구체 정밀도(oas_code 합성 제외 207건, v4 0.811 ± 0.025, 3 seed; 2026-10-31 정정 — 이전 문구의 0.855 ± 0.018은 합성 포함 265건 값)가 v4보다 표준편차 이상 떨어지지 않으면 "개선 인정". 그 외는 "불인정". 표준편차보다 큰 차이만 차이로 인정한다.
- 발표 주 수치는 어떤 경우에도 v4 원본(3 seed, reports/eval/lora_v4/)으로 둔다. v5는 추가 실험으로만 보고한다(reports/eval/lora_v5/lora_v5_report.md). **(2026-10-31 변경: C-5 수용 후 발표 주 수치를 v5로 전환 — 아래 "C-5 수용·마무리" 절)**
- v5 평가(C-4)는 기본 디코딩으로 한다(사용자 결정 2026-10-31). 작업 B의 안정화 디코딩(repetition_penalty 1.1 + JSON 스키마 제약)은 사전 기준 미달로 채택 불가 확정이며 v5 평가에 쓰지 않는다. 추가 실험(스키마 단독, rationale maxLength)은 보류. 상세 reports/eval/stable_decoding/report.md.
- 마감: 2026-11-01(일) 18:00까지 평가, C-5 전환 검증은 같은 날 24:00. 넘기면 v4를 유지한다.
- 출처 제외: test_v5·data-v5 보강분 출처는 data-v1~v4·test_v30·test_v31_supp에 쓴 프로젝트(APIs.guru 라벨링 풀에 든 서비스 포함, 예: discourse.local)와 그 포크, AGPL 프로젝트를 제외한다. **test_v5 출처 프로젝트와 그 포크는 학습 보강분(data-v5) 출처로 쓰지 않는다.**
- test_v5 라벨: 프롬프트 v3.0.1 정의와 검수 규약 G1~G8. LLM·에이전트 초안은 허용하되 전 건을 사람이 확정하고 근거(코드 줄·문서·링크)를 적는다. 검수 시트 review/test_v5_review.xlsx(담당자 열 분할). 동결 후 eval-def v2의 별도 조건으로만 추가하고 주지표는 바꾸지 않는다.
- data-v5 = data-v4 + 보강분. 규칙 라벨은 학습용 프로젝트 코드와 검수 규약에서만 도출하고 test 파일·test 오류 목록을 참조하지 않는다. 규칙 라벨과 검수 결과 일치율 95% 미만이면 동결 전에 멈춘다. 합성·LLM 라벨로 수를 채우지 않는다.
- 기존 동결본(data-v1~v4, test_v30, test_v31_supp)은 해시 확인 후 읽기만 한다. 하이퍼파라미터·프롬프트 v3.0.1은 v4와 같고 seed 42·43·44. final 어댑터만 평가하며 체크포인트 선택·문턱 조정은 하지 않는다. 평가 종료 후 Pod 정지 전에 seed 42 어댑터를 fp16 병합·GGUF Q4_K_M 변환해 저장한다.
- 정지 지점 1 결정(2026-10-31): test_v5 296건 전 건 검수, 시트 변경 없음. 검수 판단 통일(시트 '검수 규약' 탭에 추가): Rocket.Chat 본인 구독 변경은 방 비구성원 거부 시 membership_required·본인 행만 변경 시 owner_match·애매하면 EXCLUDE, canAccessRoom 17건 manual(G6), Ghost POST /posts·/pages EXCLUDE(생성 요청), Umami 팀 관리 role_required(G3)·웹사이트 수정·삭제 manual. 보고서 한계 절에 membership_required의 Rocket.Chat 편중(26/31)과 tenant_match 없음을 기록한다.
- **C-3 병행 예외(사용자 승인 2026-10-31)**: test_v5 검수와 동시에 학습 보강분 후보 수집·규칙 라벨·검수 시트(정지 지점 3)까지 진행한다. 출처에서 Rocket.Chat·Ghost·Umami와 그 포크, 기존 test 출처, AGPL을 제외한다. 규칙은 학습용 프로젝트 코드와 검수 규약에서만 도출하고 test_v5 시트·검수 결과를 참조하지 않는다. data-v5 동결은 test_v5 동결 이후에만 한다. C-4 시작 마감은 2026-10-31(토) 12:00이며 못 맞추면 v4를 유지한다.

- **정지 지점 3 결정(2026-10-31)**: 검수 완료본 review/v5_train_review_reviewed.xlsx(90건, 시트 열 기준 일치 86/90). 규칙 수정 후 416건 전체 재적용: (a) G5_owner_with_superuser_bypass는 대상을 경로 ID로 조회해 소유자 비교(IsTheSameUser 등)할 때만 owner_or_admin이고, 대상이 request.user로 필터되거나 생성 요청이면 owner_match(G4) — Taiga 10건 변경; (b) Dendrite 핸들러에 power level 검사가 없고 event auth에 의존하는 건(send 2·invite·unban·state PUT 2)은 라벨하지 않고 제외; (c) 구성원 확인 뒤 "power level OR 본인 대상"(Dendrite kick)은 NodeBB 채팅 추방과 같이 제외. 라벨 416→412, 수정 규칙 기준 검수 일치율 88/88(제외로 바뀐 2건은 분모 제외). 보강분 manual은 10% 쿼터(구체/9=33건, 하위 유형별 비율 유지, seed 42), Taiga history 댓글 계열 owner_or_admin은 자원 종류당 2건(20→10, seed 42). 보강분 328건(manual 10.06%), 쿼터·축소 제외 84건은 data_v5/train_v5_pool.jsonl. NodeBB(GPL-3.0) 코드 본문이 든 파일은 .gitignore이고 공개는 data_v5/train_v5_manifest.json(id·저장소·커밋·링크·label)만(DATA_CARD 명시). data-v5 동결(정지 지점 4)은 test_v5 동결(정지 지점 2) 뒤에만 한다.

- **순서 변경(사용자 결정 2026-10-31)**: data-v5를 test_v5보다 먼저 동결한다. 사유: data-v5는 test_v5 label을 읽지 않고 완성됐고(test_v5 후보의 (서비스, method, 경로) 키 겹침 검사만, 동결 시 0건 재확인), test 우선 동결의 목적(test를 보고 학습 데이터를 고르는 것 방지)이 이미 충족됐다. 대신 강제: (a) test_v5는 v5 예측을 생성·열람하기 전에 동결한다. (b) C-4 평가 스크립트(run_train.py)는 data_v5/test_v5_manifest.json의 동결 해시가 없으면 test_v5 평가를 시작하지 않는다(TESTV5 sha 미기입 또는 manifest·입력 부재·불일치 → test_v5 작업 생략). (c) test_v30·test_v31_supp 평가는 학습 직후 바로 진행해도 된다. 평가는 기본 디코딩이며 학습 직후 seed 42 어댑터를 fp16 병합·GGUF Q4_K_M 변환까지 포함한다(runpod/merge_gguf_v5.sh).

## data-v5 동결 (2026-10-31)

데이터셋 버전 **data-v5** = data-v4(train_v4 981 + val_v4 148, SFT 행 바이트 동일) + 코드 규칙 라벨 보강분 328건(Dendrite v0.13.8 Apache-2.0 커밋 763c79f1 · NodeBB v4.16.5 GPL-3.0 커밋 c3d8dc51 · Taiga 6.10.2 MPL-2.0 커밋 4b023d84; train 296 / val 32, 프로젝트별 핸들러 그룹 분리). 평가 test_v30(eval-def v2, 주지표 불변) + test_v31_supp(별도 조건) + test_v5(별도 조건, 동결 후). 프롬프트 v3.0.1 고정. 아래 파일은 이후 수정·재생성 금지(git 커밋·태그 `data-v5`는 사용자 승인 후). NodeBB 코드 본문이 든 파일은 .gitignore(공개는 train_v5_manifest.json).

| 파일 | 건수 | SHA-256 |
|---|---:|---|
| datasets/blade/processed/train_v5.jsonl | 1277 | `528b36907768de8d6b4253fbcb587254b5009cb33f6d38bb35e79bd3b03c6344` |
| datasets/blade/processed/val_v5.jsonl | 180 | `43d53150be7bba9564f21bfddbc225b8ebbd99bcd86a6f30e96ad898f15c81e9` |
| datasets/blade/processed/data_v5/train_v5_rule_labeled.jsonl | 432 | `6f2e02f933a88cbb84a6d8c7ea57f42a81b2c3d8db62d4559c20217209876988` |
| datasets/blade/processed/data_v5/train_v5_selected.jsonl | 328 | `12f45304c9f4a1884a09dc62ca877b8e04da21c0f6a20751109742c5bc1f8e8d` |
| datasets/blade/processed/data_v5/train_v5_pool.jsonl | 84 | `d5916fb43ea34c81b69aca2f3d252c175cada01156aa8ec59d99c2631acc0ebf` |
| training/lora/data_v5/train_sft_v5.jsonl | 1274 | `2351afe93518f6e29c95ab9305a15b5a1cda7bd6e3c6d18bec7e8e3d45c3216b` |
| training/lora/data_v5/val_sft_v5.jsonl | 179 | `0df4642f439c812d4e7b9f5ca968c89fd966703bfc59229d6f7ea7f83115748f` |
| datasets/blade/processed/data_v5/train_v5_manifest.json | - | `95efb605c79f46081550f08c8d41d985c4fda6bb85cd09b77d43f677e2ff7659` |
| training/lora/data_v5/data_v5_hashes.json | - | `39c302c5fb33d1b1506487678cd15f40cc83ffd59435449522786388554753ac` |
| training/data/rule_label_v5.py | - | `daa28db3992b2d2bfd4a99a863c1b8d3d86045fdde52e6d9f66d1f2d8fcd7c67` |
| review/v5_train_review_reviewed.xlsx | - | `4d70711494bf63ad0a0644e75967f236a204b5799b8dd67847aa508a010d519b` |
| training/lora/data_v5/test_v30_inputs.jsonl · test_v31_supp_inputs.jsonl · policy_label_v3.0.1.md | 269 · 222 · - | data_v4와 바이트 동일(`d65f25b9…`, `97e618e7…`, `d0913c27…`) |

- SFT: train 1274(manual 163 = 12.79%; data-v4 13.6%), val 179. 4096 토큰 초과 0건. 보강분 label 분포(train/val): owner_or_admin 41/4, membership_required 17/2, owner_match 76/9, role_required 106/12, manual_review_required 30/3, public 26/2.
- 검수: review/v5_train_review_reviewed.xlsx 90건(검수자 이혜인) — 수정 전 규칙 0.956(86/90), 불일치 4건은 규칙 수정으로 해소, 수정 후 88/88. 정합성: 구체 label 보류 표현 0, 검수 메타 문구 0, 규칙 ID·파일 경로 0, test_v30·test_v31_supp 겹침 0, test_v5 후보 키 겹침 0.
- test_v5_inputs.jsonl은 data_v5_hashes.json에 넣지 않는다. test_v5 동결 시 data_v5/test_v5_manifest.json 해시로 별도 검증한다(run_train.py TESTV5). 상세 reports/data_v5/freeze_report.json, reports/data_v5/stop4_data_v5_freeze.md.

- **C-4 평가 범위(사용자 결정 2026-10-31)**: v2·v3b는 재추론하지 않는다(기존 기록 사용). test_v30·test_v31_supp는 v5 3 seed만 새로 추론하고 base·v4는 reports/eval/lora_v4의 기존 예측을 쓴다. test_v5는 base 1회·v4 3 seed·v5 3 seed를 추론한다(run_all.sh 항목 모드 `v5test` = `--eval-only --jobs v5test`, test_v30·supp 재예측 없음). 모두 기본 디코딩.

## test_v5 동결 (2026-10-31, 정지 지점 2)

hold-out **test_v5** = Rocket.Chat 8.9.0(`057a927d`, MIT) · Ghost v6.73.0(`5794cfd8`, MIT) · Umami v3.4.1(`559e3c60`, MIT) 핸들러 283건, 사람 확정(검수 완료본 review/test_v5_review_reviewed.xlsx, 전 건 확정 근거 기재). 제외 13건(G8, 사유 포함). v5 예측 생성 전에 동결했고(순서 변경 강제 (a)), data-v5·test_v30·test_v31_supp와 (서비스, method, 정규화 path) 겹침 0. eval-def v2의 별도 조건으로만 추가하며 주지표는 불변. 아래 파일은 이후 수정·재생성 금지(git 커밋·태그는 사용자 승인 후).

| 파일 | 건수 | SHA-256 |
|---|---:|---|
| datasets/blade/processed/test_v5.jsonl | 283 | `7b8e4a940967ec474e0d5dbf6dcdbd6b7e04be439599c2a684664d6b9393fd9c` |
| datasets/blade/processed/data_v5/test_v5_excluded.jsonl | 13 | `56161a35cda3c7d487eecc16266a185a6f0cf9c09ac4c62e6542ca29488a839f` |
| datasets/blade/processed/data_v5/test_v5_manifest.json | - | `57fd384f46e89e905209e627a7ff7fb9f312e22a7bed222639e91a80bd05fccd` (= run_train.py TESTV5 sha) |
| training/lora/data_v5/test_v5_inputs.jsonl | 283 | `9103cd3d5276ab425f577a2866291bf8e27e7a06a18bd725701989673dbe5d82` |
| review/test_v5_review_reviewed.xlsx | 296행 | `6a6e1405b7de39c9dec1382594ec0fedda05a82ce0bf796eabee456e12a0c54f` |

- label 분포: role_required 111 · manual_review_required 65 · owner_match 34 · membership_required 33 · owner_or_admin 21 · public 19. 한계: membership_required의 Rocket.Chat 편중 28/33, tenant_match 0건, owner_or_admin support 21. 상세 reports/data_v5/stop2_test_v5_freeze.md.
- 1단계(LoRA v5 학습·test_v30·supp 평가) 결과는 reports/eval/lora_v5/lora_v5_report.md(판정은 아래 "LoRA v5 평가·판정" 절). 2단계(test_v5 예측: base 1·v4 3 seed·v5 3 seed, 기본 디코딩)는 완료됐다. s42 GGUF Q4_K_M은 **만들지 않는다**(C-4 시점 결정, 이후 C-5 승인으로 컨테이너 디스크에서 생성 — "C-5 전환 결과" 절; 당시 사유 2026-10-31: Network Volume 할당량 초과로 병합 임시 파일 35GB를 쓸 수 없음. 08:39·10:24 UTC 시도 모두 Disk quota exceeded). GGUF는 C-5 전환(개선 인정 + 승인) 시에만 별도로 만든다.

## LoRA v5 평가·판정 (2026-10-31, C-4 완료 — 정지 지점, 사용자 승인 대기)

- 2단계 test_v5 예측(base 1·v4 3 seed·v5 3 seed, 기본 디코딩)은 07:39–08:39 UTC에 완료했고 모든 run이 test_v5 manifest 해시(`57fd384f…`)를 검증했다. 채점 scripts/eval_test_v5.py → reports/eval/lora_v5/scores_test_v5.json, eval_test_v5.md. 보고서 reports/eval/lora_v5/lora_v5_report.md.
- 사전 고정 기준 적용(oas_code 조건): test_v5 owner_or_admin F1 v4 0.394 ± 0.055 → v5 0.536 ± 0.031(+0.142), membership_required 0.488 ± 0.022 → 0.589 ± 0.048(+0.101), test_v30 구체 정밀도(207건) 0.811 ± 0.025 → 0.796 ± 0.025(−0.015 < sd). 세 조건 충족 → **개선 인정**. test_v5 oas_code macro-F1 0.582 ± 0.016 → 0.683 ± 0.016, manual 21.4% → 16.6%, 세 프로젝트 정확도 모두 상승. oas(명세만) 조건에서는 차이 없음(두 판정 label 모두 0 근처). 기준 문구가 입력 조건을 명시하지 않아 oas_code(기존 주지표 조건)에 적용한 것은 사용자 확인 대상.
- 발표 주 수치는 v4 원본 그대로. v5는 추가 실험. C-5 전환(Modelfile 등록·BLADE_CLASSIFIER 연동)과 GGUF 생성·커밋·태그는 사용자 승인 뒤에만 한다. (2026-10-31 이후 상태는 "C-5 수용·마무리" 절) GGUF는 Network Volume 할당량 초과로 Pod에서 못 만들었고(사용자 결정: 만들지 않음) C-5 승인 시 컨테이너 디스크로 별도 생성한다.
- 실행 기록: 06:17(미동결, TESTV5 게이트 거부)·07:12(setup.sh 생략, transformers 없음) 시도는 예측을 만들지 못했다. Pod 재시작 후 첫 명령은 setup.sh(README_runpod_rerun.md 4.5절).

## C-5 전환 (사용자 결정 2026-10-31, 마감 일요일 24:00)

- 판정 적용 조건 oas_code 승인(주지표·기존 판정과 동일). 보고서 3b절 유지. 개선 인정 확정.
- 보고서 한계 절 추가: test_v30 public 오판 v4 1/0/0 → v5 3/2/1(분모 35, 건별 id), owner_match F1 하락(0.798→0.752)과 혼동표, test_v5 membership 28/33 Rocket.Chat, test_v5 라벨링 방식(AI 1차 판정 + 사람 확인; 확인 범위는 사용자가 알려줄 예정).
- Pod(GPU, 새 스토리지): (a) s42 GGUF Q4_K_M — 임시 파일은 컨테이너 디스크(runpod/run_c5.sh, setup_c5.sh, merge_gguf_v5.sh WORK_DIR/HF_HOME/DROP_HF_CACHE), (b) 변환 동등성 test_v30 oas_code — 같은 adapter(s42) HF final 대비, 허용 폭은 v4 때와 같은 규칙(3-seed 표준편차), (c) val_sft_v5로 MIN_CONFIDENCE — v4와 같은 규칙(choose_threshold_v4.py --rule precision, 바닥 0.7), test 사용 금지. 입력·추론은 eval_ollama_v5.py(data_v5 해시 검증, 프롬프트 v3.0.1).
- 로컬: Ollama에 blade-qwen-lora-v5 등록, v4는 롤백용으로 유지. 모델명·MIN_CONFIDENCE는 BLADE_LORA_MODEL·BLADE_LORA_MIN_CONFIDENCE 환경변수로 전환(런타임 코드 수정 없음). scripts/verify_lora_pipeline.py 종단간 검증 + pytest 전체.
- 발표용 수치 표(근거 파일 경로 포함): test_v30 oas_code 합성 제외 207건 base/v5(구체 정밀도·재현율·macro-F1·manual 비율·public 오판 /35), test_v5 oas_code 283건 base/v4/v5(macro-F1·정확도·owner_or_admin F1·membership F1), test_v31_supp oas_code base/v5(macro-F1). 발표 주 수치 v4 원본 유지 원칙은 그대로.
- 끝나면 Pod 정지, 커밋 없이 보고 후 정지. 번들 blade_c5_v5_20261031.tgz SHA-256 `c225fc35d0ad616b6064c36595e6d3405f473f37953f2dcd0626c4fec2cdace4`, 절차 README_runpod_rerun.md 4.6절.

## C-5 전환 결과 (2026-10-31, 보고 후 정지 — 커밋·태그 없음)

- 판정 확정: 사용자가 oas_code 조건 적용을 승인해 LoRA v5 **개선 인정** 확정(reports/eval/lora_v5/lora_v5_report.md 3b절). 발표 주 수치는 v4 원본 유지, v5는 추가 실험(발표용 표 reports/eval/lora_v5/presentation_numbers_v5.md, 근거 경로 포함).
- GGUF: s42 final → fp32 병합 → f16 → Q4_K_M, RunPod 컨테이너 디스크(runpod/setup_c5.sh·run_c5.sh·merge_gguf_v5.sh WORK_DIR/HF_HOME/DROP_HF_CACHE, 양자화 재개 quantize_resume_c5.sh). Q4_K_M SHA-256 `2935029694548ed0dff2f5e1aa5bcb87ae553bdfa5535d59ea62b5da9ab2976d`(4,683,073,504 bytes), f16 `2018d6f6…`, 어댑터 `75ea08c1…`. 기록 reports/eval/lora_v5_gguf/{merge_manifest_v5_s42.json, SHA256SUMS_gguf_s42, merge.log, quantize.log, c5.log}. GGUF 본체는 git 밖(로컬 Ollama blob, 원본 <USERPROFILE>\Downloads\GGUF_v5.zip).
- 변환 동등성(test_v30 oas_code, 같은 어댑터 HF s42 final 대비, 허용 폭 = v4 3-seed sd): macro-F1 합성 제외 +0.034(≤0.045), 합성 제외 구체 정밀도 +0.014(≤0.026), 265 정밀도 +0.007(≤0.018) → 수용 제안(v5 자체 sd로는 macro-F1 상승 방향 이탈, 병기). 보류 25.3% → 18.5%. reports/eval/lora_v5_gguf/equivalence_check.md.
- MIN_CONFIDENCE: val_v5만 사용, choose_threshold_v4.py --rule precision → 0.9(v4와 같음). reports/eval/lora_v5_gguf/threshold_val_v5.json.
- Ollama: blade-qwen-lora-v5 등록(Modelfile.blade-qwen-lora-v5, TEMPLATE·PARAMETER v4와 동일), blade-qwen-lora-v4 유지(롤백). 전환은 환경변수만: BLADE_CLASSIFIER=lora, BLADE_LORA_MODEL=blade-qwen-lora-v5, BLADE_LORA_MIN_CONFIDENCE=0.9 (pipeline/classifier/lora.py 기본값은 v4·0.9 그대로, 런타임 코드 미수정). 절차 training/lora/README_serve_v5.md.
- 검증: pytest tests 397 passed · 1 skipped. verify_lora_pipeline.py(demo_backend, BLADE_LLM_PROVIDER=ollama 포함 재실행): lora 경로 7건 중 6건 의도 일치, premium은 런타임 미집행으로 manual(v4와 동일), 프록시 요청 9/9 기대 코드 일치, lora 509.6초/7건. 첫 실행은 BLADE_LLM_PROVIDER 누락으로 roles 추출 실패(pipeline_compare_noprovider.*로 보존). reports/eval/lora_v5_gguf/pipeline_compare.md.
- 보고서 한계 절 추가(public 오판 id, owner_match 혼동표, test_v5 membership Rocket.Chat 28/33, test_v5 라벨링 방식 = AI 1차 + 사람 확인; 확인 범위는 사용자가 알려주면 갱신). scripts/verify_lora_pipeline.py는 출력 경로 환경변수 BLADE_VERIFY_OUT만 추가(v4 기록 보존).

## C-5 수용·마무리 (2026-10-31 사용자 결정, 커밋 실행)

- 변환 동등성: 사전 지정대로 **v4 허용 폭(v4 3-seed sd) 기준 수용 확정**. v5 폭 기준 해석(macro-F1 상승 방향 이탈)은 보고서에 병기 유지. 배포 GGUF 보류율(18.5%)이 평가 모델 HF s42(25.3%)보다 낮은 점을 lora_v5_report.md 6절 한계에 추가.
- **발표 주 수치를 LoRA v5(3 seed, HF 평가)로 전환한다.** 위 절들의 "발표 주 수치는 v4 원본 유지" 규칙은 작업 C 기간(판정 전) 규칙이며 이 결정으로 대체된다. v4는 비교 기준으로 병기. 표: reports/eval/lora_v5/presentation_numbers_v5.md(+.json, 생성 scripts/presentation_numbers_v5.py) — test_v30 207(구체 정밀도·재현율·macro-F1·manual 비율·public 오판 /35), test_v5 283(macro-F1·정확도·manual 비율·owner_or_admin F1·membership F1·프로젝트별 정확도; macro-F1은 support>0 label 6종 평균, tenant_match 정답 0건 제외), test_v31_supp 222(macro-F1 ± sd·정확도·manual 비율·public 오판 /191), 합산 712(보조).
- manual 비율 불일치 해소: v4 test_v30 29.8 ± 5.6%는 합성 제외 207건 분모, 28.6 ± 4.4%는 합성 포함 265건 분모(scores_test_v30.json main_excl_synthetic vs main). 둘 다 정확하며 발표 표는 207 기준으로 통일.
- 세 셋 합산 712건(207+222+283) 재채점은 **보조 지표**(scripts/eval_combined_v5.py → reports/eval/lora_v5/scores_combined_712.json, eval_combined_712.md): base macro-F1 0.147·정확도 0.275·구체 정밀도 0.388·재현율 0.317 → v4 0.469 ± 0.013·0.513 ± 0.019·0.698 ± 0.008·0.534 ± 0.020 → v5 0.521 ± 0.016·0.571 ± 0.013·0.744 ± 0.007·0.601 ± 0.017. 주지표(test_v30 207)는 불변.
- 커밋: feat/lora-pipeline에 data-v5·test_v5 manifest·보고서·스크립트를 나눠 커밋(태그 없음, 해시는 git log·보고 메시지). 코드 본문 비공개 파일(.gitignore)은 제외 확인 — Flowise 코드가 든 training/lora/data_v5/test_v31_supp_inputs.jsonl을 .gitignore에 추가(기존 data_v4 경로만 있었음).
- test_v5 사람 확인 범위는 사용자가 별도로 전달한다(전달 후 lora_v5_report.md 6절·DATA_CARD 갱신).

## 공개 배포 사본 (2026-11-01 사용자 승인)

- 동결 파일은 그대로 두고, 공개 배포에는 `datasets/blade/processed/public/`·`training/lora/public/`의 `*_public.jsonl`과 `withheld_manifest.json`만 쓴다. 코드 본문을 뺀 레코드 162건 = DVWS-node(GPL-3.0) 25 + 라이선스 미선언 5개 저장소 28 + NodeBB(GPL-3.0) 109. SFT 공개 사본은 해당 행을 제외한다. 원본 제외 목록 `public/PUBLIC_EXCLUDE.txt`.
- 빌드 `scripts/build_public_copies.py`(원본 해시 assert), 복원 검증 `scripts/rebuild_from_public.py`(클론 + manifest → 10개 원본 바이트 동일 확인). manifest에는 코드가 아닌 조립 규칙만 둔다. 상세 DATA_CARD "공개 배포 사본과 라이선스 처리"·"Errata"(Dendrite meta.tag 오기).
- 발표 지연 수치는 현재 코드·Docker 기준 p95 +2.0 ms(2026-11-01, verification/METRICS.md), Phase 1 +1.6 ms는 주석 병기. 21번 예시(Pixi GET /user_loves) 문구: "세션 사용자 id로만 조회하는 코드를 근거로 owner_match 판단".
