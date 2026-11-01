"""Abstention-threshold calibration for LoRA v2 (local, read-only). Input: label-conditional log-prob score files produced by
training/lora/lora_v2_abstain_calib.ipynb, copied to reports/eval/lora_v2/calib/lora_v2_seed<N>/scores_{val|test}_{oas|oas_code}_<tag>.jsonl.
Decision rule: scores[manual] -= b, then argmax over the 7 labels. b is swept and CHOSEN ON val_v2 ONLY (pre-registered rule, see RULE);
the chosen b is applied to test_v30 once and scored with eval-def v2 (scripts/eval_v30.py). The test b-curve is printed for reference only.
No training, no API calls; data-v1/data-v2 hashes asserted at start and end; test_v30 never modified."""
from __future__ import annotations
import argparse, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from data_v1_guard import assert_data_v1
from data_v2_guard import assert_data_v2
import eval_v30 as E
L, MANUAL = E.L, E.MANUAL
RULE = 'val_v2 oas_code에서 public 오판(신 정의: declared ∧ 예측 public ∧ 정답≠public)이 0인 b 범위 안에서 구체 재현율 최대; 동률이면 가장 작은 b. b=0에서 이미 0이 아니면 b=0(무조정)으로 두고 보고.'
B_GRID = [round(0.25 * i, 2) for i in range(0, 161)]  # 0 .. 40 nats
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]

def decide(scores: dict, b: float) -> str:
    s = dict(scores); s[MANUAL] = s[MANUAL] - b
    best = max(L, key=lambda l: (s[l], -L.index(l)))  # deterministic tie-break by label order
    return best

def val_metrics(rows, b):
    pairs = [(r['label'], decide(r['scores'], b)) for r in rows]
    per, mf, n = E.prf(pairs); conc = E.concrete(pairs)
    declared = [(r, p) for (r, (t, p)) in zip(rows, pairs) if r['security_state'] == 'declared']
    pub_new = sum(p == 'public' and r['label'] != 'public' for r, p in declared); pub_den = sum(r['label'] != 'public' for r, _ in declared)
    return dict(b=b, n=len(rows), macro_f1=mf, manual_ratio=round(sum(p == MANUAL for _, p in pairs) / len(pairs), 4), accuracy=round(sum(t == p for t, p in pairs) / len(pairs), 4),
                concrete_precision=conc['precision'], concrete_recall=conc['recall'], answer_rate=conc['answer_rate'], public_misjudge=pub_new, public_den=pub_den, per_label_f1={l: per[l]['f1'] for l in L if per[l]['support']})

def select_b(curve):
    ok = [m for m in curve if m['public_misjudge'] == 0]
    if not ok or curve[0]['public_misjudge'] != 0: return 0.0, 'b=0에서 public 오판>0 → 규칙 적용 불가, 무조정' if curve[0]['public_misjudge'] != 0 else '후보 없음'
    # contiguous range from b=0 while public misjudge stays 0
    rng = []
    for m in curve:
        if m['public_misjudge'] == 0: rng.append(m)
        else: break
    best = max(rng, key=lambda m: (m['concrete_recall'], -m['b']))
    return best['b'], f"public 오판 0 유지 범위 b∈[0, {rng[-1]['b']}] 안에서 구체 재현율 최대 {best['concrete_recall']} (b={best['b']})"

def to_pred_rows(rows, b, mode_tag):
    return [dict(id=r['id'], label=r['label'], source=r['source'], security_state=r['security_state'], prediction=dict(label=decide(r['scores'], b), confidence=None, rationale=f'calib argmax, manual penalty b={b}', evidence_fields=[]), raw=json.dumps(r['scores']), inference_ms=r.get('ms')) for r in rows]

def fmt(x, nd=3): return '-' if x is None else (f'{x:.{nd}f}' if isinstance(x, float) else str(x))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--calib-dir', default=str(ROOT / 'reports/eval/lora_v2/calib')); ap.add_argument('--out', default=None, help='report md (default <calib-dir>/../abstain_calib.md)')
    ap.add_argument('--seeds', default='42,43,44'); ap.add_argument('--tag', default='lora_v2_s{seed}_final'); ap.add_argument('--no-guard', action='store_true', help='dry-run on dummy scores only')
    ap.add_argument('--banner', default='', help='text placed at the top of the report (e.g. provisional/invalid notice)')
    a = ap.parse_args(); C = Path(a.calib_dir); seeds = [int(s) for s in a.seeds.split(',')]; out_md = Path(a.out) if a.out else C.parent / 'abstain_calib.md'
    if not a.no_guard: g1, g2 = assert_data_v1('start'), assert_data_v2('start')
    meta, seg = E.segments(); pred_dir = C / 'predictions'; pred_dir.mkdir(parents=True, exist_ok=True)
    results = {}; t = '# LoRA v2 보류 문턱 조정 — manual 감점 b (val_v2에서만 선택, test_v30 1회 적용)\n\n' + (f'> **{a.banner}**\n\n' if a.banner else '')
    t += f'판정: 7개 label 조건부 로그확률(training/lora/lora_v2_abstain_calib.ipynb, 생성 아님)에서 manual 점수에 b를 빼고 argmax. **선택 규칙(사전 고정)**: {RULE} b 격자 0~40(0.25 간격). 채점: eval-def v2(scripts/eval_v30.py). data-v1·data-v2 해시 assert, test_v30 불변, 학습·API 호출 없음.\n\n'
    agree_rows = []
    def find(tag, sp, c):
        # locate by file tag (authoritative), not by folder name: downloaded folders may be misnamed; identical duplicates are tolerated, distinct duplicates are an error
        import hashlib
        cands = sorted(C.glob(f'**/scores_{sp}_{c}_{tag}.jsonl')); hs = {hashlib.sha256(p.read_bytes()).hexdigest() for p in cands}
        assert cands, f'missing scores_{sp}_{c}_{tag}.jsonl under {C}'; assert len(hs) == 1, f'conflicting copies of scores_{sp}_{c}_{tag}.jsonl: {cands}'
        rows = rd(cands[0]); assert all(r.get('tag', tag) == tag for r in rows), f'tag field mismatch in {cands[0]}'
        return rows
    for seed in seeds:
        tag = a.tag.format(seed=seed)
        S = {(sp, c): find(tag, sp, c) for sp in ('val', 'test') for c in ('oas', 'oas_code')}
        top = [max(r['scores'].values()) for r in S[('test', 'oas_code')]]
        import statistics as _st; res_validity = dict(top_logp_median=round(_st.median(top), 2), top_logp_max=round(max(top), 2))
        curves = {c: [val_metrics(S[('val', c)], b) for b in B_GRID] for c in ('oas', 'oas_code')}
        b_sel, why = select_b(curves['oas_code'])
        res = dict(seed=seed, tag=tag, b_selected=b_sel, selection_note=why, val_curve=curves, test=dict(), validity=res_validity)
        t += f'## seed {seed} ({tag})\n\n선택: **b = {b_sel}** — {why}\n\n점수 타당성: test oas_code 최고 label 로그확률 중앙값 {res_validity["top_logp_median"]}, 최대 {res_validity["top_logp_max"]} (정상이면 0에 가까워야 함; −5 미만이면 스코어링 오류 의심).\n\n'
        for c in ('oas', 'oas_code'):
            t += f'### val_v2 {c} ({len(S[("val", c)])}건) b 곡선' + (' — **선택 근거**' if c == 'oas_code' else ' — 참고(선택에 사용하지 않음)') + '\n\n'
            show = [m for m in curves[c] if m['b'] in (0, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 40) or m['b'] == b_sel]
            t += E.table([[m['b'], fmt(m['macro_f1']), f"{m['manual_ratio']:.1%}", fmt(m['concrete_precision']), fmt(m['concrete_recall']), f"{m['public_misjudge']}/{m['public_den']}"] for m in show], ['b', 'macro-F1', 'manual 비율', '구체 정밀도', '구체 재현율', 'public 오판(신)']) + '\n'
        # agreement of b=0 argmax with the generated final predictions (sanity)
        for c in ('oas', 'oas_code'):
            gp = D_PRED(seed, c)
            if gp:
                gen = {r['id']: (r['prediction']['label'] if r.get('prediction') else 'output_error') for r in gp}; rows = S[('test', c)]
                agree = sum(decide(r['scores'], 0) == gen.get(r['id']) for r in rows); agree_rows.append([seed, c, len(rows), agree, f'{agree / len(rows):.1%}'])
        # apply once to test
        for c in ('oas', 'oas_code'):
            rows = S[('test', c)]
            for b, name in ((0.0, 'b0'), (b_sel, 'bsel')):
                pr = to_pred_rows(rows, b, name); p = pred_dir / f'predictions_{c}_{tag}_calib_{name}.jsonl'
                with open(p, 'w', encoding='utf-8', newline='\n') as f:
                    for r in pr: f.write(json.dumps(r, ensure_ascii=False) + '\n')
                res['test'][(c, name)] = E.score(pr, meta, seg, c, 'v2')
            # reference curve on test (NOT used for selection)
            res['test'][(c, 'curve')] = [(b, E.score(to_pred_rows(rows, b, 'ref'), meta, seg, c, 'v2')) for b in (0, 0.5, 1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 40)]
        t += f'### test_v30 적용 (b={b_sel}, 1회) — eval-def v2\n\n'
        rows_t = []
        for c in ('oas', 'oas_code'):
            for name, lab in (('b0', 'argmax b=0 (생성 예측의 스코어링 재현)'), ('bsel', f'b={b_sel} 적용')):
                r = res['test'][(c, name)]; m = r['main']; cc = m['concrete']
                rows_t.append([c, lab, fmt(m['macro_f1']), fmt(r['main_excl_synthetic']['macro_f1']), f"{m['manual_ratio']:.1%}", f"{r['public_misjudge_new']['count']}/{r['public_misjudge_new']['denominator']}", f"{fmt(cc['precision'])} / {fmt(cc['recall'])}", f"{(r.get('aux_route_only_manual_accepted') or {}).get('accuracy', '-')}"])
        t += E.table(rows_t, ['조건', '판정', 'macro-F1 주지표', '합성 제외', 'manual 비율', 'public 오판(신)', '구체 P / R', 'route_only 보조'], 2) + '\n'
        t += '### 참고: test_v30에서의 b 곡선 — **선택에 사용하지 않음** (정밀도–처리율)\n\n'
        for c in ('oas', 'oas_code'):
            t += f'{c}:\n\n' + E.table([[b, fmt(r['main']['macro_f1']), fmt(r['main_excl_synthetic']['macro_f1']), f"{r['main']['manual_ratio']:.1%}", fmt(r['main']['concrete']['precision']), fmt(r['main']['concrete']['recall']), f"{r['public_misjudge_new']['count']}/{r['public_misjudge_new']['denominator']}"] for b, r in res['test'][(c, 'curve')]], ['b', 'macro-F1', '합성 제외', 'manual', '구체 정밀도', '구체 재현율(처리율 반영)', 'public 오판']) + '\n'
        results[seed] = res
    if agree_rows: t += '## 생성 예측과 b=0 argmax 일치율 (test, 스코어링 타당성)\n\n' + E.table(agree_rows, ['seed', '조건', '건수', '일치', '비율'], 2) + '\n'
    # seed summary
    t += '## seed 요약 (test_v30, 선택 b 적용)\n\n'
    import statistics
    rows_s = []
    for c in ('oas', 'oas_code'):
        for name, lab in (('b0', 'b=0'), ('bsel', '선택 b')):
            vals = [results[s]['test'][(c, name)] for s in seeds]
            ms = lambda xs, pct=False: ((f'{statistics.mean(xs):.1%} ± {statistics.stdev(xs):.1%}' if pct else f'{statistics.mean(xs):.3f} ± {statistics.stdev(xs):.3f}') if len(xs) > 1 else (f'{xs[0]:.1%}' if pct else f'{xs[0]:.3f}'))
            rows_s.append([c, lab, ', '.join(str(results[s]['b_selected']) for s in seeds) if name == 'bsel' else '0', ms([v['main']['macro_f1'] for v in vals]), ms([v['main_excl_synthetic']['macro_f1'] for v in vals]), ms([v['main']['manual_ratio'] for v in vals], True), '·'.join(str(v['public_misjudge_new']['count']) for v in vals) + f"/{vals[0]['public_misjudge_new']['denominator']}", ms([v['main']['concrete']['precision'] or 0 for v in vals]) + ' / ' + ms([v['main']['concrete']['recall'] or 0 for v in vals])])
    t += E.table(rows_s, ['조건', '판정', 'b(seed별)', 'macro-F1 주지표', '합성 제외', 'manual 비율', 'public 오판', '구체 P / R'], 3) + '\n'
    t += '주의: 선택 b는 val_v2 oas_code 46건(gitea 28 + 합성 18)으로 정한 값이며 test 수치는 1회 적용 결과다. test 곡선은 참고용이고 b 선택에 쓰지 않았다. b는 어댑터(seed)별로 선택했다.\n'
    if not a.no_guard: assert_data_v1('end'); assert_data_v2('end'); t += f'\n해시 가드(시작·종료): data-v1 {", ".join(v for v in g1.values())} / data-v2 {", ".join(v for v in g2.values())}.\n'
    out_md.write_text(t, encoding='utf-8')
    json.dump({s: dict(b_selected=r['b_selected'], selection_note=r['selection_note'], val_curve_oas_code=r['val_curve']['oas_code'], val_curve_oas=r['val_curve']['oas'], test={f'{k[0]}_{k[1]}': v for k, v in r['test'].items() if k[1] != 'curve'}, test_curve={k[0]: [(b, dict(macro_f1=v['main']['macro_f1'], manual_ratio=v['main']['manual_ratio'], concrete=v['main']['concrete'], public_misjudge=v['public_misjudge_new']['count'])) for b, v in v2] for k, v2 in r['test'].items() if k[1] == 'curve'}) for s, r in results.items()}, open(C / 'calib_results.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(out_md); print({s: r['b_selected'] for s, r in results.items()})

def D_PRED(seed, cond):
    p = ROOT / f'reports/eval/lora_v2/lora_v2_seed{seed}/eval/predictions_{cond}_lora_v2_s{seed}_final.jsonl'
    return rd(p) if p.exists() else None

if __name__ == '__main__': main()
