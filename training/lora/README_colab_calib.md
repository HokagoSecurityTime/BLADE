# LoRA v2 보류 문턱 조정 — Colab 스코어링 안내 (lora_v2_abstain_calib.ipynb)

목적: LoRA v2 final 어댑터(seed 42·43·44)가 과보류(정답 구체 label을 manual로 답함)하는 문제에 대해, **생성 대신 label 조건부 로그확률**을 계산해 두고 로컬에서 manual 감점 b를 val_v2로만 고른다. 학습·API 키·토큰 불필요. test로 b를 고르지 않는다.

## 0. rev 2 (2026-10-24) — 1차 실행 점수 무효, 재실행 필요

1차 실행(2026-10-24 회수) 점수는 **무효**로 판단한다: 모든 파일이 `mode=full`(왼쪽 패딩)로 계산됐고 최고 label 로그확률이 약 −20 nat(정상은 0 근처), oas_code에서 b=0 argmax와 생성 예측 일치율이 55~62%였다. 또 다운로드 폴더 이름과 파일 tag가 어긋나(폴더 seed42에 s43 파일, seed43·seed44에 같은 s44 파일) s42 점수가 없었다. rev 2 노트북은 (1) `for_inference()` 적용, (2) full 모드를 오른쪽 패딩·절대 위치 인덱싱으로 변경, (3) 셀 6에서 greedy 생성 label과 스코어 argmax 일치·최고 로그확률 > −3 을 확인하고 실패하면 중단, (4) 어댑터 로드마다 1건 재검증, (5) `RESCORE=True`면 기존 rev 1 파일을 `.rev1.bak`으로 옮기고 재계산한다. 회수 시 **폴더 이름이 아니라 파일 이름의 `_s<N>_` tag**를 기준으로 `reports/eval/lora_v2/calib/lora_v2_seed<N>/`에 넣는다(calib_abstain.py도 tag로 파일을 찾고 폴더·tag 불일치나 서로 다른 중복 파일이면 중단).

**rev 2 실행 완료 (2026-10-26, RunPod)**: `lora_v2_abstain_calib_runpod.ipynb`(`python build_notebook_calib.py runpod`로 생성; Drive 마운트 대신 `/workspace/blade_lora_v2`, 셀 4~8은 Colab판과 동일)로 3 seed 12개 파일을 회수했다. 전부 rev 2·`mode=full`, 생성 예측과 b=0 argmax 일치 95.1~99.3%. 선택 b는 세 seed 모두 0(val_v2 oas_code에서 b=0부터 public 오판 2~3/23 → 규칙 적용 불가). 결과 `reports/eval/lora_v2/abstain_calib.md`.

## 1. 전제

- Drive `MyDrive/blade_lora_v2/data_v2/`에 v2 학습 때 올린 5개 파일이 그대로 있어야 한다(train_sft.jsonl, val_sft.jsonl, test_v30_inputs.jsonl, policy_label_v3.0.1.md, data_v2_hashes.json). 노트북 셀 4가 해시를 대조하고 불일치면 중단한다.
- `MyDrive/blade_lora_v2/runs/lora_v2_seed{42,43,44}/adapter/`에 final 어댑터가 있어야 한다(v2 학습 노트북 산출물).

## 2. 실행 순서

1. `training/lora/lora_v2_abstain_calib.ipynb`를 Colab에 업로드, 런타임 A100(또는 L4).
2. 셀 1(Drive) → 2(설정) → 3(설치) → 4(데이터·해시 검증) → 5(함수) → 6(cache/full 방식 일치 검사) → 7(실행) → 8(요약).
3. 셀 7은 seed별로 val oas 52 · val oas_code 46 · test oas 269 · test oas_code 265 입력에 대해 7개 label 점수를 기록한다. 중단되면 같은 순서로 다시 실행하면 이미 기록된 id는 건너뛴다.
4. 예상 시간(A100): 어댑터당 15~25분(prefix KV 캐시 재사용) → 3 seed 약 1시간. `INCLUDE_BASE=True`로 바꾸면 베이스 모델 점수도 seed 42 폴더에 남긴다(선택).

## 3. 점수 계산 방식

- 입력 = system(v3.0.1) + user(payload) + assistant 접두 `{"label": "`. 각 label에 대해 `label + "` 토큰열의 로그확률 합을 teacher forcing으로 계산한다. label 토큰열은 접두와 따로 토크나이즈해 이어붙이며, 로컬에서 Qwen2.5 토크나이저로 7개 label 모두 전체 토큰화와 일치함을 확인했다(public 2토큰, role_required·membership_required·tenant_match·owner_match 3토큰, owner_or_admin·manual_review_required 4토큰).
- cache 모드(prefix 1회 forward + label별 continuation)와 full 모드(label별 전체 시퀀스) 결과를 셀 6에서 대조하고, 차이가 0.1 nat을 넘거나 cache가 실패하면 full로 전환한다.
- 출력 레코드: `{id, label(정답), source, security_state, split, condition, tag, scores{7 label: logprob}, first_token_argmax, prompt_tokens, truncated, ms, mode}`.

## 4. 산출물 회수와 로컬 채점

Drive `runs/lora_v2_seed<N>/calib/scores_{val|test}_{oas|oas_code}_lora_v2_s<N>_final.jsonl`(12개)을 로컬 `reports/eval/lora_v2/calib/lora_v2_seed<N>/`로 복사한 뒤:

```powershell
cd C:\BLADE
$env:PYTHONPATH="C:\BLADE"
.python\python.exe -X utf8 scripts\calib_abstain.py
```

- `scripts/calib_abstain.py`: manual 점수에 감점 b(0~40, 0.25 간격)를 적용해 argmax 판정 → val_v2에서 b별 macro-F1·manual 비율·구체 정밀도/재현율·public 오판 → **선택 규칙(사전 고정)**: val_v2 oas_code에서 public 오판(신 정의) 0을 유지하는 b 범위 안에서 구체 재현율 최대, 동률은 가장 작은 b → 선택 b를 test_v30에 1회 적용해 eval-def v2로 채점(seed별·평균). test의 b 곡선도 출력하되 선택에 쓰지 않는다.
- 산출: `reports/eval/lora_v2/abstain_calib.md`, `reports/eval/lora_v2/calib/calib_results.json`, `reports/eval/lora_v2/calib/predictions/predictions_{cond}_{tag}_calib_{b0|bsel}.jsonl`(eval_v30 형식).
- 시작·종료 시 data-v1·data-v2 해시를 assert한다. test_v30·train·val 파일은 읽기만 한다.

## 5. 금지

- 노트북·스크립트 어디에도 API 키·GitHub 토큰을 넣지 않는다. 어댑터·점수 파일은 Drive에 두고, 점수 jsonl만 로컬 git에 보관한다(소형).
- test_v30 점수로 b를 고르지 않는다(규칙 위반 시 결과 무효).
