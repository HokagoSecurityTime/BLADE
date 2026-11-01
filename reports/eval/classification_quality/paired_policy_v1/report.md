# v2.8 동일 표본 OAS / OAS+코드 대조

외부 프로젝트 정확도 실험은 아직 성립하지 않았다. 아래 점수는 새 합성 대조군 14건만의 계약 대비 결과다. 외부 4건은 근거 미완성으로 채점하지 않았다.

| 조건 | 정답/14 | macro-F1 | 보류율 | 평균 ms |
|---|---:|---:|---:|---:|
| oas_only | 2 | 0.0408 | 14.3% | 2002 |
| oas_code | 8 | 0.5333 | 0.0% | 1654 |

## 설계와 검증

- 의도된 정책, 구현 검사, 근거 상태를 evidence.jsonl에 분리했다. 미확정 정답은 null이며 manual 정답으로 대체하지 않는다.
- 합성 14건: 6종 구체 라벨 각 2건, 복합 조건 보류 2건. 계약은 예측 전에 기록하고 98개 HTTP 허용/거부 검사를 통과해야 API 호출을 시작한다.
- 코드 입력은 해당 함수와 직접/간접 호출·Depends의 AST 연결만 포함한다. 외부 DRF 코드는 정확한 메서드와 클래스 설정만 포함하되 프레임워크·serializer 호출 미확보를 기록한다.
- 모델·프롬프트 v2.8·표본 순서·OAS 필드는 동일하고 description의 코드 추가만 다르다. 정답·계약·테스트 기대값은 모델에 보내지 않는다.
- 자동 생성 OAS를 사용한 새 합성 프로젝트는 기존 합성/test와 별개다. 비슷한 핸들러 쌍이 있어 14개의 독립 정책으로 해석하지 않는다.
- 원시 API 응답·usage·개별 소요 시간을 저장한다. 순차 조건 실행, 각 1회이므로 지연 시간의 인과 비교와 확정적 일반화는 하지 않는다.

OAS-only에는 실제 정책 정보가 의도적으로 생략돼 있다. 따라서 낮은 계약 일치도를 모델 추론 능력만의 실패로 해석하지 않는다. 다만 근거가 없을 때 public으로 추측하는지는 별도로 관찰할 수 있다. 이 실험은 정보를 추가했을 때의 변화이며, 코드가 다른 표현의 동등한 정책 문서보다 우수하다는 실험이 아니다. 합성 계약·구현·테스트는 같은 제작자가 작성했으므로 독립 검증은 아니다.

## 코드가 있어도 남은 불일치

| id | 계약 | 예측 | 모델 설명 원문 |
|---|---|---|---|
| controlled-observatory:calibrations | owner_or_admin | owner_match | 요청자는 객체 소유자와 일치해야 하며, 이는 guard_b 함수에서 확인된다. 요청자는 'alice'로 설정된 소유자와 일치해야 하므로 owner_match가 적합하다. |
| controlled-observatory:queues | role_required | owner_match | 요청자는 'operator' 역할을 가진 사용자만 접근할 수 있으며, 'alice'가 소유한 리소스에 대한 접근을 요구하고 있습니다. 이 조건은 요청자와 리소스 소유자의 일치가 필요함을 지지합니다. |
| controlled-observatory:relays | role_required | owner_match | 요청자는 'operator' 역할을 가진 사용자만 접근할 수 있으며, 'load' 함수에서 'owner'가 'alice'로 설정된 객체를 반환합니다. 따라서 요청자가 해당 객체의 소유자와 일치해야 접근이 가능합니다. |
| controlled-observatory:spectra | membership_required | owner_match | 요청자는 특정 아이템의 소유자와 일치해야 하며, 이를 확인하는 로직이 구현되어 있음. 사용자의 플랜이 'plus'일 때만 접근이 허용됨. |
| controlled-observatory:transfers | manual_review_required | owner_match | 요청자는 객체 소유자와 일치해야 하며, 이를 확인하는 guard_a 함수가 구현되어 있음. 요청의 소유자 조건을 명확히 지지하는 코드가 존재함. |
| controlled-observatory:reservations | manual_review_required | owner_match | 요청자는 리소스 소유자와 동일한 테넌트에 있어야 하며, 이를 확인하는 guard_c 함수가 구현되어 있음. 또한, 요청자는 'plus' 플랜을 가져야 하며, 이를 확인하는 guard_e 함수도 구현되어 있음. 이 두 조건이 충족되어야 접근이 허용됨. |

## 새 외부 소스에서 발견한 문제

RealWorld Django 구현과 최신 공통 명세의 버전이 다르다. PUT article와 DELETE comment 핸들러에서 작성자 비교를 확인하지 못했고, 최신 인가 테스트는 타인의 요청에 403을 요구한다. 이는 정적 불일치 후보이며 실제 배포 취약점으로 확정하지 않는다. 공개 조회 2건도 실행 검증 전에는 정답 점수에서 제외했다. 외부 소스에서 tenant·membership·owner_or_admin 등 전체 라벨을 검증한 것은 아니다.

## 라벨별 P/R/F1 (합성만)

| label | OAS P/R/F1 | 코드 P/R/F1 |
|---|---|---|
| public | 0.167 / 1.000 / 0.286 | 1.000 / 1.000 / 1.000 |
| role_required | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 |
| membership_required | 0.000 / 0.000 / 0.000 | 1.000 / 0.500 / 0.667 |
| tenant_match | 0.000 / 0.000 / 0.000 | 1.000 / 1.000 / 1.000 |
| owner_match | 0.000 / 0.000 / 0.000 | 0.250 / 1.000 / 0.400 |
| owner_or_admin | 0.000 / 0.000 / 0.000 | 1.000 / 0.500 / 0.667 |
| manual_review_required | 0.000 / 0.000 / 0.000 | 0.000 / 0.000 / 0.000 |

### oas_only 혼동행렬

행은 계약 정답, 열은 예측이다. 합성만 포함한다.

| 정답 / 예측 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| role_required | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| membership_required | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| tenant_match | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| owner_match | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| owner_or_admin | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| manual_review_required | 2 | 0 | 0 | 0 | 0 | 0 | 0 |

### oas_code 혼동행렬

행은 계약 정답, 열은 예측이다. 합성만 포함한다.

| 정답 / 예측 | public | role_required | membership_required | tenant_match | owner_match | owner_or_admin | manual_review_required |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| role_required | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| membership_required | 0 | 0 | 1 | 0 | 1 | 0 | 0 |
| tenant_match | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| owner_match | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| owner_or_admin | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| manual_review_required | 0 | 0 | 0 | 0 | 2 | 0 | 0 |

## 모든 사례

| id | 출처 | 채점 정답 | OAS | 코드 |
|---|---|---|---|---|
| controlled-observatory:observations | synthetic_control | owner_match | public | owner_match |
| controlled-observatory:notebooks | synthetic_control | owner_match | manual_review_required | owner_match |
| controlled-observatory:calibrations | synthetic_control | owner_or_admin | public | owner_match |
| controlled-observatory:captures | synthetic_control | owner_or_admin | public | owner_or_admin |
| controlled-observatory:allocations | synthetic_control | tenant_match | manual_review_required | tenant_match |
| controlled-observatory:inventories | synthetic_control | tenant_match | public | tenant_match |
| controlled-observatory:queues | synthetic_control | role_required | public | owner_match |
| controlled-observatory:relays | synthetic_control | role_required | public | owner_match |
| controlled-observatory:spectra | synthetic_control | membership_required | public | owner_match |
| controlled-observatory:forecasts | synthetic_control | membership_required | public | membership_required |
| controlled-observatory:catalog | synthetic_control | public | public | public |
| controlled-observatory:bulletins | synthetic_control | public | public | public |
| controlled-observatory:transfers | synthetic_control | manual_review_required | public | owner_match |
| controlled-observatory:reservations | synthetic_control | manual_review_required | public | owner_match |
| realworld-django:GET:/articles/{slug} | external_static | 미확정/채점 제외 | public | public |
| realworld-django:PUT:/articles/{slug} | external_static | 미확정/채점 제외 | manual_review_required | owner_or_admin |
| realworld-django:DELETE:/articles/{slug}/comments/{id} | external_static | 미확정/채점 제외 | manual_review_required | owner_or_admin |
| realworld-django:GET:/tags | external_static | 미확정/채점 제외 | public | public |

## 남은 작업

실제 새 외부 프로젝트에서 여섯 구체 라벨의 명시 정책·호출 연결·실행 테스트가 일치하는 사례를 확보해야 한다. 합성 성능을 외부 성능으로 대체하지 않는다. 이번 결과를 보고 v2.8을 수정하지 않았다.

## 실행량과 재현

```json
{
  "oas_only": {
    "responses": 18,
    "input_tokens": 51773,
    "output_tokens": 1109,
    "evidence_invalid": 0,
    "errors": 0
  },
  "oas_code": {
    "responses": 18,
    "input_tokens": 61546,
    "output_tokens": 1439,
    "evidence_invalid": 0,
    "errors": 0
  }
}
```

단가는 확인하지 않아 비용을 추정하지 않았다. 사용량은 API 응답 기록 기준이다.

```powershell
.python/python.exe -X utf8 -m training.experiments.collect_paired_policy
.python/python.exe -X utf8 -m scripts.eval_classifier --paired-policy prepare
.python/python.exe -X utf8 -m scripts.eval_classifier --paired-policy run
.python/python.exe -X utf8 -m pytest tests/test_paired_policy.py tests/test_eval_classifier.py tests/test_eval_context.py -q
```

정상 완료된 체크포인트는 재실행 시 추가 호출하지 않는다. 입력·프롬프트 해시가 다르면 이어서 실행하지 않는다.
