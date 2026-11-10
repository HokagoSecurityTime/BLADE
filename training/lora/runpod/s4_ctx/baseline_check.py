"""S4-3 step 2: baseline reproduction check. 20 stratified test_v5 ids (label-proportional, largest remainder, seed 42) are re-inferred on this pod
with the v5 s42 adapter and the ORIGINAL (no-context) test_v5 inputs; their labels are compared with the exported v5 s42 predictions.
  python baseline_check.py ids   --inputs data/test_v5_inputs.jsonl --out out/baseline_ids.json          -> writes the 20 ids
  python baseline_check.py compare --pred out/baseline_s42.jsonl --baseline baseline/v5test_predictions_oas_code_lora_v5_s42_final.jsonl --out out/baseline_check.json
Gate: agreement >= 0.95 (19/20) -> continue; else stop and report (mismatches listed)."""
from __future__ import annotations
import argparse, json, random
from collections import Counter
from pathlib import Path

rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
N = 20; SEED = 42


def pick(rows):
    sup = Counter(r['label'] for r in rows); labels = sorted(sup); total = sum(sup.values())
    raw = {l: sup[l] * N / total for l in labels}; alloc = {l: int(raw[l]) for l in labels}
    for l in sorted(labels, key=lambda l: (-(raw[l] - alloc[l]), l))[: N - sum(alloc.values())]: alloc[l] += 1
    rng = random.Random(SEED); ids = []
    for l in labels:
        pool = sorted(r['id'] for r in rows if r['label'] == l); ids += rng.sample(pool, alloc[l])
    return ids, alloc


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('ids'); a.add_argument('--inputs', required=True); a.add_argument('--out', required=True)
    b = sub.add_parser('compare'); b.add_argument('--pred', required=True); b.add_argument('--baseline', required=True); b.add_argument('--out', required=True)
    args = ap.parse_args()
    if args.cmd == 'ids':
        rows = [r for r in rd(args.inputs) if 'oas_code_user' in r]; ids, alloc = pick(rows)
        Path(args.out).write_text(json.dumps(ids, indent=0), encoding='utf-8'); print(json.dumps(dict(n=len(ids), allocation=alloc, ids=ids)))
    else:
        pl = lambda r: r['prediction']['label'] if r.get('prediction') else 'output_error'
        pred = {r['id']: r for r in rd(args.pred)}; base = {r['id']: r for r in rd(args.baseline)}; ids = [i for i in pred if i in base]
        agree = [i for i in ids if pl(pred[i]) == pl(base[i])]; mism = [dict(id=i, pod=pl(pred[i]), exported=pl(base[i]), raw_pod=pred[i]['raw'][:200], raw_exported=base[i]['raw'][:200]) for i in ids if pl(pred[i]) != pl(base[i])]
        res = dict(n=len(ids), agree=len(agree), agreement=round(len(agree) / len(ids), 4) if ids else None, passed=bool(ids) and len(agree) / len(ids) >= 0.95, mismatches=mism,
                   raw_identical=sum(pred[i]['raw'].strip() == base[i]['raw'].strip() for i in ids))
        Path(args.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8'); print(json.dumps({k: res[k] for k in ('n', 'agree', 'agreement', 'passed', 'raw_identical')}))
        print('BASELINE_PASSED=' + ('1' if res['passed'] else '0'))


if __name__ == '__main__': main()
