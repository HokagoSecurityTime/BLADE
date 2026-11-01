# Presentation commands — Git Bash

Run from `C:/BLADE`. Services are already running on ports 9000/8100/8080.
Tokens expire at 2026-09-15T12:14:47+00:00 (UTC).
These are local demo tokens, not API keys.

```bash
cd /c/BLADE
TOKEN99='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzk5Iiwicm9sZXMiOlsidXNlciJdLCJ0ZW5hbnRfaWQiOiJvcmdfMiIsIm1lbWJlcnNoaXAiOiJiYXNpYyIsImV4cCI6MTc4OTQ3NDQ4N30.wB0-_4zaniWea1laTd99oE2PzvLuapqBPvRhlsiARwM'
TOKEN77='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzc3Iiwicm9sZXMiOlsidXNlciJdLCJ0ZW5hbnRfaWQiOiJvcmdfMSIsIm1lbWJlcnNoaXAiOiJiYXNpYyIsImV4cCI6MTc4OTQ3NDQ4N30.uDphzO5lAqqYT_kUFq3gs5eSYFe9sVBcwSbtH7GGaqA'
FORGED='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzc3Iiwicm9sZXMiOlsidXNlciJdLCJ0ZW5hbnRfaWQiOiJvcmdfMiIsIm1lbWJlcnNoaXAiOiJiYXNpYyIsImV4cCI6MTc4OTQ3NDQ4N30.wB0-_4zaniWea1laTd99oE2PzvLuapqBPvRhlsiARwM'
```

## Step 1 (already executed)

The current store contains the generated policies. Repeating /generate will return 409;
this command records the original operation, not a reset command. Start at step 3 for recording.

```bash
curl -i -X POST http://localhost:8100/generate -F oas=@demo_backend/openapi.json -F erd=@demo_backend/schema.sql
```

## Step 2 (already approved; repeated approval returns 409)

```bash
curl -i -X POST http://localhost:8100/policies/pol_public_health_get/approve
curl -i -X POST http://localhost:8100/policies/pol_orders_get_by_orderId/approve
curl -i -X POST http://localhost:8100/policies/pol_orders_delete_by_orderId/approve
curl -i -X POST http://localhost:8100/policies/pol_users_get_by_userId/approve
curl -i -X POST http://localhost:8100/policies/pol_admin_reports_get/approve
curl -i -X POST http://localhost:8100/policies/pol_orgs_docs_get_by_orgId/approve
curl -i -X POST http://localhost:8100/policies/pol_premium_content_get/approve
curl -i "http://localhost:8100/policies?status=ACTIVE"
```

## Step 3 — expect 403
```bash
curl -i -H "Authorization: Bearer $TOKEN99" http://localhost:8080/orders/1042
```
## Step 4 — expect 200
```bash
curl -i -H "Authorization: Bearer $TOKEN77" http://localhost:8080/orders/1042
```
## Step 5 — expect 403 then 200
```bash
curl -i -X DELETE -H "Authorization: Bearer $TOKEN99" http://localhost:8080/orders/1042
curl -i -H "Authorization: Bearer $TOKEN77" http://localhost:8080/orders/1042
```
## Step 6 — expect 403
```bash
curl -i http://localhost:8080/orders/1042
```
## Step 7 — expect BLOCK >=3 (asynchronous delivery)
```bash
curl -i 'http://localhost:8100/detections?limit=100'
```
## Break 1 — expect 403
```bash
curl -i -H "Authorization: Bearer $FORGED" http://localhost:8080/orders/1042
```
## Break 2 — expect backend 404 and OBSERVE
```bash
curl -i http://localhost:8080/nothing/here
curl -i 'http://localhost:8100/detections?limit=100'
```
## Backend log lines for step 3
```bash
wc -l verification/logs/demo_backend.log
curl -i -H "Authorization: Bearer $TOKEN99" http://localhost:8080/orders/1042
wc -l verification/logs/demo_backend.log
```
