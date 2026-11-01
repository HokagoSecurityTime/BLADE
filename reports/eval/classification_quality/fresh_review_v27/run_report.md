# v2.7 100건 예측 실행 결과

사람 검수 전이므로 정확도·F1은 미측정이다. 모델 예측은 검수표와 분리해 저장했다.

| label | 건수 |
|---|---:|
| public | 16 |
| role_required | 57 |
| membership_required | 3 |
| tenant_match | 1 |
| owner_match | 2 |
| owner_or_admin | 0 |
| manual_review_required | 21 |

오류 0건; evidence_invalid 0건.

입력 ID와 사람 검수 근거는 기존 100건과 동일하다. security_details는 허용 근거 필드인 description에 출처를 표시해 전달했다. 기존 라벨·고정 test·런타임·학습 데이터는 수정하지 않았다.
