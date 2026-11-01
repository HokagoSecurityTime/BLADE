# demo_backend: llm vs lora 경로 정책 비교

| endpoint | 의도(데모 설명) | llm label | lora label | label 일치 | llm owner_lookup | lora owner_lookup | owner_lookup 일치 | lora roles |
|---|---|---|---|---|---|---|---|---|
| GET /public/health | public | manual_review_required | public | X | - | - | O | [] |
| GET /orders/{orderId} | owner_match | manual_review_required | owner_match | X | - | orders.id owner=user_id tenant=None | X | [] |
| DELETE /orders/{orderId} | owner_match | manual_review_required | owner_match | X | - | orders.id owner=user_id tenant=None | X | [] |
| GET /users/{userId} | owner_or_admin | manual_review_required | manual_review_required | O | - | - | O | [] |
| GET /admin/reports | role_required | manual_review_required | manual_review_required | O | - | - | O | [] |
| GET /orgs/{orgId}/docs | tenant_match | manual_review_required | tenant_match | X | - | orgs.id owner=None tenant=id | X | [] |
| GET /premium/content | membership_required | manual_review_required | manual_review_required | O | - | - | O | [] |

## lora 정책 승인 → 프록시 요청

| 요청 | 사용자 | 정책 label | 기대 | 실제 | 결과 |
|---|---|---|---:|---:|---|
| BOLA: other user reads order (GET /orders/1042) | user_99 | owner_match | 403 | 403 | OK |
| owner reads own order (GET /orders/1042) | user_77 | owner_match | 200 | 200 | OK |
| BOLA: other user deletes order (DELETE /orders/1042) | user_99 | owner_match | 403 | 403 | OK |
| other tenant reads org docs (GET /orgs/org_1/docs) | user_99 | tenant_match | 403 | 403 | OK |
| same tenant reads org docs (GET /orgs/org_1/docs) | user_77 | tenant_match | 200 | 200 | OK |
| non-admin reads admin reports (GET /admin/reports) | user_99 | manual_review_required | 200 | 200 | OK |
| admin reads admin reports (GET /admin/reports) | admin_1 | manual_review_required | 200 | 200 | OK |
| other user reads user record (GET /users/user_77) | user_99 | manual_review_required | 200 | 200 | OK |
| public health without JWT (GET /public/health) | - | public | 200 | 200 | OK |

## 소요 시간

- llm: 0.1s / 7 policies = 0.0s per policy; ollama ps []
- lora: 356.8s / 7 policies = 51.0s per policy; ollama ps [{'name': 'blade-qwen-lora-v5:latest', 'size': 5470494392, 'size_vram': 0}]

## lora evidence

- GET /public/health: [blade-qwen-lora-v5 policy-label-v3.0.1 label=public confidence=0.9] description: 핸들러 원문 — 인증·권한 검사 없이 익명 호출을 허용하므로; 판단: public 선택 | params: none required
- GET /orders/{orderId}: [blade-qwen-lora-v5 policy-label-v3.0.1 label=owner_match confidence=0.9] description: 핸들러 코드의 fetch_one('SELECT * FROM orders WHERE id = ?', orderId) — 처리 대상이 요청자 본인으로 고정되어 있어; 판단: 소유자 본인만 허용하는 조건이므로 owner_match | params: object_param orderId -> ERD orders.id; owner_col=user_id; tenant_col=None
- DELETE /orders/{orderId}: [blade-qwen-lora-v5 policy-label-v3.0.1 label=owner_match confidence=0.9] description: 핸들러 코드의 orders.user_id — 처리 대상이 요청자 본인으로 고정되어 있어; 판단: 소유자 본인만 허용하는 조건이므로 owner_match | params: object_param orderId -> ERD orders.id; owner_col=user_id; tenant_col=None
- GET /users/{userId}: [blade-qwen-lora-v5 policy-label-v3.0.1 label=owner_or_admin confidence=0.9] description: 핸들러 코드의 fetch_one("SELECT * FROM users WHERE id = ?", userId) — 소유자 본인 또는 권한 보유자만 통과하는 접근; 판단: owner_or_admin | manual_review_required: owner_or_admin requires roles, not found by rules or llm
- GET /admin/reports: [blade-qwen-lora-v5 policy-label-v3.0.1 label=role_required confidence=0.9] description: 핸들러 코드의 with connection — 역할·권한 검사 후 접근; 판단: admin 역할이 유일한 접근 조건이므로 role_required | manual_review_required: role_required requires roles, not found by rules or llm
- GET /orgs/{orgId}/docs: [blade-qwen-lora-v5 policy-label-v3.0.1 label=tenant_match confidence=0.9] description: 핸들러 코드의 fetch_one 'orgs WHERE id = ?' — 자원을 요청자의 tenant 범위로 한정하므로; 판단: tenant 일치가 실제 접근 조건이므로 tenant_match | params: object_param orgId -> ERD orgs.id; owner_col=None; tenant_col=id
- GET /premium/content: [blade-qwen-lora-v5 policy-label-v3.0.1 label=membership_required confidence=0.9] description: 핸들러 코드의 allowed_membership — 대상 자원을 조회해 Premium会员内容的描述表明，该端点的访问控制相关代码摘录，其他检查可能尚在。FILE 手段摘录
def premium_content() -> dict[str, str]:
        return {"content": "Premium members content"}; 판단: 需方资源的 allowed_membership — 代表资源访问的会员要求，因此membership_required | manual_review_required: original label membership_required cannot be enforced by the current runtime (AGENTS.md v2.9)
