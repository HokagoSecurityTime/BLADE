# v2.6·v2.7·v2.8 동일 100건 예측 비교

사람 정답이 미확정이므로 정확도와 macro-F1은 측정하지 않았다.
동일 ID 순서·입력 해시·모델·temperature를 manifest로 확인했다. 코드 근거를 새로 추가하지 않은 기존 OAS 표본이다.

| label | v2.6 | v2.7 | v2.8 |
|---|---:|---:|---:|
| public | 3 | 16 | 32 |
| role_required | 20 | 57 | 19 |
| membership_required | 10 | 3 | 6 |
| tenant_match | 5 | 1 | 5 |
| owner_match | 24 | 2 | 14 |
| owner_or_admin | 1 | 0 | 2 |
| manual_review_required | 37 | 21 | 22 |

| 검증 | v2.6 | v2.7 | v2.8 |
|---|---:|---:|---:|
| 출력 오류 | 0 | 0 | 0 |
| evidence_invalid | 1 | 0 | 1 |

v2.7 대비 라벨 변경 49건, 유지 51건.

## v2.7 → v2.8 전이

예측 간 전이이며 사람 정답 기준 혼동행렬이 아니다.

| v2.7 / v2.8 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 15 | 0 | 0 | 0 | 1 | 0 | 0 |
| role_required | 7 | 19 | 6 | 4 | 11 | 2 | 8 |
| membership_required | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| owner_match | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| owner_or_admin | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| manual_review_required | 7 | 0 | 0 | 0 | 0 | 0 | 14 |

## 해석 범위

- v2.8은 대상·관계·조건·구현·출처 확인, 구현과 의도 구분, 인접 라벨 배제 이유를 추가했다.
- 이 실행은 프롬프트 변경 실험이다. 새 코드 데이터의 효과나 코드 기반 판단 성능을 측정하지 않았다.
- 보류율 감소나 역할 라벨 감소만으로 정확도 개선을 주장하지 않는다.
- evidence_invalid는 필드 인용 검사이며 근거의 의미적 타당성을 보증하지 않는다.
- 여러 규칙을 함께 바꾼 단일 실행이므로 개별 규칙의 인과 효과를 분리하지 않는다.
- 기존 test·학습 데이터·런타임은 변경하지 않았다.

재현 자료: 각 fresh_review 폴더의 predictions.manifest.json, model_predictions.jsonl, usage.jsonl.
v2.8 사람 검수표: [review_100_v28.md](fresh_review_v28/review_100_v28.md).
