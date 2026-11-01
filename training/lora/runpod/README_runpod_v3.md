# LoRA v3 (data-v3a / data-v3b) — RunPod 실행 안내

실험 규칙은 AGENTS.md 'data-v3 실험 규칙'을 따른다. 먼저 RunPod 환경 기준점으로 data-v2를 seed 42로 한 번 학습하고(Colab LoRA v2 s42와 비교용), 이어서 v3a(manual 쿼터 25%)와 v3b(10%)를 각각 seed 42·43·44로 학습하고, final 어댑터만 test_v30에서 평가한다. 체크포인트 선택과 보류 문턱 조정은 하지 않는다. 하이퍼파라미터는 LoRA v2와 같다. API 키나 토큰은 필요 없다.

## 1. Pod

- GPU는 A100 80GB를 권장한다(L40S·4090 24GB도 가능하지만 느리다). PyTorch 2.x / CUDA 12.x 템플릿을 쓰고, Network Volume을 `/workspace`에 붙인다.
- 예상 시간(A100): 학습 run당 약 35~50분(train 799 / 929 / 786건, 3 epoch), 평가 run당 약 20~30분. 7 run(v2-s42 → v3a ×3 → v3b ×3)이면 약 7~9시간. 끝나면 Pod를 자동으로 정지한다.

## 2. 업로드

Pod의 `/workspace/blade_lora_v3/`가 아래 구조가 되게 올린다. 로컬 `training/lora/data_v3/`, `training/lora/data_v2/`, `training/lora/runpod/`를 그대로 복사하면 된다.

```
/workspace/blade_lora_v3/
  data_v3/   train_sft_v3a.jsonl, train_sft_v3b.jsonl, val_sft_v3.jsonl, test_v30_inputs.jsonl, policy_label_v3.0.1.md, data_v3_hashes.json
  data_v2/   train_sft.jsonl, val_sft.jsonl, test_v30_inputs.jsonl, policy_label_v3.0.1.md, data_v2_hashes.json   (기준점 run용, data-v2 동결본)
  runpod/    run_train.py, run_all.sh, setup.sh, README_runpod_v3.md
```

`run_train.py`는 시작할 때 해시 목록 파일(`data_v3_hashes.json` 또는 `data_v2_hashes.json`)의 SHA-256(동결값)과 각 입력 파일 해시를 대조한다. 하나라도 다르면 중단한다.

## 3. 실행

```bash
cd /workspace/blade_lora_v3/runpod
bash setup.sh                                   # 1회: unsloth 설치, tmux 확인, GPU·버전 출력
tmux new -d -s blade "bash /workspace/blade_lora_v3/runpod/run_all.sh"
tmux attach -t blade                            # 진행 보기, Ctrl-b d로 빠져나오기(학습은 계속됨)
```

- run 하나만 돌릴 때: `python run_train.py --data v3b --seed 43`. 일부만 돌릴 때: `RUNS="v3a:42 v3b:42" bash run_all.sh`.
- 모든 run이 끝나면(성공·실패와 무관) `runpodctl stop pod $RUNPOD_POD_ID`로 Pod를 정지한다. 정지 실패는 무시한다. 정지하지 않으려면 `STOP_POD=0`. Network Volume의 결과는 정지 후에도 남는다.
- 중단 후 같은 명령을 다시 실행하면 이어서 진행한다. 끝난 run(final 어댑터와 예측 파일이 있음)은 건너뛰고, 학습 중이던 run은 마지막 체크포인트(30 step 간격, 최근 2개 보존)에서 재개한다.
- 학습 loss가 nan이거나 발산하면 그 run은 실패로 기록되고 다음 run으로 넘어간다(`runs/run_all.log`에 FAILED).

## 4. 산출물과 회수

run마다 `runs/<run>/` 아래에 다음이 생긴다(run = `lora_v2_s42_runpod`, `lora_v3a_s<seed>`, `lora_v3b_s<seed>`).

- `logs/run.log`(진행 로그), `logs/train_log.jsonl`(loss 기록), `logs/train_result.json`(val loss 포함 — 정상 확인용)
- `config.json`, `env.json`(GPU·라이브러리 버전)
- `adapter/`(final 어댑터)
- `eval/predictions_{oas|oas_code}_<tag>.jsonl` (tag = `lora_v2_s42_runpod_final`, `lora_v3a_s<seed>_final`, `lora_v3b_s<seed>_final`)

로컬로 가져오는 것은 `eval/`, `logs/`, `config.json`, `env.json`이다. 어댑터는 크기가 커서 Pod 볼륨이나 별도 저장소에 둔다. 로컬에는 `reports/eval/lora_v3/<run>/`에 넣고 채점한다. 기준점 run은 Colab `reports/eval/lora_v2/lora_v2_seed42`의 s42 final과 비교한다.

```powershell
cd C:\BLADE
$env:PYTHONPATH="C:\BLADE"
.python\python.exe -X utf8 scripts\eval_v30.py --pred (Get-ChildItem reports\eval\lora_v3\*\eval\predictions_*.jsonl).FullName --md reports\eval\lora_v3\eval_v30.md --out reports\eval\lora_v3\scores.json
```

주지표는 oas_code 합성 제외 macro-F1, 구체 정밀도·재현율, manual 비율, public 오판(신 정의)이다. v3a와 v3b의 우열은 seed 표준편차보다 큰 차이일 때만 인정한다.
