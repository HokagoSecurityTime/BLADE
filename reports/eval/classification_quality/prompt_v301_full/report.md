# 전체 재라벨링(F) — 프롬프트 3.0.1, APIs.guru 2,027건

실행 완료 2026-10-21T08:39:26Z. 모델 gpt-4o-mini, temperature 0. 프롬프트 SHA `d0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef`, 입력 SHA `ed6e2b2d36f0edc57ceb8878e0e2b67bf8b7a5f7a57a11499aba132bb56dd0f5` (apisguru_enriched_v2.jsonl, v2.5와 동일 입력), 출력 `apisguru_labeled_v301.jsonl` SHA `ac34bd1ec3c2eeafe584e09026a5dfd2dc0fbce9b4e045dd5e1e55326905b827`, 레코드 2027. 사람 교정 미사용, test.jsonl 미접근.

API 응답 2043회, 입력 5,573,661토큰(캐시 4,342,528), 출력 137,031토큰, 사용량 기준 추정 $0.59258 (청구서 아님). 평균 추론 1521.8 ms. 출력 오류 0건, evidence 참조 오류 2건, 비익명 mutation public(flag_review) 5건.

## label 분포

| label | 건수 | 비율 |
|---|---:|---:|
| public | 173 | 8.5% |
| role_required | 124 | 6.1% |
| membership_required | 26 | 1.3% |
| tenant_match | 35 | 1.7% |
| owner_match | 138 | 6.8% |
| owner_or_admin | 1 | 0.0% |
| manual_review_required | 1530 | 75.5% |

**manual_review_required 비율 75.48%** → 70% 기준 초과: train_v30 생성 보류.

## security 선언 여부별 label 분포

| security_state | 건수 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required | manual 비율 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| declared | 1267 | 150 | 120 | 26 | 35 | 134 | 1 | 801 | 63.2% |
| explicitly_anonymous | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0% |
| unknown | 754 | 17 | 4 | 0 | 0 | 4 | 0 | 729 | 96.7% |

**public으로 판정된 건 중 security_state=declared: 150건** (public 전체 173건).

- apisguru:alertersystem.com:get:/api/media-object/{id}
- apisguru:amazonaws.com:get:/workspaces/{workspaceId}/alertmanager/definition
- apisguru:amazonaws.com:get:/workspaces/{workspaceId}/logging
- apisguru:amazonaws.com:get:/workspaces/{workspaceId}/rulegroupsnamespaces
- apisguru:amazonaws.com:get:/workspaces/{workspaceId}/rulegroupsnamespaces/{name}
- apisguru:api.video:get:/videos
- apisguru:api2cart.com:get:/attribute.group.list.json
- apisguru:apigee.net:get:/dealer/heavy-equipment/{id}
- apisguru:apigee.net:get:/dealer/rv/{id}
- apisguru:apigee.net:get:/listing/car/fsbo/{id}/extra
- apisguru:apigee.net:get:/listing/car/uk/{id}/extra
- apisguru:appwrite.io:get:/database/collections/{collectionId}/documents/{documentId}
- apisguru:appwrite.io:get:/storage/files/{fileId}
- apisguru:appwrite.io:get:/teams/{teamId}
- apisguru:appwrite.io:get:/teams/{teamId}/memberships
- apisguru:bbc.com:get:/groups
- apisguru:bbc.com:get:/images
- apisguru:bbc.com:get:/items
- apisguru:bbc.com:get:/master_brands
- apisguru:billingo.hu:get:/documents
- apisguru:box.com:get:/collections/{collection_id}/items
- apisguru:brex.io:get:/api/v1/company/announcement/{id}
- apisguru:brex.io:get:/api/v1/company/notification/list/{id}
- apisguru:brex.io:get:/api/v1/product/search/{subjectId}
- apisguru:bulksms.com:get:/messages/send
- apisguru:callfire.com:get:/calls/recordings/{id}
- apisguru:codat.io:get:/data/companies/{companyId}/assess/excel
- apisguru:codat.io:post:/data/companies/{companyId}/assess/excel
- apisguru:codat.io:get:/data/companies/{companyId}/connections/{connectionId}/assess/accounts/{accountId}/categories
- apisguru:cpy.re:get:/api/v1/users/me/abuses
- apisguru:currencytick.com:get:/historical
- apisguru:drchrono.com:get:/api/clinical_note_field_values/{id}
- apisguru:fec.gov:get:/audit-case/
- apisguru:fec.gov:get:/audit-category/
- apisguru:figshare.com:get:/account/articles/{article_id}/authors
- apisguru:figshare.com:get:/account/articles/{article_id}/categories
- apisguru:flat.io:get:/me
- apisguru:googleapis.com:patch:/accounts/{id}
- apisguru:izettle.com:get:/organizations/{organizationUuid}/categories/v2
- apisguru:izettle.com:get:/organizations/{organizationUuid}/discounts
- apisguru:izettle.com:get:/organizations/{organizationUuid}/discounts/{discountUuid}
- apisguru:izettle.com:get:/organizations/{organizationUuid}/images
- apisguru:linode.com:get:/account/logins/{loginId}
- apisguru:linqr.app:get:/images/{id}
- apisguru:mailchimp.com:get:/automations/{workflow_id}
- apisguru:mastodon.local:post:/api/v1/accounts/{id}/pin
- apisguru:meraki.com:get:/networks/{networkId}/clients
- apisguru:meteosource.com:get:/nearest_place
- apisguru:mist.com:get:/api/v1/installer/orgs/{org_id}/rftemplates
- apisguru:mist.com:get:/api/v1/installer/orgs/{org_id}/secpolicies
- …

## confidence 구간

| 구간 | 건수 | 비율 |
|---|---:|---:|
| [0,0.5] | 0 | 0.0% |
| (0.5,0.7) | 0 | 0.0% |
| [0.7,0.9) | 1549 | 76.4% |
| [0.9,1] | 478 | 23.6% |

## v2.5 → 현재 라벨 전이 (행=v2.5, 열=현재)

| v2.5 \ 현재 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 84 | 16 | 0 | 0 | 3 | 0 | 59 |
| role_required | 0 | 39 | 0 | 0 | 2 | 0 | 22 |
| membership_required | 1 | 19 | 14 | 7 | 2 | 0 | 45 |
| tenant_match | 5 | 3 | 6 | 28 | 8 | 0 | 40 |
| owner_match | 3 | 8 | 4 | 0 | 102 | 0 | 111 |
| owner_or_admin | 0 | 1 | 0 | 0 | 6 | 1 | 4 |
| manual_review_required | 80 | 38 | 2 | 0 | 15 | 0 | 1249 |

## 알려진 한계 (사용자 확인 2026-10-21)

- 코드 입력 시 인증만 있고 인가 검사 없는 핸들러를 public으로 오판(Q 재실행 6/15). 인증이 핸들러 밖(데코레이터·의존성)에 있을 때 발생 추정. 프롬프트는 v3.0.1로 고정.
- 프롬프트 v3.0.1은 security 선언 시 public을 금지하지만, 위와 같이 security_state=declared인 public 판정이 150건 남았다. spec 전역 security 선언을 모델이 해당 operation의 인증 요구로 반영하지 않은 것으로 보이며, train 구성 시 기계 필터(public_declared)로 제외 대상이다.

## 참고 중단 조건(v2.5 파일럿 규칙, 보고만)

confidence_bin_at_least_70_percent

원자료: apisguru_labeled_v301.jsonl, labeled_v301.manifest.json, training/data/label_report_v301.{json,md}, reports/eval/classification_quality/prompt_v301_full/{raw_responses,usage}.jsonl.
