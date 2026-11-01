# F. 공개 대비 라이선스 처리 방안 (2026-11-01, 방안 보고 — 적용은 승인 후)

원칙: 동결 파일(test_v30·test.jsonl·train_v3a/v3b/v31b/v4/v5·SFT·pairs)은 해시를 바꾸지 않는다. 공개 처리는 **별도 사본(public 변형) + manifest + 문서 기록**으로 한다. data-v5의 NodeBB(GPL-3.0) 처리(코드 본문 .gitignore, train_v5_manifest.json만 공개)와 test_v31_supp(코드 비공개, manifest 공개)와 같은 방식이다.

## 2-a. test_v30의 DVWS-node(GPL-3.0) 발췌 25건

### 현황

| 항목 | 값 |
|---|---|
| 레코드 | test_v30.jsonl 25건(= test.jsonl 25건, 바이트 동일), 전부 controller_text 있음. 저장소 snoopysecurity/dvws-node 커밋 `eb6e2886…`, LICENSE = GNU GPL v3 |
| 코드가 든 추적 파일 | datasets/blade/processed/test.jsonl, test_v30.jsonl, training/lora/data_v{3,31,4,5}/test_v30_inputs.jsonl(oas_code_user 필드), data_v1·v2의 test_v30_inputs.jsonl(미추적) |
| 짧은 인용 | reports/presentation_support/D_before_after_candidates.{csv,json,md}에 DVWS 3건의 핵심 코드 2~3줄 |
| 현재 표시 | 레코드 meta에 license·license_notice_required 없음(data-v2 고지 절의 표시 규칙은 vAPI·DVRestaurant에만 적용됨). DATA_CARD data-v2 절: "GPL-3.0 코드 발췌 포함 레코드는 라이선스 고지 필요" |

### 방안 1 (권장): 코드 본문 제외 사본 + manifest

- `datasets/blade/processed/public/test_v30_public.jsonl`(신규): test_v30.jsonl 269건 중 DVWS-node 25건만 `controller_text`를 `""`로 비우고 `meta.code_withheld = "GPL-3.0 excerpt withheld in public copy"`, `meta.code_ref = {repository, commit, file, start_line, end_line}` 추가. 나머지 244건은 바이트 동일. 빌드 스크립트가 원본 해시(`9bd47216…`)를 assert하고 사본 해시를 manifest에 기록.
- `datasets/blade/processed/public/test_v30_dvws_manifest.json`(신규): 25건의 id·method·path·label·repository·commit·file:start-end·고정 링크(`https://github.com/snoopysecurity/dvws-node/blob/eb6e2886…/<file>#L<s>-L<e>`)·license GPL-3.0. 재구성 스크립트 `scripts/rebuild_test_v30_from_public.py`(신규)로 클론 + manifest → test_v30.jsonl 복원 후 SHA 일치 확인(NodeBB와 같은 방식).
- SFT 입력 사본: `training/lora/data_v5/test_v30_inputs_public.jsonl`은 25건의 oas_code_user를 제외(또는 코드 블록만 삭제)하고 oas_user는 유지. 평가 재현은 원본 입력이 필요하므로 공개본 README에 "oas_code 조건 269건 중 25건은 재구성 후 평가"로 적는다.
- 공개 저장소에서 제외할 파일: test.jsonl, test_v30.jsonl, data_v3/v31/v4/v5의 test_v30_inputs.jsonl. 내부 저장소에서는 추적 유지(동결 해시 불변). 공개 대상 export 시 .gitignore-public 목록 또는 export 스크립트로 제외.
- D 산출물의 DVWS 3건 인용(2~3줄)은 공개본에서 "(GPL-3.0, 링크 참조)"로 바꾼다.
- 장점: NodeBB·Flowise와 처리 방식이 같아 설명이 한 줄이다. 단점: 공개본만으로는 oas_code 25건을 바로 재채점할 수 없다(재구성 스크립트 필요).

### 방안 2: GPL-3.0 고지 후 발췌 유지

- `THIRD_PARTY_NOTICES.md`(신규)에 dvws-node 저장소·저작권자(snoopysecurity)·GPL-3.0 전문 링크·발췌 범위(25건 file:line)를 적고, 공개본 README와 DATA_CARD에 "test_v30의 DVWS-node 발췌 25건은 GPL-3.0이며 발췌의 재배포는 GPL-3.0을 따른다"고 명시. 사이드 manifest(위 test_v30_dvws_manifest.json)로 레코드별 표시를 대신한다(동결 파일에 license_notice_required를 넣을 수 없음).
- 장점: 공개본만으로 평가 재현 가능. 단점: 데이터셋 전체 라이선스가 GPL-3.0 발췌와 섞여 "데이터셋 라이선스"를 단순하게 말할 수 없고, NodeBB(같은 GPL-3.0)는 비공개로 했으므로 처리 기준이 둘이 된다.

**권장: 방안 1.** 사유는 data-v5 NodeBB와 기준 통일, 발표 수치(207건 주지표)에 DVWS 25건이 포함돼도 공개본에는 라벨·OAS·링크가 남아 수치 자체는 설명 가능.

## 2-b. 라이선스 미선언 저장소 5개(28건) 코드 본문 공개 제외

### 현황

| 저장소(키) | 커밋 | 건수(원본/변형) | label |
|---|---|---:|---|
| gothinkster/node-express-realworld-example-app (rw_express) | `30b68e1e…` | 6 (3/3) | owner_match |
| gothinkster/rails-realworld-example-app (rw_rails) | `a2ae4fff…` | 6 (3/3) | owner_match |
| adr1enbe4udou1n/nestjs-realworld-example-app (rw_nest) | `d4ddf3fd…` | 6 (3/3) | owner_match |
| gothinkster/kotlin-spring-realworld-example-app (rw_kotlin) | `848c29e3…` | 6 (3/3) | owner_match |
| gothinkster/koa-knex-realworld-example (rw_koa) | `602e2341…` | 4 (2/2) | owner_match |

GitHub API 기준 license 없음(저장소에 LICENSE 파일 없음, "see repository"도 아님). 라이선스가 없으면 기본적으로 저작권자가 모든 권리를 보유하므로 코드 발췌의 재배포 근거가 없다. 28건은 전부 owner_match(RealWorld 게시글·댓글 수정/삭제의 작성자 검사)이며 data-v3a 이후 모든 train과 SFT에 들어 있다. val에는 없다.

코드가 든 추적 파일(건수): train_v3a.jsonl 28, train_v3b.jsonl 28, train_v31b.jsonl 28, train_v4.jsonl 28, data_v3_stage1/pairs_train_v3s1.jsonl 12, data_v3_stage1b/pairs_train_v3s1b.jsonl 28, training/lora/data_v3/train_sft_v3a.jsonl 28, train_sft_v3b.jsonl 28, data_v31/train_sft_v31b.jsonl 28, data_v4/train_sft_v4.jsonl 28, reports/data_v3/review_pairs_v3s1*.xlsx 4개(6~8행, original/variant_controller_text·removed_check_lines 열). 미추적(.gitignore): train_v5.jsonl 28, train_sft_v5.jsonl 28.

### 방안 (권장)

1. **공개 사본에서 코드 본문 제외, 레코드는 유지**: 레코드 파일(train_v*.jsonl, pairs_*.jsonl)의 공개 사본에서 28건의 `controller_text`를 비우고 `meta.code_withheld = "no license declared; excerpt withheld in public copy"`를 넣는다. 라벨·OAS·rationale·meta(repository·commit·source_locations)는 유지하므로 label 분포·건수는 변하지 않는다. 사이드 manifest `datasets/blade/processed/public/undeclared_license_manifest.json`(id·repo·commit·file:line·고정 링크·label·pair_role).
2. **SFT 공개 사본에서는 28행 제외**: user 메시지에 코드가 통째로 들어 있어 비울 수 없다. train_sft_v{3a,3b,31b,4,5}의 공개 사본은 각각 28행이 빠진다(예: train_sft_v5 1,274 → 1,246). DATA_CARD에 "공개 SFT 사본은 학습에 쓴 파일과 다르며(해시 상이), 학습 재현에는 manifest의 링크로 코드를 재구성해야 한다"고 적는다. 재구성 스크립트는 2-a와 공용.
3. **검수 시트** review_pairs_v3s1*.xlsx 4개는 공개 대상에서 제외하거나, 해당 행의 세 코드 열을 비운 사본을 둔다.
4. **대안(병행 가능)**: 저장소 저자에게 라이선스 확인 요청(gothinkster 조직 3개는 RealWorld 상위 조직이 MIT를 쓰지만 해당 저장소에는 파일이 없음). 회신이 있으면 그 저장소는 공개 사본에서 코드 복원. 회신 전까지는 1~3을 적용.

### DATA_CARD 한계 절에 넣을 문구(초안, 승인 후 추가)

> **라이선스 미선언 출처의 학습 사용(2026-11-01 기록).** data-v3 코드 쌍 가운데 라이선스를 선언하지 않은 저장소 5개(gothinkster/node-express-realworld-example-app `30b68e1e`, gothinkster/rails-realworld-example-app `a2ae4fff`, adr1enbe4udou1n/nestjs-realworld-example-app `d4ddf3fd`, gothinkster/kotlin-spring-realworld-example-app `848c29e3`, gothinkster/koa-knex-realworld-example `602e2341`)의 핸들러 발췌 28건(원본 14·검사 제거 변형 14, 전부 owner_match)을 data-v3a·v3b·v3.1b·v4·v5의 train과 SFT에 사용했다(val·test에는 없음). stage1b_report.md(2026-10-26)가 "학습 투입 전 확인 필요"로 기록했으나 확인 없이 투입됐다. 공개 배포본에서는 이 28건의 코드 본문을 제외하고(레코드·라벨은 유지, SFT 사본은 28행 제외) 저장소·커밋·줄 범위 manifest만 제공한다. 동결 파일과 해시는 바꾸지 않는다.

## 2-c. Dendrite meta.tag 오기 — DATA_CARD errata (데이터 수정 없음)

### 사실

- 원인: `data/raw_v5_train/dendrite/extract_dendrite.py`에서 전역 상수 `TAG`가 두 번 정의됐다. 처음에는 태그 `v0.13.8`로 쓰이다가 342행에서 `TAG = "clientapi/routing/room_tagging.go"`(room tagging 핸들러 파일 경로 약어)로 덮어써져, 그 뒤에 `add()`된 레코드의 `"tag": TAG` 필드(110행)에 파일 경로가 들어갔다.
- 영향 범위(값이 `clientapi/routing/room_tagging.go`인 건): candidates.jsonl 93/136, train_v5_manifest.json 91/126(train 74·val 8·pool 9), train_v5.jsonl 74/95, val_v5.jsonl 8/10, train_v5_rule_labeled·selected·pool(미추적)도 동일 비율. 나머지(43/136)는 `v0.13.8`. **commit(`763c79f1…`)·repository·source_locations·permalink는 전부 정확**하므로 출처 추적에는 영향이 없다. 라벨·코드·SFT 입력에는 tag 필드가 쓰이지 않는다.
- SOURCE.md·DATA_CARD·AGENTS.md·data_sources.md는 태그를 `v0.13.8`로 바르게 적고 있다.

### DATA_CARD에 추가할 절(초안, 승인 후 추가)

> ## Errata
>
> - **data-v5 Dendrite meta.tag 오기 (2026-11-01 발견, 데이터 미수정).** Dendrite 레코드의 `meta.tag`는 `v0.13.8`이어야 하나 추출 스크립트(data/raw_v5_train/dendrite/extract_dendrite.py)의 전역 상수 `TAG` 재정의(342행) 때문에 train_v5.jsonl 74/95건, val_v5.jsonl 8/10건, train_v5_manifest.json 91/126건, candidates.jsonl 93/136건에 파일 경로 문자열 `clientapi/routing/room_tagging.go`가 들어 있다. 커밋 `763c79f1421200c3fd74401fd68298bc00ecefbc`·저장소·source_locations·고정 링크는 정확하다. 동결 해시를 유지하기 위해 파일은 수정하지 않으며, 태그는 이 errata와 data/raw_v5_train/dendrite/SOURCE.md(`v0.13.8`)를 따른다. 재추출 시 스크립트의 상수 이름 충돌을 고쳐야 한다(런타임 코드 아님, 이번에는 수정하지 않음).

## 적용 순서(승인 시)

1. DATA_CARD.md에 2-b 한계 문구와 2-c Errata 절 추가(CRLF 유지) → 커밋.
2. `scripts/build_public_copies.py`(신규): test_v30_public.jsonl + test_v30_dvws_manifest.json, train_v*/pairs_* 공개 사본(28건 코드 비움) + undeclared_license_manifest.json, SFT 공개 사본(28행 제외), 각 사본 해시 기록, 원본 해시 assert. 공개 export 제외 목록(`PUBLIC_EXCLUDE.txt`) 작성.
3. `scripts/rebuild_from_public.py`: 클론 + manifest로 원본 복원 → SHA 일치 확인(DVWS 25건, 미선언 28건, NodeBB 109+pool).
4. reports/presentation_support/D 산출물의 DVWS 인용 3건을 링크로 교체.

## 적용 결과 (2026-11-01, 사용자 승인 후 실행)

- 빌드: `scripts/build_public_copies.py` → datasets/blade/processed/public/ 10개 사본 + withheld_manifest.json + PUBLIC_EXCLUDE.txt, training/lora/public/ SFT 6개·test_v30_inputs 4개 사본. 코드 본문을 뺀 레코드 162건(DVWS 25·미선언 28·NodeBB 109). SFT 제외 행: v3a/v3b/v31b/v4 각 28, v5 train 126, v5 val 11.
- 복원 검증: `scripts/rebuild_from_public.py` — 클론 7개 커밋 일치, 162/162 레코드 SHA 일치, 원본 10개 파일 바이트 동일(OK). manifest 조립 규칙: slices 137(줄 범위 + 들여쓰기 변환 + 생략 표시 줄) · variant 14(원본 줄 번호와 들여쓰기만) · sha_only 0.
- 유출 점검: 원본에 있는 DVWS·미선언·NodeBB 코드 문자열이 공개 사본·SFT 사본에 0건. NodeBB 레코드의 meta.auth_checks(검사 줄 1줄 인용)는 check_lines와 같은 성격이라 유지.
- 문서: DATA_CARD "공개 배포 사본과 라이선스 처리"(2-b 한계 문구 포함)·"Errata"(2-c) 추가, AGENTS.md "공개 배포 사본" 절 추가. D 산출물의 DVWS 3건 인용은 고정 링크로 교체.
- 남은 것: 미선언 저장소 저자에게 라이선스 확인 요청(선택). 회신이 오면 해당 저장소 코드를 공개 사본에 복원할 수 있다.
