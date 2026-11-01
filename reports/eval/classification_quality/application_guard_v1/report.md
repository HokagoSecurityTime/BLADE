# 원래 라벨 보존 · 자동 적용 검증기

기존 30건 × 두 입력 조건의 예측을 재사용했다. API 호출 0회. 라벨·confidence는 변경하지 않고 별도 guard 필드에 결과를 기록한다.

| 입력 | 의미 일치 | 필수 조건 누락/허용 확대 | 과도한 제한 | 보류/비정상 라벨 | 올바른 구체 라벨 오차단 | 틀린 구체 라벨 통과 |
|---|---:|---:|---:|---:|---:|---:|
| code | 12 | 7 | 2 | 9 | 0/12 | 0 |
| code_conditions | 12 | 13 | 2 | 3 | 0/12 | 0 |

## 판정 방식과 한계

코드에서 허용 조건을 제한된 AST 문법으로 추출하고, 라벨이 나타내는 조건과 64개 상태에서 비교한다. 제안은 허용하지만 코드가 거부하는 상태를 반례로 저장한다. 코드가 허용하지만 제안이 거부하는 경우도 별도로 차단한다. 정답 라벨은 차단 판정에 사용하지 않는다.

이 결과는 15개 합성 정책 × 두 문법 변형의 개발 실험이다. 모든 조건이 확보되었다는 fixture 전제와 operator/admin 역할·소유자·그룹 바인딩을 사용한다. 외부 코드의 전체 호출 경로 확보나 실제 정책 파라미터 검증을 증명하지 않는다. 미지원 코드·확인되지 않은 입력 바인딩은 통과시키지 않는다.

semantic_candidate_pass는 의미 동등성 검사 결과일 뿐이다. 실제 집행 바인딩을 검증하지 않았으므로 auto_apply_allowed는 전부 false다. 특히 현재 런타임의 membership 등급 비교는 대상 그룹 구성원 검사를 구현하지 않는다. 런타임 연결·정책 활성화는 하지 않았다. 구현된 검사와 의도된 정책의 일치도 별도 검증이 필요하다.

## 차단 반례

m=그룹 구성원, t=동일 테넌트, o=소유자, r=operator, a=admin, p=premium. 인증된 요청 상태의 비교이며 public은 별도의 명시적 익명 fixture이다.

| 입력 | ID | 원래 라벨 | 차단 사유 | 반례 |
|---|---|---|---|---|
| code | boundary-10-0 | membership_required | overrestriction | {"m": false, "t": true, "o": false, "r": false, "a": false, "p": false} |
| code | boundary-10-1 | membership_required | overrestriction | {"m": false, "t": true, "o": false, "r": false, "a": false, "p": false} |
| code | boundary-09-0 | owner_or_admin | missing_required_condition | {"m": false, "t": false, "o": false, "r": false, "a": true, "p": false} |
| code | boundary-13-0 | membership_required | missing_required_condition | {"m": true, "t": false, "o": false, "r": false, "a": false, "p": false} |
| code | boundary-06-0 | membership_required | missing_required_condition | {"m": true, "t": false, "o": false, "r": false, "a": false, "p": false} |
| code | boundary-06-1 | membership_required | missing_required_condition | {"m": true, "t": false, "o": false, "r": false, "a": false, "p": false} |
| code | boundary-13-1 | membership_required | missing_required_condition | {"m": true, "t": false, "o": false, "r": false, "a": false, "p": false} |
| code | boundary-07-0 | owner_match | missing_required_condition | {"m": false, "t": false, "o": true, "r": false, "a": false, "p": false} |
| code | boundary-07-1 | owner_match | missing_required_condition | {"m": false, "t": false, "o": true, "r": false, "a": false, "p": false} |
| code_conditions | boundary-07-1 | owner_match | missing_required_condition | {"m": false, "t": false, "o": true, "r": false, "a": false, "p": false} |
| code_conditions | boundary-09-1 | owner_or_admin | missing_required_condition | {"m": false, "t": false, "o": false, "r": false, "a": true, "p": false} |
| code_conditions | boundary-10-0 | membership_required | overrestriction | {"m": false, "t": true, "o": false, "r": false, "a": false, "p": false} |
| code_conditions | boundary-14-1 | membership_required | missing_required_condition | {"m": true, "t": false, "o": false, "r": false, "a": false, "p": false} |
| code_conditions | boundary-07-0 | owner_match | missing_required_condition | {"m": false, "t": false, "o": true, "r": false, "a": false, "p": false} |
| code_conditions | boundary-09-0 | owner_or_admin | missing_required_condition | {"m": false, "t": false, "o": false, "r": false, "a": true, "p": false} |
| code_conditions | boundary-11-0 | owner_or_admin | missing_required_condition | {"m": false, "t": false, "o": false, "r": false, "a": true, "p": false} |
| code_conditions | boundary-06-0 | membership_required | missing_required_condition | {"m": true, "t": false, "o": false, "r": false, "a": false, "p": false} |
| code_conditions | boundary-11-1 | owner_or_admin | missing_required_condition | {"m": false, "t": false, "o": false, "r": false, "a": true, "p": false} |
| code_conditions | boundary-08-0 | membership_required | missing_required_condition | {"m": true, "t": false, "o": false, "r": false, "a": false, "p": false} |
| code_conditions | boundary-13-1 | membership_required | missing_required_condition | {"m": true, "t": false, "o": false, "r": false, "a": false, "p": false} |
| code_conditions | boundary-10-1 | membership_required | overrestriction | {"m": false, "t": true, "o": false, "r": false, "a": false, "p": false} |
| code_conditions | boundary-06-1 | membership_required | missing_required_condition | {"m": true, "t": false, "o": false, "r": false, "a": false, "p": false} |
| code_conditions | boundary-13-0 | membership_required | missing_required_condition | {"m": true, "t": false, "o": false, "r": false, "a": false, "p": false} |
| code_conditions | boundary-08-1 | membership_required | missing_required_condition | {"m": true, "t": false, "o": false, "r": false, "a": false, "p": false} |
