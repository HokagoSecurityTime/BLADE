# 외부 코드 바인딩 어댑터 v1

기존 실험을 개발셋으로 사용했다. 새 독립 성능 평가가 아니다. API 재호출 없이 원래 예측을 보존했다.

23개 중 8개 핸들러의 객체 바인딩·허용 조건을 추출했다. 나머지는 미확정이다. 원본 해시가 달라지면 실행을 거부한다. 범용 Python 파서가 아니라 검토한 고정 소스용 어댑터다.

| 조건 | 검증 결과 | 건수 |
|---|---|---:|
| oas | unresolved_source | 15 |
| oas | prediction_validation_failed | 1 |
| oas | missing_required_condition | 2 |
| oas | equivalent | 1 |
| oas | overrestriction | 2 |
| oas | manual_or_invalid_label | 2 |
| oas_code | unresolved_source | 15 |
| oas_code | missing_required_condition | 4 |
| oas_code | equivalent | 4 |

## 추출한 조건

| 핸들러 | 허용 조건 | 객체 조회 |
|---|---|---|
| items.read_item | `((True and not (((not admin) and (not owner)))))` | `{'model': 'Item', 'parameter': 'id', 'variable': 'item', 'file': 'backend/app/api/routes/items.py', 'line': 53}` |
| items.update_item | `((True and not (((not admin) and (not owner)))))` | `{'model': 'Item', 'parameter': 'id', 'variable': 'item', 'file': 'backend/app/api/routes/items.py', 'line': 86}` |
| items.delete_item | `((True and not (((not admin) and (not owner)))))` | `{'model': 'Item', 'parameter': 'id', 'variable': 'item', 'file': 'backend/app/api/routes/items.py', 'line': 106}` |
| login.test_token | `(owner and (True))` | `authenticated self` |
| users.read_user_me | `(owner and (True))` | `authenticated self` |
| users.delete_user_me | `(owner and ((True and not (admin))))` | `authenticated self` |
| users.read_user_by_id | `((True and owner) or ((True and not (owner)) and not ((not admin))))` | `{'model': 'User', 'parameter': 'user_id', 'variable': 'user', 'file': 'backend/app/api/routes/users.py', 'line': 169}` |
| users.delete_user | `(((True and not ((not admin)))) and ((True and not (owner))))` | `{'model': 'User', 'parameter': 'user_id', 'variable': 'user', 'file': 'backend/app/api/routes/users.py', 'line': 221}` |

NOT superuser와 target != caller를 보존하며, 조기 반환은 OR 경로로 반영한다. 인증 사용자 반환을 그룹 membership으로 해석하지 않는다. role_required는 실제 역할 파라미터가 없어 미확정 처리한다.

의미 통과와 실제 자동 적용은 다르다. 집행 설정·DB/JWT 통합 검증이 없어 auto_apply_allowed는 전부 false다. 코드의 현재 검사와 의도된 정책 일치를 입증하지 않는다. 기존 검증기·프롬프트·고정 test·런타임을 변경하지 않았다.
