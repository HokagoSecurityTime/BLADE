# 어댑터 v2 회귀 검증

프롬프트는 v2.9 그대로다. v1의 기존 변형 10건을 재사용한 개발 검증이며 독립 평가가 아니다.

정확한 추출 7건 / 잘못된 추출 0건 / 보류 3건. API 호출 0회.

| 사례 | 결과 | 보류 사유 |
|---|---|---|
| owner_or_admin | equivalent |  |
| owner_and_admin | equivalent |  |
| owner_not_admin | equivalent |  |
| admin_early_return | equivalent |  |
| masked_404 | equivalent |  |
| helper_guard | equivalent |  |
| assert_guard | held | assert execution mode unverified |
| unknown_tenant | held | unknown condition: item.tenant_id != current_user.tenant_id |
| alias_owner | held | unsupported statement: Assign |
| nested_guard | equivalent |  |

404 인가 거부와 전달된 helper의 인자 연결을 보존한다. 미해결 호출·대입은 보류한다. assert는 Python 최적화 실행에서 사라질 수 있어 기본적으로 보류하며, 활성화가 확인된 테스트에서만 해석한다.

**제약:** 실제 ORM 핸들러 전체 호출 연결은 아직 미지원이다. v2는 이를 보류하며 v1의 8건 지원을 유지했다고 주장하지 않는다. 단독 extract 호출도 원본 해시를 확인한다. helper 소스는 명시적으로 전달해야 하며 자동 import 해석은 미구현이다. 외부 독립 실험 전에 ORM/호출 그래프 지원을 별도로 추가해야 한다. 자동 적용은 하지 않는다.
