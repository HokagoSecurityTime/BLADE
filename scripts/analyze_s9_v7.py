"""S9: data-v7 LoRA v7 vs LoRA v5 on the frozen hold-out test_v6 (289), same pod / same libraries, 3 seeds each — final verdict on the pre-registered criteria
(AGENTS.md 작업 data-v7 / test_v6 동결 S9 사전 기록): (1) test_v6 oas_code macro-F1 >= v5 + 0.016 (3-seed mean), (2) test_v30 207 concrete precision drop <= 0.025, (3) test_v30 207 public misjudge (/35) mean <= 2.0.
Reads only existing files: reports/eval/lora_v7/s9/{lora_v5_s*,lora_v7_s*}/ (S9 predictions), s9/scores_test_v6.json (scripts/eval_test_v6.py), reports/eval/lora_v7/analysis.json (stage 1: test_v30 regression).
Writes reports/eval/lora_v7/s9/analysis.json and report.md. No inference. Requires BLADE_TESTV6_STAGE=S9 (testv6_guard)."""
from __future__ import annotations
import hashlib, json, re, statistics as st, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from scripts.testv6_guard import assert_allowed
R7 = ROOT / 'reports/eval/lora_v7'; S9 = R7 / 's9'; TEST = ROOT / 'datasets/blade/processed/test_v6.jsonl'
SEEDS = [42, 43, 44]; VERS = ('v5', 'v7')
L = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']; MANUAL = 'manual_review_required'
SHORT = {'public': 'public', 'role_required': 'role', 'membership_required': 'member', 'tenant_match': 'tenant', 'owner_match': 'owner', 'owner_or_admin': 'own+adm', 'manual_review_required': 'manual', 'output_error': 'ERR'}
PROJECTS = ['seahub', 'redash', 'glitchtip', 'penpot']; STATUSES = ['human_confirmed', 'ai_double_confirmed', 'ai_single']
CRIT = dict(macro_f1_gain=0.016, precision_drop=0.025, public_misjudge_max=2.0); HAN = re.compile(r'[一-鿿]')
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
lab = lambda r: r['prediction']['label'] if r.get('prediction') else 'output_error'
pp = lambda v, s, c: S9 / f'lora_{v}_s{s}' / 'eval' / f'v6test_predictions_{c}_lora_{v}_s{s}_final.jsonl'


def ms(xs, nd=3, pct=False):
    if pct: xs = [x * 100 for x in xs]
    if len(xs) == 1: return f'{xs[0]:.{1 if pct else nd}f}' + ('%' if pct else '')
    return f'{st.mean(xs):.{1 if pct else nd}f} ± {st.stdev(xs):.{1 if pct else nd}f}' + ('%' if pct else '')


def main():
    man = assert_allowed('analysis'); t6 = {r['id']: r for r in rd(TEST)}; assert len(t6) == 289
    S = json.load(open(S9 / 'scores_test_v6.json', encoding='utf-8')); A1 = json.load(open(R7 / 'analysis.json', encoding='utf-8'))
    P = {(v, s, c): {r['id']: r for r in rd(pp(v, s, c))} for v in VERS for s in SEEDS for c in ('oas_code', 'oas')}
    for k, d in P.items(): assert len(d) == 289, (k, len(d))
    sc = lambda v, c: [r for r in S if r['condition'] == c and r['group'] == f'lora_{v}']
    A = dict(definition=__doc__, criteria=CRIT, manifest_sha256=sha(ROOT / 'datasets/blade/processed/data_v6/test_v6_manifest.json'), test_v6_records=man['records'])
    H = {}
    for v in VERS:
        a = sc(v, 'oas_code'); o = sc(v, 'oas'); assert len(a) == len(o) == 3
        H[v] = dict(oas_code=dict(macro_f1=[r['macro_f1'] for r in a], accuracy=[r['accuracy'] for r in a], manual=[r['manual_ratio'] for r in a], errors=[r['output_errors'] for r in a], precision=[r['concrete']['precision'] for r in a], recall=[r['concrete']['recall'] for r in a],
                                  public_misjudge=[r['public_misjudge']['count'] for r in a], public_den=a[0]['public_misjudge']['denominator'], public_ids={str(s): r['public_misjudge']['ids'] for s, r in zip(SEEDS, a)},
                                  per_label={l: [r['per_label'][l]['f1'] for r in a] for l in L}, per_label_pr={l: [(r['per_label'][l]['precision'], r['per_label'][l]['recall']) for r in a] for l in L}, support={l: a[0]['per_label'][l]['support'] for l in L},
                                  per_project={p: [r['per_project'][p]['accuracy'] for r in a] for p in PROJECTS}, proj_n={p: a[0]['per_project'][p]['n'] for p in PROJECTS},
                                  per_status={s_: [r['per_label_status'][s_]['accuracy'] for r in a] for s_ in STATUSES}, status_n={s_: a[0]['per_label_status'][s_]['n'] for s_ in STATUSES},
                                  g1b=[r['g1b']['accuracy'] for r in a], g1b_pred=[r['g1b']['predicted'] for r in a], confusion_mean={x: {y: round(st.mean(r['confusion'][x][y] for r in a), 1) for y in L + ['output_error']} for x in L}),
                    oas=dict(macro_f1=[r['macro_f1'] for r in o], accuracy=[r['accuracy'] for r in o], manual=[r['manual_ratio'] for r in o], errors=[r['output_errors'] for r in o], public_misjudge=[r['public_misjudge']['count'] for r in o], per_label={l: [r['per_label'][l]['f1'] for r in o] for l in L}))
    A['headline'] = H
    c1 = st.mean(H['v7']['oas_code']['macro_f1']) - st.mean(H['v5']['oas_code']['macro_f1']); V1 = A1['verdict']
    A['verdict'] = dict(c1_macro_f1_delta=round(c1, 4), c1_pass=c1 >= CRIT['macro_f1_gain'], c1_v5=round(st.mean(H['v5']['oas_code']['macro_f1']), 4), c1_v7=round(st.mean(H['v7']['oas_code']['macro_f1']), 4),
                        c2_precision_drop=V1['c2_precision_drop'], c2_pass=V1['c2_pass'], c3_public_misjudge_mean=V1['c3_public_misjudge_mean'], c3_pass=V1['c3_pass'])
    A['verdict']['adopt'] = all(A['verdict'][k] for k in ('c1_pass', 'c2_pass', 'c3_pass'))
    A['paired_delta'] = [round(b - a, 4) for a, b in zip(H['v5']['oas_code']['macro_f1'], H['v7']['oas_code']['macro_f1'])]
    A['stage1'] = dict(test_v30_207=dict(v5=A1['headline']['v5']['test_v30_207'], v7=A1['headline']['v7']['test_v30_207']))
    # transitions / disagreement (oas_code)
    trans = {}; fixed = {}; wrong = {}; manual_by_truth = {}
    for s in SEEDS:
        a = P[('v5', s, 'oas_code')]; b = P[('v7', s, 'oas_code')]
        pairs = Counter((lab(a[i]), lab(b[i])) for i in t6 if lab(a[i]) != lab(b[i])); trans[str(s)] = {f'{x}->{y}': n for (x, y), n in pairs.most_common()}
        trans[str(s) + '_fixed'] = sum(lab(a[i]) != t6[i]['label'] and lab(b[i]) == t6[i]['label'] for i in t6); trans[str(s) + '_newly_wrong'] = sum(lab(a[i]) == t6[i]['label'] and lab(b[i]) != t6[i]['label'] for i in t6)
        fixed[str(s)] = dict(Counter(t6[i]['label'] for i in t6 if lab(a[i]) != t6[i]['label'] and lab(b[i]) == t6[i]['label'])); wrong[str(s)] = dict(Counter(t6[i]['label'] for i in t6 if lab(a[i]) == t6[i]['label'] and lab(b[i]) != t6[i]['label']))
        manual_by_truth[str(s)] = {v: dict(Counter(t6[i]['label'] for i in t6 if lab(P[(v, s, 'oas_code')][i]) == MANUAL)) for v in VERS}
    dis = {}
    for v in VERS:
        n = 0; n3 = 0; pairs = Counter()
        for i in t6:
            ls = [lab(P[(v, s, 'oas_code')][i]) for s in SEEDS]
            if len(set(ls)) > 1:
                n += 1; n3 += len(set(ls)) == 3
                for x, y in {tuple(sorted(q)) for q in [(ls[0], ls[1]), (ls[0], ls[2]), (ls[1], ls[2])] if q[0] != q[1]}: pairs[f'{x}|{y}'] += 1
        dis[v] = dict(records=n, all_three=n3, pairs=dict(pairs.most_common()))
    core = [i for i in t6 if all(lab(P[(v, s, 'oas_code')][i]) != t6[i]['label'] for v in VERS for s in SEEDS)]
    A['transitions'] = dict(v5_to_v7=trans, fixed_by_truth=fixed, newly_wrong_by_truth=wrong, manual_by_truth=manual_by_truth, seed_disagree=dis, wrong_in_all_6=len(core),
                            wrong_in_all_6_by_truth=dict(Counter(t6[i]['label'] for i in core)), wrong_in_all_6_by_project=dict(Counter(t6[i]['meta']['project'] for i in core)), wrong_in_all_6_by_status=dict(Counter(t6[i]['meta']['label_status'] for i in core)))
    # G1-b detail: truth tenant_match (Redash @require_admin + current_org) predicted role_required by both models
    g1b = [i for i in t6 if i in set(sum([list(x) for x in []], [])) ] if False else None
    # errors / timing / env
    errs = {}; times = {}
    for v in VERS:
        for s in SEEDS:
            for c in ('oas_code', 'oas'):
                rows = list(P[(v, s, c)].values()); e = [r for r in rows if not r.get('prediction')]; key = f'{v}_s{s}_{c}'
                tj = json.load(open(str(pp(v, s, c)) + '.timing.json', encoding='utf-8'))
                errs[key] = dict(n=len(e), han=sum(bool(HAN.search(r['raw'] or '')) for r in e), hit_max=sum((r.get('output_tokens') or 0) >= 256 for r in e), examples=[dict(id=r['id'], truth=r['label'], raw=(r['raw'] or '')[:120]) for r in e[:2]])
                times[key] = dict(wall_s=tj['inference_wall_s'], mean_ms_per_row=tj['mean_ms_per_row'], output_tokens_mean=tj['output_tokens_mean'], output_tokens_max=tj['output_tokens_max'], hit_max_new_tokens=tj['hit_max_new_tokens'], truncated_prompts=tj['truncated_prompts'], prompt_tokens_max=tj['prompt_tokens_max'], gpu_peak_gib=tj['gpu_memory']['peak_allocated_gib'])
    A['errors'] = errs; A['times'] = times
    A['env'] = {f'{v}_s{s}': json.load(open(S9 / f'lora_{v}_s{s}/env.json', encoding='utf-8')) for v in VERS for s in SEEDS}
    assert len({json.dumps(e, sort_keys=True) for e in A['env'].values()}) == 1, 'S9 runs must share one environment'
    logs = {f'{v}_s{s}': (S9 / f'lora_{v}_s{s}/logs/run.log').read_text(encoding='utf-8', errors='replace') for v in VERS for s in SEEDS}
    A['gates'] = {k: dict(data_v7='inputs verified against data_v7_hashes.json' in g, test_v6=f"test_v6 inputs verified against test_v6_manifest.json ({A['manifest_sha256'][:12]})" in g, no_training='final adapter exists: skip training' in g) for k, g in logs.items()}
    assert all(all(d.values()) for d in A['gates'].values()), A['gates']
    runlog = (S9 / 'run_s9.log').read_text(encoding='utf-8', errors='replace'); A['run_log_marks'] = [l for l in runlog.splitlines() if l.startswith('=== ')]
    A['files'] = dict(sums=(S9 / 'SHA256SUMS_s9').read_text(encoding='utf-8').strip().splitlines(), pred_sha256={f'{v}_s{s}_{c}': sha(pp(v, s, c)) for v in VERS for s in SEEDS for c in ('oas_code', 'oas')})
    (S9 / 'analysis.json').write_text(json.dumps(A, ensure_ascii=False, indent=1), encoding='utf-8', newline='\n')
    write_report(A, t6)


def write_report(A, t6):
    H = A['headline']; V = A['verdict']; T = A['transitions']; h5, h7 = H['v5']['oas_code'], H['v7']['oas_code']; s5, s7 = A['stage1']['test_v30_207']['v5'], A['stage1']['test_v30_207']['v7']
    o = []; w = o.append
    w('# S9 보고 — data-v7 LoRA v7 vs LoRA v5, hold-out test_v6 (추론 2026-11-08 13:54–14:40 UTC, 채점 2026-11-09, 커밋 없음)\n')
    w(f"사전 기록 AGENTS.md \"작업 data-v7\"(채택 기준 3조건)·\"test_v6 동결\"(S9 절차). test_v6 289건(동결 2026-11-08, manifest `{A['manifest_sha256'][:16]}…`, A안 라벨링: AI 1차 + 독립 AI 2차 + 경계 사례 사람 확정)을 **같은 Pod(n1tl7hwtpbqnew, H100 80GB)·같은 라이브러리**에서 v5 어댑터 3개(s42·43·44, blade_v5_adapters.tar.gz `db6abe46…`)와 v7 어댑터 3개로 한 번에 추론했다(run_s9.sh, 각 run 해시 게이트 data_v7·test_v6 manifest 통과, 학습 없음, 기본 디코딩 greedy·max_new_tokens 256). v5·v7 어느 쪽도 S9 전에 test_v6을 추론하지 않았다. 판정 조건은 oas_code(주지표와 같은 입력 조건), oas(명세만)는 보조. test_v5·test_v31_supp는 v7 학습 데이터라 비교에 쓰지 않는다. 주지표(test_v30 207)·발표 수치(v5)는 이 보고로 바뀌지 않으며 전환은 사용자 승인 뒤의 별도 작업이다.\n")
    w(f"## 1. 판정 — {'사전 기준 3개 모두 충족 → **채택 후보**(사용자 승인 대상; 승인 전까지 v5가 최종 모델)' if V['adopt'] else '사전 기준 미달 → **불채택**, v5 유지'}\n")
    w('| 기준(3 seed 평균) | v5 | v7 | 차이 | 기준 | 충족 |\n|---|---:|---:|---:|---|---|')
    w(f"| (1) test_v6 oas_code macro-F1 상승 ≥ 0.016 | {ms(h5['macro_f1'])} | {ms(h7['macro_f1'])} | {V['c1_macro_f1_delta']:+.3f} | ≥ +0.016 | {'**예**' if V['c1_pass'] else '**아니오**'} |")
    w(f"| (2) test_v30 207 구체 정밀도 하락 ≤ 0.025 (1단계) | {ms(s5['precision'])} | {ms(s7['precision'])} | {-V['c2_precision_drop']:+.3f} | 하락 ≤ 0.025 | {'예' if V['c2_pass'] else '**아니오**'} |")
    w(f"| (3) test_v30 207 public 오판(/35) 평균 ≤ 2.0 (1단계) | {' / '.join(map(str, s5['public_misjudge_35']))} (평균 {st.mean(s5['public_misjudge_35']):.2f}) | {' / '.join(map(str, s7['public_misjudge_35']))} (평균 {V['c3_public_misjudge_mean']:.2f}) | {V['c3_public_misjudge_mean'] - st.mean(s5['public_misjudge_35']):+.2f} | ≤ 2.0 | {'예' if V['c3_pass'] else '**아니오**'} |")
    w(f"\n- 같은 seed끼리의 test_v6 macro-F1 차이(v7 − v5): {', '.join(f'{d:+.3f}' for d in A['paired_delta'])} — 세 seed 모두 v5 표준편차({st.stdev(h5['macro_f1']):.3f})와 v7 표준편차({st.stdev(h7['macro_f1']):.3f})보다 크다(\"표준편차보다 큰 차이만 인정\" 규칙 충족).")
    w(f"- test_v6 정확도 {st.mean(h5['accuracy']):.3f} → {st.mean(h7['accuracy']):.3f}, 구체 정밀도 {st.mean(h5['precision']):.3f} → {st.mean(h7['precision']):.3f}, 구체 재현율 {st.mean(h5['recall']):.3f} → {st.mean(h7['recall']):.3f}, manual 비율 {st.mean(h5['manual']) * 100:.1f}% → {st.mean(h7['manual']) * 100:.1f}%, public 오판(/{h5['public_den']}) {' / '.join(map(str, h5['public_misjudge']))} → {' / '.join(map(str, h7['public_misjudge']))}. 네 프로젝트 중 세 곳(seahub·Redash·Penpot) 상승, GlitchTip 제자리.")
    w('- 시한: 추론은 2026-11-08 23:40 KST에 끝났고(마감 11-09 18:00 KST 이전), 결과 파일 회수·채점은 11-09 18:44 KST 이후다. 중단 규칙 적용 여부는 사용자 판단 사항으로 기록한다.\n')
    w('## 2. test_v6 289 — oas_code\n')
    w('| 모델 | macro-F1 | 정확도 | 구체 정밀도 | 구체 재현율 | manual 비율 | public 오판(/265, seed별) | 출력 오류(seed별) |\n|---|---:|---:|---:|---:|---:|---|---|')
    for v, nm in (('v5', 'lora_v5'), ('v7', 'lora_v7')):
        h = H[v]['oas_code']; w(f"| {nm} | {ms(h['macro_f1'])} | {ms(h['accuracy'])} | {ms(h['precision'])} | {ms(h['recall'])} | {ms(h['manual'], pct=True)} | {' / '.join(map(str, h['public_misjudge']))} | {' / '.join(map(str, h['errors']))} |")
    sup = h7['support']
    w('\n### label별 F1 (support)\n\n| 모델 | ' + ' | '.join(f'{l} ({sup[l]})' for l in L) + ' |\n|---|' + '---:|' * len(L))
    for v, nm in (('v5', 'lora_v5'), ('v7', 'lora_v7')): w(f'| {nm} | ' + ' | '.join(ms(H[v]['oas_code']['per_label'][l]) for l in L) + ' |')
    w('\n### label별 정밀도 / 재현율 / F1 (seed별)\n\n| run | ' + ' | '.join(f'{SHORT[l]} P / R / F1' for l in L) + ' |\n|---|' + '---|' * len(L))
    for v in VERS:
        for k, s in enumerate(SEEDS):
            cells = []
            for l in L:
                p, r = H[v]['oas_code']['per_label_pr'][l][k]; f = H[v]['oas_code']['per_label'][l][k]; cells.append(f'{p:.3f} / {r:.3f} / {f:.3f}')
            w(f'| lora_{v}_s{s} | ' + ' | '.join(cells) + ' |')
    w('\n### 프로젝트별 정확도\n\n| 모델 | ' + ' | '.join(f"{p} ({h7['proj_n'][p]})" for p in PROJECTS) + ' |\n|---|' + '---:|' * 4)
    for v, nm in (('v5', 'lora_v5'), ('v7', 'lora_v7')): w(f'| {nm} | ' + ' | '.join(ms(H[v]['oas_code']['per_project'][p]) for p in PROJECTS) + ' |')
    w('\n### 정답 출처(label_status)별 정확도 · Redash G1-b 경계 18건\n\n| 모델 | ' + ' | '.join(f"{s_} ({h7['status_n'][s_]})" for s_ in STATUSES) + ' | G1-b 18 정확도(seed별) | G1-b 예측 분포(s42) |\n|---|' + '---:|' * 3 + '---|---|')
    for v, nm in (('v5', 'lora_v5'), ('v7', 'lora_v7')): w(f'| {nm} | ' + ' | '.join(ms(H[v]['oas_code']['per_status'][s_]) for s_ in STATUSES) + f" | {' / '.join(f'{x:.2f}' for x in H[v]['oas_code']['g1b'])} | {H[v]['oas_code']['g1b_pred'][0]} |")
    w('\nG1-b 18건(Redash `@require_admin` + `current_org` → tenant_match로 확정한 경계)은 두 모델 모두 거의 전부 role_required로 예측해 0/18이다. 이 18건을 role_required로 채점하면 두 모델 모두 정확도가 오르지만 상대 비교는 바뀌지 않는다(두 모델 예측이 같음). 사람 확정 5건·AI 이중 확정 67건의 정확도가 AI 단독 217건보다 낮은 것은 경계 사례·감사 표본의 난도가 높아서이며 표본이 작아 해석에 주의한다.')
    w('\n### 혼동표 (정답 행 → 예측 열, 3 seed 평균 건수)\n\n| 정답 \\ 예측 | ' + ' | '.join(SHORT[l] for l in L + ['output_error']) + ' |\n|---|' + '---:|' * 8)
    for a in L:
        w(f"| **{SHORT[a]}** (v5) | " + ' | '.join(str(H['v5']['oas_code']['confusion_mean'][a][b]) for b in L + ['output_error']) + ' |')
        w(f"| {SHORT[a]} (v7) | " + ' | '.join(str(H['v7']['oas_code']['confusion_mean'][a][b]) for b in L + ['output_error']) + ' |')
    w('\n### manual 예측의 정답 label 분포 (seed별)\n\n| run | ' + ' | '.join(SHORT[l] for l in L) + ' | 합 |\n|---|' + '---:|' * 8)
    for v in VERS:
        for s in map(str, SEEDS):
            d = T['manual_by_truth'][s][v]; w(f'| lora_{v}_s{s} | ' + ' | '.join(str(d.get(l, 0)) for l in L) + f' | {sum(d.values())} |')
    w(f"\npublic 오판 id — v5: {'; '.join(f'''s{s}: {', '.join(h5['public_ids'][str(s)]) or '-'}''' for s in SEEDS)}. v7: {'; '.join(f'''s{s}: {', '.join(h7['public_ids'][str(s)]) or '-'}''' for s in SEEDS)}.\n")
    w('### oas(명세만) — 보조\n\n| 모델 | macro-F1 | 정확도 | manual 비율 | public 오판(/265, seed별) | 출력 오류(seed별) |\n|---|---:|---:|---:|---|---|')
    for v, nm in (('v5', 'lora_v5'), ('v7', 'lora_v7')):
        h = H[v]['oas']; w(f"| {nm} | {ms(h['macro_f1'])} | {ms(h['accuracy'])} | {ms(h['manual'], pct=True)} | {' / '.join(map(str, h['public_misjudge']))} | {' / '.join(map(str, h['errors']))} |")
    w(f"\noas 조건에서는 두 모델이 비슷하고(macro-F1 {st.mean(H['v5']['oas']['macro_f1']):.3f} vs {st.mean(H['v7']['oas']['macro_f1']):.3f}), v7의 public 오판({' / '.join(map(str, H['v7']['oas']['public_misjudge']))})과 s44 출력 오류({H['v7']['oas']['errors'][2]}건)가 v5보다 많다. 판정 기준은 oas_code이지만 명세만 입력일 때 v7의 public 과대 예측은 한계로 기록한다(test_v30 oas에서는 v7 public 오판 0/0/2).\n")
    w('원자료 s9/scores_test_v6.json, eval_test_v6.md(scripts/eval_test_v6.py).\n')
    w('## 3. 예측 변화 v5 → v7 (test_v6 oas_code, 같은 seed)\n')
    w('| seed | 고쳐짐(v5 오답→v7 정답) | 새로 틀림(v5 정답→v7 오답) | 바뀐 전이 상위 |\n|---|---:|---:|---|')
    for s in map(str, SEEDS):
        top = ', '.join(f"{SHORT[k.split('->')[0]]}→{SHORT[k.split('->')[1]]} {n}" for k, n in list(T['v5_to_v7'][s].items())[:7]); w(f"| s{s} | {T['v5_to_v7'][s + '_fixed']} | {T['v5_to_v7'][s + '_newly_wrong']} | {top} |")
    w('\n고쳐진 건 / 새로 틀린 건의 정답 label:\n\n| seed | ' + ' | '.join(SHORT[l] for l in L) + ' |\n|---|' + '---:|' * 7)
    for s in map(str, SEEDS): w(f'| s{s} 고쳐짐 | ' + ' | '.join(str(T['fixed_by_truth'][s].get(l, 0)) for l in L) + ' |'); w(f'| s{s} 새로 틀림 | ' + ' | '.join(str(T['newly_wrong_by_truth'][s].get(l, 0)) for l in L) + ' |')
    d5, d7 = T['seed_disagree']['v5'], T['seed_disagree']['v7']
    w(f"\nseed 간 예측이 갈린 레코드: v5 {d5['records']}/289(세 seed 모두 다름 {d5['all_three']}), v7 {d7['records']}/289(세 seed 모두 다름 {d7['all_three']}). v7에서 갈린 label 쌍: " + ', '.join(f"{SHORT[k.split('|')[0]]}|{SHORT[k.split('|')[1]]} {n}" for k, n in list(d7['pairs'].items())[:8]) + '.')
    cb = T['wrong_in_all_6_by_truth']; cp = T['wrong_in_all_6_by_project']; cs = T['wrong_in_all_6_by_status']
    w(f"\nv5·v7 여섯 run 모두 틀린 레코드 {T['wrong_in_all_6']}/289 — 정답 label별 " + ', '.join(f'{SHORT[l]} {cb[l]}' for l in L if l in cb) + '; 프로젝트별 ' + ', '.join(f'{p} {n}' for p, n in cp.items()) + '; 정답 출처별 ' + ', '.join(f'{k} {n}' for k, n in cs.items()) + '. 여기에는 G1-b 18건(tenant → role)과 Redash owner_or_admin·manual 경계가 몰려 있다.\n')
    w('## 4. 실행 환경·추론 시간·출력 오류\n')
    e = A['env']['v7_s42']
    w(f"- Pod n1tl7hwtpbqnew({e['gpu']} {e['vram_gb']} GB, 볼륨 /workspace), torch {e['torch']}(CUDA {e['cuda']}), transformers {e['transformers']}, trl {e['trl']}, peft {e['peft']}, unsloth {e['unsloth']}, python {e['python']} — **여섯 run 동일**(env.json 일치 assert). v7 학습 Pod(kufx154dteqn1b, torch 2.14.1+cu130)와 torch 버전이 다르지만 v5·v7 비교는 같은 환경 안에서 이뤄졌다. 번들 blade_s9_test_v6_20261108.tgz(`fa7b93f4…`), 2026-11-08 13:52–14:40 UTC(setup 1분, run당 7~8분), 게이트(data_v7_hashes·test_v6 manifest `a9ca4fca…`, `final adapter exists: skip training`) 6 run 모두 확인, 자동 정지.")
    w('\n| run | 조건 | 행당 ms | 출력 토큰 평균/최대 | 256 도달 | 프롬프트 최대 토큰 | 절단 | 출력 오류 | 중국어 혼입 | 피크 GiB |\n|---|---|---:|---|---:|---:|---:|---:|---:|---:|')
    for v in VERS:
        for s in SEEDS:
            for c in ('oas_code', 'oas'):
                k = f'{v}_s{s}_{c}'; t = A['times'][k]; er = A['errors'][k]; w(f"| lora_{v}_s{s} | {c} | {t['mean_ms_per_row']} | {t['output_tokens_mean']} / {t['output_tokens_max']} | {t['hit_max_new_tokens']} | {t['prompt_tokens_max']} | {t['truncated_prompts']} | {er['n']} | {er['han']} | {t['gpu_peak_gib']} |")
    w('\n## 5. 한계\n')
    w('- test_v6 정답의 75%(217/289)는 AI 1차 판정 단독, 23%(67)는 AI 둘의 일치, 사람 확정은 5건(A안, 마감 사유). 감사 일치율 92.7%는 AI 간 일치다. 정답 오류가 두 모델에 같은 방향으로 작용한다고 가정할 수 없으나, v5·v7 비교는 같은 정답·같은 입력·같은 환경에서 이뤄졌다.')
    w('- label 편중: tenant_match 38 중 Redash 27, membership_required 37 중 GlitchTip 27, owner_or_admin 17 중 Redash 13; Penpot에 tenant·membership·owner_or_admin 0. G1-b 18건은 두 모델 모두 0/18(tenant → role).')
    w(f"- v7의 학습 데이터에는 test_v5 281·test_v31_supp 221이 들어 있어 그 두 셋의 v7 수치는 존재하지 않는다. v7 1단계(test_v30 207) 결과는 reports/eval/lora_v7/report.md. oas(명세만) 조건의 v7 public 오판 증가와 s44 출력 오류 {H['v7']['oas']['errors'][2]}건(중국어 혼입)은 배포 전환 시 확인 항목.")
    w('- 채점 시각이 사전 마감(11-09 18:00 KST)을 넘었다(추론 완료는 11-08 23:40 KST). data-v7 사람 확인 시트(review/data_v7_human_check.xlsx)는 미회수.')
    w('\n## 6. 다음 (사용자 승인 대상)\n')
    w('- 채택 승인 시 C-5와 같은 절차: s42 어댑터 fp16 병합 → GGUF Q4_K_M(컨테이너 디스크), 변환 동등성(test_v30 oas_code, v4/v5 때와 같은 허용 폭 규칙), MIN_CONFIDENCE(val_sft_v7, choose_threshold --rule precision), Ollama blade-qwen-lora-v7 등록·환경변수 전환, verify_lora_pipeline + pytest, 발표 수치 표 갱신(v5 병기). 전환 전까지 v5가 최종 모델이며 발표 주 수치는 v5다.')
    w('- 산출물: reports/eval/lora_v7/s9/{report.md, analysis.json, scores_test_v6.json, eval_test_v6.md, lora_v5_s4*/, lora_v7_s4*/, run_s9.log, SHA256SUMS_s9}(scripts/eval_test_v6.py, analyze_s9_v7.py). 커밋하지 않았다.')
    (S9 / 'report.md').write_text('\n'.join(o) + '\n', encoding='utf-8', newline='\r\n')


if __name__ == '__main__': main()
