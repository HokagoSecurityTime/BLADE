# v2.6 · v2.7 동일 100건 비교 보고서

작성일: 2026-10-20

**v2.7에서는 역할 라벨로 판단이 크게 이동했다. 사람 정답이 아직 없어 정확도 개선 여부는 판단할 수 없다.** 규칙과 예시 구성이 함께 바뀌었으므로 단일 변경의 효과로 해석할 수 없다.

## 1. 비교 조건

| 항목 | 공통 조건 |
|---|---|
| 모델 | OpenAI gpt-4o-mini |
| 표본 | 동일 APIs.guru 100개 ID, 78개 서비스 |
| 입력 | 동일 blind_inputs.jsonl; 상세 보안 정의는 description에 출처를 표시해 추가 |
| temperature | 0 |
| 출력 | label, confidence, rationale, evidence_fields |
| 검증 | 실제 필드 인용 검사와 재시도; confidence에 따른 라벨 사후 변환 없음 |
| 사람 정답 | 미확정. 정확도·macro-F1·구체 선택 정확도 미측정 |

두 manifest의 ID 순서·입력 SHA-256·모델·temperature가 일치한다. 여기서는 라벨링 API의 예측을 비교한다. 런타임 정책 검증까지 수행했던 v2.0 베이스라인 253건 평가와는 다르다.

표본은 seed 42, 서비스당 최대 3건, owner/tenant/both/path_only/none 신호 유형별 20건이다. 기존 검수·파일럿·분석 기록 ID를 제외했지만 이전 자동 라벨링 이력은 있다. 모집단 분포를 대표하는 단순 무작위 표본은 아니다.

## 2. 프롬프트 변경점

| 항목 | v2.6 | v2.7 | 해석 |
|---|---|---|---|
| 구성 | v2.5 규칙 + 사람 교정 30개 예시 + 우선 적용 규칙 | 정의·결정 절차·보안·근거·보류 규칙 통합 | 전체 구성 변경 |
| 보류 | 모순 또는 ID·스코프·설명이 모두 없는 경우로 제한. 약한 근거에도 구체 패턴 제안 | 정책 구분 근거 부족, ACL 불명확, 복합 조건도 허용 | ID·설명이 있다는 이유로 구체 선택을 강제하지 않음 |
| owner_match | 사용자 스코프·소유 설명·명확한 소유 컬럼으로 지지 | 요청자와 소유자의 일치가 접근 조건이라는 근거 요구 | owner 후보 컬럼이나 edit 권한 하나만으로 확정하지 않음 |
| tenant_match | 조직 스코프를 단서로 제시 | 요청자와 리소스의 조직 일치 조건을 지지하는 근거 요구 | team/project 경로명만으로 확정하지 않음 |
| role_required | 특정 역할 요구 필요. API 키/JWT 인증만으로 판단 금지 | 같은 원칙 유지, 일반 read/write/manage 기능 scope와 실제 역할을 명시적으로 구분 | 인증과 역할 구분은 기존 규칙을 강화한 것 |
| membership_required | plan/premium/subscription/tier 이용 자격 | 구독·플랜·회원 등급으로 정리. 협업 관계·조직 이름만으로 판단 금지 | 참여 관계와 구독 자격을 구분 |
| owner_or_admin | 개인 소유와 관리자 우회가 함께 명시돼야 함 | 같은 원칙 유지, 계정 owner와 개인 객체 owner 구분 | 단순 단어 공존으로 우회를 추론하지 않음 |
| public·security | 세 가지 security 상태 구분. unknown은 공개 근거 아님 | 기본 원칙 유지, 다른 제한과 충돌하면 보류. 익명 상태 표현의 한계 명시 | mutation은 두 버전 모두 explicitly_anonymous일 때만 public 허용 |
| ACL | 별도의 일관된 ACL 처리 규칙이 충분히 명시되지 않음 | 편집 권한을 소유권·역할로 자동 변환하지 않음 | 특정 패턴을 고를 수 없으면 보류 |
| 복합 조건 | 결정 흐름 중심, 독립 복수 조건 처리 불명확 | 하나로 표현하면 의미가 달라지는 독립 필수 조건은 보류 | 고정 라벨 우선순위 없음 |
| 요청 범위 | endpoint 입력으로 분류 | 해당 method에 적용되는 근거인지 명시적으로 확인 | 변경 권한 설명을 GET에 전용하지 않음 |
| confidence | 근거 강도 구간 사용, 낮다는 이유로 사후 변환 금지 | 같은 원칙 유지, 보류 confidence 의미 명시 | 점수와 정책 판별 가능성을 분리 |
| rationale | 필드와 실제 값 나열 중심 | 필드 근거와 선택·보류 이유 허용 | 값과 해석을 구분 |
| few-shot | 사람 교정 30건 포함 | 예시 0건 | 규칙 변경 효과와 예시 제거 효과를 분리할 수 없음 |
| 집행 가능성 | DB 조회 설정 출력하지 않음 | 의미 라벨과 object_param/owner_lookup 집행 가능성을 명시적으로 분리 | ID 없는 요청을 의미 라벨 자체의 실패로 처리하지 않음 |

원문: [v2.6 프롬프트](../../../training/data/prompts/policy_label_v2.6.md) · [v2.7 프롬프트](../../../training/data/prompts/policy_label_v2.7.md)

## 3. 라벨 분포

| label | v2.6 | v2.7 | 증감 |
|---|---:|---:|---:|
| public | 3 | 16 | +13 |
| role_required | 20 | 57 | +37 |
| membership_required | 10 | 3 | -7 |
| tenant_match | 5 | 1 | -4 |
| owner_match | 24 | 2 | -22 |
| owner_or_admin | 1 | 0 | -1 |
| manual_review_required | 37 | 21 | -16 |
| 합계 | 100 | 100 | 0 |

- 라벨 유지 41건, 변경 59건.
- 보류율 37% → 21%, 구체 라벨 선택률 63% → 79%.
- 출력 오류는 두 버전 모두 0건.
- evidence_invalid는 v2.6 1건, v2.7 0건.

**보류 허용 범위를 넓혔는데 실제 보류는 감소했다.** 규칙의 의도가 모델 출력에 그대로 반영됐다고 볼 수 없다. evidence_invalid=0 역시 인용 필드가 유효하다는 뜻이며, 그 근거가 선택한 라벨을 의미적으로 지지한다는 증명은 아니다.

## 4. 주요 전이

- owner_match → role_required: 21건.
- tenant_match → role_required: 5건.
- membership_required → role_required: 6건.
- manual_review_required → public: 12건.
- 기존 role_required 20건 중 19건이 유지되고 다른 라벨에서 38건이 들어와 총 57건이 됐다.
- 기존 보류 중 17건이 구체 라벨로 바뀌고, 기존 구체 라벨 1건이 보류로 바뀌었다.

아래는 **예측 간 전이표**이며 사람 정답 기준 혼동행렬이 아니다. 행은 v2.6, 열은 v2.7이다.

| v2.6 / v2.7 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 0 | 2 | 1 | 0 | 0 | 0 | 0 |
| role_required | 0 | 19 | 0 | 0 | 0 | 0 | 1 |
| membership_required | 3 | 6 | 0 | 1 | 0 | 0 | 0 |
| tenant_match | 0 | 5 | 0 | 0 | 0 | 0 | 0 |
| owner_match | 1 | 21 | 0 | 0 | 2 | 0 | 0 |
| owner_or_admin | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| manual_review_required | 12 | 3 | 2 | 0 | 0 | 0 | 20 |

## 5. 현재 판단과 한계

**확인된 사실:** 소유·조직 라벨에서 역할 라벨로 크게 이동했고, 보류와 membership 선택은 줄었다.

**미확인 사항:** 역할 집중이 올바른 정책 해석인지, 인증·기능 scope를 역할로 오해한 결과인지. public 증가가 올바른 익명 판단인지. 사람의 독립 검수와 요청별 근거 대조가 필요하다.

**원인으로 단정할 수 없는 것:** 예시 제거, 소유·조직 근거 요건 강화, 보류 규칙 변경 중 어느 요소가 이동을 일으켰는지. 여러 요소를 동시에 바꿨고 조건별 실행은 한 번이다. temperature 0도 완전한 재현성을 입증하지 않는다.

기준이 명확해졌다는 설계상 평가와 모델이 정확해졌다는 실측 평가는 다르다. 현재 결과만으로 v2.7의 성능 우위나 전체 재라벨링을 정당화할 수 없다.

## 6. 다음 검증

1. [v2.7 사람 검수표](fresh_review_v27/review_100_v27.md)를 확정한다. 이미 모델 예측을 본 검수자는 완전한 블라인드가 아니므로 이를 기록한다.
2. 같은 v2.7 사람 정답으로 두 버전의 전체 macro-F1·일치율·보류율·구체 선택률·구체 선택 정확도를 계산한다. 이는 새 기준에 대한 적합성 비교이며 v2.6 당시 기준에 대한 성능과 구분한다.
3. 오답 확인 후 개발 표본에서 규칙 변경과 예시 제거 효과를 분리해 실험한다. 이 100건을 반복 튜닝에 쓰면 이후 독립 평가셋이라고 부르지 않는다.
4. 기존 라벨·고정 test·런타임은 유지한다. 보고서 재작성에는 추가 API 호출이 없다.

## 재현 자료

- [전이 집계 JSON](v26_vs_v27_fresh100.json)
- [v2.6 실행 manifest](fresh_review_v26_control/predictions.manifest.json)
- [v2.7 실행 manifest](fresh_review_v27/predictions.manifest.json)
- [표본 선정 기록](fresh_review_v1/selection_manifest.json)

v2.6 대조 실행 manifest의 standard_sha256은 공통 평가에 사용할 v2.7 검수 기준을 가리킨다. 실제 전송된 모델 프롬프트는 prompt_sha256으로 식별되는 v2.6이다.
