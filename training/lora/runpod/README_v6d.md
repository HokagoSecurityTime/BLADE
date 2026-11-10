# C′ LoRA v6d 학습·평가 — RunPod 실행 안내 (2026-11-05, 자동 정지 포함)

v6d = LoRA v5 레시피에서 **학습 정답(data-v5 → data-v6d)만** 교정. 베이스 `unsloth/Qwen2.5-7B-Instruct-bnb-4bit`(S8 14B 불채택), 프롬프트 v3.0.1, 출력 순서(label 먼저), max_seq_len 4096, max_new_tokens 256, LoRA r16·α16·3 epoch·lr 2e-4·cosine·adamw_8bit·batch 2×4, completion-only 마스킹, greedy 디코딩은 v5와 동일. data-v6d = data-v5 SFT 행에서 C1 확정 label 36건 + C2 rationale 42건만 바뀐 것(user 입력 바이트 동일). 사전 기록 AGENTS.md "작업 C′". 커밋 없음, test_v6 추론 없음.

## 올릴 파일

| 파일 | 내용 |
|---|---|
| `blade_v6d_20261105.tgz` | `data_v6d/`(train_sft_v6d 1274 · val_sft_v6d 179 · test_v30_inputs 269 · test_v31_supp_inputs 222 · test_v5_inputs 283 · test_v5_manifest.json · policy_label_v3.0.1.md · data_v6d_hashes.json — 동결본과 바이트 동일), `runpod/`(run_train_v6d.py · run_v6d.sh · setup.sh · README_v6d.md), `SHA256SUMS_bundle` |

**새 Pod에서 번들만으로 돈다.** 어댑터·기존 네트워크 볼륨·이전 실행 기록은 필요 없다. 베이스 7B는 HF 허브에서 `/workspace/hf`로 내려받고(공개 모델, 토큰 불필요), `/workspace/blade_lora_v3/`는 번들에서 만든다. Pod 사양: RunPod **PyTorch 2.x 템플릿**, GPU A100 80GB 또는 H100(v5·S5·S8과 같은 급), **컨테이너 디스크 40 GB 이상**(베이스 5.6 GB + 체크포인트 seed당 2개 × ≈ 0.2 GB + 결과), 네트워크 볼륨 없음.

**Pod 정지는 필수이며 스크립트가 보장한다**: 시작 직후 `ensure_stop`이 정지 수단(runpodctl + `RUNPOD_POD_ID`; 없으면 runpodctl 설치 시도 → 그래도 없으면 `RUNPOD_API_KEY`로 GraphQL podStop)을 확인하고, **없으면 학습을 시작하지 않고 종료한다**(`REQUIRE_STOP=1` 기본). 정상 종료·게이트 STOP·오류 종료 모두 EXIT trap으로 `stop_pod`가 실행된다. RunPod 공식 템플릿에는 runpodctl과 `RUNPOD_POD_ID`가 들어 있어 보통 추가 설정이 없다. 혹시 모를 대비로 Pod 환경변수에 `RUNPOD_API_KEY`(RunPod 설정 > API Keys)를 넣어 두면 대체 경로가 생긴다(키는 로그에 남지 않는다).

## 실행 (Pod 터미널)

```bash
cd /workspace && mkdir -p blade_lora_v3 && tar -xzf blade_v6d_20261105.tgz -C blade_lora_v3
cd blade_lora_v3 && sha256sum -c SHA256SUMS_bundle | tail -3        # 모두 OK
grep -c $'\r' runpod/run_v6d.sh                                     # 0 이어야 함(LF)
command -v tmux >/dev/null || (apt-get update -qq && apt-get install -y -qq tmux)   # 새 템플릿에 tmux가 없을 때
tmux new -d -s v6d "bash /workspace/blade_lora_v3/runpod/run_v6d.sh"
tail -f /workspace/blade_lora_v3/runs/run_v6d.log                    # Ctrl-C 로 tail만 종료(실행은 tmux 안에서 계속)
```

tmux 대신 `nohup bash runpod/run_v6d.sh > runs/nohup.out 2>&1 &`도 된다. 로그 첫 줄들에 `auto-stop armed: …`가 있어야 한다. `ABORT before training: this pod cannot be stopped from the script`가 보이면 `export RUNPOD_API_KEY=…` 후 다시 실행한다.

단계(run_v6d.sh): 0 해시(data_v6d_hashes.json `82efda86…`, test_v5_manifest `57fd384f…`, 프롬프트 `d0913c27…`, 파일별 해시) → 1 setup.sh(unsloth 설치; 이미 설치된 Pod는 `SKIP_SETUP=1`) → 2 preflight(7B 로드 + 짧은 generate + 메모리, `preflight done`) → 3 **seed 42** 학습(체크포인트 30 step, 재시작 시 이어감) + 예측 6파일(test_v30·test_v31_supp·test_v5 × oas·oas_code, 한 건씩 append, 재시작 시 이어감) → pack → 4 seed 43 → 5 seed 44 → 6 전체 tar → Pod 정지. 조기 판정은 없다(C′ 사전 기록에 없음). 채택 판정은 결과 회수 후 로컬에서 3 seed 평균으로 한다(scripts/eval_test_v5.py · eval_v30.py · eval_v31_supp.py, 보고 reports/eval/lora_v6d/report.md).

로그 표식: `auto-stop armed` → `preflight done` → `seed 42: train + eval` → `loss mask check (row 0)` → `train done` → `lora_v6d_s42_final oas: 269 rows …` … `seed 42 ok` → … → `ALL DONE` → `script exiting (rc=0)` → `POD STOP REQUESTED`. 게이트가 실패하면 `STOP: …` 뒤 있는 결과를 묶고 Pod를 정지한다. 어떤 경로로 끝나든 마지막은 `POD STOP REQUESTED`다(없으면 콘솔에서 직접 정지).

## 예상 시간

v5(A100 80GB, 7B) 기준 학습 56분/seed + 예측 6작업 약 12분 → seed당 약 70분, **3 seed 합계 약 3.5시간 + 설치·베이스 다운로드 15분**. 끝나면 Pod가 스스로 정지한다(기본). `STOP_DELAY_MIN=10`으로 정지 전 내려받을 여유를 둘 수 있고, `STOP_POD=0`은 디버그용이며 기본이 아니다.

## 가져올 파일 (Pod 정지 후 다시 시작해 내려받기, 종료(terminate) 금지)

- `/workspace/blade_lora_v3/export/blade_v6d_all_results.tar.gz` + `SHA256SUMS_blade_v6d` — 보고서에 필요한 전부(예측·로그·config·env·preflight.json·timing).
- `/workspace/blade_lora_v3/export/blade_v6d_lora_v6d_s42_adapter.tar.gz` 등 — 어댑터(채택 시 GGUF 변환용, 7B r16 ≈ 160 MB × 3).
- 중간에 멈췄으면 있는 `blade_v6d_lora_v6d_s<seed>_results.tar.gz`만 보내도 된다(`runs/run_v6d.log` 포함).
- `RETRIEVE_CMD="scp-or-rclone-command"`를 주면 pack마다 그 명령에 아카이브 경로를 넘겨 Pod 밖으로 보낸다.

## 다시 돌릴 때

같은 명령을 다시 실행하면 끝난 seed는 건너뛰고, 중단된 seed는 마지막 체크포인트·이미 쓴 예측 행부터 이어간다. `SEEDS="43 44" bash runpod/run_v6d.sh`로 범위를 줄일 수 있다.

## 변경 요약 (v5 대비)

- 학습 데이터만 data-v6d(training/lora/data_v6d/, 해시 AGENTS.md 'data-v6d 동결'). 토큰 수 최대 4085(4096 초과 0). 예측 파일 이름은 v5와 같은 규약(`predictions_<cond>_lora_v6d_s<seed>_final.jsonl` 등)이며 행에 `prompt_tokens`·`output_tokens`, 파일마다 `.timing.json`이 추가된다(S8과 동일 포맷).
- 중단 규칙(사전 기록): 2026-11-08 12:00 KST까지 결과 없거나 기준 미달이면 C′ 중단, v5 유지.
