# data-v7 LoRA v7 학습 — RunPod 실행 안내 (2026-11-07, 자동 정지 포함)

v7 = LoRA v5 레시피(베이스 7B, 프롬프트 v3.0.1, label 먼저, 4096/256, r16·α16·3 epoch·lr 2e-4·batch 2×4·cosine·adamw_8bit, completion-only, greedy) 그대로, **학습 데이터만 data-v7**(train 1,540 / val 159). 사전 기록 AGENTS.md "작업 data-v7". 커밋 없음.

**평가 범위**: Pod에서는 **test_v30만**(oas·oas_code) 예측한다. test_v31_supp·test_v5는 data-v7의 학습 데이터라 평가하지 않으며 번들에도 없다(run_train_v7.py·run_v7.sh가 존재 자체를 거부). test_v6(S9 hold-out)은 사람 확인 후 동결되면 `--eval-only --jobs v6test`로 따로 돌린다(TESTV6 manifest 해시 게이트).

## 올릴 파일

| 파일 | 내용 |
|---|---|
| `blade_v7_20261107.tgz` | `data_v7/`(train_sft_v7 1540 · val_sft_v7 159 · test_v30_inputs 269 · policy_label_v3.0.1.md · data_v7_hashes.json), `runpod/`(run_train_v7.py · run_v7.sh · setup.sh · README_v7.md), `SHA256SUMS_bundle` |

## 실행

```bash
cd /workspace && mkdir -p blade_lora_v3 && tar -xzf blade_v7_20261107.tgz -C blade_lora_v3
cd blade_lora_v3 && sha256sum -c SHA256SUMS_bundle | tail -3        # 모두 OK
grep -c $'\r' runpod/run_v7.sh                                      # 0
tmux new -d -s v7 "bash /workspace/blade_lora_v3/runpod/run_v7.sh"
tail -f /workspace/blade_lora_v3/runs/run_v7.log
```

단계: 0 해시(data_v7_hashes.json `bd33f1bc…`, 프롬프트 `d0913c27…`, 파일별) → 1 setup.sh(이미 설치면 `SKIP_SETUP=1`) → 2 preflight → 3~5 seed 42·43·44(학습 + test_v30 예측 2파일, 체크포인트·행 단위 resume, seed마다 pack) → 6 전체 tar → Pod 정지. 표식 `preflight done` → `seed 42 ok` → … → `ALL DONE` → `POD STOP REQUESTED`.

## 예상 시간

H100 기준 학습 약 30분/seed(v6d 24.6분 × 1,540/1,274), test_v30 예측 2작업 약 4분 → 3 seed 약 1시간 45분 + 설치. A100이면 약 2배.

## 가져올 파일

`export/blade_v7_all_results.tar.gz` + `SHA256SUMS_blade_v7`(보고서용), `blade_v7_lora_v7_s4*_adapter.tar.gz`(S9 test_v6 평가·채택 시 GGUF용, 3개 모두 보관). Pod는 종료(terminate)하지 말고 정지(stop) — S9를 같은 Pod·같은 라이브러리에서 돌린다.

## S9: test_v6 평가 (test_v6 동결 후, 같은 Pod·같은 라이브러리)

사전 기록(AGENTS.md "작업 data-v7"): v5 어댑터 3개(s42·43·44) + v7 어댑터 3개를 test_v6 oas_code로 **한 번에** 추론한다. test_v5·test_v31_supp는 돌리지 않는다.

test_v6 동결(2026-11-08, A안: AI 1차 확정 + 독립 AI 2차 검수 + 경계 사례 사람 확정): 289건, 제외 13. manifest `datasets/blade/processed/data_v6/test_v6_manifest.json` SHA-256 `a9ca4fca05ee3e59226411c08c9f102440d5f36b2d4b45dc870bd74e346f3edc`(= run_train_v7.py TESTV6 sha = run_s9.sh HASH_TESTV6_MANIFEST), 입력 `test_v6_inputs.jsonl` 289행 `33d1aecdbd1a685416523eddf73722e105c2c761154a6bf95403fe1431435741`.

S9 번들 `blade_s9_test_v6_20261108.tgz`: `data_v7/test_v6_inputs.jsonl` + `data_v7/test_v6_manifest.json`, `runpod/run_train_v7.py`(TESTV6 sha 기입판 — 기존 파일 덮어쓰기), `runpod/run_s9.sh`, `runpod/README_v7.md`, `SHA256SUMS_s9`. v5 어댑터는 별도 파일 `blade_v5_adapters.tar.gz`(SHA-256 `db6abe46438b27795b51a12e875d24678932e5b3bcd3f50edb152275b294f983`, 903 MB; lora_v4_s4*·lora_v5_s4* 어댑터 포함) — 볼륨에 `runs/lora_v5_s4{2,3,4}/adapter`가 이미 있으면 생략. v7 어댑터는 run_v7.sh가 남긴 `runs/lora_v7_s4{2,3,4}/adapter`를 그대로 쓴다(같은 Pod).

```bash
# v7 학습 결과(runs/lora_v7_s4*/adapter)가 있는 볼륨에서. 경로가 /workspace-2이면 BASE=/workspace-2/blade_lora_v3 (run_s9.sh는 /workspace, /workspace-2 중 있는 쪽을 자동 선택; 기존 파일은 그대로 두고 덮어쓰기만)
BASE=/workspace/blade_lora_v3; cd $BASE
tar -xzf /path/to/blade_s9_test_v6_20261108.tgz                         # data_v7/test_v6_* 추가 + runpod/run_train_v7.py·run_s9.sh·README 덮어쓰기
sha256sum -c SHA256SUMS_s9 | tail -3                                     # 모두 OK
tar -xzf /path/to/blade_v5_adapters.tar.gz -C runs/                      # runs/lora_v5_s42/adapter … (이미 있으면 생략)
ls -d runs/lora_v5_s4*/adapter runs/lora_v7_s4*/adapter                  # 6개
tmux new -d -s s9 "BASE=$BASE bash $BASE/runpod/run_s9.sh"
tail -f $BASE/runs/run_s9.log
```

순서: 해시(data_v7·프롬프트·test_v6 manifest·입력 289행·run_train_v7.py TESTV6 sha·어댑터 6개 존재) → imports(실패 시에만 setup.sh) → v5 s42 → s43 → s44 → v7 s42 → s43 → s44(각 `--eval-only --jobs v6test`, oas + oas_code 289행, 행 단위 resume, run마다 pack) → 전체 tar → `runpodctl stop pod`. 표식 `lora_v5_s42 ok` … `lora_v7_s44 ok` → `ALL DONE` → `POD STOP REQUESTED`. 예상 H100 run당 약 4분(289 × 2 조건), 6 run 약 25분 + 모델 로드.

회수: `export/blade_s9_all_v6test.tar.gz` + `export/SHA256SUMS_s9`(run별 `blade_s9_lora_<v5|v7>_s<seed>_v6test.tar.gz`는 보조). 예측 파일 `runs/<run>/eval/v6test_predictions_{oas,oas_code}_<tag>.jsonl`. TESTV6 sha가 비어 있거나 manifest·입력이 없거나 다르면 스크립트가 test_v6 작업을 만들지 않는다. 로컬 채점은 `BLADE_TESTV6_STAGE=S9`에서만 가능(scripts/testv6_guard.py).
