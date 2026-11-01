# Phase 1 / Phase 2 load comparison

Separate client/proxy/admin/backend processes on the same host; not production capacity. Cold uses unique existing rows; warm primes order 1042. Phase 2 Redis on, Phase 1 Redis off. No LLM worker runs.

| Phase | Concurrency | Cache | Requests | p50 ms | p95 ms | p99 ms | Errors |
|---|---|---|---|---|---|---|---|
| 1 | 50 | cold | 16357 | 86.45 | 131.29 | 178.15 | 0 (0.00%) |
| 2 | 50 | cold | 17635 | 80.44 | 124.09 | 169.83 | 0 (0.00%) |
| 1 | 50 | warm | 25383 | 55.84 | 87.20 | 111.65 | 0 (0.00%) |
| 2 | 50 | warm | 24166 | 59.36 | 89.06 | 116.75 | 0 (0.00%) |
| 1 | 100 | cold | 16433 | 174.66 | 257.63 | 297.38 | 0 (0.00%) |
| 2 | 100 | cold | 12870 | 139.29 | 223.56 | 346.34 | 0 (0.00%) |
| 1 | 100 | warm | 26115 | 109.90 | 164.30 | 205.78 | 0 (0.00%) |
| 2 | 100 | warm | 24549 | 114.34 | 174.93 | 302.42 | 0 (0.00%) |
| 1 | 200 | cold | 15700 | 361.39 | 587.91 | 744.86 | 0 (0.00%) |
| 2 | 200 | cold | 20257 | 290.84 | 438.22 | 524.95 | 0 (0.00%) |
| 1 | 200 | warm | 20372 | 292.26 | 452.13 | 544.87 | 0 (0.00%) |
| 2 | 200 | warm | 20796 | 278.80 | 463.13 | 547.33 | 0 (0.00%) |

| Concurrency | Cache | Phase 2 p95 minus Phase 1 ms | +5 ms guard |
|---|---|---|---|
| 50 | cold | -7.21 | PASS |
| 50 | warm | +1.87 | PASS |
| 100 | cold | -34.07 | PASS |
| 100 | warm | +10.63 | FAIL |
| 200 | cold | -149.69 | PASS |
| 200 | warm | +11.00 | FAIL |

| Phase | Concurrency | Cache | Expected detections | Stored detections |
|---|---|---|---|---|
| 1 | 50 | cold | 16357 | 1136 |
| 2 | 50 | cold | 17635 | 17635 |
| 1 | 50 | warm | 25384 | 1163 |
| 2 | 50 | warm | 24167 | 24167 |
| 1 | 100 | cold | 16433 | 747 |
| 2 | 100 | cold | 12870 | 12870 |
| 1 | 100 | warm | 26116 | 887 |
| 2 | 100 | warm | 24550 | 24550 |
| 1 | 200 | cold | 15700 | 783 |
| 2 | 200 | cold | 20257 | 20257 |
| 1 | 200 | warm | 20373 | 1663 |
| 2 | 200 | warm | 20797 | 20797 |
