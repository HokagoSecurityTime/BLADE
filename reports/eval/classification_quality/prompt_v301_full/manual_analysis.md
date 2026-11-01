# manual_review_required 원인 분석 — 프롬프트 v3.0.1 전체 2,027건 (API 호출 없음)

rationale 문장을 정규식 규칙으로 유형화했다(첫 일치 유형을 주 유형으로 집계, 규칙 순서는 스크립트 TYPES). 모델이 쓴 문장 기반이므로 근사치다. manual 1530건.

## 1. manual rationale 상위 유형 (주 유형)

| 순위 | 유형 | 건수 | 비율 |
|---:|---|---:|---:|
| 1 | 객체 ID만 있음 | 395 | 25.8% |
| 2 | 요청자-객체 관계 미확인 | 353 | 23.1% |
| 3 | 인증만 확인·인가 조건 없음 | 291 | 19.0% |
| 4 | 접근 조건 미명시(일반) | 137 | 9.0% |
| 5 | 설명 없음·비어 있음 | 122 | 8.0% |
| 6 | API 키만 요구 | 109 | 7.1% |
| 7 | 구독·플랜·등급 조건 | 40 | 2.6% |
| 8 | 기타 | 36 | 2.4% |
| 9 | 복합 조건(AND)·단일 라벨 불가 | 26 | 1.7% |
| 10 | security·인증 정보 없음 | 12 | 0.8% |

중복 허용 집계(한 rationale이 여러 유형에 해당 가능):

| 유형 | 건수 |
|---|---:|
| 접근 조건 미명시(일반) | 1237 |
| 요청자-객체 관계 미확인 | 1146 |
| 객체 ID만 있음 | 415 |
| 인증만 확인·인가 조건 없음 | 357 |
| API 키만 요구 | 124 |
| 설명 없음·비어 있음 | 122 |
| 구독·플랜·등급 조건 | 40 |
| 복합 조건(AND)·단일 라벨 불가 | 31 |
| security·인증 정보 없음 | 13 |
| 역할·권한 조건 불명확 | 11 |
| 코드·의도 충돌 | 1 |

## 2. security_state=unknown 754건

- operation description 비어 있음: 262건 (34.7%); description·summary 모두 비어 있음: 44건.
- manual 판정: 729건 (96.7%).

security_state × description 유무별 manual:

| security_state | 건수 | description 없음 | manual(설명 없음 중) | manual(설명 있음 중) |
|---|---:|---:|---:|---:|
| declared | 1267 | 399 | 301/399 | 500/868 |
| unknown | 754 | 262 | 259/262 | 470/492 |
| explicitly_anonymous | 6 | 1 | 0/1 | 0/5 |

## 3. declared public 150건의 security 출처

| security.origin | 건수 |
|---|---:|
| global | 86 |
| operation | 64 |

참고: declared 전체 1267건의 origin 분포 {'operation': 621, 'global': 646}. declared public 중 anonymous_alternative=true 0건, description 비어 있음 17건.

declared public rationale 유형:

| 유형 | 건수 |
|---|---:|
| 공개 문서·카탈로그 설명 근거 | 142 |
| 조회·목록 성격 근거 | 5 |
| 기타 | 3 |

해석: origin=global(86건, 57.3%)은 spec 전역 security만 있고 operation 레벨 선언이 없는 경우로, 모델이 전역 선언을 해당 operation의 인증 요구로 반영하지 않은 사례다. origin=operation(64건)은 operation 자체에 security가 있는데도 public을 고른 명백한 규칙 위반이다. rationale 유형을 보면 142건이 '공개·누구나' 류의 설명 문구를 근거로 삼았다. 두 경우 모두 train_v30에서는 override(manual)로 처리했다.

원자료: manual_analysis.json, apisguru_labeled_v301.jsonl, apisguru_enriched_v2.jsonl(enrichment.security.origin, operation.description).
