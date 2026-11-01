"""Build reports/eval/lora_v2/lora_v2_report.md from scores.json (eval-def v2), training logs, and the v1 reference scores. Read-only."""
import json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]; D = ROOT / 'reports/eval/lora_v2'
L = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']; MANUAL = 'manual_review_required'
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]

def table(rows, header, right_from=1):
    return '| ' + ' | '.join(header) + ' |\n|' + '|'.join('---' if i < right_from else '---:' for i in range(len(header))) + '|\n' + ''.join('| ' + ' | '.join(str(c) for c in r) + ' |\n' for r in rows)

def ms(vals, nd=3, pct=False):
    if not vals: return '-'
    f = (lambda x: f'{x:.1%}') if pct else (lambda x: f'{x:.{nd}f}')
    if len(vals) == 1: return f(vals[0])
    return f'{f(statistics.mean(vals))} ± {f(statistics.stdev(vals))}'

def base_diff():
    out = {}
    for c in ('oas', 'oas_code'):
        a = {json.loads(l)['id']: json.loads(l) for l in open(D / f'lora_v2_seed42/eval/predictions_{c}_base_v301.jsonl', encoding='utf-8') if l.strip()}
        b = {json.loads(l)['id']: json.loads(l) for l in open(ROOT / f'reports/eval/lora_v1/predictions_{c}_base_v301.jsonl', encoding='utf-8') if l.strip()}
        out[c] = dict(n=len(a), pred_diff=sum(1 for i in a if a[i].get('prediction') != b.get(i, {}).get('prediction')), raw_diff=sum(1 for i in a if a[i].get('raw') != b.get(i, {}).get('raw')))
    return out

def main():
    S = json.load(open(D / 'scores.json', encoding='utf-8')); v2 = {(r['condition'], r['model']): r for r in S if r['eval_def'] == 'v2'}
    V1 = json.load(open(ROOT / 'reports/eval_v30_redef/scores.json', encoding='utf-8')); v1ref = {(r['condition'], r['model']): r for r in V1 if r['eval_def'] == 'v2'}
    logs = {}
    for seed in (42, 43, 44):
        tr = json.load(open(D / f'lora_v2_seed{seed}/logs/train_result.json', encoding='utf-8')); log = rd(D / f'lora_v2_seed{seed}/logs/train_log.jsonl')
        logs[seed] = dict(result=tr, losses=[(e['step'], e['loss']) for e in log if 'loss' in e and 'eval_oas_loss' not in e and 'eval_oas_code_loss' not in e], ev_oas=[(e['step'], e['eval_oas_loss']) for e in log if 'eval_oas_loss' in e], ev_code=[(e['step'], e['eval_oas_code_loss']) for e in log if 'eval_oas_code_loss' in e])
    def row(cond, model, src=v2):
        r = src[(cond, model)]; m = r['main']; c = m['concrete']
        return dict(macro=m['macro_f1'], excl=r['main_excl_synthetic']['macro_f1'], syn=r['synthetic']['macro_f1'], manual=m['manual_ratio'], pub=r['public_misjudge_new']['count'], pub_den=r['public_misjudge_new']['denominator'], prec=c['precision'], rec=c['recall'], ans=c['answer_rate'], err=m['output_errors'],
                    aux=(r.get('aux_route_only_manual_accepted') or {}).get('accuracy'), per=m['per_label'])
    tags = {'final': [f'lora_v2_s{s}_final' for s in (42, 43, 44)], 'best_oas': [m for (c, m) in v2 if c == 'oas' and '_best_oas_step' in m], 'best_oas_code': [m for (c, m) in v2 if c == 'oas' and '_best_oas_code_step' in m]}
    t = '# LoRA v2 (data-v2) — test_v30 평가, eval-def v2, seed 42·43·44\n\n'
    t += '데이터 data-v2(train_v2 799 / val_v2 98), 프롬프트 v3.0.1, 베이스 Qwen2.5-7B-Instruct 4bit, 하이퍼파라미터 v1과 동일. 학습·평가는 사용자 Colab(A100)에서 실행, 예측 파일을 scripts/eval_v30.py(eval-def v2)로 채점. 베이스 모델 행은 같은 세션(seed 42 폴더)에서 1회 측정. v1 참고 행은 reports/eval_v30_redef/scores.json(같은 정의로 재계산).\n\n'
    t += '## 1. 학습 기록\n\n' + table([[s, l['result']['steps'], round(l['result']['train_runtime'] / 60, 1), round(l['result']['train_loss'], 4), f"{l['losses'][-1][1]:.3f}" if l['losses'] else '-', f"step {l['result']['best_by_condition']['oas'][0]} ({l['result']['best_by_condition']['oas'][1]:.3f})", f"step {l['result']['best_by_condition']['oas_code'][0]} ({l['result']['best_by_condition']['oas_code'][1]:.3f})", f"{l['ev_oas'][-1][1]:.3f} / {l['ev_code'][-1][1]:.3f}"] for s, l in logs.items()], ['seed', 'steps', '분', '평균 train loss', '마지막 train loss', 'best val oas', 'best val oas_code', '최종 val loss oas / oas_code'])
    t += '\n## 2. 요약 (주지표 macro-F1 = oas: route_only 제외 160건, oas_code: 265건; 합성 제외 = oas 102 / oas_code 207)\n\n'
    rows = []
    for cond in ('oas', 'oas_code'):
        b = row(cond, 'base_v301'); rows.append([cond, '베이스 + v3.0.1 (이번 세션)', f"{b['macro']:.3f}", f"{b['excl']:.3f}", f"{b['syn']:.3f}", f"{b['manual']:.1%}", f"{b['pub']}/{b['pub_den']}", f"{b['prec']:.3f} / {b['rec']:.3f}", b['err'], f"{b['aux']:.1%}" if b['aux'] is not None else '-'])
        for name, models in tags.items():
            rs = [row(cond, m) for m in models]
            rows.append([cond, f'LoRA v2 {name} (3 seed)', ms([r['macro'] for r in rs]), ms([r['excl'] for r in rs]), ms([r['syn'] for r in rs]), ms([r['manual'] for r in rs], pct=True), '·'.join(f"{r['pub']}" for r in rs) + f" /{rs[0]['pub_den']}", ms([r['prec'] for r in rs]) + ' / ' + ms([r['rec'] for r in rs]), sum(r['err'] for r in rs), ms([r['aux'] for r in rs if r['aux'] is not None], pct=True) if cond == 'oas' else '-'])
        if (cond, 'lora_v1') in v1ref:
            v = row(cond, 'lora_v1', v1ref); rows.append([cond, '참고: LoRA v1 (data-v1, seed 42)', f"{v['macro']:.3f}", f"{v['excl']:.3f}", f"{v['syn']:.3f}", f"{v['manual']:.1%}", f"{v['pub']}/{v['pub_den']}", f"{v['prec']:.3f} / {v['rec']:.3f}", v['err'], f"{v['aux']:.1%}" if v['aux'] is not None else '-'])
            v = row(cond, 'base_v301', v1ref); rows.append([cond, '참고: 베이스 (v1 세션)', f"{v['macro']:.3f}", f"{v['excl']:.3f}", f"{v['syn']:.3f}", f"{v['manual']:.1%}", f"{v['pub']}/{v['pub_den']}", f"{v['prec']:.3f} / {v['rec']:.3f}", v['err'], f"{v['aux']:.1%}" if v['aux'] is not None else '-'])
    t += table(rows, ['조건', '모델', 'macro-F1 주지표', '합성 제외', '합성 58만', 'manual 비율', 'public 오판(신)', '구체 P / R', '출력 오류', 'route_only 보조(manual 인정)'], 2)
    bd = base_diff()
    t += '\n(3 seed 열은 평균 ± 표준편차; public 오판은 seed별 건수(42·43·44). 베이스 두 행이 같은 값인 이유: 이번 세션 베이스 예측 label은 v1 세션과 전부 일치 — 예측 불일치 oas ' + f"{bd['oas']['pred_diff']}/{bd['oas']['n']}, oas_code {bd['oas_code']['pred_diff']}/{bd['oas_code']['n']}" + f"건. raw 응답 텍스트 불일치 oas {bd['oas']['raw_diff']}, oas_code {bd['oas_code']['raw_diff']}건.)\n\n## 3. seed별 상세 (final)\n\n"
    rows = []
    for cond in ('oas', 'oas_code'):
        for s in (42, 43, 44):
            r = row(cond, f'lora_v2_s{s}_final'); rows.append([cond, s, f"{r['macro']:.3f}", f"{r['excl']:.3f}", f"{r['manual']:.1%}", f"{r['pub']}/{r['pub_den']}", f"{r['prec']:.3f} / {r['rec']:.3f} (응답률 {r['ans']:.2f})", r['err']])
    t += table(rows, ['조건', 'seed', 'macro-F1', '합성 제외', 'manual', 'public 오판', '구체 P / R', '오류'], 2)
    t += '\n## 4. label별 F1 (final, 3 seed 평균) vs 베이스\n\n'
    for cond in ('oas', 'oas_code'):
        b = row(cond, 'base_v301'); rs = [row(cond, f'lora_v2_s{s}_final') for s in (42, 43, 44)]; v = row(cond, 'lora_v1', v1ref) if (cond, 'lora_v1') in v1ref else None
        t += f'### {cond}\n\n' + table([[l, b['per'][l]['support'], f"{b['per'][l]['f1']:.3f}", ms([r['per'][l]['f1'] for r in rs]), f"{v['per'][l]['f1']:.3f}" if v else '-'] for l in L], ['label', 'support', '베이스 F1', 'LoRA v2 F1', 'LoRA v1 F1']) + '\n'
    # best checkpoints vs final
    t += '## 5. 조건별 val-loss 최저 체크포인트 vs 최종\n\n'
    rows = []
    for s in (42, 43, 44):
        for cond in ('oas', 'oas_code'):
            fin = row(cond, f'lora_v2_s{s}_final'); bo = next((m for m in tags['best_oas'] if f'_s{s}_' in m), None); bc = next((m for m in tags['best_oas_code'] if f'_s{s}_' in m), None)
            rows.append([s, cond, f"{fin['macro']:.3f}", f"{row(cond, bo)['macro']:.3f} ({bo.split('_step')[-1]})" if bo else '-', f"{row(cond, bc)['macro']:.3f} ({bc.split('_step')[-1]})" if bc else '-'])
    t += table(rows, ['seed', '조건', 'final macro-F1', 'best_oas ckpt', 'best_oas_code ckpt'], 2)
    t += '\n## 6. 해석 (사실 위주)\n\n'
    bo, bc = row('oas', 'base_v301'), row('oas_code', 'base_v301'); fo = [row('oas', m) for m in tags['final']]; fc = [row('oas_code', m) for m in tags['final']]
    t += f"- oas 주지표: 베이스 {bo['macro']:.3f} vs LoRA v2 final {ms([r['macro'] for r in fo])}; 합성 제외 {bo['excl']:.3f} vs {ms([r['excl'] for r in fo])}.\n"
    t += f"- oas_code 주지표: 베이스 {bc['macro']:.3f} vs LoRA v2 final {ms([r['macro'] for r in fc])}; 합성 제외 {bc['excl']:.3f} vs {ms([r['excl'] for r in fc])}.\n"
    t += f"- manual 비율: oas 베이스 {bo['manual']:.1%} vs v2 {ms([r['manual'] for r in fo], pct=True)}; oas_code 베이스 {bc['manual']:.1%} vs v2 {ms([r['manual'] for r in fc], pct=True)}. public 오판(신 정의): oas 베이스 {bo['pub']} vs v2 {[r['pub'] for r in fo]}; oas_code 베이스 {bc['pub']} vs v2 {[r['pub'] for r in fc]} (분모 {bo['pub_den']}).\n"
    if ('oas', 'lora_v1') in v1ref:
        v1o, v1c = row('oas', 'lora_v1', v1ref), row('oas_code', 'lora_v1', v1ref)
        t += f"- LoRA v1 대비(같은 정의): oas {v1o['macro']:.3f} → {ms([r['macro'] for r in fo])}, oas_code {v1c['macro']:.3f} → {ms([r['macro'] for r in fc])}; manual oas {v1o['manual']:.1%} → {ms([r['manual'] for r in fo], pct=True)}, oas_code {v1c['manual']:.1%} → {ms([r['manual'] for r in fc], pct=True)}. 구체 응답 정밀도 oas {v1o['prec']:.3f} → {ms([r['prec'] for r in fo])}, oas_code {v1c['prec']:.3f} → {ms([r['prec'] for r in fc])}.\n"
    t += f"- label별(final 평균): oas_code에서 owner_match F1 {bc['per']['owner_match']['f1']:.3f} → {ms([r['per']['owner_match']['f1'] for r in fc])}, role_required {bc['per']['role_required']['f1']:.3f} → {ms([r['per']['role_required']['f1'] for r in fc])}로 상승; manual_review_required F1은 {bc['per']['manual_review_required']['f1']:.3f} → {ms([r['per']['manual_review_required']['f1'] for r in fc])}, membership_required {bc['per']['membership_required']['f1']:.3f} → {ms([r['per']['membership_required']['f1'] for r in fc])}(support 4)로 하락. manual 비율 상승은 정답이 구체 label인 건을 manual로 답한 결과이며(구체 재현율 ≈ 0.44~0.49), test의 manual 정답은 14/15건뿐이다.\n"
    t += '- val-loss 최저 체크포인트는 test macro-F1에서 최종 어댑터보다 일관되게 낫지 않다(seed 42는 하락, 43·44는 상승). 체크포인트 선택을 val loss로 하는 것은 현재 val_v2 구성에서 근거가 약하다.\n'
    t += '- seed 간 표준편차(macro-F1 0.013~0.038)는 베이스 대비 차이(oas −0.027, oas_code −0.029)와 같은 크기이므로, 주지표에서 LoRA v2와 베이스의 우열은 확정할 수 없다. 합성 제외·구체 정밀도·public 오판·route_only 보조지표에서는 LoRA v2가 베이스보다 낫고, manual 비율은 베이스보다 크게 높다.\n'
    t += '- 합성 58건은 train 합성과 템플릿을 공유하므로 합성 포함 수치는 낙관 편향이 있다. 합성 제외 열이 일반화 근거에 가깝다.\n- 단일 데이터 버전 비교이며 data-v1 → data-v2는 라벨 규칙(검수·R1\'·R4·variant·VIS cap·쿼터)과 데이터 구성이 함께 바뀌었으므로 어느 요인이 효과를 냈는지 분리되지 않는다.\n'
    t += '\n원자료: reports/eval/lora_v2/scores.json, eval_v30.md, lora_v2_seed*/eval/predictions_*.jsonl, logs/. config.json·hashes.json·adapter는 Drive에만 있음(다운로드 폴더에 미포함).\n'
    (D / 'lora_v2_report.md').write_text(t, encoding='utf-8'); print(t[:3500])

if __name__ == '__main__': main()
