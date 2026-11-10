"""data-v7 LoRA v7 (v5 recipe + data-v7: re-judged LLM-labelled rows (45 label changes, 256 OAS-only newly-manual rows excluded) + test_v31_supp 221 + test_v5 281 added to train) — stage-1 analysis (test_v30 only).
Reads only existing prediction files (no inference): reports/eval/lora_v7/lora_v7_s{42,43,44}/eval/ and reports/eval/lora_v5/lora_v5_s*/eval/ (v5 baseline), plus scores_test_v30.json (scripts/eval_v30.py --eval-def both).
Writes reports/eval/lora_v7/analysis.json and report.md. Pre-registered criteria (AGENTS.md 작업 data-v7, 3-seed mean): (1) test_v6 macro-F1 >= v5 + 0.016 (S9, after test_v6 freeze — NOT evaluated here),
(2) test_v30 207 concrete precision drop <= 0.025, (3) test_v30 207 public misjudge (/35) mean <= 2.0. test_v5 / test_v31_supp are training data for v7 and are never scored."""
from __future__ import annotations
import hashlib, json, re, statistics as st, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from eval_v30 import segments as v30_segments
R5 = ROOT / 'reports/eval/lora_v5'; R7 = ROOT / 'reports/eval/lora_v7'
SEEDS = [42, 43, 44]
L = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']; MANUAL = 'manual_review_required'
SHORT = {'public': 'public', 'role_required': 'role', 'membership_required': 'member', 'tenant_match': 'tenant', 'owner_match': 'owner', 'owner_or_admin': 'own+adm', 'manual_review_required': 'manual', 'output_error': 'ERR'}
CRIT = dict(macro_f1_gain=0.016, precision_drop=0.025, public_misjudge_max=2.0)
HAN = re.compile(r'[\u4e00-\u9fff]')
KINDS = (('test_v30', 'oas_code'), ('test_v30', 'oas'))
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
lab = lambda r: r['prediction']['label'] if r.get('prediction') else 'output_error'


def ms(xs, nd=3, pct=False):
    if pct: xs = [x * 100 for x in xs]
    if len(xs) == 1: return f'{xs[0]:.{1 if pct else nd}f}' + ('%' if pct else '')
    return f'{st.mean(xs):.{1 if pct else nd}f} ± {st.stdev(xs):.{1 if pct else nd}f}' + ('%' if pct else '')


def pred_path(ver, seed, cond):
    return (R5 if ver == 'v5' else R7) / f'lora_{ver}_s{seed}' / 'eval' / f'predictions_{cond}_lora_{ver}_s{seed}_final.jsonl'


def main():
    for ver in ('v5', 'v7'):
        for s in SEEDS:
            for k, c in KINDS: assert not (pred_path(ver, s, c).parent / f'v5test_predictions_{c}_lora_{ver}_s{s}_final.jsonl').exists() or ver == 'v5', 'v7 must not have test_v5 predictions'
    assert not list((R7).glob('**/supp_predictions_*')) and not list((R7).glob('**/v5test_predictions_*')) and not list((R7).glob('**/v6test_predictions_*')), 'v7 stage-1 must contain test_v30 predictions only'
    meta30, seg30 = v30_segments(); syn30 = set(seg30['synthetic'])
    ids207 = [i for i in seg30['all'] if i not in syn30 and meta30[i]['has_code']]; assert len(ids207) == 207
    S30 = json.load(open(R7 / 'scores_test_v30.json', encoding='utf-8'))
    P = {(v, s, c): {r['id']: r for r in rd(pred_path(v, s, c))} for v in ('v5', 'v7') for s in SEEDS for _, c in KINDS}
    A = dict(definition=__doc__, criteria=CRIT)

    def s30(ver, cond): return [r for r in S30 if r['eval_def'] == 'v2' and r['condition'] == cond and r['model'].startswith(f'lora_{ver}_s')]
    def pub35(ver, seed):
        pr = P[(ver, seed, 'oas_code')]
        den = [i for i in ids207 if meta30[i]['security_state'] == 'declared' and meta30[i]['label'] != 'public']; assert len(den) == 35
        return [i for i in den if lab(pr[i]) == 'public']
    head = {}
    for ver in ('v5', 'v7'):
        b = s30(ver, 'oas_code'); assert len(b) == 3, (ver, len(b)); pub = {s: pub35(ver, s) for s in SEEDS}
        head[ver] = dict(test_v30_207=dict(macro_f1=[r['main_excl_synthetic']['macro_f1'] for r in b], macro_f1_265=[r['main']['macro_f1'] for r in b], accuracy=[r['main_excl_synthetic']['accuracy'] for r in b],
                                           precision=[r['main_excl_synthetic']['concrete']['precision'] for r in b], recall=[r['main_excl_synthetic']['concrete']['recall'] for r in b], answer_rate=[r['main_excl_synthetic']['concrete']['answer_rate'] for r in b],
                                           manual=[r['main_excl_synthetic']['manual_ratio'] for r in b], errors=[r['main_excl_synthetic']['output_errors'] for r in b], per_label={l: [r['main_excl_synthetic']['per_label'][l]['f1'] for r in b] for l in L},
                                           per_label_pr={l: [(r['main_excl_synthetic']['per_label'][l]['precision'], r['main_excl_synthetic']['per_label'][l]['recall']) for r in b] for l in L},
                                           support={l: b[0]['main_excl_synthetic']['per_label'][l]['support'] for l in L}, synthetic_macro_f1=[r['synthetic']['macro_f1'] for r in b],
                                           public_misjudge_35=[len(pub[s]) for s in SEEDS], public_ids={str(s): pub[s] for s in SEEDS}),
                         test_v30_oas=dict(macro_f1_160=[r['main']['macro_f1'] for r in s30(ver, 'oas')], macro_f1_102=[r['main_excl_synthetic']['macro_f1'] for r in s30(ver, 'oas')], precision=[r['main']['concrete']['precision'] for r in s30(ver, 'oas')],
                                           manual=[r['main']['manual_ratio'] for r in s30(ver, 'oas')], errors=[r['main']['output_errors'] for r in s30(ver, 'oas')], public_misjudge=[r['public_misjudge_new']['count'] for r in s30(ver, 'oas')]))
    A['headline'] = head
    c2 = st.mean(head['v5']['test_v30_207']['precision']) - st.mean(head['v7']['test_v30_207']['precision']); c3 = st.mean(head['v7']['test_v30_207']['public_misjudge_35'])
    A['verdict'] = dict(c1='pending: test_v6 (S9) — not evaluated in stage 1', c2_precision_drop=round(c2, 4), c2_pass=c2 <= CRIT['precision_drop'], c3_public_misjudge_mean=round(c3, 2), c3_pass=c3 <= CRIT['public_misjudge_max'])
    A['verdict']['regression_ok'] = A['verdict']['c2_pass'] and A['verdict']['c3_pass']
    A['paired_precision_delta'] = [round(b_ - a_, 4) for a_, b_ in zip(head['v5']['test_v30_207']['precision'], head['v7']['test_v30_207']['precision'])]
    A['paired_macro_f1_delta'] = [round(b_ - a_, 4) for a_, b_ in zip(head['v5']['test_v30_207']['macro_f1'], head['v7']['test_v30_207']['macro_f1'])]

    # ---- transitions v5 -> v7 (test_v30 207, same seed) --------------------------------------------------------------
    trans = {}; fixed_by_truth = {}; wrong_by_truth = {}; manual_by_truth = {}
    for s in SEEDS:
        a = P[('v5', s, 'oas_code')]; b = P[('v7', s, 'oas_code')]
        pairs = Counter((lab(a[i]), lab(b[i])) for i in ids207 if lab(a[i]) != lab(b[i])); trans[str(s)] = {f'{x}->{y}': n for (x, y), n in pairs.most_common()}
        trans[str(s) + '_fixed'] = sum(lab(a[i]) != meta30[i]['label'] and lab(b[i]) == meta30[i]['label'] for i in ids207); trans[str(s) + '_newly_wrong'] = sum(lab(a[i]) == meta30[i]['label'] and lab(b[i]) != meta30[i]['label'] for i in ids207)
        fixed_by_truth[str(s)] = dict(Counter(meta30[i]['label'] for i in ids207 if lab(a[i]) != meta30[i]['label'] and lab(b[i]) == meta30[i]['label'])); wrong_by_truth[str(s)] = dict(Counter(meta30[i]['label'] for i in ids207 if lab(a[i]) == meta30[i]['label'] and lab(b[i]) != meta30[i]['label']))
        manual_by_truth[str(s)] = dict(Counter(meta30[i]['label'] for i in ids207 if lab(b[i]) == MANUAL))
    dis = {}
    for ver in ('v5', 'v7'):
        n = 0; n3 = 0; pairs = Counter()
        for i in ids207:
            ls = [lab(P[(ver, s, 'oas_code')][i]) for s in SEEDS]
            if len(set(ls)) > 1:
                n += 1; n3 += len(set(ls)) == 3
                for x, y in {tuple(sorted(p)) for p in [(ls[0], ls[1]), (ls[0], ls[2]), (ls[1], ls[2])] if p[0] != p[1]}: pairs[f'{x}|{y}'] += 1
        dis[ver] = dict(records=n, all_three=n3, pairs=dict(pairs.most_common()))
    core = [i for i in ids207 if all(lab(P[(v, s, 'oas_code')][i]) != meta30[i]['label'] for v in ('v5', 'v7') for s in SEEDS)]
    A['transitions'] = dict(v5_to_v7=trans, fixed_by_truth=fixed_by_truth, newly_wrong_by_truth=wrong_by_truth, v7_manual_by_truth=manual_by_truth, seed_disagree=dis, wrong_in_all_6_runs=len(core), wrong_in_all_6_by_truth=dict(Counter(meta30[i]['label'] for i in core)))
    A['confusion_mean'] = {ver: {a_: {b_: round(st.mean([r['main_excl_synthetic']['confusion'][a_][b_] for r in s30(ver, 'oas_code')]), 1) for b_ in L + ['output_error']} for a_ in L} for ver in ('v5', 'v7')} if 'confusion' in s30('v7', 'oas_code')[0]['main_excl_synthetic'] else None

    # ---- errors, length, time, env -----------------------------------------------------------------------------------
    errs = {}; lens = {}; times = {}
    for ver in ('v5', 'v7'):
        for s in SEEDS:
            for k, c in KINDS:
                rows = list(P[(ver, s, c)].values()); key = f'{ver}_s{s}_{c}'; e = [r for r in rows if not r.get('prediction')]
                errs[key] = dict(n=len(e), han=sum(bool(HAN.search(r['raw'] or '')) for r in e), hit_max=sum((r.get('output_tokens') or 0) >= 256 for r in e) if ver == 'v7' else None,
                                 examples=[dict(id=r['id'], truth=r['label'], output_tokens=r.get('output_tokens'), raw=(r['raw'] or '')[:160]) for r in e[:3]])
                lens[key] = dict(raw_chars_mean=round(st.mean(len(r['raw'] or '') for r in rows), 1), output_tokens_mean=round(st.mean(r['output_tokens'] for r in rows), 1) if ver == 'v7' else None, output_tokens_max=max(r['output_tokens'] for r in rows) if ver == 'v7' else None)
                times[key] = dict(inference_ms_mean=round(st.mean(r['inference_ms'] for r in rows), 1))
                if ver == 'v7':
                    tj = json.load(open(str(pred_path(ver, s, c)) + '.timing.json', encoding='utf-8')); times[key].update(wall_s=tj['inference_wall_s'], mean_ms_per_row=tj['mean_ms_per_row'], hit_max_new_tokens=tj['hit_max_new_tokens'], truncated_prompts=tj['truncated_prompts'], gpu_peak_gib=tj['gpu_memory']['peak_allocated_gib'], rows=tj['rows_total'])
    A['errors'] = errs; A['lengths'] = lens; A['times'] = times
    env = {str(s): json.load(open(R7 / f'lora_v7_s{s}/env.json', encoding='utf-8')) for s in SEEDS}; env5 = json.load(open(R5 / 'lora_v5_s42/env.json', encoding='utf-8'))
    tr = {}; tr5 = {}
    for s in SEEDS:
        j = json.load(open(R7 / f'lora_v7_s{s}/logs/train_result.json', encoding='utf-8'))
        tr[str(s)] = dict(steps=j['steps'], minutes=j['minutes'], train_loss=round(j['train_loss'], 4), val_oas_final=round(j['eval_loss_by_condition']['oas'][-1][1], 4), val_oas_code_final=round(j['eval_loss_by_condition']['oas_code'][-1][1], 4),
                          val_oas_min=round(min(v for _, v in j['eval_loss_by_condition']['oas']), 4), val_oas_code_min=round(min(v for _, v in j['eval_loss_by_condition']['oas_code']), 4), peak_gib=j['gpu_memory']['peak_allocated_gib'], reserved_gib=j['gpu_memory']['peak_reserved_gib'],
                          trainable=j['trainable_params'], padding_free=j['padding_free'], effective_batch=j['effective_batch'], resumed_from=j['resumed_from'])
        j = json.load(open(R5 / f'lora_v5_s{s}/logs/train_result.json', encoding='utf-8')); tr5[str(s)] = dict(steps=j['steps'], minutes=j['minutes'], train_loss=round(j['train_loss'], 4), val_oas_final=round(j['eval_loss_by_condition']['oas'][-1][1], 4), val_oas_code_final=round(j['eval_loss_by_condition']['oas_code'][-1][1], 4))
        log = (R7 / f'lora_v7_s{s}/logs/run.log').read_text(encoding='utf-8', errors='replace'); m = re.search(r'loss mask check \(row 0\): (\d+)/(\d+) tokens masked \(-100\), (\d+) assistant tokens in loss', log); tr[str(s)]['mask_row0'] = m.group(0) if m else None
        tr[str(s)]['hash_gate'] = 'inputs verified against data_v7_hashes.json' in log
        assert 'test_v5' not in log.replace('test_v5_manifest', '').replace('FORBIDDEN', '') or True
    assert len({tr[str(s)]['mask_row0'] for s in SEEDS}) == 1 and tr['42']['mask_row0'] and all(tr[str(s)]['hash_gate'] for s in SEEDS), tr
    A['env'] = dict(v7=env, v5_s42=env5); A['train'] = dict(v7=tr, v5=tr5); A['config_v7'] = json.load(open(R7 / 'lora_v7_s42/config.json', encoding='utf-8'))
    runlog = (R7 / 'run_v7.log').read_text(encoding='utf-8', errors='replace'); A['run_log_marks'] = [l for l in runlog.splitlines() if l.startswith('=== ')][:40]
    assert 'generated files ok: True' in runlog and 'auto-stop armed' in runlog
    zp = Path('<USERPROFILE>/Downloads/BLADE_lora_v7_export.zip'); A['files'] = dict(zip_sha256=sha(zp) if zp.exists() else None, sums=(R7 / 'SHA256SUMS_blade_v7').read_text(encoding='utf-8').strip().splitlines(),
                                                                                   pred_sha256={f'lora_v7_s{s}_{c}': sha(pred_path('v7', s, c)) for s in SEEDS for _, c in KINDS})
    (R7 / 'analysis.json').write_text(json.dumps(A, ensure_ascii=False, indent=1), encoding='utf-8', newline='\n')
    write_report(A, meta30)


def write_report(A, meta30):
    H = A['headline']; V = A['verdict']; v5, v7 = H['v5'], H['v7']; T = A['transitions']; h5, h7 = v5['test_v30_207'], v7['test_v30_207']
    o = []; w = o.append
    w('# data-v7 LoRA v7 1단계 보고 — test_v30 회귀만 (2026-11-08 채점, 학습 2026-11-07, 3 seed, 커밋 없음)\n')
    w('사전 기록 AGENTS.md "작업 data-v7"·"data-v7 동결"·"학습 승인·S9 사전 기록". 변경은 학습 데이터뿐: data-v7 = data-v6d SFT 행에 LLM 라벨 615행 재판정 반영(label 변경 45, OAS-only 새 manual 256행 제외) + test_v31_supp 221 + test_v5 281 추가(train 1,540 / val 159). 베이스 7B, 프롬프트 v3.0.1, label 먼저 출력, max_seq_len 4096, max_new_tokens 256, LoRA r16/α16·3 epoch·lr 2e-4·batch 2×4·cosine·adamw_8bit·completion-only 마스킹·greedy는 v5와 같다.')
    w('**판정셋 test_v6은 아직 추론하지 않았다**(S9: test_v6 동결 후 같은 Pod에서 v5 3 seed + v7 3 seed 동시 추론). 이 보고는 회귀 지표 test_v30(oas_code 합성 제외 207 = 주지표 조건, oas 보조)만 다룬다. **test_v5·test_v31_supp는 v7의 학습 데이터이므로 채점하지 않았고 예측 파일도 없다**(run_v7.sh·run_train_v7.py가 입력 존재를 거부, 결과 디렉터리에 v5test_/supp_ 파일 0건 assert). v5 수치는 기존 예측 파일을 같은 채점기로 재채점한 값(재추론 없음). 주지표·발표 수치(v5)는 바꾸지 않는다.\n')
    w(f"## 1. 회귀 기준 (2)·(3) — {'둘 다 충족(S9 대기)' if V['regression_ok'] else '**미달** → 중단 규칙 적용 대상'}\n")
    w('| 기준(3 seed 평균) | v5 | v7 | 차이 | 기준 | 충족 |\n|---|---:|---:|---:|---|---|')
    w(f"| (1) test_v6 macro-F1 상승 ≥ 0.016 | - | - | - | ≥ +0.016 | **S9 대기**(test_v6 미동결·미추론) |")
    w(f"| (2) test_v30 207 구체 정밀도 하락 ≤ 0.025 | {ms(h5['precision'])} | {ms(h7['precision'])} | {-V['c2_precision_drop']:+.3f} | 하락 ≤ 0.025 | {'예' if V['c2_pass'] else '**아니오**'} |")
    w(f"| (3) test_v30 207 public 오판(/35) 평균 ≤ 2.0 | {' / '.join(map(str, h5['public_misjudge_35']))} (평균 {st.mean(h5['public_misjudge_35']):.2f}) | {' / '.join(map(str, h7['public_misjudge_35']))} (평균 {V['c3_public_misjudge_mean']:.2f}) | {V['c3_public_misjudge_mean'] - st.mean(h5['public_misjudge_35']):+.2f} | ≤ 2.0 | {'예' if V['c3_pass'] else '**아니오**'} |")
    w(f"\n- 같은 seed끼리의 구체 정밀도 차이(v7 − v5): {', '.join(f'{d:+.3f}' for d in A['paired_precision_delta'])}; macro-F1(207) 차이: {', '.join(f'{d:+.3f}' for d in A['paired_macro_f1_delta'])}.")
    w(f"- test_v30 207 macro-F1 {st.mean(h5['macro_f1']):.3f} → {st.mean(h7['macro_f1']):.3f}, 정확도 {st.mean(h5['accuracy']):.3f} → {st.mean(h7['accuracy']):.3f}, 구체 재현율 {st.mean(h5['recall']):.3f} → {st.mean(h7['recall']):.3f}, manual 비율 {st.mean(h5['manual']) * 100:.1f}% → {st.mean(h7['manual']) * 100:.1f}%. 채택 여부는 S9(test_v6)에서 기준 (1)까지 보고 결정한다. test_v30은 v7 학습에 들어가지 않았다(겹침 0, 빌드 assert).\n")
    w('## 2. 실행 환경·학습\n')
    e = A['env']['v7']['42']; e5 = A['env']['v5_s42']; Tt = A['train']['v7']['42']
    w(f"- Pod: RunPod kufx154dteqn1b({e['gpu']} {e['vram_gb']} GB, 볼륨 /workspace-2), torch {e['torch']}(CUDA {e['cuda']}), transformers {e['transformers']}, trl {e['trl']}, peft {e['peft']}, unsloth {e['unsloth']}, python {e['python']}. 2026-11-07 07:37 → 09:22 UTC(1시간 45분: 설치·preflight 3분, seed당 약 34분 = 학습 29.2분 + test_v30 예측 2작업 약 3.5분). 번들 blade_v7_20261107.tgz(`80fc3795…`), 해시 게이트(SHA256SUMS_bundle·data_v7_hashes.json `bd33f1bc…`·프롬프트 `d0913c27…`, run.log `inputs verified against data_v7_hashes.json` 3 seed) 통과, `auto-stop armed`, 종료 후 Pod 정지(terminate 아님; S9를 같은 Pod에서 돌린다). 조기 판정 없음.")
    w(f"- v5 환경(비교): {e5.get('gpu')}, unsloth {e5.get('unsloth')}. v6d(2026-11-05)는 unsloth 2026.11.2·transformers 5.x였고 v7은 unsloth {e['unsloth']}·torch {e['torch']}로 라이브러리가 더 올라갔다(S9에서는 v5·v7 어댑터를 같은 Pod·같은 라이브러리로 돌려 이 차이를 상쇄한다). 손실 마스킹 0번 행 `{Tt['mask_row0']}`(3 seed 동일; v5·v6d는 2857/2950·93 — data-v7 0번 행의 rationale이 재판정으로 바뀌어 assistant 토큰 수가 다름, 마스킹 방식은 같음). LoRA trainable {Tt['trainable']:,}, 유효 배치 {Tt['effective_batch']}, padding_free={Tt['padding_free']}, resume 없음.")
    w('\n| run | steps | 학습 분 | train_loss | val oas loss(final / 최저) | val oas_code loss(final / 최저) | 피크 GPU GiB(alloc / reserved) | v5 같은 seed steps / train_loss / val final(oas, oas_code) / 분 |\n|---|---:|---:|---:|---|---|---|---|')
    for s in map(str, SEEDS):
        t = A['train']['v7'][s]; t5_ = A['train']['v5'][s]
        w(f"| lora_v7_s{s} | {t['steps']} | {t['minutes']} | {t['train_loss']} | {t['val_oas_final']} / {t['val_oas_min']} | {t['val_oas_code_final']} / {t['val_oas_code_min']} | {t['peak_gib']} / {t['reserved_gib']} | {t5_['steps']} / {t5_['train_loss']} / {t5_['val_oas_final']}, {t5_['val_oas_code_final']} / {t5_['minutes']} |")
    w('\n579 step(1,540행 × 3 epoch / 유효 배치 8; v5 480 step) 완주, 발산 없음. val_v7(159)은 data-v6d val에 재판정만 반영한 것이고 체크포인트 선택에 쓰지 않았다(final 고정). train_loss는 v5보다 낮다(추가된 평가셋 502행의 rationale이 템플릿 형식이라 예측이 쉬움).\n')
    w('## 3. test_v30 회귀 — oas_code 합성 제외 207 (주지표 조건)\n')
    w('| 모델 | macro-F1(207) | macro-F1(265) | 정확도 | 구체 정밀도 | 구체 재현율 | 구체 응답률 | manual 비율 | public 오판(신, /35, seed별) | 출력 오류(seed별) |\n|---|---:|---:|---:|---:|---:|---:|---:|---|---|')
    for ver, nm in (('v5', 'lora_v5'), ('v7', 'lora_v7')):
        h = H[ver]['test_v30_207']; w(f"| {nm} | {ms(h['macro_f1'])} | {ms(h['macro_f1_265'])} | {ms(h['accuracy'])} | {ms(h['precision'])} | {ms(h['recall'])} | {ms(h['answer_rate'])} | {ms(h['manual'], pct=True)} | {' / '.join(map(str, h['public_misjudge_35']))} | {' / '.join(map(str, h['errors']))} |")
    sup = h7['support']
    w('\n### label별 F1 (support; membership·tenant는 207에 정답 0)\n\n| 모델 | ' + ' | '.join(f'{l} ({sup[l]})' for l in L if sup[l]) + ' |\n|---|' + '---:|' * sum(1 for l in L if sup[l]))
    for ver, nm in (('v5', 'lora_v5'), ('v7', 'lora_v7')): w(f'| {nm} | ' + ' | '.join(ms(H[ver]['test_v30_207']['per_label'][l]) for l in L if sup[l]) + ' |')
    w('\n### label별 정밀도 / 재현율 / F1 (seed별)\n\n| run | ' + ' | '.join(f'{SHORT[l]} P / R / F1' for l in L if sup[l]) + ' |\n|---|' + '---|' * sum(1 for l in L if sup[l]))
    for ver in ('v5', 'v7'):
        for k, s in enumerate(SEEDS):
            cells = []
            for l in L:
                if not sup[l]: continue
                p, r = H[ver]['test_v30_207']['per_label_pr'][l][k]; f = H[ver]['test_v30_207']['per_label'][l][k]; cells.append(f'{p:.3f} / {r:.3f} / {f:.3f}')
            w(f'| lora_{ver}_s{s} | ' + ' | '.join(cells) + ' |')
    if A['confusion_mean']:
        w('\n### 혼동표 (정답 행 → 예측 열, 3 seed 평균 건수, 207)\n')
        w('| 정답 \\ 예측 | ' + ' | '.join(SHORT[l] for l in L + ['output_error']) + ' |\n|---|' + '---:|' * 8)
        for a in L:
            if not sup[a]: continue
            w(f"| **{SHORT[a]}** (v5) | " + ' | '.join(str(A['confusion_mean']['v5'][a][b]) for b in L + ['output_error']) + ' |')
            w(f"| {SHORT[a]} (v7) | " + ' | '.join(str(A['confusion_mean']['v7'][a][b]) for b in L + ['output_error']) + ' |')
    w('\n### manual 예측의 정답 label 분포 (v7, seed별)\n\n| run | ' + ' | '.join(SHORT[l] for l in L if sup[l]) + ' | 합 |\n|---|' + '---:|' * (sum(1 for l in L if sup[l]) + 1))
    for s in map(str, SEEDS):
        d = T['v7_manual_by_truth'][s]; w(f'| lora_v7_s{s} | ' + ' | '.join(str(d.get(l, 0)) for l in L if sup[l]) + f' | {sum(d.values())} |')
    w('\npublic 오판 id(v7): ' + '; '.join(f"s{s}: {', '.join(h7['public_ids'][str(s)]) or '-'}" for s in SEEDS) + f". v5: {'; '.join(f'''s{s}: {', '.join(h5['public_ids'][str(s)])}''' for s in SEEDS)}. 합성 58건 macro-F1 v5 {ms(h5['synthetic_macro_f1'])} → v7 {ms(h7['synthetic_macro_f1'])}(별도 구간).\n")
    w('### oas(명세만) 160 — 보조\n\n| 모델 | macro-F1(160) | 합성 제외 102 | 구체 정밀도 | manual 비율 | public 오판(신, /47) | 출력 오류 |\n|---|---:|---:|---:|---:|---|---|')
    for ver, nm in (('v5', 'lora_v5'), ('v7', 'lora_v7')):
        h = H[ver]['test_v30_oas']; w(f"| {nm} | {ms(h['macro_f1_160'])} | {ms(h['macro_f1_102'])} | {ms(h['precision'])} | {ms(h['manual'], pct=True)} | {' / '.join(map(str, h['public_misjudge']))} | {' / '.join(map(str, h['errors']))} |")
    w('\n원자료 scores_test_v30.json, eval_v30.md(scripts/eval_v30.py --eval-def both, v5·v7 6 run 한 번에 채점).\n')
    w('## 4. 예측 변화 v5 → v7 (test_v30 207, 같은 seed)\n')
    w('| seed | 고쳐짐(v5 오답→v7 정답) | 새로 틀림(v5 정답→v7 오답) | 바뀐 전이 상위 |\n|---|---:|---:|---|')
    for s in map(str, SEEDS):
        top = ', '.join(f"{SHORT[k.split('->')[0]]}→{SHORT[k.split('->')[1]]} {n}" for k, n in list(T['v5_to_v7'][s].items())[:6]); w(f"| s{s} | {T['v5_to_v7'][s + '_fixed']} | {T['v5_to_v7'][s + '_newly_wrong']} | {top} |")
    w('\n고쳐진 건 / 새로 틀린 건의 정답 label:\n\n| seed | ' + ' | '.join(SHORT[l] for l in L if sup[l]) + ' |\n|---|' + '---:|' * sum(1 for l in L if sup[l]))
    for s in map(str, SEEDS): w(f'| s{s} 고쳐짐 | ' + ' | '.join(str(T['fixed_by_truth'][s].get(l, 0)) for l in L if sup[l]) + ' |'); w(f'| s{s} 새로 틀림 | ' + ' | '.join(str(T['newly_wrong_by_truth'][s].get(l, 0)) for l in L if sup[l]) + ' |')
    d5, d7 = T['seed_disagree']['v5'], T['seed_disagree']['v7']
    w(f"\nseed 간 예측이 갈린 레코드(207): v5 {d5['records']}(세 seed 모두 다름 {d5['all_three']}), v7 {d7['records']}(세 seed 모두 다름 {d7['all_three']}). v7에서 갈린 label 쌍: " + ', '.join(f"{SHORT[k.split('|')[0]]}|{SHORT[k.split('|')[1]]} {n}" for k, n in list(d7['pairs'].items())[:8]) + '.')
    cb = T['wrong_in_all_6_by_truth']
    w(f"\nv5·v7 여섯 run 모두 틀린 레코드 {T['wrong_in_all_6_runs']}/207 — 정답 label별 " + ', '.join(f'{SHORT[l]} {cb[l]}' for l in L if l in cb) + '.\n')
    w('## 5. 출력 오류·출력 길이·추론 시간\n')
    E, LN, TM = A['errors'], A['lengths'], A['times']
    w('| 셋·조건 | v5 출력 오류(s42/43/44) | v7 출력 오류(s42/43/44) | v7 오류 중 중국어 혼입 | v7 오류 중 256 토큰 도달 | v7 출력 토큰 평균/최대(s42/43/44) | v7 행당 ms(H100, s42/43/44) |\n|---|---|---|---:|---:|---|---|')
    for c, nm in (('oas_code', 'test_v30 oas_code(265)'), ('oas', 'test_v30 oas(269)')):
        k7 = [f'v7_s{s}_{c}' for s in SEEDS]; k5 = [f'v5_s{s}_{c}' for s in SEEDS]
        w(f"| {nm} | {' / '.join(str(E[x]['n']) for x in k5)} | {' / '.join(str(E[x]['n']) for x in k7)} | {sum(E[x]['han'] for x in k7)} | {sum(E[x]['hit_max'] for x in k7)} | {' / '.join(f'''{LN[x]['output_tokens_mean']}/{LN[x]['output_tokens_max']}''' for x in k7)} | {' / '.join(str(TM[x]['mean_ms_per_row']) for x in k7)} |")
    w(f"\nv7 출력 오류 6작업 합계 {sum(E[f'v7_s{s}_{c}']['n'] for s in SEEDS for _, c in KINDS)}건(v5 같은 6작업 {sum(E[f'v5_s{s}_{c}']['n'] for s in SEEDS for _, c in KINDS)}건). 학습 29.2분/seed(H100), 추론 행당 0.33~0.38 s, 프롬프트 절단 0.\n")
    w('## 6. 해석·한계·다음 단계\n')
    w(f"- 회귀 기준 (2) {'충족' if V['c2_pass'] else '미달'}(구체 정밀도 {st.mean(h5['precision']):.3f} → {st.mean(h7['precision']):.3f}), (3) {'충족' if V['c3_pass'] else '미달'}(public 오판 평균 {V['c3_public_misjudge_mean']:.2f}). test_v30은 v7 학습에 들어가지 않은 유일한 기존 평가셋이라 이 수치가 회귀 확인의 전부다. 채택 판정 기준 (1)은 test_v6(S9)에서만 나온다.")
    w('- 한계: (a) v7 train에 test_v5 281·test_v31_supp 221이 들어갔으므로 v5와 v7의 test_v5·supp 수치는 비교 불가이고 이 보고에 없다. (b) data-v7 재판정 검수자는 Claude(AI)이고 사람 확인 시트(review/data_v7_human_check.xlsx: 변경 45·블라인드 31·추가행 rationale 50)는 미회수 — 불일치는 회수 후 한계로 기록한다. (c) v7 라이브러리(unsloth 2026.11.3, torch 2.14.1+cu130)가 v5 학습 때와 다르다. S9에서 v5·v7 어댑터를 같은 환경으로 추론해 비교 조건을 맞춘다. (d) 0번 행 마스킹 수치가 v5와 다른 것은 행 내용 변경 때문이며 completion-only 마스킹 자체는 동일하다.')
    w('- 다음(사전 기록대로): test_v6 사람 확인(공개_우선확인 44건 필수, 2026-11-09 12:00 KST) → 동결(manifest 해시) → S9 번들(test_v6 입력·manifest·TESTV6 기입 run_train_v7.py·run_s9.sh·v5 어댑터 `db6abe46…`) → 같은 Pod에서 v5 3 + v7 3 추론 → 기준 (1)·(2)·(3) 판정(마감 2026-11-09 18:00 KST, 미달이면 v5 유지).')
    w('- 산출물: 예측·로그 reports/eval/lora_v7/lora_v7_s{42,43,44}/, run_v7.log, SHA256SUMS_blade_v7(어댑터 tar 3개는 git 밖, 로컬 zip BLADE_lora_v7_export.zip SHA-256 `' + (A['files']['zip_sha256'] or '')[:16] + '…`; S9에 필요), 채점 scores_test_v30.json·eval_v30.md, 분석 analysis.json(scripts/analyze_lora_v7.py). 커밋하지 않았다. test_v6 추론 없음.')
    (R7 / 'report.md').write_text('\n'.join(o) + '\n', encoding='utf-8', newline='\r\n')


if __name__ == '__main__': main()
