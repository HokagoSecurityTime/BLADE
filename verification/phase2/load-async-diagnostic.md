# Phase 1 / Phase 2 load comparison

Same-process local HTTP regression guard; not production capacity. Cold uses unique existing rows; warm primes order 1042. Phase 2 Redis on, Phase 1 Redis off. No LLM worker runs.

| Phase | Concurrency | Cache | Requests | p50 ms | p95 ms | p99 ms | Errors |
|---|---|---|---|---|---|---|---|
| 1 | 50 | cold | 1784 | 133.45 | 192.80 | 277.56 | 0 (0.00%) |
| 2 | 50 | cold | 1167 | 211.19 | 261.92 | 357.57 | 0 (0.00%) |
| 1 | 50 | warm | 2513 | 94.97 | 128.98 | 211.32 | 0 (0.00%) |
| 2 | 50 | warm | 1860 | 135.19 | 154.14 | 178.43 | 0 (0.00%) |
| 1 | 200 | cold | 1788 | 396.09 | 1809.88 | 2806.47 | 0 (0.00%) |
| 2 | 200 | cold | 1245 | 852.89 | 1239.84 | 1477.76 | 0 (0.00%) |
| 1 | 200 | warm | 2290 | 395.31 | 755.30 | 2050.60 | 0 (0.00%) |
| 2 | 200 | warm | 1763 | 577.35 | 751.00 | 1291.64 | 0 (0.00%) |

| Concurrency | Cache | Phase 2 p95 minus Phase 1 ms | +5 ms guard |
|---|---|---|---|
| 50 | cold | +69.12 | FAIL: profile only |
| 50 | warm | +25.16 | FAIL: profile only |
| 200 | cold | -570.04 | PASS |
| 200 | warm | -4.30 | PASS |
