"""[S1-4 item 4] Confidence-threshold accuracy / abstention curve of LoRA v5 (3 seeds) on test_v5 283 (oas_code). No inference:
reads the existing prediction files reports/eval/lora_v5/lora_v5_s{42,43,44}/eval/v5test_predictions_oas_code_*.jsonl.
Rule at threshold t: a concrete prediction with confidence < t (or a parse failure) is held as manual_review_required
(same rule as training/lora/choose_threshold_v4.py; the pipeline floor 0.7 is not applied here so that t in [0.5, 0.7) is visible).
Metrics per t: 보류율 = held / 283, 유지 건 정확도 = correct / retained concrete predictions, 전체 정확도 (held counts as correct iff
truth is manual), macro-F1 over labels with support. Thresholds 0.50..0.95 step 0.05 and 0.99.
Output: reports/eval/human_agreement_v5/confidence_curve_test_v5.{json,md}"""
from __future__ import annotations
import hashlib, json, statistics as st
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / 'datasets/blade/processed/test_v5.jsonl'; MANIFEST = ROOT / 'datasets/blade/processed/data_v5/test_v5_manifest.json'
OUT = ROOT / 'reports/eval/human_agreement_v5'; PRED_DIR = ROOT / 'reports/eval/lora_v5'
L = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']; MANUAL = L[-1]
SEEDS = [42, 43, 44]; TS = [round(0.5 + 0.05 * i, 2) for i in range(10)] + [0.99]
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]


def apply(row, t):
    p = row.get('prediction')
    if not p or not isinstance(p.get('confidence'), (int, float)): return MANUAL, 'error'
    if p['label'] != MANUAL and p['confidence'] < t: return MANUAL, 'held'
    return p['label'], ('manual' if p['label'] == MANUAL else 'kept')


def metrics(pairs):
    per = {}
    for l in L:
        tp = sum(a == l and b == l for a, b in pairs); fp = sum(a != l and b == l for a, b in pairs); fn = sum(a == l and b != l for a, b in pairs)
        P = tp / (tp + fp) if tp + fp else 0.; R = tp / (tp + fn) if tp + fn else 0.
        per[l] = dict(support=sum(a == l for a, _ in pairs), f1=round(2 * P * R / (P + R), 4) if P + R else 0.)
    sup = [l for l in L if per[l]['support']]
    return round(sum(per[l]['f1'] for l in sup) / len(sup), 4), round(sum(a == b for a, b in pairs) / len(pairs), 4)


def main():
    man = json.loads(MANIFEST.read_text(encoding='utf-8')); assert hashlib.sha256(TEST.read_bytes()).hexdigest() == man['sha256']['datasets/blade/processed/test_v5.jsonl']
    truth = {r['id']: r['label'] for r in rd(TEST)}; n = len(truth); res = dict(n=n, thresholds=TS, seeds={}, confidence_values={})
    for s in SEEDS:
        p = PRED_DIR / f'lora_v5_s{s}/eval/v5test_predictions_oas_code_lora_v5_s{s}_final.jsonl'; rows = [r for r in rd(p) if r['id'] in truth]; assert len(rows) == n
        res['confidence_values'][f's{s}'] = dict(sorted(Counter(str(round(r['prediction']['confidence'], 2)) if r.get('prediction') else 'error' for r in rows).items()))
        curve = []
        for t in TS:
            out = [(truth[r['id']],) + apply(r, t) for r in rows]
            kept = [(a, b) for a, b, k in out if k == 'kept']; held = sum(k in ('held', 'error') for *_, k in out); man_pred = sum(k == 'manual' for *_, k in out)
            mf, acc = metrics([(a, b) for a, b, _ in out])
            curve.append(dict(t=t, retained=len(kept), retained_accuracy=round(sum(a == b for a, b in kept) / len(kept), 4) if kept else None,
                              held_by_threshold=held, predicted_manual=man_pred, abstention=round((held + man_pred) / n, 4), accuracy=acc, macro_f1=mf))
        res['seeds'][f's{s}'] = dict(file=p.relative_to(ROOT).as_posix(), curve=curve)
    (OUT / 'confidence_curve_test_v5.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    t = ['# LoRA v5 confidence 문턱별 정확도–보류율 (test_v5 283, oas_code, 3 seed)', '',
         '기존 예측 파일만 읽음(재추론 없음). 문턱 t에서 confidence < t인 구체 예측과 출력 오류는 manual(보류)로 둔다. 파이프라인 바닥 0.7은 적용하지 않았다(0.5~0.7 구간을 보이기 위해).', '',
         '## 모델이 낸 confidence 값 분포', '', '| seed | 값: 건수 |', '|---|---|']
    for s in SEEDS: t.append(f"| s{s} | " + ', '.join(f'{k}: {v}' for k, v in res['confidence_values'][f's{s}'].items()) + ' |')
    t += ['', '## 문턱별 곡선', '', '보류율 = (문턱으로 보류 + manual 예측) / 283. 유지 건 정확도 = 유지된 구체 예측 중 정답 일치 비율. 전체 정확도는 보류를 manual 예측으로 두고 7 label로 채점.', '',
          '| t | ' + ' | '.join(f's{s} 유지 n / 유지 정확도 / 보류율 / 전체 정확도 / macro-F1' for s in SEEDS) + ' | 평균 보류율 | 평균 전체 정확도 | 평균 macro-F1 |', '|---|' + '---|' * SEEDS.__len__() + '---:|---:|---:|']
    for i, th in enumerate(TS):
        cells = []; ab, ac, mf = [], [], []
        for s in SEEDS:
            c = res['seeds'][f's{s}']['curve'][i]; ab.append(c['abstention']); ac.append(c['accuracy']); mf.append(c['macro_f1'])
            cells.append(f"{c['retained']} / {c['retained_accuracy'] if c['retained_accuracy'] is not None else '-'} / {c['abstention']:.3f} / {c['accuracy']:.3f} / {c['macro_f1']:.3f}")
        t.append(f'| {th:.2f} | ' + ' | '.join(cells) + f' | {st.mean(ab):.3f} | {st.mean(ac):.3f} | {st.mean(mf):.3f} |')
    flat = all(len([k for k in res['confidence_values'][f's{s}'] if k != 'error']) == 1 for s in SEEDS)
    t += ['', '## 해석', '',
          ('- HF 평가(기본 디코딩)의 v5 3 seed는 test_v5 전 건에서 confidence를 0.9 하나만 냈다(출력 오류 제외). 따라서 t ≤ 0.9 구간은 문턱과 무관하게 같은 값이고, t > 0.9에서는 전부 보류된다. **곡선이 평탄해 confidence 문턱으로 정확도–보류율을 조절할 수 없다.**' if flat else '- confidence 값이 여러 개라 문턱이 곡선을 만든다.'),
          '- 같은 현상은 test_v30(265)·test_v31_supp(222)의 HF 예측에서도 거의 같다(0.9가 98% 이상, s44 test_v30만 0.85 2건). 프롬프트 v3.0.1의 confidence 지침(0.9+/0.75/0.6/0.4)은 학습 데이터가 0.9에 몰려 있어 모델이 구분해 쓰지 못한다.',
          '- 예외: GGUF Q4_K_M(Ollama) 추론은 val_v5에서 0.7~1.0 분포를 냈다(reports/eval/lora_v5_gguf/threshold_val_v5.json: 0.7 3·0.8 2·0.85 20·0.9 135·1.0 18). test_v5에 실제 곡선을 그리려면 GGUF 경로 추론이 필요하며 이 작업(추론 없음) 범위 밖이다.',
          '- 보류율을 바꾸는 수단은 현재로선 문턱이 아니라 (a) 라벨 정의·학습 데이터의 manual 비율, (b) 다수결(S2, 보조 지표) 등이다. 주지표·발표 수치는 바꾸지 않는다.']
    (OUT / 'confidence_curve_test_v5.md').write_text('\n'.join(t) + '\n', encoding='utf-8')
    for s in SEEDS: print(s, [(c['t'], c['abstention'], c['accuracy'], c['macro_f1']) for c in res['seeds'][f's{s}']['curve'] if c['t'] in (0.5, 0.9, 0.95)])


if __name__ == '__main__': main()
