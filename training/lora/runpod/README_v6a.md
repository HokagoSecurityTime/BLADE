# S5 LoRA v6a 학습·평가 — RunPod H100 SXM 80GB 실행 안내 (2026-11-04, 자동 정지 포함)

v6a = data-v5 그대로 + 프롬프트 v3.1 + 출력 순서 {evidence_fields, rationale, label, confidence} + label 토큰 확률(label_prob). 사전 기록 AGENTS.md "작업 S5". 학습 3 seed(42·43·44)와 test_v30·test_v5 예측을 한 번에 돌리고 seed마다 결과를 묶는다. test_v31_supp·test_v6은 돌리지 않는다. 커밋 없음.

## 올릴 파일

| 파일 | 내용 |
|---|---|
| `blade_v6a_20261104.tgz` | `data_v6a/`(train_sft_v6a 1274 · val_sft_v6a 179 · test_v30_inputs · test_v5_inputs · test_v5_manifest.json · policy_label_v3.1.md · data_v6a_hashes.json), `runpod/`(run_train_v6.py · run_v6.sh · setup.sh · README_v6a.md), `SHA256SUMS_bundle` |

어댑터·기존 볼륨은 필요 없다(새 학습). 새 Pod(볼륨 없음)면 `/workspace/blade_lora_v3/`를 번들에서 만든다.

## 실행 (Pod 터미널)

```bash
cd /workspace && mkdir -p blade_lora_v3 && tar -xzf blade_v6a_20261104.tgz -C blade_lora_v3
cd blade_lora_v3 && sha256sum -c SHA256SUMS_bundle | tail -3        # 모두 OK
grep -c $'\r' runpod/run_v6.sh                                      # 0 이어야 함(LF)
tmux new -d -s v6 "bash /workspace/blade_lora_v3/runpod/run_v6.sh"
tail -f /workspace/blade_lora_v3/runs/run_v6.log                     # Ctrl-C 로 tail만 종료(실행은 tmux 안에서 계속)
```

단계: 0 해시(data_v6a_hashes.json `c079b9f5…`, test_v5_manifest `57fd384f…`, 파일별 해시) → 1 setup.sh(unsloth 설치; 이미 설치된 Pod는 `SKIP_SETUP=1`) → 2 preflight(베이스 로드 + generate(output_scores) + label 토큰 검사, `preflight done`) → 3 seed 42 → 43 → 44 각각 학습(체크포인트 30 step, 재시작 시 이어감) + 예측 4파일(한 건씩 append, 재시작 시 이어감) → seed마다 `export/blade_v6a_s<seed>_results.tar.gz`·`_adapter.tar.gz` 생성 → 4 전체 tar → Pod 정지.

로그에 차례로 뜨는 표식: `preflight done` → `seed 42: train + eval` → `train done` → `lora_v6a_s42_final oas: 269 rows …` … `seed 42 ok` → … → `ALL DONE` → `POD STOP REQUESTED`. 어느 게이트든 실패하면 `STOP: …` 뒤 있는 결과를 묶고 Pod를 정지한다.

## 예상 시간 (H100)

v5(A100, 4096, 1,274행)는 학습 56분 + 평가였다. v6a는 행당 토큰 1.35배·H100이라 학습 seed당 약 40~55분, 예측 4작업(1,100행, 출력 최대 512 토큰) 약 20~25분 → seed당 65~80분, **3 seed 합계 약 3.5~4시간 + 설치 15분.** 끝나면 Pod가 스스로 정지한다(`STOP_POD=0 bash run_v6.sh`로 실행하면 유지).

## 가져올 파일 (Pod 정지 후 다시 시작해 내려받기, 종료(terminate) 금지)

- `/workspace/blade_lora_v3/export/blade_v6a_all_results.tar.gz` + `SHA256SUMS_blade_v6a` — 보고서(3단계)에 필요한 전부(예측·로그·config·env).
- `/workspace/blade_lora_v3/export/blade_v6a_s42_adapter.tar.gz` 등 — 어댑터(채택 시 GGUF 변환용, 약 160 MB × 3). 당장은 선택.
- 중간에 멈췄으면 있는 `blade_v6a_s<seed>_results.tar.gz`만 보내도 된다(`runs/run_v6.log` 포함).

## 다시 돌릴 때

같은 명령을 다시 실행하면 끝난 seed는 건너뛰고, 중단된 seed는 마지막 체크포인트·이미 쓴 예측 행부터 이어간다. `SEEDS="43 44" bash runpod/run_v6.sh`로 범위를 줄일 수 있다.

## 변경 요약 (v5 대비)

- 시스템 프롬프트 policy_label_v3.1.md(3,798 토큰; v3.0.1 2,699), 출력 키 순서 변경, max_seq_len 4096 → 6144(유일한 하이퍼파라미터 변경), max_new_tokens 256 → 512. LoRA r16·α16·3 epoch·lr 2e-4·batch 2×4·cosine·adamw_8bit·completion-only 마스킹은 동일.
- 예측 파일 이름은 v5와 같다(`predictions_<cond>_lora_v6a_s<seed>_final.jsonl`, `v5test_predictions_…`). 행에 `prompt_tokens`·`output_tokens`·`label_prob{p_first, p_prefix, p_norm, p_seq, candidates, …}`가 추가된다.
