"""Choose the pipeline LoRA confidence threshold from val_v4 predictions only (test_v30 is never read).

Rule (fixed before looking at val results): a concrete prediction with confidence < t becomes manual_review_required
(parse failures are manual too; the existing ClassificationResult rule already makes confidence < 0.7 manual).
Candidates: 0 and every distinct confidence the model produced on val. Choose the t with the highest val macro-F1
over the 7 labels; on a tie the lower t (fewer abstentions). Concrete precision and the manual ratio are reported.
--rule precision (user decision 2026-10-30, fixed before the val run): the GGUF model abstains less than the HF model, so
choose the t with the highest val concrete precision; on a tie the lower t. There are no HF s42 val predictions (RunPod
used val for loss only) and test numbers must not be a target, so the full val precision / abstention curve is reported.

Usage: python -X utf8 training/lora/choose_threshold_v4.py --pred reports/eval/lora_v4_gguf/val_predictions_lora_v4_s42_gguf_q4km.jsonl
"""
import argparse, json
from pathlib import Path

LABELS = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']
MANUAL = 'manual_review_required'
EXISTING_FLOOR = 0.7  # pipeline.classifier.schema.ClassificationResult.low_confidence


def predict(row: dict, t: float) -> str:
    p = row['prediction']
    if p is None or not isinstance(p.get('confidence'), (int, float)): return MANUAL
    if p['label'] != MANUAL and p['confidence'] < max(t, EXISTING_FLOOR): return MANUAL
    return p['label']


def score(rows: list[dict], t: float) -> dict:
    pred = [predict(r, t) for r in rows]; gold = [r['label'] for r in rows]
    per = {}
    for l in LABELS:
        tp = sum(p == l and g == l for p, g in zip(pred, gold)); fp = sum(p == l and g != l for p, g in zip(pred, gold)); fn = sum(p != l and g == l for p, g in zip(pred, gold))
        pr = tp / (tp + fp) if tp + fp else 0.0; rc = tp / (tp + fn) if tp + fn else 0.0
        per[l] = dict(support=sum(g == l for g in gold), precision=round(pr, 4), recall=round(rc, 4), f1=round(2 * pr * rc / (pr + rc) if pr + rc else 0.0, 4))
    present = [l for l in LABELS if per[l]['support']]
    concrete = [(p, g) for p, g in zip(pred, gold) if p != MANUAL]
    truth_concrete = [(p, g) for p, g in zip(pred, gold) if g != MANUAL]
    return dict(threshold=t, macro_f1=round(sum(per[l]['f1'] for l in present) / len(present), 4),
                accuracy=round(sum(p == g for p, g in zip(pred, gold)) / len(rows), 4),
                concrete_precision=round(sum(p == g for p, g in concrete) / len(concrete), 4) if concrete else 0.0,
                concrete_recall=round(sum(p == g for p, g in truth_concrete) / len(truth_concrete), 4) if truth_concrete else 0.0,
                manual_ratio=round(sum(p == MANUAL for p in pred) / len(rows), 4), per_label=per)


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument('--pred', type=Path, required=True); ap.add_argument('--out', type=Path)
    ap.add_argument('--rule', choices=['macro_f1', 'precision'], default='macro_f1')
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(a.pred, encoding='utf-8') if l.strip()]
    assert all('condition' in r for r in rows), 'expects val_sft_v4 predictions (eval_ollama_v4.py --split val)'
    confs = sorted({r['prediction']['confidence'] for r in rows if r['prediction'] and isinstance(r['prediction'].get('confidence'), (int, float))})
    table = [score(rows, t) for t in sorted({0.0, *confs})]
    best = max(table, key=lambda s: (s[{'macro_f1': 'macro_f1', 'precision': 'concrete_precision'}[a.rule]], -s['threshold']))
    by_cond = {c: score([r for r in rows if r['condition'] == c], best['threshold']) for c in sorted({r['condition'] for r in rows})}
    out = dict(rule=f'max val {a.rule} (7 labels), tie -> lower threshold; existing floor 0.7 applies', rows=len(rows),
               parse_errors=sum(r['prediction'] is None for r in rows), confidence_values={str(c): sum(1 for r in rows if r['prediction'] and r['prediction'].get('confidence') == c) for c in confs},
               candidates=table, chosen=best['threshold'], chosen_by_condition={c: {k: v for k, v in s.items() if k != 'per_label'} for c, s in by_cond.items()})
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if a.out: a.out.write_text(text, encoding='utf-8')
    print(json.dumps({k: v for k, v in out.items() if k != 'candidates'} | dict(candidates=[{k: v for k, v in s.items() if k != 'per_label'} for s in table]), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
