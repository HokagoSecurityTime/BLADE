"""발표용 수치 표 (C-5 수용·마무리 2항, 사용자 결정 2026-10-31: 발표 주 수치를 LoRA v5로 전환).
모든 수치는 기존 채점 JSON에서 읽는다(재추론 없음). 출력: reports/eval/lora_v5/presentation_numbers_v5.md + .json.
- test_v30 oas_code 합성 제외 207: scores_test_v30.json (eval-def v2, main_excl_synthetic). public 오판(신 정의) 분모 35 = 207건 중 declared ∧ 정답≠public.
- test_v5 oas_code 283: scores_test_v5.json (per_label, per_project). macro-F1은 support>0 label 6종 평균(tenant_match 정답 0건은 제외).
- test_v31_supp oas_code 222: scores_supp.json + 예측 파일에서 public 오판(신 정의, 분모 191 = declared 192 중 정답 public 1 제외) 재계산.
- 합산 712(보조): scores_combined_712.json (scripts/eval_combined_v5.py).
"""
from __future__ import annotations
import hashlib, json, statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S30 = 'reports/eval/lora_v5/scores_test_v30.json'; S5 = 'reports/eval/lora_v5/scores_test_v5.json'; SS = 'reports/eval/lora_v5/scores_supp.json'; SC = 'reports/eval/lora_v5/scores_combined_712.json'
SEG = 'reports/eval_v30_redef/segments.json'; SUPP = 'datasets/blade/processed/data_v4/test_v31_supp.jsonl'; SUPP_SHA = '803d914902c7ca2042fd15d4a7852d42e71828e58d4ae4d3ac791fb868e63395'
PROJECTS5 = ['rocketchat', 'ghost', 'umami']
SEEDS = (42, 43, 44)
load = lambda p: json.load(open(ROOT / p, encoding='utf-8'))
rd = lambda p: [json.loads(l) for l in open(ROOT / p, encoding='utf-8') if l.strip()]
MODELS = {'base': ['base_qwen_runpod'], 'v4': [f'lora_v4_s{s}_final' for s in SEEDS], 'v5': [f'lora_v5_s{s}_final' for s in SEEDS]}
RUN_DIR = {'base_qwen_runpod': 'reports/eval/lora_v4/base_qwen_runpod', **{f'lora_v4_s{s}_final': f'reports/eval/lora_v4/lora_v4_s{s}' for s in SEEDS}, **{f'lora_v5_s{s}_final': f'reports/eval/lora_v5/lora_v5_s{s}' for s in SEEDS}}


def pick(rows, model, **kw):
    out = [e for e in rows if e['model'] == model and all(e.get(k) == v for k, v in kw.items())]; assert len(out) == 1, (model, kw, len(out)); return out[0]


def agg(vals):
    return (st.mean(vals), st.stdev(vals) if len(vals) > 1 else None)


def fmt(v, sd=None, pct=False, intlike=False):
    if v is None: return '-'
    if intlike: return f'{v:.0f}' if sd is None else f'{v:.1f} ± {sd:.1f}'
    if pct: return f'{v*100:.1f}%' if sd is None else f'{v*100:.1f} ± {sd*100:.1f}%'
    return f'{v:.3f}' if sd is None else f'{v:.3f} ± {sd:.3f}'


def main():
    assert hashlib.sha256((ROOT / SUPP).read_bytes()).hexdigest() == SUPP_SHA
    synthetic = set(load(SEG)['ids']['synthetic']); s30 = load(S30); s5 = load(S5); ss = load(SS); sc = load(SC)['results']
    supp_truth = {r['id']: r for r in rd(SUPP)}; supp_declared = [i for i, r in supp_truth.items() if r['security_state'] == 'declared']
    supp_denom = [i for i in supp_declared if supp_truth[i]['label'] != 'public']; assert len(supp_declared) == 192 and len(supp_denom) == 191

    def m30(model):
        e = pick(s30, model, condition='oas_code', eval_def='v2'); x = e['main_excl_synthetic']; pub = [i for i in e['public_misjudge_new']['ids'] if i not in synthetic]
        assert e['public_misjudge_new']['denominator'] == 47
        return dict(precision=x['concrete']['precision'], recall=x['concrete']['recall'], macro_f1=x['macro_f1'], manual=x['manual_ratio'], manual_265=e['main']['manual_ratio'], public_misjudge_35=len(pub), public_ids=pub)

    def m5(model):
        e = pick(s5, model, condition='oas_code'); assert e['per_label']['tenant_match']['support'] == 0 and e['records'] == 283
        return dict(macro_f1=e['macro_f1'], accuracy=e['accuracy'], manual=e['manual_ratio'], owner_or_admin_f1=e['per_label']['owner_or_admin']['f1'], membership_f1=e['per_label']['membership_required']['f1'],
                    **{f'acc_{p}': e['per_project'][p]['accuracy'] for p in PROJECTS5}, n_projects={p: e['per_project'][p]['n'] for p in PROJECTS5})

    def msupp(model):
        e = pick(ss, model, condition='oas_code'); assert e['records'] == 222
        rows = rd(f"{RUN_DIR[model]}/eval/supp_predictions_oas_code_{model}.jsonl"); pr = {r['id']: (r['prediction']['label'] if r.get('prediction') else 'output_error') for r in rows}
        assert set(pr) == set(supp_truth)
        pub = [i for i in supp_denom if pr[i] == 'public']
        return dict(macro_f1=e['macro_f1'], accuracy=e['accuracy'], manual=e['manual_ratio'], public_misjudge_191=len(pub), public_ids=pub)

    def mcomb(model):
        e = [r for r in sc if r['model'] == model]; assert len(e) == 1; c = e[0]['combined']
        return dict(macro_f1=c['macro_f1'], accuracy=c['accuracy'], precision=c['concrete']['precision'], recall=c['concrete']['recall'], manual=c['manual_ratio'])

    def table(fn):
        out = {}
        for g, models in MODELS.items():
            ms = [fn(m) for m in models]; keys = [k for k in ms[0] if isinstance(ms[0][k], (int, float))]
            out[g] = {k: agg([m[k] for m in ms]) for k in keys}; out[g]['_per_model'] = {m: {k: v for k, v in d.items() if k != 'n_projects'} for m, d in zip(models, ms)}
        return out
    T30, T5, TS, TC = table(m30), table(m5), table(msupp), table(mcomb)
    n5 = m5('base_qwen_runpod')['n_projects']

    L = ['# 발표용 수치 표 — LoRA v5 (C-5 수용·마무리, 2026-10-31)\n',
         '**발표 주 수치는 LoRA v5(data-v5, 3 seed)다**(사용자 결정 2026-10-31 "C-5 수용 및 마무리" 2항; 이전 "v4 원본 유지" 문구를 대체). v4는 비교 기준으로 함께 적는다. 모든 값은 기본 디코딩, 3 seed(42·43·44) 평균 ± 표본 표준편차(base는 1회), HF 어댑터 평가(배포용 GGUF 수치는 4절 별도). 근거 파일은 각 표 아래. 수치는 presentation_numbers_v5.json에서 그대로 읽을 수 있다(생성 scripts/presentation_numbers_v5.py).\n',
         '## 1. test_v30 oas_code, 합성 제외 207건 (eval-def v2 주지표)\n',
         '| 모델 | 구체 정밀도 | 구체 재현율 | macro-F1 | manual 비율(207) | public 오판(신 정의, /35) |', '|---|---:|---:|---:|---:|---:|']
    for name, g in (('base (qwen2.5-7b-instruct, 미학습)', 'base'), ('LoRA v4 (data-v4, 비교 기준)', 'v4'), ('**LoRA v5 (data-v5, 주 수치)**', 'v5')):
        a = T30[g]; L.append(f"| {name} | {fmt(*a['precision'])} | {fmt(*a['recall'])} | {fmt(*a['macro_f1'])} | {fmt(*a['manual'], pct=True)} | {fmt(*a['public_misjudge_35'], intlike=True)} |")
    L.append(f"\n- 근거: {S30} (condition oas_code, eval_def v2, main_excl_synthetic: concrete.precision/recall, macro_f1, manual_ratio; public 오판은 public_misjudge_new.ids에서 합성 id({SEG} 'synthetic' 58건)를 뺀 건수, 분모 35 = 207건 중 declared ∧ 정답≠public). 표 원본 reports/eval/lora_v5/eval_v30.md. 예측 파일 base·v4 reports/eval/lora_v4/<run>/eval/predictions_oas_code_*.jsonl, v5 reports/eval/lora_v5/lora_v5_s4*/eval/predictions_oas_code_*.jsonl. 채점기 scripts/eval_v30.py. 정답 datasets/blade/processed/test_v30.jsonl(SHA 9bd47216…).")
    L.append('- public 오판 건(id): ' + '; '.join(f"{m}: {', '.join(d['public_ids']) if d['public_ids'] else '없음'}" for g in MODELS for m, d in T30[g]['_per_model'].items()))
    v4m = T30['v4']['_per_model']; v5m = T30['v5']['_per_model']
    seeds = lambda dd, k: ' / '.join(f"{d[k]*100:.1f}%" for d in dd.values())
    v4_207, v4_265 = fmt(*T30['v4']['manual'], pct=True), fmt(*agg([d['manual_265'] for d in v4m.values()]), pct=True)
    v5_207, v5_265 = fmt(*T30['v5']['manual'], pct=True), fmt(*agg([d['manual_265'] for d in v5m.values()]), pct=True)
    L.append(f"- **manual 비율 분모 확인(2항 d)**: v4 test_v30 manual 비율은 분모에 따라 두 값이 있다. 합성 제외 207건 기준 {v4_207}(seed별 {seeds(v4m, 'manual')}; supplementary_metrics.md의 'manual 예측률' 0.298과 이 표), 합성 포함 265건 기준 {v4_265}(seed별 {seeds(v4m, 'manual_265')}; lora_v4_report.md·lora_v5_report.md 1절 표의 'manual 비율(265)'). 둘 다 같은 예측 파일(scores_test_v30.json main vs main_excl_synthetic)이며 차이는 합성 58건(세 seed 모두 manual 24.1%)이 들어가느냐뿐이다. v5도 같다: 207 기준 {v5_207}, 265 기준 {v5_265}. 발표 표는 주지표 조건(207)으로 통일한다.\n")

    L += ['## 2. test_v5 oas_code 283건 (hold-out, 별도 조건)\n',
          '| 모델 | macro-F1(6종) | 정확도 | manual 비율 | owner_or_admin F1 (21) | membership_required F1 (33) |', '|---|---:|---:|---:|---:|---:|']
    for name, g in (('base', 'base'), ('LoRA v4 (비교 기준)', 'v4'), ('**LoRA v5 (주 수치)**', 'v5')):
        a = T5[g]; L.append(f"| {name} | {fmt(*a['macro_f1'])} | {fmt(*a['accuracy'])} | {fmt(*a['manual'], pct=True)} | {fmt(*a['owner_or_admin_f1'])} | {fmt(*a['membership_f1'])} |")
    L += ['\n프로젝트별 정확도:\n', '| 모델 | ' + ' | '.join(f'{p} ({n5[p]})' for p in PROJECTS5) + ' |', '|---|' + '---:|' * len(PROJECTS5)]
    for name, g in (('base', 'base'), ('LoRA v4', 'v4'), ('**LoRA v5**', 'v5')):
        a = T5[g]; L.append(f"| {name} | " + ' | '.join(fmt(*a[f'acc_{p}']) for p in PROJECTS5) + ' |')
    L.append(f"\n- **macro-F1의 tenant_match 처리**: scripts/eval_test_v5.py는 그 셋에 정답 support > 0인 label만 평균한다. test_v5에는 tenant_match 정답이 0건이므로 macro-F1은 6종(public·role_required·membership_required·owner_match·owner_or_admin·manual_review_required) 평균이며, tenant_match 예측(FP)은 정확도와 다른 label의 재현율에만 반영된다. 7종으로 나누면(tenant_match F1 = 0) 값은 6/7배가 된다.")
    L.append(f"- 근거: {S5} (condition oas_code: macro_f1, accuracy, manual_ratio, per_label.owner_or_admin.f1, per_label.membership_required.f1, per_project.<p>.accuracy), 표 원본 reports/eval/lora_v5/eval_test_v5.md, 예측 reports/eval/lora_v5/<run>/eval/v5test_predictions_oas_code_*.jsonl, 정답 datasets/blade/processed/test_v5.jsonl(SHA 7b8e4a94…, manifest datasets/blade/processed/data_v5/test_v5_manifest.json 57fd384f…), 채점기 scripts/eval_test_v5.py. 판정 reports/eval/lora_v5/lora_v5_report.md 3b절. 한계: membership_required 33건 중 28건 Rocket.Chat, owner_or_admin support 21.\n")

    L += ['## 3. test_v31_supp oas_code 222건 (별도 조건)\n',
          '| 모델 | macro-F1(7종) | 정확도 | manual 비율 | public 오판(신 정의, /191) |', '|---|---:|---:|---:|---:|']
    for name, g in (('base', 'base'), ('LoRA v4 (비교 기준)', 'v4'), ('**LoRA v5 (주 수치)**', 'v5')):
        a = TS[g]; L.append(f"| {name} | {fmt(*a['macro_f1'])} | {fmt(*a['accuracy'])} | {fmt(*a['manual'], pct=True)} | {fmt(*a['public_misjudge_191'], intlike=True)} |")
    L.append('\n- public 오판 건(id, seed별): ' + '; '.join(f"{m}: {', '.join(d['public_ids']) if d['public_ids'] else '없음'}" for g in MODELS for m, d in TS[g]['_per_model'].items()))
    L.append(f"- 근거: {SS} (condition oas_code: macro_f1, accuracy, manual_ratio; macro-F1은 scripts/eval_v31_supp.py 규칙상 support>0 label 평균이며 supp는 7 label 모두 정답이 있어(public 2 포함) 7종 평균; supplementary_metrics.md의 'support ≥ 10' 6종 macro-F1과는 다른 값), 표 원본 reports/eval/lora_v5/eval_supp.md, 채점기 scripts/eval_v31_supp.py. public 오판은 이 스크립트가 예측 파일과 정답 파일(security_state)로 재계산: declared 192 중 정답 public 1건을 뺀 191건에서 예측 public인 건(정의 reports/eval/lora_v4/supplementary_metrics.md 5번과 동일; v4 1/0/0은 그 문서 값과 일치). 정답 datasets/blade/processed/data_v4/test_v31_supp.jsonl(SHA 803d9149…, 코드 본문 비공개 .gitignore). 예측 base·v4 reports/eval/lora_v4/<run>/eval/supp_predictions_oas_code_*.jsonl, v5 reports/eval/lora_v5/lora_v5_s4*/eval/supp_predictions_oas_code_*.jsonl(모두 .gitignore). 한계: label이 프로젝트에 몰려 있다(membership 50/55 Chatwoot, tenant 52/55 Flowise, owner_or_admin 19/20 Chamilo).\n")

    L += ['## 4. 보조 지표 — 세 셋 합산 712건 (207 + 222 + 283)\n',
          '| 모델 | macro-F1(7종) | 정확도 | 구체 정밀도 | 구체 재현율 | manual 비율 |', '|---|---:|---:|---:|---:|---:|']
    for name, g in (('base', 'base'), ('LoRA v4 (비교 기준)', 'v4'), ('**LoRA v5 (주 수치)**', 'v5')):
        a = TC[g]; L.append(f"| {name} | {fmt(*a['macro_f1'])} | {fmt(*a['accuracy'])} | {fmt(*a['precision'])} | {fmt(*a['recall'])} | {fmt(*a['manual'], pct=True)} |")
    L.append(f"\n- 근거: {SC} (scripts/eval_combined_v5.py, 표 원본 reports/eval/lora_v5/eval_combined_712.md). 7 label 모두 support가 있어 7종 평균. 구체 정밀도·재현율은 eval_v30.py concrete()와 같은 정의(정답 구체 건 중 응답한 건의 정확도 / 정답 구체 건 전체 대비 일치). 보조 지표이며 주지표(1절)는 바뀌지 않는다.\n")

    L += ['## 5. 배포 모델 (GGUF Q4_K_M, s42) — 변환 동등성 확인용 별도 표기\n',
          '- reports/eval/lora_v5_gguf/equivalence_check.md: test_v30 oas_code에서 GGUF와 HF s42 final 비교(v4 허용 폭 기준 수용 확정 2026-10-31). 위 1~4절 수치는 HF 3-seed 평가이며 배포 GGUF의 보류율(18.5%)은 평가 모델(s42 HF 25.3%)보다 낮다(보고서 한계 절).\n']
    md = '\n'.join(L); (ROOT / 'reports/eval/lora_v5/presentation_numbers_v5.md').write_text(md, encoding='utf-8', newline='\n')
    strip = lambda T: {g: {k: list(v) if isinstance(v, tuple) else v for k, v in a.items()} for g, a in T.items()}
    json.dump(dict(main_numbers='LoRA v5 (user decision 2026-10-31)', test_v30_207=strip(T30), test_v5_283=strip(T5), test_v31_supp_222=strip(TS), combined_712=strip(TC), test_v5_project_n=n5,
                   sources=dict(test_v30=S30, test_v5=S5, supp=SS, combined=SC, segments=SEG, supp_truth=SUPP)),
              open(ROOT / 'reports/eval/lora_v5/presentation_numbers_v5.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(md)


if __name__ == '__main__':
    main()
