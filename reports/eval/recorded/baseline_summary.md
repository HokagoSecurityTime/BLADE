# Frozen test baseline

Intermediate results; completed/total must reach 253 before comparison.

| Run | Completed | Macro F1 | Manual ratio | Mean inference ms | Errors |
|---|---:|---:|---:|---:|---:|
| a | 253/253 | 0.0896 | 54.94% | 1793.4 | 5 |

Raw/final comparison (a, n=253): macro-F1 0.1255 -> 0.0896.
Manual ratio: 17.00% -> 54.94%; changed labels: 96; missing traces: 0.
Correct -> wrong: 37; wrong -> correct: 1; invalid raw labels: 0 (counted as errors, not manual).
Validation events: `{"Caller-attribute/public policy conflicts with object lookup": 2, "confidence_below_0.7": 112, "Missing or unknown object parameter/owner lookup": 7, "Unknown lookup table or id column": 13, "json_or_schema_invalid": 5}`.

| Label | Raw P | Raw R | Raw F1 | Final P | Final R | Final F1 |
|---|---:|---:|---:|---:|---:|---:|
| public | 0.3511 | 0.7188 | 0.4718 | 0.4098 | 0.3906 | 0.4000 |
| role_required | 0.4545 | 0.1020 | 0.1667 | 0.4000 | 0.0816 | 0.1356 |
| membership_required | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| tenant_match | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| owner_match | 0.3333 | 0.1875 | 0.2400 | 0.1429 | 0.0536 | 0.0779 |
| owner_or_admin | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| manual_review_required | 0.0000 | 0.0000 | 0.0000 | 0.0072 | 0.1429 | 0.0137 |

Raw confusion matrix (invalid outputs remain errors):

| True / Raw | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 46 | 0 | 0 | 0 | 9 | 1 | 8 |
| role_required | 30 | 5 | 0 | 0 | 7 | 1 | 6 |
| membership_required | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| owner_match | 53 | 6 | 1 | 0 | 21 | 2 | 29 |
| owner_or_admin | 1 | 0 | 0 | 0 | 8 | 0 | 0 |
| manual_review_required | 1 | 0 | 0 | 0 | 6 | 0 | 0 |

## a

State: complete. Test SHA-256: `bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa`.

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| public | 0.4098 | 0.3906 | 0.4000 | 64 |
| role_required | 0.4000 | 0.0816 | 0.1356 | 49 |
| membership_required | 0.0000 | 0.0000 | 0.0000 | 6 |
| tenant_match | 0.0000 | 0.0000 | 0.0000 | 6 |
| owner_match | 0.1429 | 0.0536 | 0.0779 | 112 |
| owner_or_admin | 0.0000 | 0.0000 | 0.0000 | 9 |
| manual_review_required | 0.0072 | 0.1429 | 0.0137 | 7 |

Confusion matrix: rows=human label, columns=runtime prediction.

| True / Predicted | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 25 | 0 | 0 | 0 | 6 | 0 | 33 |
| role_required | 19 | 4 | 0 | 0 | 6 | 0 | 20 |
| membership_required | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| owner_match | 16 | 6 | 1 | 0 | 6 | 0 | 83 |
| owner_or_admin | 1 | 0 | 0 | 0 | 6 | 0 | 2 |
| manual_review_required | 0 | 0 | 0 | 0 | 6 | 0 | 1 |

Controller coverage: `{"source_present_but_runtime_handler_unmapped": 212, "parsed_current_handler": 37, "source_unavailable": 4}`.
ERD coverage: `{"missing": 211, "available": 42}`.
Errors: `{"invalid_model_output_schema": 5}`.

Protocol: unchanged pipeline.classify, prompt v2.0. Runtime confidence <0.7 and invalid owner lookup become manual_review_required.
RAG uses the runtime embedding Index over repository generic idioms only (no test labels, challenge answers, approved test policies or test source in retrieval). Controller source is supplied separately.
Unsupported/unmapped controller handlers are reported as missing runtime signals; stored review hints are not injected as parser output.
Missing ERD prevents object-label lookup validation in the unchanged runtime. These scores measure the pipeline with available OAS/ERD/controller inputs, not pure seven-label semantic classification. No ERD tables are fabricated.
Provider/schema failures retain the runtime manual result and are also counted separately. Wall inference latency includes runtime retries; retrieval is measured separately in checkpoints.
