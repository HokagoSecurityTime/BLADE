# Phase 1 / Phase 2 load comparison

Same-process local HTTP regression guard; not production capacity. Cold uses unique existing rows; warm primes order 1042. Phase 2 Redis on, Phase 1 Redis off. No LLM worker runs.

| Phase | Concurrency | Cache | Requests | p50 ms | p95 ms | p99 ms | Errors |
|---|---|---|---|---|---|---|---|
| 1 | 50 | cold | 1692 | 142.75 | 187.46 | 277.85 | 0 (0.00%) |
| 2 | 50 | cold | 1097 | 228.92 | 283.44 | 301.13 | 0 (0.00%) |
| 1 | 50 | warm | 2310 | 101.69 | 147.95 | 256.92 | 0 (0.00%) |
| 2 | 50 | warm | 2312 | 100.58 | 180.96 | 226.87 | 0 (0.00%) |
| 1 | 200 | cold | 1656 | 427.55 | 1866.59 | 3146.92 | 0 (0.00%) |
| 2 | 200 | cold | 1139 | 940.56 | 1369.17 | 1625.19 | 0 (0.00%) |
| 1 | 200 | warm | 1965 | 447.71 | 1333.36 | 2666.33 | 0 (0.00%) |
| 2 | 200 | warm | 2083 | 455.55 | 907.67 | 2081.93 | 0 (0.00%) |

| Concurrency | Cache | Phase 2 p95 minus Phase 1 ms | +5 ms guard |
|---|---|---|---|
| 50 | cold | +95.98 | FAIL: profile only |
| 50 | warm | +33.01 | FAIL: profile only |
| 200 | cold | -497.41 | PASS |
| 200 | warm | -425.69 | PASS |
