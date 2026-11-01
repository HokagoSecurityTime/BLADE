# Proxy critical path audit

2026-10-12. Audited: `proxy/server.py`, `evaluator.py`, `cache.py`, `lookup.py`, `jwt_auth.py`, `router.py`.

Latest Phase 2 changes: Redis reads are async and coalesced; server-assisted invalidation enables local cache hits; writes are queued. SQLite misses share read-only connections in batches. Detection delivery sends up to 256 records per Stream entry to a background consumer with commit-before-removal and replay deduplication, falling back to HTTP on Redis failure. Compose uses a separate AOF Redis for detection delivery; the ownership cache Redis is unchanged. A full in-memory queue applies backpressure in Phase 2. Shutdown allows 30 seconds for Phase 2 queue draining. No LLM or webhook runs in the request handler. All new paths remain feature-gated. See [verification](../verification/phase2/FINAL_STATUS.md) for durability limits and remaining performance failures. The following numbered description records the original implementation before these improvements.

1. `handle()` matches the in-memory route snapshot, verifies HS256 locally, and calls `evaluate()`.
2. Attribute/public/manual decisions use policy/JWT data only. Object decisions call cache.get; configured Redis I/O runs through `asyncio.to_thread` with bounded connect/socket timeouts and a failure circuit.
3. A cache miss performs the parameterized, read-only SQLite owner lookup in a thread. Cache.set may write Redis. No object row is a PASS for backend 404 handling.
4. observe converts a would-be BLOCK to OBSERVE/would_block. A BLOCK returns 403 before upstream I/O.
5. In-memory counters and `queue.put_nowait()` do not await the admin API. PASS/OBSERVE forwards headers/query/body to the backend. Mutating responses invalidate the lookup cache (including Redis when configured).

The only awaited request-path external I/O categories are Redis, DB lookup and upstream forwarding. JWT verification and matching are local. No classifier, RAG, LLM, webhook or explanation call is reachable from the request handler.

| Background path | Separation / failure |
|---|---|
| Detection sender | Independent task consumes queue, POST /detections; queue-full or delivery failure is logged. Request handler does not await delivery. |
| Observability | Independent task POSTs rolling 60-second snapshot every second. |
| Policy updates | Redis subscriber plus reconciliation/poll fallback updates in-memory routes. Startup waits for initial refresh. |
| Alerts and explanations | Independent admin workers; alert delivery does not wait for LLM explanation. |
| Reanalysis | Admin worker reads persisted detections and rollback events; LLM creates a proposal only. |

Rollback is an admin state transition, not a proxy observation. Its event is saved in the same SQLite transaction as ACTIVE→PENDING; proxy receives the resulting policy snapshot. would_block travels through the existing asynchronous detection path. Both reach the reanalysis worker without new synchronous proxy calls.

Shutdown drains the detection queue for up to five seconds; this affects shutdown, not request latency. In-memory counter work, JSON serialization, thread-pool waits, Redis round trips and shared-host CPU/SQLite contention can still affect measured latency. `scripts/load_test.py` compares identical requests with Phase 2 off/on. A p95 regression over 5 ms is recorded and profiled, not optimized away in this stage.
