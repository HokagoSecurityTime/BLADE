# 발표 수치 출처 확인 (2026-10-31)

대상: 베이스(unsloth/Qwen2.5-7B-Instruct-bnb-4bit, 어댑터 없음)·LoRA v4(3 seed) / test_v30 oas_code / eval-def v2 / 합성 제외 207건. 모두 기본 디코딩(2026-10-27 RunPod run). 원자료는 `reports/eval/lora_v4/scores_test_v30.json`(scripts/eval_v30.py 출력)이며, 항목 선택 조건은 `condition == "oas_code"`, `eval_def == "v2"`, 모델은 `model` 필드 `base_qwen_runpod` / `lora_v4_s42_final` / `lora_v4_s43_final` / `lora_v4_s44_final`. 각 항목의 `file` 필드가 예측 파일(`reports/eval/lora_v4/<run>/eval/predictions_oas_code_<model>.jsonl`)을 가리킨다.

| 발표 값 | 베이스 | v4 (3 seed 평균 ± 표본표준편차) | v4 seed 42 / 43 / 44 | JSON 항목 |
|---|---:|---:|---|---|
| 구체 정밀도 | 0.353 | 0.811 ± 0.025 | 0.8380 / 0.7874 / 0.8077 | `main_excl_synthetic.concrete.precision` |
| 구체 재현율 | 0.316 | 0.558 ± 0.065 | 0.5777 / 0.4854 / 0.6117 | `main_excl_synthetic.concrete.recall` |
| macro-F1 | 0.197 | 0.356 ± 0.045 | 0.3796 / 0.3042 / 0.3856 | `main_excl_synthetic.macro_f1` |
| manual 비율 | 0.068 | 0.298 ± 0.056 | 0.2899 / 0.3575 / 0.2464 | `main_excl_synthetic.manual_ratio` |
| public 오판(신 정의) | 17/35 | 0~1/35 | 1 / 0 / 0 | `public_misjudge_new.count` (분모는 아래 참조) |

- `main_excl_synthetic.records` = 207 (oas_code 채점 265건 − 합성 58건). 베이스 값은 소수 넷째 자리에서 반올림(0.3533, 0.3155, 0.1967, 0.0676).
- 평균 ± 표준편차는 statistics.stdev(표본, n−1)이다. lora_v4_report.md 1절 표와 같은 계산이다.
- **public 오판 분모 35**: scores_test_v30.json의 `public_misjudge_new.denominator`는 47(oas_code 채점 265건 전체에서 security 선언 ∧ 정답≠public)이다. 그중 합성 레코드가 12건이므로 합성 제외 분모는 35다. 분자는 베이스 17건·v4 1/0/0건이 전부 비합성 레코드이므로(`public_misjudge_new.ids`를 `reports/eval_v30_redef/segments.json`의 `ids.synthetic`과 대조, 겹침 0) 그대로다. 즉 17/35와 0~1/35는 파일에 그대로 적혀 있지 않고 47 → 35 분모 환산을 거친 값이다. 합성 포함으로 쓰면 17/47, 1/0/0 /47이며 lora_v4_report.md 1절 표는 /47 기준이다.
- 비교용 합성 포함(265건) 구체 정밀도: v4 0.855 ± 0.018 (`main.concrete.precision`). AGENTS.md 작업 C 기준은 2026-10-31 사용자 결정으로 합성 제외 207건 0.811 ± 0.025로 정정했다.

확인 명령:

```bash
python - <<'PY'
import json, statistics as st
r=[e for e in json.load(open('reports/eval/lora_v4/scores_test_v30.json',encoding='utf-8')) if e['eval_def']=='v2' and e['condition']=='oas_code']
for e in r:
    if 'base' in e['model'] or 'lora_v4' in e['model']:
        m=e['main_excl_synthetic']; print(e['model'], m['records'], m['concrete']['precision'], m['concrete']['recall'], m['macro_f1'], m['manual_ratio'], e['public_misjudge_new']['count'], '/', e['public_misjudge_new']['denominator'], e['file'])
PY
```
