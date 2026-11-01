# LoRA v1 (data-v1) — Colab 실행 안내

프롬프트 v3.0.1 고정. 베이스 `unsloth/Qwen2.5-7B-Instruct-bnb-4bit`(Qwen2.5-7B-Instruct 4bit), Unsloth QLoRA. 학습 입력은 추론 시와 동일하게 system=프롬프트 v3.0.1 원문, user=`Return JSON.\n{payload JSON}`, assistant=`{"label","confidence","rationale","evidence_fields"}` 한 줄이다. 이 저장소에서는 모델 학습을 실행하지 않는다. 노트북은 Colab에서 사용자가 직접 실행한다.

## 1. 로컬에서 Drive 업로드 파일 만들기

```powershell
cd C:\BLADE
$env:PYTHONPATH="C:\BLADE"
.python\python.exe -X utf8 training\lora\prepare_lora_inputs.py
```

생성 위치 `training/lora/data_v1/` (git 추적):

| 파일 | 내용 |
|---|---|
| train_sft.jsonl | train_v30 471건 → {id, system, user, assistant, label, source} |
| val_sft.jsonl | val_v30 52건, 같은 형식 |
| test_v30_inputs.jsonl | test_v30 269건 → {id, label, source, security_state, oas_user, oas_code_user(코드 있을 때)} |
| policy_label_v3.0.1.md | 프롬프트 사본(system) |
| data_v1_hashes.json | 원본(train_v30/val_v30/test_v30/프롬프트)과 생성 파일의 SHA-256. 노트북이 대조한다 |

override·relabel 레코드(label은 manual이지만 모델 rationale은 public 등)는 assistant rationale을 규칙 문장으로 대체했다(`rationale_source` 필드에 기록). 원본 데이터 파일은 바꾸지 않는다.

## 2. Google Drive 폴더 구조

```
MyDrive/blade_lora_v1/
  data_v1/                 ← 위 5개 파일 업로드
  runs/<run_name>/         ← 노트북이 생성: config.json, hashes.json, adapter/, checkpoints/, logs/, eval/{metrics.json,report.md,predictions_*.jsonl}
```

## 3. 실행 순서 (Colab)

1. `training/lora/lora_v1_colab.ipynb`를 Colab에 업로드. 런타임: GPU **L4(권장, 24GB)** 또는 T4(16GB).
2. 셀 1: Drive 마운트. 셀 2: 하이퍼파라미터·경로(`RUN_NAME` 지정). 셀 3: 패키지 설치. 셀 4: 해시 검증(불일치면 중단).
3. 셀 5~6: 학습. 체크포인트는 `runs/<run_name>/checkpoints/`에 저장되고, 세션이 끊기면 같은 RUN_NAME으로 다시 실행하면 마지막 체크포인트에서 재개한다.
4. 셀 7~9: test_v30 평가 — (a) 베이스 + 프롬프트 v3.0.1(어댑터 없음), (b) LoRA v1. 각 oas / oas_code. 결과는 `runs/<run_name>/eval/`.
5. API 키·토큰은 노트북에 쓰지 않는다. HF 토큰도 필요 없다(공개 모델).

예상 시간(471건 × 3 epoch, 최대 시퀀스 4096): L4 약 40~60분 학습 + 평가 약 60분, T4 약 2시간 학습 + 평가 약 2.5시간. T4 메모리 부족 시 조정은 노트북 셀 2 주석 참조.

## 4. 결과 회수

Drive `runs/<run_name>/eval/` 의 `metrics.json`, `report.md`, `predictions_*.jsonl`과 `config.json`, `hashes.json`, `logs/train_log.jsonl`을 로컬 `reports/eval/lora_v1/`에 복사한다. 어댑터(`adapter/`, 수십~수백 MB)는 git에 올리지 않고 `reports/untracked_artifacts.md`에 경로·SHA-256만 기록한다.

```powershell
# 예: Drive 데스크톱 동기화 폴더에서
Copy-Item "G:\내 드라이브\blade_lora_v1\runs\<run_name>\eval\*" C:\BLADE\reports\eval\lora_v1\
Copy-Item "G:\내 드라이브\blade_lora_v1\runs\<run_name>\config.json","G:\내 드라이브\blade_lora_v1\runs\<run_name>\hashes.json" C:\BLADE\reports\eval\lora_v1\
```

그 다음 `reports/eval/lora_v1/report_template.md`의 표를 metrics.json 값으로 채워 `report.md`를 완성한다(로컬 베이스라인 gpt-4o-mini·qwen CPU 결과는 참고 열).
