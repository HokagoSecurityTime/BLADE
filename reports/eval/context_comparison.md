# GPT-4o-mini 입력 보강 전후 평가

고정 test 253건, v2.0, RAG on, controller on. 두 실행 모두 모델 원문을 저장했다.

| 입력 | 최초 macro-F1 | 검증 후 macro-F1 | 최초 보류율 | 최종 보류율 | 검증으로 정답→오답 | 오답→정답 |
|---|---:|---:|---:|---:|---:|---:|
| 기존 입력 | 0.1255 | 0.0896 | 17.00% | 54.94% | 37 | 1 |
| 소스 보강 입력 | 0.1884 | 0.1587 | 8.30% | 41.11% | 37 | 0 |

## 입력 전달 범위

| 입력 | ERD | controller 상태 |
|---|---|---|
| 기존 | {"missing": 211, "available": 42} | {"source_present_but_runtime_handler_unmapped": 212, "parsed_current_handler": 37, "source_unavailable": 4} |
| 보강 | {"available": 247, "missing": 6} | {"source_present_but_runtime_handler_unmapped": 139, "parsed_current_handler": 110, "source_unavailable": 4} |

## 검증 사유

| 입력 | 사유별 건수 (한 레코드에 여러 사유 가능) |
|---|---|
| before | {"Caller-attribute/public policy conflicts with object lookup": 2, "confidence_below_0.7": 112, "Missing or unknown object parameter/owner lookup": 7, "Unknown lookup table or id column": 13, "json_or_schema_invalid": 5} |
| after | {"Caller-attribute/public policy conflicts with object lookup": 8, "Missing or unknown object parameter/owner lookup": 21, "confidence_below_0.7": 69, "Cannot identify ownership column in ERD": 1, "Unknown lookup table or id column": 1, "json_or_schema_invalid": 3} |

## 실제 정답 손실 원인

| 입력 | 원문→스키마 처리 후→정책 검증 후 macro-F1 | 정답→오답 사유별 건수 | 최종 보류의 출처 |
|---|---|---|---|
| before | 0.1255 → 0.1120 → 0.0896 | {"Caller-attribute/public policy conflicts with object lookup": 2, "Missing or unknown object parameter/owner lookup": 5, "confidence_below_0.7": 20, "Unknown lookup table or id column": 5, "json_or_schema_invalid": 5} | {"converted": 96, "model_manual": 43} |
| after | 0.1884 → 0.1826 → 0.1587 | {"Caller-attribute/public policy conflicts with object lookup": 2, "Missing or unknown object parameter/owner lookup": 18, "confidence_below_0.7": 13, "Cannot identify ownership column in ERD": 1, "json_or_schema_invalid": 3} | {"converted": 83, "model_manual": 21} |

## 해석 제한

- 보강은 ERD와 소스 연결을 함께 바꿨다. ERD가 RAG 검색 질의에도 들어가므로 개선량을 ERD 단독 효과로 해석하지 않는다.
- 각 조건 한 번의 호출이다. 모델의 출력 변동이 포함되며 통계적 유의성이나 일반화 성능을 보장하지 않는다.
- 동일 prompt 해시: 48건. 이 중 최종 라벨 변경: 2건.
- MongoDB 스키마는 논리적 필드 목록을 DDL 문법으로 전달했다. SQL 실행 가능성을 뜻하지 않는다.
- 경로 파싱 성공은 핸들러 전체 및 호출된 서비스의 인가 검사를 이해했다는 뜻이 아니다. Java/Go/Flask 등 지원하지 않는 형태는 누락으로 유지했다.
- 고정 test 및 런타임 코드는 수정하지 않았으며 학습이나 재라벨링을 수행하지 않았다.

## 소스별 점수

| 소스 | 입력 | 최초 macro-F1 | 최종 macro-F1 |
|---|---|---:|---:|
| vuln | 기존 | 0.1297 | 0.0836 |
| vuln | 보강 | 0.2060 | 0.1704 |
| synthetic | 기존 | 0.0357 | 0.0357 |
| synthetic | 보강 | 0.0357 | 0.0357 |
