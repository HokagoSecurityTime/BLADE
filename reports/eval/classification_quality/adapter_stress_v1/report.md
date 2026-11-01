# 외부 어댑터 v1 조건 보존 스트레스 실험

기존 어댑터를 수정하지 않고 합성 변형 10개 × 상태 8개를 실행했다. 실제 Python 함수의 허용/거부와 추출 조건을 비교했다. 새로운 외부 프로젝트 성능 평가가 아니라 파서 확장 위험을 확인하는 개발 실험이다.

조건 일치 4개, 잘못 추출 3개, 미지원 거부 3개. API 호출 0회.

| 사례 | 결과 | 추출 조건 |
|---|---|---|
| owner_or_admin | equivalent | `((True and not (((not admin) and (not owner)))))` |
| owner_and_admin | equivalent | `((True and not (((not admin) or (not owner)))))` |
| owner_not_admin | equivalent | `((True and not ((admin or (not owner)))))` |
| admin_early_return | equivalent | `((True and admin) or ((True and not (admin)) and not ((not owner))))` |
| masked_404 | incorrect | `(True)` |
| helper_guard | incorrect | `(True)` |
| assert_guard | incorrect | `(True)` |
| unknown_tenant | unsupported | `Unsupported authorization expression: item.tenant_id != current_user.tenant_id` |
| alias_owner | unsupported | `Unsupported authorization expression: item.owner_id != caller.id` |
| nested_guard | unsupported | `Unsupported branch` |

## 발견 사항

권한 거부를 404로 숨기는 검사, 별도 helper 호출, assert 검사는 현재 파서가 누락한다. 따라서 알 수 없는 코드에 이 파서를 직접 적용해서는 안 된다. 기존 전체 실행은 원본 해시와 검토한 핸들러 목록으로 제한되므로 이번 변형을 운영에서 처리했다는 뜻은 아니다. extract() 단독 호출에는 자체 해시 검사가 없다는 점도 호출 경계의 약점이다.

## 다음 조치

외부 프로젝트 확대보다 먼저 별도 v2 어댑터에서 미지원 문장·호출을 보류하고, 404를 객체 부재 검사로만 인정하며, 호출 진입점마다 소스 무결성을 확인해야 한다. 이번 v1 결과와 해시는 보존했다. 모델 라벨·기존 test·런타임은 변경하지 않았다. 자동 적용은 계속 금지 상태다.
