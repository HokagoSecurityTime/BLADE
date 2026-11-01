# LoRA v2 (data-v2) — Colab 실행 안내

프롬프트 v3.0.1 고정, 베이스 `unsloth/Qwen2.5-7B-Instruct-bnb-4bit`, 하이퍼파라미터는 v1과 동일(r=16, alpha=16, lr 2e-4, 3 epoch, batch 2×4, max_seq_len 4096). seed 42·43·44 3회. 이 저장소에서는 학습을 실행하지 않는다.

## 1. Drive 업로드 대상 (로컬 `training/lora/data_v2/` → Drive `MyDrive/blade_lora_v2/data_v2/`)

| 파일 | 내용 |
|---|---|
| train_sft.jsonl | train_v2에서 4096 토큰 초과를 뺀 학습 입력 {id, source, condition, label, user, assistant, tokens} |
| val_sft.jsonl | val_v2 98건, `condition`(oas = val_v30 52건, oas_code = 코드 val 46건) |
| test_v30_inputs.jsonl | test_v30 269건 평가 입력(v1과 동일 파일) |
| policy_label_v3.0.1.md | 프롬프트(system) |
| data_v2_hashes.json | 원본(train_v2/val_v2/test_v30/프롬프트)과 생성 파일 SHA-256. 노트북 셀 4가 대조 |

`training/lora/prepare_lora_v2_inputs.py`로 생성했다(해시는 data_v2_hashes.json과 AGENTS.md data-v2 절).

## 2. Drive 구조

```
MyDrive/blade_lora_v2/
  data_v2/                       ← 위 5개 파일
  runs/lora_v2_seed42/           ← 노트북 생성: config.json, hashes.json, checkpoints/(전부 보존), adapter/, logs/{train_log.jsonl,train_result.json}, eval/predictions_*.jsonl
  runs/lora_v2_seed43/, runs/lora_v2_seed44/
  runs/summary_train.json
```

## 3. 실행 순서

1. `training/lora/lora_v2.ipynb`를 Colab에 업로드(`파일 → 노트 업로드`), 런타임 유형 A100 또는 L4.
2. 셀 1(Drive 마운트) → 2(설정) → 3(설치) → 4(해시 검증; 불일치면 중단) → 5(공통 함수) → 6(학습 3 seed 반복, seed마다 30 step 간격 eval/save, val loss는 `eval_oas_loss`·`eval_oas_code_loss`로 따로 기록) → 7(평가).
3. 세션이 끊기면 같은 노트북에서 1→2→3→4→5→6을 다시 실행. seed별 `checkpoints/`의 마지막 체크포인트에서 재개하고 이미 끝난 seed는 adapter가 있어도 다시 돌지 않도록 하려면 셀 2의 `SEEDS`에서 완료된 seed를 빼면 된다.
4. 셀 7은 seed별로 최종 어댑터 + 조건별 val loss 최저 체크포인트(`best_by_condition`)를 test_v30에서 평가하고, seed 42 폴더에 베이스 모델(어댑터 없음) 결과도 1회 남긴다. 예측 파일 이름 `predictions_{oas|oas_code}_{tag}.jsonl`, 형식은 v1과 동일.

## 4. 결과 회수와 채점

Drive `runs/*/eval/predictions_*.jsonl`, `config.json`, `hashes.json`, `logs/`를 로컬 `reports/eval/lora_v2/<run>/`에 복사한 뒤:

```powershell
cd C:\BLADE
$env:PYTHONPATH="C:\BLADE"
.python\python.exe -X utf8 scripts\eval_v30.py --pred reports\eval\lora_v2\lora_v2_seed42\eval\predictions_oas_lora_v2_s42_final.jsonl ... --md reports\eval\lora_v2\eval_v30.md
```

eval-def v2(route_only 제외 주지표, manual 인정 보조지표, public 오판 재정의, 합성 분리)로 채점된다. 어댑터·체크포인트는 git에 올리지 않고 경로·해시만 기록한다.
