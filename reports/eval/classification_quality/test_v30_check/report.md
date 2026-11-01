# T. frozen test.jsonl의 membership_required·tenant_match를 v3.0 정의와 대조 (읽기 전용)

test.jsonl SHA-256 `bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa` 확인. 대상 12건(membership_required 6, tenant_match 6). 전부 test 전용 합성 서비스이며 intended_labels.yaml의 reason과 핸들러 코드의 403 조건으로 대조했다. test.jsonl은 수정하지 않았다.

결과: 일치 6, 불일치 6, 미확정 0. (test 레코드에는 핸들러 원문이 없어 intended reason 기준으로 판정했다.)

| id | service | test label | intended reason | 판정 | v3.0 기준 라벨 | 근거 |
|---|---|---|---|---|---|---|
| quill_blog_workspace_0 | quill_blog | tenant_match | Caller and record must share a tenant. | 일치 | tenant_match | 요청자·객체 tenant 일치 |
| quill_blog_workspace_1 | quill_blog | tenant_match | Caller and record must share a tenant. | 일치 | tenant_match | 요청자·객체 tenant 일치 |
| quill_blog_subscription_0 | quill_blog | membership_required | A premium plan is required. | 불일치 | manual_review_required | 구독·플랜 조건(v3.0: 그룹 구성원 관계가 아니므로 보류) |
| quill_blog_subscription_1 | quill_blog | membership_required | A premium plan is required. | 불일치 | manual_review_required | 구독·플랜 조건(v3.0: 그룹 구성원 관계가 아니므로 보류) |
| folio_wiki_workspace_0 | folio_wiki | tenant_match | Caller and record must share a tenant. | 일치 | tenant_match | 요청자·객체 tenant 일치 |
| folio_wiki_workspace_1 | folio_wiki | tenant_match | Caller and record must share a tenant. | 일치 | tenant_match | 요청자·객체 tenant 일치 |
| folio_wiki_subscription_0 | folio_wiki | membership_required | A premium plan is required. | 불일치 | manual_review_required | 구독·플랜 조건(v3.0: 그룹 구성원 관계가 아니므로 보류) |
| folio_wiki_subscription_1 | folio_wiki | membership_required | A premium plan is required. | 불일치 | manual_review_required | 구독·플랜 조건(v3.0: 그룹 구성원 관계가 아니므로 보류) |
| beacon_iot_workspace_0 | beacon_iot | tenant_match | Caller and record must share a tenant. | 일치 | tenant_match | 요청자·객체 tenant 일치 |
| beacon_iot_workspace_1 | beacon_iot | tenant_match | Caller and record must share a tenant. | 일치 | tenant_match | 요청자·객체 tenant 일치 |
| beacon_iot_subscription_0 | beacon_iot | membership_required | A premium plan is required. | 불일치 | manual_review_required | 구독·플랜 조건(v3.0: 그룹 구성원 관계가 아니므로 보류) |
| beacon_iot_subscription_1 | beacon_iot | membership_required | A premium plan is required. | 불일치 | manual_review_required | 구독·플랜 조건(v3.0: 그룹 구성원 관계가 아니므로 보류) |

## test_v30.jsonl 별도 생성 계획(제안만, 미실행)

- test.jsonl은 그대로 둔다(해시 고정).
- `datasets/blade/processed/test_v30.jsonl`을 새로 만들되, 위 불일치 6건만 label을 v3.0 기준(manual_review_required)으로 바꾸고 `meta.v30_relabel_reason`에 사유를 기록한다. 나머지 6건과 다른 레코드는 바이트 동일.
- 결과: test_v30에서 membership_required support가 0건으로 줄어 해당 label 점수는 측정 불가(N/A)가 된다. 그룹 구성원 의미의 membership 테스트 사례는 별도 확보가 필요하다.
- 사람 확정이 필요하므로 사용자 승인 후에만 생성한다. 생성 시 새 SHA-256을 AGENTS.md에 test.jsonl과 별도 항목으로 기록한다.
