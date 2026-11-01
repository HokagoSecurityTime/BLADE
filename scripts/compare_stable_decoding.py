"""Task B (reports/eval/stable_decoding): compare default decoding (reports/eval/lora_v4 scores, 2026-10-27 run) with stable decoding
(repetition_penalty 1.1 + JSON-schema constrained decoding, same adapters, same inputs, 2026-10-30 re-inference). No training, no inference here.
Per model group (base, v2, v3b, v4; 3 seeds each except base): mean ± std of the eval-def v2 metrics, output-error counts, output-error kinds
(truncated at max_new_tokens 256 vs other), label recoverable from truncated output, inference ms/row. Writes comparison.json and prints markdown tables.
Pre-fixed acceptance criterion (recorded before the run): output errors decrease AND concrete precision / macro-F1 (oas_code, synthetic excluded) do not
drop by more than one seed-std. Decided per group from the numbers only."""
from __future__ import annotations
import json, re, statistics as st, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEF = ROOT / 'reports/eval/lora_v4'; STA = ROOT / 'reports/eval/stable_decoding'
MAX_NEW = 256
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]


def group(model):
    m = re.match(r'(.+?)_s(\d+)(_.*)?$', model)
    g = (m.group(1) + (m.group(3) or '')) if m else model
    return g.replace('_final', '').replace('_stable', '').replace('_runpod', '')


def ms(xs, nd=3):
    xs = [x for x in xs if x is not None]
    if not xs: return '-'
    return f'{st.mean(xs):.{nd}f} ± {st.stdev(xs):.{nd}f}' if len(xs) > 1 else f'{xs[0]:.{nd}f}'


def load_scores(d):
    v30 = [e for e in json.load(open(d / 'scores_test_v30.json', encoding='utf-8')) if e['eval_def'] == 'v2']
    supp = json.load(open(d / 'scores_supp.json', encoding='utf-8'))
    return v30, supp


def error_kinds(pred_dir_glob, tok):
    """Per prediction file: output errors split into truncated (>= MAX_NEW-2 generated tokens) / other; label present in truncated raw; mean inference ms."""
    out = {}
    for p in sorted(ROOT.glob(pred_dir_glob)):
        rows = rd(p); errs = [r for r in rows if not r.get('prediction')]
        trunc = other = label_ok = 0
        for r in errs:
            n = len(tok(r.get('raw') or '')['input_ids']) if tok else None
            is_trunc = (n is not None and n >= MAX_NEW - 2) or (n is None and len(r.get('raw') or '') > 300)
            trunc += is_trunc; other += not is_trunc
            if is_trunc and re.search(r'"label"\s*:\s*"(public|role_required|membership_required|tenant_match|owner_match|owner_or_admin|manual_review_required)"', r.get('raw') or ''): label_ok += 1
        out[p.name] = dict(rows=len(rows), errors=len(errs), truncated=trunc, other=other, truncated_label_present=label_ok, mean_ms=round(st.mean([r['inference_ms'] for r in rows]), 1) if rows else None)
    return out


def main():
    try:
        from transformers import AutoTokenizer; tok = AutoTokenizer.from_pretrained('unsloth/Qwen2.5-7B-Instruct-bnb-4bit')
    except Exception as e:
        print('tokenizer unavailable, truncation inferred from raw length:', repr(e)); tok = None
    d30, dsupp = load_scores(DEF); s30, ssupp = load_scores(STA)
    kinds = dict(default=error_kinds('reports/eval/lora_v4/*/eval/*predictions_*.jsonl', tok), stable=error_kinds('reports/eval/stable_decoding/*/eval_stable/*predictions_*.jsonl', tok))
    groups = ['base_qwen', 'lora_v2', 'lora_v3b', 'lora_v4']
    def collect(entries, cond, key):
        g = defaultdict(list)
        for e in entries:
            if e['condition'] != cond: continue
            gr = group(e['model'])
            if gr not in groups: continue   # v3a: not re-run in task B
            g[gr].append(key(e))
        return g
    def errs_total(kind, gr, pattern):
        tot = defaultdict(int)
        for name, v in kinds[kind].items():
            if group(re.sub(r'^(supp_)?predictions_(oas_code|oas)_', '', Path(name).stem)) == gr and re.match(pattern, name):
                for k in ('errors', 'truncated', 'other', 'truncated_label_present'): tot[k] += v[k]
        return dict(tot)
    def ms_mean(kind, gr, pattern):
        xs = [v['mean_ms'] for name, v in kinds[kind].items() if group(re.sub(r'^(supp_)?predictions_(oas_code|oas)_', '', Path(name).stem)) == gr and re.match(pattern, name) and v['mean_ms']]
        return round(st.mean(xs)) if xs else None
    metrics = {
        'oas_code 합성 제외 macro-F1': ('oas_code', lambda e: e['main_excl_synthetic']['macro_f1']),
        'oas_code 합성 제외 구체 정밀도': ('oas_code', lambda e: e['main_excl_synthetic']['concrete']['precision']),
        'oas_code 합성 제외 구체 재현율': ('oas_code', lambda e: e['main_excl_synthetic']['concrete']['recall']),
        'oas_code 합성 제외 manual 비율': ('oas_code', lambda e: e['main_excl_synthetic']['manual_ratio']),
        'oas_code 합성 포함 macro-F1': ('oas_code', lambda e: e['main']['macro_f1']),
        'oas_code public 오판(신, 건수)': ('oas_code', lambda e: e['public_misjudge_new']['count']),
        'oas 주지표(160) macro-F1': ('oas', lambda e: e['main']['macro_f1']),
        'oas 합성 제외 macro-F1': ('oas', lambda e: e['main_excl_synthetic']['macro_f1']),
        'oas 합성 제외 구체 정밀도': ('oas', lambda e: e['main_excl_synthetic']['concrete']['precision']),
        'oas 주지표 manual 비율': ('oas', lambda e: e['main']['manual_ratio']),
        'oas public 오판(신, 건수)': ('oas', lambda e: e['public_misjudge_new']['count']),
    }
    supp_metrics = {'supp oas_code macro-F1': ('oas_code', lambda e: e['macro_f1']), 'supp oas_code 정확도': ('oas_code', lambda e: e['accuracy']), 'supp oas_code manual 비율': ('oas_code', lambda e: e['manual_ratio']),
                    'supp oas macro-F1': ('oas', lambda e: e['macro_f1']), 'supp oas 정확도': ('oas', lambda e: e['accuracy'])}
    result = dict(groups={}, error_kinds=kinds, criterion='output errors decrease AND oas_code(synthetic excluded) concrete precision and macro-F1 do not drop by more than one seed-std (pre-fixed)')
    lines = []
    lines.append('| 지표 | 모델 | 기본 디코딩 (2026-10-27) | 안정화 디코딩 (2026-10-30) | 차이(평균) |\n|---|---|---:|---:|---:|')
    for name, (cond, key) in list(metrics.items()) + list(supp_metrics.items()):
        src_d, src_s = (dsupp, ssupp) if name.startswith('supp') else (d30, s30)
        gd, gs = collect(src_d, cond, key), collect(src_s, cond, key)
        for gr in groups:
            a, b = gd.get(gr, []), gs.get(gr, [])
            if not a or not b: continue
            nd = 0 if '건수' in name else 3
            diff = st.mean(b) - st.mean(a)
            result['groups'].setdefault(gr, {})[name] = dict(default=a, stable=b, default_mean=st.mean(a), stable_mean=st.mean(b), default_std=st.stdev(a) if len(a) > 1 else None, stable_std=st.stdev(b) if len(b) > 1 else None)
            lines.append(f'| {name} | {gr} | {ms(a, nd)} | {ms(b, nd)} | {diff:+.{nd}f} |')
    lines.append('\n| 모델 | 파일군 | 기본: 오류 합 (잘림/그 외) | 안정화: 오류 합 (잘림/그 외) | 안정화 잘림 중 label 존재 | 기본 ms/row | 안정화 ms/row |\n|---|---|---:|---:|---:|---:|---:|')
    for gr in groups:
        for label, pat in (('test_v30 oas', r'^predictions_oas_[^c]'), ('test_v30 oas_code', r'^predictions_oas_code_'), ('supp oas', r'^supp_predictions_oas_[^c]'), ('supp oas_code', r'^supp_predictions_oas_code_'), ('전체 4종', r'.')):
            a, b = errs_total('default', gr, pat), errs_total('stable', gr, pat)
            result['groups'].setdefault(gr, {})[f'errors {label}'] = dict(default=a, stable=b)
            lines.append(f"| {gr} | {label} | {a.get('errors', 0)} ({a.get('truncated', 0)}/{a.get('other', 0)}) | {b.get('errors', 0)} ({b.get('truncated', 0)}/{b.get('other', 0)}) | {b.get('truncated_label_present', 0)} | {ms_mean('default', gr, pat) or '-'} | {ms_mean('stable', gr, pat) or '-'} |")
    # criterion per group
    lines.append('\n| 모델 | 출력 오류(4종 합) 기본→안정화 | 구체 정밀도(oas_code 합성 제외) 기본→안정화, 허용 하한(기본 평균 − 기본 std) | macro-F1(oas_code 합성 제외) 기본→안정화, 허용 하한 | 판정 |\n|---|---|---|---|---|')
    for gr in groups:
        G = result['groups'].get(gr, {})
        if 'oas_code 합성 제외 구체 정밀도' not in G: continue
        e_d, e_s = G['errors 전체 4종']['default'].get('errors', 0), G['errors 전체 4종']['stable'].get('errors', 0)
        P, F = G['oas_code 합성 제외 구체 정밀도'], G['oas_code 합성 제외 macro-F1']
        sdP = P['default_std'] or 0; sdF = F['default_std'] or 0
        okE = e_s < e_d; okP = P['stable_mean'] >= P['default_mean'] - sdP; okF = F['stable_mean'] >= F['default_mean'] - sdF
        verdict = '채택 가능' if (okE and okP and okF) else '채택 불가'
        if gr == 'base_qwen': verdict += ' (단일 run, std 없음)'
        result['groups'][gr]['verdict'] = dict(errors_default=e_d, errors_stable=e_s, errors_ok=okE, precision_ok=okP, macro_f1_ok=okF, verdict=verdict)
        lines.append(f"| {gr} | {e_d} → {e_s} ({'감소' if okE else '감소 아님'}) | {P['default_mean']:.3f} → {P['stable_mean']:.3f}, 하한 {P['default_mean'] - sdP:.3f} ({'충족' if okP else '미달'}) | {F['default_mean']:.3f} → {F['stable_mean']:.3f}, 하한 {F['default_mean'] - sdF:.3f} ({'충족' if okF else '미달'}) | {verdict} |")
    (STA / 'comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
    (STA / 'comparison_tables.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__': main()
