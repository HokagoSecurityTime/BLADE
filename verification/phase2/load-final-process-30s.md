# Phase 1 / Phase 2 load comparison

Separate client/proxy/admin/backend processes on the same host; not production capacity. Cold uses unique existing rows; warm primes order 1042. Phase 2 Redis on, Phase 1 Redis off. No LLM worker runs.

| Phase | Concurrency | Cache | Requests | p50 ms | p95 ms | p99 ms | Errors |
|---|---|---|---|---|---|---|---|
| 1 | 50 | cold | 17513 | 81.55 | 120.87 | 141.15 | 0 (0.00%) |
| 2 | 50 | cold | 18325 | 78.55 | 114.97 | 137.72 | 0 (0.00%) |
| 1 | 50 | warm | 26851 | 53.37 | 80.62 | 98.26 | 0 (0.00%) |
| 2 | 50 | warm | 25009 | 57.48 | 82.74 | 107.54 | 0 (0.00%) |
| 1 | 100 | cold | 17311 | 167.27 | 229.81 | 287.79 | 0 (0.00%) |
| 2 | 100 | cold | 17131 | 143.38 | 223.66 | 320.34 | 0 (0.00%) |
| 1 | 100 | warm | 31103 | 93.27 | 130.61 | 155.98 | 0 (0.00%) |
| 2 | 100 | warm | 26195 | 103.64 | 187.73 | 253.25 | 0 (0.00%) |
| 1 | 200 | cold | 14796 | 396.73 | 606.25 | 678.23 | 0 (0.00%) |
| 2 | 200 | cold | 19966 | 298.00 | 440.41 | 515.58 | 0 (0.00%) |
| 1 | 200 | warm | 23855 | 218.14 | 449.53 | 511.62 | 0 (0.00%) |
| 2 | 200 | warm | 22943 | 242.55 | 457.28 | 524.87 | 0 (0.00%) |

| Concurrency | Cache | Phase 2 p95 minus Phase 1 ms | +5 ms guard |
|---|---|---|---|
| 50 | cold | -5.90 | PASS |
| 50 | warm | +2.12 | PASS |
| 100 | cold | -6.14 | PASS |
| 100 | warm | +57.12 | FAIL |
| 200 | cold | -165.84 | PASS |
| 200 | warm | +7.75 | FAIL |

| Phase | Concurrency | Cache | Expected detections | Stored detections |
|---|---|---|---|---|
| 1 | 50 | cold | 17513 | 1159 |
| 2 | 50 | cold | 18325 | 18325 |
| 1 | 50 | warm | 26852 | 1194 |
| 2 | 50 | warm | 25010 | 25010 |
| 1 | 100 | cold | 17311 | 765 |
| 2 | 100 | cold | 17131 | 17131 |
| 1 | 100 | warm | 31104 | 1055 |
| 2 | 100 | warm | 26196 | 26196 |
| 1 | 200 | cold | 14796 | 608 |
| 2 | 200 | cold | 19966 | 19966 |
| 1 | 200 | warm | 23856 | 1459 |
| 2 | 200 | warm | 22944 | 22944 |
