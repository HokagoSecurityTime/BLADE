# Frozen test baseline

Intermediate results; completed/total must reach 253 before comparison.

| Run | Completed | Macro F1 | Manual ratio | Mean inference ms | Errors |
|---|---:|---:|---:|---:|---:|
| a | 253/253 | 0.1587 | 41.11% | 1805.9 | 3 |

Raw/final comparison (a, n=253): macro-F1 0.1884 -> 0.1587.
Manual ratio: 8.30% -> 41.11%; changed labels: 83; missing traces: 0.
Correct -> wrong: 37; wrong -> correct: 0; invalid raw labels: 0 (counted as errors, not manual).
Validation events: `{"Caller-attribute/public policy conflicts with object lookup": 8, "Missing or unknown object parameter/owner lookup": 21, "confidence_below_0.7": 69, "Cannot identify ownership column in ERD": 1, "Unknown lookup table or id column": 1, "json_or_schema_invalid": 3}`.

| Label | Raw P | Raw R | Raw F1 | Final P | Final R | Final F1 |
|---|---:|---:|---:|---:|---:|---:|
| public | 0.3739 | 0.6719 | 0.4804 | 0.4915 | 0.4531 | 0.4715 |
| role_required | 0.8462 | 0.2245 | 0.3548 | 0.8333 | 0.2041 | 0.3279 |
| membership_required | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| tenant_match | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| owner_match | 0.5152 | 0.4554 | 0.4834 | 0.3919 | 0.2589 | 0.3118 |
| owner_or_admin | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| manual_review_required | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

Raw confusion matrix (invalid outputs remain errors):

| True / Raw | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 43 | 1 | 0 | 0 | 14 | 1 | 5 |
| role_required | 27 | 11 | 0 | 0 | 8 | 1 | 2 |
| membership_required | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| owner_match | 43 | 1 | 2 | 0 | 51 | 1 | 14 |
| owner_or_admin | 1 | 0 | 0 | 0 | 8 | 0 | 0 |
| manual_review_required | 1 | 0 | 0 | 0 | 6 | 0 | 0 |

## a

State: complete. Test SHA-256: `bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa`.

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| public | 0.4915 | 0.4531 | 0.4715 | 64 |
| role_required | 0.8333 | 0.2041 | 0.3279 | 49 |
| membership_required | 0.0000 | 0.0000 | 0.0000 | 6 |
| tenant_match | 0.0000 | 0.0000 | 0.0000 | 6 |
| owner_match | 0.3919 | 0.2589 | 0.3118 | 112 |
| owner_or_admin | 0.0000 | 0.0000 | 0.0000 | 9 |
| manual_review_required | 0.0000 | 0.0000 | 0.0000 | 7 |

Confusion matrix: rows=human label, columns=runtime prediction.

| True / Predicted | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 29 | 1 | 0 | 0 | 11 | 1 | 22 |
| role_required | 14 | 10 | 0 | 0 | 8 | 1 | 16 |
| membership_required | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| owner_match | 15 | 1 | 2 | 0 | 29 | 0 | 65 |
| owner_or_admin | 0 | 0 | 0 | 0 | 8 | 0 | 1 |
| manual_review_required | 1 | 0 | 0 | 0 | 6 | 0 | 0 |

Controller coverage: `{"source_present_but_runtime_handler_unmapped": 139, "parsed_current_handler": 110, "source_unavailable": 4}`.
ERD coverage: `{"available": 247, "missing": 6}`.
Errors: `{"invalid_model_output_schema": 3}`.

Protocol: unchanged pipeline.classify, prompt v2.0. Runtime confidence <0.7 and invalid owner lookup become manual_review_required.
RAG uses the runtime embedding Index over repository generic idioms only (no test labels, challenge answers, approved test policies or test source in retrieval). Controller source is supplied separately.
Unsupported/unmapped controller handlers are reported as missing runtime signals; stored review hints are not injected as parser output.
Missing ERD prevents object-label lookup validation in the unchanged runtime. These scores measure the pipeline with available OAS/ERD/controller inputs, not pure seven-label semantic classification. No ERD tables are fabricated.
Provider/schema failures retain the runtime manual result and are also counted separately. Wall inference latency includes runtime retries; retrieval is measured separately in checkpoints.
