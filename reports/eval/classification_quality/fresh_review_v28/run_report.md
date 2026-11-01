# v2.8 100건 예측 실행 결과

사람 검수 전이므로 정확도·F1은 미측정이다. 모델 예측은 검수표와 분리해 저장했다.

| label | 건수 |
|---|---:|
| public | 32 |
| role_required | 19 |
| membership_required | 6 |
| tenant_match | 5 |
| owner_match | 14 |
| owner_or_admin | 2 |
| manual_review_required | 22 |

오류 0건; evidence_invalid 1건.

입력 ID와 사람 검수 근거는 기존 100건과 동일하다. security_details는 허용 근거 필드인 description에 출처를 표시해 전달했다. 기존 라벨·고정 test·런타임·학습 데이터는 수정하지 않았다.
