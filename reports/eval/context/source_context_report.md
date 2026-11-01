# 소스 기반 평가 입력 보강

고정 test의 라벨·경로·OAS는 변경하지 않는다. 별도 overlay에는 ERD와 controller 원문 및 출처만 저장한다.

| Service | ERD 추가 | 원문 소스 매핑 | 런타임 경로 파싱 | 경로 미매핑 |
|---|---:|---:|---:|---:|
| VAmPI | 12 | 12 | 0 | 12 |
| crAPI | 47 | 53 | 0 | 53 |
| juice-shop | 69 | 69 | 66 | 3 |
| Pixi | 52 | 48 | 44 | 8 |
| DVWS-node | 25 | 25 | 0 | 25 |

## 추출 범위와 한계

- SQLAlchemy 명시 컬럼, Sequelize init·관계 선언, JPA 명시 이름 및 단순 필드, Django 현재 모델, Mongoose Schema, Pixi insert 객체 키를 정적 분석했다.
- 공개 API 211건 중 205건에 필드 목록을 제공한다. crAPI community 6건은 미보강이다. 합성 42건은 기존 입력을 유지한다.
- 테이블 타입은 TEXT로 통일한 파서 전달용 표현이다. 실제 타입이나 완전한 DB DDL을 복원했다고 주장하지 않는다. 명시 PK 및 확인한 Sequelize FK만 보존한다.
- MongoDB는 컬렉션/모델 필드 목록을 DDL 형태로 표현한다. 특히 Mongoose 모델명은 실제 컬렉션명과 다를 수 있어 정책 실행용 lookup으로 검증된 이름이 아니다.
- service 전체 모델을 전달하며 crAPI는 identity/workshop 저장소 범위를 분리한다. 엔드포인트별 실제 접근 테이블을 모두 증명한 매핑은 아니다.
- 원래 meta.source_locations의 실제 파일을 연결한다. Juice Shop server.ts의 라우트 등록도 포함한다. 인가 검사나 가짜 데코레이터를 만들지 않는다.
- 경로 파싱 성공은 함수 호출을 따라 모든 인가 검사를 읽은 성공률이 아니다. factory handler·Java/Go·Flask·Express router.route 체인은 여전히 불완전하다.
- 원문 파일 경로·줄·SHA-256은 source_context_report.json 및 source_overlay.jsonl에 기록한다. 공개 저장소를 실행하거나 수정하지 않았다.
