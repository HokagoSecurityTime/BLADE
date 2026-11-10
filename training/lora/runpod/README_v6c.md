# S8 LoRA v6c 학습·평가 — RunPod H100 80GB 실행 안내 (2026-11-04, 조기 판정·자동 정지 포함)

v6c = LoRA v5 레시피에서 **베이스 모델만** `unsloth/Qwen2.5-7B-Instruct-bnb-4bit` → `unsloth/Qwen2.5-14B-Instruct-bnb-4bit`로 교체. 데이터 data-v5 train/val, 프롬프트 v3.0.1, 출력 순서(label 먼저), max_seq_len 4096, max_new_tokens 256, LoRA r16·α16·3 epoch·lr 2e-4·cosine·adamw_8bit·batch 2×4, completion-only 마스킹, greedy 디코딩은 v5와 동일. 사전 기록 AGENTS.md "작업 S8". 커밋 없음, test_v6 추론 없음.

## 올릴 파일

| 파일 | 내용 |
|---|---|
| `blade_v6c_20261104.tgz` | `data_v5/`(train_sft_v5 1274 · val_sft_v5 179 · test_v30_inputs 269 · test_v31_supp_inputs 222 · test_v5_inputs 283 · test_v5_manifest.json · policy_label_v3.0.1.md · data_v5_hashes.json — 동결본과 바이트 동일), `runpod/`(run_train_v6c.py · run_v6c.sh · early_gate_v6c.py · setup.sh · README_v6c.md), `baseline/`(v5 s42 test_v5 oas_code 예측, 조기 판정 기준), `SHA256SUMS_bundle` |

어댑터·기존 볼륨은 필요 없다(새 학습). 새 Pod(볼륨 없음)면 `/workspace/blade_lora_v3/`를 번들에서 만든다. 디스크: 베이스 14B 4bit 9.3 GB(HF 캐시) + 체크포인트(seed당 2개 × ≈ 0.5 GB) + 결과 → 컨테이너/볼륨 **40 GB 이상**.

## 실행 (Pod 터미널)

```bash
cd /workspace && mkdir -p blade_lora_v3 && tar -xzf blade_v6c_20261104.tgz -C blade_lora_v3
cd blade_lora_v3 && sha256sum -c SHA256SUMS_bundle | tail -3        # 모두 OK
grep -c $'\r' runpod/run_v6c.sh                                     # 0 이어야 함(LF)
tmux new -d -s v6c "bash /workspace/blade_lora_v3/runpod/run_v6c.sh"
tail -f /workspace/blade_lora_v3/runs/run_v6c.log                    # Ctrl-C 로 tail만 종료(실행은 tmux 안에서 계속)
```

단계(run_v6c.sh): 0 해시(data_v5_hashes.json `39c302c5…`, test_v5_manifest `57fd384f…`, 프롬프트 `d0913c27…`, 파일별 해시) → 1 setup.sh(unsloth 설치; 이미 설치된 Pod는 `SKIP_SETUP=1`) → 2 preflight(14B 로드 + 짧은 generate + 메모리, `preflight done`) → 3 **seed 42** 학습(체크포인트 30 step, 재시작 시 이어감) + 예측 6파일(test_v30·test_v31_supp·test_v5 × oas·oas_code, 한 건씩 append, 재시작 시 이어감) → pack → **조기 판정**(early_gate_v6c.py: v6c s42 test_v5 oas_code macro-F1 ≤ v5 s42 0.6661이면 `GATE=STOP` → s43·s44·base 미실행, 전체 tar, Pod 정지) → 4 seed 43 → 5 seed 44 → 6 base 14B zero-shot(어댑터 없음, 6작업; 판정에 쓰지 않음) → 7 전체 tar → Pod 정지.

로그 표식: `preflight done` → `seed 42: train + eval` → `loss mask check (row 0)` → `train done` → `lora_v6c_s42_final oas: 269 rows …` … `seed 42 ok` → `GATE=PASS|STOP` → … → `ALL DONE` → `POD STOP REQUESTED`. 어느 게이트든 실패하면 `STOP: …` 뒤 있는 결과를 묶고 Pod를 정지한다.

## 예상 시간 (H100, reports/eval/lora_v6c/prep.md 4절)

학습 50~65분/seed, 예측 6작업(1,544행, 출력 최대 256 토큰) 약 20분 → seed당 70~90분. 조기 판정 통과 시 3 seed + base zero-shot(≈ 25분) **합계 약 4~5시간 + 설치 15분 + 베이스 9.3 GB 다운로드**. 조기 STOP이면 약 1.5시간. 끝나면 Pod가 스스로 정지한다(`STOP_POD=0 bash runpod/run_v6c.sh`로 실행하면 유지, `STOP_DELAY_MIN=10`으로 내려받을 여유를 둘 수 있음).

## 가져올 파일 (Pod 정지 후 다시 시작해 내려받기, 종료(terminate) 금지)

- `/workspace/blade_lora_v3/export/blade_v6c_all_results.tar.gz` + `SHA256SUMS_blade_v6c` — 보고서(3단계)에 필요한 전부(예측·로그·config·env·early_gate.json·preflight.json·timing).
- `/workspace/blade_lora_v3/export/blade_v6c_lora_v6c_s42_adapter.tar.gz` 등 — 어댑터(채택 시 GGUF 변환용, 14B r16 ≈ 275 MB × 3). 당장은 선택.
- 중간에 멈췄으면 있는 `blade_v6c_lora_v6c_s<seed>_results.tar.gz`만 보내도 된다(`runs/run_v6c.log` 포함).
- `RETRIEVE_CMD="scp-or-rclone-command"`를 주면 pack마다 그 명령에 아카이브 경로를 넘겨 Pod 밖으로 보낸다.

## 다시 돌릴 때

같은 명령을 다시 실행하면 끝난 seed는 건너뛰고, 중단된 seed는 마지막 체크포인트·이미 쓴 예측 행부터 이어간다. `SEEDS="43 44" bash runpod/run_v6c.sh`로 범위를 줄일 수 있다(첫 seed가 조기 판정 대상이 되므로 42가 끝난 뒤에만). `RUN_BASE14B=0`이면 base zero-shot을 건너뛴다.

## 변경 요약 (v5 대비)

- 베이스 모델만 14B. 토크나이저·chat_template은 7B와 바이트 동일(tokenizer.json SHA `9c5ae00e…`)이라 train_on_responses_only 경계·토큰 수(train 최대 4085, 4096 초과 0)는 그대로다.
- 예측 파일 이름은 v5와 같다(`predictions_<cond>_lora_v6c_s<seed>_final.jsonl`, `supp_predictions_…`, `v5test_predictions_…`). 행에 `prompt_tokens`·`output_tokens`가 추가되고, 파일마다 `.timing.json`(시간·메모리)이 생긴다. train_result.json에 피크 GPU 메모리·trainable 파라미터·padding_free 설정을 기록한다.
- 채택 시 GGUF 병합 Pod 요건: RAM ≥ 80 GB(fp32 병합 ≈ 59 GB), 컨테이너 디스크 ≥ 120 GB(병합 fp16 29.5 GB + f16 GGUF 29.5 GB + Q4_K_M 8.4 GB + 베이스). 로컬 CPU 추론은 정책당 ≈ 140~160 s(v5 72.8 s).
