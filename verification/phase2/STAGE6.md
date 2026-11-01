# [6] 재분석 검증

실제 프록시 → admin 저장소로 `/users/user_77` 요청 20건을 전송했다. manual_review 정책은 **명시적인 검증 fixture**이며 사용자 정책/DB는 변경하지 않았다. 실제 Ollama qwen2.5:7b, E5/Chroma code+idiom과 관리자 우회 Controller fixture를 사용했다.

최종 결과: OBSERVE 20건, 제안 1건, **owner_or_admin**, 원본 manual_review 정책 유지. [stage6-result.json](stage6-result.json), [HTTP 전문](stage6-http.json), [원본 LLM 응답](stage6-llm.json), [제안](stage6-proposals.json).

재분석 임계값·롤백·다수 주체의 would_block 비율, fingerprint 마스킹, 중복 억제, 버전 증가/observe 리셋, stale 제안 409, REJECTED 복원 거부를 테스트했다. `tests/test_reanalysis.py` 5개 PASS. 전체 결과는 stage6-pytest.txt 참조.

실패도 보존했다. attempt1/2는 CPU LLM의 60초 타임아웃(각 최대 2회 재시도)으로 제안 0건. attempt3은 owner_or_admin을 출력했지만 근거 ID에 공백을 덧붙여 검증기가 manual_review로 처리했다. 재분석에 한해 응답 근거를 짧게 제한하고, 인용 ID는 실제 검색 ID enum으로 제한했다. snippet은 모델이 재생성하지 않고 실제 검색 원문을 저장한다. 타임아웃은 변경하지 않았다. 네 번째 실제 실행에서 통과했다.

Phase 1 저장 정책에는 생성 시의 OAS/ERD/Controller context가 없을 수 있다. 이 경우 자동 추측하지 않고 워커가 경고·백오프한다. Phase 2 /generate부터 context를 함께 저장한다. 탐지 스키마에는 JWT 역할이 없으므로 로그 요약만 보고 admin 역할이라고 주장하지 않는다.
