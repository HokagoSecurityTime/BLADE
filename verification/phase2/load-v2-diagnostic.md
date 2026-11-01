# Phase 1 / Phase 2 load comparison

Same-process local HTTP regression guard; not production capacity. Cold uses unique existing rows; warm primes order 1042. Phase 2 Redis on, Phase 1 Redis off. No LLM worker runs.

| Phase | Concurrency | Cache | Requests | p50 ms | p95 ms | p99 ms | Errors |
|---|---|---|---|---|---|---|---|
| 1 | 50 | cold | 1533 | 158.02 | 238.56 | 295.37 | 0 (0.00%) |
| 2 | 50 | cold | 1048 | 215.97 | 446.44 | 874.41 | 0 (0.00%) |
| 1 | 50 | warm | 2340 | 102.23 | 133.10 | 203.65 | 0 (0.00%) |
| 2 | 50 | warm | 1332 | 166.67 | 334.26 | 597.16 | 0 (0.00%) |

| Concurrency | Cache | Phase 2 p95 minus Phase 1 ms | +5 ms guard |
|---|---|---|---|
| 50 | cold | +207.88 | FAIL |
| 50 | warm | +201.16 | FAIL |

| Phase | Concurrency | Cache | Expected detections | Stored detections |
|---|---|---|---|---|
| 1 | 50 | cold | 1533 | 538 |
| 2 | 50 | cold | 1048 | 1048 |
| 1 | 50 | warm | 2341 | 468 |
| 2 | 50 | warm | 1333 | 1333 |
