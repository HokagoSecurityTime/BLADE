# v2.9 새 경계 사례 30건: 추출 조건식 효과

동일 프롬프트·동일 모델·동일 코드에 추출 허용 조건식만 추가했다. 모델의 최종 라벨을 변경하지 않았다.

| 조건 | 계약 일치 | macro-F1 | 복합 정책을 구체 라벨로 축약 |
|---|---:|---:|---:|
| code | 21/30 | 0.7905 | 7/16 |
| code_conditions | 15/30 | 0.6800 | 13/16 |

## 해석 범위

15개 정책 템플릿 × 코드 표현 2종이다. 독립 정책 30개가 아니다. 기존 8건의 파일·ID는 사용하지 않지만 단일 조건 의미는 일부 겹친다. 새 프로젝트 또는 독립 외부 평가셋이 아니다. 동일 제작자가 합성 계약과 구현을 작성했다.

조건식은 AST의 반환·거부 분기에서 추출하고 별칭 확장과 De Morgan 변환을 수행했다. 30×64=1,920개 조합에서 원본 함수·추출식·별도 계약 논리의 판정을 비교했다. 기존 8건과 달리 복합 조건을 의도적으로 많이 포함하므로 이전 7/8과 직접 점수 비교하지 않는다.

복합 계약을 구체 라벨로 축약한 건수는 계약 불일치 위험 지표다. 실제 운영에서 권한이 확대됐음을 입증한 수치는 아니다. runtime에는 반영하지 않았다. 양 조건은 seed 42로 섞어 동시성 4로 실행했고 각 1회이며 반복 실행 안정성은 측정하지 않았다. 오류는 보류 정답으로 처리하지 않는다.

## 사례별 비교

| 사례 | 계약 | 코드 | 코드+조건 |
|---|---|---|---|
| boundary-00-0 | membership_required | membership_required | membership_required |
| boundary-00-1 | membership_required | membership_required | membership_required |
| boundary-01-0 | tenant_match | tenant_match | tenant_match |
| boundary-01-1 | tenant_match | tenant_match | tenant_match |
| boundary-02-0 | owner_match | owner_match | owner_match |
| boundary-02-1 | owner_match | owner_match | owner_match |
| boundary-03-0 | role_required | role_required | role_required |
| boundary-03-1 | role_required | role_required | role_required |
| boundary-04-0 | owner_or_admin | owner_or_admin | owner_or_admin |
| boundary-04-1 | owner_or_admin | owner_or_admin | owner_or_admin |
| boundary-05-0 | public | public | public |
| boundary-05-1 | public | public | public |
| boundary-06-0 | manual_review_required | membership_required | membership_required |
| boundary-06-1 | manual_review_required | membership_required | membership_required |
| boundary-07-0 | manual_review_required | owner_match | owner_match |
| boundary-07-1 | manual_review_required | owner_match | owner_match |
| boundary-08-0 | manual_review_required | manual_review_required | membership_required |
| boundary-08-1 | manual_review_required | manual_review_required | membership_required |
| boundary-09-0 | manual_review_required | owner_or_admin | owner_or_admin |
| boundary-09-1 | manual_review_required | manual_review_required | owner_or_admin |
| boundary-10-0 | manual_review_required | membership_required | membership_required |
| boundary-10-1 | manual_review_required | membership_required | membership_required |
| boundary-11-0 | manual_review_required | manual_review_required | owner_or_admin |
| boundary-11-1 | manual_review_required | manual_review_required | owner_or_admin |
| boundary-12-0 | manual_review_required | manual_review_required | manual_review_required |
| boundary-12-1 | manual_review_required | manual_review_required | manual_review_required |
| boundary-13-0 | manual_review_required | membership_required | membership_required |
| boundary-13-1 | manual_review_required | membership_required | membership_required |
| boundary-14-0 | manual_review_required | manual_review_required | manual_review_required |
| boundary-14-1 | manual_review_required | manual_review_required | membership_required |

## 원본 및 재현

contracts.json은 모델에게 전달하지 않은 계약·검사 논리, inputs.jsonl은 두 조건의 실제 입력, 각 폴더의 predictions.jsonl·usage.jsonl은 원시 예측과 사용량이다. raw_responses.jsonl은 API 응답 전체다. manifest에는 모델·프롬프트·입력·계약 해시를 기록했다. 기존 membership 런타임은 그룹 관계를 집행하지 못하므로 새 의미 결과 자동 적용은 금지한다.
