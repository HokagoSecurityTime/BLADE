# LoRA v1 (data-v1) 평가 — test_v30 269건 (양식)

프롬프트 v3.0.1 고정. data-v1 = train_v30 471 / val_v30 52. 베이스 Qwen2.5-7B-Instruct(4bit). 평가 환경: Colab <GPU>, run `<run_name>`, 어댑터 SHA-256 `<...>`. 로컬 베이스라인 열은 다른 환경(gpt-4o-mini API / qwen2.5:7b Ollama CPU)에서 측정한 참고값이며 같은 추이로 연결하지 않는다.

입력 조건: `oas` = 명세만, `oas_code` = 명세 + 핸들러 원문(controller_text가 있는 건만, N=<n>).

## 1. 요약

| 조건 | 모델 | macro-F1 (support 있는 label 수) | manual 비율 | public 오판(security 선언 건의 public 판정) | 출력 오류 | 평균 추론 ms |
|---|---|---:|---:|---:|---:|---:|
| oas | (a) 베이스 + v3.0.1 | | | | | |
| oas | (b) LoRA v1 | | | | | |
| oas_code | (a) 베이스 + v3.0.1 | | | | | |
| oas_code | (b) LoRA v1 | | | | | |
| oas | 참고: gpt-4o-mini + v3.0.1 (로컬 API) | | | | | |
| oas | 참고: qwen2.5:7b Ollama CPU + v3.0.1 | | | | | |

## 2. label별 P/R/F1 — 조건별·모델별 (support 포함)

| label | support | (a) P | (a) R | (a) F1 | (b) P | (b) R | (b) F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| public | | | | | | | |
| role_required | | | | | | | |
| membership_required | | | | | | | |
| tenant_match | | | | | | | |
| owner_match | | | | | | | |
| owner_or_admin | | | | | | | |
| manual_review_required | | | | | | | |

(oas 조건 표와 oas_code 조건 표를 각각 둔다.)

## 3. confusion matrix (행=정답, 열=예측, output_error 열 포함)

(조건·모델별 4개)

## 4. public 오판 상세

security_state=declared인데 public으로 예측한 건의 id 목록과 건수(모델·조건별). test_v30의 declared 건수 N=<n>.

## 5. 학습 기록

- 하이퍼파라미터(config.json), 학습 손실 곡선 요약, 체크포인트 수, 재개 여부.
- 데이터·프롬프트 해시 검증 결과(hashes.json ↔ AGENTS.md data-v1).

## 6. 해석과 한계

- test_v30의 tenant_match 8·membership_required 4·owner_or_admin 11건은 지원 표본이 작다.
- synthetic 58건과 vuln 211건을 분리한 수치를 병기한다.
