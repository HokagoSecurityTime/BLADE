# D2 — Seerr v3.5.1 실서비스 연동 시연 (2026-11-10, LoRA v7 GGUF 정책 생성 + BLADE 프록시 집행)

대상 **Seerr v3.5.1**(구 Jellyseerr, 커밋 `564bfb08`, **MIT License** — 원문 `upstream/LICENSE` SHA-256 `0fa8ec7a…`; 애플리케이션 코드·Docker 이미지 `ghcr.io/seerr-team/seerr:v3.5.1`(digest `d8fab675…`)는 수정하지 않았다). Seerr는 Node 22·Express·TypeORM·SQLite(WAL)이며 Docker 컨테이너 `seerr_d2`(127.0.0.1:5055, 볼륨 `seerr_d2_config`)로 실행했다. 정책 label은 **LoRA v7 GGUF(blade-qwen-lora-v7, MIN_CONFIDENCE 0.9)** 가 추론했고 사람은 label을 정하지 않았다(사람 개입은 아래 전부 기록). BLADE 런타임 코드(pipeline/·proxy/·admin_api/)는 수정하지 않았다. 토큰은 **X-API-Key + X-API-User 헤더 shim**(`token_shim_seerr.py`)만 썼다.

## 1. 단계별 결과

| 단계 | 시각(UTC) | 결과 |
|---|---|---|
| 관문 0(문서·코드 읽기) | D1 Pod 대기 중 | 초기 마법사는 Plex/Jellyfin 미디어 서버 없이 완료 불가(설계) → 사용자 판정: Docker + 수작업 시딩(b) 허용 |
| 관문 1(실행·사용자·데이터) | 03:32:25 → 03:59:25 (27분) | 컨테이너 기동, settings.json 원문 복사, 사용자 4명(admin 1·demo 1·alice·bob), 요청 4·이슈 2(+자동 댓글) |
| 삭제 대상 풀 | 04:03:50 | alice 영화 요청 70 + 이슈 80(API로 생성, DELETE 정상 사례용) |
| 입력·하네스 준비 | ~04:14 | OAS 10 operation 부분집합, 핸들러 평탄화 TS, 스키마 dump, shim, seerr_sim.py(28사례) |
| (D1 Pod·GGUF 대기) | 04:14 → 11:20 | 타임박스에서 제외(사용자 승인) |
| 정책 생성(`/generate`, v7) | 11:20:08 → 11:41:20 (1,272 s, 10건 = 127 s/건, CPU) | 10건 PENDING |
| 사람 수정(owner_lookup)·승인 | 12:45:46 → 12:45:48 | 10건 ACTIVE(apply_human_edits.py, human_edits.json) |
| 검증 실행(seerr_sim.py -n 20) | 12:46:40 → 12:47:03 | 28사례 × 20 × 3경로 = 1,680 요청, 오류 0 |
| 정리 | 12:48:28 | BLADE 프로세스(admin 8102·shim 5056·proxy 127.0.0.3:8080) 종료, Seerr 컨테이너는 유지(`docker stop seerr_d2`로 정리 가능) |

실제 작업 시간(대기 제외) 약 2시간 10분, 사용자 지정 종료 13:37 UTC(22:37 KST) 이전 완료.

## 2. 생성 정책 10건 (label = v7 모델 출력, 파라미터 = 파이프라인 추출, 사람 수정은 E1~E3)

| # | 엔드포인트 | 모델 label(확신도) | 파이프라인 결과 | 사람 수정 | 최종 ACTIVE 정책 | Seerr 실제 조건(코드) |
|---|---|---|---|---|---|---|
| 1 | GET /api/v1/request/{requestId} | owner_or_admin 0.9 | manual 0.0 (requestId ERD 미결합 "Unknown lookup table") | **E1** owner_lookup media_request.id/requestedById, label 복원 | owner_or_admin, roles [owner, admin] | 요청자 본인 OR MANAGE_REQUESTS·REQUEST_VIEW |
| 2 | PUT /api/v1/request/{requestId} | role_required 0.9 | roles ['admin','user'](LLM 추출) | 없음 | role_required ['admin','user'] | (본인 AND 영화면 REQUEST_ADVANCED) OR MANAGE_REQUESTS |
| 3 | DELETE /api/v1/request/{requestId} | owner_or_admin 0.9 | manual 0.0 (같은 미결합) | **E1** | owner_or_admin | MANAGE_REQUESTS OR (본인 AND PENDING) |
| 4 | GET /api/v1/issue/{issueId} | owner_or_admin 0.9 | owner_col modifiedById | **E3** owner_col → createdById | owner_or_admin | 작성자 OR MANAGE_ISSUES·VIEW_ISSUES |
| 5 | DELETE /api/v1/issue/{issueId} | owner_or_admin 0.9 | owner_col modifiedById | **E3** | owner_or_admin | MANAGE_ISSUES OR (작성자 AND 댓글 ≤ 1) |
| 6 | POST /api/v1/issue/{issueId}/comment | owner_or_admin 0.9 | owner_col modifiedById | **E3** | owner_or_admin | 작성자 OR MANAGE_ISSUES |
| 7 | PUT /api/v1/issueComment/{commentId} | owner_match 0.9 | manual 0.0 (commentId 미결합) | **E2** owner_lookup issue_comment.id/userId, label 복원 | owner_match | 댓글 작성자만(관리자도 거부) |
| 8 | GET /api/v1/user/{userId} | role_required 0.9 | roles ['admin'] | 없음 | role_required ['admin'] | 인증만; 본인·MANAGE_USERS 아니면 필터된 공개 필드 반환 |
| 9 | GET /api/v1/user/{userId}/quota | owner_or_admin 0.9 | user.id/id | 없음 | owner_or_admin | 본인 OR (MANAGE_USERS AND MANAGE_REQUESTS) |
| 10 | GET /api/v1/settings/main | owner_match 0.9 | manual 0.0 (객체 없음) | 없음 | manual_review_required(OBSERVE) | ADMIN 전용 |

- 모델 label 10건 중 Seerr 의도와 맞는 것 7건(1·3·4·5·6·7·9), 어긋난 것 3건: #2(복합 조건을 role_required로), #8(필터 응답 허용 패턴을 role_required로), #10(ADMIN 전용을 owner_match로 — 객체가 없어 파이프라인이 manual로 보류). 이 판정은 사후 분석이며 정책 label에는 반영하지 않았다.
- 사람 수정 3종(E1·E2·E3)은 모두 **owner_lookup의 ERD 결합**만 바꿨다(기록 `blade/human_edits.json` SHA-256 `de4bf544…`, before/after 전문). E1·E2는 파이프라인이 모델 label을 보류로 떨어뜨린 것을 모델 label로 되돌리며 결합을 채운 것이고, E3은 파이프라인이 고른 `modifiedById`가 Seerr가 수정 시에만 채우는 열이어서(새 이슈는 NULL → 작성자 본인도 차단됨) `createdById`로 바꾼 것이다. roles 목록은 추출 그대로 두었다.
- 생성 원본 `blade/generate_response.json`(SHA `63a34a1a…`), 실행 시점 정책 `results/policies_at_run.json`(`5ab2740f…`), YAML `blade/policies/`.

## 3. 검증 — 공격·정상 요청 28사례 × 20회, 세 경로(프록시 → shim → Seerr / shim → Seerr / Seerr 직접)

전체(프록시): 공격 260요청 중 차단 220(**탐지율 84.6%**), 정상 300요청 중 차단 40(**오탐율 13.3%**). shim 경로와 직접 경로의 HTTP 코드는 1,680건 모두 일치(oracle 1.0) → shim은 인가 판단에 관여하지 않는다. Seerr 자체는 공격 사례를 전부 401/403으로 거부했으므로(취약하지 않음) 프록시는 **Seerr 앞단에서 같은 판단을 먼저 내리는 심층 방어**로 동작했고, 프록시가 놓친 공격(FN 40)은 Seerr가 막았다.

| 생성 label | 요청 | TP | FN | FP | TN | 탐지율 | 오탐율 |
|---|---:|---:|---:|---:|---:|---:|---:|
| owner_or_admin (6 엔드포인트) | 320 | 140 | 0 | 0 | 180 | 100% | 0% |
| owner_match (1) | 60 | 40 | 0 | 0 | 20 | 100% | 0% |
| role_required (2) | 120 | 20 | 20 | 40 | 40 | 50% | 50% |
| manual_review_required (1) | 60 | 20 | 20 | 0 | 20 | 50% | 0% |
| **전체** | 560 | 220 | 40 | 40 | 260 | **84.6%** | **13.3%** |

사례별(각 20회, 괄호는 프록시 / shim / 직접 HTTP 코드):

| 엔드포인트 | 사례 | 판정 | 프록시 verdict | 코드 |
|---|---|---|---|---|
| GET request/1 | alice 본인 / admin / **bob 타인** / **익명** | TN / TN / TP / TP | PASS / PASS(admin_bypass) / BLOCK policy_mismatch / BLOCK no_token | 200·200·200 / 200·200·200 / 403·403·403 / 403·401·401 |
| PUT request/1 | admin / **bob 타인** | TN / **FN** | PASS / PASS(role user 포함) | 200·200·200 / 403·403·403 (Seerr가 차단) |
| DELETE request/{alice 소유} | alice 본인 | TN | PASS | 204·204·204 |
| DELETE request/1 | **bob 타인** | TP | BLOCK | 403·401·401 |
| GET issue/1 | alice / admin / **bob** | TN / TN / TP | PASS / PASS(admin_bypass) / BLOCK | 200 / 200 / 403·403·403 |
| POST issue/1/comment | alice / **bob** | TN / TP | PASS / BLOCK | 200 / 403·403·403 |
| DELETE issue/{alice 소유} | alice | TN | PASS | 204·204·204 |
| DELETE issue/1 | **bob** | TP | BLOCK | 403·401·401 |
| PUT issueComment/1 | alice 본인 / **bob** / **admin**(Seerr는 작성자만) | TN / TP / TP | PASS / BLOCK / BLOCK | 200 / 403 / 403·403·403 |
| GET user/3 | alice 본인 / admin / bob(필터된 공개 필드, 정상) / **익명** | **FP** / TN / **FP** / TP | BLOCK(role_required ['admin']) / PASS / BLOCK / BLOCK no_token | 403·200·200 / 200 / 403·200·200 / 403·401·401 |
| GET user/3/quota | alice / admin / **bob** | TN / TN / TP | PASS / PASS / BLOCK | 200 / 200 / 403·403·403 |
| GET settings/main | admin / **alice 비관리자** / **익명** | TN / **FN** / TP | OBSERVE / OBSERVE(manual) / BLOCK no_token | 200 / 403(Seerr) / 403·401·401 |

- 오탐 40건은 전부 `GET /user/{userId}`: 모델이 role_required(['admin'])로 판정했는데 Seerr는 인증 사용자 누구에게나 필터된 프로필을 돌려준다. 본인 조회(alice)와 타인 조회(bob)가 프록시에서 막혔다. 정상 요청이 프록시에서 거부된 건수 `non2xx_normal` 40 = 이 둘.
- 미탐 40건: `PUT /request/1`(bob) — roles ['admin','user']라 role user도 통과(Seerr가 403); `GET /settings/main`(alice) — manual 보류라 OBSERVE 통과(Seerr가 403). 두 경우 모두 Seerr 자체 인가가 차단했다.
- 지연(560요청, ms): 프록시 경로 p50 8.7 / p95 33.8, shim 경로 p50 9.5 / p95 38.3, 직접 p50 8.4 / p95 24.4. 프록시 경로는 shim을 포함하므로 프록시 추가분은 shim 대비로 보면 p95 차이가 측정 잡음 안이다(로컬 프로세스·CPU 공유). 원본 `results/metrics-{proxy,shim,direct}.json`, 집계 `results/summary.json`(`aba90b64…`).

## 4. 사람이 개입한 지점 (전부)

1. **설정 주입**: `cypress/config/settings.cypress.json`(v3.5.1 원문, SHA `2fc1c447…`)을 바이트 그대로 `/app/config/settings.json`으로 복사(`seed/settings.json`). apiKey "testkey"·sessionSecret·vapid 키는 공개 저장소 테스트 값이며 로컬 전용. Seerr 첫 기동 후 기본 키 34개가 추가됨(`seed/settings.after_first_start.json`, 변경 0).
2. **사용자 행 2건**: `cypress/seedTestDb.ts`(SHA `3ce54cf4…`)의 값 그대로 sqlite 삽입(`seed/seed_users.py` SHA `34462a83…`: admin@seerr.dev perms 2 / demo@seerr.dev perms 32, bcrypt(test1234) 해시, plexToken '1234', gravatar). WAL 때문에 db+wal+shm을 꺼내 checkpoint 후 삽입·복귀. 임의 값 추가 없음.
3. **권한 수정(파일시스템)**: `docker cp`가 root 소유로 쓴 설정 파일 → `chown -R node:node /app/config`(이미지·코드 수정 없음).
4. **일반 사용자 2명**: `POST /api/v1/user`(alice 3, bob 4, defaultPermissions 32) 후 `POST /user/{id}/settings/permissions {"permissions": 4194336}`(REQUEST + CREATE_ISSUES — 이슈·댓글 경로 사례에 필요, 시드 파일에 없는 값이라 기록).
5. **데이터**: 요청 4(TMDB 550·603 alice, 680·155 bob), 이슈 2(alice media 1, bob media 3), 자동 첫 댓글 2; 삭제 대상 alice 요청 70·이슈 80(`prepare_targets.py`, 전부 API).
6. **입력 구성**: OAS 10 operation 부분집합(`inputs/openapi_seerr_subset.json`, `/api/v1` 접두 확장), 핸들러 평탄화(`inputs/controller_seerr_flat.ts`: 라우트 문자열을 전체 경로로 치환, 호출부 TS 제네릭 제거, 헬퍼 2파일 첨부), 스키마 dump. 핸들러 본문은 원문 그대로.
7. **정책 파라미터 수정 E1·E2·E3**(2절) — owner_lookup 결합만, label은 모델 출력(E1·E2는 파이프라인이 보류로 바꾼 것을 모델 label로 복원).
8. **하네스 사례 설계**: 공격/정상 지정 28사례(`seerr_sim.py`), 특히 `PUT /issueComment`의 admin 수정을 공격으로, `GET /user/{id}` 타인 조회를 정상으로 둔 판단.

## 5. 한계

- Seerr는 모든 공격 사례를 스스로 거부하므로 "취약 서비스 보호" 시연이 아니라 "프록시 판정이 서비스 인가와 얼마나 일치하는가"의 측정이다(일치 84.6%, 과차단 13.3%).
- 10건 중 3건은 파이프라인 파라미터 단계가 owner_lookup을 ERD에 결합하지 못해 모델 label이 보류로 떨어졌고 사람이 결합을 채웠다. 실서비스 스키마(테이블 `media_request`·열 `requestedById`)와 경로 변수명(`requestId`)의 불일치가 원인이며 자동 결합의 한계다.
- 생성은 CPU Ollama 127 s/건(10건 21분), 7B Q4_K_M. 반복 측정 없음(단일 생성).
- 비교 셋·학습 데이터와의 겹침: Seerr는 data-v1~v7·test_v30·supp·test_v5·test_v6·APIs.guru 풀에 없다(D2 조사 보고 reports/deployment_candidates_d2.md).

## 6. 디스크

C: 여유 6.0 GB(Docker 이미지 254 MB, 볼륨 수 MB 포함). GGUF v7 4.7 GB·qwen2.5:7b 4.7 GB는 Ollama blob.

## 7. 파일

`upstream/`(원문·SHA256SUMS), `seed/`(settings·sqlite 스냅샷·seed_users.py·SHA256SUMS_seed), `inputs/`(OAS·controller·schema·selection.json), `blade/`(env.sh·run_*.sh·apply_human_edits.py·generate_response.json·human_edits.json·policies/·blade.db·detections.jsonl·admin_8102.log), `token_shim_seerr.py`, `build_inputs.py`, `prepare_targets.py`, `seerr_sim.py`, `data/`(targets.json·create_*.jsonl), `snapshot/db.sqlite3`(`dcc9bfd7…`), `results/`, `logs/timeline.log`. 커밋하지 않았다(사용자 승인 후).
