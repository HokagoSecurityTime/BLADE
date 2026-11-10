# 마감 후 과제 목록 (2026-11-09, S9 결과 수용·LoRA v7 채택 시점)

사용자 결정(2026-11-09): LoRA v7 채택(사전 기준 3개 충족, 채점이 사전 기한 18:00 KST를 44분 넘겼으나 데이터·판정 기준·절차 변경이 없고 중단 규칙의 목적인 "실험 추가 방지"에 어긋나는 추가 실험이 없어 채택 유지). 아래는 발표 뒤에 다룰 과제이며 현재 동결본·채점 결과는 바꾸지 않는다.

| # | 과제 | 근거 | 범위·방법 | 산출 |
|---|---|---|---|---|
| 1 | **Redash G1-b 경계 18건 재검토** | S9에서 v5·v7 모두 0/18(정답 tenant_match, 예측 role_required). 보충 규약 G1-b(`@require_admin` = 조직 그룹 권한 메커니즘 → `current_org`와 함께면 tenant_match)가 모델 입장에서는 역할 검사로 읽힘 | 18건 코드·규약 재확인(사람), G1-b 정의 유지 여부 결정, 유지 시 학습 데이터에 같은 패턴(조직 권한 데코레이터 + 조직 필터)이 있는지 점검, 폐기 시 test_v6 재채점(정답 변경은 재동결·manifest 갱신) | reports/data_v6/g1b_review.md, 결정에 따라 test_v6 v2 |
| 2 | **여섯 run 공통 오답 70건 분석** | v5·v7 3 seed 모두 틀린 70/289(tenant 30·manual 15·role 14·membership 6·owner 4·own+adm 1; Redash 22·seahub 19·Penpot 18·GlitchTip 11; ai_single 40·ai_double 29·human 1) | 70건을 (a) 정답 오류 의심, (b) 입력 근거 부족(핸들러 밖 권한 정의), (c) 모델 한계로 분류. (a)는 사람 확정, (b)는 S4 문맥 블록 설계(학습 입력에도 같은 형식) 후보, (c)는 manual 규칙 재설계 입력 | reports/eval/lora_v7/s9/common_errors_70.md |
| 3 | **OAS pool 256건 사람 검수** | data-v7 재판정에서 OAS-only 행 390 중 256행이 manual로 바뀌어 학습 제외·pool 보존(train_v7_oas_manual_pool.jsonl). 보류 2(설명문에 접근 조건 미명시 → manual) 적용 결과이며 사람 확인 없음. C′ 블라인드 감사 OAS-only 불일치 76.2% | 256행(+ 기존 OAS-only 134행 표본) 사람 검수로 보류 2 적용 타당성 확인. 결과에 따라 (a) manual로 학습 재투입, (b) 계속 제외, (c) 설명문 기준 완화 | review/oas_pool_256_review.xlsx, reports/data_v7/oas_pool_review.md |
| 4 | **manual_review_required 규칙 재설계** | manual이 "7종에 없음·조건 OR 분기·설정 의존·인증만·근거 부족"을 한 label로 묶어 F1이 0.5대에 머물고(test_v5 0.499→0.541, test_v6 0.532→0.564), seed 간 갈림의 대부분이 manual 경계(test_v6 v7 갈린 쌍 manual|member 17·manual|role 9·manual|tenant 7). 검수에서도 manual 판정 일치율이 가장 낮음 | v3.1 라벨 정의 초안(보류 1~5)을 기준으로 manual 하위 유형(복합 OR / 설정 의존 / 인증만 / 근거 부족)을 분리하거나 출력 필드(hold_reason)로 보존하는 설계. 프롬프트·학습 target 동시 변경이 필요하므로 S5 교훈(프롬프트만 바꾸면 하락) 반영. 평가는 새 hold-out 필요 | reports/eval/human_agreement_v5/manual_redesign_proposal.md |
| 5 | test_v6 사람 전수 검수 | 정답의 75%(217/289)가 AI 단독 판정(A안) | 우선순위: 공통 오답 70건 → ai_single 217건. 완료 시 label_status 갱신·재동결(test_v6 v2) | review/test_v6_full_human_review.xlsx |
| 6 | data-v7 사람 확인 시트 회수 | review/data_v7_human_check.xlsx(변경 45·블라인드 31·추가행 rationale 50) 미회수 | 회수 후 불일치를 DATA_CARD·보고서 한계에 기록(학습 재실행 없음) | reports/data_v7/human_check_result.md |
| 7 | 배포 전환 확인 항목 | oas(명세만) 조건에서 v7 public 오판 14/24/6(v5 5/7/6), s44 출력 오류 21건(중국어 혼입); GGUF 변환 동등성·MIN_CONFIDENCE(val_sft_v7)·KV 캐시 | C-5 절차 그대로. 명세만 입력(oas) 경로의 public 예측에 추가 보류 규칙이 필요한지 verify_lora_pipeline로 확인 | reports/eval/lora_v7_gguf/ |
| 8 | test_v5·test_v31_supp 재분리 | 두 셋이 data-v7 학습에 들어가 더는 hold-out이 아님 | 이후 실험의 dev셋은 test_v6(S9 사용으로 dev 전환), 최종 판정은 새 hold-out(test_v7) 필요. 출처 제외 규칙(기존 전 프로젝트·포크·AGPL) 유지 | AGENTS.md 사전 기록 |

우선순위: 1·2(결과 해석 직결) → 7(배포) → 3·4(다음 데이터 버전) → 5·6 → 8.
