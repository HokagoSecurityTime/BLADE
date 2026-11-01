# [4] RAG 비교 결과

실제 Ollama qwen2.5:7b, multilingual-e5-small, ChromaDB로 35개 분류를 순차 실행했다. 단위·회귀 169 passed / 1 skipped. 원본: [rag-ablation.json](rag-ablation.json), [비교표](rag-ablation.md).

| 조합 | 정답 | off 대비 |
|---|---|---|
| off | 3/7 | — |
| code | 6/7 | +3 |
| code + idiom | 6/7 | +3 |
| code + idiom + policy | 6/7 | +3 |
| code + idiom + policy + cve | 6/7 | +3 |

off보다 떨어진 조합은 없다. RAG 조합은 모두 조직 문서 경로를 tenant_match 대신 manual_review_required로 분류했다. 2026-10-12 사용자 선택에 따라 `.env`와 `.env.example`의 `BLADE_RAG_KINDS=code,idiom`을 반영했다.

한계: code에는 데모 소스의 Intended policy 설명이 포함된다. ACTIVE 정책 7개도 평가 엔드포인트와 겹친다. 따라서 이 수치는 새로운 서비스에 대한 일반화 정확도가 아니다. cve는 0개여서 마지막 행은 CVE 추가 효과를 검증하지 않는다. Controller 설정과 소스는 모든 조합에서 동일하며, off는 검색만 비활성화했다. 타임아웃 60초·재시도 2회의 기존 어댑터를 유지했다. 일부 실행 중 Docker 빌드도 진행됐으므로 지연을 성능 벤치마크로 해석하지 않는다.
