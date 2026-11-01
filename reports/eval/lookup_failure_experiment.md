# 객체 파라미터·lookup 실패 재현 실험

외부 API 호출 0회. 저장된 응답 21건을 실제 classify에 재주입해 최종 라벨·검증 사유가 모두 일치함을 확인했다. 이 중 최초 라벨이 사람 정답과 일치한 18건을 분석했다.

## 결과

- 정답 18건 모두 path/query 파라미터가 없고 object_param=null이다. lookup 자체 누락은 0건이다.
- 18건 모두 lookup 테이블과 id 컬럼이 보강 입력에 존재한다: 18/18.
- GET 6건, POST 11건, PUT 1건이다. /me·자기 정보/목록·생성/업로드 등 ID가 경로에 없는 형태를 포함한다.
- 따라서 이 18건의 직접 원인은 lookup을 안 쓴 것이 아니라, 객체 라벨에 path/query object_param을 필수로 요구하는 현재 정책 표현과 엔드포인트 형태의 불일치다.
- 테이블·컬럼이 존재한다는 것은 실제 해당 핸들러가 그 테이블을 사용한다는 증명이 아니다. 잘못된 테이블 선택까지 검증된 정답으로 간주하지 않는다.
- body 스키마가 있다는 것만으로 body 필드가 소유권 검증용 객체 ID라고 가정하지 않는다. 실제 요청·조회 흐름 확인이 필요하다.

## 권고

1. label 예측 점수와 실행 가능한 정책 생성 점수를 계속 분리한다. 이 실험에서는 보류를 억지로 해제하지 않았다.
2. 개발/검증 데이터에서 객체 ID 기반 조회, JWT 주체 기반 자기 리소스, 생성 시 소유자 지정, 소유자별 목록 필터를 구분하는 정책 표현을 설계한다.
3. body ID 지원만 추가하면 /me·목록·생성 전 객체가 없는 경우는 해결되지 않는다. 각 방식에 맞는 집행 가능성 검토가 먼저다.
4. 런타임 변경과 인터페이스 확장은 현재 금지 범위이므로 구현하지 않았다. 고정 test의 결과에 맞춰 가짜 파라미터를 추가하거나 라벨·threshold를 바꾸지 않는다.

| id | service | method | path | 최초 label | object_param | lookup table / id | body 명세 |
|---|---|---|---|---|---|---|---|
| 759eb32d69ab1820e44d | VAmPI | GET | /me | owner_match | None | users / id | False |
| ff8c5eda79000fa6687f | VAmPI | POST | /books/v1 | owner_match | None | books / id | True |
| c917e3e10dce94cc245c | crAPI | POST | /identity/api/v2/user/pictures | owner_match | None | profile_Video / id | True |
| 4de2f44349d88f3d6b3a | crAPI | POST | /identity/api/v2/user/videos | owner_match | None | profile_Video / id | True |
| 97abea85e395e6649df4 | crAPI | POST | /identity/api/v2/vehicle/add_vehicle | owner_match | None | vehicle_details / id | True |
| 956a6feb1b1f65eb5a9a | crAPI | POST | /workshop/api/shop/apply_coupon | owner_match | None | applied_coupon / id | True |
| 0f7dacc4c4c5dc50ad69 | crAPI | POST | /workshop/api/shop/orders | owner_match | None | order / id | True |
| 16f4b2d20c0ba89ed279 | juice-shop | POST | /api/Cards | owner_match | None | Cards / id | False |
| bbaf2ce2f276bd2f4679 | juice-shop | POST | /api/Complaints | owner_match | None | Complaints / id | False |
| 4033e696c5dc2d5b3aa2 | juice-shop | POST | /api/Feedbacks | owner_match | None | Feedbacks / id | False |
| ed9b8680702e673060d4 | juice-shop | POST | /api/Recycles | owner_match | None | Recycles / id | False |
| 745151104eb860a9e9ec | juice-shop | POST | /rest/memories | owner_match | None | Memories / id | False |
| 314ffc8290ffcff7031e | juice-shop | PUT | /rest/wallet/balance | owner_match | None | Wallets / id | False |
| e8437c5320794a594af6 | Pixi | GET | /api/user/info | owner_match | None | users / _id | False |
| fd938e89d9362deb8656 | Pixi | GET | /api/user/pictures | owner_match | None | pictures / _id | False |
| bf900bef2d12400d0880 | Pixi | GET | /user_info | owner_match | None | users / _id | False |
| 7ab0a0779b998f445f3c | Pixi | GET | /user_loves | owner_match | None | loves / user_id | False |
| 2f8f43be0ee49cc83b1e | Pixi | GET | /user_pictures | owner_match | None | pictures / _id | False |
