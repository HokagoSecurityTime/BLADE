# Frozen test baseline

All three configurations completed 253/253 records. These are end-to-end runtime results with the input limitations described below.

| Run | Completed | Macro F1 | Manual ratio | Mean inference ms | Errors |
|---|---:|---:|---:|---:|---:|
| a | 253/253 | 0.0903 | 55.73% | 2038.2 | 1 |
| b | 253/253 | 0.1222 | 8.70% | 68159.3 | 0 |
| c | 253/253 | 0.1874 | 3.16% | 12947.1 | 0 |

## a

State: complete. Test SHA-256: `bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa`.

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| public | 0.4310 | 0.3906 | 0.4098 | 64 |
| role_required | 0.3333 | 0.0816 | 0.1311 | 49 |
| membership_required | 0.0000 | 0.0000 | 0.0000 | 6 |
| tenant_match | 0.0000 | 0.0000 | 0.0000 | 6 |
| owner_match | 0.1429 | 0.0536 | 0.0779 | 112 |
| owner_or_admin | 0.0000 | 0.0000 | 0.0000 | 9 |
| manual_review_required | 0.0071 | 0.1429 | 0.0135 | 7 |

Confusion matrix: rows=human label, columns=runtime prediction.

| True / Predicted | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 25 | 0 | 0 | 0 | 6 | 0 | 33 |
| role_required | 17 | 4 | 0 | 0 | 6 | 0 | 22 |
| membership_required | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| owner_match | 15 | 8 | 0 | 0 | 6 | 0 | 83 |
| owner_or_admin | 1 | 0 | 0 | 0 | 6 | 0 | 2 |
| manual_review_required | 0 | 0 | 0 | 0 | 6 | 0 | 1 |

Controller coverage: `{"source_present_but_runtime_handler_unmapped": 212, "parsed_current_handler": 37, "source_unavailable": 4}`.
ERD coverage: `{"missing": 211, "available": 42}`.
Errors: `{"invalid_model_output_schema": 1}`.

## b

State: complete. Test SHA-256: `bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa`.

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| public | 0.3354 | 0.8281 | 0.4775 | 64 |
| role_required | 0.3871 | 0.2449 | 0.3000 | 49 |
| membership_required | 0.0000 | 0.0000 | 0.0000 | 6 |
| tenant_match | 0.0000 | 0.0000 | 0.0000 | 6 |
| owner_match | 0.1429 | 0.0536 | 0.0779 | 112 |
| owner_or_admin | 0.0000 | 0.0000 | 0.0000 | 9 |
| manual_review_required | 0.0000 | 0.0000 | 0.0000 | 7 |

Confusion matrix: rows=human label, columns=runtime prediction.

| True / Predicted | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 53 | 3 | 0 | 0 | 6 | 0 | 2 |
| role_required | 29 | 12 | 0 | 0 | 6 | 0 | 2 |
| membership_required | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| owner_match | 74 | 16 | 0 | 0 | 6 | 0 | 16 |
| owner_or_admin | 1 | 0 | 0 | 0 | 6 | 0 | 2 |
| manual_review_required | 1 | 0 | 0 | 0 | 6 | 0 | 0 |

Controller coverage: `{"source_present_but_runtime_handler_unmapped": 212, "parsed_current_handler": 37, "source_unavailable": 4}`.
ERD coverage: `{"missing": 211, "available": 42}`.
Errors: `{}`.

## c

State: complete. Test SHA-256: `bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa`.

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| public | 0.3595 | 0.8594 | 0.5069 | 64 |
| role_required | 0.4314 | 0.4490 | 0.4400 | 49 |
| membership_required | 0.0000 | 0.0000 | 0.0000 | 6 |
| tenant_match | 1.0000 | 0.1667 | 0.2857 | 6 |
| owner_match | 0.1500 | 0.0536 | 0.0789 | 112 |
| owner_or_admin | 0.0000 | 0.0000 | 0.0000 | 9 |
| manual_review_required | 0.0000 | 0.0000 | 0.0000 | 7 |

Confusion matrix: rows=human label, columns=runtime prediction.

| True / Predicted | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 55 | 2 | 0 | 0 | 6 | 0 | 1 |
| role_required | 21 | 22 | 0 | 0 | 6 | 0 | 0 |
| membership_required | 0 | 1 | 0 | 0 | 5 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 1 | 5 | 0 | 0 |
| owner_match | 75 | 25 | 0 | 0 | 6 | 0 | 6 |
| owner_or_admin | 1 | 1 | 0 | 0 | 6 | 0 | 1 |
| manual_review_required | 1 | 0 | 0 | 0 | 6 | 0 | 0 |

Controller coverage: `{"disabled": 253}`.
ERD coverage: `{"missing": 211, "available": 42}`.
Errors: `{}`.

Protocol: unchanged pipeline.classify, prompt v2.0. Runtime confidence <0.7 and invalid owner lookup become manual_review_required.
RAG uses the runtime embedding Index over repository generic idioms only (no test labels, challenge answers, approved test policies or test source in retrieval). Controller source is supplied separately.
Unsupported/unmapped controller handlers are reported as missing runtime signals; stored review hints are not injected as parser output.
Missing ERD prevents object-label lookup validation in the unchanged runtime. These scores measure the pipeline with available OAS/ERD/controller inputs, not pure seven-label semantic classification. No ERD tables are fabricated.
Provider/schema failures retain the runtime manual result and are also counted separately. Wall inference latency includes runtime retries; retrieval is measured separately in checkpoints.
