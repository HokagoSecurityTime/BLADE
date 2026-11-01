# Phase 1 / Phase 2 load comparison

Separate client/proxy/admin/backend processes on the same host; not production capacity. Cold uses unique existing rows; warm primes order 1042. Phase 2 Redis on, Phase 1 Redis off. No LLM worker runs.

| Phase | Concurrency | Cache | Requests | p50 ms | p95 ms | p99 ms | Errors |
|---|---|---|---|---|---|---|---|
| 1 | 50 | cold | 2686 | 87.31 | 129.83 | 259.96 | 0 (0.00%) |
| 2 | 50 | cold | 2146 | 108.46 | 188.38 | 244.79 | 0 (0.00%) |
| 1 | 50 | warm | 4543 | 51.79 | 83.70 | 104.64 | 0 (0.00%) |
| 2 | 50 | warm | 2960 | 81.09 | 121.27 | 190.66 | 0 (0.00%) |

| Concurrency | Cache | Phase 2 p95 minus Phase 1 ms | +5 ms guard |
|---|---|---|---|
| 50 | cold | +58.55 | FAIL |
| 50 | warm | +37.57 | FAIL |

| Phase | Concurrency | Cache | Expected detections | Stored detections |
|---|---|---|---|---|
| 1 | 50 | cold | 2686 | 563 |
| 2 | 50 | cold | 2146 | 2146 |
| 1 | 50 | warm | 4544 | 520 |
| 2 | 50 | warm | 2961 | 2961 |
