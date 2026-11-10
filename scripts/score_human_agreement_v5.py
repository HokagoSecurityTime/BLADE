"""[S1-3] Scoring of returned agreement sheets for the test_v5 60-record stratified sample (no training, no inference).
Inputs: two filled copies of review/human_agreement_v5_{A,B}.xlsx (column 'label', '확신도(상/중/하)', '근거 메모'),
reports/eval/human_agreement_v5/sample_60.json (ids), frozen test_v5.jsonl (hash-asserted) and the existing v5 3-seed oas_code
predictions (reports/eval/lora_v5/lora_v5_s*/eval/v5test_predictions_oas_code_*.jsonl, read only).
Computes A vs B (agreement, Cohen's kappa, macro-F1 with A as reference, per-label agreement), A/B vs frozen label, v5 per-seed
macro-F1 on the same 60 ids, and the three-way disagreement list. --kind ai_proxy marks the reviewers as Claude (AI), not humans.
Usage: python scripts/score_human_agreement_v5.py --a <xlsx> --b <xlsx> --kind ai_proxy --out report_ai_proxy.md"""
from __future__ import annotations
import argparse, hashlib, json, re, statistics as st
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / 'datasets/blade/processed/test_v5.jsonl'; MANIFEST = ROOT / 'datasets/blade/processed/data_v5/test_v5_manifest.json'
OUT = ROOT / 'reports/eval/human_agreement_v5'; PRED_DIR = ROOT / 'reports/eval/lora_v5'
L = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']
SEEDS = [42, 43, 44]; CONF = ['상', '중', '하']
KIND = {'ai_proxy': dict(title='AI 검수자(Claude) 간 일치도 — 사람 일치도 아님', who='검수자 Claude-A / Claude-B (AI 대리 검수, 사람 아님)', short='AI 검수자(Claude) 간 일치도, 사람 일치도 아님'),
        'human': dict(title='사람 검수자 간 일치도', who='검수자 A / B (사람)', short='사람 검수자 간 일치도')}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]


def read_sheet(path):
    from openpyxl import load_workbook
    ws = load_workbook(path, read_only=True)['human_agreement_v5']; rows = list(ws.iter_rows(values_only=True)); h = {n: i for i, n in enumerate(rows[0])}
    out = {}
    for r in rows[1:]:
        if not r or not r[h['id']]: continue
        lab = (r[h['label']] or '').strip() or None; conf = (r[h['확신도(상/중/하)']] or '').strip() or None
        assert lab is None or lab in L, (path, r[h['id']], lab); assert conf is None or conf in CONF, (path, r[h['id']], conf)
        out[r[h['id']]] = dict(label=lab, conf=conf, memo=(r[h['근거 메모']] or '').strip())
    return out


def per_label(pairs):
    """pairs: list of (reference, other). P/R/F1 per label (reference side defines support), macro over labels with support."""
    per = {}
    for l in L:
        tp = sum(a == l and b == l for a, b in pairs); fp = sum(a != l and b == l for a, b in pairs); fn = sum(a == l and b != l for a, b in pairs)
        P = tp / (tp + fp) if tp + fp else 0.; R = tp / (tp + fn) if tp + fn else 0.
        per[l] = dict(support=sum(a == l for a, _ in pairs), other_count=sum(b == l for _, b in pairs), tp=tp, precision=round(P, 4), recall=round(R, 4), f1=round(2 * P * R / (P + R), 4) if P + R else 0.)
    sup = [l for l in L if per[l]['support']]
    return per, round(sum(per[l]['f1'] for l in sup) / len(sup), 4)


def kappa(pairs):
    n = len(pairs); po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs); pe = sum(ca[l] * cb[l] for l in L) / (n * n)
    return round((po - pe) / (1 - pe), 4) if pe < 1 else 1.0, round(po, 4)


def compare(ref, oth):
    pairs = [(ref[i], oth[i]) for i in ref]; k, po = kappa(pairs); per, mf = per_label(pairs)
    return dict(n=len(pairs), agreement=po, kappa=k, macro_f1=mf, per_label=per, confusion={a: {b: sum(x == a and y == b for x, y in pairs) for b in L} for a in L})


def f3(v): return f'{v:.3f}'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--a', required=True); ap.add_argument('--b', required=True); ap.add_argument('--kind', choices=list(KIND), required=True)
    ap.add_argument('--out', default='report.md'); ap.add_argument('--json', default=None); a = ap.parse_args(); K = KIND[a.kind]
    man = json.loads(MANIFEST.read_text(encoding='utf-8')); assert sha(TEST) == man['sha256']['datasets/blade/processed/test_v5.jsonl'], 'test_v5.jsonl differs from the frozen manifest hash'
    samp = json.loads((OUT / 'sample_60.json').read_text(encoding='utf-8')); ids = [x['id'] for x in samp['ids']]
    truth = {r['id']: r for r in rd(TEST) if r['id'] in set(ids)}; assert len(truth) == len(ids)
    A, B = read_sheet(a.a), read_sheet(a.b)
    assert set(A) == set(ids) and set(B) == set(ids), 'sheet ids differ from sample_60'
    missing = [i for i in ids if not A[i]['label'] or not B[i]['label']]; assert not missing, f'unfilled labels: {missing}'
    la = {i: A[i]['label'] for i in ids}; lb = {i: B[i]['label'] for i in ids}; lt = {i: truth[i]['label'] for i in ids}
    ab, at, bt = compare(la, lb), compare(lt, la), compare(lt, lb)
    # v5 3 seeds on the same 60 ids (oas_code; the existing prediction files, no inference)
    v5 = {}
    for s in SEEDS:
        p = PRED_DIR / f'lora_v5_s{s}/eval/v5test_predictions_oas_code_lora_v5_s{s}_final.jsonl'
        pred = {r['id']: (r['prediction']['label'] if r.get('prediction') else 'output_error') for r in rd(p) if r['id'] in truth}; assert len(pred) == len(ids), p
        per, mf = per_label([(lt[i], pred[i]) for i in ids])
        v5[f's{s}'] = dict(file=p.relative_to(ROOT).as_posix(), macro_f1=mf, accuracy=round(sum(pred[i] == lt[i] for i in ids) / len(ids), 4),
                           manual_ratio=round(sum(pred[i] == 'manual_review_required' for i in ids) / len(ids), 4), output_errors=sum(pred[i] == 'output_error' for i in ids), per_label=per, pred=pred)
    v5_mf = [v5[s]['macro_f1'] for s in v5]; v5_acc = [v5[s]['accuracy'] for s in v5]
    # agreement by confidence
    conf_tab = {c: dict(n_A=sum(A[i]['conf'] == c for i in ids), A_vs_truth=sum(A[i]['conf'] == c and la[i] == lt[i] for i in ids),
                        n_B=sum(B[i]['conf'] == c for i in ids), B_vs_truth=sum(B[i]['conf'] == c and lb[i] == lt[i] for i in ids)) for c in CONF}
    dis = [dict(id=i, project=truth[i]['meta']['project'], method=truth[i]['method'], path=truth[i]['path'], truth=lt[i], A=la[i], A_conf=A[i]['conf'], B=lb[i], B_conf=B[i]['conf'],
                v5=[v5[f's{s}']['pred'][i] for s in SEEDS], A_memo=A[i]['memo'], B_memo=B[i]['memo'], kind=('A=B≠정답' if la[i] == lb[i] else 'A=정답≠B' if la[i] == lt[i] else 'B=정답≠A' if lb[i] == lt[i] else '셋 다 다름'))
           for i in ids if not (la[i] == lb[i] == lt[i])]
    res = dict(kind=a.kind, reviewers=K['who'], n=len(ids), sample='reports/eval/human_agreement_v5/sample_60.json', test_v5_sha256=man['sha256']['datasets/blade/processed/test_v5.jsonl'],
               inputs={'A': Path(a.a).relative_to(ROOT).as_posix() if Path(a.a).is_absolute() else a.a, 'B': Path(a.b).relative_to(ROOT).as_posix() if Path(a.b).is_absolute() else a.b},
               input_sha256={'A': sha(a.a), 'B': sha(a.b)}, label_dist=dict(truth=dict(Counter(lt.values())), A=dict(Counter(la.values())), B=dict(Counter(lb.values()))),
               A_vs_B=ab, A_vs_truth=at, B_vs_truth=bt, v5_oas_code={s: {k: v for k, v in v5[s].items() if k != 'pred'} for s in v5},
               v5_summary=dict(macro_f1_mean=round(st.mean(v5_mf), 4), macro_f1_sd=round(st.stdev(v5_mf), 4), accuracy_mean=round(st.mean(v5_acc), 4), accuracy_sd=round(st.stdev(v5_acc), 4)),
               by_confidence=conf_tab, all_three_agree=sum(la[i] == lb[i] == lt[i] for i in ids), disagreements=dis)
    (OUT / (a.json or a.out.replace('.md', '.json'))).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    # ---- markdown
    t = [f"# test_v5 라벨 상한 측정 (60건 표본) — {K['title']}", '',
         f"**주의: 이 보고서의 검수자는 {K['who']}이다.**" + (' 사람 간 일치도가 아니며, 사람 검수본이 회수되면 같은 스크립트로 다시 채점한다.' if a.kind == 'ai_proxy' else ''), '',
         f"- 표본: test_v5 283건(동결 SHA `{res['test_v5_sha256'][:16]}…`) 중 60건, label support 비례 층화(seed 42), reports/eval/human_agreement_v5/sample_60.json",
         f"- 입력: A = {res['inputs']['A']} (`{res['input_sha256']['A'][:16]}…`), B = {res['inputs']['B']} (`{res['input_sha256']['B'][:16]}…`). 두 시트는 현재 정답·AI 1차 판정·모델 예측 없이 엔드포인트·OAS·핸들러 코드·v3.0.1 라벨 정의만 제공했다.",
         '- 검수 규약 G1~G8은 시트에 넣지 않았다(지시의 "label 정의표(v3.0.1)"만 제공). 현재 정답은 G1~G8까지 적용해 확정한 것이므로 정답 대비 일치율은 보수적으로 읽는다.',
         '- v5 수치는 reports/eval/lora_v5/lora_v5_s{42,43,44}/eval의 기존 oas_code 예측을 같은 60건으로 재채점한 것이다(재추론 없음). 학습·추론 없음, 커밋 없음.',
         '- macro-F1은 기준(reference) 쪽 support>0인 label 평균(tenant_match는 정답 0건이라 제외; A/B가 tenant_match를 고른 경우 해당 label의 FP로만 반영). kappa는 7 label Cohen\'s kappa.', '',
         f"## 1. 요약 ({K['short']})", '', '| 비교 | n | 일치율 | Cohen\'s κ | macro-F1 | 비고 |', '|---|---:|---:|---:|---:|---|',
         f"| A vs B | {ab['n']} | {f3(ab['agreement'])} | {f3(ab['kappa'])} | {f3(ab['macro_f1'])} | A를 기준으로 둔 B |",
         f"| A vs 현재 정답 | {at['n']} | {f3(at['agreement'])} | {f3(at['kappa'])} | {f3(at['macro_f1'])} | 정답 기준 |",
         f"| B vs 현재 정답 | {bt['n']} | {f3(bt['agreement'])} | {f3(bt['kappa'])} | {f3(bt['macro_f1'])} | 정답 기준 |",
         f"| v5 3 seed vs 현재 정답 (oas_code) | 60 | {f3(res['v5_summary']['accuracy_mean'])} ± {f3(res['v5_summary']['accuracy_sd'])} | - | {f3(res['v5_summary']['macro_f1_mean'])} ± {f3(res['v5_summary']['macro_f1_sd'])} | seed별 " + ' / '.join(f"s{s} {f3(v5[f's{s}']['macro_f1'])}" for s in SEEDS) + ' |',
         '', f"세 쪽(A·B·정답) 모두 같은 건: {res['all_three_agree']}/{len(ids)}. 불일치 {len(dis)}건 유형: " + ', '.join(f'{k} {v}' for k, v in Counter(d['kind'] for d in dis).items()) + '.',
         '', '불일치 쌍 집계(정답 → A / B, 프로젝트별 건수):', '']
    pairs_cnt = Counter((d['truth'], d['A'], d['B'], d['project']) for d in dis)
    for (tr, xa, xb, pj), n in sorted(pairs_cnt.items(), key=lambda kv: (-kv[1], kv[0])): t.append(f'- {tr} → A {xa} / B {xb}: {pj} {n}건')
    t += ['',
         '## 2. label 분포 (60건)', '', '| label | 정답 | A | B | v5 s42 | v5 s43 | v5 s44 |', '|---|---:|---:|---:|---:|---:|---:|']
    for l in L:
        t.append(f"| {l} | {res['label_dist']['truth'].get(l, 0)} | {res['label_dist']['A'].get(l, 0)} | {res['label_dist']['B'].get(l, 0)} | " + ' | '.join(str(sum(v5[f's{s}']['pred'][i] == l for i in ids)) for s in SEEDS) + ' |')
    t += ['', '## 3. label별 일치 (A vs B, A 기준)', '', '| label | A가 고른 수 | B가 고른 수 | 둘 다(tp) | P | R | F1 |', '|---|---:|---:|---:|---:|---:|---:|']
    for l in L:
        p = ab['per_label'][l]; t.append(f"| {l} | {p['support']} | {p['other_count']} | {p['tp']} | {f3(p['precision'])} | {f3(p['recall'])} | {f3(p['f1'])} |")
    t += ['', '### A vs B 혼동표 (행 = A, 열 = B)', '', '| A \\ B | ' + ' | '.join(L) + ' |', '|---|' + '---:|' * len(L)]
    for x in L: t.append(f'| {x} | ' + ' | '.join(str(ab['confusion'][x][y]) for y in L) + ' |')
    t += ['', '## 4. label별 F1 — 현재 정답 기준 (support = 정답 건수)', '', '| label | support | A F1 | B F1 | v5 s42 | v5 s43 | v5 s44 | v5 평균 |', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for l in L:
        vs = [v5[f's{s}']['per_label'][l]['f1'] for s in SEEDS]
        t.append(f"| {l} | {at['per_label'][l]['support']} | {f3(at['per_label'][l]['f1'])} | {f3(bt['per_label'][l]['f1'])} | " + ' | '.join(f3(v) for v in vs) + f' | {f3(st.mean(vs))} |')
    t += ['', '### 정답 vs A 혼동표 (행 = 정답, 열 = A)', '', '| 정답 \\ A | ' + ' | '.join(L) + ' |', '|---|' + '---:|' * len(L)]
    for x in L: t.append(f'| {x} | ' + ' | '.join(str(at['confusion'][x][y]) for y in L) + ' |')
    t += ['', '### 정답 vs B 혼동표 (행 = 정답, 열 = B)', '', '| 정답 \\ B | ' + ' | '.join(L) + ' |', '|---|' + '---:|' * len(L)]
    for x in L: t.append(f'| {x} | ' + ' | '.join(str(bt['confusion'][x][y]) for y in L) + ' |')
    t += ['', '## 5. 확신도별 정답 일치', '', '| 확신도 | A n | A 일치 | B n | B 일치 |', '|---|---:|---:|---:|---:|']
    for c in CONF:
        x = conf_tab[c]; t.append(f"| {c} | {x['n_A']} | {x['A_vs_truth']} ({x['A_vs_truth'] / x['n_A']:.0%}) | {x['n_B']} | {x['B_vs_truth']} ({x['B_vs_truth'] / x['n_B']:.0%}) |" if x['n_A'] and x['n_B'] else f"| {c} | {x['n_A']} | {x['A_vs_truth']} | {x['n_B']} | {x['B_vs_truth']} |")
    t += ['', f'## 6. 불일치 목록 ({len(dis)}건; A·B·정답 중 하나라도 다른 건)', '', '| id | project | method path | 정답 | A (확신) | B (확신) | v5 s42/43/44 | 유형 |', '|---|---|---|---|---|---|---|---|']
    for d in dis:
        t.append(f"| {d['id']} | {d['project']} | {d['method']} {d['path']} | {d['truth']} | {d['A']} ({d['A_conf']}) | {d['B']} ({d['B_conf']}) | {' / '.join(d['v5'])} | {d['kind']} |")
    t += ['', '### 불일치 건 근거 메모 (시트 원문)', '']
    for d in dis: t += [f"- **{d['id']}** {d['method']} {d['path']} — 정답 {d['truth']} / A {d['A']} / B {d['B']}", f"  - A: {d['A_memo'] or '(없음)'}", f"  - B: {d['B_memo'] or '(없음)'}"]
    t += ['', '## 7. 해석 한계', '', f"- {K['short']}. " + ('두 검수자가 같은 모델(Claude)이라 독립 검수가 아니며, 같은 오류를 공유할 수 있어 A-B 일치율은 사람 간 일치율의 대체가 아니다. 사람 상한 측정은 사람 검수본 회수 후 별도 채점한다.' if a.kind == 'ai_proxy' else ''),
          '- 60건 표본이라 label별 support가 작다(owner_or_admin 4, public 4). label별 F1은 건수 변화 한두 건에 크게 움직인다.',
          '- 현재 정답은 AI 1차 판정 + 사람 확인으로 확정됐고(검수 규약 G1~G8 적용), 이 시트는 v3.0.1 정의만 제공했다. 규약 차이에서 오는 불일치(예: 그룹 안 역할 role_required, 구성원 OR 관리자 우회 membership_required)는 라벨 오류가 아니라 기준 차이일 수 있다.',
          '- v5 수치는 비교용 보조 지표이며 주지표·발표 수치(reports/eval/lora_v5/presentation_numbers_v5.md)는 바꾸지 않는다.']
    (OUT / a.out).write_text('\n'.join(t) + '\n', encoding='utf-8')
    print(json.dumps({k: res[k] for k in ('A_vs_B', 'A_vs_truth', 'B_vs_truth')} | dict(v5=res['v5_summary'], all_three=res['all_three_agree'], dis=len(dis)), ensure_ascii=False, default=lambda o: None)[:1500])


if __name__ == '__main__': main()
