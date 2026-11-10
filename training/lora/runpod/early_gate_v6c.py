"""S8 early gate on the pod (no model code). Scores one test_v5 oas_code prediction file with the scripts/eval_combined_v5.py definitions (same code as
training/lora/runpod/s4_ctx/score_ctx.py) and compares its macro-F1 with the v5 s42 baseline file scored by the same code.
Pre-registered rule (AGENTS.md "작업 S8", user decision 2026-11-04): if v6c s42 test_v5 oas_code macro-F1 <= v5 s42 (0.6661, scores_test_v5.json) then
seeds 43/44 and the base zero-shot are NOT run, the result is "not adopted" and the pod stops.
  python early_gate_v6c.py --pred runs/lora_v6c_s42/eval/v5test_predictions_oas_code_lora_v6c_s42_final.jsonl --baseline baseline/v5test_predictions_oas_code_lora_v5_s42_final.jsonl \
                           --inputs data_v5/test_v5_inputs.jsonl --out runs/lora_v6c_s42/eval/early_gate.json
Prints GATE=PASS or GATE=STOP as the last line (exit code 0 either way; a scoring error exits 2)."""
import argparse, json, sys
from collections import defaultdict

L = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']; MANUAL = 'manual_review_required'
V5_S42_EXPECTED = 0.6661   # reports/eval/lora_v5/scores_test_v5.json, lora_v5_s42_final oas_code macro_f1 (the baseline file is re-scored here and must reproduce it)
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
                concrete=dict(n_truth_concrete=len(conc), answered=len(ans), precision=round(sum(t == p for t, p in ans) / len(ans), 4) if ans else None, recall=round(sum(t == p for t, p in conc) / len(conc), 4)),
                per_label=per)


def score_file(pred_path, inputs_path):
    inputs = {r['id']: r for r in rd(inputs_path) if 'oas_code_user' in r}
    preds = {r['id']: r for r in rd(pred_path)}; ids = [i for i in inputs if i in preds]
    assert len(ids) == 283 and len(inputs) == 283, ('test_v5 oas_code must have 283 scored rows', len(ids), len(inputs))
    pl = lambda r: r['prediction']['label'] if r.get('prediction') else 'output_error'
    pairs = [(inputs[i]['label'], pl(preds[i])) for i in ids]; m = metrics(pairs); m['pred'] = pred_path
    proj = defaultdict(list)
    for i in ids: proj[i.split('-')[1]].append(inputs[i]['label'] == pl(preds[i]))
    m['per_project'] = {p: dict(n=len(v), accuracy=round(sum(v) / len(v), 4)) for p, v in sorted(proj.items())}
    return m


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--pred', required=True); ap.add_argument('--baseline', required=True); ap.add_argument('--inputs', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    try:
        v6c = score_file(a.pred, a.inputs); v5 = score_file(a.baseline, a.inputs)
    except Exception as e:
        print(f'early gate scoring error: {e!r}'); sys.exit(2)
    assert abs(v5['macro_f1'] - V5_S42_EXPECTED) < 1e-4, f"baseline re-score {v5['macro_f1']} != expected {V5_S42_EXPECTED}: wrong baseline file or scorer"
    passed = v6c['macro_f1'] > v5['macro_f1']
    out = dict(rule='STOP if v6c s42 test_v5 oas_code macro-F1 <= v5 s42 macro-F1 (pre-registered, AGENTS.md 작업 S8)', gate='PASS' if passed else 'STOP',
               v6c_s42=dict(macro_f1=v6c['macro_f1'], accuracy=v6c['accuracy'], manual_ratio=v6c['manual_ratio'], output_errors=v6c['output_errors'], concrete=v6c['concrete'], per_project=v6c['per_project'], per_label=v6c['per_label']),
               v5_s42=dict(macro_f1=v5['macro_f1'], accuracy=v5['accuracy'], manual_ratio=v5['manual_ratio'], output_errors=v5['output_errors'], concrete=v5['concrete'], per_project=v5['per_project']),
               delta_macro_f1=round(v6c['macro_f1'] - v5['macro_f1'], 4), pred=a.pred, baseline=a.baseline)
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ('gate', 'delta_macro_f1')} | dict(v6c_macro_f1=v6c['macro_f1'], v5_macro_f1=v5['macro_f1'], v6c_accuracy=v6c['accuracy'], v6c_manual=v6c['manual_ratio'], v6c_errors=v6c['output_errors'])))
    print('GATE=' + out['gate'])


if __name__ == '__main__': main()
