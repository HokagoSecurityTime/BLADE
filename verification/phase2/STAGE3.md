# [3] Controller 정적 분석

2026-10-08. Python AST, JS/TS tree-sitter, 의존성 부재 시 Express/Nest 정규식 폴백을 구현했다. 다른 라우트의 코드가 현재 엔드포인트에 섞이지 않도록 입력을 분리한다. 원본 demo_backend 코드는 수정하지 않았다.

## 검증

- Controller 테스트 10개 PASS: 데모 7개 모두 인가 검사 없음, FastAPI 3개, Express 2개, Nest, 이름으로 참조하는 핸들러·미들웨어, 폴백, 잘못된 입력, 비활성화 시 원래 프롬프트 유지.
- `demo_with_admin.py` fixture는 데모의 7개 라우트를 유지하고 사용자 조회에만 소유자·관리자 검사를 추가했다. 정적 분석에서도 해당 라우트에만 인가 신호가 나온다.
- 실제 Ollama `qwen2.5:7b`, CPU, HTTP `/generate`로 사용자 조회 엔드포인트를 검증했다. LLM mock 없이 **owner_or_admin**, 올바른 `users.id` 조회 컬럼, PENDING을 반환했다. 약 30.922초.
- 실행: `.python/python.exe -m verification.phase2.verify_stage3 --users-only`
- [요청·응답 전문](stage3-users-fixture-generate.txt), [정책](stage3-users-fixture-policies.json), [LLM 입력·원본 출력](stage3-users-fixture-llm.json), [판정](stage3-users-fixture-live-result.json).
- 이 최종 실제 검증은 문제 라우트 1개를 대상으로 했다. 7개 전체 실제 분류 성공률을 뜻하지 않는다.

## 실패를 포함한 실험 이력

| 실행 | 범위 | 사용자 조회 결과 | 판단 |
|---|---|---|---|
| 1 | 7개 / FastAPI 3핸들러 fixture | role_required | FAIL; 336.859초, 최초 요청 타임아웃 후 재시도 |
| 2 | 7개 / 코드 분리·Q4 설명 보완 | role_required | FAIL; DELETE도 다른 핸들러 영향으로 오분류 |
| 3 | 7개 / 미매칭 코드 제외·일반 예시 | manual_review_required | FAIL; 다른 6개 label은 일치, 소유 컬럼 미지정 |
| 4 | 데모 기반 fixture, 사용자 조회 1개 | manual_review_required | FAIL |
| 5 | 동일 입력, LLM 원본 출력 추적 | manual_review_required | FAIL; 원본 label은 owner_or_admin이나 owner_col=null |
| 6 | 호출자 ID 직접 비교를 구조적 바인딩에 반영 | owner_or_admin | PASS |

실패 자료는 `stage3-*-attempt1/2/3`, `stage3-users-fixture-*-attempt4/5` 파일에 보존했다.

원인: ERD에 users.user_id 같은 FK가 없어 owner_col 힌트가 null이었고 LLM이 이를 복사했다. Controller가 호출자 id/sub와 경로 파라미터를 직접 비교하면, 해당 객체 조회 키를 owner_col 후보로 전달한다. label을 강제하거나 출력의 잘못된 컬럼을 자동 치환하지 않는다. 실제 컬럼 검증에 실패하면 여전히 manual_review_required다.

## 범위 및 한계

정적 신호는 인가가 올바르게 구현됐다는 증명이 아니다. 일반적인 FastAPI 데코레이터, Express 라우트·함수 참조, Nest 데코레이터를 처리한다. 동적 라우팅·복잡한 상속·외부 모듈 의존성은 추론하지 않는다. 정규식 폴백은 AST보다 부정확할 수 있으므로 경고를 남긴다. `BLADE_CONTROLLER_ENABLED=false` 또는 전체 Phase 2 비활성화 시 Phase 1 프롬프트를 사용한다.
