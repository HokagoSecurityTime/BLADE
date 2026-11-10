"""작업 S2 (2026-11-03): LoRA v5 3 seed 다수결(ensemble vote) 재채점 — 학습·추론 없음, 보조 지표.
대상: test_v30 oas_code 합성 제외 207 · test_v31_supp oas_code 222 · test_v5 oas_code 283. 기존 seed 42·43·44 예측 파일만 읽는다.

동률 규칙(AGENTS.md '작업 S2' 절, 채점 전 사전 기록):
- 3 seed가 모두 다르면 seed 42 예측.
- 출력 오류는 기권. 나머지 2개로 다수결, 그래도 동률이면 seed 42 예측(seed 42 자체가 기권이면 출력 오류). 3개 모두 기권이면 출력 오류.
지표 정의는 scripts/eval_combined_v5.py metrics()와 동일(7-class, macro-F1은 support>0 label 평균, 구체 정밀도·재현율은 eval_v30.py concrete()).
단일 seed 평균 ± 표본 표준편차와 나란히 표기. 주지표·발표 수치는 바꾸지 않는다."""
from __future__ import annotations
import json, statistics as st, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from eval_combined_v5 import L, MANUAL, V5, metrics, preds, truth_sets, verify, sha, TEST30, SUPP_SHA, TEST5, MANIFEST5_SHA
from data_v1_guard import assert_data_v1

SEEDS = [42, 43, 44]
OUT_JSON = ROOT / 'reports/eval/lora_v5/scores_ensemble_vote.json'; OUT_MD = ROOT / 'reports/eval/lora_v5/ensemble_vote.md'
SETS = [('test_v30_207', 'test_v30 oas_code 합성 제외'), ('test_v31_supp', 'test_v31_supp oas_code'), ('test_v5', 'test_v5 oas_code')]


def vote(votes):
    """votes: seed 순서(42, 43, 44)의 label 리스트('output_error' 포함). 반환 (label, 사유)."""
    valid = [v for v in votes if v != 'output_error']
    if not valid: return 'output_error', 'all_abstain'
    c = Counter(valid); top, n = c.most_common(1)[0]
    if n >= 2: return top, 'majority' if len(valid) == 3 else 'majority_after_abstain'
    if len(valid) == 1: return valid[0], 'single_valid'
    # 동률: 3개 모두 다름(len 3) 또는 기권 후 2개 불일치(len 2) → seed 42
    s42 = votes[0]
    if s42 == 'output_error': return 'output_error', 'tie_seed42_abstain'
    return s42, 'tie_all_differ' if len(valid) == 3 else 'tie_after_abstain'


def ms(vals, pct=False):
    mu, sd = st.mean(vals), st.stdev(vals)
    return f'{mu*100:.1f} ± {sd*100:.1f}%' if pct else f'{mu:.3f} ± {sd:.3f}'


def f3(v, pct=False): return f'{v*100:.1f}%' if pct else f'{v:.3f}'


def main():
    verify(); T = truth_sets(); out = {}
    for kind, title in SETS:
        truth = T[kind]; seed_preds = {}; files = []
        for s in SEEDS:
            p, pr = preds(V5 / f'lora_v5_s{s}', f'lora_v5_s{s}_final', kind); files.append(str(p.relative_to(ROOT)).replace('\\', '/'))
            assert all(i in pr for i in truth), (kind, s); seed_preds[s] = pr
        single = {s: metrics([(truth[i], seed_preds[s][i]) for i in truth]) for s in SEEDS}
        voted = {}; reasons = Counter(); tie_ids = []
        for i in truth:
            vs = [seed_preds[s][i] for s in SEEDS]; lab, why = vote(vs); voted[i] = lab; reasons[why] += 1
            if why.startswith('tie'): tie_ids.append(dict(id=i, truth=truth[i], votes=dict(zip(map(str, SEEDS), vs)), chosen=lab, reason=why))
        ens = metrics([(truth[i], voted[i]) for i in truth])
        # 단일 seed와 다수결이 다른 레코드 수, 다수결이 맞고 각 seed가 틀린 건수 등
        agree3 = sum(len({seed_preds[s][i] for s in SEEDS}) == 1 for i in truth)
        flips = {str(s): dict(changed=sum(voted[i] != seed_preds[s][i] for i in truth), gained=sum(voted[i] == truth[i] != seed_preds[s][i] for i in truth), lost=sum(seed_preds[s][i] == truth[i] != voted[i] for i in truth)) for s in SEEDS}
        out[kind] = dict(title=title, files=files, records=len(truth), unanimous=agree3, vote_reasons=dict(reasons), tie_records=tie_ids, single={str(s): single[s] for s in SEEDS}, ensemble=ens, flips_vs_seed=flips,
                         voted_labels={i: voted[i] for i in truth})
    assert_data_v1('end')
    json.dump(dict(definition=__doc__, truth_hashes=dict(test_v30=sha(TEST30), test_v31_supp=SUPP_SHA, test_v5=sha(TEST5), test_v5_manifest=MANIFEST5_SHA), sets=out), open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    t = '# 작업 S2 — LoRA v5 3 seed 다수결 재채점 (보조 지표, 학습·추론 없음)\n\n'
    t += '2026-11-03. 기존 v5 seed 42·43·44 예측 파일(reports/eval/lora_v5/lora_v5_s*/eval/, oas_code, 기본 디코딩)을 레코드별 label 다수결로 합쳐 재채점했다. 재추론 없음. 주지표(test_v30 207 단일 seed 평균)와 발표 수치(presentation_numbers_v5.md)는 바꾸지 않는다.\n\n'
    t += '동률 규칙(채점 전 AGENTS.md에 기록): 3 seed가 모두 다르면 seed 42 예측. 출력 오류는 기권으로 보고 나머지 2개로 다수결, 그래도 동률이면 seed 42 예측(seed 42가 기권이면 출력 오류). 지표 정의는 scripts/eval_combined_v5.py와 같다(7-class, macro-F1은 support>0 label 평균, 구체 정밀도 = 정답 구체 건 중 구체로 답한 건의 정답률, 구체 재현율 = 정답 구체 건 전체 대비 정답률). 단일 seed 열은 3 seed 평균 ± 표본 표준편차.\n\n'
    t += '## 1. 요약 (단일 seed 평균 ± sd vs 다수결)\n\n| 셋 | n | 지표 | 단일 seed (3) | 다수결 | 차이 | sd 초과 |\n|---|---:|---|---:|---:|---:|:--:|\n'
    for kind, title in SETS:
        o = out[kind]; S = [o['single'][str(s)] for s in SEEDS]; E = o['ensemble']
        rows = [('macro-F1', [x['macro_f1'] for x in S], E['macro_f1'], False), ('정확도', [x['accuracy'] for x in S], E['accuracy'], False),
                ('구체 정밀도', [x['concrete']['precision'] for x in S], E['concrete']['precision'], False), ('구체 재현율', [x['concrete']['recall'] for x in S], E['concrete']['recall'], False),
                ('구체 응답률', [x['concrete']['answer_rate'] for x in S], E['concrete']['answer_rate'], False), ('manual 비율', [x['manual_ratio'] for x in S], E['manual_ratio'], True)]
        for name, vals, ev, pct in rows:
            mu, sd = st.mean(vals), st.stdev(vals); d = ev - mu
            dtxt = f'{d*100:+.1f}%p' if pct else f'{d:+.3f}'
            t += f"| {title} | {o['records']} | {name} | {ms(vals, pct)} | {f3(ev, pct)} | {dtxt} | {'예' if abs(d) > sd else '아니오'} |\n"
        t += f"| {title} | {o['records']} | 출력 오류 | {' / '.join(str(x['output_errors']) for x in S)} | {E['output_errors']} | - | - |\n"
    t += '\n"sd 초과"는 다수결과 단일 seed 평균의 차이 절대값이 3 seed 표본 표준편차보다 큰지 여부(작업 C 규칙: 표준편차보다 큰 차이만 차이로 인정). manual 비율 열의 sd 초과도 같은 기준이다.\n\n'
    t += '## 2. label별 F1 (support)\n\n'
    for kind, title in SETS:
        o = out[kind]; S = [o['single'][str(s)] for s in SEEDS]; E = o['ensemble']
        sup = [l for l in L if E['per_label'][l]['support']]
        t += f"### {title} ({o['records']}건)\n\n| label (support) | 단일 seed F1 | 다수결 F1 | 차이 | 다수결 P / R |\n|---|---:|---:|---:|---:|\n"
        for l in sup:
            vals = [x['per_label'][l]['f1'] for x in S]; ev = E['per_label'][l]['f1']
            t += f"| {l} ({E['per_label'][l]['support']}) | {ms(vals)} | {f3(ev)} | {ev - st.mean(vals):+.3f} | {E['per_label'][l]['precision']:.3f} / {E['per_label'][l]['recall']:.3f} |\n"
        if len(sup) < len(L): t += f"\n정답 support 0인 label(제외): {', '.join(l for l in L if l not in sup)}\n"
        t += '\n'
    t += '## 3. 다수결 구성\n\n| 셋 | n | 3 seed 일치 | 과반(3개 유효) | 기권 후 과반 | 유효 1개 | 동률(3개 다름→s42) | 기권 후 동률→s42 | s42 기권 동률→오류 | 전부 기권 |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n'
    for kind, title in SETS:
        o = out[kind]; r = o['vote_reasons']
        t += f"| {title} | {o['records']} | {o['unanimous']} | {r.get('majority', 0)} | {r.get('majority_after_abstain', 0)} | {r.get('single_valid', 0)} | {r.get('tie_all_differ', 0)} | {r.get('tie_after_abstain', 0)} | {r.get('tie_seed42_abstain', 0)} | {r.get('all_abstain', 0)} |\n"
    t += '\n### 다수결이 각 seed 단독 예측을 바꾼 건수 (정답 기준 득·실)\n\n| 셋 | seed | 바뀐 건 | 오답→정답 | 정답→오답 | 순득 |\n|---|---:|---:|---:|---:|---:|\n'
    for kind, title in SETS:
        for s in SEEDS:
            f = out[kind]['flips_vs_seed'][str(s)]; t += f"| {title} | {s} | {f['changed']} | {f['gained']} | {f['lost']} | {f['gained'] - f['lost']:+d} |\n"
    t += '\n### 동률 레코드 (seed 42 규칙 적용)\n\n'
    any_tie = False
    for kind, title in SETS:
        ties = out[kind]['tie_records']
        if not ties: continue
        any_tie = True; t += f"{title}:\n\n| id | 정답 | s42 | s43 | s44 | 채택 | 사유 |\n|---|---|---|---|---|---|---|\n"
        for x in ties: t += f"| {x['id']} | {x['truth']} | {x['votes']['42']} | {x['votes']['43']} | {x['votes']['44']} | {x['chosen']} | {x['reason']} |\n"
        t += '\n'
    if not any_tie: t += '동률 레코드 없음.\n\n'
    t += '## 4. 비고\n\n'
    t += '- 다수결은 3 seed 모두의 추론을 요구하므로(추론 비용 3배) 배포 모델(단일 어댑터 s42 GGUF)과 조건이 다르다. 보조 지표로만 기록하며 주지표·발표 수치·판정에 쓰지 않는다.\n'
    t += '- 단일 seed 값은 scores_test_v30.json(main_excl_synthetic)·scores_supp.json·scores_test_v5.json의 oas_code v5 값과 같다(같은 예측 파일, 같은 정의).\n'
    t += '- 예측 파일: ' + '; '.join(f"{title}: " + ', '.join(out[kind]['files']) for kind, title in SETS) + '\n'
    t += f"- 정답 해시: test_v30 {sha(TEST30)[:16]}…, test_v31_supp {SUPP_SHA[:16]}…, test_v5 {sha(TEST5)[:16]}… (manifest {MANIFEST5_SHA[:16]}…). 원자료 scores_ensemble_vote.json(레코드별 다수결 label 포함). 생성 scripts/eval_ensemble_vote_v5.py.\n"
    OUT_MD.write_text(t, encoding='utf-8', newline='\r\n'); print(OUT_MD.relative_to(ROOT), OUT_JSON.relative_to(ROOT))


if __name__ == '__main__':
    main()
