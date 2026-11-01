# 발표·논문 근거 보완 (A~E, 2026-11-01)

학습 없음, 동결 파일은 해시 확인 후 읽기만(test_v30 `9bd47216…`, train_sft_v5 `2351afe9…`, train_v5 `528b3690…`), 커밋 없음.

| 항목 | 산출물 | 요약 |
|---|---|---|
| A. 프록시 재측정 | A_proxy_remeasure_20261101.md, A_comparison_tables.md, A_comparison.json, A_remeasure_20261101/ (METRICS.md·metrics-*.json·SHA256SUMS) | 커밋 7b857e2, Docker 컨테이너, phase2=false. 탐지 5종 100%·6종 83.33%·오탐 0/140 — Phase 1과 요청 단위까지 동일. p95 추가 지연 +1.60(9-13 로컬) → +2.64(10-31 Docker) → **+2.03 ms(이번)**. 정책은 승인 전 상태(public ACTIVE·6건 PENDING)로 복원. |
| B. 데이터셋 출처 목록 | ../data_sources.md (직전 작업에서 작성, 그대로 유효) | 출처별 저장소·태그·커밋·라이선스·건수·용도·공개 범위, 제외 출처 표, APIs.guru 370 services/2,027건·스냅샷 2026-10-13(커밋 f04b8d0b). |
| C. label × 출처 유형 | C_label_x_source_type.md, C_label_x_source_type.csv, C_label_x_project.csv | SFT 1,274 = 공개 명세 338 / 실서비스 코드 793 / 합성 143. owner_or_admin은 실서비스 63·합성 32·명세 1. |
| D. 학습 전후 예시 | D_before_after_candidates.md, .csv, .json | 207건 중 base public 오판 77건 → v5 3 seed 모두 정답 28건(owner_match 26·role_required 2). 추천 3건: Pixi GET /user_loves, VAmPI GET /me, juice-shop GET /rest/wallet/balance. |
| F. 공개 라이선스 처리 방안 | F_license_release_plan.md | DVWS-node 25건(코드 제외 사본 + manifest 권장), 미선언 5개 저장소 28건(코드 제외·SFT 사본 28행 제외, DATA_CARD 한계 문구 초안), Dendrite meta.tag 오기(extract 스크립트 TAG 재정의; errata 초안). 적용은 승인 후. |
| G. 21번 예시 | G_example21_pixi_user_loves.md | Pixi GET /user_loves: security 선언 없음(unknown), login_check + find({ user_id : req.session.user._id }), base public(0.9) → v5 3 seed owner_match(0.9), rationale 원문. |
| E. 데모 녹화 명령 | E_demo_recording_commands.md | 로컬 uvicorn 3종 + Ollama(LoRA v5) 기동, 토큰(user_77=alice·user_99=bob), 정답 문구 없는 OAS 사본, 장면 1~8 명령·기대 응답, Slack 조건(BLOCK만)·메시지 예시. |

결정(2026-11-01): 발표 지연 수치는 +2.0 ms(11-01, Docker)이고 Phase 1 +1.6 ms는 주석 병기. verification/METRICS.md·metrics-*.json은 11-01 결과로 확정, phase1_20260913/·remeasure_20261031/ 보존. 2번(라이선스)은 방안만 보고하고 적용은 승인 후.

2차 결정(2026-11-01): 2번 적용 완료(공개 사본 datasets/blade/processed/public/, training/lora/public/, 복원 검증 OK; DATA_CARD·AGENTS.md 갱신; D의 DVWS 인용 링크 교체). 21번 예시 문구는 "세션 사용자 id로만 조회하는 코드를 근거로 owner_match 판단"으로 확정(G 문서).
