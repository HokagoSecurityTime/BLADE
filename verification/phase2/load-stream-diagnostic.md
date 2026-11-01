# Phase 1 / Phase 2 load comparison

Separate client/proxy/admin/backend processes on the same host; not production capacity. Cold uses unique existing rows; warm primes order 1042. Phase 2 Redis on, Phase 1 Redis off. No LLM worker runs.

| Phase | Concurrency | Cache | Requests | p50 ms | p95 ms | p99 ms | Errors |
|---|---|---|---|---|---|---|---|
| 1 | 50 | cold | 2803 | 83.98 | 131.57 | 158.58 | 0 (0.00%) |
| 2 | 50 | cold | 1683 | 143.78 | 197.33 | 310.91 | 0 (0.00%) |
| 1 | 50 | warm | 3884 | 56.16 | 117.76 | 159.22 | 0 (0.00%) |
| 2 | 50 | warm | 4229 | 56.74 | 83.06 | 111.00 | 0 (0.00%) |

| Concurrency | Cache | Phase 2 p95 minus Phase 1 ms | +5 ms guard |
|---|---|---|---|
| 50 | cold | +65.76 | FAIL |
| 50 | warm | -34.70 | PASS |

| Phase | Concurrency | Cache | Expected detections | Stored detections |
|---|---|---|---|---|
| 1 | 50 | cold | 2803 | 523 |
| 2 | 50 | cold | 1683 | 1683 |
| 1 | 50 | warm | 3885 | 439 |
| 2 | 50 | warm | 4230 | 4230 |
