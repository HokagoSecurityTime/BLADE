"""S4 scoring + budget selection on the pod (also runnable locally). No model code.
  score   --pred P --inputs I --kind test_v5|test_v30_207 [--out J]   metrics = scripts/eval_combined_v5.py definitions:
          macro-F1 over labels with support, accuracy, manual ratio, output errors, concrete precision/recall (truth concrete; answered = not manual/error),
          per-label P/R/F1; test_v30_207 adds public misjudge (declared ∧ pred public ∧ truth≠public, denominator declared ∧ truth≠public);
          test_v5 adds per-project accuracy (id prefix v5t-<project>-).
  select  --out-dir OUT --baseline-dir B      budget rule (AGENTS.md S4, user decision 2026-11-04, seed 42):
          1) ctx6144 is rejected if, vs the v5 s42 baseline, test_v30 207 concrete precision drops by > 0.025 or public misjudge > 2 -> ctx4096
          2) else the budget with the higher test_v5 macro-F1; if the difference < 0.016 (v5 seed sd) -> ctx4096 (inside the training length)
  summary --out-dir OUT --baseline-dir B      summary.json / summary.md over every prediction file present (s42 both budgets, s43/s44 selected budget)."""
from __future__ import annotations
import argparse, json, os, statistics as st
from collections import Counter, defaultdict
from pathlib import Path

L = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']; MANUAL = 'manual_review_required'
SEEDS = [42, 43, 44]; BUDGETS = ['ctx4096', 'ctx6144']; SETS = ['test_v5', 'test_v30']
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]


def metrics(pairs):
    per = {}
    for l in L:
        tp = sum(t == l and p == l for t, p in pairs); fp = sum(t != l and p == l for t, p in pairs); fn = sum(t == l and p != l for t, p in pairs)
        P = tp / (tp + fp) if tp + fp else 0.; R = tp / (tp + fn) if tp + fn else 0.; F = 2 * P * R / (P + R) if P + R else 0.
        per[l] = dict(support=sum(t == l for t, _ in pairs), precision=round(P, 4), recall=round(R, 4), f1=round(F, 4))
    sup = [l for l in L if per[l]['support']]
    conc = [(t, p) for t, p in pairs if t != MANUAL]; ans = [(t, p) for t, p in conc if p not in (MANUAL, 'output_error')]
    return dict(records=len(pairs), macro_f1=round(sum(per[l]['f1'] for l in sup) / len(sup), 4), supported_labels=len(sup), accuracy=round(sum(t == p for t, p in pairs) / len(pairs), 4),
                manual_ratio=round(sum(p == MANUAL for _, p in pairs) / len(pairs), 4), output_errors=sum(p == 'output_error' for _, p in pairs),
                concrete=dict(n_truth_concrete=len(conc), answered=len(ans), answer_rate=round(len(ans) / len(conc), 4), precision=round(sum(t == p for t, p in ans) / len(ans), 4) if ans else None, recall=round(sum(t == p for t, p in conc) / len(conc), 4)),
                per_label=per)


def score_file(pred_path, inputs_path, kind):
    inputs = {r['id']: r for r in rd(inputs_path) if 'oas_code_user' in r}
    if kind == 'test_v30_207': inputs = {i: r for i, r in inputs.items() if r.get('source') == 'vuln'}
    preds = {r['id']: r for r in rd(pred_path)}; ids = [i for i in inputs if i in preds]
    assert len(ids) == (283 if kind == 'test_v5' else 207), (kind, len(ids))
    pl = lambda r: r['prediction']['label'] if r.get('prediction') else 'output_error'
    pairs = [(inputs[i]['label'], pl(preds[i])) for i in ids]; m = metrics(pairs); m['kind'] = kind; m['pred'] = str(pred_path)
    if kind == 'test_v30_207':
        decl = [i for i in ids if inputs[i].get('security_state') == 'declared' and inputs[i]['label'] != 'public']
        mis = [i for i in decl if pl(preds[i]) == 'public']; m['public_misjudge'] = dict(count=len(mis), denominator=len(decl), ids=mis)
    else:
        proj = defaultdict(list)
        for i in ids: proj[i.split('-')[1]].append(inputs[i]['label'] == pl(preds[i]))
        m['per_project'] = {p: dict(n=len(v), accuracy=round(sum(v) / len(v), 4)) for p, v in sorted(proj.items())}
    m['prompt_tokens_max'] = max((preds[i].get('prompt_tokens') or 0) for i in ids); m['mean_ms_per_row'] = round(sum(preds[i].get('inference_ms', 0) for i in ids) / len(ids), 1)
    return m


def load_scores(out_dir, baseline_dir):
    """{(set, budget|'v5', seed): metrics} for every prediction file present."""
    out_dir, baseline_dir = Path(out_dir), Path(baseline_dir); S = {}
    inputs = {s: {bk: out_dir.parent / 'data' / f'{s}_{bk}_inputs.jsonl' for bk in BUDGETS} for s in SETS}
    for s in SETS:
        kind = 'test_v5' if s == 'test_v5' else 'test_v30_207'
        for bk in BUDGETS:
            for seed in SEEDS:
                p = out_dir / f'pred_{s}_{bk}_s{seed}.jsonl'
                if p.exists(): S[(s, bk, seed)] = score_file(p, inputs[s][bk], kind)
        for seed in SEEDS:  # v5 baseline (no context): the exported RunPod predictions, scored with the same code
            name = ('v5test_predictions_oas_code_' if s == 'test_v5' else 'predictions_oas_code_') + f'lora_v5_s{seed}_final.jsonl'; p = baseline_dir / name
            if p.exists(): S[(s, 'v5', seed)] = score_file(p, inputs[s]['ctx4096'], kind)
    return S


def select(args):
    S = load_scores(args.out_dir, args.baseline_dir); need = [('test_v30', 'ctx6144', 42), ('test_v30', 'v5', 42), ('test_v5', 'ctx4096', 42), ('test_v5', 'ctx6144', 42)]
    missing = [k for k in need if k not in S]; assert not missing, f'missing scores for selection: {missing}'
    b30 = S[('test_v30', 'v5', 42)]; c30 = S[('test_v30', 'ctx6144', 42)]; f4 = S[('test_v5', 'ctx4096', 42)]['macro_f1']; f6 = S[('test_v5', 'ctx6144', 42)]['macro_f1']
    drop = round(b30['concrete']['precision'] - c30['concrete']['precision'], 4); pub = c30['public_misjudge']['count']
    if drop > 0.025 or pub > 2: chosen, why = 'ctx4096', f'rule 1: ctx6144 test_v30 concrete precision drop {drop} > 0.025 or public misjudge {pub} > 2'
    elif abs(f6 - f4) < 0.016: chosen, why = 'ctx4096', f'rule 2: test_v5 macro-F1 difference |{f6} - {f4}| = {abs(f6 - f4):.4f} < 0.016 -> ctx4096 (training length)'
    else: chosen, why = ('ctx6144' if f6 > f4 else 'ctx4096'), f'rule 2: higher test_v5 macro-F1 (ctx4096 {f4}, ctx6144 {f6})'
    sel = dict(chosen=chosen, reason=why, s42=dict(test_v5_macro_f1={'ctx4096': f4, 'ctx6144': f6}, test_v30_concrete_precision={'v5': b30['concrete']['precision'], 'ctx4096': S.get(('test_v30', 'ctx4096', 42), {}).get('concrete', {}).get('precision'), 'ctx6144': c30['concrete']['precision']},
                                                   test_v30_public_misjudge={'v5': b30['public_misjudge']['count'], 'ctx4096': S.get(('test_v30', 'ctx4096', 42), {}).get('public_misjudge', {}).get('count'), 'ctx6144': pub}))
    Path(args.out_dir, 'selection.json').write_text(json.dumps(sel, ensure_ascii=False, indent=1), encoding='utf-8'); print(json.dumps(sel, ensure_ascii=False)); print('BUDGET=' + chosen)


def ms(vals, pct=False):
    if not vals: return '-'
    f = (lambda v: f'{v * 100:.1f}%') if pct else (lambda v: f'{v:.3f}')
    return f(vals[0]) if len(vals) == 1 else f'{f(st.mean(vals))} ± {f(st.stdev(vals))}'


def summary(args):
    S = load_scores(args.out_dir, args.baseline_dir); out = Path(args.out_dir)
    Path(out, 'scores_all.json').write_text(json.dumps({f'{s}|{bk}|s{seed}': v for (s, bk, seed), v in S.items()}, ensure_ascii=False, indent=1), encoding='utf-8')
    t = ['# S4 pod summary (scored on the pod; the final report is written locally)', '']
    for s in SETS:
        t += [f'## {s}', '', '| model | seeds | macro-F1 | accuracy | concrete P | concrete R | manual | output errors | ' + ('public misjudge' if s == 'test_v30' else 'ghost / rocketchat / umami acc') + ' |', '|---|---|---|---|---|---|---|---|---|']
        for bk in ['v5'] + BUDGETS:
            rs = [S[(s, bk, seed)] for seed in SEEDS if (s, bk, seed) in S]
            if not rs: continue
            extra = ' / '.join(str(r['public_misjudge']['count']) for r in rs) if s == 'test_v30' else ' · '.join(f"{p}: {ms([r['per_project'][p]['accuracy'] for r in rs if p in r['per_project']])}" for p in ('ghost', 'rocketchat', 'umami'))
            t.append(f"| {bk} | {','.join(str(seed) for seed in SEEDS if (s, bk, seed) in S)} | {ms([r['macro_f1'] for r in rs])} | {ms([r['accuracy'] for r in rs])} | {ms([r['concrete']['precision'] for r in rs])} | {ms([r['concrete']['recall'] for r in rs])} | {ms([r['manual_ratio'] for r in rs], True)} | {' / '.join(str(r['output_errors']) for r in rs)} | {extra} |")
        t.append('')
    sel = Path(out, 'selection.json'); t += ['## budget selection', '', sel.read_text(encoding='utf-8') if sel.exists() else '(not run)', '']
    tim = sorted(out.glob('*.timing.json')); t += ['## timing', '', '| file | gpu | rows | model load s | inference wall s | ms/row | parse errors | prompt tokens max | truncated |', '|---|---|---|---|---|---|---|---|---|']
    for p in tim:
        j = json.loads(p.read_text(encoding='utf-8')); t.append(f"| {Path(j['out']).name} | {j['gpu']} | {j['rows_total']} | {j['model_load_s']} | {j['inference_wall_s']} | {j['mean_ms_per_row']} | {j['parse_errors']} | {j['prompt_tokens_max']} | {j['truncated_prompts']} |")
    Path(out, 'summary.md').write_text('\n'.join(t) + '\n', encoding='utf-8'); print('\n'.join(t))


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('score'); a.add_argument('--pred', required=True); a.add_argument('--inputs', required=True); a.add_argument('--kind', choices=['test_v5', 'test_v30_207'], required=True); a.add_argument('--out')
    for c in ('select', 'summary'):
        b = sub.add_parser(c); b.add_argument('--out-dir', required=True); b.add_argument('--baseline-dir', required=True)
    args = ap.parse_args()
    if args.cmd == 'score':
        m = score_file(args.pred, args.inputs, args.kind); print(json.dumps({k: m[k] for k in m if k != 'per_label'}, ensure_ascii=False))
        if args.out: Path(args.out).write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')
    elif args.cmd == 'select': select(args)
    else: summary(args)


if __name__ == '__main__': main()
