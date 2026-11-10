"""S8 LoRA v6c (base model 7B -> 14B, everything else = LoRA v5) — stage-3 analysis and report.
Reads only existing prediction files (no inference): reports/eval/lora_v6c/{lora_v6c_s42,43,44,base_qwen14b_runpod}/eval/ (retrieved from the Pod)
and reports/eval/lora_v5/lora_v5_s*/eval/ (v5 baseline), plus the scorer outputs scores_test_v5.json / scores_test_v30.json / scores_supp.json produced
by scripts/eval_test_v5.py, eval_v30.py (eval-def v2) and eval_v31_supp.py. Writes reports/eval/lora_v6c/analysis.json and report.md.
Pre-registered adoption criteria (AGENTS.md 작업 S8, 3-seed mean): (1) test_v5 oas_code macro-F1 >= v5 + 0.016, (2) test_v30 207 concrete precision drop <= 0.025,
(3) test_v30 207 public misjudge (/35) mean <= 2.0. Early gate (s42 test_v5 macro-F1 > v5 s42 0.6661) was evaluated on the Pod (early_gate.json)."""
from __future__ import annotations
import hashlib, json, re, statistics as st, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from eval_v30 import segments as v30_segments
R5 = ROOT / 'reports/eval/lora_v5'; R6 = ROOT / 'reports/eval/lora_v6c'
TEST5 = ROOT / 'datasets/blade/processed/test_v5.jsonl'; MAN5 = ROOT / 'datasets/blade/processed/data_v5/test_v5_manifest.json'
MAN5_SHA = '57fd384f46e89e905209e627a7ff7fb9f312e22a7bed222639e91a80bd05fccd'
SEEDS = [42, 43, 44]; VERS = ('v5', 'v6c')
L = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']; MANUAL = 'manual_review_required'
SHORT = {'public': 'public', 'role_required': 'role', 'membership_required': 'member', 'tenant_match': 'tenant', 'owner_match': 'owner', 'owner_or_admin': 'own+adm', 'manual_review_required': 'manual', 'output_error': 'ERR'}
CRIT = dict(macro_f1_gain=0.016, precision_drop=0.025, public_misjudge_max=2.0)
HAN = re.compile(r'[\u4e00-\u9fff]')
S13 = [('v5t-ghost-924636cc9d', 'G3-b/G6-c 경계(모든 역할 보유 권한)'), ('v5t-rocketchat-0398a2f985', 'canAccessRoom(G6-a)'), ('v5t-rocketchat-0780c8e386', 'G3-a 그룹 안 역할'),
       ('v5t-rocketchat-09c0e4be92', 'G3-a 그룹 안 역할'), ('v5t-rocketchat-0d896bf7fc', 'G3-a 그룹 안 역할'), ('v5t-rocketchat-23a530da4b', 'G4-c/G6-b 경계(설정 의존)'),
       ('v5t-rocketchat-7508165c03', 'G3-a 그룹 안 역할'), ('v5t-rocketchat-d83dae7c4e', 'canAccessRoom(G6-a)'), ('v5t-rocketchat-ec189eb0b4', 'G3-a 그룹 안 역할'),
       ('v5t-rocketchat-f7c14cc85e', 'canAccessRoom(G6-a)'), ('v5t-umami-bf7e66056f', 'G6-a 복합 OR(Umami canView)'), ('v5t-umami-dd7523bace', 'G6-a 복합 OR(Umami canDelete)')]
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
lab = lambda r: r['prediction']['label'] if r.get('prediction') else 'output_error'
KINDS = (('test_v5', 'oas_code'), ('test_v5', 'oas'), ('test_v30', 'oas_code'), ('test_v30', 'oas'), ('supp', 'oas_code'), ('supp', 'oas'))
PREFIX = {'test_v5': 'v5test_predictions_', 'test_v30': 'predictions_', 'supp': 'supp_predictions_'}


def ms(xs, nd=3, pct=False):
    if pct: xs = [x * 100 for x in xs]
    if len(xs) == 1: return f'{xs[0]:.{1 if pct else nd}f}' + ('%' if pct else '')
    return f'{st.mean(xs):.{1 if pct else nd}f} ± {st.stdev(xs):.{1 if pct else nd}f}' + ('%' if pct else '')


def pred_path(ver, seed, kind, cond):
    if ver == 'base14b': return R6 / 'base_qwen14b_runpod' / 'eval' / f'{PREFIX[kind]}{cond}_base_qwen14b_runpod.jsonl'
    return (R5 if ver == 'v5' else R6) / f'lora_{ver}_s{seed}' / 'eval' / f'{PREFIX[kind]}{cond}_lora_{ver}_s{seed}_final.jsonl'


def main():
    assert sha(MAN5) == MAN5_SHA; man = json.load(open(MAN5, encoding='utf-8')); assert sha(TEST5) == man['sha256']['datasets/blade/processed/test_v5.jsonl']
    t5 = {r['id']: r for r in rd(TEST5)}; meta30, seg30 = v30_segments(); syn30 = set(seg30['synthetic'])
    ids207 = [i for i in seg30['all'] if i not in syn30 and meta30[i]['has_code']]; assert len(ids207) == 207
    S5 = json.load(open(R6 / 'scores_test_v5.json', encoding='utf-8')); S30 = json.load(open(R6 / 'scores_test_v30.json', encoding='utf-8')); SS = json.load(open(R6 / 'scores_supp.json', encoding='utf-8'))
    P = {(v, s, k, c): {r['id']: r for r in rd(pred_path(v, s, k, c))} for v in VERS for s in SEEDS for k, c in KINDS}
    for k, c in KINDS: P[('base14b', 0, k, c)] = {r['id']: r for r in rd(pred_path('base14b', 0, k, c))}
    A = dict(definition=__doc__, criteria=CRIT)

    # ---- 1. headline --------------------------------------------------------------------------------------------
    def s5(m, cond): return [r for r in S5 if r['condition'] == cond and r['model'].startswith(m)]
    def s30(m, cond): return [r for r in S30 if r['eval_def'] == 'v2' and r['condition'] == cond and r['model'].startswith(m)]
    def ssp(m, cond): return [r for r in SS if r['condition'] == cond and r['model'].startswith(m)]
    def pub35(ver, seed):
        pr = P[(ver, seed, 'test_v30', 'oas_code')]
        den = [i for i in ids207 if meta30[i]['security_state'] == 'declared' and meta30[i]['label'] != 'public']; assert len(den) == 35
        return [i for i in den if lab(pr[i]) == 'public']
    head = {}
    for ver, m, seeds in (('v5', 'lora_v5_s', SEEDS), ('v6c', 'lora_v6c_s', SEEDS), ('base14b', 'base_qwen14b_runpod', [0]), ('base7b', 'base_qwen_runpod', [0])):
        a = s5(m, 'oas_code'); b = s30(m, 'oas_code'); pub = {s: pub35(ver, s) for s in seeds} if ver in ('v5', 'v6c', 'base14b') else {}
        h = dict(test_v5=dict(macro_f1=[r['macro_f1'] for r in a], accuracy=[r['accuracy'] for r in a], manual=[r['manual_ratio'] for r in a], errors=[r['output_errors'] for r in a],
                              per_label={l: [r['per_label'][l]['f1'] for r in a] for l in L}, per_label_pr={l: [(r['per_label'][l]['precision'], r['per_label'][l]['recall']) for r in a] for l in L},
                              per_project={p: [r['per_project'][p]['accuracy'] for r in a] for p in ('rocketchat', 'ghost', 'umami')}, manual_count=[int(round(r['manual_ratio'] * 283)) for r in a]),
                 test_v5_oas=dict(macro_f1=[r['macro_f1'] for r in s5(m, 'oas')], accuracy=[r['accuracy'] for r in s5(m, 'oas')], manual=[r['manual_ratio'] for r in s5(m, 'oas')], errors=[r['output_errors'] for r in s5(m, 'oas')]))
        if b:
            h['test_v30_207'] = dict(macro_f1=[r['main_excl_synthetic']['macro_f1'] for r in b], macro_f1_265=[r['main']['macro_f1'] for r in b], accuracy=[r['main_excl_synthetic']['accuracy'] for r in b],
                                     precision=[r['main_excl_synthetic']['concrete']['precision'] for r in b], recall=[r['main_excl_synthetic']['concrete']['recall'] for r in b], answer_rate=[r['main_excl_synthetic']['concrete']['answer_rate'] for r in b],
                                     manual=[r['main_excl_synthetic']['manual_ratio'] for r in b], errors=[r['main_excl_synthetic']['output_errors'] for r in b], per_label={l: [r['main_excl_synthetic']['per_label'][l]['f1'] for r in b] for l in L},
                                     public_misjudge_35=[len(pub[s]) for s in seeds], public_ids={str(s): pub[s] for s in seeds})
            h['test_v30_oas'] = dict(macro_f1_160=[r['main']['macro_f1'] for r in s30(m, 'oas')], macro_f1_102=[r['main_excl_synthetic']['macro_f1'] for r in s30(m, 'oas')], precision=[r['main']['concrete']['precision'] for r in s30(m, 'oas')],
                                     manual=[r['main']['manual_ratio'] for r in s30(m, 'oas')], errors=[r['main']['output_errors'] for r in s30(m, 'oas')], public_misjudge=[r['public_misjudge_new']['count'] for r in s30(m, 'oas')])
        if ssp(m, 'oas_code'):
            h['supp'] = {c: dict(macro_f1=[r['macro_f1'] for r in ssp(m, c)], accuracy=[r['accuracy'] for r in ssp(m, c)], manual=[r['manual_ratio'] for r in ssp(m, c)], errors=[r['output_errors'] for r in ssp(m, c)],
                                 per_label={l: [r['per_label'][l]['f1'] for r in ssp(m, c)] for l in L}, per_project={p: [r['per_project'][p]['accuracy'] for r in ssp(m, c)] for p in ssp(m, c)[0]['per_project']}) for c in ('oas_code', 'oas')}
        head[ver] = h
    A['headline'] = head
    c1 = st.mean(head['v6c']['test_v5']['macro_f1']) - st.mean(head['v5']['test_v5']['macro_f1']); c2 = st.mean(head['v5']['test_v30_207']['precision']) - st.mean(head['v6c']['test_v30_207']['precision']); c3 = st.mean(head['v6c']['test_v30_207']['public_misjudge_35'])
    A['verdict'] = dict(c1_macro_f1_delta=round(c1, 4), c1_pass=c1 >= CRIT['macro_f1_gain'], c2_precision_drop=round(c2, 4), c2_pass=c2 <= CRIT['precision_drop'], c3_public_misjudge_mean=round(c3, 2), c3_pass=c3 <= CRIT['public_misjudge_max'])
    A['verdict']['adopt'] = all(A['verdict'][k] for k in ('c1_pass', 'c2_pass', 'c3_pass'))
    A['early_gate'] = json.load(open(R6 / 'lora_v6c_s42/eval/early_gate.json', encoding='utf-8'))

    # ---- 2. transitions v5 -> v6c (test_v5 oas_code, same seed) -------------------------------------------------
    trans = {}; manual_by_truth = {}; disagree_pairs = Counter(); n_disagree = 0; n_all_three = 0
    for s in SEEDS:
        a = P[('v5', s, 'test_v5', 'oas_code')]; b = P[('v6c', s, 'test_v5', 'oas_code')]
        pairs = Counter((lab(a[i]), lab(b[i])) for i in t5 if lab(a[i]) != lab(b[i])); trans[str(s)] = {f'{x}->{y}': n for (x, y), n in pairs.most_common()}
        manual_by_truth[str(s)] = dict(Counter(t5[i]['label'] for i in t5 if lab(a[i]) != MANUAL and lab(b[i]) == MANUAL))
        trans[str(s) + '_fixed'] = sum(lab(a[i]) != t5[i]['label'] and lab(b[i]) == t5[i]['label'] for i in t5); trans[str(s) + '_newly_wrong'] = sum(lab(a[i]) == t5[i]['label'] and lab(b[i]) != t5[i]['label'] for i in t5)
    for i in t5:
        ls = [lab(P[('v6c', s, 'test_v5', 'oas_code')][i]) for s in SEEDS]
        if len(set(ls)) > 1:
            n_disagree += 1; n_all_three += len(set(ls)) == 3
            for x, y in {tuple(sorted(p)) for p in [(ls[0], ls[1]), (ls[0], ls[2]), (ls[1], ls[2])] if p[0] != p[1]}: disagree_pairs[f'{x}|{y}'] += 1
    v5_dis = sum(len({lab(P[('v5', s, 'test_v5', 'oas_code')][i]) for s in SEEDS}) > 1 for i in t5)
    A['transitions'] = dict(v5_to_v6c=trans, new_manual_by_truth=manual_by_truth, v6c_seed_disagree_records=n_disagree, v6c_all_three_differ=n_all_three, v5_seed_disagree_records=v5_dis, v6c_disagree_pairs=dict(disagree_pairs.most_common()))
    A['v6c_confusion_mean'] = {a_: {b_: round(st.mean([r['confusion'][a_][b_] for r in s5('lora_v6c_s', 'oas_code')]), 1) for b_ in L + ['output_error']} for a_ in L}
    A['v5_confusion_mean'] = {a_: {b_: round(st.mean([r['confusion'][a_][b_] for r in s5('lora_v5_s', 'oas_code')]), 1) for b_ in L + ['output_error']} for a_ in L}

    # ---- 3. S1-3 disagreement records -----------------------------------------------------------------------------
    A['s13'] = [dict(id=i, type=ty, project=t5[i]['meta']['project'], method=t5[i]['method'], path=t5[i]['path'], truth=t5[i]['label'], v5=[lab(P[('v5', s, 'test_v5', 'oas_code')][i]) for s in SEEDS], v6c=[lab(P[('v6c', s, 'test_v5', 'oas_code')][i]) for s in SEEDS]) for i, ty in S13]
    by_type = defaultdict(lambda: dict(n=0, v5_correct=0, v6c_correct=0))
    for r in A['s13']:
        d = by_type[r['type']]; d['n'] += 1; d['v5_correct'] += sum(x == r['truth'] for x in r['v5']); d['v6c_correct'] += sum(x == r['truth'] for x in r['v6c'])
    A['s13_by_type'] = dict(by_type)

    # ---- 4. output errors, length, time, environment ---------------------------------------------------------------
    errs = {}; lens = {}; times = {}
    for ver in VERS + ('base14b',):
        for s in (SEEDS if ver != 'base14b' else [0]):
            for k, c in KINDS:
                rows = list(P[(ver, s, k, c)].values()); key = f'{ver}_s{s}_{k}_{c}'; e = [r for r in rows if not r.get('prediction')]; new = ver != 'v5'
                errs[key] = dict(n=len(e), han=sum(bool(HAN.search(r['raw'] or '')) for r in e), hit_max=sum((r.get('output_tokens') or 0) >= 256 for r in e) if new else None,
                                 examples=[dict(id=r['id'], truth=r['label'], output_tokens=r.get('output_tokens'), raw=(r['raw'] or '')[:120]) for r in e[:3]])
                lens[key] = dict(raw_chars_mean=round(st.mean(len(r['raw'] or '') for r in rows), 1), raw_chars_max=max(len(r['raw'] or '') for r in rows),
                                 output_tokens_mean=round(st.mean(r['output_tokens'] for r in rows), 1) if new else None, output_tokens_max=max(r['output_tokens'] for r in rows) if new else None,
                                 prompt_tokens_mean=round(st.mean(r['prompt_tokens'] for r in rows), 1) if new else None, prompt_tokens_max=max(r['prompt_tokens'] for r in rows) if new else None)
                times[key] = dict(inference_ms_mean=round(st.mean(r['inference_ms'] for r in rows), 1), inference_ms_sum_s=round(sum(r['inference_ms'] for r in rows) / 1000, 1))
                if new:
                    tj = json.load(open(str(pred_path(ver, s, k, c)) + '.timing.json', encoding='utf-8')); times[key].update(wall_s=tj['inference_wall_s'], mean_ms_per_row=tj['mean_ms_per_row'], hit_max_new_tokens=tj['hit_max_new_tokens'], truncated_prompts=tj['truncated_prompts'], gpu_peak_gib=tj['gpu_memory']['peak_allocated_gib'])
    A['errors'] = errs; A['lengths'] = lens; A['times'] = times
    env = {str(s): json.load(open(R6 / f'lora_v6c_s{s}/env.json', encoding='utf-8')) for s in SEEDS}; env5 = json.load(open(R5 / 'lora_v5_s42/env.json', encoding='utf-8'))
    tr = {}; tr5 = {}
    for s in SEEDS:
        j = json.load(open(R6 / f'lora_v6c_s{s}/logs/train_result.json', encoding='utf-8')); tr[str(s)] = dict(steps=j['steps'], minutes=j['minutes'], train_loss=round(j['train_loss'], 4), val_oas_final=round(j['eval_loss_by_condition']['oas'][-1][1], 4), val_oas_code_final=round(j['eval_loss_by_condition']['oas_code'][-1][1], 4), val_oas_min=round(min(v for _, v in j['eval_loss_by_condition']['oas']), 4), val_oas_code_min=round(min(v for _, v in j['eval_loss_by_condition']['oas_code']), 4), gpu=j['gpu_memory'], trainable=j['trainable_params'], padding_free=j.get('padding_free'))
        j = json.load(open(R5 / f'lora_v5_s{s}/logs/train_result.json', encoding='utf-8')); tr5[str(s)] = dict(steps=j['steps'], minutes=j['minutes'], train_loss=round(j['train_loss'], 4), val_oas_final=round(j['eval_loss_by_condition']['oas'][-1][1], 4), val_oas_code_final=round(j['eval_loss_by_condition']['oas_code'][-1][1], 4))
        log = (R6 / f'lora_v6c_s{s}/logs/run.log').read_text(encoding='utf-8', errors='replace'); m = re.search(r'loss mask check \(row 0\): (\d+)/(\d+) tokens masked \(-100\), (\d+) assistant tokens in loss', log); tr[str(s)]['mask_row0'] = m.group(0) if m else None
    assert len({tr[str(s)]['mask_row0'] for s in SEEDS}) == 1 and tr['42']['mask_row0'], tr
    A['env'] = dict(v6c=env, v5_s42=env5); A['train'] = dict(v6c=tr, v5=tr5); A['config_v6c'] = json.load(open(R6 / 'lora_v6c_s42/config.json', encoding='utf-8')); A['preflight'] = json.load(open(R6 / 'lora_v6c_s42/logs/preflight.json', encoding='utf-8'))
    runlog = (R6 / 'run_v6c.log').read_text(encoding='utf-8', errors='replace'); marks = re.findall(r'^=== (\S+) (.*)$', runlog, re.M); A['run_marks'] = [f'{a} {b}' for a, b in marks]
    zp = Path('<USERPROFILE>/Downloads/BLADE_lora_v6c_export.zip'); A['files'] = dict(zip_sha256=sha(zp) if zp.exists() else None, sums=(R6 / 'SHA256SUMS_blade_v6c').read_text(encoding='utf-8').strip().splitlines())
    (R6 / 'analysis.json').write_text(json.dumps(A, ensure_ascii=False, indent=1), encoding='utf-8', newline='\n')
    write_report(A)


def write_report(A):
    H = A['headline']; V = A['verdict']; v5, v6, b14, b7 = H['v5'], H['v6c'], H['base14b'], H['base7b']; G = A['early_gate']
    o = []; w = o.append
    w('# S8 LoRA v6c 보고 — 베이스 모델만 14B로 교체 (2026-11-05, 3 seed + base 14B zero-shot, 커밋 없음)\n')
    w('사전 기록 AGENTS.md "작업 S8". 변경은 베이스 모델 하나뿐(`unsloth/Qwen2.5-7B-Instruct-bnb-4bit` → `unsloth/Qwen2.5-14B-Instruct-bnb-4bit`): 데이터 data-v5 train/val(해시 게이트), 프롬프트 v3.0.1, 출력 순서(label 먼저), max_seq_len 4096, max_new_tokens 256, LoRA r16·α16·3 epoch·lr 2e-4·cosine·adamw_8bit·batch 2×4, completion-only 마스킹, greedy 디코딩은 v5와 동일. 판정셋 test_v5 283(dev, oas_code) + 회귀 test_v30 oas_code 합성 제외 207, 보조 test_v31_supp 222. v5 수치는 reports/eval/lora_v5의 기존 예측을 같은 채점기로 재채점한 값(재추론 없음). test_v6은 추론하지 않았다. 주지표·발표 수치(v5)는 바꾸지 않는다.\n')
    w(f"## 1. 판정 — 기준 (1) 미달, **불채택** (v5가 최종 모델, S9 대상)\n")
    w('| 기준(3 seed 평균) | v5 | v6c | 차이 | 기준 | 충족 |\n|---|---:|---:|---:|---|---|')
    w(f"| (1) test_v5 oas_code macro-F1 상승 ≥ 0.016 | {ms(v5['test_v5']['macro_f1'])} | {ms(v6['test_v5']['macro_f1'])} | {V['c1_macro_f1_delta']:+.3f} | ≥ +0.016 | {'예' if V['c1_pass'] else '**아니오**'} |")
    w(f"| (2) test_v30 207 구체 정밀도 하락 ≤ 0.025 | {ms(v5['test_v30_207']['precision'])} | {ms(v6['test_v30_207']['precision'])} | {-V['c2_precision_drop']:+.3f} | 하락 ≤ 0.025 | {'예' if V['c2_pass'] else '**아니오**'} |")
    w(f"| (3) test_v30 207 public 오판(/35) 평균 ≤ 2.0 | {' / '.join(map(str, v5['test_v30_207']['public_misjudge_35']))} (평균 {st.mean(v5['test_v30_207']['public_misjudge_35']):.2f}) | {' / '.join(map(str, v6['test_v30_207']['public_misjudge_35']))} (평균 {V['c3_public_misjudge_mean']:.2f}) | {V['c3_public_misjudge_mean'] - st.mean(v5['test_v30_207']['public_misjudge_35']):+.2f} | ≤ 2.0 | {'예' if V['c3_pass'] else '**아니오**'} |")
    w(f"\n- 조기 판정(Pod, early_gate.json): v6c s42 test_v5 macro-F1 {G['v6c_s42']['macro_f1']} > v5 s42 {G['v5_s42']['macro_f1']} → PASS(+{G['delta_macro_f1']}), s43·s44·base zero-shot을 실행했다. 그러나 3 seed 평균은 v5와 같은 수준이고(seed별 {' / '.join(f'{x:.3f}' for x in v6['test_v5']['macro_f1'])} vs v5 {' / '.join(f'{x:.3f}' for x in v5['test_v5']['macro_f1'])}) 차이가 사전 기준 +0.016은 물론 seed 표준편차보다 작다. (2)·(3)은 충족(정밀도 소폭 상승, public 오판 감소)이지만 세 조건을 모두 충족해야 채택이다.")
    w('- 사전 기록대로 **v5를 최종 모델로 확정한다(S9 대상)**. 14B 채택 시 필요했던 GGUF 병합 Pod 요건(RAM ≥ 80 GB, 디스크 ≥ 120 GB)·로컬 CPU 추론 2배 지연은 해당 없다.\n')
    w('## 2. 실행 환경·학습\n')
    e = A['env']['v6c']['42']; e5 = A['env']['v5_s42']; pf = A['preflight']
    w(f"- Pod: RunPod zra2rcdj6gbixh, {e['gpu']} {e['vram_gb']} GB, torch {e['torch']}(CUDA {e['cuda']}), transformers {e['transformers']}, trl {e['trl']}, peft {e['peft']}, unsloth {e['unsloth']}, python {e['python']}. 2026-11-04 14:49 UTC 시작 → 11-05 00:32 UTC 종료(9시간 43분: 설치·preflight·seed 3개·base zero-shot 포함), 번들 blade_v6c_20261104.tgz(`7ff02800…`), 해시 게이트(data_v5_hashes.json `39c302c5…`, test_v5_manifest `57fd384f…`, 프롬프트 `d0913c27…`) 통과, Pod 자동 정지. 회수 zip BLADE_lora_v6c_export.zip SHA-256 `{(A['files']['zip_sha256'] or '')[:16]}…`, 결과 tar 해시는 SHA256SUMS_blade_v6c와 일치.")
    w(f"- v5 환경(비교): {e5.get('gpu')}, torch {e5.get('torch')}, transformers {e5.get('transformers')}, unsloth {e5.get('unsloth')}. 이번 Pod도 unsloth가 'Padding-free batching'을 자동으로 켰다(S5와 같음, v5 로그에는 없음). preflight: 14B 4bit 로드(48층·hidden 5120 확인), 짧은 generate 파싱 성공, 메모리 {pf['gpu_memory']['peak_allocated_gib']} GiB.")
    w(f"- 손실 마스킹(completion-only): 0번 행 `{A['train']['v6c']['42']['mask_row0']}` (3 seed 동일, v5 run_train.py 119행과 같은 train_on_responses_only 호출). trainable 파라미터 {A['train']['v6c']['42']['trainable']:,}(v5 7B 로그에는 기록 없음).")
    w('\n| run | steps | 학습 분 | train_loss | val oas loss(final / 최저) | val oas_code loss(final / 최저) | 학습 피크 GiB(alloc / reserved) | v5 같은 seed train_loss / val final(oas, oas_code) / 분 |\n|---|---:|---:|---:|---|---|---|---|')
    for s in map(str, SEEDS):
        t = A['train']['v6c'][s]; t5_ = A['train']['v5'][s]
        w(f"| lora_v6c_s{s} | {t['steps']} | {t['minutes']} | {t['train_loss']} | {t['val_oas_final']} / {t['val_oas_min']} | {t['val_oas_code_final']} / {t['val_oas_code_min']} | {t['gpu']['peak_allocated_gib']} / {t['gpu']['peak_reserved_gib']} | {t5_['train_loss']} / {t5_['val_oas_final']}, {t5_['val_oas_code_final']} / {t5_['minutes']} |")
    w('\n세 seed 모두 480 step 완주, 발산 없음. val은 학습 정상 여부 확인용이며 체크포인트 선택에 쓰지 않았다(final 고정). 학습 시간은 seed당 132분으로 7B(A100 56분)의 2.4배다. val loss는 v5보다 조금 낮다(final oas 0.235 vs 0.248, oas_code 0.12 vs 0.14 수준)이나 test 지표 차이로 이어지지 않았다(3절).\n')
    w('## 3. test_v5 283 (dev) — oas_code\n')
    w('| 모델 | macro-F1 | 정확도 | manual 비율 | manual 건수(seed별) | 출력 오류(합) |\n|---|---:|---:|---:|---|---:|')
    for ver, nm in (('v5', 'lora_v5 (7B)'), ('v6c', 'lora_v6c (14B)'), ('base14b', 'base Qwen2.5-14B zero-shot'), ('base7b', 'base Qwen2.5-7B zero-shot')):
        h = H[ver]['test_v5']; w(f"| {nm} | {ms(h['macro_f1'])} | {ms(h['accuracy'])} | {ms(h['manual'], pct=True)} | {' / '.join(map(str, h['manual_count']))} | {sum(h['errors'])} |")
    w('\n### label별 F1 (support)\n')
    sup = {l: [r for r in json.load(open(R6 / 'scores_test_v5.json', encoding='utf-8')) if r['condition'] == 'oas_code'][0]['per_label'][l]['support'] for l in L}
    w('| 모델 | ' + ' | '.join(f'{l} ({sup[l]})' for l in L) + ' |\n|---|' + '---:|' * len(L))
    for ver, nm in (('v5', 'lora_v5'), ('v6c', 'lora_v6c'), ('base14b', 'base 14B')): w(f'| {nm} | ' + ' | '.join(ms(H[ver]['test_v5']['per_label'][l]) for l in L) + ' |')
    w('\n### 판정 label 정밀도 / 재현율 (seed별)\n\n| run | owner_or_admin P / R / F1 | membership_required P / R / F1 | role_required P / R / F1 | public P / R / F1 | manual P / R / F1 |\n|---|---|---|---|---|---|')
    for ver in VERS:
        for k, s in enumerate(SEEDS):
            cells = []
            for l in ('owner_or_admin', 'membership_required', 'role_required', 'public', MANUAL):
                p, r = H[ver]['test_v5']['per_label_pr'][l][k]; f = H[ver]['test_v5']['per_label'][l][k]; cells.append(f'{p:.3f} / {r:.3f} / {f:.3f}')
            w(f'| lora_{ver}_s{s} | ' + ' | '.join(cells) + ' |')
    w('\n### 프로젝트별 정확도\n\n| 모델 | rocketchat (157) | ghost (69) | umami (57) |\n|---|---:|---:|---:|')
    for ver, nm in (('v5', 'lora_v5'), ('v6c', 'lora_v6c'), ('base14b', 'base 14B')): w(f"| {nm} | " + ' | '.join(ms(H[ver]['test_v5']['per_project'][p]) for p in ('rocketchat', 'ghost', 'umami')) + ' |')
    w('\n### 혼동표 (정답 행 → 예측 열, 3 seed 평균 건수)\n')
    w('| 정답 \\ 예측 | ' + ' | '.join(SHORT[l] for l in L + ['output_error']) + ' |\n|---|' + '---:|' * 8)
    for a in L:
        if not sup[a]: continue
        w(f'| **{SHORT[a]}** (v5) | ' + ' | '.join(str(A['v5_confusion_mean'][a][b]) for b in L + ['output_error']) + ' |')
        w(f'| {SHORT[a]} (v6c) | ' + ' | '.join(str(A['v6c_confusion_mean'][a][b]) for b in L + ['output_error']) + ' |')
    w('\n### oas(명세만) 보조\n\n| 모델 | macro-F1 | 정확도 | manual 비율 | 출력 오류(합) |\n|---|---:|---:|---:|---:|')
    for ver, nm in (('v5', 'lora_v5'), ('v6c', 'lora_v6c'), ('base14b', 'base 14B')):
        h = H[ver]['test_v5_oas']; w(f"| {nm} | {ms(h['macro_f1'])} | {ms(h['accuracy'])} | {ms(h['manual'], pct=True)} | {sum(h['errors'])} |")
    w('\n원자료 scores_test_v5.json, eval_test_v5.md(scripts/eval_test_v5.py, manifest 해시 검증).\n')
    w('## 4. test_v30 회귀 — oas_code 합성 제외 207 (주지표 조건)\n')
    w('| 모델 | macro-F1(207) | macro-F1(265) | 정확도 | 구체 정밀도 | 구체 재현율 | 구체 응답률 | manual 비율 | public 오판(신, /35, seed별) | 출력 오류(seed별) |\n|---|---:|---:|---:|---:|---:|---:|---:|---|---|')
    for ver, nm in (('v5', 'lora_v5'), ('v6c', 'lora_v6c'), ('base14b', 'base 14B')):
        h = H[ver]['test_v30_207']; w(f"| {nm} | {ms(h['macro_f1'])} | {ms(h['macro_f1_265'])} | {ms(h['accuracy'])} | {ms(h['precision'])} | {ms(h['recall'])} | {ms(h['answer_rate'])} | {ms(h['manual'], pct=True)} | {' / '.join(map(str, h['public_misjudge_35']))} | {' / '.join(map(str, h['errors']))} |")
    w('\n| 모델 | ' + ' | '.join(f'{l}' for l in L if l not in ('membership_required', 'tenant_match')) + ' |\n|---|' + '---:|' * 5)
    for ver, nm in (('v5', 'lora_v5'), ('v6c', 'lora_v6c'), ('base14b', 'base 14B')): w(f'| {nm} | ' + ' | '.join(ms(H[ver]['test_v30_207']['per_label'][l]) for l in L if l not in ('membership_required', 'tenant_match')) + ' |')
    w('\npublic 오판 id(v6c): ' + '; '.join(f"s{s}: {', '.join(v6['test_v30_207']['public_ids'][str(s)])}" for s in SEEDS) + f". v5: {'; '.join(f'''s{s}: {', '.join(v5['test_v30_207']['public_ids'][str(s)])}''' for s in SEEDS)}.")
    w('\n14B는 보류가 줄고(manual 28% → 20%) 응답한 것의 정밀도도 소폭 올랐다. public 오판은 줄었다. 회귀 기준 (2)·(3)은 충족이다.\n')
    w('### oas(명세만) 160\n\n| 모델 | macro-F1(160) | 합성 제외 102 | 구체 정밀도 | manual 비율 | public 오판(신) | 출력 오류 |\n|---|---:|---:|---:|---:|---|---|')
    for ver, nm in (('v5', 'lora_v5'), ('v6c', 'lora_v6c'), ('base14b', 'base 14B')):
        h = H[ver]['test_v30_oas']; w(f"| {nm} | {ms(h['macro_f1_160'])} | {ms(h['macro_f1_102'])} | {ms(h['precision'])} | {ms(h['manual'], pct=True)} | {' / '.join(map(str, h['public_misjudge']))} | {' / '.join(map(str, h['errors']))} |")
    w('\n원자료 scores_test_v30.json, eval_v30.md(scripts/eval_v30.py --eval-def both).\n')
    w('## 5. test_v31_supp 222 (보조 조건)\n')
    w('| 모델 | oas_code macro-F1 | oas_code 정확도 | oas_code manual | oas macro-F1 | oas 정확도 | oas manual |\n|---|---:|---:|---:|---:|---:|---:|')
    for ver, nm in (('v5', 'lora_v5'), ('v6c', 'lora_v6c'), ('base14b', 'base 14B')):
        h = H[ver]['supp']; w(f"| {nm} | {ms(h['oas_code']['macro_f1'])} | {ms(h['oas_code']['accuracy'])} | {ms(h['oas_code']['manual'], pct=True)} | {ms(h['oas']['macro_f1'])} | {ms(h['oas']['accuracy'])} | {ms(h['oas']['manual'], pct=True)} |")
    w('\n| 모델 | ' + ' | '.join(L) + ' |\n|---|' + '---:|' * 7)
    for ver, nm in (('v5', 'lora_v5'), ('v6c', 'lora_v6c')): w(f'| {nm} (oas_code F1) | ' + ' | '.join(ms(H[ver]['supp']['oas_code']['per_label'][l]) for l in L) + ' |')
    pj = list(H['v5']['supp']['oas_code']['per_project'])
    w('\n| 모델 | ' + ' | '.join(pj) + ' |\n|---|' + '---:|' * len(pj))
    for ver, nm in (('v5', 'lora_v5'), ('v6c', 'lora_v6c')): w(f'| {nm} (oas_code 정확도) | ' + ' | '.join(ms(H[ver]['supp']['oas_code']['per_project'][p]) for p in pj) + ' |')
    w('\nsupp oas_code macro-F1은 평균이 오르지만 seed 편차(s43만 0.598)가 커서 차이로 인정하지 않는다. 원자료 scores_supp.json, eval_supp.md(scripts/eval_v31_supp.py).\n')
    w('## 6. 예측 변화 v5 → v6c (test_v5 oas_code, 같은 seed)\n')
    T = A['transitions']
    w('| seed | 고쳐짐(v5 오답→v6c 정답) | 새로 틀림(v5 정답→v6c 오답) | 바뀐 전이 상위 |\n|---|---:|---:|---|')
    for s in map(str, SEEDS):
        top = ', '.join(f"{SHORT[k.split('->')[0]]}→{SHORT[k.split('->')[1]]} {n}" for k, n in list(T['v5_to_v6c'][s].items())[:6]); w(f"| s{s} | {T['v5_to_v6c'][s + '_fixed']} | {T['v5_to_v6c'][s + '_newly_wrong']} | {top} |")
    w('\n새로 manual이 된 건(v5 구체 → v6c manual)의 정답 label:\n\n| seed | ' + ' | '.join(SHORT[l] for l in L) + ' |\n|---|' + '---:|' * 7)
    for s in map(str, SEEDS): w(f'| s{s} | ' + ' | '.join(str(T['new_manual_by_truth'][s].get(l, 0)) for l in L) + ' |')
    w(f"\nseed 간 예측이 갈린 레코드: v6c {T['v6c_seed_disagree_records']}/283(세 seed 모두 다름 {T['v6c_all_three_differ']}), v5 {T['v5_seed_disagree_records']}/283. v6c에서 갈린 label 쌍: " + ', '.join(f"{SHORT[k.split('|')[0]]}|{SHORT[k.split('|')[1]]} {n}" for k, n in list(T['v6c_disagree_pairs'].items())[:8]) + '.')
    w('\n고쳐진 건과 새로 틀린 건이 seed마다 비슷한 수로 맞물려 순효과가 없다. 14B가 특정 경계(membership·owner_or_admin·manual)를 더 잘 푸는 증거는 없다.\n')
    w('## 7. S1-3 불일치 12건에서의 예측 (v5 → v6c, seed 42/43/44)\n')
    w('| id | 유형 | method path | 정답 | v5 s42/43/44 | v6c s42/43/44 |\n|---|---|---|---|---|---|')
    for r in A['s13']: w(f"| {r['id']} | {r['type']} | {r['method']} {r['path']} | {SHORT[r['truth']]} | {' / '.join(SHORT[x] for x in r['v5'])} | {' / '.join(SHORT[x] for x in r['v6c'])} |")
    w('\n| 유형 | 건수 | v5 정답(3 seed 합 / 가능) | v6c 정답(3 seed 합 / 가능) |\n|---|---:|---:|---:|')
    for ty, d in A['s13_by_type'].items(): w(f"| {ty} | {d['n']} | {d['v5_correct']} / {d['n'] * 3} | {d['v6c_correct']} / {d['n'] * 3} |")
    w(f"\n12건 합계 v5 {sum(d['v5_correct'] for d in A['s13_by_type'].values())}/36 → v6c {sum(d['v6c_correct'] for d in A['s13_by_type'].values())}/36. 이 12건은 라벨 정의(G3-a 등)가 학습 데이터와 어긋나는 경계라 베이스 크기로는 풀리지 않는다(작업 C′의 대상).\n")
    w('## 8. 출력 오류·출력 길이·추론 시간\n')
    E, LN, TM = A['errors'], A['lengths'], A['times']
    w('| 셋·조건 | v5 출력 오류(s42/43/44) | v6c 출력 오류(s42/43/44) | v6c 오류 중 중국어 혼입 | base 14B 오류 | v6c 출력 토큰 평균/최대(s42) | 출력 문자 수 평균 v5 → v6c(s42) | v6c 프롬프트 토큰 평균/최대 |\n|---|---|---|---:|---:|---|---|---|')
    for k, c in KINDS:
        k6 = [f'v6c_s{s}_{k}_{c}' for s in SEEDS]; k5 = [f'v5_s{s}_{k}_{c}' for s in SEEDS]; kb = f'base14b_s0_{k}_{c}'
        w(f"| {k} {c} | {' / '.join(str(E[x]['n']) for x in k5)} | {' / '.join(str(E[x]['n']) for x in k6)} | {sum(E[x]['han'] for x in k6)} | {E[kb]['n']} | {LN[k6[0]]['output_tokens_mean']} / {LN[k6[0]]['output_tokens_max']} | {LN[k5[0]]['raw_chars_mean']} → {LN[k6[0]]['raw_chars_mean']} | {LN[k6[0]]['prompt_tokens_mean']} / {LN[k6[0]]['prompt_tokens_max']} |")
    w('\n| 셋·조건 | v5 행당 ms(A100, 7B, s42) | v6c 행당 ms(A100, 14B, s42/43/44) | v6c 벽시계 s(s42) | v6c 평가 피크 GiB(s42) | base 14B 행당 ms | 프롬프트 절단 |\n|---|---:|---|---:|---:|---:|---:|')
    for k, c in KINDS:
        k6 = [f'v6c_s{s}_{k}_{c}' for s in SEEDS]; w(f"| {k} {c} | {TM[f'v5_s42_{k}_{c}']['inference_ms_mean']} | {' / '.join(str(TM[x]['mean_ms_per_row']) for x in k6)} | {TM[k6[0]]['wall_s']} | {TM[k6[0]]['gpu_peak_gib']} | {TM[f'base14b_s0_{k}_{c}']['mean_ms_per_row']} | {sum(TM[x]['truncated_prompts'] for x in k6)} |")
    w('\n행당 ms는 배치 8 기준(배치 벽시계 / 8). 같은 A100에서 14B 추론은 7B의 약 2배다. 출력 오류(JSON 깨짐·7종 밖 label)는 14B에서 test_v5 oas_code 0건, test_v30 oas_code seed당 0~1건으로 v5(seed당 3~5건)보다 적다.\n')
    w('## 9. 해석·한계·다음 단계\n')
    w(f"- **불채택.** 베이스를 14B로 키워도 test_v5 macro-F1은 v5와 같은 수준({ms(v5['test_v5']['macro_f1'])} → {ms(v6['test_v5']['macro_f1'])})이고, 회귀 지표만 소폭 좋아졌다. 학습 데이터(data-v5)와 평가셋 사이의 라벨 정의 차이(S1-4: G3-a 그룹 안 역할, G6-a 복합 OR, G4-c 설정 의존)는 모델 크기로 메워지지 않는다. 사전 기록대로 v5를 최종 모델로 확정하고 S9(test_v6)는 v5로 간다.")
    w(f"- base 14B zero-shot은 base 7B zero-shot보다 크게 낫지만(test_v5 macro-F1 {ms(b7['test_v5']['macro_f1'])} → {ms(b14['test_v5']['macro_f1'])}), LoRA v5(7B)에는 미치지 못한다. 판정에는 쓰지 않았다.")
    w('- 작업 C′(v6d, 학습 정답만 교정)의 베이스는 S8 불채택이므로 7B(`unsloth/Qwen2.5-7B-Instruct-bnb-4bit`)다. 로컬 Ollama의 v4·qwen2.5:7b 부재(prep.md)는 S9 이후 배포 정리 때 복구한다.')
    w('- 산출물: 예측·로그 reports/eval/lora_v6c/{lora_v6c_s42,43,44,base_qwen14b_runpod}/, run_v6c.log, SHA256SUMS_blade_v6c(어댑터 tar 3개 ≈ 257 MB씩은 git 밖, 로컬 zip BLADE_lora_v6c_export.zip), 채점 scores_test_v5.json·eval_test_v5.md·scores_test_v30.json·eval_v30.md·scores_supp.json·eval_supp.md, 분석 analysis.json(scripts/analyze_lora_v6c.py). 커밋하지 않았다. 주지표·발표 수치(v5) 불변, test_v6 추론 없음.')
    (R6 / 'report.md').write_text('\n'.join(o) + '\n', encoding='utf-8', newline='\r\n')


if __name__ == '__main__': main()
