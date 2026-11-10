"""S5 LoRA v6a (prompt v3.1 + rationale-first output + label-token-probability confidence) — stage-3 analysis and report.
Reads only existing prediction files (no inference): reports/eval/lora_v6a/lora_v6a_s{42,43,44}/eval/ (v6a) and reports/eval/lora_v5/lora_v5_s*/eval/ (v5 baseline),
plus the scorer outputs scores_test_v5.json / scores_test_v30.json produced by scripts/eval_test_v5.py and scripts/eval_v30.py (eval-def v2).
Writes reports/eval/lora_v6a/analysis.json and report.md. Pre-registered adoption criteria (AGENTS.md 작업 S5, 3-seed mean):
 (1) test_v5 oas_code macro-F1 >= v5 + 0.016, (2) test_v30 207 concrete precision drop <= 0.025, (3) test_v30 207 public misjudge (/35) mean <= 2.0."""
from __future__ import annotations
import hashlib, json, re, statistics as st, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from eval_v30 import segments as v30_segments
R5 = ROOT / 'reports/eval/lora_v5'; R6 = ROOT / 'reports/eval/lora_v6a'
TEST5 = ROOT / 'datasets/blade/processed/test_v5.jsonl'; MAN5 = ROOT / 'datasets/blade/processed/data_v5/test_v5_manifest.json'
MAN5_SHA = '57fd384f46e89e905209e627a7ff7fb9f312e22a7bed222639e91a80bd05fccd'
SEEDS = [42, 43, 44]
L = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']; MANUAL = 'manual_review_required'
SHORT = {'public': 'public', 'role_required': 'role', 'membership_required': 'member', 'tenant_match': 'tenant', 'owner_match': 'owner', 'owner_or_admin': 'own+adm', 'manual_review_required': 'manual', 'output_error': 'ERR'}
CRIT = dict(macro_f1_gain=0.016, precision_drop=0.025, public_misjudge_max=2.0)
HAN = re.compile(r'[\u4e00-\u9fff]')
# S1-3 disagreement list (reports/eval/human_agreement_v5/report_ai_proxy.md §6; truth, type, 규약 항목 from s1_4_report.md)
S13 = [('v5t-ghost-924636cc9d', 'G3-b/G6-c 경계(모든 역할 보유 권한)'), ('v5t-rocketchat-0398a2f985', 'canAccessRoom(G6-a)'), ('v5t-rocketchat-0780c8e386', 'G3-a 그룹 안 역할'),
       ('v5t-rocketchat-09c0e4be92', 'G3-a 그룹 안 역할'), ('v5t-rocketchat-0d896bf7fc', 'G3-a 그룹 안 역할'), ('v5t-rocketchat-23a530da4b', 'G4-c/G6-b 경계(설정 의존)'),
       ('v5t-rocketchat-7508165c03', 'G3-a 그룹 안 역할'), ('v5t-rocketchat-d83dae7c4e', 'canAccessRoom(G6-a)'), ('v5t-rocketchat-ec189eb0b4', 'G3-a 그룹 안 역할'),
       ('v5t-rocketchat-f7c14cc85e', 'canAccessRoom(G6-a)'), ('v5t-umami-bf7e66056f', 'G6-a 복합 OR(Umami canView)'), ('v5t-umami-dd7523bace', 'G6-a 복합 OR(Umami canDelete)')]
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
lab = lambda r: r['prediction']['label'] if r.get('prediction') else 'output_error'


def ms(xs, nd=3, pct=False):
    if pct: xs = [x * 100 for x in xs]
    if len(xs) == 1: return f'{xs[0]:.{1 if pct else nd}f}' + ('%' if pct else '')
    return f'{st.mean(xs):.{1 if pct else nd}f} ± {st.stdev(xs):.{1 if pct else nd}f}' + ('%' if pct else '')


def pred_path(ver, seed, kind, cond):
    base = (R5 if ver == 'v5' else R6) / f'lora_{ver}_s{seed}' / 'eval'
    prefix = 'v5test_predictions_' if kind == 'test_v5' else 'predictions_'
    return base / f'{prefix}{cond}_lora_{ver}_s{seed}_final.jsonl'


def main():
    assert sha(MAN5) == MAN5_SHA; man = json.load(open(MAN5, encoding='utf-8')); assert sha(TEST5) == man['sha256']['datasets/blade/processed/test_v5.jsonl']
    t5 = {r['id']: r for r in rd(TEST5)}; meta30, seg30 = v30_segments(); syn30 = set(seg30['synthetic'])
    ids207 = [i for i in seg30['all'] if i not in syn30 and meta30[i]['has_code']]; assert len(ids207) == 207
    S5 = json.load(open(R6 / 'scores_test_v5.json', encoding='utf-8')); S30 = json.load(open(R6 / 'scores_test_v30.json', encoding='utf-8'))
    P = {(v, s, k, c): {r['id']: r for r in rd(pred_path(v, s, k, c))} for v in ('v5', 'v6a') for s in SEEDS for k, c in (('test_v5', 'oas_code'), ('test_v5', 'oas'), ('test_v30', 'oas_code'), ('test_v30', 'oas'))}
    A = dict(definition=__doc__, criteria=CRIT)

    # ---- 1. headline tables -------------------------------------------------------------------------------------
    def s5(ver, cond): return [r for r in S5 if r['condition'] == cond and r['model'].startswith(f'lora_{ver}_s')]
    def s30(ver, cond): return [r for r in S30 if r['eval_def'] == 'v2' and r['condition'] == cond and r['model'].startswith(f'lora_{ver}_s')]
    def pub35(ver, seed):
        pr = P[(ver, seed, 'test_v30', 'oas_code')]
        den = [i for i in ids207 if meta30[i]['security_state'] == 'declared' and meta30[i]['label'] != 'public']; assert len(den) == 35
        return [i for i in den if lab(pr[i]) == 'public']
    head = {}
    for ver in ('v5', 'v6a'):
        a = s5(ver, 'oas_code'); b = s30(ver, 'oas_code'); pub = {s: pub35(ver, s) for s in SEEDS}
        head[ver] = dict(test_v5=dict(macro_f1=[r['macro_f1'] for r in a], accuracy=[r['accuracy'] for r in a], manual=[r['manual_ratio'] for r in a], errors=[r['output_errors'] for r in a],
                                      per_label={l: [r['per_label'][l]['f1'] for r in a] for l in L}, per_label_pr={l: [(r['per_label'][l]['precision'], r['per_label'][l]['recall']) for r in a] for l in L},
                                      per_project={p: [r['per_project'][p]['accuracy'] for r in a] for p in ('rocketchat', 'ghost', 'umami')}, manual_count=[int(round(r['manual_ratio'] * 283)) for r in a]),
                         test_v5_oas=dict(macro_f1=[r['macro_f1'] for r in s5(ver, 'oas')], accuracy=[r['accuracy'] for r in s5(ver, 'oas')], manual=[r['manual_ratio'] for r in s5(ver, 'oas')], errors=[r['output_errors'] for r in s5(ver, 'oas')]),
                         test_v30_207=dict(macro_f1=[r['main_excl_synthetic']['macro_f1'] for r in b], macro_f1_265=[r['main']['macro_f1'] for r in b], accuracy=[r['main_excl_synthetic']['accuracy'] for r in b],
                                           precision=[r['main_excl_synthetic']['concrete']['precision'] for r in b], recall=[r['main_excl_synthetic']['concrete']['recall'] for r in b], answer_rate=[r['main_excl_synthetic']['concrete']['answer_rate'] for r in b],
                                           manual=[r['main_excl_synthetic']['manual_ratio'] for r in b], errors=[r['main_excl_synthetic']['output_errors'] for r in b], per_label={l: [r['main_excl_synthetic']['per_label'][l]['f1'] for r in b] for l in L},
                                           public_misjudge_35=[len(pub[s]) for s in SEEDS], public_ids={str(s): pub[s] for s in SEEDS}),
                         test_v30_oas=dict(macro_f1_160=[r['main']['macro_f1'] for r in s30(ver, 'oas')], macro_f1_102=[r['main_excl_synthetic']['macro_f1'] for r in s30(ver, 'oas')], precision=[r['main']['concrete']['precision'] for r in s30(ver, 'oas')],
                                           manual=[r['main']['manual_ratio'] for r in s30(ver, 'oas')], errors=[r['main']['output_errors'] for r in s30(ver, 'oas')], public_misjudge=[r['public_misjudge_new']['count'] for r in s30(ver, 'oas')]))
    A['headline'] = head
    c1 = st.mean(head['v6a']['test_v5']['macro_f1']) - st.mean(head['v5']['test_v5']['macro_f1']); c2 = st.mean(head['v5']['test_v30_207']['precision']) - st.mean(head['v6a']['test_v30_207']['precision']); c3 = st.mean(head['v6a']['test_v30_207']['public_misjudge_35'])
    A['verdict'] = dict(c1_macro_f1_delta=round(c1, 4), c1_pass=c1 >= CRIT['macro_f1_gain'], c2_precision_drop=round(c2, 4), c2_pass=c2 <= CRIT['precision_drop'], c3_public_misjudge_mean=round(c3, 2), c3_pass=c3 <= CRIT['public_misjudge_max'])
    A['verdict']['adopt'] = all(A['verdict'][k] for k in ('c1_pass', 'c2_pass', 'c3_pass'))

    # ---- 2. prediction transitions v5 -> v6a (test_v5 oas_code, same seed) ------------------------------------------
    trans = {}; manual_by_truth = {}; disagree_pairs = Counter(); n_disagree = 0; n_all_three = 0
    for s in SEEDS:
        a = P[('v5', s, 'test_v5', 'oas_code')]; b = P[('v6a', s, 'test_v5', 'oas_code')]
        pairs = Counter((lab(a[i]), lab(b[i])) for i in t5 if lab(a[i]) != lab(b[i])); trans[str(s)] = {f'{x}->{y}': n for (x, y), n in pairs.most_common()}
        # where did new manual predictions come from (truth label of rows that v5 answered concretely but v6a holds)
        manual_by_truth[str(s)] = dict(Counter(t5[i]['label'] for i in t5 if lab(a[i]) != MANUAL and lab(b[i]) == MANUAL))
        # fixed / newly wrong
        trans[str(s) + '_fixed'] = sum(lab(a[i]) != t5[i]['label'] and lab(b[i]) == t5[i]['label'] for i in t5); trans[str(s) + '_newly_wrong'] = sum(lab(a[i]) == t5[i]['label'] and lab(b[i]) != t5[i]['label'] for i in t5)
    for i in t5:
        ls = [lab(P[('v6a', s, 'test_v5', 'oas_code')][i]) for s in SEEDS]
        if len(set(ls)) > 1:
            n_disagree += 1; n_all_three += len(set(ls)) == 3
            for x, y in {tuple(sorted(p)) for p in [(ls[0], ls[1]), (ls[0], ls[2]), (ls[1], ls[2])] if p[0] != p[1]}: disagree_pairs[f'{x}|{y}'] += 1
    v5_dis = sum(len({lab(P[('v5', s, 'test_v5', 'oas_code')][i]) for s in SEEDS}) > 1 for i in t5)
    A['transitions'] = dict(v5_to_v6a=trans, new_manual_by_truth=manual_by_truth, v6a_seed_disagree_records=n_disagree, v6a_all_three_differ=n_all_three, v5_seed_disagree_records=v5_dis, v6a_disagree_pairs=dict(disagree_pairs.most_common()))
    # per-truth-label manual rate (v6a seeds) and confusion of truth membership/owner_or_admin
    A['v6a_confusion_mean'] = {a_: {b_: round(st.mean([r['confusion'][a_][b_] for r in s5('v6a', 'oas_code')]), 1) for b_ in L + ['output_error']} for a_ in L}
    A['v5_confusion_mean'] = {a_: {b_: round(st.mean([r['confusion'][a_][b_] for r in s5('v5', 'oas_code')]), 1) for b_ in L + ['output_error']} for a_ in L}

    # ---- 3. S1-3 disagreement records ---------------------------------------------------------------------------
    A['s13'] = [dict(id=i, type=ty, project=t5[i]['meta']['project'], method=t5[i]['method'], path=t5[i]['path'], truth=t5[i]['label'], v5=[lab(P[('v5', s, 'test_v5', 'oas_code')][i]) for s in SEEDS], v6a=[lab(P[('v6a', s, 'test_v5', 'oas_code')][i]) for s in SEEDS]) for i, ty in S13]
    by_type = defaultdict(lambda: dict(n=0, v5_correct=0, v6a_correct=0))
    for r in A['s13']:
        d = by_type[r['type']]; d['n'] += 1; d['v5_correct'] += sum(x == r['truth'] for x in r['v5']); d['v6a_correct'] += sum(x == r['truth'] for x in r['v6a'])
    A['s13_by_type'] = dict(by_type)

    # ---- 4. label-token probability curve (test_v5 oas_code) ------------------------------------------------------
    TH = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99]; curve = {}; dist = {}
    for s in SEEDS:
        rows = list(P[('v6a', s, 'test_v5', 'oas_code')].values()); pn = {r['id']: (r['label_prob'] or {}).get('p_norm') for r in rows}
        vals = [v for v in pn.values() if v is not None]; qs = st.quantiles(vals, n=100) if len(vals) > 1 else vals
        dist[str(s)] = dict(n=len(vals), min=round(min(vals), 6), p1=round(qs[0], 6), p5=round(qs[4], 6), p50=round(qs[49], 6), mean=round(st.mean(vals), 6), below_0_99=sum(v < 0.99 for v in vals), below_0_999=sum(v < 0.999 for v in vals),
                            gen_conf=dict(Counter(str((r.get('prediction') or {}).get('confidence', 'ERR')) for r in rows)), p_first_min=round(min(r['label_prob']['p_first'] for r in rows if r.get('label_prob')), 6),
                            p_seq_min=round(min(r['label_prob']['p_seq'] for r in rows if r.get('label_prob')), 6), tokenization_match_all=all(r['label_prob']['tokenization_match'] for r in rows if r.get('label_prob')),
                            generated_eq_parsed=all(r['label_prob']['generated_label'] == r['prediction']['label'] for r in rows if r.get('label_prob') and r.get('prediction')))
        cv = []
        for t in TH:
            pairs = []
            for r in rows:
                p = lab(r); keep = p != MANUAL and p != 'output_error' and pn[r['id']] is not None and pn[r['id']] >= t
                pairs.append((t5[r['id']]['label'], p if keep else MANUAL, keep, p))
            kept = [x for x in pairs if x[2]]; per = {}
            for l in L:
                tp = sum(a == l and b == l for a, b, *_ in pairs); fp = sum(a != l and b == l for a, b, *_ in pairs); fn = sum(a == l and b != l for a, b, *_ in pairs)
                Pp = tp / (tp + fp) if tp + fp else 0.; Rr = tp / (tp + fn) if tp + fn else 0.; per[l] = 2 * Pp * Rr / (Pp + Rr) if Pp + Rr else 0.
            sup = [l for l in L if any(a == l for a, *_ in pairs)]
            cv.append(dict(t=t, kept=len(kept), kept_acc=round(sum(a == b for a, b, *_ in kept) / len(kept), 4) if kept else None, abstain=round(1 - len(kept) / len(pairs), 4), acc=round(sum(a == b for a, b, *_ in pairs) / len(pairs), 4), macro_f1=round(sum(per[l] for l in sup) / len(sup), 4)))
        curve[str(s)] = cv
    A['pnorm'] = dict(thresholds=TH, curve=curve, dist=dist)
    # where in the output does the label first appear? (rationale names the label before the "label" key)
    first_in_rationale = {str(s): sum(1 for r in P[('v6a', s, 'test_v5', 'oas_code')].values() if r.get('prediction') and r['prediction']['label'] in (r['prediction'].get('rationale') or '')) for s in SEEDS}
    A['pnorm']['label_named_in_rationale'] = first_in_rationale

    # ---- 5. output errors, length, time, environment ---------------------------------------------------------------
    errs = {}; lens = {}; times = {}
    for ver in ('v5', 'v6a'):
        for s in SEEDS:
            for k, c in (('test_v5', 'oas_code'), ('test_v5', 'oas'), ('test_v30', 'oas_code'), ('test_v30', 'oas')):
                rows = list(P[(ver, s, k, c)].values()); key = f'{ver}_s{s}_{k}_{c}'
                e = [r for r in rows if not r.get('prediction')]
                errs[key] = dict(n=len(e), han=sum(bool(HAN.search(r['raw'] or '')) for r in e), hit_max=sum((r.get('output_tokens') or 0) >= 512 for r in e) if ver == 'v6a' else None,
                                 examples=[dict(id=r['id'], truth=r['label'], output_tokens=r.get('output_tokens'), raw=(lambda s_, m_: s_[max(0, (m_.start() if m_ else 0) - 40):(m_.start() if m_ else 0) + 60])(r['raw'] or '', HAN.search(r['raw'] or ''))) for r in e[:3]])
                lens[key] = dict(raw_chars_mean=round(st.mean(len(r['raw'] or '') for r in rows), 1), raw_chars_max=max(len(r['raw'] or '') for r in rows),
                                 output_tokens_mean=round(st.mean(r['output_tokens'] for r in rows), 1) if ver == 'v6a' else None, output_tokens_max=max(r['output_tokens'] for r in rows) if ver == 'v6a' else None,
                                 prompt_tokens_mean=round(st.mean(r['prompt_tokens'] for r in rows), 1) if ver == 'v6a' else None, prompt_tokens_max=max(r['prompt_tokens'] for r in rows) if ver == 'v6a' else None)
                times[key] = dict(inference_ms_mean=round(st.mean(r['inference_ms'] for r in rows), 1), inference_ms_sum_s=round(sum(r['inference_ms'] for r in rows) / 1000, 1))
                if ver == 'v6a':
                    tj = json.load(open(str(pred_path(ver, s, k, c)) + '.timing.json', encoding='utf-8')); times[key].update(wall_s=tj['inference_wall_s'], mean_ms_per_row=tj['mean_ms_per_row'], hit_max_new_tokens=tj['hit_max_new_tokens'], truncated_prompts=tj['truncated_prompts'])
    A['errors'] = errs; A['lengths'] = lens; A['times'] = times
    env = {str(s): json.load(open(R6 / f'lora_v6a_s{s}/env.json', encoding='utf-8')) for s in SEEDS}; env5 = json.load(open(R5 / 'lora_v5_s42/env.json', encoding='utf-8'))
    tr = {}; tr5 = {}
    for s in SEEDS:
        j = json.load(open(R6 / f'lora_v6a_s{s}/logs/train_result.json', encoding='utf-8')); tr[str(s)] = dict(steps=j['steps'], minutes=j['minutes'], train_loss=round(j['train_loss'], 4), val_oas_final=round(j['eval_loss_by_condition']['oas'][-1][1], 4), val_oas_code_final=round(j['eval_loss_by_condition']['oas_code'][-1][1], 4), val_oas_min=round(min(v for _, v in j['eval_loss_by_condition']['oas']), 4), val_oas_code_min=round(min(v for _, v in j['eval_loss_by_condition']['oas_code']), 4))
        j = json.load(open(R5 / f'lora_v5_s{s}/logs/train_result.json', encoding='utf-8')); tr5[str(s)] = dict(steps=j['steps'], minutes=j['minutes'], train_loss=round(j['train_loss'], 4), val_oas_final=round(j['eval_loss_by_condition']['oas'][-1][1], 4), val_oas_code_final=round(j['eval_loss_by_condition']['oas_code'][-1][1], 4))
        log = (R6 / f'lora_v6a_s{s}/logs/run.log').read_text(encoding='utf-8', errors='replace'); m = re.search(r'loss mask check \(row 0\): (\d+)/(\d+) tokens masked \(-100\), (\d+) assistant tokens in loss', log); tr[str(s)]['mask_row0'] = m.group(0) if m else None
        tr[str(s)]['padding_free'] = 'Padding-free' in log
    assert len({tr[str(s)]['mask_row0'] for s in SEEDS}) == 1 and tr['42']['mask_row0'], tr
    A['env'] = dict(v6a=env, v5_s42=env5); A['train'] = dict(v6a=tr, v5=tr5)
    A['config_v6a'] = json.load(open(R6 / 'lora_v6a_s42/config.json', encoding='utf-8'))
    A['files'] = dict(zip_sha256=sha(Path('<USERPROFILE>/Downloads/BLADE_lora_v6a_export.zip')) if Path('<USERPROFILE>/Downloads/BLADE_lora_v6a_export.zip').exists() else None, sums=(R6 / 'SHA256SUMS_blade_v6a').read_text(encoding='utf-8').strip().splitlines())
    (R6 / 'analysis.json').write_text(json.dumps(A, ensure_ascii=False, indent=1), encoding='utf-8', newline='\n')
    write_report(A, t5)


def write_report(A, t5):
    H = A['headline']; V = A['verdict']; v5, v6 = H['v5'], H['v6a']
    o = []; w = o.append
    w('# S5 LoRA v6a 보고 — 프롬프트 v3.1 + 근거 먼저 출력 + label 토큰 확률 confidence (2026-11-04, 3 seed, 커밋 없음)\n')
    w('사전 기록 AGENTS.md "작업 S5". 데이터 data-v5 그대로(label·rationale·user 불변, assistant 키 순서만 변경), 프롬프트 policy_label_v3.1.md(3,798 토큰), max_seq_len 6144(유일한 하이퍼파라미터 변경), max_new_tokens 512, 기본 디코딩(greedy). 판정셋 test_v5 283(dev, oas_code) + 회귀 test_v30 oas_code 합성 제외 207. v5 수치는 reports/eval/lora_v5의 기존 예측 파일을 같은 채점기로 재채점한 값(재추론 없음). test_v6은 추론하지 않았다. 주지표·발표 수치(v5)는 바꾸지 않는다.\n')
    w('## 1. 판정 — 사전 기준 3개 모두 미달, **불채택**\n')
    w('| 기준(3 seed 평균) | v5 | v6a | 차이 | 기준 | 충족 |\n|---|---:|---:|---:|---|---|')
    w(f"| (1) test_v5 oas_code macro-F1 상승 ≥ 0.016 | {ms(v5['test_v5']['macro_f1'])} | {ms(v6['test_v5']['macro_f1'])} | {V['c1_macro_f1_delta']:+.3f} | ≥ +0.016 | {'예' if V['c1_pass'] else '**아니오**'} |")
    w(f"| (2) test_v30 207 구체 정밀도 하락 ≤ 0.025 | {ms(v5['test_v30_207']['precision'])} | {ms(v6['test_v30_207']['precision'])} | {-V['c2_precision_drop']:+.3f} | 하락 ≤ 0.025 | {'예' if V['c2_pass'] else '**아니오**'} |")
    w(f"| (3) test_v30 207 public 오판(/35) 평균 ≤ 2.0 | {' / '.join(map(str, v5['test_v30_207']['public_misjudge_35']))} (평균 {st.mean(v5['test_v30_207']['public_misjudge_35']):.2f}) | {' / '.join(map(str, v6['test_v30_207']['public_misjudge_35']))} (평균 {V['c3_public_misjudge_mean']:.2f}) | {V['c3_public_misjudge_mean'] - st.mean(v5['test_v30_207']['public_misjudge_35']):+.2f} | ≤ 2.0 | {'예' if V['c3_pass'] else '**아니오**'} |")
    w('\n세 기준 모두 미달이라 v6a는 채택하지 않는다. v5(프롬프트 v3.0.1, 발표 주 수치)는 그대로다. test_v5에서는 보류(manual)가 늘고 membership_required·owner_or_admin F1이 크게 떨어졌으며, test_v30에서는 반대로 보류가 6.6%까지 줄면서 틀린 구체 답(특히 public)이 늘었다(4·5절). seed 간 예측이 갈린 레코드도 v5 69건 → v6a 143건으로 늘어 불안정하다.\n')
    w('## 2. 실행 환경·학습\n')
    e = A['env']['v6a']['42']; e5 = A['env']['v5_s42']
    w(f"- Pod: RunPod y3fn8g1psetyh8, {e['gpu']} {e['vram_gb']} GB, torch {e['torch']}(CUDA {e['cuda']}), transformers {e['transformers']}, trl {e['trl']}, peft {e['peft']}, unsloth {e['unsloth']}, python {e['python']}. 2026-11-03 23:21 UTC 시작 → 11-04 01:33 UTC 종료(2시간 12분, 설치·preflight 포함), 번들 blade_v6a_20261104.tgz(`91c0c204…`), 해시 게이트(data_v6a_hashes.json `c079b9f5…`, test_v5_manifest `57fd384f…`) 통과, Pod 자동 정지.")
    w(f"- v5 환경(비교): {e5.get('gpu')}, torch {e5.get('torch')}, transformers {e5.get('transformers')}, unsloth {e5.get('unsloth')}. 이번 Pod의 unsloth는 'Padding-free batching'을 자동으로 켰다(로그 `Padding-free auto-enabled`; v5 로그에는 없음). 손실 값은 같은 정의이나 배치 구성이 달라 v5와 완전히 같은 실행 환경은 아니다.")
    w('- 첫 시도는 RTX PRO 4000 Blackwell Pod(02c4twegbgj8g3)에서 시작했으나 학습 전(setup 단계)에 중단하고 H100으로 옮겼다. 결과는 H100 1회 실행분이다.')
    w(f"- 손실 마스킹(completion-only) 확인: 학습 시작 시 0번 행 `{A['train']['v6a']['42']['mask_row0']}` (3 seed 동일). v5와 같은 train_on_responses_only 호출.")
    w('\n| run | steps | 학습 분 | train_loss | val oas loss(final / 최저) | val oas_code loss(final / 최저) | v5 같은 seed train_loss / val final(oas, oas_code) / 분 |\n|---|---:|---:|---:|---|---|---|')
    for s in map(str, SEEDS):
        t = A['train']['v6a'][s]; t5_ = A['train']['v5'][s]
        w(f"| lora_v6a_s{s} | {t['steps']} | {t['minutes']} | {t['train_loss']} | {t['val_oas_final']} / {t['val_oas_min']} | {t['val_oas_code_final']} / {t['val_oas_code_min']} | {t5_['train_loss']} / {t5_['val_oas_final']}, {t5_['val_oas_code_final']} / {t5_['minutes']} |")
    w('\nval은 학습 정상 여부 확인용이며(발산 없음, 세 seed 모두 480 step 완주) 체크포인트 선택에 쓰지 않았다(final 고정). val loss는 v5와 비슷하거나 약간 높다(v3.1 프롬프트가 길어 같은 데이터의 손실 비교는 참고치).\n')
    w('## 3. test_v5 283 (dev) — oas_code\n')
    w('| 모델 | macro-F1 | 정확도 | manual 비율 | manual 건수(seed별) | 출력 오류(합) |\n|---|---:|---:|---:|---|---:|')
    for ver, nm in (('v5', 'lora_v5'), ('v6a', 'lora_v6a')):
        h = H[ver]['test_v5']; w(f"| {nm} | {ms(h['macro_f1'])} | {ms(h['accuracy'])} | {ms(h['manual'], pct=True)} | {' / '.join(map(str, h['manual_count']))} | {sum(h['errors'])} |")
    w('\n### label별 F1 (support)\n')
    sup = {l: [r for r in json.load(open(R6 / 'scores_test_v5.json', encoding='utf-8')) if r['condition'] == 'oas_code'][0]['per_label'][l]['support'] for l in L}
    w('| 모델 | ' + ' | '.join(f'{l} ({sup[l]})' for l in L) + ' |\n|---|' + '---:|' * len(L))
    for ver, nm in (('v5', 'lora_v5'), ('v6a', 'lora_v6a')): w(f'| {nm} | ' + ' | '.join(ms(H[ver]['test_v5']['per_label'][l]) for l in L) + ' |')
    w('\n### 판정 label 정밀도 / 재현율 (seed별)\n\n| run | owner_or_admin P / R / F1 | membership_required P / R / F1 | role_required P / R / F1 | public P / R / F1 |\n|---|---|---|---|---|')
    for ver in ('v5', 'v6a'):
        for k, s in enumerate(SEEDS):
            cells = []
            for l in ('owner_or_admin', 'membership_required', 'role_required', 'public'):
                p, r = H[ver]['test_v5']['per_label_pr'][l][k]; f = H[ver]['test_v5']['per_label'][l][k]; cells.append(f'{p:.3f} / {r:.3f} / {f:.3f}')
            w(f'| lora_{ver}_s{s} | ' + ' | '.join(cells) + ' |')
    w('\n### 프로젝트별 정확도\n\n| 모델 | rocketchat (157) | ghost (69) | umami (57) |\n|---|---:|---:|---:|')
    for ver, nm in (('v5', 'lora_v5'), ('v6a', 'lora_v6a')): w(f"| {nm} | " + ' | '.join(ms(H[ver]['test_v5']['per_project'][p]) for p in ('rocketchat', 'ghost', 'umami')) + ' |')
    w('\n### 혼동표 (정답 행 → 예측 열, 3 seed 평균 건수)\n')
    w('| 정답 \\ 예측 | ' + ' | '.join(SHORT[l] for l in L + ['output_error']) + ' |\n|---|' + '---:|' * 8)
    for a in L:
        if not sup[a]: continue
        w(f'| **{SHORT[a]}** (v5) | ' + ' | '.join(str(A['v5_confusion_mean'][a][b]) for b in L + ['output_error']) + ' |')
        w(f'| {SHORT[a]} (v6a) | ' + ' | '.join(str(A['v6a_confusion_mean'][a][b]) for b in L + ['output_error']) + ' |')
    w('\n### oas(명세만) 보조\n\n| 모델 | macro-F1 | 정확도 | manual 비율 | 출력 오류(합) |\n|---|---:|---:|---:|---:|')
    for ver, nm in (('v5', 'lora_v5'), ('v6a', 'lora_v6a')):
        h = H[ver]['test_v5_oas']; w(f"| {nm} | {ms(h['macro_f1'])} | {ms(h['accuracy'])} | {ms(h['manual'], pct=True)} | {sum(h['errors'])} |")
    w('\n원자료 scores_test_v5.json, eval_test_v5.md(scripts/eval_test_v5.py, manifest 해시 검증).\n')
    w('## 4. test_v30 회귀 — oas_code 합성 제외 207 (주지표 조건)\n')
    w('| 모델 | macro-F1(207) | macro-F1(265) | 정확도 | 구체 정밀도 | 구체 재현율 | 구체 응답률 | manual 비율 | public 오판(신, /35, seed별) | 출력 오류(seed별) |\n|---|---:|---:|---:|---:|---:|---:|---:|---|---|')
    for ver, nm in (('v5', 'lora_v5'), ('v6a', 'lora_v6a')):
        h = H[ver]['test_v30_207']; w(f"| {nm} | {ms(h['macro_f1'])} | {ms(h['macro_f1_265'])} | {ms(h['accuracy'])} | {ms(h['precision'])} | {ms(h['recall'])} | {ms(h['answer_rate'])} | {ms(h['manual'], pct=True)} | {' / '.join(map(str, h['public_misjudge_35']))} | {' / '.join(map(str, h['errors']))} |")
    w('\n| 모델 | ' + ' | '.join(f'{l}' for l in L if l not in ('membership_required', 'tenant_match')) + ' |\n|---|' + '---:|' * 5)
    for ver, nm in (('v5', 'lora_v5'), ('v6a', 'lora_v6a')): w(f'| {nm} | ' + ' | '.join(ms(H[ver]['test_v30_207']['per_label'][l]) for l in L if l not in ('membership_required', 'tenant_match')) + ' |')
    w('\npublic 오판 id(v6a): ' + '; '.join(f"s{s}: {', '.join(v6['test_v30_207']['public_ids'][str(s)])}" for s in SEEDS) + f". v5: {'; '.join(f'''s{s}: {', '.join(v5['test_v30_207']['public_ids'][str(s)])}''' for s in SEEDS)}.")
    w('\n보류가 28% → 7%로 줄며 응답률은 올랐지만 응답의 정밀도가 0.80 → 0.61로 떨어졌다. v3.1의 public 정의(G7: "조건 없는 익명 허용만 public")와 보류 절 변경이 취약 API(명세에 security 선언, 코드에 검사 없음) 입력에서 public·구체 답을 늘린 것으로 보인다. v3.1 안전 가드(public 오판 ≤ 2.0)가 바로 이 경우를 막기 위한 것이었고 미달했다.\n')
    w('### oas(명세만) 160\n\n| 모델 | macro-F1(160) | 합성 제외 102 | 구체 정밀도 | manual 비율 | public 오판(신) | 출력 오류 |\n|---|---:|---:|---:|---:|---|---|')
    for ver, nm in (('v5', 'lora_v5'), ('v6a', 'lora_v6a')):
        h = H[ver]['test_v30_oas']; w(f"| {nm} | {ms(h['macro_f1_160'])} | {ms(h['macro_f1_102'])} | {ms(h['precision'])} | {ms(h['manual'], pct=True)} | {' / '.join(map(str, h['public_misjudge']))} | {' / '.join(map(str, h['errors']))} |")
    w('\n원자료 scores_test_v30.json, eval_v30.md(scripts/eval_v30.py --eval-def both). reports/eval_v30_redef/segments.json은 재생성됐으나 내용 동일(git diff 없음).\n')
    w('## 5. 예측 변화 v5 → v6a (test_v5 oas_code, 같은 seed)\n')
    T = A['transitions']
    w('| seed | 고쳐짐(v5 오답→v6a 정답) | 새로 틀림(v5 정답→v6a 오답) | 바뀐 전이 상위 |\n|---|---:|---:|---|')
    for s in map(str, SEEDS):
        top = ', '.join(f"{SHORT[k.split('->')[0]]}→{SHORT[k.split('->')[1]]} {n}" for k, n in list(T['v5_to_v6a'][s].items())[:6]); w(f"| s{s} | {T['v5_to_v6a'][s + '_fixed']} | {T['v5_to_v6a'][s + '_newly_wrong']} | {top} |")
    w('\n새로 manual이 된 건(v5 구체 → v6a manual)의 정답 label:\n\n| seed | ' + ' | '.join(SHORT[l] for l in L) + ' |\n|---|' + '---:|' * 7)
    for s in map(str, SEEDS): w(f'| s{s} | ' + ' | '.join(str(T['new_manual_by_truth'][s].get(l, 0)) for l in L) + ' |')
    w(f"\nseed 간 예측이 갈린 레코드: v6a {T['v6a_seed_disagree_records']}/283(세 seed 모두 다름 {T['v6a_all_three_differ']}), v5 {T['v5_seed_disagree_records']}/283. v6a에서 갈린 label 쌍: " + ', '.join(f"{SHORT[k.split('|')[0]]}|{SHORT[k.split('|')[1]]} {n}" for k, n in list(T['v6a_disagree_pairs'].items())[:8]) + '.')
    w('\nmanual 비율이 seed에 따라 24%~41%로 크게 흔들리고(s44 117건), 구체 답을 내던 membership_required·role_required 건이 manual로 후퇴한 것이 macro-F1 하락의 주된 경로다. 이는 v3.1 보류 절(독립 조건 AND 결합·설정 의존 → 보류)의 문구가 학습 데이터(data-v5의 rationale은 v3.0.1 기준으로 쓰인 것)와 어긋나, 모델이 프롬프트의 보류 규칙을 넓게 적용한 결과로 보인다. 학습 target(rationale·label)은 v3.1 정의로 다시 쓰지 않았으므로 프롬프트와 target의 기준이 불일치한 채 학습됐다.\n')
    w('## 6. S1-3 불일치 12건에서의 예측 (v5 → v6a, seed 42/43/44)\n')
    w('| id | 유형 | method path | 정답 | v5 s42/43/44 | v6a s42/43/44 |\n|---|---|---|---|---|---|')
    for r in A['s13']: w(f"| {r['id']} | {r['type']} | {r['method']} {r['path']} | {SHORT[r['truth']]} | {' / '.join(SHORT[x] for x in r['v5'])} | {' / '.join(SHORT[x] for x in r['v6a'])} |")
    w('\n| 유형 | 건수 | v5 정답(3 seed 합 / 가능) | v6a 정답(3 seed 합 / 가능) |\n|---|---:|---:|---:|')
    for ty, d in A['s13_by_type'].items(): w(f"| {ty} | {d['n']} | {d['v5_correct']} / {d['n'] * 3} | {d['v6a_correct']} / {d['n'] * 3} |")
    g3 = A['s13_by_type']['G3-a 그룹 안 역할']
    w(f"\nv3.1이 명문화한 G3-a(그룹 구성원 확인 뒤 그룹 안 역할 → role_required) 5건은 v5 {g3['v5_correct']}/15 → v6a {g3['v6a_correct']}/15로 조금 나아졌고(groups.rename이 member→role), G3-b 경계(GET posts, 모든 역할 보유 권한 → manual)도 0/3 → 2/3이다. 그러나 setType·resetRoomKey는 seed마다 갈리고(owner/role/manual), 설정 의존(resetAvatar)·Umami canDelete는 그대로 틀렸다. 12건 합계 v5 {sum(d['v5_correct'] for d in A['s13_by_type'].values())}/36 → v6a {sum(d['v6a_correct'] for d in A['s13_by_type'].values())}/36. 이 12건의 국소 개선은 전체 하락(3절)을 상쇄하지 못하며, 프롬프트 정의만 바꾸고 학습 target을 그대로 둔 상태에서는 규칙이 안정적으로 적용되지 않는다.\n")
    w('## 7. label 토큰 확률(p_norm) 정확도–보류율 곡선 (test_v5 oas_code)\n')
    D = A['pnorm']['dist']
    w('| seed | n | p_norm 최소 | 1% 분위 | 5% 분위 | 중앙값 | < 0.99 건수 | < 0.999 건수 | 생성 confidence 값 분포 | 토큰화 일치 | 생성 label = 파싱 label |\n|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|')
    for s in map(str, SEEDS):
        d = D[s]; w(f"| s{s} | {d['n']} | {d['min']} | {d['p1']} | {d['p5']} | {d['p50']} | {d['below_0_99']} | {d['below_0_999']} | {d['gen_conf']} | {d['tokenization_match_all']} | {d['generated_eq_parsed']} |")
    w('\n| t | ' + ' | '.join(f's{s} 유지 n / 유지 정확도 / 보류율 / 전체 정확도 / macro-F1' for s in SEEDS) + ' | 평균 보류율 | 평균 전체 정확도 | 평균 macro-F1 |\n|---|' + '---|' * 3 + '---:|---:|---:|')
    for k, t in enumerate(A['pnorm']['thresholds']):
        cells = [A['pnorm']['curve'][str(s)][k] for s in SEEDS]
        w(f"| {t:.2f} | " + ' | '.join(f"{c['kept']} / {c['kept_acc'] if c['kept_acc'] is not None else '-'} / {c['abstain']:.3f} / {c['acc']:.3f} / {c['macro_f1']:.3f}" for c in cells) + f" | {st.mean(c['abstain'] for c in cells):.3f} | {st.mean(c['acc'] for c in cells):.3f} | {st.mean(c['macro_f1'] for c in cells):.3f} |")
    w(f"\n- p_norm은 greedy 디코딩에서 label 키 다음 토큰의 7종 후보 정규화 확률이다. 세 seed 모두 거의 전 건이 1.0에 붙어 있어(0.99 미만 {', '.join(str(D[str(s)]['below_0_99']) for s in SEEDS)}건) 문턱 0.5~0.99 구간에서 곡선이 평탄하다. **생성 confidence(0.9 단일값)와 마찬가지로 label 토큰 확률도 보류 조절 수단이 되지 못했다.**")
    w(f"- 원인: 출력 순서를 근거 먼저로 바꾸면 rationale 문장이 label 이름을 먼저 적고(rationale 안에 label 문자열 포함 {', '.join(str(A['pnorm']['label_named_in_rationale'][str(s)]) for s in SEEDS)}/283) `\"label\"` 키의 토큰은 그 문장을 복사하는 결정적 토큰이 된다. 불확실성은 rationale 안에서 label 이름이 처음 나오는 위치의 토큰 확률에 있으며, 이번 추론은 그 위치의 scores를 저장하지 않았다. 대안은 (a) rationale에서 label 이름이 처음 등장하는 토큰의 확률을 저장, (b) label을 먼저 내는 순서에서 label 토큰 확률 측정, (c) 7종 label을 각각 강제한 teacher-forcing 로그확률 비교(추가 forward 7회).")
    w('\n## 8. 출력 오류·출력 길이·추론 시간\n')
    E, LN, TM = A['errors'], A['lengths'], A['times']
    w('| 셋·조건 | v5 출력 오류(s42/43/44) | v6a 출력 오류(s42/43/44) | v6a 오류 중 중국어 혼입 | v6a 오류 중 512 토큰 도달 | v6a 출력 토큰 평균/최대(s42) | 출력 문자 수 평균 v5 → v6a(s42) | v6a 프롬프트 토큰 평균/최대 |\n|---|---|---|---:|---:|---|---|---|')
    for k, c, nm in (('test_v5', 'oas_code', 'test_v5 oas_code'), ('test_v5', 'oas', 'test_v5 oas'), ('test_v30', 'oas_code', 'test_v30 oas_code(265)'), ('test_v30', 'oas', 'test_v30 oas(269)')):
        k6 = [f'v6a_s{s}_{k}_{c}' for s in SEEDS]; k5 = [f'v5_s{s}_{k}_{c}' for s in SEEDS]
        w(f"| {nm} | {' / '.join(str(E[x]['n']) for x in k5)} | {' / '.join(str(E[x]['n']) for x in k6)} | {sum(E[x]['han'] for x in k6)} | {sum(E[x]['hit_max'] for x in k6)} | {LN[k6[0]]['output_tokens_mean']} / {LN[k6[0]]['output_tokens_max']} | {LN[k5[0]]['raw_chars_mean']} → {LN[k6[0]]['raw_chars_mean']} | {LN[k6[0]]['prompt_tokens_mean']} / {LN[k6[0]]['prompt_tokens_max']} |")
    ex = [x for key in E for x in E[key]['examples'] if key.startswith('v6a') and 'test_v30' in key][:4]
    w('\nv6a 출력 오류는 test_v5 oas_code에서는 0건, test_v30(취약 API)에서 seed당 4~9건이며 대부분 rationale 중간에 중국어·영어가 섞여 들어가 JSON이 깨진 경우다(중국어 혼입 위치 전후 발췌: ' + '; '.join(f"{x['id']} {x['output_tokens']}토큰 `…{x['raw'].replace('|', '/').replace(chr(10), ' ')}…`" for x in ex) + '). v5(v3.0.1)도 test_v30에서 seed당 0~5건의 같은 유형 오류가 있었고 v6a에서 조금 늘었다.\n')
    w('| 셋·조건 | v5 행당 ms(A100, s42) | v6a 행당 ms(H100, s42/43/44) | v6a 벽시계 s(s42) | 프롬프트 절단 |\n|---|---:|---|---:|---:|')
    for k, c, nm in (('test_v5', 'oas_code', 'test_v5 oas_code'), ('test_v5', 'oas', 'test_v5 oas'), ('test_v30', 'oas_code', 'test_v30 oas_code'), ('test_v30', 'oas', 'test_v30 oas')):
        k6 = [f'v6a_s{s}_{k}_{c}' for s in SEEDS]; w(f"| {nm} | {TM[f'v5_s42_{k}_{c}']['inference_ms_mean']} | {' / '.join(str(TM[x]['mean_ms_per_row']) for x in k6)} | {TM[k6[0]]['wall_s']} | {sum(TM[x]['truncated_prompts'] for x in k6)} |")
    w('\n행당 ms는 배치 8 기준(배치 벽시계 / 8)이며 GPU가 다르므로(v5 A100, v6a H100) 직접 비교는 참고치다. 학습은 seed당 32.5분(v5 A100 56분).\n')
    w('## 9. 해석·한계·다음 단계\n')
    w('- **불채택.** v3.1 정의를 프롬프트에만 넣고 학습 target(data-v5 rationale·label, v3.0.1 기준 작성)은 그대로 둔 결과, 프롬프트 규칙과 target이 어긋난 채 학습됐다. test_v5에서는 보류가 늘고 test_v30에서는 보류가 줄어, 두 셋에서 반대 방향으로 나빠졌다. 프롬프트 변경 효과와 출력 순서 변경 효과는 이 실험에서 분리되지 않는다(둘을 함께 바꿈).')
    w('- label 토큰 확률은 근거 먼저 출력 설계에서는 결정적(≈1.0)이라 보류 조절에 쓸 수 없다(7절). confidence를 쓰려면 측정 위치나 출력 순서를 바꿔야 한다.')
    w('- v3.1 반영이 목표라면 학습 target을 v3.1 정의로 다시 쓰는 단계(data-v5 rationale 재작성·G3-a 등 라벨 재검토)가 먼저 필요하며, 이는 별도 설계·승인 대상이다. S5b(문맥 블록을 학습 입력에 포함)는 이 결과와 별개로 보류한다.')
    w('- 산출물: 예측·로그 reports/eval/lora_v6a/lora_v6a_s{42,43,44}/, run_v6.log, SHA256SUMS_blade_v6a(어댑터 tar 3개는 git 밖, 로컬 zip BLADE_lora_v6a_export.zip SHA-256 `' + (A['files']['zip_sha256'] or '')[:16] + '…`), 채점 scores_test_v5.json·eval_test_v5.md·scores_test_v30.json·eval_v30.md, 분석 analysis.json(scripts/analyze_lora_v6a.py). 커밋하지 않았다. 주지표·발표 수치(v5) 불변, test_v6 추론 없음.')
    (R6 / 'report.md').write_text('\n'.join(o) + '\n', encoding='utf-8', newline='\r\n')


if __name__ == '__main__': main()
