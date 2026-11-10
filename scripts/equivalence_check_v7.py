"""D1: GGUF Q4_K_M conversion-equivalence numbers for LoRA v7 s42 (test_v30 oas_code), same construction as the v5 check
(reports/eval/lora_v5_gguf/equivalence_check.md, equivalence_numbers.json). Nothing is tuned on test_v30; this only compares the
deployed model (Ollama GGUF) with the SAME adapter's HF final predictions (RunPod, 4bit base, bf16 inference).

Inputs (all produced beforehand, no inference here):
  --scores     scores json from scripts/eval_v30.py --pred <gguf predictions> <hf s42 predictions>  (models lora_v7_s42_gguf_q4km, lora_v7_s42_final)
  --gguf/--hf  the two prediction files (row-level agreement, transitions, who is right on mismatches)
  --template   template_check.log from eval_ollama_v7.py --check-template (json lines)
Tolerance (pre-registered 2026-11-10 before any GGUF result was seen, AGENTS.md 작업 D1 "v5 때와 같은 허용 폭"):
  primary  = the SAME widths that were applied at the v5 check, i.e. LoRA v4 3-seed sd (macro-F1 207 0.0454, concrete precision 207 0.0255, concrete precision 265 0.0175);
  also reported = v5 3-seed sd and v7 3-seed sd (reports/eval/lora_v5|lora_v7/scores_test_v30.json). Decision proposal = all three primary metrics within the primary width;
  otherwise "조건부 수용 제안" to the user (v4/v5 precedent: abstention shift, not degradation).
Usage: python -X utf8 scripts/equivalence_check_v7.py --scores reports/eval/lora_v7_gguf/scores_test_v30.json \
         --gguf reports/eval/lora_v7_gguf/predictions_oas_code_lora_v7_s42_gguf_q4km.jsonl --hf reports/eval/lora_v7/lora_v7_s42/eval/predictions_oas_code_lora_v7_s42_final.jsonl \
         --template reports/eval/lora_v7_gguf/template_check.log --out-dir reports/eval/lora_v7_gguf
"""
from __future__ import annotations
import argparse, json, statistics as st
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUAL = 'manual_review_required'
METRICS = dict(f1_207=('main_excl_synthetic', 'macro_f1'), p_207=('main_excl_synthetic', 'concrete', 'precision'), r_207=('main_excl_synthetic', 'concrete', 'recall'),
               p_265=('main', 'concrete', 'precision'), f1_265=('main', 'macro_f1'), manual_265=('main', 'manual_ratio'))
PRIMARY = ['f1_207', 'p_207', 'p_265']
NAMES = dict(f1_207='macro-F1 합성 제외 207 (주지표)', p_207='구체 정밀도 합성 제외 207', r_207='구체 재현율 합성 제외 207', p_265='구체 정밀도 265', f1_265='macro-F1 265', manual_265='manual 비율 265')
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]


def get(d, path):
    for k in path: d = d[k]
    return d


def pick(scores, model):
    r = [e for e in scores if e['condition'] == 'oas_code' and e['eval_def'] == 'v2' and e['model'] == model]
    assert len(r) == 1, f'{model}: {len(r)} oas_code/v2 entries'
    return r[0]


def seeds(scores, prefix):
    rows = [e for e in scores if e['condition'] == 'oas_code' and e['eval_def'] == 'v2' and e['model'].startswith(prefix) and e['model'].endswith('_final')]
    assert len(rows) == 3, (prefix, [e['model'] for e in rows])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scores', type=Path, required=True); ap.add_argument('--gguf', type=Path, required=True); ap.add_argument('--hf', type=Path, required=True)
    ap.add_argument('--template', type=Path); ap.add_argument('--out-dir', type=Path, default=ROOT / 'reports/eval/lora_v7_gguf')
    ap.add_argument('--gguf-model', default='lora_v7_s42_gguf_q4km'); ap.add_argument('--hf-model', default='lora_v7_s42_final')
    ap.add_argument('--v5-scores', type=Path, default=ROOT / 'reports/eval/lora_v5/scores_test_v30.json'); ap.add_argument('--v7-scores', type=Path, default=ROOT / 'reports/eval/lora_v7/scores_test_v30.json')
    a = ap.parse_args()
    sc = json.load(open(a.scores, encoding='utf-8')); g, h = pick(sc, a.gguf_model), pick(sc, a.hf_model)
    s5 = json.load(open(a.v5_scores, encoding='utf-8')); s7 = json.load(open(a.v7_scores, encoding='utf-8'))
    ref = dict(v4=seeds(s5, 'lora_v4_s'), v5=seeds(s5, 'lora_v5_s'), v7=seeds(s7, 'lora_v7_s'))
    out = dict(gguf={k: get(g, p) for k, p in METRICS.items()}, hf_s42={k: get(h, p) for k, p in METRICS.items()})
    for m in ('gguf', 'hf_s42'):
        e = g if m == 'gguf' else h
        out[m].update(err=e['main']['output_errors'], pub_new=e['public_misjudge_new']['count'], pub_den=e['public_misjudge_new']['denominator'], pub_ids=e['public_misjudge_new']['ids'])
    for k, p in METRICS.items():
        d = dict(gguf=out['gguf'][k], hf_s42=out['hf_s42'][k], diff=round(out['gguf'][k] - out['hf_s42'][k], 4))
        for v, rows in ref.items():
            vals = [get(r, p) for r in rows]; d[f'{v}_mean'] = round(st.mean(vals), 4); d[f'{v}_sd'] = round(st.stdev(vals), 4); d[f'within_{v}_sd'] = abs(d['diff']) <= d[f'{v}_sd']
        out[k] = d
    out['tolerance'] = dict(rule='pre-registered 2026-11-10: primary width = v4 3-seed sd (the widths applied at the v5 check); v5 sd and v7 sd reported alongside',
                            primary_metrics=PRIMARY, primary_width={k: out[k]['v4_sd'] for k in PRIMARY},
                            primary_pass={k: out[k]['within_v4_sd'] for k in PRIMARY}, all_primary_pass=all(out[k]['within_v4_sd'] for k in PRIMARY),
                            v5_width_pass={k: out[k]['within_v5_sd'] for k in PRIMARY}, v7_width_pass={k: out[k]['within_v7_sd'] for k in PRIMARY})
    # row level
    G = {r['id']: r for r in rd(a.gguf)}; H = {r['id']: r for r in rd(a.hf)}; ids = [i for i in H if i in G]
    lab = lambda r: r['prediction']['label'] if r.get('prediction') else 'output_error'
    mism = [i for i in ids if lab(G[i]) != lab(H[i])]
    conc = lambda x: x not in (MANUAL, 'output_error')
    trans = Counter(f'{lab(H[i])}->{lab(G[i])}' for i in mism)
    out['rows'] = dict(n=len(ids), match=len(ids) - len(mism), mismatch=len(mism),
                       hf_hold_or_error_to_gguf_concrete=sum(not conc(lab(H[i])) and conc(lab(G[i])) for i in mism),
                       gguf_hold_or_error_from_hf_concrete=sum(conc(lab(H[i])) and not conc(lab(G[i])) for i in mism),
                       concrete_to_other_concrete=sum(conc(lab(H[i])) and conc(lab(G[i])) for i in mism),
                       mismatch_correct_hf=sum(lab(H[i]) == H[i]['label'] for i in mism), mismatch_correct_gguf=sum(lab(G[i]) == G[i]['label'] for i in mism),
                       output_errors=dict(gguf=sum(lab(G[i]) == 'output_error' for i in ids), hf=sum(lab(H[i]) == 'output_error' for i in ids)),
                       top_transitions=trans.most_common(10), mean_inference_s_gguf=round(st.mean(G[i].get('inference_ms', 0) for i in ids) / 1000, 2))
    if a.template and a.template.exists():
        out['template_check'] = [json.loads(l) for l in open(a.template, encoding='utf-8') if l.startswith('{') and 'hf_prompt_tokens' in l]
    a.out_dir.mkdir(parents=True, exist_ok=True)
    (a.out_dir / 'equivalence_numbers.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    t = '# GGUF Q4_K_M 변환 동등성 확인 — LoRA v7 s42 (test_v30 oas_code, 튜닝 없음) — 판정 제안 (사용자 확정 전)\n\n'
    t += '비교 대상은 **같은 어댑터(lora_v7_s42 final)의 HF 예측**(reports/eval/lora_v7/lora_v7_s42/eval/predictions_oas_code_lora_v7_s42_final.jsonl, RunPod 4bit 학습 환경·bf16 추론). GGUF 추론은 Pod GPU Ollama(/api/chat, Modelfile.blade-qwen-lora-v7, greedy·repeat_penalty 1·num_predict 256·num_ctx 8192), eval_ollama_v7.py. 채점 scripts/eval_v30.py(eval-def v2).\n\n'
    t += '## 수치 (equivalence_numbers.json)\n\n| 지표 | GGUF Q4_K_M | HF s42 final | 차이 | 허용 폭(주, v4 3-seed sd = v5 때 적용 폭) | 판정 | v5 sd | v7 sd |\n|---|---:|---:|---:|---:|---|---:|---:|\n'
    for k in METRICS:
        d = out[k]; judge = ('안' if d['within_v4_sd'] else ('이탈(상승)' if d['diff'] > 0 else '이탈(하락)')) if k in PRIMARY or k in ('r_207', 'f1_265') else ''
        t += f"| {NAMES[k]}{' (주)' if k in PRIMARY else ''} | {d['gguf']:.4f} | {d['hf_s42']:.4f} | {d['diff']:+.4f} | {d['v4_sd']:.4f} | {judge} | {d['v5_sd']:.4f}{'' if d['within_v5_sd'] else ' (이탈)'} | {d['v7_sd']:.4f}{'' if d['within_v7_sd'] else ' (이탈)'} |\n"
    t += f"| 출력 오류 265 | {out['gguf']['err']} | {out['hf_s42']['err']} | {out['gguf']['err'] - out['hf_s42']['err']:+d} | | | | |\n"
    t += f"| public 오판(신, /{out['gguf']['pub_den']}) | {out['gguf']['pub_new']} | {out['hf_s42']['pub_new']} | {out['gguf']['pub_new'] - out['hf_s42']['pub_new']:+d} | | | | |\n\n"
    r = out['rows']
    t += f"- 행 단위 label 일치 {r['match']}/{r['n']} ({r['match'] / r['n']:.1%}). 불일치 {r['mismatch']}건 중 HF 보류/오류 → GGUF 구체 {r['hf_hold_or_error_to_gguf_concrete']}, 그 반대 {r['gguf_hold_or_error_from_hf_concrete']}, 구체↔구체 {r['concrete_to_other_concrete']}. 불일치에서 정답을 맞힌 쪽은 GGUF {r['mismatch_correct_gguf']} / HF {r['mismatch_correct_hf']}. 상위 전이: {', '.join(f'{k} {v}' for k, v in r['top_transitions'][:6])}.\n"
    t += f"- GGUF public 오판 id: {', '.join(out['gguf']['pub_ids']) or '없음'}; HF: {', '.join(out['hf_s42']['pub_ids']) or '없음'}.\n"
    if out.get('template_check'):
        t += f"- 템플릿 검사 {len(out['template_check'])}건: HF chat_template 토큰 수 = Ollama raw = Ollama chat ({', '.join(str(x['hf_prompt_tokens']) for x in out['template_check'])}).\n"
    tol = out['tolerance']
    t += '\n## 판정 제안 (사전 기록 2026-11-10: "v5 때와 같은 허용 폭" = v4 3-seed sd)\n\n'
    t += f"- 주지표 3개({', '.join(NAMES[k] for k in PRIMARY)}) 허용 폭 안: {sum(tol['primary_pass'].values())}/3 → **{'수용 제안' if tol['all_primary_pass'] else '조건부 수용 제안(사용자 판단)'}**.\n"
    t += f"- 참고: v5 3-seed sd 기준 {sum(tol['v5_width_pass'].values())}/3, v7 3-seed sd 기준 {sum(tol['v7_width_pass'].values())}/3 (좁은 폭으로 읽으면 이탈 방향을 병기).\n"
    t += '- 발표·보고서 성능 수치는 LoRA v7 3-seed(HF) 평가(reports/eval/lora_v7/presentation_numbers_v7.md)를 유지하고, 위 GGUF 수치는 "배포 모델 변환 동등성 확인"으로만 표기한다.\n'
    (a.out_dir / 'equivalence_check.md').write_text(t, encoding='utf-8')
    print(json.dumps({k: out[k] for k in METRICS}, ensure_ascii=False, indent=1)); print(json.dumps(out['tolerance'], ensure_ascii=False, indent=1)); print('rows', json.dumps(r, ensure_ascii=False))


if __name__ == '__main__':
    main()
