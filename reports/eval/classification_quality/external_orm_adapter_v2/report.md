# 프롬프트 v2.9 / ORM 어댑터 v2 개발 검증

검토한 고정 소스의 ORM 조회·인가 의존성·객체 변경 호출을 연결했다. v1과 기존 결과는 보존했다.

지원 8/23건. 나머지는 보류한다. API 호출 0회.

| 입력 | 결과 | 건수 |
|---|---|---:|
| oas | unresolved_source | 15 |
| oas | prediction_validation_failed | 1 |
| oas | missing_required_condition | 2 |
| oas | equivalent | 1 |
| oas | overrestriction | 2 |
| oas | manual_or_invalid_label | 2 |
| oas_code | unresolved_source | 15 |
| oas_code | missing_required_condition | 4 |
| oas_code | equivalent | 4 |

## 범위

호출과 변수 연결은 evidence.json에 원본 위치·정규화 내역으로 기록했다. 객체 부재 검사만 404 전제 처리하며 소유권 404는 조건으로 남긴다. 허용 목록 밖 호출·대입은 보류한다. 입력 소스 전체 해시를 매번 확인하므로 허용 목록을 임의의 외부 코드에 적용하지 않는다.

SQLModel 라이브러리 의미와 검토한 모델을 전제로 한다. 실제 DB·JWT 통합 검증이나 일반적인 import/call graph 분석을 완료한 것은 아니다. 기존 프로젝트를 개발셋으로 재사용했으므로 독립 성능 수치가 아니다. 의미 통과도 자동 적용 승인이 아니며 auto_apply_allowed는 false다.
