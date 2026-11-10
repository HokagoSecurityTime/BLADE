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

## 작업 S2: v5 3 seed 다수결 재채점 (2026-11-03, 채점 전 사전 기록 — 학습·추론 없음, 보조 지표)

- 대상: test_v30 oas_code 합성 제외 207 · test_v31_supp oas_code 222 · test_v5 oas_code 283. 기존 v5 seed 42·43·44 예측 파일(reports/eval/lora_v5/lora_v5_s*/eval/)만 읽어 레코드별 label 다수결을 만든다. 재추론 없음.
- 동률 규칙(사전 고정): 3 seed가 모두 다르면 seed 42 예측을 쓴다. 출력 오류는 기권으로 보고 나머지 2개로 다수결하고, 그래도 동률이면 seed 42 예측을 쓴다(seed 42 자체가 기권이면 결과도 출력 오류로 둔다). 3 seed 모두 출력 오류면 출력 오류.
- 지표: macro-F1(support>0 label 평균)·정확도·구체 정밀도·재현율·manual 비율·label별 F1, 정의는 scripts/eval_combined_v5.py와 동일. 단일 seed 평균 ± 표준편차와 나란히 표기한다.
- 산출: scripts/eval_ensemble_vote_v5.py → reports/eval/lora_v5/ensemble_vote.md(+scores_ensemble_vote.json). 주지표·발표 수치는 바꾸지 않으며 커밋하지 않는다.
- S2 결과(사용자 확인 2026-11-03): 다수결은 채택하지 않고 보조 지표로만 유지. 커밋 948cb1a.

## 작업 S3 추가 지시 (2026-11-03 사용자, S3 진행 시 적용 — 과제 본문은 별도 전달 예정)

- 오답 목록에 'S2 동률 여부' 열을 추가한다(test_v5 동률 9건 표시, 출처 reports/eval/lora_v5/scores_ensemble_vote.json tie_records).
- 오류 분석 1순위는 Rocket.Chat 오답. canAccessRoomAsync·hasPermission 계열 호출 여부와 공개 방/비공개 방 분기 유무를 열로 추가한다.
- 같은 레코드에서 seed 간 예측이 갈린 건수를 label 쌍별로 집계한다(어느 경계가 불안정한지).

## 작업 S0: hold-out test_v6 구축 (2026-11-03, 학습·추론·커밋 금지)

- 목적: test_v5는 v5 판정에 썼으므로 이후 dev셋으로 전환한다. test_v6은 최종 판정(S9)용 새 hold-out이다. S9 전까지 어떤 모델로도 test_v6을 추론하지 않는다(동결 시 eval 스크립트에 manifest 해시 게이트·추론 가드 추가). 정지 지점: 1번 후보 보고 후, 2번 검수 xlsx 생성 후, 3번 동결 후.
- 정지 지점 1 결정(사용자 승인 2026-11-03): **A안** — seahub `v14.0.9-server`(`0841826c`, Apache-2.0) 90 · Redash `v26.9.0`(`42fdf9d4`, BSD-2-Clause) 70 · GlitchTip backend `v6.2.6`(`d3039088`, MIT, gitlab.com) 70 · Penpot `2.18.5`(`f4456696`, MPL-2.0) 60 = 290건. Wekan·Papercups 제외. 보고서 reports/data_v6/stop1_test_v6_candidates.md. 클론은 `datasets/blade/raw/opensource/test_v6_candidates/`(.gitignore) 읽기 전용.
- **test_v6 검수 규약 보충**(G1~G8과 test_v5 선례에서 도출, 사용자 확정 2026-11-03):
  1. Redash `current_org` 필터(`get_by_id_and_org(id, self.current_org)`, `current_org` 목록 필터) → tenant_match(G1, Flowise 선례). 프로젝트별 한 label 상한 50%. **(2026-11-03 정지 지점 2 결정, G1-b)** `@require_admin`은 `require_permission("admin")`(permissions.py:86-87)이고 `User.permissions`는 요청자 그룹(Group.org_id로 조직 귀속, ADMIN_PERMISSIONS=["admin","super_admin"] users.py:261)의 권한 합(users.py:173-175)이라 `require_permission`과 같은 조직 그룹 권한 메커니즘이다 → `get_by_id_and_org`/`current_org`와 함께면 tenant_match. `@require_super_admin`(handlers/admin.py 시스템 상태 등 조직 횡단) → role_required.
  2. Redash `require_object_modify_permission`(owner OR admin OR ACL 공유) → manual_review_required(G6, test_v5 Umami canUpdateWebsite 선례). `require_admin_or_owner` → owner_or_admin(G5). `require_access`(데이터소스 그룹 ACL) → manual(G6). **seahub `is_repo_admin` 단독 검사(share/utils.py:39-73: 소유자 OR ACL 공유 관리 권한 OR 부서 관리자)도 같은 구조로 manual(G6) — 2026-11-03 정지 지점 2 결정.**
  (정지 지점 2 결정 2026-11-03) 3.1 Penpot은 5b 유지: read 명령 48건(`get-read-permissions` OR 조직 소유자 경로)은 투입하지 않는다(보조 파일 `data/raw_v6/penpot/candidates_5b_excluded.jsonl`은 조립 미사용). 근거: v3.1 보류 5(설정 의존 → manual), test_v5 resetAvatar 선례, 플래그 기본값이 입력 코드 밖(nitrate.clj)에 있어 모델이 볼 수 없음. Penpot membership 0은 한계로 기록. 대신 seahub 상한을 93 → 최대 110으로 올려 `is_group_member` 엔드포인트에서 membership_required 15건 이상을 보충한다(다른 label 상한·중복 대조 규칙 동일).
  3. seahub `check_folder_permission`: seaf-server RPC(외부 권한 합산)만이면 manual(G6), `is_group_member` 선행 검사가 있으면 membership_required(G2).
  4. seahub org 관리 API(org_admin + `request.user.org.org_id` 필터) → tenant_match(G1).
  5. Penpot `share-id` 겸용 조회(구성원 OR 공유 링크) → manual(G6). `get-organization-owner-permissions` OR 경로가 있는 명령 → EXCLUDE(플래그 의존).
  6. GlitchTip `has_permission`(토큰 스코프)은 근거에서 제외한다. `get_organizations_queryset`(구성원 필터)·`actor_role`만 근거. `open_membership` 설정 분기 → manual(G6).
  7. (Wekan 쟁점은 제외로 소멸)
  8. 근거 부족·경계 → EXCLUDE(G8) 유지. 사유별 제외 건수를 보고하고 **제외율 10% 초과 시 멈추고 보고**한다.
- tenant_match 포함으로 test_v6 label 구성이 test_v5(tenant 0건)와 다름을 SOURCE.md·DATA_CARD에 명시한다.
- 2번 산출: `data/raw_v6/<project>/{extract_*.py, candidates.jsonl, SOURCE.md}`(규격 data/raw_v4/EXTRACTION_SPEC.md + data/raw_v6/EXTRACTION_SPEC_v6.md) → `scripts/build_test_v6.py assemble|sheets` → `review/test_v6_review.xlsx`(모델 v5 예측 열 없음). AI 1차 판정은 코드 규칙·정적 읽기이며 LLM API 호출 없음.
- 다른 세션 작업("작업 S2" 절, reports/eval/human_agreement_v5/, ensemble_vote.*)은 건드리지 않는다.
- **AI 1차 검수·사람 확인 프로토콜(2026-11-04 사용자 결정, 동결 보류)**: 검수자 Claude(AI)의 확정본 review/test_v6_review_reviewed.xlsx(302 = 확정 289 + EXCLUDE 13, 변경 7; 원본 data_v6/review_ai/*_review.jsonl, 병합 scripts/merge_test_v6_ai_review.py)는 사람 확인 전이다. 사람 확인 시트 review/test_v6_human_check.xlsx(scripts/build_test_v6_human_check.py): (1) 공개_우선확인 = EXCLUDE 13 ∪ AI confidence<0.7 ∪ 초안 대비 변경 7 ∪ seahub owner_or_admin→manual 4(확인 질문 명시) ∪ Redash G1-b 경계 18(16 + 일관 적용 2), 중복 제거 44건; (2) 블라인드_감사 = 나머지 258건에서 (AI label × project) 층화 15%, seed 42 → 41건, AI·초안 label·근거·evidence 숨김, 정답키는 data_v6/review_ai/human_check_audit_key.json(시트 밖). 검수자 A/B/C 균등. **사전 기록: 블라인드 감사 불일치율(사람 판정 ≠ AI 확정) ≤ 5%면 나머지 AI 확정을 수용하고, 5% 초과면 전수 사람 검수. 불일치 건은 사람 판정 우선.** 조립 보정: 익명 operation(`security: []`)에 프로젝트 기본 스킴을 스펙 전역 security로 넣어 `explicitly_anonymous`로 통일(26건, build_test_v6.py anonymous_fix, 빌드 assert).
- **동결 보고·DATA_CARD 한계 추가 항목(2026-11-04)**: owner_or_admin support 17(Redash 13); test_v5 public 19건 중 13건(Ghost 7·Umami 6)이 security_state=declared 입력(동결본 불변); test_v6 익명 operation 입력 수정 내역(26건, 빌드 assert).
- **정지 지점 2 재조립본 확정(2026-11-03 사용자)**: 후보 302건(seahub 94 · Redash 74 · GlitchTip 73 · Penpot 61), 검수 시트 review/test_v6_review.xlsx(xlsx는 커밋하지 않음). Redash controller_text의 `User.permissions` 블록은 `require_*` 체인을 쓰는 레코드 전부에 동일 포함한다. 3번 동결 보고·DATA_CARD 한계에 반드시 추가: (a) tenant_match 37 중 Redash 26(70%), membership_required 37 중 GlitchTip 27(73%); (b) Redash G1-b 경계 16건 id 목록(`datasets/blade/processed/data_v6/redash_g1b_boundary_ids.json`, S9에서 따로 집계); (c) S9 보고에 프로젝트별 정확도·label별 F1 필수.

## S1-4 후속 계획 (2026-11-03 사용자 결정, S1-4 확인 후)

- S1-4 산출(커밋 74b17f0): reports/eval/human_agreement_v5/s1_4_report.md(G1~G8 vs v3.0.1 대조: 충돌 4 — G3-a 그룹 안 역할, G1-b tenant+RBAC, G7-a declared mutation public, G8 처리 방식; 정의에 없음 8; 일치 3), label_defs_v3.1_draft.md(v3.1 라벨 정의 초안), confidence_curve_test_v5.md(+.json). S1-3 채점 커밋 fedf1f5.
- v3.1 초안 2차 수정(2026-11-03, 미커밋): (1) G4-c vs G6-b 구분 — 설정이 본인 분기 자체를 켜고 끄면(꺼지면 관리자만) 보류 5(manual), 관리자 조건이 본인 대상의 설정 제한만 우회하면 owner_match. (2) G3-b/G6-c 경계 — "모든 사용자 역할(스태프 역할)이 보유한 권한"은 manual, 통합·API 키 주체는 판단에서 제외, 모델 재정의(permissible)로 일부 역할이 거부되면 role_required(test_v5 Ghost GET posts·GET tags manual / copy·bulkDestroy role_required와 일치 확인). (3) 변경 요약표에 반영 시 안전 가드: v3.1 반영 모델의 public 오판(test_v30 oas_code 합성 제외 207건, 분모 35)이 v5 3 seed 평균 2.0건을 넘으면 불채택. 프롬프트 파일 policy_label_v3.0.1.md는 계속 수정 금지.
- **S4는 프롬프트 v3.0.1을 유지한다**(문맥 효과만 분리해 측정).
- **S5에서 v3.1 프롬프트 반영 + 출력 순서 변경 + confidence를 label 토큰 확률로 산출.** 생성 confidence 필드는 유지하되 판정·문턱에는 label 토큰 확률을 쓰고, 추론 시 scores를 저장한다.
- 발표·논문에서 현재 confidence 문턱을 보류 근거로 쓰지 않는다. 근거: HF 평가 v5 3 seed의 confidence가 test_v5 전 건 0.9 단일값(test_v30·supp도 0.9가 98% 이상)이라 문턱별 정확도–보류율 곡선이 평탄하다(confidence_curve_test_v5.md). GGUF 경로만 val에서 0.7~1.0 분포.

## 작업 S4: 권한 문맥 보강 추론 실험 (2026-11-03, 실행 전 사전 기록 — 학습 없음, test_v6 추론 금지)

- 프롬프트: v3.0.1 그대로(v3.1은 S5). 문맥 효과만 분리한다. 입력은 기존 oas_code 입력 뒤에 `[관련 권한 코드]` 블록을 붙인 것이며, 핸들러 원문은 유지하고 4096 토큰 초과 시 헬퍼를 호출 순서대로 잘라 낸다(잘린 건수 기록). 시스템 프롬프트 2,699 토큰 + 기존 test_v5 oas_code 입력 평균 3,491(최대 4,051) 토큰이라 추가 블록 예산은 평균 약 600 토큰이다.
- 정적 분석기(scripts/build_context_aug_v5.py): 핸들러가 호출하는 권한 관련 함수(auth·permission·access·role·member·owner·admin·can*·has*·is*·check*·ensure*·require*)를 정의까지 깊이 2로 추적하고, 라우트 미들웨어·데코레이터 정의, 권한 정의 파일(Ghost rolePermissions·모델 permissible, Rocket.Chat canAccessRoom 계열 본문·hasPermission 권한명의 보유 역할, Umami can* 정의)을 포함한다. JS/TS + Python·Go·Java(test_v30 crAPI·VAmPI). 정답 label·근거 열·검수 메모·초안은 입력에 쓰지 않는다. 진입점은 각 레코드의 핸들러 위치(meta.source_locations 첫 항목)와 controller_text 본문뿐이며 나머지 source_locations(초안 근거 선택 결과)는 쓰지 않는다.
- 판정셋: test_v5 283(dev). 회귀 확인: test_v30 oas_code 합성 제외 207.
- 채택 기준(사전 고정): test_v5 macro-F1이 v5 대비 seed 표준편차(0.016) 이상 상승, test_v30 207 구체 정밀도가 표준편차(0.025) 이상 하락하지 않을 것, test_v30 207 public 오판(/35)이 v5 평균 2.0건을 넘지 않을 것. 셋 다 충족해야 채택.
- 추론: v5 3 seed final 어댑터, greedy, 기존 디코딩 그대로. S3 재검수로 test_v5 정답이 바뀌면 같은 예측 파일로 재채점만 한다(재추론 없음).
- 정지 지점 1: test_v5 10건(세 프로젝트 고르게) 입력 샘플과 프로젝트별 권한 정의 포함 건수 보고. 정지 지점 2: reports/eval/context_aug_v5/report.md 보고. S4 산출물은 커밋하지 않는다.
- **정지 지점 1 피드백 반영(2026-11-03, 추론 전 사전 기록 추가)**: (1) 정의 해석은 핸들러 파일의 import/require 경로를 따라가며(상대 경로·프로젝트 alias·re-export·Ghost getter/property require), 해석 실패 시 이름 매칭으로 대체하지 않고 미해석 건수를 기록한다. Rocket.Chat omnichannel/livechat 경로 파일은 livechat 라우트일 때만 허용. .d.ts·한 줄 타입 시그니처 제외. (2) 인증 전용 헬퍼(authenticate*, API 키·토큰·세션·해시·비밀번호 계열)는 본문에 인가 검사(역할·권한·소유자·구성원)가 없으면 제외하고, 같은 정의(겹치는 범위)는 한 번만 넣는다. (3) Rocket.Chat 권한표 행은 핸들러·유지된 헬퍼에 문자열로 등장한 권한명만 포함(예산 절단 후 재계산). Ghost 권한표 객체는 docName(발췌 또는 엔드포인트 파일) 또는 canThis(ctx).action.object 체인에서 읽는다. (4) 입력은 두 예산으로 생성한다 — ctx4096(기존 상한), ctx6144(추론 상한 6144, 기존 입력 부분 동일·추가 문맥만 증가). **6144는 학습 길이 밖이므로 seed 42로 두 조건을 먼저 비교하고, 더 나은 쪽만 s43·s44를 진행한다.** (5) 정지 지점 1-2: test_v5 30건(Ghost 8·Rocket.Chat 14·Umami 8, seed 42) 유지 블록을 직접/간접/무관/잘못된 구현으로 분류해 개선 전후를 비교한다(reports/eval/context_aug_v5/stop12_precision.md). 정답 열은 계속 읽지 않는다.
- **3번 추론 승인(2026-11-04, RunPod) — 예산 선택 규칙(seed 42 결과로 판정, 추론 전 기록)**: (1) ctx6144가 test_v30 207 구체 정밀도 하락 > 0.025 또는 public 오판 > 2건(s42 기준)이면 ctx4096 선택. (2) 아니면 test_v5 macro-F1이 높은 쪽. 단 차이 < 0.016(v5 seed sd)이면 ctx4096(학습 길이 안). 최종 채택 판정은 기존 기준 그대로(선택된 예산의 3 seed 평균 vs v5 3 seed). 순서: test_v30 207 입력 빌드(두 예산, 통계·샘플 5건 부록) → seed 42 두 예산 × (test_v5 283 + test_v30 207) 추론·채점 → 규칙으로 예산 선택 → 선택 예산으로 s43·s44 → reports/eval/context_aug_v5/report.md. 추론은 사용자가 RunPod에 직접 올려 실행하고 결과를 전달한다(실행 종료 시 Pod 자동 정지 포함).
- 실행 번들(2026-11-04): export/blade_s4_ctx_20261104.tgz SHA-256 `32054392a499f773dc3015ee69d789437bce1b3286f3aff18c9cff2891682bbf`(run_ctx_eval.py·score_ctx.py·run_s4.sh·README_s4.md, 입력 4개, 프롬프트, v5 3 seed 기준 예측). 어댑터는 기존 볼륨 runs/lora_v5_s4{2,3,4}/adapter 또는 blade_v5_adapters.tar.gz(`db6abe46…`). 채점기 score_ctx.py는 eval_combined_v5.py 정의이며 기준 예측 재채점으로 검증(test_v5 v5 3 seed macro-F1 0.683 ± 0.016, test_v30 207 s42 구체 정밀도 0.767·public 오판 3 일치). test_v30 207 입력은 블록이 붙은 건 13/207뿐(취약 API는 인라인 인가·토큰 검증 헬퍼 위주)이라 사실상 표식 추가에 대한 회귀 확인이다(reports/eval/context_aug_v5/appendix_test_v30_inputs.md). 커밋 없음.
- **S4-3(2026-11-04, RunPod RTX PRO 4000 Blackwell sm_120 24GB, 추론 전 사전 기록)**: 예산 선택 규칙·최종 채택 판정은 위 3번 승인 항목과 동일. 실행 환경(GPU·드라이버·torch/CUDA·transformers·peft·bitsandbytes 버전)은 out/env.json에 기록하고 보고서에 싣는다. 점검 게이트: torch ≥ 2.7(cu128)·CUDA ≥ 12.8·capability (12,0); flash-attn 미사용, attn_implementation="sdpa"; 베이스 로딩은 기존 v5 HF 평가(run_train.py 176-178행: unsloth/Qwen2.5-7B-Instruct-bnb-4bit, load_in_4bit=True, dtype=None(bf16), eval_batch 8, max_new_tokens 256, greedy)와 동일하되 로더는 transformers+bitsandbytes(sdpa)이며 bitsandbytes가 sm_120에서 실패하면 멈추고 보고한다. 기준선 재현: v5 s42·문맥 없는 기존 test_v5 입력 20건(label 비례 층화, seed 42) 추론 → 기존 예측과 label 일치 ≥ 95%(19/20)이면 기존 v5 수치를 기준선으로 쓰고 진행, 미만이면 멈추고 보고. 추론은 seed·셋·예산별 파일에 한 건마다 append 저장·--resume, 순서 s42 ctx4096 test_v5 → s42 ctx6144 test_v5 → s42 ctx4096 test_v30 → s42 ctx6144 test_v30 → 선택 → s43·s44(test_v5 → test_v30). 파일이 끝날 때마다 Pod 밖으로 회수한다. Pod 정지는 사용자가 직접(자동 정지 없음). 커밋 금지.
- S4-3 번들(2026-11-04, rev b, 자동 정지 없음): export/blade_s4_ctx_20261104b.tgz SHA-256 `e7c97a7b11bf0d47bfcb5bf85fdc4cf4ef7393f7cc151471ab36877ac10e0137` — run_ctx_eval.py(transformers+bnb 4bit+sdpa 로더, --resume 한 건 append, --ids), env_check.py(게이트), baseline_check.py(20건 층화 seed 42: role 8·manual 5·owner_match 2·membership 2·owner_or_admin 2·public 1), score_ctx.py, run_s4.sh(순서 고정·파일마다 pack+RETRIEVE_CMD), 원본 test_v5_inputs.jsonl 추가. 이전 번들(`32054392…`, runpodctl 자동 정지 포함)은 대체. 로컬에서 ssh 설정된 세 호스트(195.26.233.52/.96, 185.216.23.189)는 모두 접속 거부 — 현재 Pod 접속 정보 없음.
- S4-3 H100 번들(2026-11-04, 이전 b·c 번들 폐기): export/blade_s4_ctx_h100_20261104.tgz SHA-256 `1920ffff823ff6f8040f4a33c62b3e6f50914dc8ba5e58145c925a0e1b79ba07`(LF 정규화 재빌드). 환경 게이트 torch≥2.4·CUDA≥12.1·capability (9,0) 권장(다른 GPU 경고), transformers 4.x/5.x dtype 인자 자동, 로더 hf(bnb 4bit + sdpa)·배치 8·greedy·256, 자동 정지 STOP_POD=1(정상 종료·게이트 STOP 모두 결과 tar 후 runpodctl stop pod). 어댑터 tar 로컬 위치 <USERPROFILE>/Downloads/export_v5_pahse1/export/blade_v5_adapters.tar.gz(`db6abe46…` 확인). 11-03 Blackwell Pod(hcqy2w9elye9e8)는 어댑터 미업로드로 게이트 STOP 뒤 감시 명령 오류로 정지됨(결과 없음).
- **S4 결과(2026-11-04, H100 Pod 83tcjk0ara7vc4, 16:38–17:10 UTC) — 사전 기준 미달, 불채택**: 환경 게이트 통과(torch 2.8.0+cu128, transformers 5.22.1, peft 0.21.2, bitsandbytes 0.50.2, 로더 hf+sdpa), 기준선 재현 20/20(raw 동일 16/20), 예산 선택 ctx4096(규칙 1: public 오판 3 > 2 — v5 s42와 같은 3건·test_v30 두 예산 입력 동일; 규칙 2로도 ctx4096). test_v5 macro-F1 v5 0.683 ± 0.016 → ctx4096 0.606 ± 0.029(−0.077, 기준 +0.016 미달), test_v30 207 구체 정밀도 0.796 → 0.812(충족), public 오판 3/2/1 → 3/3/1 평균 2.33(기준 ≤ 2.0 미달). 원인: perm_table 블록이 role_required 편향(→role 전이 94건 중 92건이 perm_table 포함 레코드), public→manual 후퇴(public F1 0.894 → 0.691), 블록 없는 57건은 변화 없음. 회수본 reports/eval/context_aug_v5/pod_results/(tar SHA-256 `09755545…`), 보고서 report.md·fixed_newly_wrong.md·analysis.json(scripts/analyze_context_aug_v5.py, 로컬 재채점 = Pod 채점). Pod summary 단계는 score_ctx.py timing 키 오기(rows→rows_total)로 KeyError(예측·채점·pack 뒤라 결과 무영향, 로컬 수정). 주지표·발표 수치 불변, 커밋 없음. 문맥 블록을 다시 쓰려면 학습 입력에도 같은 형식을 넣는 설계(S5 이후)가 필요하다.

## 작업 S5: v3.1 프롬프트 + 근거 먼저 출력 + label 토큰 확률 confidence 재학습 (v6a, 2026-11-04 사전 기록 — 학습 전, 커밋 금지)

- 문맥 블록 없음(S4 불채택; 문맥은 S5b에서 학습 입력과 함께 별도). test_v6 추론 금지.
- 프롬프트: `training/data/prompts/policy_label_v3.1.md`(새 파일, SHA-256 `e8b6c506fda669ea89790e155c8ad1049d9089965ca537cef726ef4817b6343b`, 3,798 토큰; v3.0.1 2,699) = v3.0.1의 고정 라벨·보류·판단 절차·보안과 근거(첫 문단) 네 절을 label_defs_v3.1_draft.md로 교체(근거 태그 제거, 보류 5의 "(G4-c)" 표기 제거), 머리글의 버전 이력 문장 제거(출력 순서 안내 문장만 유지, 사용자 지시 2026-11-04), 예시 8개는 내용 그대로 키 순서만 변경, 출력 절에 키 순서 고정 문장. v3.0.1은 수정 금지(해시 불변 확인). diff reports/eval/lora_v6a/prompt_v31_diff.txt.
- 출력 순서 {evidence_fields, rationale, label, confidence}. 데이터 data-v5 train/val 그대로(label·rationale·user 불변, assistant JSON 키 순서만 재직렬화; diff 0건 확인). SFT `training/lora/data_v6a/`: train_sft_v6a 1274 `63941b0c…`, val_sft_v6a 179 `1d6b2235…`, data_v6a_hashes.json `c079b9f5…`(run_train_v6.py DATASETS sha). test_v5_inputs.jsonl·test_v5_manifest.json(`57fd384f…`)은 data_v5 바이트 동일 사본이며 해시 목록 밖, TESTV5 게이트로 별도 검증.
- **max_seq_len 4096 → 6144(A안 승인 2026-11-04, 학습·추론 동일)** — v5 대비 유일한 하이퍼파라미터 변경, 사유: v3.1 시스템 프롬프트 +1,099 토큰으로 SFT train 1125/1274·val 157/179·test_v5 oas_code 입력 282/283이 4096 초과(최대 5,184·5,150), 6144 초과 0건. 그 외 LoRA r16·α16·3 epoch·lr 2e-4·batch 2×4·cosine·adamw_8bit·seed 42·43·44 동일, max_new_tokens 256 → 512. **배포 시 시스템 프롬프트 KV 캐시 확인 필요(S5 채택 시 GGUF 변환 단계; 프롬프트 3,798 토큰).**
- 손실 마스킹: v5는 run_train.py 119행 `train_on_responses_only(instruction_part='<|im_start|>user\n', response_part='<|im_start|>assistant\n')`로 completion-only(assistant 토큰만 손실)였고(LoRA v2 노트북 build_notebook_v2.py 108행 동일; run.log에는 문구 없음, 코드 줄이 근거), v6a(run_train_v6.py)도 같은 호출을 쓰며 학습 시작 시 0번 행의 마스킹 비율을 로그에 남긴다.
- 실행: training/lora/runpod/{run_train_v6.py, run_v6.sh, README_v6a.md}. 번들 export/blade_v6a_20261104.tgz SHA-256 `91c0c2049b75301a8ae9f3f6945fea40a69243e0f7e54c4b7ad2c0a11e651f1c`(data_v6a 7파일 + runpod 4파일 + SHA256SUMS_bundle; 데이터는 바이트 동일, 스크립트 LF). 순서 해시 → setup.sh → preflight(generate output_scores·label 토큰 검사) → seed 42 → 43 → 44(학습 체크포인트·예측 행 단위 resume, seed마다 results·adapter tar) → 전체 tar → Pod 자동 정지. seed 실패 시 다음 seed로 가지 않고 STOP. 예측 파일 이름은 v5 규약 그대로이며 행에 label_prob·prompt_tokens·output_tokens 추가.
- confidence: 판정·문턱·곡선에는 label 토큰 확률 `p_norm`(구별 가능한 최소 접두 토큰 확률의 곱을 7종 후보 질량으로 정규화; owner_match·owner_or_admin은 첫 토큰 `owner`가 같아 2토큰 접두 `owner`+`_match`/`owner`+`_or`, 나머지 5종은 첫 토큰 1개)을 쓴다. generate(output_scores)에서 추출, 추가 forward 없음. p_first·p_prefix·p_seq·candidates·생성 confidence 필드는 기록만. 상세 reports/eval/lora_v6a/data_prep.md 4절.
- 판정셋 test_v5 283(dev) + 회귀 test_v30 207. 채택 기준(3 seed 평균): (1) test_v5 macro-F1 ≥ v5 + 0.016, (2) test_v30 207 구체 정밀도 하락 ≤ 0.025, (3) test_v30 207 public 오판 평균 ≤ 2.0(v3.1 안전 가드). 채점기는 prediction["label"]만 읽어 키 순서 무관(282/282 재파싱 확인).
- 순서: 1 데이터 준비(완료, 보고 후 정지) → 2 학습·평가(승인 후 RunPod, seed 단위 저장·회수·--resume, s42 먼저 → 보고 없이 43·44) → 3 보고 reports/eval/lora_v6a/report.md(v5 병기, S1-3 불일치 유형별 예측 변화, p_norm 문턱 0.5~0.99 정확도–보류율 곡선, 출력 오류·평균 출력 길이·추론 시간).
- **S5 결과(2026-11-04, H100 Pod y3fn8g1psetyh8, 23:21–01:33 UTC, 3 seed 480 step 완주, 해시 게이트 통과, 자동 정지) — 사전 기준 3개 모두 미달, 불채택**: test_v5 oas_code macro-F1 v5 0.683 ± 0.016 → v6a 0.549 ± 0.008(−0.134; 기준 ≥ +0.016), test_v30 207 구체 정밀도 0.796 → 0.607(−0.188; 기준 하락 ≤ 0.025), public 오판(/35) 3/2/1 → 5/7/3 평균 5.0(기준 ≤ 2.0). test_v5 manual 16.6% → 31.4 ± 8.6%(s44 117건), membership F1 0.589 → 0.243, owner_or_admin 0.536 → 0.345, seed 간 갈린 레코드 69 → 143. test_v30은 반대로 manual 28% → 6.6%로 줄며 정밀도 하락. label 토큰 확률 p_norm은 근거 먼저 출력에서 거의 전 건 1.0(0.99 미만 0·1·0건)이라 곡선이 평탄해 보류 조절에 쓸 수 없다(불확실성은 rationale 안 label 첫 등장 위치에 있으며 저장하지 않음). 출력 오류는 test_v30에서 seed당 4~9건(중국어 혼입). 해석: v3.1 정의를 프롬프트에만 넣고 학습 target(v3.0.1 기준 rationale)은 그대로 둬 기준 불일치; 프롬프트 효과와 출력 순서 효과는 분리되지 않음. 산출 reports/eval/lora_v6a/{report.md, analysis.json, scores_test_v5.json, scores_test_v30.json, eval_*.md, lora_v6a_s4*/, run_v6.log, SHA256SUMS_blade_v6a}(scripts/analyze_lora_v6a.py). 어댑터 tar는 git 밖(로컬 BLADE_lora_v6a_export.zip `78f3f7db…`). 주지표·발표 수치(v5) 불변, test_v6 추론 없음, 커밋 없음. v3.1 반영을 계속하려면 학습 target 재작성이 선행돼야 하며 별도 승인 대상.

## 작업 S8: 베이스 모델만 14B로 교체 (v6c, 2026-11-04 1단계 준비 — 학습 전 정지, 커밋 금지, 마감 2026-11-11)

- 변경은 베이스 모델 하나뿐: `unsloth/Qwen2.5-7B-Instruct-bnb-4bit` → `unsloth/Qwen2.5-14B-Instruct-bnb-4bit`(Apache-2.0, 9.27 GB). 데이터 data-v5 train/val(data_v6a 아님), 프롬프트 v3.0.1, 출력 순서 v5와 동일(label 먼저), max_seq_len 4096, max_new_tokens 256, LoRA r16·α16·3 epoch·lr 2e-4·cosine·adamw_8bit, seed 42/43/44, 유효 배치 2×4=8(메모리 추정 20~30 GB라 조정 불필요; 조정 시 기록). 문맥 블록·label 토큰 확률 없음. test_v6 추론 금지.
- 후보 비교(reports/eval/lora_v6c/prep.md 1절): Qwen3-14B(hybrid thinking 템플릿, `<think>`·added tokens 26, tokenizer.json 다름)와 Qwen3.5/3.6(14B 없음: 9B·27B·35B-A3B, 멀티모달 아키텍처·thinking 템플릿)은 템플릿이 달라 규칙대로 제외. Qwen3-14B-2507은 존재하지 않음. Qwen2.5-Coder-14B-Instruct는 단일 변수 비교를 흐려 보류. 14B 토크나이저·chat_template은 7B와 바이트 동일(tokenizer.json SHA `9c5ae00e…`).
- 토큰 재계산(14B 토크나이저, prep_tokens.json): train 1274 최대 4085·val 179 최대 4015·test_v30·test_v5 입력 모두 4096 초과 0, 7B 계산과 전 행 동일. completion-only 마스킹은 v5와 같은 train_on_responses_only 호출(템플릿 동일, 경계 문자열 그대로).
- H100 추정: 학습 50~65분/seed, 평가 15분(+supp 6분), 3 seed 3.5~4.5시간 + 설치. 배포 영향: GGUF Q4_K_M ≈ 8.4 GiB(v5 4.36 GiB), Pod 병합 fp32 RAM ≈ 59 GB·디스크 ≈ 60 GB, 로컬 PC(GPU 없음, RAM 31.8 GB, C: 여유 17.2 GB)에서 CPU 추론 정책당 ≈ 140~160 s(v5 72.8 s); 프록시 요청 지연은 영향 없음. 현재 로컬 Ollama에는 blade-qwen-lora-v5만 있고 v4·qwen2.5:7b가 없음(확인 필요).
- 2단계 계획(승인 대기): run_train_v6c.py = run_train.py에서 base_model만 교체, run 이름 lora_v6c_s{seed}, 평가 test_v30·test_v5·test_v31_supp 3 seed 기본 디코딩, base 14B zero-shot 1회는 선택. 채택 기준 제안(사용자 확인 필요): S5와 같은 3조건 — test_v5 oas_code macro-F1 ≥ v5 + 0.016, test_v30 207 구체 정밀도 하락 ≤ 0.025, public 오판(/35) 평균 ≤ 2.0. 3단계 보고 reports/eval/lora_v6c/report.md.
- **1단계 승인·2단계 사전 기록(2026-11-04 사용자 결정, 학습 전 기록)**: 베이스 `unsloth/Qwen2.5-14B-Instruct-bnb-4bit` 확정. **조기 판정**: s42 test_v5 oas_code macro-F1 ≤ 0.6661(v5 s42, reports/eval/lora_v5/scores_test_v5.json; 번들 baseline/ 파일을 같은 채점기로 재채점해 확인)이면 s43·s44·base zero-shot 미실행, 불채택, Pod 정지(runpod/early_gate_v6c.py, 정의 scripts/eval_combined_v5.py). **채택 기준**: S5와 같은 3조건(3 seed 평균) — (1) test_v5 oas_code macro-F1 ≥ v5 + 0.016(v5 0.683 ± 0.016), (2) test_v30 207 구체 정밀도 하락 ≤ 0.025(v5 0.796), (3) test_v30 207 public 오판(/35) 평균 ≤ 2.0. **불채택이면 v5를 최종 모델로 확정(S9 대상)**. 평가: test_v30 + test_v5 + test_v31_supp(oas·oas_code), 3 seed, 기본 디코딩; base 14B zero-shot은 조기 판정 통과 시에만 s44 뒤 마지막에 1회(판정에 쓰지 않음). 실행 순서(runpod/run_v6c.sh): 해시 → setup → preflight(14B 로드·generate·메모리) → s42 학습·평가(6작업) → pack → 조기 판정 기록(early_gate.json) → (통과 시) s43 → s44 → base zero-shot → 전체 tar → 자동 정지. seed별 pack·RETRIEVE_CMD 회수, 학습 체크포인트·예측 행 단위 resume. 로컬 Ollama v4·qwen2.5:7b 부재는 prep.md에 사실만 기록(복구는 S9 이후 배포 정리 때). 14B 채택 시 GGUF 병합 Pod 요건(RAM ≥ 80 GB, 컨테이너 디스크 ≥ 120 GB)을 보고서에 기록. 번들 export/blade_v6c_20261104.tgz SHA-256 `7ff028004fc43b242ea6d72409bcf0b220c3ba00c5d43f2021c0631e577a8b16`(data_v5 8파일 바이트 동일 + runpod 5파일 LF + baseline v5 s42 test_v5 oas_code 예측 + SHA256SUMS_bundle). 전 결과 회수 후 3단계 보고(reports/eval/lora_v6c/report.md, v5 병기, 같은 채점기) 후 정지. 커밋 금지.

- **S8 결과(2026-11-05, RunPod zra2rcdj6gbixh A100 80GB PCIe — H100 아님, 11-04 14:49 → 11-05 00:32 UTC 9시간 43분, 3 seed 480 step 완주, 해시 게이트 통과, 자동 정지) — 기준 (1) 미달, 불채택 → v5 최종 확정(S9 대상)**: 조기 판정 s42 test_v5 oas_code macro-F1 0.686 > 0.666 PASS. 3 seed 평균 test_v5 macro-F1 v5 0.683 ± 0.016 → v6c 0.680 ± 0.015(−0.003; 기준 ≥ +0.016; 같은 seed 차이 +0.020/+0.007/−0.036), test_v30 207 구체 정밀도 0.796 → 0.813(충족), public 오판(/35) 3/2/1 → 2/2/1 평균 1.67(충족). 정확도 0.691 → 0.710, manual 16.6% → 14.3%, 출력 오류 18작업 합 15 → 7, test_v31_supp macro-F1 0.485 → 0.531 ± 0.059(보조, sd 커서 차이 불인정)는 나아졌으나 판정 label membership 0.589 → 0.595·owner_or_admin 0.536 → 0.539 제자리, owner_match 0.760 → 0.711·manual 0.499 → 0.474 하락. v5·v6c 여섯 run 모두 틀린 레코드 39/283(manual 23, Rocket.Chat 23). base 14B zero-shot test_v5 macro-F1 0.504(7B 0.238). 학습 132분/seed(피크 11.7 GiB, batch 2×4 유지, padding-free 자동 활성은 v5 로그에도 있음), 추론 행당 1.55~1.84 s(7B 2배). 1단계 시간 추정(H100 50~65분)은 A100 PCIe 배정으로 빗나감. 산출 reports/eval/lora_v6c/{report.md, analysis.json, scores_test_v5.json, scores_test_v30.json, scores_supp.json, eval_*.md, lora_v6c_s4*/, base_qwen14b_runpod/, run_v6c.log, SHA256SUMS_blade_v6c}(scripts/analyze_lora_v6c.py). 어댑터 tar 3개는 git 밖(로컬 BLADE_lora_v6c_export.zip `97cd45dd…`). GGUF·배포 전환 없음, 주지표·발표 수치(v5) 불변, test_v6 추론 없음, 커밋 없음. 작업 C′의 베이스는 7B(v5)로 확정.

## 작업 C′: v5 설정 + 학습 정답만 교정 (v6d, 2026-11-05 사전 기록 — C0 설계 대체, 학습·추론·커밋 금지)

- C0 결과(reports/data_v6d/c0_impact.md): data-v5 SFT 1,453행 중 v3.1 기준 label 변경 후보 94건(변경 예상 33 + 판정 필요 61, 6.5%)뿐. 가장 큰 묶음은 gitea reqOrgOwnership 23건(LLM owner_match → G3-a role_required). test_v30·test_v31_supp·test_v5·test_v6 후보와 겹침 0.
- **설계 변경(사용자 결정 2026-11-05)**: C0 보고서의 "S5(v6a) 설정 위에서 정답만 교정" 설계를 폐기하고 **C′ = v5 설정 그대로 + 학습 정답만 교정**으로 한다. 근거: label 변경 후보가 6.5%뿐이라 S5 하락(test_v5 macro-F1 −0.134)은 정답 불일치보다 프롬프트·출력 순서·길이·배치 변경의 영향이 클 가능성이 있고, S5 설정 위에서 하면 그 하락을 그대로 안는다.
- 고정: 프롬프트 v3.0.1(`d0913c27…`), label 먼저 출력, max_seq_len 4096, max_new_tokens 256, LoRA r16·α16·3 epoch·lr 2e-4·batch 2×4·cosine·adamw_8bit·seed 42/43/44 — v5와 동일. 베이스는 S8 채택이면 `unsloth/Qwen2.5-14B-Instruct-bnb-4bit`, 아니면 7B.
- 변경: C1 재판정 결과 label + 해당 행 rationale만. user 입력은 data-v5 SFT와 바이트 동일(빌드 assert). C2 출발점은 SFT assistant rationale(processed rationale과 21건 다름). 재작성 rationale은 기존 정합성 규칙(구체 label에 보류 표현 0, 검수 메타 문구 0, 규칙 ID·파일 경로 0) assert.
- 비교: C′ vs v5(단일 변수 = 학습 정답). 채택 기준(3 seed 평균, 기존 3조건): (1) test_v5 oas_code macro-F1 ≥ v5 + 0.016(v5 0.683 ± 0.016), (2) test_v30 207 구체 정밀도 하락 ≤ 0.025(v5 0.796), (3) test_v30 207 public 오판(/35) 평균 ≤ 2.0. test_v6 추론 금지.
- 검수: review/c1_relabel_review.xlsx(scripts/build_c1_review_sheet.py, seed 42, 시트 5개 — 안내·검수 규약 / 무작위5%_블라인드 68 / 판정필요_코드 39 / 판정필요_OAS문구 22 / 변경예상_C2 46 = 결정적 초안 32 + review 1 + C2 전용 13; 검수자 A/B/C 균등, 블라인드 시트 먼저). 결정적 32건 기계 초안 reports/data_v6d/c1_draft_deterministic.jsonl, 블라인드 정답키 c1_audit_key.json(시트 밖). **사전 기록: 5% 감사 불일치율 > 5%면 한계로 기록하고 전수 검수는 마감 후.** 기존 검수 행(28건)은 기존 label 유지가 기본값.
- 중단 규칙: 2026-11-08 12:00 KST까지 결과 없거나 기준 미달이면 C′ 중단(v5 유지, S8 결과는 별도). 정지 지점: C1 시트 생성 후(현재) → 검수 완료본 반영·C2 후 data-v6d 동결 전 → 학습 전.


## S8 결과·data-v6d 동결 (2026-11-05, 커밋 금지 — 학습 전 정지)

- **S8(v6c, 14B) 불채택**: 3 seed test_v5 oas_code macro-F1 v5 0.683 ± 0.016 → v6c 0.680 ± 0.015(-0.003, 기준 ≥ +0.016 미달), test_v30 207 구체 정밀도 0.796 → 0.813(충족), public 오판 2.00 → 1.67(충족). 조기 판정은 통과(s42 0.686). 사전 기록대로 **v5가 최종 모델(S9 대상)**, C′ 베이스는 7B. 보고 reports/eval/lora_v6c/report.md(+analysis.json, scores_*.json; scripts/analyze_lora_v6c.py). 어댑터 tar는 git 밖(BLADE_lora_v6c_export.zip).
- **C1 반영**: 검수 완료본 review/c1_relabel_review_reviewed.xlsx(`d9f8299f…`, 검수자 Claude(AI)). label 변경 36(train 36·val 6 행 중) + rationale 교체 42; 전부 gitea(owner_match->role_required 23, manual_review_required->role_required 5, membership_required->manual_review_required 2, manual_review_required->owner_match 2, manual_review_required->owner_or_admin 1, owner_match->manual_review_required 1, role_required->public 1, membership_required->owner_match 1). 결정적 초안 32 중 31 수용·1 거부(GET /user/hooks/{id} owner_match 유지). 기존 사람 검수 행 변경 1건(GET /teams/{id}/repos membership → manual, G6-a 가시성 분기). OAS-only는 현행 유지(사용자 결정), AI 의견 manual 21건은 reports/data_v6d/oas_relabel_candidates_post_deadline.jsonl(마감 후 APIs.guru OAS 일괄 점검 후보). 합성 tenant AND membership 3건 영어 rationale 유지. 확정 rationale의 파일 경로 참조 4건 제거. 블라인드 시트 판정은 미반영.
- **블라인드 감사 불일치율 41.2%(28/68; 코드 행 25.5% 12/47, OAS-only 76.2% 16/21; 24건이 → manual) → 사전 기록대로 한계로 기록, 전수 검수는 마감(2026-11-08 12:00 KST) 후.** reports/data_v6d/c1_blind_audit.json.

## data-v6d 동결 (2026-11-05)

데이터셋 버전 **data-v6d** = data-v5 SFT 행 + C1 확정 label 36 + C2 rationale 42(user 입력·순서·나머지 행 바이트 동일). 평가 test_v30(eval-def v2, 주지표 불변) + test_v31_supp + test_v5(dev). 프롬프트 v3.0.1 고정. 아래 파일은 이후 수정·재생성 금지(git 커밋·태그는 사용자 승인 후). NodeBB 코드 본문이 든 파일·Flowise supp 사본·검수 xlsx·번들은 .gitignore.

| 파일 | 건수 | SHA-256 |
|---|---:|---|
| datasets/blade/processed/train_v6d.jsonl | 1277 | `aed2b275a76fa684e426a656fb04b1c934a29bc987f45a146fe1c244ced4d372` |
| datasets/blade/processed/val_v6d.jsonl | 180 | `159e01780eb2d8aa1710146d2c06533c20c81920a828a60b889ec6db221361cf` |
| training/lora/data_v6d/train_sft_v6d.jsonl | 1274 | `63c1768949a0e8c7f0747712c6a55e4fb492e1d03baeddfa111884f31ff65b98` |
| training/lora/data_v6d/val_sft_v6d.jsonl | 179 | `1a421c836032ff3c611f3a74380b519374393deb44519c1772db8049d7d671ee` |
| training/lora/data_v6d/data_v6d_hashes.json | - | `82efda868e7bde511d0838e10bf0e8a5cc3e6aae577c68b15fcbf370a9d94b53` |
| reports/data_v6d/c1_changes.jsonl | 42 | `6258a226a04fa03cbfbe2248ce6a2cec73109d52c20966256db118f9ec5442a4` |
| reports/data_v6d/c1_blind_audit.json | - | `882fcb5a9af3a2b0097bc6ef7ab6ac4def052dbf02dd52e679c710759a393006` |
| reports/data_v6d/oas_relabel_candidates_post_deadline.jsonl | 21 | `bac1d5260a86489e4040fb90121349933cf83bf7d331ac936a27880bc685a8c9` |
| review/c1_relabel_review_reviewed.xlsx | 175행 | `d9f8299ff4a514b409e799515ad5e538c1d3810fba2c0ad8d3a492ad5377136e` |
| training/lora/data_v6d/test_v30_inputs.jsonl · test_v31_supp_inputs.jsonl · test_v5_inputs.jsonl · test_v5_manifest.json · policy_label_v3.0.1.md | 269 · 222 · 283 · - · - | data_v5와 바이트 동일(`d65f25b9…`, `97e618e7…`, `9103cd3d…`, `57fd384f…`, `d0913c27…`) |

- 정합성(빌드 assert, scripts/build_data_v6d.py): 구체 label 보류 표현 0, 검수 메타 문구 0, 규칙 ID·파일 경로 0, 토큰 최대 4085(4096 초과 0; tokenizers + chat template 수동 계산, data_v6a 계산치 1,453/1,453 일치로 검증). SFT manual 비율 train 12.6%, val 21.8%. Errata: data-v5 SFT tokens 필드는 gitea 69행에서 최대 24 어긋남(학습 무관).
- C′ 학습 번들 export/blade_v6d_20261105.tgz SHA-256 `3c52b2cd300ce33fa1c7b7ef72de70de278d397490a7f54dd7eb7aa3add4657b`(data_v6d 8파일 + runpod/run_train_v6d.py·run_v6d.sh·setup.sh·README_v6d.md LF + SHA256SUMS_bundle). run_train_v6d.py = run_train_v6c.py에서 베이스 7B·데이터 data_v6d(해시 게이트 `746926bc…`)만 변경, 조기 판정 없음, 순서 해시 → setup → preflight → s42 → s43 → s44 → tar → Pod 정지. 평가 test_v30·test_v31_supp·test_v5 × oas·oas_code, 기본 디코딩. 채택 기준은 "작업 C′" 절의 3조건(3 seed 평균). **학습은 사용자 승인 후 실행하며 아직 실행하지 않았다.** 상세 reports/data_v6d/stop_c1_c2_data_v6d.md, freeze_report.json.
- **C′ 결과(학습 2026-11-05 07:18–09:14 UTC, RunPod H100 80GB, unsloth 2026.11.2, 3 seed 480 step 완주, 해시 게이트 data_v6d `82efda86…`·test_v5 manifest `57fd384f…`·프롬프트 통과, 자동 정지; 채점 2026-11-07) — 기준 (1) 미달, 불채택 → v5 유지(최종 모델, S9 대상)**: 3 seed 평균 test_v5 oas_code macro-F1 v5 0.683 ± 0.016 → v6d 0.694 ± 0.038(+0.011; 기준 ≥ +0.016; seed별 0.687/0.735/0.661, 같은 seed 차이 +0.021/+0.051/−0.038 — s43 하나가 끌어올림, v6d sd가 v5의 2배), test_v30 207 구체 정밀도 0.796 → 0.795(충족), public 오판(/35) 3/2/1 → 3/2/1 평균 2.0(충족). test_v5 정확도 0.691 → 0.697, manual 46/43/52 → 44/65/69건(16.6% → 21.0%), seed 간 갈린 레코드 69 → 74, 여섯 run 모두 틀린 레코드 43/283. label F1: manual 0.499 → 0.541·owner_or_admin 0.536 → 0.562 상승, role 0.818 → 0.808·membership 0.589 → 0.587 제자리. S1-3 G3-a(그룹 안 역할) 5건은 7/15 → 4/15로 하락 — gitea 교정(owner→role 23건)이 Rocket.Chat 같은 패턴으로 전이되지 않고 manual로 감. supp macro-F1 0.485 → 0.487. 출력 오류 18작업 합 25 → 23(s42 test_v30 oas 8·oas_code 6, 중국어 혼입). 학습 24.6분/seed(피크 7.35 GiB), 손실 마스킹 v5와 동일(2857/2950). 해석: 학습 라벨 36건(2.8%) 교정의 효과 크기는 seed 잡음보다 작다. data-v6d 동결본은 보존(마감 후 OAS-only 390행·블라인드 불일치 28건 사람 전수 검수와 합쳐 재사용). 산출 reports/eval/lora_v6d/{report.md, analysis.json, scores_test_v5.json, scores_test_v30.json, scores_supp.json, eval_*.md, lora_v6d_s4*/, run_v6d.log, SHA256SUMS_blade_v6d}(scripts/analyze_lora_v6d.py), supp 예측은 .gitignore. 어댑터 tar 3개는 git 밖(로컬 BLADE_lora_v6d_export.zip `a9b587c0…`). GGUF·배포 전환 없음, 주지표·발표 수치(v5) 불변, test_v6 추론 없음, 커밋 없음.

## 작업 data-v7: 학습셋 LLM 라벨 615건 전면 재판정 (2026-11-07 사전 기록 — 재판정 시작 전, 커밋 금지, 2번 보고 후 정지)

- 학습 설정은 v5와 동일(프롬프트 v3.0.1, label 먼저, max_seq_len 4096·max_new_tokens 256, LoRA r16·α16·3 epoch·lr 2e-4·batch 2×4·cosine·adamw_8bit, seed 42/43/44, 베이스 7B). 변경은 라벨 출처가 LLM(gpt-4o-mini, v3.0.1; processed meta.label_source == model_api)인 615행(gitea 코드 225 + APIs.guru OAS-only 390 = train 535·val 80)의 label·rationale만. user 입력은 바이트 동일(빌드 assert). 출발점 data-v6d(C′ 교정 36건 포함, 동결 해시 불변).
- 판정 기준: G1~G8(data-v4 검수 규약) + v3.1 정의(reports/eval/human_agreement_v5/label_defs_v3.1_draft.md) + test_v6 보충 규약 + 정지 지점 결정(작업 C 정지 지점 1·3, test_v31_supp 규약) — test_v5·test_v6 정답과 같은 기준. OAS-only 행은 보류 2를 적용한다(설명문에 접근 조건이 명시되지 않으면 manual; security 선언·mutation 제한은 OAS-only에서 유지). C′ 블라인드 불일치 28건 중 규칙 라벨러 행도 같이 재판정한다(집계는 615와 분리).
- 1단계 재판정: AI(Claude 서브에이전트, 프로젝트·서비스별 청크 병렬)가 입력(SFT user 필드 = 모델이 보는 코드/OAS)만 보고 label·근거(입력 문자열 인용)·확신도를 낸다. 현재 label·rationale은 입력 파일에 넣지 않고 별도 키 파일(datasets/blade/processed/data_v7/rejudge/current_labels_key.json)에 두어 집계 단계에서만 읽는다. 판정 안내문 data_v7/rejudge/REJUDGE_GUIDE.md(위 기준 원문 발췌), 입력 data_v7/rejudge/inputs/*.jsonl, 출력 data_v7/rejudge/out/*.jsonl. LLM API 호출 없음, 모델 학습·추론 없음, test_v6 추론 없음.
- 2단계 집계 후 정지·보고: 변경 건수, 현재→새 label 전이표, 프로젝트별·코드/OAS 분리, 학습셋 전체(SFT 1453행) label 분포 변화, manual 비율(**20% 초과 시 경고**), 확신도 분포. 보고 reports/data_v7/stop2_rejudge_report.md.
- 3단계(승인 후): 사람 확인 시트 = manual로 바뀐 행 전부 + 그 외 변경 행 30% + 안 바뀐 행 10% 블라인드(seed 42) → 바뀐 행 rationale 재작성(SFT 형식, 입력에 있는 근거만, 규칙 ID·경로·메타 문구 금지) → 정합성 assert(구체 label 보류 표현 0, 메타 문구 0, 규칙 ID·경로 0, 4096 초과 0, user 바이트 동일) → data-v7 동결 → 학습 번들.
- 비교: data-v7 vs v5(단일 변수 = 학습 정답). 채택 기준(3 seed 평균, 기존 3조건): (1) test_v5 oas_code macro-F1 ≥ v5 + 0.016(v5 0.683 ± 0.016), (2) test_v30 207 구체 정밀도 하락 ≤ 0.025(v5 0.796), (3) test_v30 207 public 오판(/35) 평균 ≤ 2.0. **중단 규칙 갱신(사용자 결정 2026-11-07): 2026-11-09 18:00 KST까지 채점 결과가 없거나 기준 미달이면 v5 유지**(기존 C′ 11-08 12:00 규칙 대체).
- **2단계 집계 결과(2026-11-07, 정지 지점 — 사용자 승인 대기)**: 재판정 19청크(Claude 서브에이전트, 안내문 REJUDGE_GUIDE.md SHA `d734ce9a…`, 입력·출력 해시 stop2_rejudge.json). 615행 중 label 변경 **301(48.9%)**: gitea 코드 21/225(9.3%; →manual 13, manual→구체 6, own+adm→owner 2), OAS-only 280/390(71.8%; →manual 256, 그중 보류2 232). 전이 상위 owner→manual 116·role→manual 89·tenant→manual 29·member→manual 16·public→manual 16. 확신도 0.9 310·0.7 288·0.5 17(변경 행 0.9 106·0.7 179·0.5 16). 학습셋 manual 비율 train 12.6% → **31.9% (20% 초과 경고)**, val 21.8% → 31.3%. C′ 블라인드 불일치 중 규칙 라벨러 행 10건은 별도 집계(변경 5, →manual 4; 자동 반영 없음). 선택지 계산(stop2_options.json): A 전부 반영 31.9% / B OAS 새 manual 256행 제외 16.4% / C OAS manual 299행 전부 제외 13.9% / D 25% 쿼터(train 구체 868 → manual 289). 보고 reports/data_v7/stop2_rejudge_report.md(+stop2_rejudge.json, rejudge_changes.jsonl), 빌드·집계 scripts/build_data_v7_rejudge.py. 3단계(사람 확인 시트·rationale 재작성·동결)는 승인 전 미착수. 커밋 없음.
- **2단계 확인·결정(사용자 2026-11-07) — 사전 기록 변경(학습 전)**: (1) 구성 **B안 + 기존 평가셋 2개 학습 투입** — 615행 재판정 반영, 단 OAS-only에서 새로 manual이 된 256행(train 236 + val 20)은 학습 제외·pool 보존; test_v31_supp 222 + test_v5 283을 train에 추가(확정 정답, 제외 목록 제외); test_v30은 학습에 넣지 않음(회귀·안전 지표); val은 data-v6d val에 재판정 반영분만 적용. (2) 추가 행 SFT: user = 각 셋의 oas_code 입력 그대로, assistant = 확정 label + 검수 근거 기반 템플릿 rationale(입력에 있는 식별자·코드 인용만, 규칙 ID·경로·메타 금지), 4096 초과 행 제외·건수 보고. (3) **판정셋 test_v6**(사람 확인 후 동결), v5 3 seed vs data-v7 3 seed를 1회 동시 평가. **채택 기준**: (1) test_v6 macro-F1 ≥ v5 + 0.016(3 seed 평균), (2) test_v30 207 구체 정밀도 하락 ≤ 0.025, (3) test_v30 207 public 오판 평균 ≤ 2.0. **test_v5·test_v31_supp는 학습에 투입되었으므로 data-v7 평가에 쓰지 않는다**(run_train_v7.py·run_v7.sh가 해당 입력 존재를 거부). 중단 규칙 2026-11-09 18:00 KST. (4) 사람 확인 시트: 학습에 들어가는 변경 행 전부(gitea 21 + OAS 비-manual 변경 24) + 안 바뀐 행 10% 블라인드 + 추가 505행 rationale 10% 표본. (5) 집계 보고 후 정지.

## data-v7 동결 (2026-11-07, 학습 전 정지 — 커밋 금지)

데이터셋 버전 **data-v7** = data-v6d SFT 행(615 LLM 라벨 행 재판정 반영: label 변경 45 적용, OAS-only 새 manual 256행 제외) + test_v31_supp 221 + test_v5 281(4096 초과 3건 제외: v4t-chatwoot-03a9708adc·v5t-rocketchat-2b42fcece3·v5t-rocketchat-a41ec34093). train 1540(manual 17.1%) / val 159(manual 22.6%). 평가 test_v30(eval-def v2, 주지표 불변) + test_v6(S9, 동결 후). 프롬프트 v3.0.1 고정. 아래 파일은 이후 수정·재생성 금지(git 커밋은 사용자 승인 후; NodeBB·Flowise 코드가 든 파일·xlsx·번들은 .gitignore).

| 파일 | 건수 | SHA-256 |
|---|---:|---|
| datasets/blade/processed/train_v7.jsonl | 1540 | `662b16405d5775c0ecfceb8361c53953751b554390c5f1f63e30bfdfbffa32db` |
| datasets/blade/processed/val_v7.jsonl | 159 | `cf04b4b3b8928985377a53a69905d0e1a343f705850e8694bc3f38286b9da325` |
| training/lora/data_v7/train_sft_v7.jsonl | 1540 | `6654f79afb8cc984b42944cf3b246111c06d7704b02809577fa85cd5630b6178` |
| training/lora/data_v7/val_sft_v7.jsonl | 159 | `2173171ed412b2b3949c1d21f29fec69bcdd5b7e4732e67ace4fb84bc2e57087` |
| training/lora/data_v7/data_v7_hashes.json | - | `bd33f1bcf0f68ab5fe5b96195c0da3cf6affbb3486fb85bef542b3f77e88ba73` |
| datasets/blade/processed/data_v7/train_v7_oas_manual_pool.jsonl | 256 | `7e663b76526b3cbba1d36e2b03c84069bec72e037353e66c863ee2b2dd745688` |
| reports/data_v7/v7_changes.jsonl | 45 | `4be15fad7791fbe494f0647faad116ce94cbe732312de0522279555bc890ee05` |
| reports/data_v7/added_rows_rationale.jsonl | 505 | `dfd296d42b7fce0c3f97ea4004f519710154c45f0bc12d41d2671afd72eb9b33` |
| review/data_v7_human_check.xlsx | - | `b6a3d484abe700d62cdb59061effeea79c81b9d040b02fded6dd30f21508ac99` |
| training/lora/data_v7/test_v30_inputs.jsonl · policy_label_v3.0.1.md | 269 · - | data_v5와 바이트 동일(`d65f25b9…`, `d0913c27…`) |

- 재판정 출처: data_v7/rejudge/REJUDGE_GUIDE.md `d734ce9a8852cf26…`, 판정 19파일 해시는 data_v7_hashes.json rejudge.outputs. 45건 변경 전이 {'membership_required->role_required': 5, 'role_required->owner_match': 4, 'membership_required->manual_review_required': 4, 'manual_review_required->role_required': 4, 'owner_or_admin->owner_match': 3, 'tenant_match->role_required': 3, 'owner_match->manual_review_required': 3, 'owner_or_admin->manual_review_required': 3, 'public->manual_review_required': 2, 'tenant_match->owner_match': 2, 'membership_required->tenant_match': 2, 'manual_review_required->owner_match': 2, 'membership_required->owner_match': 2, 'owner_match->tenant_match': 2, 'manual_review_required->public': 1, 'owner_match->role_required': 1, 'role_required->manual_review_required': 1, 'role_required->tenant_match': 1}; rationale은 판정 근거 인용 + 템플릿(rule_label_v5 JUDGE/TEMPLATE 문구). C′ 블라인드 불일치 중 규칙 라벨러 10행은 미반영(reports/data_v7/audit_rule_rows_not_applied.jsonl).
- 추가 행 rationale 근거: auth_summary 식별자(입력에 등장) 374 · 코드 인용(입력에 등장) 118 · 일반 문구 10. label 분포(추가 502): {'manual_review_required': 94, 'owner_or_admin': 41, 'role_required': 149, 'owner_match': 55, 'membership_required': 87, 'public': 21, 'tenant_match': 55}. 프로젝트: {'chamilo': 58, 'chatwoot': 78, 'flowise': 60, 'generic_university': 21, 'multitenant_lab': 4, 'ghost': 69, 'rocketchat': 155, 'umami': 57}.
- train label 분포 {'public': 88, 'role_required': 425, 'membership_required': 138, 'tenant_match': 111, 'owner_match': 382, 'owner_or_admin': 132, 'manual_review_required': 264}, val {'public': 14, 'role_required': 46, 'membership_required': 6, 'tenant_match': 6, 'owner_match': 38, 'owner_or_admin': 13, 'manual_review_required': 36}. train 프로젝트별 {'gitea': 197, 'rocketchat': 155, 'synthetic': 143, 'zulip': 132, 'data_v3_pairs': 108, 'taiga': 103, 'apisguru': 102, 'nodebb': 98, 'dendrite': 95, 'chatwoot': 78, 'ghost': 69, 'label_studio': 60, 'flowise': 60, 'chamilo': 58, 'umami': 57, 'generic_university': 21}. 정합성: 구체 label 보류 표현 0·메타 문구 0·규칙 ID·경로 0(전체 세트), user 바이트 동일, test_v30 겹침 0, 토큰 최대 4085.
- 사람 확인 시트 review/data_v7_human_check.xlsx(변경 45 · 블라인드 31 · 추가행 rationale 50, seed 42, 검수자 A/B/C), 정답키 reports/data_v7/human_check_key.json. 검수 결과는 data-v7 학습을 막지 않으며(마감 압축 실행) 불일치는 보고서 한계에 기록한다.
- 학습 번들 export/blade_v7_20261107.tgz SHA-256 `80fc379548d9d6d2c108c002d233495cffcf94480a99be487e3142dc1e9ff8d7`(data_v7 5파일 + runpod/run_train_v7.py·run_v7.sh·setup.sh·README_v7.md + SHA256SUMS_bundle), Pod 평가는 test_v30만. 상세 reports/data_v7/freeze_report.json, stop5_build_report.md. **학습은 사용자 승인 후 실행하며 아직 실행하지 않았다.**
- **학습 승인·S9 사전 기록(사용자 2026-11-07, 학습 시작 전)**: 학습 승인(export/blade_v7_20261107.tgz, val 159 그대로). 순서 s42 → s43 → s44, seed별 pack·회수, 완료 후 Pod 정지(terminate 아님). test_v30 결과 회수 후 v5와 나란히 보고하고 정지. (1) **S9 절차**: test_v6 동결 후 **같은 Pod·같은 라이브러리**에서 v5 어댑터 3개(s42·43·44, blade_v5_adapters.tar.gz `db6abe46…`) + v7 어댑터 3개를 test_v6 oas_code로 한 번에 추론한다(run_train_v7.py `--data v5|v7 --eval-only --jobs v6test`, TESTV6 manifest 해시 게이트; v5 어댑터를 S9 번들에 포함, README_v7.md S9 절). (2) **test_v6 동결 최소 조건**: 공개_우선확인 44건 사람 판정 완료(필수); 블라인드 감사 41건까지 완료되면 기존 규칙(불일치 ≤ 5%면 AI 확정 수용, 초과면 전수) 적용; 감사 미완료면 "AI 확정 + 사람 우선확인 44건"으로 동결하고 한계로 기록; **2026-11-09 12:00 KST까지 우선확인 44건도 미완료면 S9 미실행, v5 유지**. 커밋 금지.
- **v7 1단계 결과(학습 2026-11-07 07:37–09:22 UTC, RunPod kufx154dteqn1b H100 80GB, torch 2.14.1+cu130·transformers 5.17.0·unsloth 2026.11.3, 3 seed 579 step 완주, 해시 게이트 data_v7 `bd33f1bc…`·프롬프트 통과, auto-stop; 채점 2026-11-08) — 회귀 기준 (2)·(3) 충족, 기준 (1)은 S9(test_v6) 대기**: test_v30 207 구체 정밀도 v5 0.796 ± 0.025 → v7 0.824 ± 0.020(+0.028, 같은 seed +0.041/+0.037/+0.006; 기준 하락 ≤ 0.025 충족), public 오판(/35) 3/2/1 → 1/1/2 평균 1.33(≤ 2.0 충족). macro-F1(207) 0.374 → 0.398, 정확도 0.568 → 0.630, 구체 재현율 0.566 → 0.628, manual 28.2% → 22.9%, owner_match F1 0.752 → 0.811, seed 간 갈린 레코드 69 → 34, 출력 오류 6작업 합 15 → 12(중국어 혼입). oas(명세만) 160 macro-F1 0.739 → 0.755(보조). test_v5·test_v31_supp는 v7 학습 데이터라 채점하지 않았고 예측 파일 없음(assert). 학습 29.2분/seed(피크 7.33 GiB), 손실 마스킹 0번 행 2904/2971(행 내용 변경, 방식 동일). 산출 reports/eval/lora_v7/{report.md, analysis.json, scores_test_v30.json, eval_v30.md, lora_v7_s4*/, run_v7.log, SHA256SUMS_blade_v7}(scripts/analyze_lora_v7.py). 어댑터 tar 3개(`9dc03740…`, `850793b2…`, `63d842ed…`)는 git 밖(로컬 BLADE_lora_v7_export.zip `283d2349…`), S9에 사용. Pod는 정지 상태(S9 같은 Pod). 채택 판정은 S9 후. 사람 확인 시트(review/data_v7_human_check.xlsx) 미회수. 주지표·발표 수치(v5) 불변, test_v6 추론 없음, 커밋 없음.

## test_v6 동결 방식 변경 — A안: AI 이중 검수 + 경계 사례만 사람 확정 (2026-11-08 사용자 결정, S9 실행 전·test_v6 예측 미열람 상태에서 사전 기록)

- 사유: 마감 일정상 302건 전체 사람 검수 불가. 기존 사전 기록(공개_우선확인 44건 사람 판정 필수, 블라인드 감사 41건 ≤ 5% 규칙)을 아래로 대체한다.
- 정답 출처(레코드별 meta.label_status에 기록, DATA_CARD·보고서·발표에 명시): (a) `human_confirmed` — 우선확인 44건 중 AI 확정 ≠ Claude 2차 의견 3건(penpot-0366cd50c0, redash-e8133c143b, seahub-5569330cd5) + 저확신 1건(redash-c89e256edf) + 블라인드 감사 41건 중 Claude 판정 ≠ AI 확정 건: 사용자가 '사람 판정 label' 열에 채운 값으로 확정. (b) `ai_double_confirmed` — 우선확인 44건 중 AI 확정 = Claude 의견 40건, 감사 41건 중 Claude 판정 = AI 확정 건. (c) `ai_single` — 나머지(258 − 41 = 217건): AI 1차 확정만(review/test_v6_review_reviewed.xlsx, 2026-11-04). 2차 검수 Claude는 1차 확정·근거를 보지 않은 독립 판정(감사 41건은 블라인드 시트, 우선확인 44건은 AI 확정 열이 보이는 상태에서의 동의 여부 — 시트 'Claude AI동의' 열).
- 절차: 1 감사 41건 Claude 판정 vs human_check_audit_key.json 일치율·불일치 목록 보고(scripts/apply_test_v6_human_check.py audit) → 2 우선확인 44건 반영 → 3 감사 불일치 건 사용자 판정 반영 → 4 동결(build_test_v6.py freeze --sheet review/test_v6_review_final.xlsx, 정답 출처 열 → meta.label_status) → 해시·제외율 보고 → S9 번들(v5 3 + v7 3, 같은 Pod·환경) 생성 후 정지. 커밋 금지.
- 입력 파일: review/test_v6_human_check_우선확인_사람판정.xlsx(사용자 전달 2026-11-08, Claude 의견 열 + 사람 판정 열 포함), 감사 41건 Claude 판정 파일(전달 대기). 기존 AI 확정본 test_v6_review_reviewed.xlsx는 그대로 두고 반영본은 test_v6_review_final.xlsx로 따로 쓴다.
- 한계(동결 보고·DATA_CARD 필수): 사람 확정은 경계 사례 4 + 감사 불일치 건뿐이며 나머지는 AI 판정이다. 감사 일치율은 'AI 1차 vs AI 2차' 일치율이고 사람 대비 정확도가 아니다. 기존 S0 한계 항목(tenant 37 중 Redash 26, membership 37 중 GlitchTip 27, owner_or_admin 17, Redash G1-b 경계 16 id, 익명 operation 보정 26건)은 그대로 유지한다.

## test_v6 동결 (2026-11-08, 정지 지점 3 — A안, 커밋 금지)

hold-out **test_v6** = seahub v14.0.9-server(`0841826c`, Apache-2.0) 88 · Redash v26.9.0(`42fdf9d4`, BSD-2-Clause) 72 · GlitchTip v6.2.6(`d3039088`, MIT) 70 · Penpot 2.18.5(`f4456696`, MPL-2.0) 55 = 289건, 제외 13(4.3%, G8·보충 규약 5). label: role 65 · owner 59 · manual 52 · tenant 38 · membership 37 · public 21 · owner_or_admin 17. 정답 출처(meta.label_status): human_confirmed 5 · ai_double_confirmed 67 · ai_single 217. 블라인드 감사 41건 AI 1차 vs Claude 2차 일치 38/41(92.7%, 사람 정확도 아님); 사람 판정 7건(glitchtip-196fbf241d manual 유지, penpot-30c4fcfc6a manual 유지, penpot-05b0504832 → EXCLUDE, penpot-0366cd50c0 → EXCLUDE, redash-e8133c143b → tenant_match, seahub-5569330cd5 → public, redash-c89e256edf tenant_match 유지). v5·v7 예측 생성 전 동결, 기존 셋과 (서비스, method, 정규화 path) 겹침 0. 아래 파일은 이후 수정·재생성 금지.

| 파일 | 건수 | SHA-256 |
|---|---:|---|
| datasets/blade/processed/test_v6.jsonl | 289 | `872675957276d15777acde947ab99b6e4b9112941a8bedef404ffac9e20bc765` |
| datasets/blade/processed/data_v6/test_v6_excluded.jsonl | 13 | `b66e8ac3a40a68e8252ac058bf26dc71190dcc969e150a7e6992d1e8de005136` |
| training/lora/data_v6/test_v6_inputs.jsonl | 289 | `33d1aecdbd1a685416523eddf73722e105c2c761154a6bf95403fe1431435741` |
| datasets/blade/processed/data_v6/test_v6_manifest.json | - | `a9ca4fca05ee3e59226411c08c9f102440d5f36b2d4b45dc870bd74e346f3edc` (= run_train_v7.py TESTV6 sha, run_s9.sh 게이트) |
| review/test_v6_review_final.xlsx (.gitignore) | 302행 | `0bf36fb58d9bd8d087651797f32007d6e5063f8661027a0334a6683a5d2197b0` |

- 스크립트: scripts/apply_test_v6_human_check.py(audit·apply), build_test_v6.py freeze `--sheet`/`--dry-run`/'정답 출처' 열 → meta.label_status. 보고 reports/data_v6/stop3_test_v6_freeze.md, audit41_compare.md, human_check_apply.json. DATA_CARD "test_v6" 절 추가.
- **S9 사전 기록**: 같은 Pod(kufx154dteqn1b)·같은 라이브러리에서 v5 어댑터 3개(blade_v5_adapters.tar.gz `db6abe46…`) + v7 어댑터 3개(Pod runs/lora_v7_s4*/adapter)를 test_v6 oas·oas_code로 한 번에 추론(runpod/run_s9.sh: 해시 게이트 → v5 s42·43·44 → v7 s42·43·44, 각 `--eval-only --jobs v6test`, pack, Pod 정지). 기본 디코딩. 채택 기준은 "작업 data-v7" 절 3조건(기준 (1) test_v6 oas_code macro-F1 ≥ v5 + 0.016; (2)·(3)은 1단계에서 충족). S9 보고 필수: 프로젝트별 정확도, label별 F1, G1-b 18건 집계, label_status별 정확도(human/ai_double/ai_single), public 오판(분모 declared ∧ 정답 ≠ public). 로컬 채점은 BLADE_TESTV6_STAGE=S9에서만. 마감 2026-11-09 18:00 KST, 미달·미완이면 v5 유지. 번들 export/blade_s9_test_v6_20261108.tgz SHA-256 `fa7b93f430a224fb7deb1ec9746db5e12acd15cb8ba17ea1f37045383031353b`(data_v7/test_v6_inputs.jsonl·test_v6_manifest.json + runpod/run_train_v7.py(TESTV6 기입)·run_s9.sh·README_v7.md + SHA256SUMS_s9; v5 어댑터 tar는 별도). 커밋 금지.
- **S9 결과(추론 2026-11-08 13:54–14:40 UTC, Pod n1tl7hwtpbqnew H100 80GB·볼륨 /workspace, torch 2.13.0+cu129·transformers 5.17.0·unsloth 2026.11.3 여섯 run 동일, 게이트 data_v7·test_v6 manifest `a9ca4fca…` 6 run 통과, 학습 없음, 자동 정지; 채점 2026-11-09 18:44 KST — 사전 마감 18:00 KST 이후, 추론 완료는 11-08 23:40 KST) — 사전 기준 3개 모두 충족 → LoRA v7 채택 후보(사용자 승인 대상, 승인 전까지 v5 최종)**: (1) test_v6 oas_code macro-F1 v5 0.586 ± 0.006 → v7 0.650 ± 0.016(+0.064 ≥ 0.016; 같은 seed +0.088/+0.053/+0.050, 두 모델 sd보다 큼), (2) test_v30 207 구체 정밀도 +0.028(1단계), (3) public 오판 평균 1.33(1단계). test_v6 정확도 0.606 → 0.661, 구체 정밀도·재현율 상승, manual 15.8% → 18.1%, public 오판(/265) 1/1/1 → 1/0/0, 프로젝트별 seahub 0.649 → 0.746·Redash 0.519 → 0.588·Penpot 0.539 → 0.582·GlitchTip 0.690 → 0.686, label F1 owner_or_admin 0.585 → 0.714·role 0.537 → 0.618·tenant 0.131 → 0.249·membership 0.536 → 0.568·manual 0.532 → 0.564. label_status별 정확도(v5→v7) human 0.40 → 0.53(5건)·ai_double 0.45 → 0.49·ai_single 0.66 → 0.72. Redash G1-b 18건은 두 모델 모두 0/18(tenant → role 예측). seed 간 갈린 레코드 70 → 56, 여섯 run 모두 틀린 레코드 70/289(tenant 30·manual 15·role 14). oas(명세만) 보조: macro-F1 0.319 vs 0.302, v7 public 오판 14/24/6(v5 5/7/6)·s44 출력 오류 21건(중국어 혼입) — 한계로 기록. 산출 reports/eval/lora_v7/s9/{report.md, analysis.json, scores_test_v6.json, eval_test_v6.md, lora_v5_s4*/, lora_v7_s4*/, run_s9.log, SHA256SUMS_s9}(scripts/eval_test_v6.py — testv6_guard BLADE_TESTV6_STAGE=S9 필수, analyze_s9_v7.py). 주지표·발표 수치(v5) 불변, 전환(GGUF·Ollama·환경변수·발표 표 갱신)은 사용자 승인 후 C-5 절차. 커밋 없음.
- **S9 확인·v7 채택(사용자 결정 2026-11-09)**: (a) **LoRA v7 채택 — 최종 모델은 LoRA v7(data-v7, 3 seed)**. 기록: 추론 11-08 23:40 KST 완료, 채점 11-09 18:44 KST(사전 기한 18:00 KST 44분 초과); 데이터·판정 기준·절차 변경 없음. 중단 규칙은 실험 추가 방지 목적이며 추가 실험이 없어 채택 유지. 발표 수치 파일을 v7 기준으로 갱신: reports/eval/lora_v7/presentation_numbers_v7.md(+.json, scripts/presentation_numbers_v7.py) — test_v30 207(base/v4/v5/v7 구체 정밀도·재현율·macro-F1·manual·public 오판 /35), test_v6 289(v5/v7 macro-F1·정확도·manual·public 오판 /265·label별 F1·프로젝트별 정확도·정답 출처별 정확도), test_v5·test_v31_supp는 v7 학습 데이터라 v7 수치 없음(v5 값은 참고로만). v5 발표 표(presentation_numbers_v5.md)는 기록으로 보존. 배포 전환(GGUF Q4_K_M·Ollama blade-qwen-lora-v7·환경변수)은 사용자 결정 후 C-5 절차로 진행하며 확인 항목에 oas(명세만) 조건 public 오판 증가(14/24/6 vs v5 5/7/6)·s44 oas 출력 오류 21건을 기록. 마감 후 과제 목록 reports/post_deadline_tasks.md(Redash G1-b 18건, 여섯 run 공통 오답 70건, OAS pool 256건 사람 검수, manual 규칙 재설계, test_v6 전수 검수, data-v7 사람 확인 시트 회수, 배포 확인 항목, test_v5·supp 재분리). 커밋: 미커밋 보고서·스크립트·AGENTS.md·DATA_CARD·동결 데이터(코드 본문 비공개 파일·xlsx·어댑터·번들 제외, .gitignore 유지)를 feat/lora-pipeline에 커밋. 다른 세션 작업(demo_backend portal, presentation_support 데모 런북, verification/demo_*·mealie_*, writing_1101, deployment_readiness.md, export_public.py)은 이 커밋에 넣지 않는다.
- **S9-base: 베이스 모델 참고 수치(2026-11-10 사전 기록, 추론 전) — 채택 판정과 무관, 커밋 금지**: (1) test_v30 207 oas_code 베이스(base_qwen_runpod, reports/eval/lora_v4 기존 예측 재채점만, 추론 없음): 정확도 0.319·macro-F1 0.197·구체 정밀도 0.353·재현율 0.316·manual 6.8%·public 오판 17/35·출력 오류 9. (2) test_v6 289 oas_code: 베이스 unsloth/Qwen2.5-7B-Instruct-bnb-4bit 어댑터 없음, 프롬프트 v3.0.1, greedy·max_new_tokens 256(S9 디코딩 그대로), S9와 같은 Pod·라이브러리, BLADE_TESTV6_STAGE=S9 게이트, 단일 run(seed 0, 학습 없음) — run_train_v7.py DATASETS 'base'(no_adapter, run base_qwen7b_s9) + runpod/run_s9_base.sh(해시 게이트 → 추론 oas+oas_code → pack → Pod 정지). 지표 macro-F1·정확도·구체 정밀도·public 오판(/265)·출력 오류. S9 판정(v5 vs v7) 이후의 참고 추론이며 판정·채택에 영향 없음. (3) presentation_numbers_v7.md 표에 베이스 열 추가, v5 열은 발표 표(md)에서 빼고 json에 보존. 보고 후 정지.
- **S9-base 결과(추론 2026-11-09 15:29–15:42 UTC, Pod 49dkegbotxusbe H100, S9와 같은 라이브러리 torch 2.13.0+cu129·transformers 5.17.0·unsloth 2026.11.3, 게이트 통과·어댑터 없음 로그 확인·자동 정지; 채점 2026-11-10, 판정 무관)**: test_v6 289 oas_code Base macro-F1 0.214 · 정확도 0.304 · 구체 정밀도 0.425 · 구체 재현율 0.371 · manual 0% · public 오판 36/265 · 출력 오류 37(예측 role 173·public 59·ERR 37·owner 15, 보류 0). v7(3 seed) 같은 지표: 0.650 ± 0.016 · 0.661 ± 0.012 · 0.758 ± 0.038 · 0.682 ± 0.024 · 18.1% · 1/0/0 · 1/0/1(S9 채점 그대로, 재채점 바이트 동일). oas(명세만) Base macro-F1 0.039·출력 오류 142. test_v30 207 Base 정확도 0.319(기존 예측 재채점). **발표 표(사용자 지시 2026-11-10)**: test_v6 하나만, Base vs BLADE LoRA(v7), 지표 4개(macro-F1·정확도·구체 정밀도·public 오판 /265) — presentation_numbers_v7.md 재구성, v5 열·test_v30 표·test_v5/supp 참고값은 json에만 보존. 산출 reports/eval/lora_v7/s9/{base_qwen7b_s9/, run_s9_base.log, SHA256SUMS_s9_base, base_reference.md}, scores_test_v6.json·eval_test_v6.md(base 포함 재생성), runpod/run_s9_base.sh. 커밋 없음.

## 작업 D1: LoRA v7 배포 전환 (2026-11-10 사전 기록 — Pod 실행 전, C-5 절차 그대로, 커밋 금지)

- 순서: s42 fp16 병합 → GGUF Q4_K_M(컨테이너 디스크) → 변환 동등성(test_v30 oas_code, 같은 어댑터 HF s42 final 대비) → val_sft_v7로 MIN_CONFIDENCE(`choose_threshold_v4.py --rule precision`, 바닥 0.7, test 미사용) → Ollama `blade-qwen-lora-v7` 등록 → 환경변수 전환(런타임 코드 미수정) → 로컬 verify_lora_pipeline + pytest + attack_sim 재측정. **v5(blade-qwen-lora-v5, 문턱 0.9)는 롤백용으로 유지.** 결과 보고 후 정지.
- **허용 폭 사전 기록(GGUF 결과 열람 전)**: "v5 때와 같은 허용 폭" = v5 검사에 실제 적용한 수치인 **LoRA v4 3-seed sd(macro-F1 합성 제외 207 0.0454 / 구체 정밀도 207 0.0255 / 구체 정밀도 265 0.0175)**. v5 3-seed sd(0.0104 / 0.0252 / 0.0197)·v7 3-seed sd(0.0187 / 0.0200 / 0.0150)는 병기한다. 세 지표 모두 폭 안이면 수용 제안, 아니면 v4·v5 선례대로 보류 비율 이동 여부를 보고 조건부 수용 제안(사용자 확정). 채점 scripts/eval_v30.py → scripts/equivalence_check_v7.py(v5 수치 재현 확인: 215/265 일치, 전이 23/9/12).
- Pod 게이트(runpod/run_c7.sh, 사용자 지시): RAM ≥ 64 GB(`free -g` 표시값 ≥ 60), 컨테이너 디스크 여유 ≥ 70 GB, 볼륨 `/workspace` 또는 `/workspace-2`(v7 학습 볼륨 `/workspace-2/blade_lora_v3`에 어댑터·data_v7 있음) 자동 감지, 어댑터 SHA `66c68a58…`(lora_v7_s42 adapter_model.safetensors)·data_v7_hashes `bd33f1bc…`·프롬프트 `d0913c27…`·입력 해시 검증 후 시작. 번들 export/blade_c7_v7_20261110.tgz SHA-256 `11f2312446bb442a6c6ce1a908dabaed48753fc16c33fe64332129615f86c31c`(어댑터 s42 + data_v7 4파일 + runpod/{setup_c5.sh, merge_gguf_v7.sh, run_c7.sh} LF + eval_ollama_v7.py + Modelfile.blade-qwen-lora-v7 + README_serve_v7.md + SHA256SUMS_bundle). 절차 training/lora/README_serve_v7.md. Pod 실행과 GGUF(4.7 GB) 회수는 사용자가 한다(로컬에 runpodctl·Pod 접속 정보 없음).
- 로컬 전제(2026-11-10 확인): C: 여유 7.6 GB, Ollama에 blade-qwen-lora-v5만 있고 `qwen2.5:7b`(roles·파라미터 추출, verify_lora_pipeline 필수) 없음 → v7 GGUF 4.7 GB + qwen2.5:7b 4.7 GB에 약 2 GB 부족. GGUF는 Ollama blob 이름으로 두어 복사 없이 등록(v5 방식). 전환 전 기준선 pytest 397 passed·1 skipped(34.7 s). attack_sim 재측정은 scripts/d1_remeasure_v7.py로 verification/remeasure_v7_<date>/에 기록하고 METRICS.md(2026-10-31)는 덮어쓰지 않는다. 결과 기록 reports/eval/lora_v7_gguf/.
- **D1 결과(2026-11-10, Pod 03:0x–03:42 UTC·로컬 10:5x–11:19 UTC) — GGUF 조건부 수용 확정(사용자), blade-qwen-lora-v7 등록·검증 완료, 커밋 1회**: Q4_K_M SHA-256 `1dd24dcdff60619d055277591b134f133a24a4cd62a9b51f3cec8abcdc88144d`(4,683,073,504 bytes, f16 `ab60f867…`, 어댑터 `66c68a58…`, 베이스 `a09a3545…`, llama.cpp b11693; manifest·로그 reports/eval/lora_v7_gguf/). 동등성(test_v30 oas_code, HF s42 대비): macro-F1 207 −0.007(폭 안), **구체 정밀도 207 −0.032(폭 0.0255 이탈)·265 −0.025(폭 0.0175 이탈)**, public 오판 1 → 3(crAPI owner_match 2건 추가), manual 22.6% → 23.4%, 행 일치 229/265(86.4%); v5·v7 sd로 읽어도 1/3. v5 때와 달리 보류 이동으로 설명되지 않는 소폭 정밀도 하락 → 사전 규칙 "조건부 수용 제안" → **사용자 조건부 수용 확정**. 조건: 발표·보고 수치는 HF 3-seed 유지, "평가는 HF 어댑터 기준·배포는 Q4_K_M GGUF" 명시; 한계 절(lora_v7/report.md 6절·presentation_numbers_v7.md)에 정밀도 −0.03·public 오판 +2 기록; 운영 조건 public 판정 정책은 승인(PENDING → ACTIVE) 시 우선 검토; **GGUF 경로 confidence가 test 261/265건 0.9 고정이라 MIN_CONFIDENCE가 실질적으로 거르는 행 0건**임을 한계에 명시(발표 자료에 "문턱으로 불확실 판정 차단" 류 문구 없음 확인); v5 롤백 유지. MIN_CONFIDENCE: val_v7 `--rule precision` → **0.9**(val confidence 0.7:5·0.85:24·0.9:112·1.0:18). 등록: GGUF를 Ollama blob 이름으로 이동(복사 없음), `Modelfile.blade-qwen-lora-v7.local`(.gitignore). 전환은 환경변수만(BLADE_LORA_MODEL=blade-qwen-lora-v7, BLADE_LORA_MIN_CONFIDENCE=0.9; pipeline/classifier/lora.py 기본값 v4·0.9 그대로, 런타임 코드 미수정). 검증: pytest 397 passed·1 skipped(38.3 s); verify_lora_pipeline(BLADE_VERIFY_OUT=reports/eval/lora_v7_gguf, demo_backend/openapi.json 입력) lora 경로 7건 중 6건 의도 일치(premium은 v5와 같이 manual 보류), 프록시 요청 9/9 기대 코드 일치, lora 477.5 s/7건·llm 587.7 s/7건. **2.3 데모 정책 v7 재생성**(verification/demo_v7_runtime/, 입력 openapi_clean.json = Intended 힌트 제거본, v5 데모와 동일, 197 s/7건, 전부 승인): v5 생성본 대비 2/7 변경 — `GET /admin/reports` role_required → **manual**, `GET /orders/{orderId}` owner_match → **manual**(둘 다 보류 방향; DELETE /orders owner_match·orgs tenant_match·users tenant_match·public·premium manual은 동일). 힌트 있는 openapi.json(verify)에서는 6/7 일치이므로 데모 입력의 힌트 유무가 결과를 좌우한다. 2.2 attack_sim 재측정은 D2 뒤로 미룸(시간 부족 시 생략, Phase 1 수치 유지). 어댑터 결과 tar `dd4f771e…`. C: 여유 6.1 GB.

## 작업 D2: 실서비스 적용 후보 조사 (2026-11-10, 조사만 — 구현·실행·커밋 없음)

- 조건: 허용 라이선스 / Windows·Docker 없이 Python·Node + SQLite / owner·role 검사 API ≥ 10 / data-v1~v7·test_v30·supp·test_v5·test_v6·APIs.guru 풀·Mealie(AGPL, verification/mealie_runtime 선례)와 비겹침. 보고 reports/deployment_candidates_d2.md.
- 결과: 1순위 **Seerr v3.5.1**(구 Jellyseerr, MIT, Node 22·Express·TypeORM·sqlite3, OpenAPI `seerr-api.yml` 168 path; owner_or_admin 패턴 다수 — request·issue·issueComment·user 하위, issueComment PUT은 owner_match; 토큰은 `X-API-Key` + `X-API-User` 헤더 치환만, 소유자 조회는 SQLite 정수 id 직접) 2.5–3.5 h → 마감 후(10건·헤더 shim 한정 시 ~2 h 경계; 초기 마법사의 미디어 서버 요구 여부 미검증). 2순위 **Healthchecks v5.0.3**(BSD-3, Django·SQLite, 프로젝트 API 키 = 테넌트 → tenant_match 시연; OpenAPI 없음, UUID 32-hex 저장 → 뷰 필요) 2.5–3 h → 마감 후. 3순위 **Open WebUI v0.13.3**(라이선스 4조 브랜딩 금지 — 허용 라이선스 판단은 사용자 몫; FastAPI·SQLite, owner/role 검사 다수) 2.5 h+ → 마감 후. 기각: InvenTree(Windows 비공식·역할 편중), Payload·Strapi(인가가 설정/엔진에 있어 핸들러 텍스트에 없음, Strapi ee 폴더 EE 라이선스), django-oscar-api(객체 권한 뷰 수 미확인), Wagtail·Saleor, BSL/AGPL/GPL 다수.
- 세 후보 모두 2시간 초과 → 전부 "마감 후". 실행·클론·설치 없음(GitHub raw 읽기만, 스크래치패드).

## 작업 D2 실행 결과: Seerr v3.5.1 연동 시연 (2026-11-10, 사용자 승인 — D1 뒤, 커밋 없음)

- 사용자 결정: 순서 디스크 정리 → D1 → D2, Seerr 한정 3시간 타임박스(Pod 대기 시간 제외 승인, 종료 22:37 KST), 관문 0 판정 "Docker + 수작업 시딩(b)"(settings.cypress.json·seedTestDb.ts 값 그대로, 임의 값 금지, 일반 사용자는 POST /user, Seerr 코드·이미지 수정 금지, 프록시 127.0.0.3, Mealie 잔존 프로세스 불가침). 정책 label은 v7 LoRA(GGUF) 추론만, 토큰은 X-API-Key + X-API-User shim만.
- 결과(verification/d2_seerr_20261110/METRICS_seerr.md): 관문 1 27분 통과(컨테이너 `seerr_d2` ghcr.io/seerr-team/seerr:v3.5.1 digest `d8fab675…`, 사용자 4명, 요청 74·이슈 82). `/generate` 10건 1,272 s(CPU). 모델 label: owner_or_admin 6·role_required 2·owner_match 1·(owner_match→파이프라인 manual 보류) 1; Seerr 의도 일치 7/10(PUT /request 복합 조건·GET /user 필터 응답·GET /settings/main ADMIN 전용은 불일치). **사람 수정 E1·E2·E3은 owner_lookup ERD 결합만**(media_request.requestedById·issue_comment.userId 결합 실패 3건 → 모델 label 복원, issue owner_col modifiedById → createdById 3건; blade/human_edits.json). 검증 28사례 × 20 × 3경로 1,680요청: 프록시 탐지율 84.6%(220/260)·오탐 13.3%(40/300, 전부 GET /user/{id} role_required 과차단), shim·직접 코드 일치 1,680/1,680. Seerr 자체가 공격을 전부 거부하므로 "서비스 인가와의 일치 측정"이다. 지연 p95 프록시 33.8 / shim 38.3 / 직접 24.4 ms. 시딩 등 사람 개입 8항목은 METRICS_seerr.md 4절. MIT 고지 포함. C: 여유 6.0 GB. 데모 정책 재현성: GET /admin/reports·GET /orders/{orderId} 재생성 2/2 동일(manual). 데모 시나리오(manual → owner_match 수정·승인 → BOLA 403) 현재 코드로 동작 확인(scenario_manual_to_owner.sh). 2.2 attack_sim 재측정은 생략(사용자 결정, 발표는 Phase 1 집행 / test_v6 판정 분리 표기).

## 공개 저장소 v7 갱신 (2026-11-11 사용자 지시)

- 공개 저장소 두 개(HokagoSecurityTime/BLADE 프로젝트, HokagoSecurityTime/BLADE-dataset 데이터셋)는 11-02 내부 커밋 3265385의 스퀴시 export(scripts/export_public.py + export/*_manifest.txt) 이후 갱신이 없었다. 이번에 LoRA v7 상태(data-v7·test_v6·LoRA v7 보고·배포 GGUF 기록·한계)로 다시 export해 각 공개 main 위에 한 커밋으로 올린다(내부 히스토리는 공개하지 않는다). 계정은 HyeInLee95(gh 인증), 데모 전용 저장소는 그 다음 단계.
- 공개 사본 v7 확장: build_public_copies.py에 RESTRICTED(Chamilo·Flowise·Generic University·multitenant lab, test_v31_supp 정책)와 data-v7 FROZEN 해시를 추가. train_v7_public 1,540(코드 제외 269)·val_v7_public 159(11)·SFT v7 공개 1,271/148·data_v7_test_v30_inputs_public. 기존 사본 10개는 바이트 동일, 복원 204/305(train_v7 101건은 sha_only — DATA_CARD "공개 배포 사본 v7 확장"). PUBLIC_EXCLUDE에 v7 원본·test_v31_supp 원본 추가.
- 가중치 공개: GitHub Release `lora-v7`(프로젝트 저장소) — 어댑터 tar.gz 3개(SHA256SUMS_blade_v7) + GGUF Q4_K_M 3조각(.part00~02, 1900 MiB 단위 split; 이어 붙인 SHA `1dd24dcd…` 확인) + SHA256SUMS_release_lora_v7 + Modelfile.blade-qwen-lora-v7. GitHub 자산 2 GiB 제한 때문에 분할. Hugging Face 미사용(계정·토큰 없음).
- Errata: test_v6 seahub 건수는 88이 아니라 92(DATA_CARD Errata 추가).
