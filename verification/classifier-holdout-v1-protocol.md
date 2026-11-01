# 신규 합성 데이터셋 평가 절차

## 사전 고정 사항

- 데이터: [classifier-holdout-v1.json](classifier-holdout-v1.json), 7 label × 2건 = 14건.
- 모델: Ollama `qwen2.5:7b`, 기존 temperature=0과 60초 I/O 타임아웃·2회 재시도 유지.
- 기존 prompt.py, llm.py, classifier 검증 코드는 이번 평가 동안 수정하지 않습니다.
- 사례별 1회 classify 호출. 내부 HTTP 재시도는 기존 동작을 따릅니다.
- 테스트 점수를 높이기 위해 실패한 사례만 재실행하거나 결과를 제외하지 않습니다.
- 점수 합격선을 새로 설정하지 않습니다. 평가 CLI의 0 종료는 실행 완료를 의미합니다.

## 데이터 구성

기존 데모 리소스와 프롬프트 예시(invoice/workspace)를 제외한 새 엔드포인트입니다.
실제 서비스를 수집한 자료가 아니라, 이 저장소의 7개 label 정의에 따라 직접 작성한 합성 사례입니다.
판단에 필요한 짧은 controller 코드가 모든 사례에 포함되어 있으므로 이전 controller 없는 데모 6/7과
점수를 직접 비교할 수 없습니다. 외부 검토자가 정답을 독립 검증하지 않았습니다.

- public: 익명 버전 조회, ID가 있지만 익명 공개인 상품 카탈로그.
- role_required: auditor와 moderator 역할.
- membership_required: gold와 enterprise 등급.
- owner_match: 경로 ID/owner_id, query ID/비표준 FK.
- tenant_match: organization_id, query ID/비표준 조직 FK.
- owner_or_admin: author_id 관리자 우회, query ID/비표준 사용자 FK 관리자 우회.
- manual_review_required: 소유자 컬럼 불명, 조직 비교와 사용자 FK 간 모순.

정답 label·정답 params·채점 rationale은 모델에 전달하지 않습니다.
모델 입력은 endpoint, 파싱된 DDL, controller_text뿐입니다.
분류기가 기존 방식으로 생성하는 object_bindings는 유지합니다.

## 지표

- 전체 label 정확도: 정답 label 수 / 모든 사례 수. 탈출도 예측 label로 포함합니다.
- label별 precision/recall/F1 및 혼동행렬(행=정답, 열=예측).
- 수동 검토 비율: manual_review_required 예측 수 / 전체.
- 자동 분류 정확도: 수동 검토로 빠지지 않은 사례 중 정답 비율.
- 전체 정책 정확도: label과 object_param/owner_lookup/roles/allowed_membership이 모두 정답인 비율.
  confidence와 evidence 문구는 이 정확도에 포함하지 않습니다.
- 호출 실패 수: 최종 evidence가 `LLM unavailable:`인 사례 수. 내부 성공 재시도 횟수는 계측하지 않습니다.
- 분류 시간: classify 전체 wall-clock 시간의 평균, p50, p95(최근접 순위).
  HTTP 재시도, 모델 로딩, CPU 상태가 포함되며 프록시 지연과 다릅니다.

이 지표는 정책 label/필드 분류 성능이며 공격 요청에 대한 BOLA 오탐·미탐률이 아닙니다.
현재 자료만으로 운영 보안 성능이나 신뢰도 보정을 주장하지 않습니다.

## 보존과 재현

```powershell
$env:BLADE_LLM_PROVIDER='ollama'
$env:BLADE_LLM_MODEL='qwen2.5:7b'
python -m pipeline.classifier.evaluate verification/classifier-holdout-v1.json --output verification/classifier-holdout-v1-run1.json
```

출력에는 데이터셋/소스 SHA256, 모델명, 시작·종료 시간, 사례별 결과 및 누적 지표를 저장합니다.
각 사례가 끝날 때 파일을 갱신하며 실행 중단 상태는 completed=false로 남습니다.
기존 결과 파일은 덮어쓰지 않습니다. 이미지 자료는 생성하지 않습니다.

이 평가 결과를 이용해 프롬프트를 수정한다면 v1은 더 이상 새로운 평가 자료가 아닙니다.
그 이후의 일반화 평가에는 별도 데이터셋을 작성해야 합니다.
