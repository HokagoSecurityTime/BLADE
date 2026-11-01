# v2.9 고정 · 새 외부 프로젝트 OAS/코드 비교

**새 프로젝트 1개, 엔드포인트 23개를 두 입력 조건으로 실행했다. 분류 결과와 적용 검증 결과를 분리했다. 고정 검증기는 외부 코드·바인딩을 지원하지 않아 23/23건 평가 불가이며, 모두 적용 보류다. 이는 위험 탐지 성공률 100%를 뜻하지 않는다.**

출처: [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template/tree/b1125d8839482cb7bbae603ddc6d0081bf87532e). 이전 실험 수집 manifest/스크립트 검색에서 이 프로젝트 사용 기록이 없었다. 같은 프레임워크 일반화 검증이며, 다중 프로젝트·6종 전체 평가가 아니다.

## 고정 조건

v2.9 프롬프트·application_guard.py 해시는 수집 전에 protocol.json에 고정했다. 모델 gpt-4o-mini, temperature 0, seed 42, 조건별 1회, 동시 요청 4개다. 대상 ID·입력·에이전트 참조 라벨은 API 실행 전에 해시로 고정했다. 조건별 ID는 같다. 원시 응답과 원래 라벨을 보존했다.

저장소에 OpenAPI 파일이 없어 라우트 선언·docstring·응답 필드로 만든 **정적 OAS 투영본**을 사용했다. 실제 서버 export와 동일하다고 주장하지 않는다. 타입/본문 스키마는 완전하지 않다. 익명 경로에 임의 security: []를 추가하지 않았으며, 인증 없는 경로의 security_state는 unknown이다. 코드 조건에는 실제 핸들러·참조 함수·모델·라우터 등록과 전역 middleware를 추가했다. 정답·검수 설명·테스트 코드는 모델 입력에 넣지 않았다. private 경로 1개는 개발 환경 전용임을 기록했다.

## 분류 결과 — 사람 정답 정확도가 아닌 코드 검토 참조 일치율

의도된 정책 원문, 구현 검사, 근거 확보 여부를 references.json에 분리했다. 독립 명시 정책이 부족하므로 의도 라벨은 확정하지 않았다. 평가 가능한 19건의 라벨은 에이전트의 소스·테스트 검토 참조이며, 미확정 4건을 manual 정답으로 채우지 않았다.

| 입력 | 참조 일치 | macro-F1(지원 라벨) | macro-F1(7종) | 모델 보류 | 평균 ms |
|---|---:|---:|---:|---:|---:|
| oas | 7/19 (36.8%) | 0.3091 | 0.2208 | 43.5% | 1470 |
| oas_code | 15/19 (78.9%) | 0.6921 | 0.4943 | 8.7% | 1604 |

분모에서 빠진 4건은 목록 행 필터링, 새 객체 생성, reset-token capability, 개발 전용 등록이다. tenant/membership 정답 사례가 없어 이 두 라벨의 성능은 측정할 수 없다. 지원 라벨 macro-F1은 참조 support가 있는 5종 평균이며, 7종 평균에서는 support 없는 라벨 F1을 0으로 둔다.

### oas: 라벨별 지표

| 라벨 | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 4 | 0.600 | 0.750 | 0.667 |
| role_required | 5 | 1.000 | 0.200 | 0.333 |
| membership_required | 0 | 0.000 | 0.000 | 0.000 |
| tenant_match | 0 | 0.000 | 0.000 | 0.000 |
| owner_match | 4 | 0.429 | 0.750 | 0.545 |
| owner_or_admin | 4 | 0.000 | 0.000 | 0.000 |
| manual_review_required | 2 | 0.000 | 0.000 | 0.000 |

혼동행렬(행=참조, 열=예측):

| 참조 / 예측 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required | output_error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| public | 3 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| role_required | 1 | 1 | 0 | 0 | 0 | 0 | 3 | 0 |
| membership_required | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| owner_match | 1 | 0 | 0 | 0 | 3 | 0 | 0 | 0 |
| owner_or_admin | 0 | 0 | 0 | 0 | 2 | 0 | 2 | 0 |
| manual_review_required | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
### oas_code: 라벨별 지표

| 라벨 | support | P | R | F1 |
|---|---:|---:|---:|---:|
| public | 4 | 1.000 | 1.000 | 1.000 |
| role_required | 5 | 1.000 | 1.000 | 1.000 |
| membership_required | 0 | 0.000 | 0.000 | 0.000 |
| tenant_match | 0 | 0.000 | 0.000 | 0.000 |
| owner_match | 4 | 0.667 | 0.500 | 0.571 |
| owner_or_admin | 4 | 0.800 | 1.000 | 0.889 |
| manual_review_required | 2 | 0.000 | 0.000 | 0.000 |

혼동행렬(행=참조, 열=예측):

| 참조 / 예측 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required | output_error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| public | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| role_required | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| membership_required | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| owner_match | 0 | 0 | 2 | 0 | 2 | 0 | 0 | 0 |
| owner_or_admin | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 |
| manual_review_required | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 |

## 검증기 결과

| 입력 | 평가 불가 | 올바른 구체 제안도 보류 | 별도 소스 감사에서 허용 확대 | 검증기의 구체 누락 탐지 | 자동 적용 |
|---|---:|---:|---:|---:|---:|
| oas | 23/23 | 7/7 | 0 | 0/0 | 0 |
| oas_code | 23/23 | 15/15 | 0 | 0/0 | 0 |

0/0은 N/A다. 지원 영역에서의 오차단율은 지원 표본 0건이므로 N/A다. 운영 관점에서는 올바른 구체 제안도 모두 보류되는 적용 손실이 있다. 허용 확대 보조 감사는 실제 핸들러 본문 검증을 수행한 item 조회·수정·삭제와 user-by-id 4개 경계에 한정한다. public/tenant/membership 제안이 비소유자·비관리자를 허용할 수 있는 반례를 확인한다. 특정 역할 바인딩 없는 role_required 등의 안전성을 추정하지 않는다. 나머지 경로의 위험 검출률로 일반화하지 않는다. 모든 요청 보류를 특정 필수 조건 누락 탐지로 세지 않았다.

## 검증 범위

원본 함수 본문을 사용한 로컬 handler/dependency 검사 22건 통과. DB 세션·객체는 대역이며 로그인/JWT/PostgreSQL/전체 HTTP 통합 검증이 아니다. 원본 upstream 테스트는 수집·정적으로 확인했지만 실행하지 않았다. 런타임·기존 test·train은 수정하지 않았다.

## 전체 결과

| ID | 참조 | OAS | OAS+코드 | 근거 상태 |
|---|---|---|---|---|
| items.read_items | 미확정 | manual_review_required | membership_required | unresolved |
| items.read_item | owner_or_admin | owner_match | owner_or_admin | agent_source_review |
| items.create_item | 미확정 | manual_review_required | membership_required | unresolved |
| items.update_item | owner_or_admin | manual_review_required | owner_or_admin | agent_source_review |
| items.delete_item | owner_or_admin | manual_review_required | owner_or_admin | agent_source_review |
| login.login_access_token | public | public | public | agent_source_review |
| login.test_token | owner_match | public | membership_required | agent_source_review |
| login.recover_password | public | manual_review_required | public | agent_source_review |
| login.reset_password | 미확정 | manual_review_required | manual_review_required | unresolved |
| login.recover_password_html_content | role_required | manual_review_required | role_required | agent_source_review |
| private.create_user | 미확정 | manual_review_required | manual_review_required | unresolved |
| users.read_users | role_required | public | role_required | agent_source_review |
| users.create_user | role_required | role_required | role_required | agent_source_review |
| users.update_user_me | owner_match | owner_match | owner_match | agent_source_review |
| users.update_password_me | owner_match | owner_match | owner_match | agent_source_review |
| users.read_user_me | owner_match | owner_match | membership_required | agent_source_review |
| users.delete_user_me | manual_review_required | owner_match | owner_match | agent_source_review |
| users.register_user | public | public | public | agent_source_review |
| users.read_user_by_id | owner_or_admin | owner_match | owner_or_admin | agent_source_review |
| users.update_user | role_required | manual_review_required | role_required | agent_source_review |
| users.delete_user | manual_review_required | owner_match | owner_or_admin | agent_source_review |
| utils.test_email | role_required | manual_review_required | role_required | agent_source_review |
| utils.health_check | public | public | public | agent_source_review |

API 응답 47회, 입력 87,862토큰, 출력 3,494토큰. 실제 결제 금액은 이 보고서에서 추정하지 않았다.

## 판단

현재 고정 검증기는 외부 환경에 바로 적용할 수 없다. 안전하게 보류하지만 활용률이 0이다. 다음 개발 과제는 원래 코드→조건/객체 바인딩 어댑터이며, 이 데이터는 이후 어댑터 개발에 쓰면 개발셋으로 취급해야 한다. 프롬프트와 검증기를 결과에 맞춰 이번 실행 도중 고치지 않았다. 새 어댑터의 효과는 별도 버전과 다른 프로젝트로 측정해야 한다.

원자료: inputs.json, references.json, handler_checks.json, raw_responses.jsonl, predictions.jsonl, guard_decisions.json, metrics.json, protocol.json, execution_manifest.json.
