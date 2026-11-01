# Phase 1 / Phase 2 load comparison

Separate client/proxy/admin/backend processes on the same host; not production capacity. Cold uses unique existing rows; warm primes order 1042. Phase 2 Redis on, Phase 1 Redis off. No LLM worker runs.

| Phase | Concurrency | Cache | Requests | p50 ms | p95 ms | p99 ms | Errors |
|---|---|---|---|---|---|---|---|
| 1 | 100 | cold | 2728 | 171.97 | 265.16 | 342.69 | 0 (0.00%) |
| 2 | 100 | cold | 3747 | 128.85 | 184.40 | 250.45 | 0 (0.00%) |
| 1 | 100 | warm | 3622 | 124.73 | 211.13 | 377.41 | 0 (0.00%) |
| 2 | 100 | warm | 4018 | 109.14 | 232.98 | 354.08 | 0 (0.00%) |
| 1 | 200 | cold | 2919 | 329.14 | 527.33 | 661.38 | 0 (0.00%) |
| 2 | 200 | cold | 3667 | 266.71 | 390.15 | 419.65 | 0 (0.00%) |
| 1 | 200 | warm | 4256 | 238.73 | 328.75 | 380.96 | 0 (0.00%) |
| 2 | 200 | warm | 4154 | 249.55 | 324.88 | 399.58 | 0 (0.00%) |

| Concurrency | Cache | Phase 2 p95 minus Phase 1 ms | +5 ms guard |
|---|---|---|---|
| 100 | cold | -80.76 | PASS |
| 100 | warm | +21.85 | FAIL |
| 200 | cold | -137.19 | PASS |
| 200 | warm | -3.87 | PASS |

| Phase | Concurrency | Cache | Expected detections | Stored detections |
|---|---|---|---|---|
| 1 | 100 | cold | 2728 | 443 |
| 2 | 100 | cold | 3747 | 3747 |
| 1 | 100 | warm | 3623 | 476 |
| 2 | 100 | warm | 4019 | 4019 |
| 1 | 200 | cold | 2919 | 397 |
| 2 | 200 | cold | 3667 | 3667 |
| 1 | 200 | warm | 4257 | 452 |
| 2 | 200 | warm | 4155 | 4155 |
