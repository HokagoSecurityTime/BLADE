# 본인 계정 바인딩 추출·타인 ID 주입 검사

인증 사용자 → 핸들러 대상 → 저장소 대상 키 → SQL WHERE 연결을 확인했다. 요청에 넣은 id/user_id/owner_id는 수정 대상 키로 사용되지 않는다. username은 변경할 새 값이며 기존 대상 키와 다르다.

격리 검사 **9/9 통과**. 모든 사례에서 다른 계정의 DB 행은 그대로였다.

| 요청 | 주입값 | 상태 | 타인 계정 보존 |
|---|---|---:|---|
| GET ?id=2&user_id=2&username=bob | null | 200 | True |
| PUT  | {"id": 2, "bio": "changed"} | 200 | True |
| PUT  | {"user_id": 2, "bio": "changed"} | 200 | True |
| PUT  | {"owner_id": "bob", "bio": "changed"} | 200 | True |
| PUT  | {"user": {"username": "bob"}, "bio": "changed"} | 200 | True |
| PUT ?username=bob&id=2 | {"bio": "changed"} | 200 | True |
| PUT  | {"username": "bob", "bio": "changed"} | 400 | True |
| PUT  | {"email": "bob@example.com", "bio": "changed"} | 400 | True |
| PUT  | {"username": "alice_new", "id": 2, "bio": "changed"} | 200 | True |

## 해석

200 응답을 주입 차단 실패로 보지 않는다. 알 수 없는 필드는 원본 Update 스키마에서 무시되고 실제 대상은 인증 사용자로 유지된다. 이미 존재하는 다른 username/email로 변경하려는 요청은 원본 중복 검사에서 400으로 거부된다. 사용하지 않는 새 username으로 이름을 바꾸는 경우에도 동일한 사용자 행만 갱신된다.

## 실행 범위

원본 GET/PUT 핸들러·update_user 저장소 메서드·중복 검사 함수의 본문을 그대로 격리 실행했다. import·타입 annotation·Depends 기본값은 격리 호출을 위해 제거했다. 원본 UserInUpdate 스키마는 Pydantic v1 호환 모드로 실행했다. 같은 커밋의 원본 SQL을 SQLite에서 실행했으며 전체 PostgreSQL 앱 실행은 아니다. 인증 사용자는 테스트 헤더로 주입했고 JWT는 검증하지 않았다.

## 라벨 처리

요청자에게 대상을 고정하는 패턴을 구현 근거로 추가했다. 기존 owner_match의 후보로만 기록하며 새 8번째 라벨을 만들지 않았다. 최종 라벨·고정 test·학습 데이터·런타임은 변경하지 않았다. 다음은 생성자 귀속과 관계 레코드의 요청자 키 추적이다.
