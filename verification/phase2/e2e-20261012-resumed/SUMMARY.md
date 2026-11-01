# Phase 2 integration

Real LLM/E5/Chroma/HTTP/SQLite/Redis. Local webhook receiver; external Slack deferred.

| Step | Result | Evidence |
|---|---|---|
| 1 | PASS | 7 PENDING policies generated with real LLM/RAG/controller |
| 2 | PASS | 7 ACTIVE policies, all observe |
| 3 | PASS | 200 + OBSERVE + would_block=true |
| 4 | PASS | 403 + local Slack-format webhook + real LLM explanation |
| 5 | PASS | 20 OBSERVE requests -> real LLM owner_or_admin proposal |
| 6 | PASS | Proposal accepted via API: v2 / owner_or_admin / observe |
| 7 | PASS | Rollback triggered a separate review proposal |
| 8 | PASS | observability rate > 0 |
| 9 | PASS | Redis stopped: still 200 + OBSERVE + would_block |

Steps 5/6 use an explicitly seeded manual-review v1 fixture; original generated policy is preserved in generated-policies.json.
