# Phase 1 / Phase 2 load comparison

Same-process local HTTP regression guard; not production capacity. Cold uses unique existing rows; warm primes order 1042. Phase 2 Redis on, Phase 1 Redis off. No LLM worker runs.

| Phase | Concurrency | Cache | Requests | p50 ms | p95 ms | p99 ms | Errors |
|---|---|---|---|---|---|---|---|
| 1 | 50 | cold | 7718 | 184.95 | 282.35 | 337.47 | 0 (0.00%) |
| 2 | 50 | cold | 5776 | 254.81 | 365.23 | 415.97 | 0 (0.00%) |
| 1 | 50 | warm | 14178 | 101.53 | 137.55 | 175.70 | 0 (0.00%) |
| 2 | 50 | warm | 8122 | 173.74 | 265.62 | 401.34 | 0 (0.00%) |
| 1 | 100 | cold | 7721 | 385.85 | 570.19 | 686.43 | 0 (0.00%) |
| 2 | 100 | cold | 5794 | 521.47 | 648.15 | 805.77 | 0 (0.00%) |
| 1 | 100 | warm | 14423 | 197.13 | 273.15 | 332.87 | 0 (0.00%) |
| 2 | 100 | warm | 8172 | 353.70 | 507.96 | 698.91 | 0 (0.00%) |
| 1 | 200 | cold | 5193 | 1027.98 | 2968.44 | 8213.44 | 0 (0.00%) |
| 2 | 200 | cold | 3791 | 1647.81 | 2873.51 | 3348.43 | 0 (0.00%) |
| 1 | 200 | warm | 6818 | 1041.22 | 1512.24 | 1829.86 | 0 (0.00%) |
| 2 | 200 | warm | 4807 | 1056.58 | 2805.52 | 3497.42 | 0 (0.00%) |

| Concurrency | Cache | Phase 2 p95 minus Phase 1 ms | +5 ms guard |
|---|---|---|---|
| 50 | cold | +82.88 | FAIL: profile only |
| 50 | warm | +128.07 | FAIL: profile only |
| 100 | cold | +77.97 | FAIL: profile only |
| 100 | warm | +234.81 | FAIL: profile only |
| 200 | cold | -94.93 | PASS |
| 200 | warm | +1293.27 | FAIL: profile only |
