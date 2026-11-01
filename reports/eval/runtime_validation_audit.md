# 기존 베이스라인 검증 단계 감사

API 호출 0회. 원시 응답은 저장되지 않았다. 아래는 최종 결과와 런타임 사유 문자열에 따른 분해이며, 원시 라벨의 F1 또는 검증 전후 점수 차이를 복원한 결과가 아니다.

구체 라벨로 남은 결과는 런타임에서 label이 바뀌지 않은 결과다. 검증 실패 사유는 현재 코드의 반환 문자열과 대조했다. 원시 응답이 없으므로 모델이 동일 문자열을 직접 출력했을 가능성까지 배제하는 실행 추적 증거는 아니다.

| 설정 | 최종 macro-F1 | 구체 라벨 정답 | 구체 라벨 오답 | 정책 검증→보류 | JSON/schema 실패 | 원인 구분 불가 보류 |
|---|---:|---:|---:|---:|---:|---:|
| a | 0.0903 | 35 | 77 | 26 | 1 | 114 |
| b | 0.1222 | 71 | 160 | 22 | 0 | 0 |
| c | 0.1874 | 84 | 161 | 6 | 0 | 2 |

a = gpt-4o-mini, RAG/controller on; b = qwen2.5:7b, on; c = qwen2.5:7b, off.

## 해석과 한계

- 정책 검증은 구체 라벨을 manual로 바꾸지만, 해당 구체 라벨이 원래 정답이었는지는 기록되지 않았다. 위 건수를 점수 하락 건수로 계산하지 않는다.
- 원인 구분 불가 보류에는 모델 자체 보류, confidence < 0.7에 의한 변환, 미등록 label 변환이 섞일 수 있다. 저장된 confidence가 낮다는 것만으로 변환 전 label을 알아낼 수 없다.
- 구체 라벨 오답은 런타임 label 변환 탓이 아니다. 모델·프롬프트·입력 문맥을 포함한 검증 이전 단계의 오류이며 모델 자체 능력만의 오류로 단정하지 않는다.
- b와 c는 RAG와 controller 두 설정이 동시에 다르므로 점수 차이를 RAG 단독 효과로 해석할 수 없다.
- 정확한 전후 점수는 평가 스크립트에서 llm.complete 반환 원문을 파싱 전에 별도로 기록하는 재측정이 필요하다. 이 감사에서는 재호출하거나 런타임을 수정하지 않았다.
- 근거 코드: scripts/eval_classifier.py의 record 저장, pipeline/classifier/schema.py의 unknown_label/low_confidence/parse_result, pipeline/classifier/__init__.py의 classify 검증 분기.
- JSON 보고서에는 759건 전부의 단계 분류와 입력 파일 해시를 보존한다.

## a: 검증 실패 분해

| 사유 | 건수 |
|---|---:|
| Caller-attribute/public policy conflicts with object lookup | 3 |
| Unknown lookup table or id column | 14 |
| Missing or unknown object parameter/owner lookup | 9 |

검증 보류의 사람 정답: `{"role_required": 2, "public": 8, "owner_match": 14, "owner_or_admin": 2}`.
검증 보류 중 ERD가 비어 있는 건수: 26/26.

아래 목록은 검증에서 보류로 바뀐 것으로 식별된 사례다. 원래 세부 label을 알 수 없어 정답이 오답으로 바뀐 건수라고 해석하면 안 된다.

| id | service | 사람 정답 | 검증 사유 |
|---|---|---|---|
| b98a2ab3b50a679bfa16 | VAmPI | role_required | Caller-attribute/public policy conflicts with object lookup |
| c47f96241d6d7fc93158 | VAmPI | public | Unknown lookup table or id column |
| b3906a959a0b669047ba | VAmPI | owner_match | Unknown lookup table or id column |
| 217a26a0ed334f7297d0 | VAmPI | owner_match | Unknown lookup table or id column |
| 2463648df20db46705c1 | crAPI | role_required | Unknown lookup table or id column |
| 9a7d3d59efab53f32063 | crAPI | public | Unknown lookup table or id column |
| d0afe4b052514b189dfa | crAPI | owner_match | Unknown lookup table or id column |
| 324601a8dc9e9ea969bb | crAPI | public | Unknown lookup table or id column |
| cc7aabb324d891f2d312 | juice-shop | owner_match | Unknown lookup table or id column |
| 7ff76e2ecef4c5c31665 | juice-shop | owner_or_admin | Unknown lookup table or id column |
| 4e0c68cd981acbfe4a95 | juice-shop | owner_or_admin | Unknown lookup table or id column |
| 90b7d387b719e9937263 | Pixi | public | Missing or unknown object parameter/owner lookup |
| c31d0a5bb5c879e094f3 | Pixi | public | Caller-attribute/public policy conflicts with object lookup |
| bcfa59eea899fc11ba4f | Pixi | public | Caller-attribute/public policy conflicts with object lookup |
| e8437c5320794a594af6 | Pixi | owner_match | Missing or unknown object parameter/owner lookup |
| c250b480c9ec5ee55617 | Pixi | owner_match | Missing or unknown object parameter/owner lookup |
| bbfd5bfc671dc4af42c5 | Pixi | owner_match | Missing or unknown object parameter/owner lookup |
| fd938e89d9362deb8656 | Pixi | owner_match | Missing or unknown object parameter/owner lookup |
| b92cea1a3f110420ee85 | Pixi | public | Unknown lookup table or id column |
| b036005643c333b5e7ae | Pixi | public | Unknown lookup table or id column |
| bf900bef2d12400d0880 | Pixi | owner_match | Missing or unknown object parameter/owner lookup |
| 28fa5fab6338ef186954 | Pixi | owner_match | Missing or unknown object parameter/owner lookup |
| 7ab0a0779b998f445f3c | Pixi | owner_match | Missing or unknown object parameter/owner lookup |
| 7292860512c06eed2ffd | Pixi | owner_match | Missing or unknown object parameter/owner lookup |
| 6309b77a47e9b994f9fe | Pixi | owner_match | Unknown lookup table or id column |
| a15a54f7818a6cf25d98 | DVWS-node | owner_match | Unknown lookup table or id column |

## b: 검증 실패 분해

| 사유 | 건수 |
|---|---:|
| Unknown lookup table or id column | 22 |

검증 보류의 사람 정답: `{"owner_match": 16, "role_required": 2, "public": 2, "owner_or_admin": 2}`.
검증 보류 중 ERD가 비어 있는 건수: 22/22.

아래 목록은 검증에서 보류로 바뀐 것으로 식별된 사례다. 원래 세부 label을 알 수 없어 정답이 오답으로 바뀐 건수라고 해석하면 안 된다.

| id | service | 사람 정답 | 검증 사유 |
|---|---|---|---|
| 4af8a0694ed2e327e0db | VAmPI | owner_match | Unknown lookup table or id column |
| aae57acca0e9317e81c1 | crAPI | owner_match | Unknown lookup table or id column |
| d0afe4b052514b189dfa | crAPI | owner_match | Unknown lookup table or id column |
| c3203410c4072686beaa | crAPI | owner_match | Unknown lookup table or id column |
| 6bca6097b26cf226f405 | crAPI | owner_match | Unknown lookup table or id column |
| d42ed128370ce4d3ce71 | crAPI | owner_match | Unknown lookup table or id column |
| 0b0918598294090d14c3 | crAPI | owner_match | Unknown lookup table or id column |
| 267af32d80a0676db11d | juice-shop | owner_match | Unknown lookup table or id column |
| 8f823c91369626ba6d9f | juice-shop | role_required | Unknown lookup table or id column |
| d03dd5bb033fde20a6b9 | juice-shop | owner_match | Unknown lookup table or id column |
| cc7aabb324d891f2d312 | juice-shop | owner_match | Unknown lookup table or id column |
| bb8c80531d0fc1d9caed | juice-shop | public | Unknown lookup table or id column |
| 13b3024516b002a3d17d | juice-shop | owner_match | Unknown lookup table or id column |
| 7ff76e2ecef4c5c31665 | juice-shop | owner_or_admin | Unknown lookup table or id column |
| be9b12fb6e4c31c1d823 | juice-shop | owner_match | Unknown lookup table or id column |
| 7b6e2731e933a52a9070 | juice-shop | owner_match | Unknown lookup table or id column |
| a15c48c2351014fde76c | juice-shop | owner_match | Unknown lookup table or id column |
| 4e0c68cd981acbfe4a95 | juice-shop | owner_or_admin | Unknown lookup table or id column |
| fbe864fbd2d924117550 | juice-shop | role_required | Unknown lookup table or id column |
| 6c5807ef29707164f73b | juice-shop | owner_match | Unknown lookup table or id column |
| b036005643c333b5e7ae | Pixi | public | Unknown lookup table or id column |
| 6309b77a47e9b994f9fe | Pixi | owner_match | Unknown lookup table or id column |

## c: 검증 실패 분해

| 사유 | 건수 |
|---|---:|
| Unknown lookup table or id column | 6 |

검증 보류의 사람 정답: `{"owner_match": 5, "owner_or_admin": 1}`.
검증 보류 중 ERD가 비어 있는 건수: 6/6.

아래 목록은 검증에서 보류로 바뀐 것으로 식별된 사례다. 원래 세부 label을 알 수 없어 정답이 오답으로 바뀐 건수라고 해석하면 안 된다.

| id | service | 사람 정답 | 검증 사유 |
|---|---|---|---|
| d0afe4b052514b189dfa | crAPI | owner_match | Unknown lookup table or id column |
| 7ff76e2ecef4c5c31665 | juice-shop | owner_or_admin | Unknown lookup table or id column |
| be9b12fb6e4c31c1d823 | juice-shop | owner_match | Unknown lookup table or id column |
| 93b3678d43a24b94f1c3 | Pixi | owner_match | Unknown lookup table or id column |
| 6309b77a47e9b994f9fe | Pixi | owner_match | Unknown lookup table or id column |
| ffe188e6f24418c23676 | DVWS-node | owner_match | Unknown lookup table or id column |
