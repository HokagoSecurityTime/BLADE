# 검사 조건 추출·라벨 매핑 실험

기존 v2.8 프롬프트와 런타임을 바꾸지 않은 제한적 Python 정적 분석 실험이다. 추가 API 호출은 0회다.

| 방법 | 합성 계약 일치 / 14 | macro-F1 |
|---|---:|---:|
| 기존 v2.8 LLM + 코드 | 8 | 0.5333 |
| 조건 추출 + 규칙 매핑 | 14 | 1.0000 |

추출한 조건식의 허용/거부 결과: 84/84 계약 검사 일치. 기존 HTTP 98개 검사는 별도 기록에 보존했다. 조건식 검사와 라벨 매핑 점수를 구분한다.

## 처리 방식

- HTTPException(403) 거부 조건을 논리적으로 반전하여 허용식을 만든다. `not owner AND not admin`은 `owner OR admin`이다.
- 순서대로 호출한 두 검사 함수는 AND로 결합한다. owner와 tenant, tenant와 subscription 조건을 하나로 버리지 않는다.
- 반환 객체의 owner 필드만으로는 조건을 만들지 않는다. 인증(401)과 객체 부재(404)는 인가 조건과 분리한다.
- 근거 경로·해시·줄번호·원래 거부식과 허용식을 predictions.json에 기록한다.
- 지원하지 않는 제어 흐름·함수 호출·외부 프레임워크는 보류한다. 불확실한 의도를 구현에서 만들어내지 않는다.

## 적용 범위와 한계

이 추출기는 현재 개발 합성 코드의 Python/HTTPException 및 sub·owner·tenant·role·plan 필드 관례에 맞춘 제한적 구현이다. 일반 변수 별칭, 메서드 호출, DB query 필터, 동적 dispatch, 전역 middleware를 검증하는 범용 분석기가 아니다. 외부 Django 4건은 지원 범위 밖이며 미확정 상태를 유지한다. 기존 14건을 보고 개발했으므로 독립 정확도나 새 모델 성능으로 보고하지 않는다. OAS-only는 명시적 공개 근거 외에 구체 조건을 추측하지 않는 것이 원칙이다. 새 외부 프로젝트와 독립 표본의 검증이 여전히 필요하다.

## 개별 결과

| ID | 라벨 | 사유 | 추출 상태 |
|---|---|---|---|
| controlled-observatory:observations | owner_match | single_condition | 지원 범위 내 |
| controlled-observatory:notebooks | owner_match | single_condition | 지원 범위 내 |
| controlled-observatory:calibrations | owner_or_admin | explicit_owner_or_admin | 지원 범위 내 |
| controlled-observatory:captures | owner_or_admin | explicit_owner_or_admin | 지원 범위 내 |
| controlled-observatory:allocations | tenant_match | single_condition | 지원 범위 내 |
| controlled-observatory:inventories | tenant_match | single_condition | 지원 범위 내 |
| controlled-observatory:queues | role_required | single_condition | 지원 범위 내 |
| controlled-observatory:relays | role_required | single_condition | 지원 범위 내 |
| controlled-observatory:spectra | membership_required | single_condition | 지원 범위 내 |
| controlled-observatory:forecasts | membership_required | single_condition | 지원 범위 내 |
| controlled-observatory:catalog | public | explicit_anonymous_evidence | 지원 범위 내 |
| controlled-observatory:bulletins | public | explicit_anonymous_evidence | 지원 범위 내 |
| controlled-observatory:transfers | manual_review_required | compound_or_unrepresentable_condition | 지원 범위 내 |
| controlled-observatory:reservations | manual_review_required | compound_or_unrepresentable_condition | 지원 범위 내 |
| realworld-django:GET:/articles/{slug} | manual_review_required | unsupported_or_incomplete_code | non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, handler_unresolved |
| realworld-django:PUT:/articles/{slug} | manual_review_required | unsupported_or_incomplete_code | non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, handler_unresolved |
| realworld-django:DELETE:/articles/{slug}/comments/{id} | manual_review_required | unsupported_or_incomplete_code | non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, handler_unresolved |
| realworld-django:GET:/tags | manual_review_required | unsupported_or_incomplete_code | non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, non_top_level_or_incomplete_excerpt, handler_unresolved |
