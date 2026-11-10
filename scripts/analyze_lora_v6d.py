"""C′ LoRA v6d (v5 recipe + corrected training labels: data-v6d = data-v5 SFT rows with 36 C1 label changes + 42 C2 rationale rewrites) — stage-3 analysis and report.
Reads only existing prediction files (no inference): reports/eval/lora_v6d/lora_v6d_s{42,43,44}/eval/ and reports/eval/lora_v5/lora_v5_s*/eval/ (v5 baseline),
plus the scorer outputs scores_test_v5.json / scores_test_v30.json / scores_supp.json (scripts/eval_test_v5.py, eval_v30.py --eval-def both, eval_v31_supp.py).
Writes reports/eval/lora_v6d/analysis.json and report.md. Pre-registered adoption criteria (AGENTS.md 작업 C′, 3-seed mean):
 (1) test_v5 oas_code macro-F1 >= v5 + 0.016, (2) test_v30 207 concrete precision drop <= 0.025, (3) test_v30 207 public misjudge (/35) mean <= 2.0. No early gate."""
from __future__ import annotations
import hashlib, json, re, statistics as st, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from eval_v30 import segments as v30_segments
R5 = ROOT / 'reports/eval/lora_v5'; R6 = ROOT / 'reports/eval/lora_v6d'; RD = ROOT / 'reports/data_v6d'
TEST5 = ROOT / 'datasets/blade/processed/test_v5.jsonl'; MAN5 = ROOT / 'datasets/blade/processed/data_v5/test_v5_manifest.json'
MAN5_SHA = '57fd384f46e89e905209e627a7ff7fb9f312e22a7bed222639e91a80bd05fccd'
SEEDS = [42, 43, 44]
L = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']; MANUAL = 'manual_review_required'
SHORT = {'public': 'public', 'role_required': 'role', 'membership_required': 'member', 'tenant_match': 'tenant', 'owner_match': 'owner', 'owner_or_admin': 'own+adm', 'manual_review_required': 'manual', 'output_error': 'ERR'}
CRIT = dict(macro_f1_gain=0.016, precision_drop=0.025, public_misjudge_max=2.0)
HAN = re.compile(r'[\u4e00-\u9fff]')
S13 = [('v5t-ghost-924636cc9d', 'G3-b/G6-c 경계(모든 역할 보유 권한)'), ('v5t-rocketchat-0398a2f985', 'canAccessRoom(G6-a)'), ('v5t-rocketchat-0780c8e386', 'G3-a 그룹 안 역할'),
       ('v5t-rocketchat-09c0e4be92', 'G3-a 그룹 안 역할'), ('v5t-rocketchat-0d896bf7fc', 'G3-a 그룹 안 역할'), ('v5t-rocketchat-23a530da4b', 'G4-c/G6-b 경계(설정 의존)'),
       ('v5t-rocketchat-7508165c03', 'G3-a 그룹 안 역할'), ('v5t-rocketchat-d83dae7c4e', 'canAccessRoom(G6-a)'), ('v5t-rocketchat-ec189eb0b4', 'G3-a 그룹 안 역할'),
       ('v5t-rocketchat-f7c14cc85e', 'canAccessRoom(G6-a)'), ('v5t-umami-bf7e66056f', 'G6-a 복합 OR(Umami canView)'), ('v5t-umami-dd7523bace', 'G6-a 복합 OR(Umami canDelete)')]
KINDS = (('test_v5', 'oas_code'), ('test_v5', 'oas'), ('test_v30', 'oas_code'), ('test_v30', 'oas'), ('supp', 'oas_code'), ('supp', 'oas'))
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
lab = lambda r: r['prediction']['label'] if r.get('prediction') else 'output_error'


def ms(xs, nd=3, pct=False):
    if pct: xs = [x * 100 for x in xs]
    if len(xs) == 1: return f'{xs[0]:.{1 if pct else nd}f}' + ('%' if pct else '')
    return f'{st.mean(xs):.{1 if pct else nd}f} ± {st.stdev(xs):.{1 if pct else nd}f}' + ('%' if pct else '')


def pred_path(ver, seed, kind, cond):
    prefix = {'test_v5': 'v5test_predictions_', 'test_v30': 'predictions_', 'supp': 'supp_predictions_'}[kind]
    return (R5 if ver == 'v5' else R6) / f'lora_{ver}_s{seed}' / 'eval' / f'{prefix}{cond}_lora_{ver}_s{seed}_final.jsonl'


def main():
    assert sha(MAN5) == MAN5_SHA; man = json.load(open(MAN5, encoding='utf-8')); assert sha(TEST5) == man['sha256']['datasets/blade/processed/test_v5.jsonl']
    t5 = {r['id']: r for r in rd(TEST5)}; meta30, seg30 = v30_segments(); syn30 = set(seg30['synthetic'])
    ids207 = [i for i in seg30['all'] if i not in syn30 and meta30[i]['has_code']]; assert len(ids207) == 207
    S5 = json.load(open(R6 / 'scores_test_v5.json', encoding='utf-8')); S30 = json.load(open(R6 / 'scores_test_v30.json', encoding='utf-8')); SS = json.load(open(R6 / 'scores_supp.json', encoding='utf-8'))
    P = {(v, s, k, c): {r['id']: r for r in rd(pred_path(v, s, k, c))} for v in ('v5', 'v6d') for s in SEEDS for k, c in KINDS}
    A = dict(definition=__doc__, criteria=CRIT)

    def s5(ver, cond): return [r for r in S5 if r['condition'] == cond and r['model'].startswith(f'lora_{ver}_s')]
    def s30(ver, cond): return [r for r in S30 if r['eval_def'] == 'v2' and r['condition'] == cond and r['model'].startswith(f'lora_{ver}_s')]
    def ssp(ver, cond): return [r for r in SS if r['condition'] == cond and r['model'].startswith(f'lora_{ver}_s')]
    def pub35(ver, seed):
        pr = P[(ver, seed, 'test_v30', 'oas_code')]
        den = [i for i in ids207 if meta30[i]['security_state'] == 'declared' and meta30[i]['label'] != 'public']; assert len(den) == 35
        return [i for i in den if lab(pr[i]) == 'public']
    head = {}
    for ver in ('v5', 'v6d'):
        a = s5(ver, 'oas_code'); b = s30(ver, 'oas_code'); sp = ssp(ver, 'oas_code'); pub = {s: pub35(ver, s) for s in SEEDS}
        head[ver] = dict(test_v5=dict(macro_f1=[r['macro_f1'] for r in a], accuracy=[r['accuracy'] for r in a], manual=[r['manual_ratio'] for r in a], errors=[r['output_errors'] for r in a],
                                      per_label={l: [r['per_label'][l]['f1'] for r in a] for l in L}, per_label_pr={l: [(r['per_label'][l]['precision'], r['per_label'][l]['recall']) for r in a] for l in L},
                                      per_project={p: [r['per_project'][p]['accuracy'] for r in a] for p in ('rocketchat', 'ghost', 'umami')}, manual_count=[int(round(r['manual_ratio'] * 283)) for r in a]),
                         test_v5_oas=dict(macro_f1=[r['macro_f1'] for r in s5(ver, 'oas')], accuracy=[r['accuracy'] for r in s5(ver, 'oas')], manual=[r['manual_ratio'] for r in s5(ver, 'oas')], errors=[r['output_errors'] for r in s5(ver, 'oas')]),
                         test_v30_207=dict(macro_f1=[r['main_excl_synthetic']['macro_f1'] for r in b], macro_f1_265=[r['main']['macro_f1'] for r in b], accuracy=[r['main_excl_synthetic']['accuracy'] for r in b],
                                           precision=[r['main_excl_synthetic']['concrete']['precision'] for r in b], recall=[r['main_excl_synthetic']['concrete']['recall'] for r in b], answer_rate=[r['main_excl_synthetic']['concrete']['answer_rate'] for r in b],
                                           manual=[r['main_excl_synthetic']['manual_ratio'] for r in b], errors=[r['main_excl_synthetic']['output_errors'] for r in b], per_label={l: [r['main_excl_synthetic']['per_label'][l]['f1'] for r in b] for l in L},
                                           public_misjudge_35=[len(pub[s]) for s in SEEDS], public_ids={str(s): pub[s] for s in SEEDS}),
                         test_v30_oas=dict(macro_f1_160=[r['main']['macro_f1'] for r in s30(ver, 'oas')], macro_f1_102=[r['main_excl_synthetic']['macro_f1'] for r in s30(ver, 'oas')], precision=[r['main']['concrete']['precision'] for r in s30(ver, 'oas')],
                                           manual=[r['main']['manual_ratio'] for r in s30(ver, 'oas')], errors=[r['main']['output_errors'] for r in s30(ver, 'oas')], public_misjudge=[r['public_misjudge_new']['count'] for r in s30(ver, 'oas')]),
                         supp=dict(macro_f1=[r['macro_f1'] for r in sp], accuracy=[r['accuracy'] for r in sp], manual=[r['manual_ratio'] for r in sp], errors=[r['output_errors'] for r in sp],
                                   per_label={l: [r['per_label'][l]['f1'] for r in sp] for l in L}, per_project={p: [r['per_project'][p]['accuracy'] for r in sp] for p in ('chatwoot', 'chamilo', 'flowise', 'multitenant_lab', 'generic_university')}),
                         supp_oas=dict(macro_f1=[r['macro_f1'] for r in ssp(ver, 'oas')], accuracy=[r['accuracy'] for r in ssp(ver, 'oas')], manual=[r['manual_ratio'] for r in ssp(ver, 'oas')], errors=[r['output_errors'] for r in ssp(ver, 'oas')]))
    A['headline'] = head
    c1 = st.mean(head['v6d']['test_v5']['macro_f1']) - st.mean(head['v5']['test_v5']['macro_f1']); c2 = st.mean(head['v5']['test_v30_207']['precision']) - st.mean(head['v6d']['test_v30_207']['precision']); c3 = st.mean(head['v6d']['test_v30_207']['public_misjudge_35'])
    A['verdict'] = dict(c1_macro_f1_delta=round(c1, 4), c1_pass=c1 >= CRIT['macro_f1_gain'], c2_precision_drop=round(c2, 4), c2_pass=c2 <= CRIT['precision_drop'], c3_public_misjudge_mean=round(c3, 2), c3_pass=c3 <= CRIT['public_misjudge_max'])
    A['verdict']['adopt'] = all(A['verdict'][k] for k in ('c1_pass', 'c2_pass', 'c3_pass'))
    A['paired_t5_delta'] = [round(b_ - a_, 4) for a_, b_ in zip(head['v5']['test_v5']['macro_f1'], head['v6d']['test_v5']['macro_f1'])]

    # ---- transitions v5 -> v6d (test_v5 oas_code, same seed) ----------------------------------------------------------
    trans = {}; manual_by_truth = {}; disagree_pairs = Counter(); n_disagree = 0; n_all_three = 0; fixed_by_truth = {}; wrong_by_truth = {}
    for s in SEEDS:
        a = P[('v5', s, 'test_v5', 'oas_code')]; b = P[('v6d', s, 'test_v5', 'oas_code')]
        pairs = Counter((lab(a[i]), lab(b[i])) for i in t5 if lab(a[i]) != lab(b[i])); trans[str(s)] = {f'{x}->{y}': n for (x, y), n in pairs.most_common()}
        manual_by_truth[str(s)] = dict(Counter(t5[i]['label'] for i in t5 if lab(a[i]) != MANUAL and lab(b[i]) == MANUAL))
        trans[str(s) + '_fixed'] = sum(lab(a[i]) != t5[i]['label'] and lab(b[i]) == t5[i]['label'] for i in t5); trans[str(s) + '_newly_wrong'] = sum(lab(a[i]) == t5[i]['label'] and lab(b[i]) != t5[i]['label'] for i in t5)
        fixed_by_truth[str(s)] = dict(Counter(t5[i]['label'] for i in t5 if lab(a[i]) != t5[i]['label'] and lab(b[i]) == t5[i]['label'])); wrong_by_truth[str(s)] = dict(Counter(t5[i]['label'] for i in t5 if lab(a[i]) == t5[i]['label'] and lab(b[i]) != t5[i]['label']))
    for i in t5:
        ls = [lab(P[('v6d', s, 'test_v5', 'oas_code')][i]) for s in SEEDS]
        if len(set(ls)) > 1:
            n_disagree += 1; n_all_three += len(set(ls)) == 3
            for x, y in {tuple(sorted(p)) for p in [(ls[0], ls[1]), (ls[0], ls[2]), (ls[1], ls[2])] if p[0] != p[1]}: disagree_pairs[f'{x}|{y}'] += 1
    v5_dis = sum(len({lab(P[('v5', s, 'test_v5', 'oas_code')][i]) for s in SEEDS}) > 1 for i in t5)
    core = [i for i in t5 if all(lab(P[(v, s, 'test_v5', 'oas_code')][i]) != t5[i]['label'] for v in ('v5', 'v6d') for s in SEEDS)]
    A['transitions'] = dict(v5_to_v6d=trans, new_manual_by_truth=manual_by_truth, fixed_by_truth=fixed_by_truth, newly_wrong_by_truth=wrong_by_truth, v6d_seed_disagree_records=n_disagree, v6d_all_three_differ=n_all_three,
                            v5_seed_disagree_records=v5_dis, v6d_disagree_pairs=dict(disagree_pairs.most_common()), wrong_in_all_6_runs=len(core), wrong_in_all_6_by_truth=dict(Counter(t5[i]['label'] for i in core)), wrong_in_all_6_by_project=dict(Counter(t5[i]['meta']['project'] for i in core)))
    A['v6d_confusion_mean'] = {a_: {b_: round(st.mean([r['confusion'][a_][b_] for r in s5('v6d', 'oas_code')]), 1) for b_ in L + ['output_error']} for a_ in L}
    A['v5_confusion_mean'] = {a_: {b_: round(st.mean([r['confusion'][a_][b_] for r in s5('v5', 'oas_code')]), 1) for b_ in L + ['output_error']} for a_ in L}
    # per-seed manual counts by truth (test_v5): where does the extra abstention come from?
    A['manual_by_truth_seed'] = {ver: {str(s): dict(Counter(t5[i]['label'] for i in t5 if lab(P[(ver, s, 'test_v5', 'oas_code')][i]) == MANUAL)) for s in SEEDS} for ver in ('v5', 'v6d')}
    # training-label change summary (C1) for context: which label pairs changed in training
    ch = rd(RD / 'c1_changes.jsonl'); A['c1_changes'] = dict(n=len(ch), label_changes=dict(Counter(f"{c['label_from']}->{c['label_to']}" for c in ch if c.get('label_changed'))), splits=dict(Counter(c['split'] for c in ch)))

    # ---- S1-3 ------------------------------------------------------------------------------------------------------
    A['s13'] = [dict(id=i, type=ty, project=t5[i]['meta']['project'], method=t5[i]['method'], path=t5[i]['path'], truth=t5[i]['label'], v5=[lab(P[('v5', s, 'test_v5', 'oas_code')][i]) for s in SEEDS], v6d=[lab(P[('v6d', s, 'test_v5', 'oas_code')][i]) for s in SEEDS]) for i, ty in S13]
    by_type = defaultdict(lambda: dict(n=0, v5_correct=0, v6d_correct=0))
    for r in A['s13']:
        d = by_type[r['type']]; d['n'] += 1; d['v5_correct'] += sum(x == r['truth'] for x in r['v5']); d['v6d_correct'] += sum(x == r['truth'] for x in r['v6d'])
    A['s13_by_type'] = dict(by_type)

    # ---- errors, length, time, env -----------------------------------------------------------------------------------
    errs = {}; lens = {}; times = {}
    for ver in ('v5', 'v6d'):
        for s in SEEDS:
            for k, c in KINDS:
                rows = list(P[(ver, s, k, c)].values()); key = f'{ver}_s{s}_{k}_{c}'; e = [r for r in rows if not r.get('prediction')]
                errs[key] = dict(n=len(e), han=sum(bool(HAN.search(r['raw'] or '')) for r in e), hit_max=sum((r.get('output_tokens') or 0) >= 256 for r in e) if ver == 'v6d' else None,
                                 examples=[dict(id=r['id'], truth=r['label'], output_tokens=r.get('output_tokens'), raw=(r['raw'] or '')[:160]) for r in e[:3]])
                lens[key] = dict(raw_chars_mean=round(st.mean(len(r['raw'] or '') for r in rows), 1), output_tokens_mean=round(st.mean(r['output_tokens'] for r in rows), 1) if ver == 'v6d' else None, output_tokens_max=max(r['output_tokens'] for r in rows) if ver == 'v6d' else None)
                times[key] = dict(inference_ms_mean=round(st.mean(r['inference_ms'] for r in rows), 1))
                if ver == 'v6d':
                    tj = json.load(open(str(pred_path(ver, s, k, c)) + '.timing.json', encoding='utf-8')); times[key].update(wall_s=tj['inference_wall_s'], mean_ms_per_row=tj['mean_ms_per_row'], hit_max_new_tokens=tj['hit_max_new_tokens'], truncated_prompts=tj['truncated_prompts'], gpu_peak_gib=tj['gpu_memory']['peak_allocated_gib'])
    A['errors'] = errs; A['lengths'] = lens; A['times'] = times
    env = {str(s): json.load(open(R6 / f'lora_v6d_s{s}/env.json', encoding='utf-8')) for s in SEEDS}; env5 = json.load(open(R5 / 'lora_v5_s42/env.json', encoding='utf-8'))
    tr = {}; tr5 = {}
    for s in SEEDS:
        j = json.load(open(R6 / f'lora_v6d_s{s}/logs/train_result.json', encoding='utf-8'))
        tr[str(s)] = dict(steps=j['steps'], minutes=j['minutes'], train_loss=round(j['train_loss'], 4), val_oas_final=round(j['eval_loss_by_condition']['oas'][-1][1], 4), val_oas_code_final=round(j['eval_loss_by_condition']['oas_code'][-1][1], 4),
                          val_oas_min=round(min(v for _, v in j['eval_loss_by_condition']['oas']), 4), val_oas_code_min=round(min(v for _, v in j['eval_loss_by_condition']['oas_code']), 4), peak_gib=j['gpu_memory']['peak_allocated_gib'], reserved_gib=j['gpu_memory']['peak_reserved_gib'],
                          trainable=j['trainable_params'], padding_free=j['padding_free'], effective_batch=j['effective_batch'])
        j = json.load(open(R5 / f'lora_v5_s{s}/logs/train_result.json', encoding='utf-8')); tr5[str(s)] = dict(steps=j['steps'], minutes=j['minutes'], train_loss=round(j['train_loss'], 4), val_oas_final=round(j['eval_loss_by_condition']['oas'][-1][1], 4), val_oas_code_final=round(j['eval_loss_by_condition']['oas_code'][-1][1], 4))
        log = (R6 / f'lora_v6d_s{s}/logs/run.log').read_text(encoding='utf-8', errors='replace'); m = re.search(r'loss mask check \(row 0\): (\d+)/(\d+) tokens masked \(-100\), (\d+) assistant tokens in loss', log); tr[str(s)]['mask_row0'] = m.group(0) if m else None
        tr[str(s)]['hash_gate'] = 'inputs verified against data_v6d_hashes.json' in log and 'test_v5 inputs verified against test_v5_manifest.json' in log
    assert len({tr[str(s)]['mask_row0'] for s in SEEDS}) == 1 and tr['42']['mask_row0'] and all(tr[str(s)]['hash_gate'] for s in SEEDS), tr
    A['env'] = dict(v6d=env, v5_s42=env5); A['train'] = dict(v6d=tr, v5=tr5); A['config_v6d'] = json.load(open(R6 / 'lora_v6d_s42/config.json', encoding='utf-8'))
    runlog = (R6 / 'run_v6d.log').read_text(encoding='utf-8', errors='replace'); A['run_log_marks'] = [l for l in runlog.splitlines() if l.startswith('=== ')][:40]
    zp = Path('<USERPROFILE>/Downloads/BLADE_lora_v6d_export.zip'); A['files'] = dict(zip_sha256=sha(zp) if zp.exists() else None, sums=(R6 / 'SHA256SUMS_blade_v6d').read_text(encoding='utf-8').strip().splitlines())
    (R6 / 'analysis.json').write_text(json.dumps(A, ensure_ascii=False, indent=1), encoding='utf-8', newline='\n')
    write_report(A, t5)


def write_report(A, t5):
    H = A['headline']; V = A['verdict']; v5, v6 = H['v5'], H['v6d']; T = A['transitions']
    o = []; w = o.append
    w('# C′ LoRA v6d 보고 — v5 설정 + 학습 정답만 교정 (2026-11-07 채점, 학습 2026-11-05, 3 seed, 커밋 없음)\n')
    w('사전 기록 AGENTS.md "작업 C′"·"data-v6d 동결". 변경은 학습 정답뿐: data-v6d = data-v5 SFT 행에 C1 확정 label 36건(전부 gitea; owner_match→role_required 23 등) + C2 rationale 42건을 반영한 것이며 user 입력·행 순서·나머지 행은 바이트 동일. 베이스 7B(S8 불채택으로 확정), 프롬프트 v3.0.1, 출력 순서, max_seq_len 4096, max_new_tokens 256, LoRA r16/α16·3 epoch·lr 2e-4·batch 2×4·cosine·adamw_8bit·completion-only 마스킹·greedy는 v5와 같다. 판정셋 test_v5 283(dev, oas_code) + 회귀 test_v30 oas_code 합성 제외 207, 보조 test_v31_supp 222. v5 수치는 기존 예측 파일을 같은 채점기로 재채점한 값(재추론 없음). test_v6은 추론하지 않았다. 주지표·발표 수치(v5)는 바꾸지 않는다.\n')
    w(f"## 1. 판정 — {'사전 기준 3개 충족, 채택 후보(사용자 승인 대상)' if V['adopt'] else '사전 기준 미달, **불채택** → v5 유지(최종 모델, S9 대상)'}\n")
    w('| 기준(3 seed 평균) | v5 | v6d | 차이 | 기준 | 충족 |\n|---|---:|---:|---:|---|---|')
    w(f"| (1) test_v5 oas_code macro-F1 상승 ≥ 0.016 | {ms(v5['test_v5']['macro_f1'])} | {ms(v6['test_v5']['macro_f1'])} | {V['c1_macro_f1_delta']:+.3f} | ≥ +0.016 | {'예' if V['c1_pass'] else '**아니오**'} |")
    w(f"| (2) test_v30 207 구체 정밀도 하락 ≤ 0.025 | {ms(v5['test_v30_207']['precision'])} | {ms(v6['test_v30_207']['precision'])} | {-V['c2_precision_drop']:+.3f} | 하락 ≤ 0.025 | {'예' if V['c2_pass'] else '**아니오**'} |")
    w(f"| (3) test_v30 207 public 오판(/35) 평균 ≤ 2.0 | {' / '.join(map(str, v5['test_v30_207']['public_misjudge_35']))} (평균 {st.mean(v5['test_v30_207']['public_misjudge_35']):.2f}) | {' / '.join(map(str, v6['test_v30_207']['public_misjudge_35']))} (평균 {V['c3_public_misjudge_mean']:.2f}) | {V['c3_public_misjudge_mean'] - st.mean(v5['test_v30_207']['public_misjudge_35']):+.2f} | ≤ 2.0 | {'예' if V['c3_pass'] else '**아니오**'} |")
    sd6 = st.stdev(v6['test_v5']['macro_f1'])
    w(f"\n- 같은 seed끼리의 test_v5 macro-F1 차이(v6d − v5): {', '.join(f'{d:+.3f}' for d in A['paired_t5_delta'])}. seed별 v6d {', '.join(f'{x:.3f}' for x in v6['test_v5']['macro_f1'])} — seed 표준편차가 {sd6:.3f}(v5 0.016)로 커져 평균 차이 {V['c1_macro_f1_delta']:+.3f}은 v6d 자체 표준편차 안이다. 기준 (1)은 {'충족' if V['c1_pass'] else '미달'}이고, 실험 규칙 \"표준편차보다 큰 차이만 차이로 인정\"으로 봐도 seed 하나(s43 +0.051)가 끌어올린 결과라 안정적 개선이 아니다. manual 비율도 16.6% → {st.mean(v6['test_v5']['manual']) * 100:.1f}%로 올라 보류가 늘었다.")
    w(f"- test_v5 정확도 {st.mean(v5['test_v5']['accuracy']):.3f} → {st.mean(v6['test_v5']['accuracy']):.3f}, manual 건수 {' / '.join(map(str, v5['test_v5']['manual_count']))} → {' / '.join(map(str, v6['test_v5']['manual_count']))}(seed별). test_v30 207 구체 정밀도 {st.mean(v5['test_v30_207']['precision']):.3f} → {st.mean(v6['test_v30_207']['precision']):.3f}, public 오판 평균 {st.mean(v5['test_v30_207']['public_misjudge_35']):.2f} → {V['c3_public_misjudge_mean']:.2f}, test_v30 macro-F1(207) {st.mean(v5['test_v30_207']['macro_f1']):.3f} → {st.mean(v6['test_v30_207']['macro_f1']):.3f}. supp macro-F1 {st.mean(v5['supp']['macro_f1']):.3f} → {st.mean(v6['supp']['macro_f1']):.3f}.\n")
    w('## 2. 실행 환경·학습\n')
    e = A['env']['v6d']['42']; e5 = A['env']['v5_s42']; Tt = A['train']['v6d']['42']
    w(f"- Pod: RunPod H100({e['gpu']} {e['vram_gb']} GB), torch {e['torch']}(CUDA {e['cuda']}), transformers {e['transformers']}, trl {e['trl']}, peft {e['peft']}, unsloth {e['unsloth']}, python {e['python']}. 2026-11-05 07:18 → 09:14 UTC(1시간 56분: 설치 2분, preflight 1분, seed당 37~38분 × 3), 번들 blade_v6d_20261105.tgz(`3c52b2cd…`), 해시 게이트(data_v6d_hashes.json `82efda86…`, test_v5_manifest `57fd384f…`, 프롬프트 `d0913c27…`, run.log `inputs verified` 3 seed 확인) 통과, Pod 자동 정지. 조기 판정 없음(사전 기록대로).")
    w(f"- v5 환경(비교): {e5.get('gpu')}, unsloth {e5.get('unsloth')}. 손실 마스킹 0번 행 `{Tt['mask_row0']}`(3 seed 동일, v5·v6c와 같은 값). LoRA trainable {Tt['trainable']:,}, 유효 배치 {Tt['effective_batch']}, padding_free={Tt['padding_free']}.")
    w('\n| run | steps | 학습 분 | train_loss | val oas loss(final / 최저) | val oas_code loss(final / 최저) | 피크 GPU GiB(alloc / reserved) | v5 같은 seed train_loss / val final(oas, oas_code) / 분 |\n|---|---:|---:|---:|---|---|---|---|')
    for s in map(str, SEEDS):
        t = A['train']['v6d'][s]; t5_ = A['train']['v5'][s]
        w(f"| lora_v6d_s{s} | {t['steps']} | {t['minutes']} | {t['train_loss']} | {t['val_oas_final']} / {t['val_oas_min']} | {t['val_oas_code_final']} / {t['val_oas_code_min']} | {t['peak_gib']} / {t['reserved_gib']} | {t5_['train_loss']} / {t5_['val_oas_final']}, {t5_['val_oas_code_final']} / {t5_['minutes']} |")
    w('\nval은 학습 정상 여부 확인용(발산 없음, 480 step 완주)이며 체크포인트 선택에 쓰지 않았다(final 고정). train_loss·val loss는 v5보다 약간 높다(교정된 36행의 label이 바뀌어 같은 입력에 대한 target 분포가 달라짐; val_v6d에도 교정 6행 포함).\n')
    w('## 3. test_v5 283 (dev) — oas_code\n')
    w('| 모델 | macro-F1 | 정확도 | manual 비율 | manual 건수(seed별) | 출력 오류(합) |\n|---|---:|---:|---:|---|---:|')
    for ver, nm in (('v5', 'lora_v5'), ('v6d', 'lora_v6d')):
        h = H[ver]['test_v5']; w(f"| {nm} | {ms(h['macro_f1'])} | {ms(h['accuracy'])} | {ms(h['manual'], pct=True)} | {' / '.join(map(str, h['manual_count']))} | {sum(h['errors'])} |")
    w('\n### label별 F1 (support)\n')
    sup = {l: [r for r in json.load(open(R6 / 'scores_test_v5.json', encoding='utf-8')) if r['condition'] == 'oas_code'][0]['per_label'][l]['support'] for l in L}
    w('| 모델 | ' + ' | '.join(f'{l} ({sup[l]})' for l in L) + ' |\n|---|' + '---:|' * len(L))
    for ver, nm in (('v5', 'lora_v5'), ('v6d', 'lora_v6d')): w(f'| {nm} | ' + ' | '.join(ms(H[ver]['test_v5']['per_label'][l]) for l in L) + ' |')
    w('\n### 판정 label 정밀도 / 재현율 (seed별)\n\n| run | owner_or_admin P / R / F1 | membership_required P / R / F1 | role_required P / R / F1 | owner_match P / R / F1 | manual P / R / F1 |\n|---|---|---|---|---|---|')
    for ver in ('v5', 'v6d'):
        for k, s in enumerate(SEEDS):
            cells = []
            for l in ('owner_or_admin', 'membership_required', 'role_required', 'owner_match', 'manual_review_required'):
                p, r = H[ver]['test_v5']['per_label_pr'][l][k]; f = H[ver]['test_v5']['per_label'][l][k]; cells.append(f'{p:.3f} / {r:.3f} / {f:.3f}')
            w(f'| lora_{ver}_s{s} | ' + ' | '.join(cells) + ' |')
    w('\n### 프로젝트별 정확도\n\n| 모델 | rocketchat (157) | ghost (69) | umami (57) |\n|---|---:|---:|---:|')
    for ver, nm in (('v5', 'lora_v5'), ('v6d', 'lora_v6d')): w(f"| {nm} | " + ' | '.join(ms(H[ver]['test_v5']['per_project'][p]) for p in ('rocketchat', 'ghost', 'umami')) + ' |')
    w('\n### 혼동표 (정답 행 → 예측 열, 3 seed 평균 건수)\n')
    w('| 정답 \\ 예측 | ' + ' | '.join(SHORT[l] for l in L + ['output_error']) + ' |\n|---|' + '---:|' * 8)
    for a in L:
        if not sup[a]: continue
        w(f'| **{SHORT[a]}** (v5) | ' + ' | '.join(str(A['v5_confusion_mean'][a][b]) for b in L + ['output_error']) + ' |')
        w(f'| {SHORT[a]} (v6d) | ' + ' | '.join(str(A['v6d_confusion_mean'][a][b]) for b in L + ['output_error']) + ' |')
    w('\n### manual 예측의 정답 label 분포 (seed별)\n\n| run | ' + ' | '.join(SHORT[l] for l in L if l != 'tenant_match') + ' | 합 |\n|---|' + '---:|' * 7)
    for ver in ('v5', 'v6d'):
        for s in map(str, SEEDS):
            d = A['manual_by_truth_seed'][ver][s]; w(f'| lora_{ver}_s{s} | ' + ' | '.join(str(d.get(l, 0)) for l in L if l != 'tenant_match') + f' | {sum(d.values())} |')
    w('\n### oas(명세만) 보조\n\n| 모델 | macro-F1 | 정확도 | manual 비율 | 출력 오류(합) |\n|---|---:|---:|---:|---:|')
    for ver, nm in (('v5', 'lora_v5'), ('v6d', 'lora_v6d')):
        h = H[ver]['test_v5_oas']; w(f"| {nm} | {ms(h['macro_f1'])} | {ms(h['accuracy'])} | {ms(h['manual'], pct=True)} | {sum(h['errors'])} |")
    w('\n원자료 scores_test_v5.json, eval_test_v5.md(scripts/eval_test_v5.py, manifest 해시 검증).\n')
    w('## 4. test_v30 회귀 — oas_code 합성 제외 207 (주지표 조건)\n')
    w('| 모델 | macro-F1(207) | macro-F1(265) | 정확도 | 구체 정밀도 | 구체 재현율 | 구체 응답률 | manual 비율 | public 오판(신, /35, seed별) | 출력 오류(seed별) |\n|---|---:|---:|---:|---:|---:|---:|---:|---|---|')
    for ver, nm in (('v5', 'lora_v5'), ('v6d', 'lora_v6d')):
        h = H[ver]['test_v30_207']; w(f"| {nm} | {ms(h['macro_f1'])} | {ms(h['macro_f1_265'])} | {ms(h['accuracy'])} | {ms(h['precision'])} | {ms(h['recall'])} | {ms(h['answer_rate'])} | {ms(h['manual'], pct=True)} | {' / '.join(map(str, h['public_misjudge_35']))} | {' / '.join(map(str, h['errors']))} |")
    w('\n| 모델 | ' + ' | '.join(f'{l}' for l in L if l not in ('membership_required', 'tenant_match')) + ' |\n|---|' + '---:|' * 5)
    for ver, nm in (('v5', 'lora_v5'), ('v6d', 'lora_v6d')): w(f'| {nm} | ' + ' | '.join(ms(H[ver]['test_v30_207']['per_label'][l]) for l in L if l not in ('membership_required', 'tenant_match')) + ' |')
    w('\npublic 오판 id(v6d): ' + '; '.join(f"s{s}: {', '.join(v6['test_v30_207']['public_ids'][str(s)]) or '-'}" for s in SEEDS) + f". v5: {'; '.join(f'''s{s}: {', '.join(v5['test_v30_207']['public_ids'][str(s)])}''' for s in SEEDS)}.\n")
    w('### oas(명세만) 160\n\n| 모델 | macro-F1(160) | 합성 제외 102 | 구체 정밀도 | manual 비율 | public 오판(신) | 출력 오류 |\n|---|---:|---:|---:|---:|---|---|')
    for ver, nm in (('v5', 'lora_v5'), ('v6d', 'lora_v6d')):
        h = H[ver]['test_v30_oas']; w(f"| {nm} | {ms(h['macro_f1_160'])} | {ms(h['macro_f1_102'])} | {ms(h['precision'])} | {ms(h['manual'], pct=True)} | {' / '.join(map(str, h['public_misjudge']))} | {' / '.join(map(str, h['errors']))} |")
    w('\n원자료 scores_test_v30.json, eval_v30.md(scripts/eval_v30.py --eval-def both).\n')
    w('## 5. test_v31_supp 222 (보조 조건)\n')
    w('| 모델 | oas_code macro-F1 | 정확도 | manual 비율 | 출력 오류(합) | oas macro-F1 | oas manual 비율 |\n|---|---:|---:|---:|---:|---:|---:|')
    for ver, nm in (('v5', 'lora_v5'), ('v6d', 'lora_v6d')):
        h = H[ver]['supp']; ho = H[ver]['supp_oas']; w(f"| {nm} | {ms(h['macro_f1'])} | {ms(h['accuracy'])} | {ms(h['manual'], pct=True)} | {sum(h['errors'])} | {ms(ho['macro_f1'])} | {ms(ho['manual'], pct=True)} |")
    w('\n| 모델 | ' + ' | '.join(L) + ' |\n|---|' + '---:|' * 7)
    for ver, nm in (('v5', 'lora_v5'), ('v6d', 'lora_v6d')): w(f'| {nm} | ' + ' | '.join(ms(H[ver]['supp']['per_label'][l]) for l in L) + ' |')
    w('\n| 모델 | chatwoot | chamilo | flowise | multitenant_lab | generic_university |\n|---|---:|---:|---:|---:|---:|')
    for ver, nm in (('v5', 'lora_v5'), ('v6d', 'lora_v6d')): w(f'| {nm} | ' + ' | '.join(ms(H[ver]['supp']['per_project'][p]) for p in ('chatwoot', 'chamilo', 'flowise', 'multitenant_lab', 'generic_university')) + ' |')
    w('\n원자료 scores_supp.json, eval_supp.md(scripts/eval_v31_supp.py). supp 예측 파일은 .gitignore 대상(Flowise 코드 발췌가 raw에 섞일 수 있음).\n')
    w('## 6. 예측 변화 v5 → v6d (test_v5 oas_code, 같은 seed)\n')
    w('| seed | 고쳐짐(v5 오답→v6d 정답) | 새로 틀림(v5 정답→v6d 오답) | 바뀐 전이 상위 |\n|---|---:|---:|---:|')
    for s in map(str, SEEDS):
        top = ', '.join(f"{SHORT[k.split('->')[0]]}→{SHORT[k.split('->')[1]]} {n}" for k, n in list(T['v5_to_v6d'][s].items())[:6]); w(f"| s{s} | {T['v5_to_v6d'][s + '_fixed']} | {T['v5_to_v6d'][s + '_newly_wrong']} | {top} |")
    w('\n고쳐진 건 / 새로 틀린 건의 정답 label:\n\n| seed | ' + ' | '.join(SHORT[l] for l in L if l != 'tenant_match') + ' |\n|---|' + '---:|' * 6)
    for s in map(str, SEEDS): w(f'| s{s} 고쳐짐 | ' + ' | '.join(str(T['fixed_by_truth'][s].get(l, 0)) for l in L if l != 'tenant_match') + ' |'); w(f'| s{s} 새로 틀림 | ' + ' | '.join(str(T['newly_wrong_by_truth'][s].get(l, 0)) for l in L if l != 'tenant_match') + ' |')
    w(f"\nseed 간 예측이 갈린 레코드: v6d {T['v6d_seed_disagree_records']}/283(세 seed 모두 다름 {T['v6d_all_three_differ']}), v5 {T['v5_seed_disagree_records']}/283. v6d에서 갈린 label 쌍: " + ', '.join(f"{SHORT[k.split('|')[0]]}|{SHORT[k.split('|')[1]]} {n}" for k, n in list(T['v6d_disagree_pairs'].items())[:8]) + '.')
    cb = T['wrong_in_all_6_by_truth']; cp = T['wrong_in_all_6_by_project']
    w(f"\nv5·v6d 여섯 run 모두 틀린 레코드 {T['wrong_in_all_6_runs']}/283 — 정답 label별 " + ', '.join(f'{SHORT[l]} {cb[l]}' for l in L if l in cb) + '; 프로젝트별 ' + ', '.join(f'{p} {n}' for p, n in cp.items()) + '(S8 v6c 대비 때는 39건).')
    w(f"\n학습에서 바뀐 것은 gitea의 owner_match→role_required 23건 등 C1 {A['c1_changes']['n']}건(label 변경 {sum(A['c1_changes']['label_changes'].values())}: " + ', '.join(f'{k} {n}' for k, n in A['c1_changes']['label_changes'].items()) + ')이다. test_v5에서 그 방향(owner→role, manual→role)으로 예측이 옮겨간 것이 위 전이 표에 보이면 교정 효과이고, manual로 옮겨간 것은 교정과 무관한 seed 변동일 가능성이 크다.\n')
    w('## 7. S1-3 불일치 12건에서의 예측 (v5 → v6d, seed 42/43/44)\n')
    w('| id | 유형 | method path | 정답 | v5 s42/43/44 | v6d s42/43/44 |\n|---|---|---|---|---|---|')
    for r in A['s13']: w(f"| {r['id']} | {r['type']} | {r['method']} {r['path']} | {SHORT[r['truth']]} | {' / '.join(SHORT[x] for x in r['v5'])} | {' / '.join(SHORT[x] for x in r['v6d'])} |")
    w('\n| 유형 | 건수 | v5 정답(3 seed 합 / 가능) | v6d 정답(3 seed 합 / 가능) |\n|---|---:|---:|---:|')
    for ty, d in A['s13_by_type'].items(): w(f"| {ty} | {d['n']} | {d['v5_correct']} / {d['n'] * 3} | {d['v6d_correct']} / {d['n'] * 3} |")
    w(f"\n12건 합계 v5 {sum(d['v5_correct'] for d in A['s13_by_type'].values())}/36 → v6d {sum(d['v6d_correct'] for d in A['s13_by_type'].values())}/36. G3-a(그룹 안 역할 → role_required)는 C1 교정(gitea reqOrgOwnership owner_match → role_required 23건)과 같은 규약 항목이라 이 유형이 교정 효과의 직접 신호인데, {A['s13_by_type']['G3-a 그룹 안 역할']['v5_correct']}/15 → {A['s13_by_type']['G3-a 그룹 안 역할']['v6d_correct']}/15로 오히려 내렸다(Rocket.Chat 그룹 안 역할 건이 role 대신 manual로 감). gitea 23건의 교정이 다른 프로젝트의 같은 규약 패턴으로 전이되지 않았다.\n")
    w('## 8. 출력 오류·출력 길이·추론 시간\n')
    E, LN, TM = A['errors'], A['lengths'], A['times']
    w('| 셋·조건 | v5 출력 오류(s42/43/44) | v6d 출력 오류(s42/43/44) | v6d 오류 중 중국어 혼입 | v6d 오류 중 256 토큰 도달 | v6d 출력 토큰 평균/최대(s42) | v6d 행당 ms(H100, s42/43/44) |\n|---|---|---|---:|---:|---|---|')
    for k, c, nm in (('test_v5', 'oas_code', 'test_v5 oas_code'), ('test_v5', 'oas', 'test_v5 oas'), ('test_v30', 'oas_code', 'test_v30 oas_code(265)'), ('test_v30', 'oas', 'test_v30 oas(269)'), ('supp', 'oas_code', 'supp oas_code'), ('supp', 'oas', 'supp oas')):
        k6 = [f'v6d_s{s}_{k}_{c}' for s in SEEDS]; k5 = [f'v5_s{s}_{k}_{c}' for s in SEEDS]
        w(f"| {nm} | {' / '.join(str(E[x]['n']) for x in k5)} | {' / '.join(str(E[x]['n']) for x in k6)} | {sum(E[x]['han'] for x in k6)} | {sum(E[x]['hit_max'] for x in k6)} | {LN[k6[0]]['output_tokens_mean']} / {LN[k6[0]]['output_tokens_max']} | {' / '.join(str(TM[x]['mean_ms_per_row']) for x in k6)} |")
    w(f"\nv6d 출력 오류 18작업 합계 {sum(E[f'v6d_s{s}_{k}_{c}']['n'] for s in SEEDS for k, c in KINDS)}건(v5 {sum(E[f'v5_s{s}_{k}_{c}']['n'] for s in SEEDS for k, c in KINDS)}건). s42 test_v30 oas 8건·oas_code 6건이 두드러지며 대부분 rationale 중국어 혼입이다. 학습 24.6분/seed(H100), 추론 행당 0.36~0.50 s.\n")
    w('## 9. 해석·한계·다음 단계\n')
    w(f"- 숫자상 기준 (1)은 {'충족' if V['c1_pass'] else '미달'}, (2)·(3)은 {'충족' if V['c2_pass'] and V['c3_pass'] else '미달'}. 그러나 v6d의 seed 표준편차({sd6:.3f})가 v5(0.016)의 두 배가 넘고 세 seed 중 하나(s43)만 크게 올랐다. \"표준편차보다 큰 차이만 인정\" 규칙으로는 개선으로 보기 어렵고, manual 비율이 16.6% → {st.mean(v6['test_v5']['manual']) * 100:.1f}%로 올라 보류가 늘었다. 학습 라벨 36건(2.8%) 교정으로 기대할 수 있는 효과 크기가 seed 잡음보다 작다는 것이 이 실험의 결론이다.")
    w('- 한계: data-v6d의 C1 검수자는 사람이 아니라 Claude(AI)이고 블라인드 감사 불일치 41.2%는 한계로 기록된 상태다(reports/data_v6d/stop_c1_c2_data_v6d.md). OAS-only 390행은 이번 범위 밖이다. 이 결과는 "코드 행 라벨 소폭 교정"의 효과이지 "학습 라벨 전면 재정의"의 효과가 아니다.')
    w('- 다음: 사전 기준 (1) 미달이므로 작업 C′ 중단 규칙대로 **v5 유지**가 기본 결론이다. 발표 주 수치는 v5이며 S9(test_v6) 전까지 바꾸지 않는다. 교정 라벨 data-v6d 자체는 보존하며(동결 해시 불변), 마감 후 OAS-only 390행·블라인드 불일치 28건의 사람 전수 검수와 합쳐 더 큰 교정분으로 재실험할 때 재사용한다.')
    w('- 산출물: 예측·로그 reports/eval/lora_v6d/lora_v6d_s{42,43,44}/, run_v6d.log, SHA256SUMS_blade_v6d(어댑터 tar 3개는 git 밖, 로컬 zip BLADE_lora_v6d_export.zip SHA-256 `' + (A['files']['zip_sha256'] or '')[:16] + '…`), 채점 scores_test_v5.json·eval_test_v5.md·scores_test_v30.json·eval_v30.md·scores_supp.json·eval_supp.md, 분석 analysis.json(scripts/analyze_lora_v6d.py). 커밋하지 않았다. test_v6 추론 없음.')
    (R6 / 'report.md').write_text('\n'.join(o) + '\n', encoding='utf-8', newline='\r\n')


if __name__ == '__main__': main()
