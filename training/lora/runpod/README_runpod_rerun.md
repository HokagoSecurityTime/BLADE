# RunPod 재실행 가이드 — 작업 A·B·C (2026-10-30 작성)

이 문서는 LoRA v4 실행(2026-10-27, `reports/eval/lora_v4/`) 이후에 RunPod에서 실험을 다시 돌릴 때 따르는 절차다. 기존 안내(`README_runpod_v3.md`, `README_runpod_v4.md`)와 실험 규칙(AGENTS.md 'data-v3 실험 규칙')은 그대로 유효하고, 여기서는 세 작업에 필요한 차이점만 더한다. 코드 변경은 아직 하지 않았다. 3절·4절의 변경안을 적용한 뒤에 실행한다.

## 0. 어느 작업에 RunPod이 필요한가

| 작업 | RunPod | 내용 | 예상 GPU 시간(A100 80GB) |
|---|---|---|---:|
| A. 보조 지표 재채점 | 불필요 | `reports/eval/lora_v4/*/eval/*.jsonl` 기존 예측만 재채점 | 0 |
| B. 출력 안정화 재추론 | 필요(평가만) | 10개 모델(base, v2·v3b·v4 각 3 seed) × test_v30 2조건 + supp 2조건, 디코딩 설정만 변경 | 약 3~5시간 |
| C-1~C-3. test_v5·data-v5 구축 | 불필요 | 라벨링·검수·동결(사람 승인 정지 지점 4곳) | 0 |
| C-4. LoRA v5 학습·평가 | 필요(학습 3 + 평가) | v5 s42·43·44 학습, v4·base는 test_v5 예측만 추가 | 약 4.5~5시간 |

마감: C-4 평가는 일요일(2026-11-01) 18:00까지 끝나야 한다. 채점·보고에 2시간을 남기면 **토요일(10-31) 낮 12:00 전에 C-4를 시작**해야 한다. C-1~C-3의 사람 검수가 그 전에 끝나지 않으면 v5는 발표에서 제외한다(작업 C 원칙).

## 1. 변하지 않는 것 (모든 재실행 공통)

- **환경**: A100 80GB(SXM), PyTorch 2.x / CUDA 12.x 템플릿, Network Volume을 `/workspace`에 붙인다. 10-27 실행 환경은 `reports/eval/lora_v4/lora_v4_s42/env.json`에 있다(torch 2.14.1+cu130, transformers 5.17.0, trl 1.15.0, peft 0.21.2, unsloth 2026.10.9, python 3.12.3). setup.sh는 `pip install unsloth`로 최신을 받으므로 버전이 달라질 수 있다. 달라지면 env.json에 기록되고, 보고서에 "환경 차이"로 적는다.
- **볼륨 배치**: `/workspace/blade_lora_v3/{data_v2,data_v3,data_v4,runpod,runs,export}`. 디렉터리 이름은 v3 때 것을 계속 쓴다(스크립트 기본값 `BASE=/workspace/blade_lora_v3`).
- **해시 assert**: `run_train.py verify()`가 해시 목록 파일(`data_v*_hashes.json`)의 SHA-256을 `DATASETS[...]['sha']`와 대조하고, 목록 안의 입력 파일 해시를 다시 대조한다. 하나라도 다르면 중단한다. 해시 목록을 고쳐서 통과시키지 않는다. 동결 파일을 다시 복사한다.
- **고정 규칙**: final 어댑터만 평가, 체크포인트 선택·보류 문턱(MIN_CONFIDENCE) 조정 금지, 하이퍼파라미터 `HP`(LoRA v2와 동일)·프롬프트 v3.0.1 고정. 생성 설정 기본값은 greedy(do_sample=False), max_new_tokens 256, eval_batch 8, left padding, max_seq_len 4096이다. 작업 B만 이 중 디코딩 두 항목(repetition_penalty, 스키마 제약)을 바꾼다.
- **어댑터 보관**: 저장소에는 어댑터가 없다. 볼륨 `runs/<run>/adapter/`가 원본이다. 로컬 백업은 v2-s42·v3a·v3b는 `reports/blade_v3_export/blade_v3_adapters.tar.gz`, v2-s43·44와 v4 3 seed는 다운로드 폴더의 `blade_v4_adapters.tar.gz`(1.8GB)다. **볼륨을 지웠거나 새 볼륨이면 작업 B·C-4 전에 두 tar를 `runs/`에 복원해야 한다.** 어댑터가 없는 eval-only 항목은 학습하지 않고 FAILED로 넘어간다.
- **Pod 정지**: run_all.sh가 모든 항목 뒤에 `runpodctl stop pod $RUNPOD_POD_ID`를 호출하고 run_all.log 마지막 줄에 "POD STOP REQUESTED" 또는 "POD NOT STOPPED …"를 남긴다. 주의 두 가지. (1) export_results.sh는 정지 직전에 run_all.log를 tar에 넣으므로 **로컬로 가져온 run_all.log에는 정지 줄이 없다**(10-27 로컬 로그는 "all runs ended"에서 끝난다). (2) 10-27 오전 실행에서는 "pod stop skipped by shim"으로 정지가 실행되지 않았다. 따라서 정지 확인은 로컬 PC에서 `runpodctl get pod <POD_ID>`를 실행해 상태(EXITED/STOPPED)를 보고 그 출력 줄을 보고서에 붙인다. 콘솔 확인도 병행한다.
- **시간대**: run_all.log 시각은 UTC다. KST = UTC+9.

## 2. 공통 절차 (체크리스트)

### 2.1 로컬에서 번들 만들기 (PowerShell, C:\BLADE)

tgz 안의 경로가 `data_v4/...`, `runpod/...`처럼 `training/lora/` 아래 이름으로 시작해야 한다. Windows 기본 `tar`(bsdtar)로 만든다.

```powershell
cd C:\BLADE
tar -czf "$env:USERPROFILE\Downloads\blade_lora_runpod_$(Get-Date -Format yyyyMMdd).tgz" -C training\lora data_v2 data_v3 data_v4 runpod
# C-4 때는 data_v5 를 추가한다:  -C training\lora data_v2 data_v3 data_v4 data_v5 runpod
Get-FileHash "$env:USERPROFILE\Downloads\blade_lora_runpod_*.tgz" -Algorithm SHA256
```

번들에 들어가는 입력 파일이 동결 해시와 같은지 올리기 전에 확인한다(`data_v4_hashes.json`의 `generated` 항목과 `Get-FileHash` 비교).

### 2.2 Pod 시작과 업로드

1. RunPod 콘솔에서 기존 Network Volume을 붙여 A100 80GB Pod를 만든다(PyTorch 2.x 템플릿). 볼륨이 있는 데이터센터의 GPU만 고를 수 있다.
2. 업로드는 Jupyter Lab의 업로드 버튼(가장 단순) 또는 로컬 `runpodctl send <파일>` → Pod에서 `runpodctl receive <코드>`. 번들은 `/workspace/`에 둔다(볼륨이라 Pod를 바꿔도 남는다).
3. 풀고 사전 점검:

```bash
cd /workspace/blade_lora_v3 && tar -xzf /workspace/blade_lora_runpod_<날짜>.tgz
bash runpod/setup.sh                              # unsloth 설치, torchaudio 충돌 제거, GPU·버전 출력
ls runs/*/adapter/adapter_model.safetensors        # eval-only 대상 어댑터가 모두 있는지 (base 제외 9개 이상)
df -h /workspace; nvidia-smi --query-gpu=name,memory.total --format=csv
command -v runpodctl && echo "POD_ID=$RUNPOD_POD_ID"   # 둘 중 하나가 없으면 자동 정지가 안 된다 → 끝나고 수동 정지
sha256sum data_v4/data_v4_hashes.json             # DATASETS['v4']['sha'] = df24db70… 과 같아야 한다
```

어댑터가 없으면 로컬 tar를 올려 복원한다: `tar -xzf blade_v3_adapters.tar.gz -C /workspace/blade_lora_v3/runs` (v4도 같은 방식).

### 2.3 실행과 감시

```bash
tmux new -d -s blade "RUNS='<항목 목록>' bash /workspace/blade_lora_v3/runpod/run_all.sh"
tmux attach -t blade          # Ctrl-b d 로 빠져나오기
tail -f /workspace/blade_lora_v3/runs/run_all.log
```

- 항목 형식은 `data:seed`(학습+평가) 또는 `data:seed:eval`(평가만, 학습 안 함). `RUNS`를 비우면 run_all.sh 기본값(v4 실험 목록)이 돌아가므로 **반드시 RUNS를 명시**한다.
- 끝난 항목은 건너뛰고(final 어댑터 + 예측 파일 존재), 중단된 학습은 마지막 체크포인트에서 재개한다. 연결이 끊겨도 tmux 안의 작업은 계속된다.
- 첫 항목이 끝나면 run.log의 "rows, parse errors, manual" 줄과 걸린 시간을 보고 전체 예상 시간을 다시 계산한다.

### 2.4 회수와 검증

1. 모든 항목이 끝나면 run_all.sh가 `export_results.sh`를 실행해 `export/blade_v4_results.tar.gz`(예측·로그·config·env), `export/blade_v4_adapters.tar.gz`, `SHA256SUMS`, `SUMMARY.tsv`를 만든다. 파일 이름은 스크립트 상수라 v5에서도 `blade_v4_*`로 나온다. 혼동을 막으려면 export_results.sh의 두 이름을 작업별로 바꾼다(3·4절).
2. Pod가 정지되기 전에 받아야 하므로, 자동 정지가 켜져 있으면 **다음 Pod 시작 때** 볼륨 `export/`에서 받는다. 바로 받고 싶으면 `STOP_POD=0`으로 실행하고 받은 뒤 수동 정지한다.
3. 로컬에서 해시를 맞춘다: `Get-FileHash` 결과와 SHA256SUMS 비교. 다르면 다시 받는다.
4. 작업별 디렉터리에 푼다(`reports/eval/stable_decoding/`, `reports/eval/lora_v5/`). `.gitignore`에 그 디렉터리의 `**/supp_predictions_*.jsonl`(test_v31_supp는 코드 본문 비공개)을 추가한다. test_v5도 라이선스 미선언·제한 출처가 있으면 같은 처리를 한다.
5. 로컬 정지 확인: `runpodctl get pod <POD_ID>` 출력을 보고서 '실행 기록' 절에 그대로 붙인다.

### 2.5 로컬 채점 명령

```powershell
cd C:\BLADE; $env:PYTHONPATH="C:\BLADE"
.python\python.exe -X utf8 scripts\eval_v30.py --pred (Get-ChildItem reports\eval\<작업>\*\eval*\predictions_*.jsonl).FullName --out reports\eval\<작업>\scores_test_v30.json --md reports\eval\<작업>\eval_v30.md
.python\python.exe -X utf8 scripts\eval_v31_supp.py --pred (Get-ChildItem reports\eval\<작업>\*\eval*\supp_predictions_*.jsonl).FullName --out reports\eval\<작업>\scores_supp.json --md reports\eval\<작업>\eval_supp.md
```

`eval_v30.py`는 파일 이름이 `predictions_(oas_code|oas)_<tag>.jsonl` 형식이어야 한다(정규식 assert). `eval_v31_supp.py`는 tag의 `_s<seed>`로 seed를 묶어 평균 ± 표준편차를 낸다. 그래서 새 예측 파일은 **접두사를 유지하고 tag 뒤에 접미사**를 붙인다(예: `predictions_oas_code_lora_v4_s42_final_stable.jsonl` → 그룹 `lora_v4_stable`).

## 3. 작업 B — 출력 안정화 재추론 (학습 없음)

### 3.1 결과 확인 전에 고정하는 설정

| 항목 | 기존(v4 평가) | 안정화 |
|---|---|---|
| repetition_penalty | 1.0(미지정) | **1.1** |
| 출력 형식 제약 | 없음(정규식으로 `{...}` 추출 후 label 검사) | **JSON 스키마 제약 디코딩**, label은 7종 enum |
| do_sample / temperature / top_p | False / None / None | 동일 |
| max_new_tokens / eval_batch / padding | 256 / 8 / left | 동일 |
| 어댑터·프롬프트·입력 | final, v3.0.1, data_v4 입력 | 동일 |

스키마(SFT 정답 형식과 같다):

```json
{"type": "object",
 "properties": {"label": {"enum": ["public","role_required","membership_required","tenant_match","owner_match","owner_or_admin","manual_review_required"]},
                "confidence": {"type": "number"}, "rationale": {"type": "string"}, "evidence_fields": {"type": "array", "items": {"type": "string"}}},
 "required": ["label"]}
```

제약 디코딩 라이브러리는 `lm-format-enforcer`를 1순위로 쓴다(HF `generate`의 `prefix_allowed_tokens_fn`으로 붙어서 배치 greedy와 함께 쓸 수 있다). transformers 5.x와의 호환은 확인되지 않았으므로 **전체 실행 전에 8건 스모크 테스트**로 동작·속도를 확인하고, 실패하면 `outlines`로 바꾼다. 어느 쪽을 썼는지 config에 기록한다. 알려진 한계: rationale이 256토큰을 넘어 잘리면 JSON이 닫히지 않아 여전히 출력 오류로 집계된다(스키마 제약은 길이를 막지 않는다). 이것도 그대로 출력 오류로 센다.

### 3.2 스크립트 변경 (2026-10-31 적용 완료, HP는 그대로)

| 파일 | 변경 |
|---|---|
| run_train.py | `DECODING`·`SCHEMA` 상수, `--decoding {default,stable}`(stable은 `--eval-only`/base에서만 허용), `--limit N`(스모크). stable 출력은 `<run>/eval_stable/`에 tag 접미사 `_stable`, 로그 `logs/run_stable.log`, 설정 `config_stable.json`·`env_stable.json`. 기존 `eval/`·`config.json`·`run.log`는 건드리지 않는다. 로그 줄에 `mean ms/row` 추가 |
| run_all.sh | `DECODING=stable`이면 기본 RUNS가 작업 B 10개 모델(eval-only)로 바뀌고 로그는 `runs/run_all_stable.log`, export 이름 `blade_stable`, 어댑터 tar 생략 |
| export_results.sh | `EXPORT_NAME`·`EXPORT_ADAPTERS` 환경변수, `eval*`·`config*.json`·`env*.json`·`run_all*.log` 포함, `*_smoke` 제외, SUMMARY에 로그 파일·supp 오류 열 추가, `SHA256SUMS_<이름>` |
| setup.sh | `pip install -q lm-format-enforcer`, 버전 출력 |

로컬 사전 검증(2026-10-31, Qwen2.5-7B-Instruct 토크나이저 + lm-format-enforcer 최신, GPU 없이):

- 제약기 알파벳(토크나이저 단일 문자 토큰 17,805개)이 train_sft_v4 정답 출력의 문자 418종을 모두 포함한다. 한국어 rationale이 막히지 않는다.
- 문자 단위 재생: 978건 중 976건 통과. 나머지 2건(gitea 코드 인용의 공백 13개 이상 연속)은 제약기의 연속 공백 상한(기본 12)에 걸린다. 생성 시에는 긴 공백 반복이 막히는 쪽이라 그대로 둔다.
- 토큰 단위 재생(seed 42, 150건): 132건은 토큰 경로까지 동일. 18건은 병합 토큰 `.",`가 막혔지만 `."`·`",`·`"` 단일 토큰은 허용되므로 **문자 내용은 같고 토큰 분할만 달라진다**. 문자열 자유 텍스트 캐시가 따옴표 뒤에 글자가 더 붙은 토큰을 제외하는 lm-format-enforcer의 동작이다.
- lm-format-enforcer의 transformers 연동 모듈이 transformers 5.x에서 import에 실패하면 run_train.py가 같은 토크나이저 데이터를 직접 만들어 쓴다(`schema_prefix_fn`, 로컬에서 두 경로의 허용 토큰 집합이 300/300 단계 동일함을 확인). 로그에 `[direct]`로 표시된다.
- CPU에서 캐시 없는 상태의 단계당 13 ms. GPU 생성 시 배치 8 × 256토큰 기준 1.5~2배 느려질 수 있다. 3.3 스모크에서 실제 배수를 확인한다.

### 3.3 스모크 테스트 (전체 실행 전, 약 5분)

```bash
cd /workspace/blade_lora_v3
python runpod/run_train.py --data base --seed 0 --eval-only --decoding stable --limit 8 --base /workspace/blade_lora_v3
python runpod/run_train.py --data v4 --seed 42 --eval-only --decoding stable --limit 8 --base /workspace/blade_lora_v3
grep -h "SMOKE" runs/base_qwen_runpod/logs/run_stable.log runs/lora_v4_s42/logs/run_stable.log
head -c 600 runs/lora_v4_s42/eval_stable_smoke/predictions_oas_code_lora_v4_s42_final_stable.jsonl
```

확인할 것: (1) `decoding=stable … tokenizer data built` 줄이 나오고 오류 없이 끝남, (2) 8건 모두 `prediction`이 null이 아님(스키마 JSON으로 파싱), (3) `mean ms/row`를 기존 평가와 비교. 기존 v4 oas_code는 `reports/eval/lora_v4/lora_v4_s42/eval/predictions_oas_code_lora_v4_s42_final.jsonl`의 `inference_ms`(건당 약 1~2초)다. 배수를 3.4 예상 시간에 곱해 시작 전에 보고한다. 스모크 출력(`eval_stable_smoke/`)은 채점·export에서 제외된다.

### 3.4 실행 목록과 예상 시간

```bash
tmux new -d -s blade "DECODING=stable bash /workspace/blade_lora_v3/runpod/run_all.sh"
tmux attach -t blade      # Ctrl-b d 로 빠져나오기
```

`DECODING=stable`의 기본 RUNS = `base:0:eval v2:42:eval v2:43:eval v2:44:eval v3b:42:eval v3b:43:eval v3b:44:eval v4:42:eval v4:43:eval v4:44:eval`. 일부만 돌릴 때는 `RUNS="v4:42:eval v4:43:eval" DECODING=stable bash …`.

10-27 실측: 모델 로드 포함 4개 평가 작업(test_v30 269+265, supp 222+222 = 978건)이 base에서 14.6분, supp 2개만(444건)이 어댑터당 6.5분. 모델당 약 15분 × 10개 = 2.5시간이 기준이고, 제약 디코딩의 토큰별 콜백 때문에 1.5~2배 느려질 수 있다. **예상 3~5시간, 스모크 테스트 뒤에 확정해서 시작 전에 보고한다.** 설치·점검 20분은 별도다. 끝나면 `export/blade_stable_results.tar.gz`와 `SHA256SUMS_blade_stable`이 생기고 Pod가 정지된다.

### 3.4b 새 Pod(Network Volume 없음)에서 돌리기 (2026-10-31)

볼륨이 있는 데이터센터에 GPU가 없을 때. 어댑터 백업이 로컬에 있으므로 볼륨 없이도 된다.

- Pod: GPU는 VRAM 16GB 이상 아무것이나(24GB 이상 권장: 4090·A5000·L4·L40S·A6000·A100). PyTorch 2.x 템플릿. Volume Disk(/workspace) 30GB 이상, Container Disk 30GB 이상.
- 가능하면 GPU가 있는 데이터센터에 **새 Network Volume(20GB)을 만들어 붙인다**. 자동 정지 뒤에도 결과가 볼륨에 남고, 그 데이터센터의 어떤 Pod에서든 받을 수 있다. 네트워크 볼륨 없이 만들어도 Pod 자체의 Volume Disk(/workspace)는 정지 후 유지된다(종료·삭제하면 사라짐). 어느 쪽이든 자동 정지(`STOP_POD=1`, 기본값)를 그대로 쓴다.
- 올릴 파일 2개(Jupyter 업로드 또는 `runpodctl send`), 둘 다 `/workspace/`에:
  - `<USERPROFILE>\Downloads\blade_lora_stable_runpod_20261031.tgz` (1.1MB, 데이터·스크립트)
  - `<USERPROFILE>\Downloads\blade_v4_adapters.tar.gz` (1.7GB, 어댑터 12개 전부: v2·v3a·v3b·v4 각 3 seed. SHA-256 `a3ce55a4…`) — `blade_v3_adapters.tar.gz`는 필요 없다(부분집합).
- 실행:

```bash
cd /workspace && mkdir -p blade_lora_v3 && tar -xzf blade_lora_stable_runpod_20261031.tgz -C blade_lora_v3
bash /workspace/blade_lora_v3/runpod/new_pod.sh /workspace/blade_v4_adapters.tar.gz   # 해시 확인 → 어댑터 복원 → setup → 스모크 8건 → 실행 명령 출력
tmux new -d -s blade "DECODING=stable bash /workspace/blade_lora_v3/runpod/run_all.sh"
tail -f /workspace/blade_lora_v3/runs/run_all_stable.log
```

- 모든 항목이 끝나면 export 후 `runpodctl stop pod`로 **자동 정지**한다(기본값). 결과 `/workspace/blade_lora_v3/export/blade_stable_results.tar.gz`와 `SHA256SUMS_blade_stable`은 /workspace에 남으므로, 정지된 Pod를 다시 시작(또는 같은 네트워크 볼륨을 붙인 다른 Pod)해서 내려받는다. **받기 전에 Pod를 종료(terminate)하지 않는다.** 정지 확인은 로컬에서 `runpodctl get pod <POD_ID>`와 콘솔.
- 끝나는 시점에 지켜볼 수 있으면 `STOP_DELAY_MIN=20`을 붙여 export 뒤 20분 기다렸다가 정지하게 할 수 있다(그 사이 내려받기). 기본은 0분이다.
- 베이스 모델(약 5.5GB)은 처음 한 번 HF에서 받는다(`/workspace/hf`). 24GB GPU면 A100 대비 1.5~2배 더 걸린다.

### 3.5 채점과 보고

- `blade_stable_results.tar.gz`를 `reports/eval/stable_decoding/`에 풀고 2.5의 명령을 적용한다(`eval*` 글롭이 `eval_stable`을 잡는다. 같은 디렉터리에 기존 `eval/` 예측이 없게 한다). 기존 설정 수치는 `reports/eval/lora_v4/scores_*.json`을 다시 읽는다. 재추론하지 않는다.
- `reports/eval/stable_decoding/report.md`: 모델별(base, v2, v3b, v4) × 설정(기존/안정화)로 출력 오류 수, 구체 정밀도·재현율, macro-F1(oas_code 합성 제외 207건·supp 222건), manual 비율을 seed 평균 ± 표준편차로 적는다. 판정은 사전 기준 그대로: 출력 오류가 줄고 구체 정밀도·macro-F1이 표준편차 이상 떨어지지 않으면 "채택 가능". 채택해도 발표 주 수치는 v4 원본이다.
- 실행 기록 절: Pod ID, 시작·종료 UTC, env.json 버전, 스모크 결과, `runpodctl get pod` 출력(정지 확인). 커밋하지 않는다.

## 4. 작업 C-4 — LoRA v5 학습·평가

### 4.1 전제 (C-3 정지 지점 4를 통과한 뒤)

`training/lora/data_v5/`에 다음이 있어야 한다: `train_sft_v5.jsonl`, `val_sft_v5.jsonl`, `test_v30_inputs.jsonl`(data_v4와 바이트 동일), `test_v31_supp_inputs.jsonl`(동일), `test_v5_inputs.jsonl`(C-2에서 동결, 같은 레코드 형식: id·source·service·label·security_state·oas_user·oas_code_user), `policy_label_v3.0.1.md`, `data_v5_hashes.json`. 해시 목록 파일의 SHA-256을 AGENTS.md data-v5 동결 절과 `DATASETS['v5']['sha']`에 적는다. 4096 토큰 초과 제외 건수는 C-3 보고에 이미 있어야 한다.

### 4.2 run_train.py 변경안

```python
DATASETS['v5'] = dict(dir='data_v5', train='train_sft_v5.jsonl', val='val_sft_v5.jsonl', hashes='data_v5_hashes.json', sha='<data_v5_hashes.json SHA-256>', run='lora_v5_s{seed}', tag='lora_v5_s{seed}_final')
# test_v5: SUPP와 같은 방식의 상수 + evaluate()에 작업 추가. 파일 이름 v5test_predictions_{cond}_{tag}.jsonl (test_v30·supp 채점기와 충돌하지 않는 접두사)
TESTV5 = dict(dir='data_v5', file='test_v5_inputs.jsonl', hashes='data_v5_hashes.json', sha='<같은 값>')
```

- `base`·`v4`의 `--eval-only`는 test_v30·supp 예측이 이미 있으므로 건너뛰고 test_v5 예측만 추가한다(기존 "파일이 있으면 skip" 로직 그대로). v4 어댑터 3개가 볼륨 `runs/lora_v4_s4*/adapter/`에 있어야 한다.
- HP·프롬프트는 바꾸지 않는다. 디코딩은 **기존 설정(default)** 으로 돈다. 작업 B가 "채택 가능"으로 끝났더라도 v5 비교의 기준은 v4 원본 설정이다. 안정화 설정 수치가 필요하면 평가만 `--decoding stable`로 한 번 더 돌린다(모델당 약 15~25분 추가).
- export_results.sh의 tar 이름을 `blade_v5_*`로 바꾼다.
- 채점기: `scripts/eval_v5.py`를 `eval_v31_supp.py`를 본으로 만든다(TEST 경로·해시를 test_v5로, PROJECTS를 test_v5 출처 프로젝트로). label별 표와 프로젝트별 표를 함께 낸다.

### 4.3 실행 목록과 예상 시간

```bash
RUNS="v5:42 v5:43 v5:44 v4:42:eval v4:43:eval v4:44:eval base:0:eval" \
  tmux new -d -s blade "bash /workspace/blade_lora_v3/runpod/run_all.sh"
```

10-27 실측: v4 학습(978건, 369 step) 44분 + 평가 4작업 15분 = 항목당 59분. v5는 train이 더 크고 평가가 6작업(test_v5 2조건 추가)이므로 항목당 약 75~85분 × 3 = 약 4시간. v4 eval-only(test_v5 2조건)는 모델당 약 5분 × 3, base 약 5~8분. **합계 약 4.5~5시간 + 설치·점검 20분.** 첫 v5 항목이 끝난 시각으로 다시 계산해 보고한다. 토요일 12:00 KST 시작이면 토요일 17~18시 KST에 끝난다.

### 4.4 채점과 보고

- 2.5의 명령을 `reports/eval/lora_v5/`에 적용하고 `scripts/eval_v5.py`로 test_v5를 채점한다. v4 수치는 재채점 없이 `reports/eval/lora_v4/scores_*.json`을 쓴다(test_v5만 새 예측).
- `reports/eval/lora_v5/lora_v5_report.md`: v4 vs v5(각 3 seed) × test_v30 oas_code 합성 제외 / test_v31_supp / test_v5. 지표는 주지표, 구체 정밀도·재현율, manual 비율, label별 F1 + support, 출력 오류 수, 작업 A 보조 지표(구체 label macro-F1·커버리지, support ≥ 10 macro-F1). 판정은 사전 기준: test_v5의 owner_or_admin·membership_required F1이 v4보다 표준편차 이상 오르고 test_v30 구체 정밀도가 표준편차 이상 떨어지지 않으면 "개선 인정", 아니면 "불인정". 발표 주 수치는 v4 원본이다.
- 실행 기록 절은 3.5와 같다. 커밋하지 않는다.

### 4.5 적용된 변경과 실제 실행 명령 (2026-10-31, data-v5 동결 후)

사용자 결정(2026-10-31)으로 **data-v5를 test_v5보다 먼저 동결**했다(data-v5는 test_v5 label을 읽지 않음, 후보 키 겹침 0건 재확인). 대신 test_v5는 v5 예측을 만들기 전에 동결해야 하고, run_train.py는 test_v5 동결 해시가 없으면 test_v5 평가를 만들지 않는다.

| 파일 | 변경 |
|---|---|
| run_train.py | `DATASETS['v5']`(sha `39c302c5…` = data_v5_hashes.json), `TESTV5`(manifest 해시 게이트: `sha=None`이거나 manifest·입력이 없거나 다르면 test_v5 작업 생략), `testv5_rows()`, 출력 `v5test_predictions_<cond>_<tag>.jsonl`, `--jobs v5test`(v4·base 어댑터에 test_v5 예측만 추가) |
| run_all.sh | RUNS에 `v5:`가 있으면 export 이름 `blade_v5`; 모든 run 뒤 `merge_gguf_v5.sh $GGUF_SEED`(기본: RUNS에 `v5:42` 학습 항목이 있으면 42) → export → Pod 정지 |
| merge_gguf_v5.sh | seed 어댑터를 unquantized Qwen2.5-7B-Instruct(리비전 `a09a3545…`)에 fp32로 병합 → fp16 HF → llama.cpp(b11693) f16 GGUF → Q4_K_M. 결과 `export/gguf/blade-qwen-lora-v5-s<seed>-Q4_K_M.gguf` + `merge_manifest_v5.json` + `SHA256SUMS_gguf`. 병합 체크포인트·f16 GGUF는 삭제(디스크 약 35GB 일시 사용, RAM 32GB 이상) |
| export_results.sh | SUMMARY에 v5test 오류 열, gguf/ manifest 포함 |
| scripts/eval_test_v5.py | test_v5 채점기(eval_v31_supp.py 본, label별·프로젝트별 표, manifest 해시 assert) |

**test_v5 동결 전**(지금 상태)에는 학습과 test_v30·supp 평가만 돈다. test_v5가 동결되면 ① `data_v5/test_v5_inputs.jsonl`·`test_v5_manifest.json`을 Pod의 `data_v5/`에 올리고 ② `run_train.py`의 `TESTV5['sha']`에 manifest SHA-256을 적은 뒤 ③ 아래 eval-only 항목으로 test_v5 예측을 추가한다(끝난 run은 파일 존재로 건너뛰므로 같은 RUNS를 다시 돌려도 된다).

```bash
# 번들: training/lora 아래 data_v2 data_v3 data_v4 data_v5 runpod (bsdtar, 로컬 PowerShell)
cd /workspace/blade_lora_v3 && tar -xzf /workspace/blade_lora_runpod_v5_<날짜>.tgz && bash runpod/setup.sh
sha256sum data_v5/data_v5_hashes.json      # 39c302c5fb33d1b1506487678cd15f40cc83ffd59435449522786388554753ac
ls runs/lora_v4_s4*/adapter/adapter_model.safetensors   # v4 3 seed (blade_v4_adapters.tar.gz 복원) — test_v5 eval-only에 필요
# 1) 학습 + test_v30/supp 평가 + GGUF(s42) + export + 정지  (test_v5 미동결 상태에서 시작 가능)
tmux new -d -s blade "RUNS='v5:42 v5:43 v5:44' bash /workspace/blade_lora_v3/runpod/run_all.sh"
# 2) test_v5 동결 후(TESTV5 sha 기입, 파일 업로드): v5 3 seed + v4 3 seed + base(1회)에 test_v5 예측만 추가 (항목 모드 v5test = --eval-only --jobs v5test)
#    C-4 평가 범위(사용자 결정 2026-10-31): v2·v3b 재추론 없음(기존 기록), test_v30·supp는 v5만 새로 추론하고 base·v4는 reports/eval/lora_v4 예측 사용, 모두 기본 디코딩
# (test_v5 동결 2026-10-31: TESTV5 sha 57fd384f…; 올릴 파일 data_v5/test_v5_inputs.jsonl, data_v5/test_v5_manifest.json, runpod/run_train.py, runpod/export_results.sh)
# GGUF는 만들지 않는다(사용자 결정 2026-10-31): Network Volume 할당량 때문에 merge_gguf_v5.sh의 임시 파일(병합 15GB + f16 15GB)이 Disk quota exceeded로 실패한다. GGUF_SEED= 로 끈다. C-5 전환 시에만 컨테이너 디스크(100GB 이상)로 WORK를 돌려 별도 실행한다.
# !! Pod를 멈췄다 켜거나 새 Pod면 pip 패키지(unsloth·transformers·peft)는 사라진다(/workspace 볼륨 밖). 어떤 단계든 첫 명령은 반드시 setup.sh이고, env ok가 찍힌 뒤에만 tmux를 연다. (07:12 UTC 2단계 실패 원인: setup.sh 생략 → ModuleNotFoundError transformers)
cd /workspace/blade_lora_v3 && bash runpod/setup.sh && python -c "import unsloth, transformers, peft; print('env ok')"
[ -f runpod/merge_gguf_v5.sh.off ] && mv runpod/merge_gguf_v5.sh.off runpod/merge_gguf_v5.sh
tmux new -d -s blade "RUNS='v5:42:v5test v5:43:v5test v5:44:v5test v4:42:v5test v4:43:v5test v4:44:v5test base:0:v5test' GGUF_SEED= bash /workspace/blade_lora_v3/runpod/run_all.sh"
tail -f /workspace/blade_lora_v3/runs/run_all.log
```

예상 시간(A100 80GB, 10-27 실측 기준): v5 학습 1,274건 ≈ 480 step ≈ 57분 + 평가 4작업 15분 ≈ 항목당 72분 × 3 ≈ 3.6시간, GGUF 병합·변환·양자화 ≈ 25~40분, 설치 20분 → **약 4.5시간**. test_v5(296건 이하 × 2조건) 추가 평가는 모델당 약 5분 × 7 ≈ 35분.

### 4.6 C-5 전환 (사용자 승인 2026-10-31) — Pod: GGUF + 동등성·문턱 추론, 로컬: 채점·등록·검증

새 Pod(새 스토리지)에서 a~c만 GPU로 돌린다. 임시 파일 30GB는 컨테이너 디스크(`/root/c5`)에 두고 볼륨에는 결과(Q4_K_M 4.7GB + 예측)만 쓴다. Pod 사양: A100 등 GPU 1개, **RAM 64GB 이상(fp32 병합), 컨테이너 디스크 80GB 이상**, 볼륨 20GB 이상.

번들 `blade_c5_v5_20261031.tgz`(145MB, SHA-256 `c225fc35d0ad616b6064c36595e6d3405f473f37953f2dcd0626c4fec2cdace4`): runs/lora_v5_s42/adapter(SHA `75ea08c1…`), data_v5(test_v30_inputs·val_sft_v5·hashes·prompt), runpod/{setup_c5.sh, merge_gguf_v5.sh, run_c5.sh}, eval_ollama_v5.py, Modelfile.blade-qwen-lora-v5.

```bash
# Pod (Jupyter로 번들을 /workspace 에 올린 뒤)
mkdir -p /workspace/blade_c5 && cd /workspace/blade_c5 && tar -xzf /workspace/blade_c5_v5_20261031.tgz && bash runpod/setup_c5.sh
tmux new -d -s c5 "bash /workspace/blade_c5/runpod/run_c5.sh"
tail -f /workspace/blade_c5/export/c5.log
# 끝나면 60초 뒤 자동 정지. 받을 파일: export/gguf/blade-qwen-lora-v5-s42-Q4_K_M.gguf, merge_manifest_v5_s42.json, SHA256SUMS_gguf_s42, merge.log,
#   export/gguf_eval/*.jsonl, template_check.log, export/SHA256SUMS_c5, export/c5.log
```

- run_c5.sh는 어댑터·data_v5_hashes.json 해시를 검증하고, 병합(fp32, 베이스 리비전 a09a3545…) → f16 → Q4_K_M → `ollama create blade-qwen-lora-v5` → `--check-template 3`(HF 템플릿 토큰 수 = Ollama prompt_eval_count assert) → test_v30 oas_code 265건 → val_sft_v5 179건 순서다. 다시 돌리면 GGUF가 있고 해시가 맞을 때 병합을 건너뛴다.
- 예상 시간: 설치 5분, 베이스 다운로드 2~5분, 병합 5분, f16 변환 3분, Q4_K_M 5분, 추론 GPU 기준 10분 → 약 40분.

```powershell
# 로컬 (C:\BLADE), 받은 파일을 reports/eval/lora_v5_gguf/ 에 둔 뒤
.python\python.exe -X utf8 scripts\eval_v30.py --pred reports\eval\lora_v5_gguf\predictions_oas_code_lora_v5_s42_gguf_q4km.jsonl reports\eval\lora_v5\lora_v5_s42\eval\predictions_oas_code_lora_v5_s42_final.jsonl --out reports\eval\lora_v5_gguf\scores_test_v30.json
.python\python.exe -X utf8 training\lora\choose_threshold_v4.py --rule precision --pred reports\eval\lora_v5_gguf\val_predictions_lora_v5_s42_gguf_q4km.jsonl --out reports\eval\lora_v5_gguf\threshold_val_v5.json
copy training\lora\Modelfile.blade-qwen-lora-v5 <gguf dir>\ ; ollama create blade-qwen-lora-v5 -f <gguf dir>\Modelfile.blade-qwen-lora-v5     # v4 모델은 남긴다
$env:BLADE_CLASSIFIER='lora'; $env:BLADE_LORA_MODEL='blade-qwen-lora-v5'; $env:BLADE_LORA_MIN_CONFIDENCE='<threshold_val_v5.json chosen>'
.python\python.exe -X utf8 scripts\verify_lora_pipeline.py ; .python\python.exe -m pytest tests
```

- 동등성 판정(v4와 같은 규칙, equivalence_check.md): 같은 adapter(s42) HF final 예측과 비교, 허용 폭은 3-seed 표준편차(주지표 macro-F1 합성 제외 207, 합성 제외 구체 정밀도, 265 구체 정밀도). 보류 비율 이동이 주원인이면 v4 때처럼 조건부 수용을 사용자에게 제안한다.
- 문턱: val_v5만 사용, `--rule precision`(v4와 같은 규칙), 기존 바닥 0.7. test로 고르지 않는다.
- 런타임 코드는 바꾸지 않는다: 모델명·문턱은 `BLADE_LORA_MODEL`·`BLADE_LORA_MIN_CONFIDENCE` 환경변수로만 전환하고, v4(기본값 blade-qwen-lora-v4, 0.9)는 롤백용으로 Ollama에 남긴다.

## 5. 문제 해결

| 증상 | 조치 |
|---|---|
| `import transformers` 실패(libtorchaudio undefined symbol) | setup.sh가 처리한다. 수동이면 `pip uninstall -y torchaudio` |
| unsloth 버전이 10-27과 달라 결과가 달라질 우려 | `pip install unsloth==2026.10.9 transformers==5.17.0 trl==1.15.0 peft==0.21.2`로 고정 시도. 안 되면 env.json 차이를 보고서에 적는다 |
| `input hash mismatch, stop` | 번들에 든 입력이 동결본과 다르다. 해시 목록을 고치지 말고 로컬 동결 파일로 번들을 다시 만든다 |
| `--eval-only but no final adapter` | 볼륨에 어댑터가 없다. 1절의 tar를 `runs/`에 복원한다 |
| `training loss abnormal (nan/divergent)` → FAILED | 그 run은 실패로 기록되고 다음 항목으로 넘어간다. 보고서에 FAILED를 적고 재학습 여부는 사용자 결정 |
| 연결 끊김 | tmux 세션은 계속 돈다. 재접속 후 `tmux attach -t blade`. Pod가 재시작됐으면 같은 RUNS로 다시 실행하면 이어서 진행 |
| run_all.log 마지막 줄이 "POD NOT STOPPED" 또는 "skipped by shim" | 콘솔에서 수동 정지. 로컬 `runpodctl get pod`로 확인하고 출력을 보고서에 남긴다 |
| 디스크 부족 | `runs/*/checkpoints/`(재개용, run당 2개 보존)와 `/workspace/hf`(모델 캐시) 확인. 끝난 run의 checkpoints는 지워도 된다(어댑터·예측은 유지) |
| `--eval-only but no final adapter in .../adapter` (새 Pod, 어댑터 tar만 복원) | 어댑터 tar에는 `adapter/`만 있고 `logs/train_result.json`이 없어 생긴 오류. run_train.py가 `--eval-only`면 `adapter_model.safetensors`만 확인하도록 수정됨(2026-10-31). 구 번들이면 run_train.py만 교체 |
| 제약 디코딩이 transformers 5.x에서 오류 | 3.3 스모크에서 잡는다. `outlines`로 교체하고 config에 기록. 둘 다 실패하면 작업 B를 보류하고 보고 |
