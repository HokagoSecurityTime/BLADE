# C. data-v5 train SFT 1,274건 — label × 출처 유형 교차표

- 입력: training/lora/data_v5/train_sft_v5.jsonl (SHA-256 `2351afe9…` 확인), 출처·프로젝트는 datasets/blade/processed/train_v5.jsonl(`528b3690…` 확인)의 meta.project/service를 id로 조인. 라벨은 두 파일이 전부 일치(assert).
- 출처 유형: 공개 명세 = APIs.guru(oas 조건, 코드 없음) / 실서비스 코드 = Gitea·data-v3 오픈소스 쌍(13개 저장소)·Zulip·Label Studio·Dendrite·NodeBB·Taiga(oas_code) / 합성 = 자체 제작 fixture(oas_code).
- CSV: C_label_x_source_type.csv, C_label_x_project.csv (같은 폴더).

## 1. label × 출처 유형

| label | 공개 명세(APIs.guru) | 실서비스 코드 | 합성 | 합계 | 실서비스 비율 |
|---|---:|---:|---:|---:|---:|
| public | 19 | 49 | 14 | 82 | 60% |
| role_required | 104 | 200 | 22 | 326 | 61% |
| membership_required | 25 | 32 | 20 | 77 | 42% |
| tenant_match | 32 | 29 | 22 | 83 | 35% |
| owner_match | 126 | 299 | 22 | 447 | 67% |
| owner_or_admin | 1 | 63 | 32 | 96 | 66% |
| manual_review_required | 31 | 121 | 11 | 163 | 74% |
| 합계 | 338 | 793 | 143 | 1274 | 62% |

## 2. 출처 유형별 label 분포(열 비율)

| label | 공개 명세(APIs.guru) | 실서비스 코드 | 합성 |
|---|---:|---:|---:|
| public | 19 (5.6%) | 49 (6.2%) | 14 (9.8%) |
| role_required | 104 (30.8%) | 200 (25.2%) | 22 (15.4%) |
| membership_required | 25 (7.4%) | 32 (4.0%) | 20 (14.0%) |
| tenant_match | 32 (9.5%) | 29 (3.7%) | 22 (15.4%) |
| owner_match | 126 (37.3%) | 299 (37.7%) | 22 (15.4%) |
| owner_or_admin | 1 (0.3%) | 63 (7.9%) | 32 (22.4%) |
| manual_review_required | 31 (9.2%) | 121 (15.3%) | 11 (7.7%) |

## 3. label × 프로젝트(상세)

| label | APIs.guru | Dendrite | Gitea | Label Studio | NodeBB | Taiga | Zulip | adr1enbe4udou1n/nestjs-realworld-example-app | gothinkster/flask-realworld-example-app | gothinkster/golang-gin-realworld-example-app | gothinkster/koa-knex-realworld-example | gothinkster/kotlin-spring-realworld-example-app | gothinkster/laravel-realworld-example-app | gothinkster/node-express-realworld-example-app | gothinkster/rails-realworld-example-app | gothinkster/spring-boot-realworld-example-app | nsidnev/fastapi-realworld-example-app | spring-petclinic/spring-petclinic-rest | thedevs-network/kutt | usememos/memos | 합성:campus_records | 합성:campus_records_variants | 합성:copper_wallet | 합성:copper_wallet_variants | 합성:harbor_manifests | 합성:meadow_plots | 합성:orbit_tickets | 합성:orbit_tickets_variants | 합성:pixel_gallery | 합성:relay_forum | 합성:relay_forum_variants | 합계 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| public | 19 | 12 | 13 | 5 | 5 | 9 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 2 | 0 | 2 | 2 | 2 | 0 | 2 | 2 | 0 | 82 |
| role_required | 104 | 19 | 36 | 0 | 41 | 46 | 34 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 24 | 0 | 0 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 326 |
| membership_required | 25 | 6 | 10 | 5 | 10 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 4 | 0 | 0 | 4 | 4 | 4 | 77 |
| tenant_match | 32 | 0 | 0 | 29 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 83 |
| owner_match | 126 | 46 | 96 | 8 | 13 | 17 | 45 | 6 | 6 | 6 | 4 | 6 | 6 | 6 | 6 | 6 | 6 | 0 | 0 | 16 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 447 |
| owner_or_admin | 1 | 4 | 5 | 0 | 16 | 21 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 7 | 2 | 2 | 2 | 2 | 4 | 4 | 2 | 2 | 4 | 4 | 4 | 96 |
| manual_review_required | 31 | 8 | 37 | 13 | 13 | 9 | 41 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 1 | 0 | 0 | 2 | 2 | 0 | 1 | 2 | 163 |
| 합계 | 338 | 95 | 197 | 60 | 98 | 103 | 132 | 6 | 6 | 6 | 4 | 6 | 6 | 6 | 6 | 6 | 6 | 24 | 3 | 23 | 11 | 8 | 12 | 9 | 16 | 16 | 12 | 10 | 16 | 17 | 16 | 1274 |

## 4. source 필드 원값별 건수(참고)

| source | 건수 | 조건 |
|---|---:|---|
| apisguru | 338 | oas |
| opensource_v5 | 296 | oas_code |
| gitea | 197 | oas_code |
| opensource_v4 | 192 | oas_code |
| synthetic | 143 | oas_code |
| opensource_v3 | 108 | oas_code |

주: SFT 1,274건은 train_v5 1,277건에서 4096 토큰 초과 3건(data-v4 시기 제외분)을 뺀 것이다. manual_review_required 163건(12.8%)은 data-v5 쿼터 결과다.
