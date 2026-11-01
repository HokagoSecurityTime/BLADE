# Phase 1 / Phase 2 load comparison

Same-process local HTTP regression guard; not production capacity. Cold uses unique existing rows; warm primes order 1042. Phase 2 Redis on, Phase 1 Redis off. No LLM worker runs.

| Phase | Concurrency | Cache | Requests | p50 ms | p95 ms | p99 ms | Errors |
|---|---|---|---|---|---|---|---|
| 1 | 50 | cold | 10506 | 138.22 | 181.36 | 212.82 | 0 (0.00%) |
| 2 | 50 | cold | 5636 | 233.72 | 342.72 | 755.64 | 0 (0.00%) |
| 1 | 50 | warm | 15787 | 91.70 | 120.56 | 144.05 | 0 (0.00%) |
| 2 | 50 | warm | 13612 | 97.91 | 204.11 | 241.08 | 0 (0.00%) |
| 1 | 100 | cold | 11873 | 244.46 | 304.52 | 354.30 | 0 (0.00%) |
| 2 | 100 | cold | 6529 | 459.29 | 545.99 | 567.71 | 0 (0.00%) |
| 1 | 100 | warm | 15755 | 183.48 | 238.35 | 295.09 | 0 (0.00%) |
| 2 | 100 | warm | 11481 | 204.19 | 493.24 | 624.99 | 0 (0.00%) |
| 1 | 200 | cold | 6911 | 535.92 | 2977.24 | 5612.61 | 0 (0.00%) |
| 2 | 200 | cold | 2695 | 2143.21 | 3675.70 | 4154.94 | 0 (0.00%) |
| 1 | 200 | warm | 10126 | 584.39 | 869.26 | 1973.17 | 0 (0.00%) |
| 2 | 200 | warm | 10554 | 437.92 | 1025.63 | 1166.62 | 0 (0.00%) |

| Concurrency | Cache | Phase 2 p95 minus Phase 1 ms | +5 ms guard |
|---|---|---|---|
| 50 | cold | +161.36 | FAIL |
| 50 | warm | +83.56 | FAIL |
| 100 | cold | +241.47 | FAIL |
| 100 | warm | +254.89 | FAIL |
| 200 | cold | +698.45 | FAIL |
| 200 | warm | +156.38 | FAIL |

| Phase | Concurrency | Cache | Expected detections | Stored detections |
|---|---|---|---|---|
| 1 | 50 | cold | 10506 | 863 |
| 2 | 50 | cold | 5636 | 5636 |
| 1 | 50 | warm | 15788 | 913 |
| 2 | 50 | warm | 13613 | 12286 |
| 1 | 100 | cold | 11873 | 663 |
| 2 | 100 | cold | 6529 | 6529 |
| 1 | 100 | warm | 15756 | 699 |
| 2 | 100 | warm | 11482 | 10262 |
| 1 | 200 | cold | 6911 | 450 |
| 2 | 200 | cold | 2695 | 2695 |
| 1 | 200 | warm | 10127 | 565 |
| 2 | 200 | warm | 10555 | 8817 |
