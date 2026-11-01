# LoRA v4 (data-v4) + test_v31_supp — RunPod 실행 안내

실험 규칙은 AGENTS.md 'data-v3 실험 규칙'과 같다. final 어댑터만 평가하고 체크포인트 선택·보류 문턱 조정은 하지 않는다. 하이퍼파라미터는 LoRA v2와 같다. API 키·토큰은 필요 없다.

## 실행 순서 (run_all.sh 기본값)

| 순서 | 항목 | 내용 |
|---:|---|---|
| 1–2 | `v2:43`, `v2:44` | RunPod 기준점 data-v2(기존 s42와 합쳐 3 seed). 학습 + test_v30 + test_v31_supp |
| 3–5 | `v4:42`, `v4:43`, `v4:44` | data-v4 학습 + test_v30 + test_v31_supp |
| 6–9 | `v2:42:eval`, `v3b:42:eval`, `v3b:43:eval`, `v3b:44:eval` | 기존 final 어댑터로 test_v31_supp 예측만 추가(학습 안 함) |
| 10 | `base:0` | 어댑터 없는 베이스 모델, test_v30 + test_v31_supp |

모든 항목이 끝나면 export_results.sh로 결과를 묶고 runpodctl로 Pod를 정지한다. run_all.log 마지막 줄에 정지 여부가 항상 남는다("POD STOP REQUESTED" 또는 "POD NOT STOPPED … STOP THE POD MANUALLY").

예상 시간(A100 80GB): 학습 run 5개 × 약 40–50분 + 평가(test_v30 + supp) run당 약 30–40분, eval-only 4개 × 약 10–15분, 베이스 약 35분 → 약 7–8시간.

## 업로드

Network Volume의 `/workspace/blade_lora_v3/`에 번들을 풀면 아래 구조가 된다(기존 runs/는 그대로 둔다).

```
/workspace/blade_lora_v3/
  data_v2/  data_v3/  data_v4/   (data_v4: train_sft_v4, val_sft_v4, test_v30_inputs, test_v31_supp_inputs, policy_label_v3.0.1.md, data_v4_hashes.json)
  runpod/   run_train.py, run_all.sh, setup.sh, export_results.sh, README_runpod_v4.md
  runs/     (이전 실행 결과: lora_v2_s42_runpod, lora_v3a_s*, lora_v3b_s* — eval-only 항목이 여기 어댑터를 쓴다)
```

**eval-only 항목에는 기존 어댑터가 필요하다.** 볼륨에 `runs/lora_v3b_s42/adapter/adapter_model.safetensors` 등이 없으면(볼륨을 지웠거나 새 Pod), 로컬 `reports/blade_v3_export/blade_v3_adapters.tar.gz`를 올려 `tar -xzf blade_v3_adapters.tar.gz -C /workspace/blade_lora_v3/runs`로 복원한다. 어댑터가 없으면 해당 항목은 학습하지 않고 FAILED로 넘어간다.

## 실행

```bash
cd /workspace/blade_lora_v3 && tar -xzf /workspace/blade_lora_v4_runpod.tgz && bash runpod/setup.sh && tmux new -d -s blade "bash /workspace/blade_lora_v3/runpod/run_all.sh"
```

- 진행 보기 `tmux attach -t blade`(Ctrl-b d로 빠져나옴). 중단 후 같은 명령을 다시 실행하면 끝난 항목은 건너뛰고 이어서 진행한다.
- 시작할 때 각 데이터의 해시 목록(data_v4_hashes.json 등)과 입력 파일 해시를 대조하고, 다르면 중단한다.

## 산출물과 채점

- run마다 `runs/<run>/eval/predictions_{oas|oas_code}_<tag>.jsonl`(test_v30)과 `supp_predictions_{oas|oas_code}_<tag>.jsonl`(test_v31_supp).
- `export/blade_v4_results.tar.gz`(예측·로그), `export/blade_v4_adapters.tar.gz`(어댑터), `SHA256SUMS`, `SUMMARY.tsv`.
- 로컬에서 `reports/eval/lora_v4/`에 풀고 채점:

```powershell
cd C:\BLADE; $env:PYTHONPATH="C:\BLADE"
.python\python.exe -X utf8 scripts\eval_v30.py --pred (Get-ChildItem reports\eval\lora_v4\*\eval\predictions_*.jsonl).FullName --out reports\eval\lora_v4\scores_test_v30.json
.python\python.exe -X utf8 scripts\eval_v31_supp.py --pred (Get-ChildItem reports\eval\lora_v4\*\eval\supp_predictions_*.jsonl).FullName --out reports\eval\lora_v4\scores_supp.json --md reports\eval\lora_v4\eval_supp.md
```

test_v31_supp 예측 파일은 코드 본문이 없지만 .gitignore 대상이다(raw 출력에 발췌 인용 가능).
