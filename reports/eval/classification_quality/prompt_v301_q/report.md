# 프롬프트 3.0.1 품질 확인(Q) — 사람 라벨 없는 합성 train 전용 셋

## v3.0 대비 비교 (같은 42건 × 2조건)

입력 동일성: v3.0 inputs SHA `a7b3b87cb08bf143b852966eea678d04b95491758d1e2d1cd2482a2f00d52517` / 현재 inputs SHA `a7b3b87cb08bf143b852966eea678d04b95491758d1e2d1cd2482a2f00d52517` → 동일.

| 버전 / 조건 | v3.0 보정 일치 | 구현 기준 일치 | 취약 변형 15건 public 오판 | 정상 구현 27건 일치 | manual 비율 | macro-F1(보정) |
|---|---:|---:|---:|---:|---:|---:|
| 3.0 / oas | 28.6% | 57.1% | 0 | 9/27 | 100.0% | 0.0741 |
| 3.0 / oas_code | 71.4% | 81.0% | 8 | 27/27 | 38.1% | 0.6873 |
| 3.0.1 / oas | 28.6% | 57.1% | 0 | 9/27 | 100.0% | 0.0741 |
| 3.0.1 / oas_code | 71.4% | 85.7% | 6 | 27/27 | 42.9% | 0.6889 |

oas_code 라벨이 바뀐 건 2건:

| id | v3.0 | 현재 | expected_v30 |
|---|---:|---:|---:|
| orbit_tickets_audit_1 | public | manual_review_required | role_required |
| campus_records_shared_1 | public | manual_review_required | owner_or_admin |

실행 2026-10-21T08:24:32Z, 모델 gpt-4o-mini, temperature 0. 프롬프트 SHA `d0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef`, 입력 SHA `a7b3b87cb08bf143b852966eea678d04b95491758d1e2d1cd2482a2f00d52517`, 검증기 v1 SHA `f77246fc336ac4d7e06e04c77bb665706065dc57f5096e8ad8e29e357860856e`. 사람 교정 미사용, test.jsonl·test 전용 합성 미접근.

API 응답 84회, 입력 222,077토큰(캐시 69,888), 출력 5,866토큰, 사용량 기준 추정 $0.03159 (청구서 아님).

## 확인용 셋

train 전용 합성 3개 서비스(orbit_tickets·copper_wallet·campus_records) 42건. 전 건 intended_labels와 핸들러 코드 보유. 두 입력 조건: `oas`(명세만), `oas_code`(명세 + 핸들러 원문을 description에 포함).

기대 라벨 세 가지를 구분한다.
- **intended**: intended_labels.yaml 원본.
- **expected_v30**: v3.0 정의 보정 — subscription(premium plan) 6건은 manual_review_required.
- **expected_v30_code**: 구현 기준 — archive 변형 15건(vulnerable=true)은 인증만 하고 인가 검사가 없어 코드만으로는 manual_review_required가 v3.0 정답.

## 요약

| 조건 | intended 일치 | expected_v30 일치 | expected_v30_code 일치 | manual 비율 | 평균 ms | 출력 오류 | evidence 오류 |
|---|---:|---:|---:|---:|---:|---:|---:|
| oas | 14.3% | 28.6% | 57.1% | 100.0% | 1684.0 | 0 | 0 |
| oas_code | 57.1% | 71.4% | 85.7% | 42.9% | 1505.5 | 0 | 0 |

중단 기준(60%): oas_code의 expected_v30 일치율 71.4% → **통과**. 기준 선택 근거: agreement_expected_v30 on oas_code (intended label; subscription->manual per v3.0). agreement_intended (raw yaml) and agreement_expected_v30_code (implementation-based) reported alongside for the user decision

oas_code expected_v30 일치율을 변형별로 보면 정상 구현 27건 100.0%, 취약 변형 15건 20.0%.

## oas: label별 P/R/F1 (기준 expected_v30)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 6 | 0.0 | 0.0 | 0.0 |
| role_required | 6 | 0.0 | 0.0 | 0.0 |
| membership_required | 0 | 0.0 | 0.0 | 0.0 |
| tenant_match | 6 | 0.0 | 0.0 | 0.0 |
| owner_match | 6 | 0.0 | 0.0 | 0.0 |
| owner_or_admin | 6 | 0.0 | 0.0 | 0.0 |
| manual_review_required | 12 | 0.2857 | 1.0 | 0.4444 |

macro-F1(support 있는 6종: public, role_required, tenant_match, owner_match, owner_or_admin, manual_review_required) = 0.0741

혼동행렬:

| 정답 \ 예측 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required | output_error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| public | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| role_required | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| membership_required | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| owner_match | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| owner_or_admin | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| manual_review_required | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 0 |

confidence 구간: {'[0,0.5]': 0, '(0.5,0.7)': 0, '[0.7,0.9)': 42, '[0.9,1]': 0}

## oas_code: label별 P/R/F1 (기준 expected_v30)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 6 | 0.5 | 1.0 | 0.6667 |
| role_required | 6 | 1.0 | 0.5 | 0.6667 |
| membership_required | 0 | 0.0 | 0.0 | 0.0 |
| tenant_match | 6 | 1.0 | 0.5 | 0.6667 |
| owner_match | 6 | 1.0 | 0.5 | 0.6667 |
| owner_or_admin | 6 | 1.0 | 0.5 | 0.6667 |
| manual_review_required | 12 | 0.6667 | 1.0 | 0.8 |

macro-F1(support 있는 6종: public, role_required, tenant_match, owner_match, owner_or_admin, manual_review_required) = 0.6889

혼동행렬:

| 정답 \ 예측 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required | output_error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| public | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| role_required | 1 | 3 | 0 | 0 | 0 | 0 | 2 | 0 |
| membership_required | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| tenant_match | 2 | 0 | 0 | 3 | 0 | 0 | 1 | 0 |
| owner_match | 1 | 0 | 0 | 0 | 3 | 0 | 2 | 0 |
| owner_or_admin | 2 | 0 | 0 | 0 | 0 | 3 | 1 | 0 |
| manual_review_required | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 0 |

### oas_code: 기준 expected_v30_code(구현 기준)

| label | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 6 | 0.5 | 1.0 | 0.6667 |
| role_required | 3 | 1.0 | 1.0 | 1.0 |
| membership_required | 0 | 0.0 | 0.0 | 0.0 |
| tenant_match | 3 | 1.0 | 1.0 | 1.0 |
| owner_match | 3 | 1.0 | 1.0 | 1.0 |
| owner_or_admin | 3 | 1.0 | 1.0 | 1.0 |
| manual_review_required | 24 | 1.0 | 0.75 | 0.8571 |

macro-F1(support 있는 6종: public, role_required, tenant_match, owner_match, owner_or_admin, manual_review_required) = 0.9206

confidence 구간: {'[0,0.5]': 0, '(0.5,0.7)': 0, '[0.7,0.9)': 18, '[0.9,1]': 24}

## 적용 검증기 v1 (oas_code 결과에 적용)

| 검증기 판정 | 건수 |
|---|---:|
| equivalent | 15 |
| manual_or_invalid_label | 18 |
| context_or_binding_unverified | 6 |
| missing_required_condition | 3 |

| 코드→fixture 변환 상태 | 건수 |
|---|---:|
| anonymous_allow | 6 |
| translated | 15 |
| authenticated_no_authorization_guard | 15 |
| deny_all | 6 |

올바른 구체 라벨(구현 기준) 18건 중 차단 3건, 틀린 구체 라벨 통과 0건.

한계: (1) 검증기 v1 fixture 문법에는 "인증만" 상태가 없어 취약 변형 15건은 평가 불가(보류). (2) v1은 role_required를 operator 역할 원자에 고정하므로 admin 역할을 요구하는 audit 건은 올바른 role_required도 차단으로 표시된다. 변환기(bridge)는 합성 세 템플릿 전용이며 검증기 코드는 수정하지 않았다.

## 알려진 한계 (사용자 확인 2026-10-21)

코드 입력 시 인증만 있고 인가 검사 없는 핸들러를 public으로 오판(6/15). 인증이 핸들러 밖(데코레이터·의존성)에 있을 때 발생 추정. 이번 단계에서는 허용하며 프롬프트는 v3.0.1로 고정한다.

## 전체 결과

| id | vulnerable | intended | expected_v30 | expected_v30_code | oas | oas_code | conf(oas_code) | 검증기 |
|---|---|---|---|---|---|---|---:|---|
| orbit_tickets_catalogue_0 | False | public | public | public | manual_review_required | public | 0.9 | equivalent |
| orbit_tickets_catalogue_1 | False | public | public | public | manual_review_required | public | 0.9 | equivalent |
| orbit_tickets_drafts_0 | False | owner_match | owner_match | owner_match | manual_review_required | owner_match | 0.9 | equivalent |
| orbit_tickets_drafts_1 | True | owner_match | owner_match | manual_review_required | manual_review_required | manual_review_required | 0.85 | manual_or_invalid_label |
| orbit_tickets_shared_0 | False | owner_or_admin | owner_or_admin | owner_or_admin | manual_review_required | owner_or_admin | 0.9 | equivalent |
| orbit_tickets_shared_1 | True | owner_or_admin | owner_or_admin | manual_review_required | manual_review_required | public | 0.9 | context_or_binding_unverified |
| orbit_tickets_workspace_0 | False | tenant_match | tenant_match | tenant_match | manual_review_required | tenant_match | 0.9 | equivalent |
| orbit_tickets_workspace_1 | True | tenant_match | tenant_match | manual_review_required | manual_review_required | public | 0.9 | context_or_binding_unverified |
| orbit_tickets_audit_0 | False | role_required | role_required | role_required | manual_review_required | role_required | 0.9 | missing_required_condition |
| orbit_tickets_audit_1 | True | role_required | role_required | manual_review_required | manual_review_required | manual_review_required | 0.85 | manual_or_invalid_label |
| orbit_tickets_subscription_0 | False | membership_required | manual_review_required | manual_review_required | manual_review_required | manual_review_required | 0.85 | manual_or_invalid_label |
| orbit_tickets_subscription_1 | True | membership_required | manual_review_required | manual_review_required | manual_review_required | manual_review_required | 0.85 | manual_or_invalid_label |
| orbit_tickets_disputed_0 | False | manual_review_required | manual_review_required | manual_review_required | manual_review_required | manual_review_required | 0.8 | manual_or_invalid_label |
| orbit_tickets_disputed_1 | False | manual_review_required | manual_review_required | manual_review_required | manual_review_required | manual_review_required | 0.8 | manual_or_invalid_label |
| copper_wallet_catalogue_0 | False | public | public | public | manual_review_required | public | 0.9 | equivalent |
| copper_wallet_catalogue_1 | False | public | public | public | manual_review_required | public | 0.9 | equivalent |
| copper_wallet_drafts_0 | False | owner_match | owner_match | owner_match | manual_review_required | owner_match | 0.9 | equivalent |
| copper_wallet_drafts_1 | True | owner_match | owner_match | manual_review_required | manual_review_required | public | 0.9 | context_or_binding_unverified |
| copper_wallet_shared_0 | False | owner_or_admin | owner_or_admin | owner_or_admin | manual_review_required | owner_or_admin | 0.9 | equivalent |
| copper_wallet_shared_1 | True | owner_or_admin | owner_or_admin | manual_review_required | manual_review_required | public | 0.9 | context_or_binding_unverified |
| copper_wallet_workspace_0 | False | tenant_match | tenant_match | tenant_match | manual_review_required | tenant_match | 0.9 | equivalent |
| copper_wallet_workspace_1 | True | tenant_match | tenant_match | manual_review_required | manual_review_required | public | 0.9 | context_or_binding_unverified |
| copper_wallet_audit_0 | False | role_required | role_required | role_required | manual_review_required | role_required | 0.9 | missing_required_condition |
| copper_wallet_audit_1 | True | role_required | role_required | manual_review_required | manual_review_required | public | 0.9 | context_or_binding_unverified |
| copper_wallet_subscription_0 | False | membership_required | manual_review_required | manual_review_required | manual_review_required | manual_review_required | 0.85 | manual_or_invalid_label |
| copper_wallet_subscription_1 | True | membership_required | manual_review_required | manual_review_required | manual_review_required | manual_review_required | 0.85 | manual_or_invalid_label |
| copper_wallet_disputed_0 | False | manual_review_required | manual_review_required | manual_review_required | manual_review_required | manual_review_required | 0.8 | manual_or_invalid_label |
| copper_wallet_disputed_1 | False | manual_review_required | manual_review_required | manual_review_required | manual_review_required | manual_review_required | 0.8 | manual_or_invalid_label |
| campus_records_catalogue_0 | False | public | public | public | manual_review_required | public | 0.9 | equivalent |
| campus_records_catalogue_1 | False | public | public | public | manual_review_required | public | 0.9 | equivalent |
| campus_records_drafts_0 | False | owner_match | owner_match | owner_match | manual_review_required | owner_match | 0.9 | equivalent |
| campus_records_drafts_1 | True | owner_match | owner_match | manual_review_required | manual_review_required | manual_review_required | 0.85 | manual_or_invalid_label |
| campus_records_shared_0 | False | owner_or_admin | owner_or_admin | owner_or_admin | manual_review_required | owner_or_admin | 0.9 | equivalent |
| campus_records_shared_1 | True | owner_or_admin | owner_or_admin | manual_review_required | manual_review_required | manual_review_required | 0.85 | manual_or_invalid_label |
| campus_records_workspace_0 | False | tenant_match | tenant_match | tenant_match | manual_review_required | tenant_match | 0.9 | equivalent |
| campus_records_workspace_1 | True | tenant_match | tenant_match | manual_review_required | manual_review_required | manual_review_required | 0.85 | manual_or_invalid_label |
| campus_records_audit_0 | False | role_required | role_required | role_required | manual_review_required | role_required | 0.9 | missing_required_condition |
| campus_records_audit_1 | True | role_required | role_required | manual_review_required | manual_review_required | manual_review_required | 0.85 | manual_or_invalid_label |
| campus_records_subscription_0 | False | membership_required | manual_review_required | manual_review_required | manual_review_required | manual_review_required | 0.85 | manual_or_invalid_label |
| campus_records_subscription_1 | True | membership_required | manual_review_required | manual_review_required | manual_review_required | manual_review_required | 0.85 | manual_or_invalid_label |
| campus_records_disputed_0 | False | manual_review_required | manual_review_required | manual_review_required | manual_review_required | manual_review_required | 0.8 | manual_or_invalid_label |
| campus_records_disputed_1 | False | manual_review_required | manual_review_required | manual_review_required | manual_review_required | manual_review_required | 0.8 | manual_or_invalid_label |

## 불일치 근거(oas_code, expected_v30 기준)

- **orbit_tickets_drafts_1** 기대 owner_match / 출력 manual_review_required (0.85): description: 객체에 대한 인가 검사가 생략되어 있음; 판단: 접근 조건이 명확하지 않아 보류
- **orbit_tickets_shared_1** 기대 owner_or_admin / 출력 public (0.9): description: 핸들러가 인증·인가 검사 없이 객체를 반환한다; 판단: 익명 허용의 긍정 근거가 코드에 있어 public 선택
- **orbit_tickets_workspace_1** 기대 tenant_match / 출력 public (0.9): description: 핸들러가 인증·인가 검사 없이 객체를 반환한다; 판단: 익명 허용의 긍정 근거가 코드에 있어 public 선택
- **orbit_tickets_audit_1** 기대 role_required / 출력 manual_review_required (0.85): description: 접근 조건에 대한 인가 검사가 없고, 객체에 대한 권한 검사가 생략됨; 판단: 명확한 접근 조건이 없으므로 보류
- **copper_wallet_drafts_1** 기대 owner_match / 출력 public (0.9): description: 핸들러가 인증·인가 검사 없이 객체를 반환한다; 판단: 익명 허용의 긍정 근거가 코드에 있어 public 선택
- **copper_wallet_shared_1** 기대 owner_or_admin / 출력 public (0.9): description: 핸들러가 인증·인가 검사 없이 객체를 반환한다; 판단: 익명 허용의 긍정 근거가 코드에 있어 public 선택
- **copper_wallet_workspace_1** 기대 tenant_match / 출력 public (0.9): description: 핸들러가 인증·인가 검사 없이 객체를 반환한다; 판단: 익명 허용의 긍정 근거가 코드에 있어 public 선택
- **copper_wallet_audit_1** 기대 role_required / 출력 public (0.9): description: 핸들러가 인증·인가 검사 없이 객체를 반환한다; 판단: 익명 허용의 긍정 근거가 코드에 있어 public 선택
- **campus_records_drafts_1** 기대 owner_match / 출력 manual_review_required (0.85): description: 접근 조건에 대한 인가 검사가 없고, 객체 권한 확인이 생략됨; 판단: 명확한 접근 조건이 없으므로 보류
- **campus_records_shared_1** 기대 owner_or_admin / 출력 manual_review_required (0.85): description: 핸들러가 인증 후 객체를 반환하지만 인가 검사가 없으며, 접근 조건이 명확하지 않음; 판단: 인가 조건이 불확정적이므로 보류
- **campus_records_workspace_1** 기대 tenant_match / 출력 manual_review_required (0.85): description: 핸들러가 객체에 대한 인가 검사를 생략하고 있으며, 요청자와 객체의 관계를 확인할 수 있는 조건이 부족하다; 판단: 접근 조건이 명확하지 않아 보류
- **campus_records_audit_1** 기대 role_required / 출력 manual_review_required (0.85): description: 인증 후 객체에 대한 인가 검사가 생략됨; 판단: 접근 조건이 명확하지 않아 보류

원자료: inputs.jsonl, predictions_oas.jsonl, predictions_oas_code.jsonl, raw_responses.jsonl, usage.jsonl, metrics.json, manifest.json, estimate.json.
