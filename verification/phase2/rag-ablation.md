# RAG ablation

Provider/model: ollama / qwen2.5:7b. Embedding: intfloat/multilingual-e5-small.

| Configuration | Correct / 7 | vs off |
|---|---|---|
| off | 3/7 | +0 |
| code | 6/7 | +3 |
| code+idiom | 6/7 | +3 |
| code+idiom+policy | 6/7 | +3 |
| code+idiom+policy+cve | 6/7 | +3 |

Corpus counts: {"code": 10, "idiom": 6, "policy": 7, "cve": 0}

All configurations keep the same controller input/settings. Off disables retrieval only.
Approved policies may overlap the evaluated demo endpoints; these are demo results, not a held-out accuracy estimate.
An empty CVE corpus means the last row does not measure the effect of CVE evidence.
No configuration has been selected automatically; the user chooses after reviewing this table.
