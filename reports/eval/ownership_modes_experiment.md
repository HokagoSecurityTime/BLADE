# 소유권 처리 방식 개발 실험

독립 개발 예제 18건 통과. API 호출·학습 없음. 고정 test 성능 실험이 아니다.

| 처리 방식 | 검증한 계약 | 제품 적용에 필요한 기능 |
|---|---|---|
| object_lookup | 요청 ID로 조회 후 소유자 비교 | 신뢰 가능한 DB 조회·실행 시점 일관성 |
| subject_resource | 검증된 주체로 자기 리소스 선택 | 백엔드의 주체 기반 조회를 보장하는 어댑터 |
| create_owner | 타인 소유자 지정 거부·주체로 소유자 확정 | 저장 트랜잭션까지 소유자 연결 보장 |
| owner_collection | 주체 소유 데이터만 반환 | DB 쿼리 제한·페이지네이션/집계 누출 방지 |

새 방식은 백엔드 어댑터가 없으면 unsupported이다. JWT 존재만으로 허용하거나 lookup에 가짜 ID를 넣지 않는다.

| 예제 | 기대 | 결과 |
|---|---|---|
| owned object | allow | allow |
| other object | deny | deny |
| missing id | deny | deny |
| missing owner | deny | deny |
| own subject resource | allow | allow |
| missing subject resource | deny | deny |
| create assigns owner | allow | allow |
| create matching owner | allow | allow |
| create forged owner | deny | deny |
| create null owner | deny | deny |
| collection excludes other/missing owner | allow | allow |
| object_lookup unauthenticated | deny | deny |
| subject_resource unauthenticated | deny | deny |
| create_owner unauthenticated | deny | deny |
| owner_collection unauthenticated | deny | deny |
| subject_resource no backend adapter | unsupported | unsupported |
| create_owner no backend adapter | unsupported | unsupported |
| owner_collection no backend adapter | unsupported | unsupported |

## 해석

- 의미 라벨 owner_match와 집행 방식을 분리하면 ID 없는 요청의 요구사항을 표현할 수 있다. 라벨은 기존 7종을 유지한다.
- 메모리 객체로 계약을 검증했을 뿐 실제 HTTP/JWT/DB/동시성/중첩 body/응답 스트리밍은 구현하지 않았다. 제품 보안이나 성능 향상을 입증한 결과가 아니다.
- 고정 test의 18건을 자동으로 새 방식에 배정하거나 보류를 해제하지 않았다. 실제 데이터 흐름 검증이 필요하다.
- 다음 구현은 별도 개발 서비스 및 실제 백엔드 어댑터 통합 검증이다. 현재 런타임 변경 금지 규약 때문에 제품 코드는 수정하지 않았다.
