# Baseline preparation

Execution started after user confirmation and freezing the 253-row test file. SHA-256: `bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa`. Consult baseline_summary.md for live checkpoint counts and outcomes.

| Configuration | Provider/model | Prompt | RAG | Controller |
|---|---|---|---|---|
| a | OpenAI / gpt-4o-mini | v2.0 | on | on |
| b | Ollama / qwen2.5:7b | v2.0 | on | on |
| c | Ollama / qwen2.5:7b | v2.0 | off | off |

The installed Ollama model list includes qwen2.5:7b. The local embedding model cache and Python dependencies are present; actual retrieval will be verified when each run starts.

Runner: `python -m scripts.eval_classifier --configuration a --test-sha256 <frozen hash>` (likewise b/c). Each configuration has a lock, per-record fsynced checkpoint, immutable settings manifest, and intermediate metrics. Run b then c to avoid contending for the same local model. Configuration a can run separately while the local baseline executes.

RAG uses the unchanged runtime embedding Index over generic repository idioms, with corpus hashes recorded. No human test labels, challenge answers, test policies, or test source enter the retrieval corpus. Controller source enters its separate runtime input. Absent/mismatched/unsupported handlers are reported instead of fabricating parsed signals.

**Input availability limitation:** current test preparation has no ERD for 211 public-vulnerability rows; 42 synthetic rows have DDL. The unchanged runtime converts invalid object lookups and confidence below 0.7 to manual_review_required. Baseline scores therefore measure pipeline performance with available inputs, not pure seven-label semantic classification. Missing ERD is not synthesized, and runtime validation is not bypassed. The v2.5 labeling policy is not substituted for runtime v2.0.

Three evaluator unit tests passed: metric false-positive accounting, human-annotation exclusion, and explicit malformed-ERD handling. Runtime code is unchanged.
