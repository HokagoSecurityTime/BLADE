"""S4 권한 문맥 보강 추론 실험 — 로컬 재채점·분석 (학습·추론 없음, test_v6 미사용).

입력
- 문맥 보강 입력: reports/eval/context_aug_v5/inputs/{set}_{budget}_inputs.jsonl (정답 label·security_state·ctx 블록 메타)
- Pod 예측(회수본): reports/eval/context_aug_v5/pod_results/pred_{set}_{budget}_s{seed}.jsonl (+ .timing.json, env.json, baseline_check.json, selection.json)
- v5 기준 예측(문맥 없음, 기존 기록): reports/eval/lora_v5/lora_v5_s{seed}/eval/{v5test_,}predictions_oas_code_lora_v5_s{seed}_final.jsonl
지표 정의는 scripts/eval_combined_v5.py와 같다(training/lora/runpod/s4_ctx/score_ctx.py metrics 재사용).
출력: reports/eval/context_aug_v5/analysis.json, report.md, fixed_newly_wrong.md
채택 기준(사전 고정, AGENTS.md S4): test_v5 macro-F1 v5 대비 +0.016 이상, test_v30 207 구체 정밀도 하락 ≤ 0.025, test_v30 207 public 오판 평균 ≤ 2.0 — 셋 다 충족해야 채택.
"""
from __future__ import annotations
import hashlib, json, statistics as st, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'training/lora/runpod/s4_ctx'))
from score_ctx import metrics, L, MANUAL  # noqa: E402

CA = ROOT / 'reports/eval/context_aug_v5'; POD = CA / 'pod_results'; V5 = ROOT / 'reports/eval/lora_v5'
SEEDS = [42, 43, 44]; SETS = ['test_v5', 'test_v30']; CRIT = dict(f1_gain=0.016, prec_drop=0.025, pub_max=2.0)
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pl = lambda r: r['prediction']['label'] if r.get('prediction') else 'output_error'
SHORT = {'public': 'pub', 'role_required': 'role', 'membership_required': 'member', 'tenant_match': 'tenant', 'owner_match': 'owner', 'owner_or_admin': 'own+adm', 'manual_review_required': 'manual', 'output_error': 'ERR'}


def msd(vals, pct=False, d=3):
    if not vals: return '-'
    f = (lambda v: f'{v * 100:.1f}%') if pct else (lambda v: f'{v:.{d}f}')
    return f(vals[0]) if len(vals) == 1 else f'{f(st.mean(vals))} ± {f(st.stdev(vals))}'


def load_inputs(s, budget):
    rows = rd(CA / 'inputs' / f'{s}_{budget}_inputs.jsonl')
    if s == 'test_v30': rows = [r for r in rows if r.get('source') == 'vuln']
    return {r['id']: r for r in rows}


def load_pred(s, budget, seed):
    if budget == 'v5': p = V5 / f'lora_v5_s{seed}/eval' / (('v5test_' if s == 'test_v5' else '') + f'predictions_oas_code_lora_v5_s{seed}_final.jsonl')
    else: p = POD / f'pred_{s}_{budget}_s{seed}.jsonl'
    return ({r['id']: r for r in rd(p)}, p) if p.exists() else (None, p)


def score(inputs, preds):
    ids = [i for i in inputs if i in preds]; assert len(ids) == len(inputs), (len(ids), len(inputs))
    pairs = [(inputs[i]['label'], pl(preds[i])) for i in ids]; m = metrics(pairs)
    decl = [i for i in ids if inputs[i].get('security_state') == 'declared' and inputs[i]['label'] != 'public']
    m['public_misjudge'] = dict(count=sum(pl(preds[i]) == 'public' for i in decl), denominator=len(decl), ids=[i for i in decl if pl(preds[i]) == 'public'])
    proj = defaultdict(list)
    for i in ids: proj[inputs[i].get('service') or i.split('-')[1]].append(inputs[i]['label'] == pl(preds[i]))
    m['per_project'] = {p: dict(n=len(v), accuracy=round(sum(v) / len(v), 4)) for p, v in sorted(proj.items())}
    return m


def main():
    out = dict(generated='2026-11-04', criterion=CRIT, files={}, scores={}, env=json.load(open(POD / 'env.json', encoding='utf-8')), baseline_check=json.load(open(POD / 'baseline_check.json', encoding='utf-8')),
               selection=json.load(open(POD / 'selection.json', encoding='utf-8')), timing={})
    for p in sorted(POD.glob('*.timing.json')): out['timing'][p.name.replace('.timing.json', '')] = json.load(open(p, encoding='utf-8'))
    inputs = {(s, b): load_inputs(s, b) for s in SETS for b in ('ctx4096', 'ctx6144')}
    preds = {}
    for s in SETS:
        for b in ('v5', 'ctx4096', 'ctx6144'):
            for seed in SEEDS:
                pr, p = load_pred(s, b, seed)
                if pr is None: continue
                preds[(s, b, seed)] = pr; out['files'][f'{s}|{b}|s{seed}'] = dict(path=str(p.relative_to(ROOT)).replace('\\', '/'), sha256=sha(p), rows=len(pr))
                out['scores'][f'{s}|{b}|s{seed}'] = score(inputs[(s, b if b != 'v5' else 'ctx4096')], pr)
    S = out['scores']
    # 입력 통계
    blk = {}
    for (s, b), inp in inputs.items():
        kinds = Counter(k['kind'] for r in inp.values() for k in r['ctx']['blocks'])
        blk[f'{s}|{b}'] = dict(n=len(inp), with_blocks=sum(bool(r['ctx']['blocks']) for r in inp.values()), cut=sum(r['ctx']['cut'] for r in inp.values()), kinds=dict(kinds),
                              tokens_after_mean=round(st.mean(r['ctx']['tokens_after'] for r in inp.values()), 1), tokens_after_max=max(r['ctx']['tokens_after'] for r in inp.values()),
                              per_project={p: dict(n=len(v), with_blocks=sum(v)) for p, v in sorted(defaultdict(list, {}).items())})
        pp = defaultdict(list)
        for r in inp.values(): pp[r.get('service') or r['id'].split('-')[1]].append(bool(r['ctx']['blocks']))
        blk[f'{s}|{b}']['per_project'] = {p: dict(n=len(v), with_blocks=sum(v)) for p, v in sorted(pp.items())}
    out['inputs'] = blk
    # test_v30 두 예산 label 동일성
    i30 = inputs[('test_v30', 'ctx4096')]
    out['test_v30_budget_label_identical'] = all(pl(preds[('test_v30', 'ctx4096', 42)][i]) == pl(preds[('test_v30', 'ctx6144', 42)][i]) for i in i30)
    # 판정
    f5 = [S[f'test_v5|ctx4096|s{x}']['macro_f1'] for x in SEEDS]; f5b = [S[f'test_v5|v5|s{x}']['macro_f1'] for x in SEEDS]
    p30 = [S[f'test_v30|ctx4096|s{x}']['concrete']['precision'] for x in SEEDS]; p30b = [S[f'test_v30|v5|s{x}']['concrete']['precision'] for x in SEEDS]
    pub = [S[f'test_v30|ctx4096|s{x}']['public_misjudge']['count'] for x in SEEDS]; pubb = [S[f'test_v30|v5|s{x}']['public_misjudge']['count'] for x in SEEDS]
    c1 = st.mean(f5) - st.mean(f5b) >= CRIT['f1_gain']; c2 = st.mean(p30b) - st.mean(p30) <= CRIT['prec_drop']; c3 = st.mean(pub) <= CRIT['pub_max']
    out['verdict'] = dict(test_v5_macro_f1=dict(v5=f5b, ctx=f5, diff=round(st.mean(f5) - st.mean(f5b), 4), pass_=c1), test_v30_concrete_precision=dict(v5=p30b, ctx=p30, drop=round(st.mean(p30b) - st.mean(p30), 4), pass_=c2),
                          test_v30_public_misjudge=dict(v5=pubb, ctx=pub, mean=round(st.mean(pub), 2), pass_=c3), adopted=bool(c1 and c2 and c3))
    # 고쳐진/새로 틀린 (seed별 + 3 seed 일관)
    chg = {}
    for s in SETS:
        inp = inputs[(s, 'ctx4096')]; per = {}
        for seed in SEEDS:
            a, b = preds[(s, 'v5', seed)], preds[(s, 'ctx4096', seed)]
            per[seed] = dict(fixed=[i for i in inp if pl(a[i]) != inp[i]['label'] and pl(b[i]) == inp[i]['label']], broken=[i for i in inp if pl(a[i]) == inp[i]['label'] and pl(b[i]) != inp[i]['label']],
                             changed=sum(pl(a[i]) != pl(b[i]) for i in inp))
        allfix = [i for i in inp if all(pl(preds[(s, 'v5', x)][i]) != inp[i]['label'] and pl(preds[(s, 'ctx4096', x)][i]) == inp[i]['label'] for x in SEEDS)]
        allbrk = [i for i in inp if all(pl(preds[(s, 'v5', x)][i]) == inp[i]['label'] and pl(preds[(s, 'ctx4096', x)][i]) != inp[i]['label'] for x in SEEDS)]
        # 블록 유무별 정확도
        byblk = {}
        for has in (True, False):
            ids = [i for i in inp if bool(inp[i]['ctx']['blocks']) == has]
            if not ids: continue
            byblk['with_blocks' if has else 'no_blocks'] = dict(n=len(ids), v5_acc=[round(sum(pl(preds[(s, 'v5', x)][i]) == inp[i]['label'] for i in ids) / len(ids), 4) for x in SEEDS],
                                                               ctx_acc=[round(sum(pl(preds[(s, 'ctx4096', x)][i]) == inp[i]['label'] for i in ids) / len(ids), 4) for x in SEEDS],
                                                               v5_manual=[round(sum(pl(preds[(s, 'v5', x)][i]) == MANUAL for i in ids) / len(ids), 4) for x in SEEDS],
                                                               ctx_manual=[round(sum(pl(preds[(s, 'ctx4096', x)][i]) == MANUAL for i in ids) / len(ids), 4) for x in SEEDS])
        # 전이(v5 예측 → ctx 예측), 3 seed 합산; perm_table 블록 유무별 →role_required 전이
        trans = Counter(); trans_t = Counter(); pt = Counter()
        for x in SEEDS:
            for i in inp:
                a, b = pl(preds[(s, 'v5', x)][i]), pl(preds[(s, 'ctx4096', x)][i]); has_pt = any(k['kind'] == 'perm_table' for k in inp[i]['ctx']['blocks'])
                pt['records_with_perm_table' if has_pt else 'records_without'] += 1
                if a != b:
                    trans[f'{a}→{b}'] += 1; trans_t[f'{a}→{b}|truth={inp[i]["label"]}'] += 1; pt['changed_with_pt' if has_pt else 'changed_without'] += 1
                    if b == 'role_required': pt['to_role_with_pt' if has_pt else 'to_role_without'] += 1
                    if b == MANUAL: pt['to_manual_with_pt' if has_pt else 'to_manual_without'] += 1
                if a == inp[i]['label'] and b != inp[i]['label']: pt['broken_with_pt' if has_pt else 'broken_without'] += 1
        chg[s] = dict(per_seed=per, fixed_all_seeds=allfix, broken_all_seeds=allbrk, by_blocks=byblk, transitions=dict(trans.most_common()), transitions_truth=dict(trans_t.most_common(25)), perm_table_effect=dict(pt))
    out['changes'] = chg
    (CA / 'analysis.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    write_report(out, inputs, preds); write_lists(out, inputs, preds)


def row_metrics(S, s, b, seeds):
    rs = [S[f'{s}|{b}|s{x}'] for x in seeds if f'{s}|{b}|s{x}' in S]
    if not rs: return None
    g = lambda f: [f(r) for r in rs]
    return dict(seeds=[x for x in seeds if f'{s}|{b}|s{x}' in S], macro_f1=g(lambda r: r['macro_f1']), acc=g(lambda r: r['accuracy']), P=g(lambda r: r['concrete']['precision']), R=g(lambda r: r['concrete']['recall']),
                manual=g(lambda r: r['manual_ratio']), err=g(lambda r: r['output_errors']), pub=g(lambda r: r['public_misjudge']['count']), per_label={l: g(lambda r: r['per_label'][l]['f1']) for l in L},
                proj={p: g(lambda r: r['per_project'][p]['accuracy']) for p in rs[0]['per_project']}, support={l: rs[0]['per_label'][l]['support'] for l in L})


def write_report(out, inputs, preds):
    S = out['scores']; V = out['verdict']; env = out['env']; bc = out['baseline_check']; sel = out['selection']; t = []
    A = t.append
    A('# S4 권한 문맥 보강 추론 실험 — 결과 보고 (2026-11-04)'); A('')
    A('실험 조건은 AGENTS.md "작업 S4" 절의 사전 기록 그대로다: 프롬프트 v3.0.1 고정, LoRA v5 final 어댑터 3 seed(42·43·44), 기본 디코딩(greedy, max_new_tokens 256, batch 8), 입력 = 기존 oas_code 입력 + `[관련 권한 코드]` 블록. '
      '학습 없음, test_v6 추론 없음. Pod 실행 번들 `export/blade_s4_ctx_h100_20261104.tgz`(SHA-256 `1920ffff…`), 결과 회수본 `reports/eval/context_aug_v5/pod_results/`(tar SHA-256 `09755545…`, TAR_SHA256.txt). 채점은 scripts/eval_combined_v5.py 정의(score_ctx.metrics)로 로컬에서 다시 했고 Pod 채점(scores_all.json)과 일치한다.'); A('')
    A('## 1. 판정 — 채택 기준 미달 (불채택)'); A('')
    A('사전 고정 채택 기준 세 가지(셋 다 충족해야 채택):'); A('')
    A('| 기준 | v5 (3 seed) | ctx4096 (3 seed) | 차이 | 판정 |'); A('|---|---|---|---|---|')
    v = V['test_v5_macro_f1']; A(f"| test_v5 macro-F1 ≥ v5 + 0.016 | {msd(v['v5'])} | {msd(v['ctx'])} | {v['diff']:+.4f} | {'충족' if v['pass_'] else '**미달**'} |")
    v = V['test_v30_concrete_precision']; A(f"| test_v30 207 구체 정밀도 하락 ≤ 0.025 | {msd(v['v5'])} | {msd(v['ctx'])} | 하락 {v['drop']:+.4f} | {'충족' if v['pass_'] else '**미달**'} |")
    v = V['test_v30_public_misjudge']; A(f"| test_v30 207 public 오판(/35) 평균 ≤ 2.0 | {' / '.join(map(str, v['v5']))} (평균 {st.mean(v['v5']):.2f}) | {' / '.join(map(str, v['ctx']))} (평균 {v['mean']:.2f}) | | {'충족' if v['pass_'] else '**미달**'} |")
    A(''); A(f"**결론: {'채택' if V['adopted'] else '불채택'}.** 권한 문맥 블록을 붙인 입력은 test_v5 macro-F1을 v5 대비 {abs(V['test_v5_macro_f1']['diff']):.3f} 낮췄다(seed 표준편차 {st.stdev(V['test_v5_macro_f1']['v5']):.3f}·{st.stdev(V['test_v5_macro_f1']['ctx']):.3f}보다 큰 하락). "
      f"test_v30 207 구체 정밀도는 오히려 {abs(V['test_v30_concrete_precision']['drop']):.3f} 올랐지만(블록이 붙은 건은 13/207뿐이라 사실상 표식 `[관련 권한 코드] (없음)` 추가에 대한 회귀 확인), public 오판 평균은 {V['test_v30_public_misjudge']['mean']:.2f}건으로 기준 2.0을 넘는다. "
      '프롬프트 v3.0.1과 현재 v5 어댑터는 문맥 블록 없이 학습됐으므로, 블록은 학습 분포 밖 입력으로 작용했다. S5(v3.1 프롬프트·토큰 확률 confidence) 설계에서 문맥 블록을 다시 쓰려면 학습 입력에도 같은 형식을 넣어야 한다.'); A('')
    A('## 2. 실행 환경·게이트·시간'); A('')
    A(f"- GPU {env['gpu']}(capability {tuple(env['capability'])}, VRAM {env['vram_gb']} GB), 드라이버 {env['driver']}, Python {env['python']}, torch {env['torch']}(CUDA {env['cuda']}), transformers {env['transformers']}, peft {env['peft']}, bitsandbytes {env['bitsandbytes']}, unsloth 미설치(로더 hf: AutoModelForCausalLM + bnb 4bit 체크포인트 + attn_implementation=sdpa), flash-attn 미설치.")
    A('- 환경 게이트(env_check.json): torch≥2.4·CUDA≥12.1·capability (9,0)·bitsandbytes NF4 forward·sdpa 모두 통과(`ENV_OK=1`). 번들 해시·기준 예측 3파일 해시 OK. 어댑터는 `/workspace/blade_v5_adapters.tar.gz`(SHA-256 `db6abe46…`)에서 복원(어댑터 3개 각 161,533,192 bytes).')
    A(f"- 기준선 재현(v5 s42, 문맥 없는 원본 test_v5 입력 20건 층화 seed 42): label 일치 {bc['agree']}/{bc['n']}({bc['agreement']:.0%}), raw 출력 바이트 동일 {bc['raw_identical']}/{bc['n']} → 게이트 통과(`BASELINE_PASSED=1`). unsloth 로더(기존 v5 평가) 대신 transformers+bitsandbytes 로더를 써도 label이 같음을 확인했다. raw가 다른 4건은 rationale 문구 차이다.")
    A('- Pod 시간: 시작 16:38:16 → 마지막 추론 종료 17:10:03 UTC(약 32분, 설치·어댑터 복원·기준선 포함). 절단(tokenizer truncation) 0건, 프롬프트 최대 토큰 ctx4096 4,090 / ctx6144 5,583.'); A('')
    A('| 작업 | 행 | 모델 로드 s | 추론 벽시계 s | ms/행 | 파싱 오류 | 프롬프트 최대 토큰 |'); A('|---|---:|---:|---:|---:|---:|---:|')
    for k, j in out['timing'].items(): A(f"| {k} | {j['rows_total']} | {j['model_load_s']} | {j['inference_wall_s']} | {j['mean_ms_per_row']} | {j['parse_errors']} | {j['prompt_tokens_max']} |")
    A(''); A('(test_v30 행 265 = oas_code 전체; 채점은 취약 API 207건. 파싱 오류 수는 265건 기준이며 207건 기준 출력 오류는 4절 표.)'); A('')
    A('- Pod 스크립트의 마지막 `summary` 단계는 score_ctx.py의 timing 키 오기(`rows` → `rows_total`)로 KeyError가 났다. 이 단계는 모든 추론·채점·pack 뒤의 표 출력뿐이라 예측·채점 파일에는 영향이 없고, 로컬에서 키를 고친 뒤 같은 코드로 재채점했다(Pod `scores_all.json`과 수치 일치). `ALL DONE`·Pod 정지 호출은 그 뒤 줄이라 회수본 로그에는 없다(Pod 정지 여부는 콘솔에서 확인).'); A('')
    A('## 3. 예산 선택 (seed 42, 사전 규칙)'); A('')
    s42 = sel['s42']
    A('| 조건 | test_v5 macro-F1 | test_v30 207 구체 정밀도 | test_v30 207 public 오판 |'); A('|---|---|---|---|')
    A(f"| v5 (문맥 없음) | {S['test_v5|v5|s42']['macro_f1']:.4f} | {s42['test_v30_concrete_precision']['v5']:.4f} | {s42['test_v30_public_misjudge']['v5']} |")
    A(f"| ctx4096 | {s42['test_v5_macro_f1']['ctx4096']:.4f} | {s42['test_v30_concrete_precision']['ctx4096']:.4f} | {s42['test_v30_public_misjudge']['ctx4096']} |")
    A(f"| ctx6144 | {s42['test_v5_macro_f1']['ctx6144']:.4f} | {s42['test_v30_concrete_precision']['ctx6144']:.4f} | {s42['test_v30_public_misjudge']['ctx6144']} |"); A('')
    A(f"- 선택: **{sel['chosen']}** (Pod 기록: `{sel['reason']}`). 규칙 1이 public 오판 3 > 2로 발동했는데, 이 3건은 v5 s42 자체의 3건과 같은 id이고 test_v30 입력은 두 예산이 바이트 동일(블록 13/207)이라 ctx6144 고유의 악화가 아니다. "
      f"규칙 2로 판단해도 test_v5 macro-F1 차이 {s42['test_v5_macro_f1']['ctx4096'] - s42['test_v5_macro_f1']['ctx6144']:+.4f}로 ctx4096이 높아 결과는 같다. "
      f"test_v30 두 예산의 예측 label은 207건 전부 동일{'(확인)' if out['test_v30_budget_label_identical'] else '하지 않음(확인 필요)'}.")
    A('- ctx6144는 학습 길이(4096) 밖 입력이며 test_v5에서 ctx4096보다 더 낮았다(Umami 0.474). 이후 s43·s44는 ctx4096만 실행했다.'); A('')
    for s, title, n in (('test_v5', 'test_v5 283건 (dev, oas_code)', 283), ('test_v30', 'test_v30 oas_code 합성 제외 207건 (회귀 확인)', 207)):
        A(f'## {4 if s == "test_v5" else 5}. {title}'); A('')
        rows = [(b, row_metrics(S, s, b, SEEDS)) for b in ('v5', 'ctx4096', 'ctx6144')]; rows = [(b, r) for b, r in rows if r]
        A('| 모델 | seeds | macro-F1 | 정확도 | 구체 정밀도 | 구체 재현율 | manual 비율 | 출력 오류 |' + (' public 오판 /35 |' if s == 'test_v30' else '')); A('|---|---|---|---|---|---|---|---|' + ('---|' if s == 'test_v30' else ''))
        for b, r in rows:
            A(f"| {b} | {','.join(map(str, r['seeds']))} | {msd(r['macro_f1'])} | {msd(r['acc'])} | {msd(r['P'])} | {msd(r['R'])} | {msd(r['manual'], True)} | {' / '.join(map(str, r['err']))} |" + (f" {' / '.join(map(str, r['pub']))} |" if s == 'test_v30' else ''))
        A(''); A('label별 F1 (support, v5 → ctx4096, 3 seed 평균 ± sd):'); A('')
        A('| label | support | v5 | ctx4096 | 차이 |'); A('|---|---:|---|---|---|')
        r5, rc = dict(rows)['v5'], dict(rows)['ctx4096']
        for l in L:
            if r5['support'][l] == 0: continue
            A(f"| {l} | {r5['support'][l]} | {msd(r5['per_label'][l])} | {msd(rc['per_label'][l])} | {st.mean(rc['per_label'][l]) - st.mean(r5['per_label'][l]):+.3f} |")
        A(''); A('프로젝트별 정확도:'); A('')
        A('| 프로젝트 | n | v5 | ctx4096 | 차이 |'); A('|---|---:|---|---|---|')
        for p in r5['proj']:
            A(f"| {p} | {S[f'{s}|v5|s42']['per_project'][p]['n']} | {msd(r5['proj'][p])} | {msd(rc['proj'][p])} | {st.mean(rc['proj'][p]) - st.mean(r5['proj'][p]):+.3f} |")
        A('')
        ch = out['changes'][s]; bb = ch['by_blocks']; ib = out['inputs'][f'{s}|ctx4096']
        pp = ', '.join(f"{p} {d['with_blocks']}/{d['n']}" for p, d in ib['per_project'].items())
        A(f"입력: 블록이 붙은 건 {ib['with_blocks']}/{ib['n']}, 예산 절단(cut) {ib['cut']}건, 블록 종류 {ib['kinds']}, 프로젝트별 블록 포함 {pp}."); A('')
        A('블록 유무별 정확도·manual 비율 (3 seed):'); A(''); A('| 구간 | n | v5 정확도 | ctx 정확도 | v5 manual | ctx manual |'); A('|---|---:|---|---|---|---|')
        for k, d in bb.items(): A(f"| {k} | {d['n']} | {msd(d['v5_acc'])} | {msd(d['ctx_acc'])} | {msd(d['v5_manual'], True)} | {msd(d['ctx_manual'], True)} |")
        chg_s = ', '.join(f"s{x} {ch['per_seed'][x]['changed']}" for x in SEEDS); fb_s = ', '.join(f"s{x} +{len(ch['per_seed'][x]['fixed'])}/−{len(ch['per_seed'][x]['broken'])}" for x in SEEDS)
        A(''); A(f"- 예측이 바뀐 건(v5 → ctx, seed별): {chg_s}. 고쳐진/새로 틀린(seed별): {fb_s}. 3 seed 모두 고쳐진 {len(ch['fixed_all_seeds'])}건, 3 seed 모두 새로 틀린 {len(ch['broken_all_seeds'])}건(목록 fixed_newly_wrong.md).")
        A('- 전이 상위(v5 예측 → ctx 예측, 3 seed 합산): ' + ', '.join(f'{k} {v}' for k, v in list(ch['transitions'].items())[:8]) + '.'); A('')
    A('## 6. 해석'); A('')
    c5 = out['changes']['test_v5']; tr = c5['transitions']
    pe = c5['perm_table_effect']
    A(f"- test_v5에서 하락은 블록이 붙은 {out['inputs']['test_v5|ctx4096']['with_blocks']}건에 집중된다(블록 없는 {out['inputs']['test_v5|ctx4096']['n'] - out['inputs']['test_v5|ctx4096']['with_blocks']}건은 표식만 추가되어 정확도가 오히려 약간 올랐다; 위 블록 유무별 표). 전이는 구체 label 사이 이동과 구체→manual이 섞여 있어 블록이 '근거 추가'보다 '판단 흔들기'로 작용했다.")
    A(f"- **권한표 블록의 role_required 편향**: v5→ctx 전이 중 role_required로 간 {pe.get('to_role_with_pt', 0) + pe.get('to_role_without', 0)}건(3 seed 합산) 가운데 {pe.get('to_role_with_pt', 0)}건이 perm_table 블록(Rocket.Chat permission→roles 행, Ghost rolePermissions, Umami ROLE_PERMISSIONS)을 포함한 레코드다(perm_table 포함 레코드 {pe.get('records_with_perm_table', 0) // 3}/283). "
      f"새로 틀린 건도 perm_table 포함 {pe.get('broken_with_pt', 0)} vs 미포함 {pe.get('broken_without', 0)}. 정답이 owner_or_admin·manual(설정·가시성 분기)·membership인 핸들러에 역할 목록이 보이자 모델이 role_required로 기울었다(3 seed 일관 새로 틀린 9건 중 Rocket.Chat hasPermission 3건·Umami ROLES 1건이 이 유형). "
      '반대로 public 19건은 블록(Ghost tokenPermissionCheck·authentication 권한표)이 붙자 manual로 물러났다(public F1 0.894 → 0.691). 3 seed 일관 고쳐진 4건은 모두 Rocket.Chat roomAccessValidators(canAccessRoom 분기) 블록 건으로, 방 접근 분기를 보여주면 manual/membership 구분이 나아진다는 신호는 있다.')
    A('- 모델이 블록을 활용하지 못한 원인 후보: (1) 학습 입력에 없던 형식(분포 밖), (2) 핸들러 본문 뒤에 붙은 권한표·헬퍼가 rationale의 "description/path_params" 근거 선택을 흐트러뜨림, (3) 예산 절단으로 핸들러 뒤 블록이 잘린 건(cut)의 불완전한 문맥. 어느 것이 주원인인지는 이 실험으로 가릴 수 없다(학습 없는 문맥 효과 분리 실험).')
    A('- test_v30 207에서는 블록이 13건뿐인데도 s44 manual 비율이 30.0% → 44.9%로 뛰었다. 표식 한 줄(`[관련 권한 코드] (없음)`)만으로도 seed에 따라 보류가 늘 수 있어, 입력 형식 변경은 학습과 함께 가야 한다.'); A('')
    A('## 7. 한계'); A('')
    A('- 문맥 없는 v5 기준 수치는 재추론하지 않고 기존 기록(reports/eval/lora_v5, unsloth 로더)을 썼다. 로더 차이는 기준선 재현 20/20으로만 확인했다.')
    A('- test_v30 207은 블록 13건이라 문맥 효과가 아니라 표식 회귀 확인이다. 채택 기준의 test_v30 조건은 이 한계 안에서 적용했다.')
    A('- ctx6144는 seed 42·test_v5·test_v30만 실행했다(사전 규칙).')
    A('- 정적 분석기의 정밀도(stop12_precision.md: 30건 분류)는 바뀌지 않았으며, 블록의 "직접 근거" 비율 자체가 낮은 레코드가 남아 있다.')
    A('- S4 산출물은 커밋하지 않았다(사용자 지시). 주지표·발표 수치는 불변.'); A('')
    A('## 8. 파일'); A('')
    for k, f in out['files'].items(): A(f"- `{k}`: {f['path']} ({f['rows']}행, SHA-256 `{f['sha256'][:12]}…`)")
    A('- 분석: reports/eval/context_aug_v5/analysis.json, fixed_newly_wrong.md (scripts/analyze_context_aug_v5.py)')
    A('- 입력 통계: test_v5_ctx4096_stats.json 등, appendix_test_v30_inputs.md, stop12_precision.md')
    (CA / 'report.md').write_text('\n'.join(t) + '\n', encoding='utf-8'); print('\n'.join(t[:40]))


def write_lists(out, inputs, preds):
    t = ['# S4 고쳐진 건 · 새로 틀린 건 목록 (v5 → ctx4096, seed별 및 3 seed 일관)', '', '열: id · 프로젝트 · 정답 · v5 예측(s42/s43/s44) · ctx4096 예측(s42/s43/s44) · 권한 블록 포함(블록 수·종류·cut) · 블록 이름', '']
    for s in ['test_v5', 'test_v30']:
        inp = inputs[(s, 'ctx4096')]; ch = out['changes'][s]
        def row(i):
            r = inp[i]; bl = r['ctx']['blocks']; kinds = Counter(b['kind'] for b in bl)
            v5 = '/'.join(SHORT[pl(preds[(s, 'v5', x)][i])] for x in SEEDS); cx = '/'.join(SHORT[pl(preds[(s, 'ctx4096', x)][i])] for x in SEEDS)
            inc = ('예 ' + ','.join(f'{k}{n}' for k, n in sorted(kinds.items())) + (' cut' if r['ctx']['cut'] else '')) if bl else '아니오'
            return f"| {i} | {r.get('service') or i.split('-')[1]} | {SHORT[r['label']]} | {v5} | {cx} | {inc} | {'; '.join(b['name'] for b in bl)[:90]} |"
        hdr = ['| id | 프로젝트 | 정답 | v5 s42/43/44 | ctx s42/43/44 | 블록 포함 | 블록 이름 |', '|---|---|---|---|---|---|---|']
        t += [f'## {s}', '', f"### 3 seed 모두 고쳐진 건 ({len(ch['fixed_all_seeds'])})", ''] + hdr + [row(i) for i in ch['fixed_all_seeds']] + ['']
        t += [f"### 3 seed 모두 새로 틀린 건 ({len(ch['broken_all_seeds'])})", ''] + hdr + [row(i) for i in ch['broken_all_seeds']] + ['']
        for x in SEEDS:
            p = ch['per_seed'][x]
            t += [f"### seed {x}: 고쳐진 {len(p['fixed'])} · 새로 틀린 {len(p['broken'])}", '', '고쳐진:', ''] + hdr + [row(i) for i in p['fixed']] + ['', '새로 틀린:', ''] + hdr + [row(i) for i in p['broken']] + ['']
        t += ['### 전이 (v5 예측 → ctx 예측 | 정답, 3 seed 합산, 상위 25)', ''] + [f'- {k}: {v}' for k, v in ch['transitions_truth'].items()] + ['']
    (CA / 'fixed_newly_wrong.md').write_text('\n'.join(t) + '\n', encoding='utf-8')


if __name__ == '__main__': main()
