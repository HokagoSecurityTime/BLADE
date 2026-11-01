# demo_backend: llm vs lora 경로 정책 비교

| endpoint | 의도(데모 설명) | llm label | lora label | label 일치 | llm owner_lookup | lora owner_lookup | owner_lookup 일치 | lora roles |
|---|---|---|---|---|---|---|---|---|
| GET /public/health | public | public | public | O | - | - | O | [] |
| GET /orders/{orderId} | owner_match | owner_match | owner_match | O | orders.id owner=user_id tenant=None | orders.id owner=user_id tenant=None | O | [] |
| DELETE /orders/{orderId} | owner_match | owner_match | owner_match | O | orders.id owner=user_id tenant=None | orders.id owner=user_id tenant=None | O | [] |
| GET /users/{userId} | owner_or_admin | manual_review_required | owner_or_admin | X | - | users.id owner=id tenant=org_id | X | ['admin'] |
| GET /admin/reports | role_required | role_required | role_required | O | - | - | O | ['admin'] |
| GET /orgs/{orgId}/docs | tenant_match | tenant_match | tenant_match | O | orgs.id owner=None tenant=id | orgs.id owner=None tenant=id | O | [] |
| GET /premium/content | membership_required | membership_required | manual_review_required | X | - | - | O | [] |

## lora 정책 승인 → 프록시 요청

| 요청 | 사용자 | 정책 label | 기대 | 실제 | 결과 |
|---|---|---|---:|---:|---|
| BOLA: other user reads order (GET /orders/1042) | user_99 | owner_match | 403 | 403 | OK |
| owner reads own order (GET /orders/1042) | user_77 | owner_match | 200 | 200 | OK |
| BOLA: other user deletes order (DELETE /orders/1042) | user_99 | owner_match | 403 | 403 | OK |
| other tenant reads org docs (GET /orgs/org_1/docs) | user_99 | tenant_match | 403 | 403 | OK |
| same tenant reads org docs (GET /orgs/org_1/docs) | user_77 | tenant_match | 200 | 200 | OK |
| non-admin reads admin reports (GET /admin/reports) | user_99 | role_required | 403 | 403 | OK |
| admin reads admin reports (GET /admin/reports) | admin_1 | role_required | 200 | 200 | OK |
| other user reads user record (GET /users/user_77) | user_99 | owner_or_admin | 403 | 403 | OK |
| public health without JWT (GET /public/health) | - | public | 200 | 200 | OK |

## 소요 시간

- llm: 578.1s / 7 policies = 82.6s per policy; ollama ps [{'name': 'qwen2.5:7b', 'size': 5069917388, 'size_vram': 0}]
- lora: 482.1s / 7 policies = 68.9s per policy; ollama ps [{'name': 'blade-qwen-lora-v4:latest', 'size': 5470494392, 'size_vram': 0}, {'name': 'qwen2.5:7b', 'size': 5069917388, 'size_vram': 0}]

## lora evidence

- GET /public/health: [blade-qwen-lora-v4 policy-label-v3.0.1 label=public confidence=0.9] description: 핸들러 원문 — 인증·권한 검사 없이 공개된 헬스체크를 반환하므로; 판단: 익명 접근이 허용되는 긍정 근거가 있어 public 선택 | params: none required
- GET /orders/{orderId}: [blade-qwen-lora-v4 policy-label-v3.0.1 label=owner_match confidence=0.9] description: 핸들러 원문 — 요청자가 객체 소유자여야 함(구현은 owner_id = principal.id로 명시되지 않지만 의도된 정책은 owner_match); 판단: owner_match | params: object_param orderId -> ERD orders.id; owner_col=user_id; tenant_col=None
- DELETE /orders/{orderId}: [blade-qwen-lora-v4 policy-label-v3.0.1 label=owner_match confidence=0.9] description: 핸들러 원문 — 요청자 id와 객체 소유자 id를 비교해 다르면 거부; 판단: owner_match | params: object_param orderId -> ERD orders.id; owner_col=user_id; tenant_col=None
- GET /users/{userId}: [blade-qwen-lora-v4 policy-label-v3.0.1 label=owner_or_admin confidence=0.9] description: 핸들러 원문 — 소유자 또는 관리자만 허용하는 조건이 명시되어 있음; 판단: owner_or_admin | params: object_param userId -> ERD users.id; owner_col=id; tenant_col=org_id; llm v2.0 filled ['roles']
- GET /admin/reports: [blade-qwen-lora-v4 policy-label-v3.0.1 label=role_required confidence=0.9] description: 핸들러 원문 — 관리자 역할 검사가 접근 조건이라; 판단: admin 역할이 필요하므로 role_required | params: llm v2.0 filled ['roles']
- GET /orgs/{orgId}/docs: [blade-qwen-lora-v4 policy-label-v3.0.1 label=tenant_match confidence=0.9] description: 핸들러 코드의 fetch_one — 자원을 요청자의 tenant 범위로 한정하지 않지만, 의도된 정책은 tenant 일치이므로 tenant_match | params: object_param orgId -> ERD orgs.id; owner_col=None; tenant_col=id
- GET /premium/content: [blade-qwen-lora-v4 policy-label-v3.0.1 label=membership_required confidence=0.9] description: 핸들러 원문 — premium 멤버십만 허용하는 조건부; 판단: membership_required | manual_review_required: original label membership_required cannot be enforced by the current runtime (AGENTS.md v2.9)
