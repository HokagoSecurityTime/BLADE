"""[작업 A] LoRA v4 보조 지표(사후 정의) 재채점. 학습·추론·문턱 변경 없음: reports/eval/lora_v4/*/eval/ 의 기존 예측 파일(oas_code 조건)만 읽는다.
주지표(eval-def v2 macro-F1, scripts/eval_v30.py)는 바꾸지 않는다. 데이터 해시(test_v30, test_v31_supp, segments.json, data-v1 guard)를 assert한다.

데이터 셋: A = test_v30 oas_code 합성 제외(207), B = test_v31_supp oas_code(222), C = A ∪ B(429).
지표 (모두 seed 평균 ± 표본표준편차; 베이스는 어댑터 없는 단일 run이라 편차 없음):
 1. 구체 label macro-F1(보류 제외): 예측 manual_review_required 와 출력 오류를 '보류'로 보고 보류 건을 뺀 나머지에서 6개 구체 label P/R/F1을 계산, 정답 support>0 인 구체 label 평균.
    커버리지 = 1 − 보류율(manual 예측 + 출력 오류). 변형(보류=누락): 정밀도 분모는 응답 건, 재현율 분모는 전체 정답 건.
 2. support ≥ 10 label macro-F1: eval-def v2 와 같은 7-class 채점(manual 도 class) 에서 해당 셋 정답 support ≥ 10 인 label 만 평균. 포함 label 명시.
 3. label별 F1 + support (C 기준): 7-class 표준 F1 과 1번 보류 제외 F1.
 4. seed별 출력 오류 건수(예측 JSON 파싱 실패 = prediction 없음).
산출: reports/eval/lora_v4/supplementary_metrics.md, supplementary_metrics.json."""
from __future__ import annotations
import hashlib, json, re, statistics as st, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'scripts'))
from data_v1_guard import assert_data_v1
from eval_v30 import segments as v30_segments
EV = ROOT / 'reports/eval/lora_v4'
TEST30 = ROOT / 'datasets/blade/processed/test_v30.jsonl'; TEST30_SHA = '9bd47216575afc602b03afa20e617308dd9a97476c94e67a117eb17009afd5e2'
SUPP = ROOT / 'datasets/blade/processed/data_v4/test_v31_supp.jsonl'; SUPP_SHA = '803d914902c7ca2042fd15d4a7852d42e71828e58d4ae4d3ac791fb868e63395'
SEG = ROOT / 'reports/eval_v30_redef/segments.json'; SEG_SHA = '76f3210137fc8723138f3fcea0c9cc1f0d259e8fb4892d42a81d366d1eb5ce97'
SCORES30 = EV / 'scores_test_v30.json'; SCORES_SUPP = EV / 'scores_supp.json'
L = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']; MANUAL = 'manual_review_required'
CONC = L[:6]; ERR = 'output_error'; ABSTAIN = {MANUAL, ERR}
MODELS = {  # 그룹 → (run 디렉터리, 예측 파일 tag)
    'base': [('base_qwen_runpod', 'base_qwen_runpod')],
    'v2': [(f'lora_v2_s{s}_runpod', f'lora_v2_s{s}_runpod_final') for s in (42, 43, 44)],
    'v3b': [(f'lora_v3b_s{s}', f'lora_v3b_s{s}_final') for s in (42, 43, 44)],
    'v4': [(f'lora_v4_s{s}', f'lora_v4_s{s}_final') for s in (42, 43, 44)]}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
seed_of = lambda tag: (re.search(r'_s(\d+)', tag) or [None, 'base'])[1]


def f1_block(pairs, labels):
    out = {}
    for l in labels:
        tp = sum(t == l and p == l for t, p in pairs); fp = sum(t != l and p == l for t, p in pairs); fn = sum(t == l and p != l for t, p in pairs)
        P = tp / (tp + fp) if tp + fp else 0.; R = tp / (tp + fn) if tp + fn else 0.
        out[l] = dict(support=tp + fn, tp=tp, fp=fp, fn=fn, precision=round(P, 4), recall=round(R, 4), f1=round(2 * P * R / (P + R), 4) if P + R else 0.)
    return out


def score(pairs):
    n = len(pairs); support = {l: sum(t == l for t, _ in pairs) for l in L}
    n_manual = sum(p == MANUAL for _, p in pairs); n_err = sum(p == ERR for _, p in pairs)
    # 1. 보류 제외 구체 label F1
    covered = [(t, p) for t, p in pairs if p not in ABSTAIN]
    conc_labels = [l for l in CONC if support[l]]
    per_conc = f1_block(covered, CONC)
    conc_macro = round(sum(per_conc[l]['f1'] for l in conc_labels) / len(conc_labels), 4)
    # 1'. 변형: 보류를 재현율 누락으로 계산(정밀도 분모 = 응답 건, 재현율 분모 = 전체 정답 건)
    per_miss = {}
    for l in CONC:
        tp = per_conc[l]['tp']; fp = per_conc[l]['fp']; fn = support[l] - tp
        P = tp / (tp + fp) if tp + fp else 0.; R = tp / (tp + fn) if tp + fn else 0.
        per_miss[l] = dict(support=support[l], precision=round(P, 4), recall=round(R, 4), f1=round(2 * P * R / (P + R), 4) if P + R else 0.)
    miss_macro = round(sum(per_miss[l]['f1'] for l in conc_labels) / len(conc_labels), 4)
    # 2. 7-class 표준 F1 (eval-def v2 와 동일 계산), support ≥ 10 label 평균
    per_std = f1_block(pairs, L)
    sup_labels = [l for l in L if support[l]]; std_macro = round(sum(per_std[l]['f1'] for l in sup_labels) / len(sup_labels), 4)
    ge10 = [l for l in L if support[l] >= 10]; ge10_macro = round(sum(per_std[l]['f1'] for l in ge10) / len(ge10), 4)
    return dict(n=n, support=support, manual_pred=n_manual, output_errors=n_err, manual_rate=round(n_manual / n, 4), error_rate=round(n_err / n, 4),
                coverage=round(1 - (n_manual + n_err) / n, 4), covered_n=len(covered), covered_accuracy=round(sum(t == p for t, p in covered) / len(covered), 4) if covered else None,
                concrete_macro_f1=conc_macro, concrete_labels=conc_labels, per_label_concrete=per_conc,
                concrete_macro_f1_abstain_as_miss=miss_macro, per_label_abstain_as_miss=per_miss,
                std_macro_f1=std_macro, std_labels=sup_labels, ge10_macro_f1=ge10_macro, ge10_labels=ge10, per_label_std=per_std)


CONCLUSION = '''
## 판정 (표준편차보다 큰 차이만 차이로 인정; 수치는 위 표, 2026-10-31 재채점 결과에 근거)

보조 지표는 주지표를 대체하지 않는다. 특히 1번(보류 제외 F1)은 보류를 많이 할수록 유리하므로 커버리지와 변형(보류=누락)을 같이 읽어야 한다.

- **C 합산 429건, 보류 제외 구체 macro-F1**: v4 0.562 ± 0.012 > v2 0.451 ± 0.009 ≈ v3b 0.436 ± 0.019 (v4 와의 차이 0.11 이상, 표준편차의 5배 이상). v2 와 v3b 는 차이 없음(0.015 < 0.019).
  - 커버리지는 v3b 0.886 ± 0.034 가 v4 0.722 ± 0.055 · v2 0.744 ± 0.049 보다 높다(차이 0.14 이상 > 표준편차). v4 와 v2 는 차이 없음.
  - 보류를 누락으로 넣는 변형에서도 v4 0.460 ± 0.017 > v3b 0.410 ± 0.005 (차이 0.050 > 0.017). v3b 와 v2 0.383 ± 0.023 의 차이 0.027 은 v2 표준편차(0.023)와 비슷해 경계.
  - 응답 건 정확도: v4 0.617 ± 0.018 > v3b 0.494 ± 0.019 ≈ v2 0.491 ± 0.020. v4 는 구체로 답한 건에서 가장 정확하고, 그 대신 v3b 보다 보류가 많다.
- **A test_v30 207건**: 보류 제외 F1 은 v4 0.562 ± 0.045 > v3b 0.465 ± 0.035 (차이 0.097). v2 0.511 ± 0.024 는 v3b 보다 높지만(차이 0.046) 커버리지가 0.572 ± 0.072 로 v3b(0.804 ± 0.064)보다 0.23 낮다. 변형(보류=누락)에서는 v4 0.437 ± 0.055 vs v3b 0.409 ± 0.021 로 차이 없음(0.028 < 0.055). support ≥ 10 macro-F1(public·role_required·owner_match 3종) 도 v4 0.583 ± 0.074 vs v3b 0.545 ± 0.028 은 차이 없음(0.038 < 0.074); v4 vs v2 0.490 ± 0.063 은 차이 0.093 으로 인정. 주지표가 0.3 대인 것은 support 3·1 인 owner_or_admin·manual 이 평균에 들어가기 때문이며, 3종만 보면 0.5 대다.
- **B test_v31_supp 222건**: 보류 제외 F1 v4 0.546 ± 0.044 > v3b 0.473 ± 0.027 (차이 0.073) > v2 0.436 ± 0.017 (차이 0.037, 경계). 커버리지는 v3b 0.963 ± 0.007 > v2 0.905 ± 0.028 > v4 0.757 ± 0.056. 변형에서는 v4 vs v3b 차이 없음(0.022 < 0.037). support ≥ 10 macro-F1(6종, public 제외): v4 0.367 ± 0.019 > v3b 0.322 ± 0.026 (차이 0.045); v3b 와 v2 0.308 ± 0.005 는 차이 없음.
- **C label별(보류 제외 F1, 3b)**: v4 가 v3b 보다 표준편차를 넘어 높은 label 은 public(0.675 vs 0.528), role_required(0.485 vs 0.414), membership_required(0.608 vs 0.552), tenant_match(0.473 ± 0.157 vs 0.062), owner_match(0.799 vs 0.703). owner_or_admin(23건)은 세 모델 모두 0.32~0.36 으로 차이 없음. tenant_match 는 v4 가 55건 중 평균 28.3건만 구체로 답해(나머지 보류) 정밀도 0.97 · 재현율 0.32 이고 seed 편차(± 0.157)가 커서 수치보다 방향만 읽는다. v2 대비로는 public·membership 이 차이 없고 role_required·tenant_match·owner_match 만 v4 가 높다.
- **출력 오류(4번)**: 합산 C 에서 base 76(supp 222건 중 67 = 30%), v2 1/2/6, v3b 4/8/8, v4 9/8/1. v4 는 seed 편차가 커서(1~9) v3b 와 우열을 말할 수 없다. base 의 supp 커버리지 0.698 은 manual 예측이 아니라 출력 오류 때문이다.
- base 는 단일 run 이라 표준편차가 없으며, 모든 지표에서 LoRA 세 모델보다 낮다(합산 보류 제외 F1 0.138, support ≥ 10 0.119).
- **public 오판(5번, 신 정의)**: 기존 채점에는 test_v30 분모(47, 합성 포함)만 있고 supp 분모는 없었다. supp 분모 191(declared 192 중 정답 public 1 제외)에서 v2·v3b 0/0/0, v4 1/0/0(Flowise GET /api/v1/upsert-history/{id}, 정답 tenant_match, seed 42만), base 15(tenant_match 6·membership 3·owner_match 3·manual 2·owner_or_admin 1). 합산 분모 226 에서 v4 2/0/0 · v2 2/1/0 · v3b 0/0/0 으로 LoRA 세 모델은 모두 1% 미만이고 서로 차이 없음(표준편차 안). test_v30 쪽 v4·v2 의 오판 1건은 같은 레코드(crAPI POST /identity/api/v2/vehicle/resend_email, 정답 owner_match)다. 구 정의(declared ∧ 예측 public) 건수가 더 큰 것은 정답이 public 인 declared 건(test_v30 합성 제외 15건)을 세기 때문이며 오판이 아니다. unknown 구간(security 미선언)에서 비public 정답에 public 을 답한 건은 정의상 오판에 들어가지 않지만 참고로 적었다(LoRA 세 모델 합산 4~10건, base 75건).

요약: 보류를 뺀 구체 label 성능과 응답 건 정확도는 v4 가 v2·v3b 보다 일관되게 높다(세 셋 모두, 합산에서는 표준편차의 5배 이상). 커버리지는 v3b 가 가장 높고 v4 는 v2 수준이다. 보류를 누락으로 세면 v4 의 우위는 합산·supp 에서는 유지되나 test_v30 단독에서는 표준편차 안이다. 주지표(eval-def v2 macro-F1) 판정 "v4 vs v3b 차이 없음"은 바뀌지 않는다.
'''


def pub_block(rows):
    """public 오판 신 정의(eval-def v2): declared ∧ 예측 public ∧ 정답≠public, 분모 declared ∧ 정답≠public. 구 정의: declared ∧ 예측 public, 분모 declared. rows = (id, truth, pred, security_state, project)."""
    dec = [r for r in rows if r[3] == 'declared']; denom = [r for r in dec if r[1] != 'public']
    new = [r for r in denom if r[2] == 'public']; old = [r for r in dec if r[2] == 'public']
    return dict(declared=len(dec), denominator_new=len(denom), count_new=len(new), rate_new=round(len(new) / len(denom), 4) if denom else None, count_old=len(old), rate_old=round(len(old) / len(dec), 4) if dec else None,
                ids_new=[r[0] for r in new], truth_labels_new=dict(Counter(r[1] for r in new)), projects_new=dict(Counter(r[4] for r in new)),
                unknown_n=sum(r[3] != 'declared' for r in rows), unknown_pred_public=sum(r[3] != 'declared' and r[2] == 'public' and r[1] != 'public' for r in rows))


def ms(xs, d=3):
    xs = [x for x in xs if x is not None]
    if not xs: return '-'
    return f'{st.mean(xs):.{d}f} ± {st.stdev(xs):.{d}f}' if len(xs) > 1 else f'{xs[0]:.{d}f}'


def main():
    # --- 해시 assert (시작) ---
    assert_data_v1('start')
    for p, h in ((TEST30, TEST30_SHA), (SUPP, SUPP_SHA), (SEG, SEG_SHA)): assert sha(p) == h, f'hash mismatch: {p}'
    meta30, seg = v30_segments(); seg_file = json.loads(SEG.read_text(encoding='utf-8'))
    assert seg_file['ids'] == seg, 'segments.json differs from recomputed segments'
    synthetic = set(seg['synthetic']); truth_supp = {r['id']: r for r in rd(SUPP)}
    # 기존 채점 결과(교차 검증용)
    s30 = {r['model']: r for r in json.load(open(SCORES30, encoding='utf-8')) if r['eval_def'] == 'v2' and r['condition'] == 'oas_code'}
    ssupp = {r['model']: r for r in json.load(open(SCORES_SUPP, encoding='utf-8')) if r['condition'] == 'oas_code'}

    runs = []; files = {}
    for grp, lst in MODELS.items():
        for d, tag in lst:
            f30 = EV / d / 'eval' / f'predictions_oas_code_{tag}.jsonl'; fsp = EV / d / 'eval' / f'supp_predictions_oas_code_{tag}.jsonl'
            files[str(f30.relative_to(ROOT)).replace('\\', '/')] = sha(f30); files[str(fsp.relative_to(ROOT)).replace('\\', '/')] = sha(fsp)
            p30 = {r['id']: (r['prediction']['label'] if r.get('prediction') else ERR) for r in rd(f30)}
            psp = {r['id']: (r['prediction']['label'] if r.get('prediction') else ERR) for r in rd(fsp)}
            assert all(p in L or p == ERR for p in list(p30.values()) + list(psp.values())), tag
            Am = [(i, meta30[i]['label'], p30[i], meta30[i]['security_state'], 'test_v30') for i in seg['all'] if i in p30 and i not in synthetic]
            Bm = [(i, truth_supp[i]['label'], psp[i], truth_supp[i]['security_state'], truth_supp[i]['meta']['project']) for i in psp if i in truth_supp]
            A = [(t, p) for _, t, p, *_ in Am]; B = [(t, p) for _, t, p, *_ in Bm]
            assert len(A) == 207 and len(B) == 222, (tag, len(A), len(B))
            sA, sB, sC = score(A), score(B), score(A + B)
            sA['public_misjudge'] = pub_block(Am); sB['public_misjudge'] = pub_block(Bm); sC['public_misjudge'] = pub_block(Am + Bm)
            # 교차 검증: 표준 7-class macro-F1·출력 오류가 기존 scores 파일과 일치해야 한다(주지표 불변 확인)
            e30 = s30[tag]['main_excl_synthetic']; esp = ssupp[tag]
            assert abs(sA['std_macro_f1'] - e30['macro_f1']) < 1e-4 and sA['output_errors'] == e30['output_errors'], (tag, sA['std_macro_f1'], e30['macro_f1'])
            assert abs(sB['std_macro_f1'] - esp['macro_f1']) < 1e-4 and sB['output_errors'] == esp['output_errors'], (tag, sB['std_macro_f1'], esp['macro_f1'])
            runs.append(dict(group=grp, tag=tag, seed=seed_of(tag), A=sA, B=sB, C=sC))
    out = dict(definition=__doc__, data_hashes={str(TEST30.relative_to(ROOT)).replace('\\', '/'): TEST30_SHA, str(SUPP.relative_to(ROOT)).replace('\\', '/'): SUPP_SHA, str(SEG.relative_to(ROOT)).replace('\\', '/'): SEG_SHA},
               prediction_file_hashes=files, runs=runs)
    (EV / 'supplementary_metrics.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')

    # --- 보고서 ---
    G = defaultdict(list)
    for r in runs: G[r['group']].append(r)
    order = ['base', 'v2', 'v3b', 'v4']; DS = [('A', 'test_v30 oas_code 합성 제외 (207)'), ('B', 'test_v31_supp oas_code (222)'), ('C', '두 셋 합산 (429)')]
    supC = runs[0]['C']['support']; supA = runs[0]['A']['support']; supB = runs[0]['B']['support']
    t = '# LoRA v4 보조 지표 (사후 정의) — 기존 예측 재채점\n\n'
    t += '- 작업 A: 학습·추론·문턱 변경 없음. reports/eval/lora_v4/*/eval/ 의 oas_code 조건 예측 파일만 다시 채점했다(2026-10-31).\n'
    t += '- **주지표(eval-def v2 macro-F1, scripts/eval_v30.py)는 그대로다.** 아래는 사후에 정의한 보조 지표이며 주지표를 대체하지 않는다. 재채점 과정에서 7-class 표준 macro-F1·출력 오류 건수가 기존 scores_test_v30.json·scores_supp.json 과 일치함을 assert 했다.\n'
    t += '- 모델: base(어댑터 없음, 단일 run — seed 편차 없음), v2·v3b·v4 각 seed 42·43·44. 수치는 seed 평균 ± 표본표준편차. 표준편차보다 큰 차이만 차이로 인정한다.\n'
    t += '- 데이터: A = test_v30 oas_code 합성 제외 207건, B = test_v31_supp oas_code 222건, C = A ∪ B 429건. 출력 오류(JSON 파싱 실패)는 어떤 label 도 아닌 오답이며 1번 지표에서는 보류로 함께 뺀다.\n'
    t += '- 해시 assert: test_v30 `' + TEST30_SHA[:16] + '…`, test_v31_supp `' + SUPP_SHA[:16] + '…`, segments.json `' + SEG_SHA[:16] + '…`, data-v1 guard 통과. 예측 파일 24개 SHA-256 은 supplementary_metrics.json 에 기록.\n\n'
    t += '## 지표 정의\n\n'
    t += '1. **구체 label macro-F1(보류 제외)**: 예측이 manual_review_required 이거나 출력 오류인 건을 보류로 보고 제외한 뒤, 남은 건에서 6개 구체 label 의 P/R/F1 을 계산하고 해당 셋에 정답 support 가 있는 구체 label 만 평균한다(A 는 public·role_required·owner_match·owner_or_admin 4종, B·C 는 6종). 정답이 manual 인 건이 구체로 답해지면 그 label 의 FP 다. **커버리지** = 1 − 보류율(manual 예측 + 출력 오류). 커버리지가 낮을수록 같은 F1 이라도 적용 범위가 좁으므로 반드시 함께 읽는다.\n'
    t += '   - 변형(보류=누락): 정밀도 분모는 응답 건, 재현율 분모는 전체 정답 건. 보류한 정답 구체 건은 재현율 누락이다. 커버리지 차이를 F1 에 반영한 값이다.\n'
    t += '2. **support ≥ 10 label macro-F1**: eval-def v2 와 같은 7-class 채점(manual 도 class, 보류 제외 없음)에서 그 셋의 정답 support ≥ 10 인 label 만 평균. 포함 label 은 표에 명시.\n'
    t += '3. **label별 F1 + support(C 합산)**: 7-class 표준 F1 과 1번의 보류 제외 F1 을 각각 표로 싣는다.\n'
    t += '4. **seed별 출력 오류**: prediction 없음(JSON 파싱 실패) 건수.\n\n'

    for key, name in DS:
        s = runs[0][key]['support']
        t += f'## {key}. {name}\n\n정답 support: ' + ', '.join(f'{l} {s[l]}' for l in L if s[l]) + '\n\n'
        t += '### 1. 구체 label macro-F1(보류 제외)과 커버리지\n\n| 모델 | 구체 macro-F1(보류 제외) | 커버리지 | manual 예측률 | 출력 오류율 | 응답 건 정확도 | 변형: 보류=누락 macro-F1 | 포함 label |\n|---|---:|---:|---:|---:|---:|---:|---|\n'
        for g in order:
            v = [r[key] for r in G[g]]
            t += f"| {g} | {ms([x['concrete_macro_f1'] for x in v])} | {ms([x['coverage'] for x in v])} | {ms([x['manual_rate'] for x in v])} | {ms([x['error_rate'] for x in v])} | {ms([x['covered_accuracy'] for x in v])} | {ms([x['concrete_macro_f1_abstain_as_miss'] for x in v])} | {', '.join(v[0]['concrete_labels'])} |\n"
        t += '\n### 2. support ≥ 10 label macro-F1 (7-class 표준 채점)\n\n| 모델 | support≥10 macro-F1 | 참고: support>0 전체 macro-F1(eval-def v2 방식) | 포함 label |\n|---|---:|---:|---|\n'
        for g in order:
            v = [r[key] for r in G[g]]
            t += f"| {g} | {ms([x['ge10_macro_f1'] for x in v])} | {ms([x['std_macro_f1'] for x in v])} | {', '.join(f'{l} ({s[l]})' for l in v[0]['ge10_labels'])} |\n"
        t += '\n### 4. seed별 출력 오류 건수\n\n| 모델 | ' + ' | '.join(f'seed {r["seed"]}' for r in G['v4']) + ' |\n|---|---:|---:|---:|\n'
        for g in order:
            cells = [str(r[key]['output_errors']) for r in G[g]]
            t += f"| {g} | " + ' | '.join(cells + ['-'] * (3 - len(cells))) + ' |\n'
        t += '\n'

    t += '## 3. label별 F1 + support (C 합산 429건)\n\n### 3a. 7-class 표준 F1 (보류 제외 없음)\n\n| 모델 | ' + ' | '.join(f'{l} ({supC[l]})' for l in L) + ' |\n|---|' + '---:|' * len(L) + '\n'
    for g in order:
        v = [r['C'] for r in G[g]]; t += f'| {g} | ' + ' | '.join(ms([x['per_label_std'][l]['f1'] for x in v]) for l in L) + ' |\n'
    t += '\n### 3b. 보류 제외 F1 (6개 구체 label; 보류 건 제외 후 계산)\n\n| 모델 | ' + ' | '.join(f'{l} ({supC[l]})' for l in CONC) + ' |\n|---|' + '---:|' * len(CONC) + '\n'
    for g in order:
        v = [r['C'] for r in G[g]]; t += f'| {g} | ' + ' | '.join(ms([x['per_label_concrete'][l]['f1'] for x in v]) for l in CONC) + ' |\n'
    t += '\n### 3c. 보류 제외 정밀도 / 재현율 (C, 6개 구체 label)\n\n| 모델 | ' + ' | '.join(f'{l} P / R' for l in CONC) + ' |\n|---|' + '---:|' * len(CONC) + '\n'
    for g in order:
        v = [r['C'] for r in G[g]]; t += f'| {g} | ' + ' | '.join(f"{ms([x['per_label_concrete'][l]['precision'] for x in v], 2)} / {ms([x['per_label_concrete'][l]['recall'] for x in v], 2)}" for l in CONC) + ' |\n'
    t += '\n### 3d. 보류 제외 label별 응답 건수 (C, seed 평균; 보류로 빠진 정답 건 = support − 응답)\n\n| 모델 | ' + ' | '.join(f'{l} ({supC[l]})' for l in CONC) + ' |\n|---|' + '---:|' * len(CONC) + '\n'
    for g in order:
        v = [r['C'] for r in G[g]]; t += f'| {g} | ' + ' | '.join(ms([x['per_label_concrete'][l]['tp'] + x['per_label_concrete'][l]['fn'] for x in v], 1) for l in CONC) + ' |\n'
    t += '## 5. public 오판 (신 정의, 사후 추가) — 기존 채점에 없던 supp·합산 분모\n\n'
    t += '기존 채점 결과 확인: scores_test_v30.json 에는 신 정의 public 오판(분모 declared ∧ 정답≠public = 47, 합성 포함 265건 기준)이 있으나 scores_supp.json 에는 public 오판 항목이 없다. 여기서는 세 셋을 같은 정의로 다시 센다. A 는 합성 제외 207건 기준이라 분모가 47 이 아니라 35 다(합성 beacon_iot 의 declared ∧ 비public 12건 제외). security_state 는 test 파일 값(eval_v30.py security_state() 와 같은 규칙: operation 또는 spec 에 security 선언)이며 supp 는 declared 192 · unknown 30(chamilo 8 · generic_university 21 · multitenant_lab 1).\n\n'
    for key, name in DS:
        pb = runs[0][key]['public_misjudge']
        t += f"### {key}. {name} — declared {pb['declared']}, 분모(declared ∧ 정답≠public) {pb['denominator_new']}, unknown {pb['unknown_n']}\n\n| 모델 | 오판 건수(seed별) | 오판률 | 구 정의 건수(declared ∧ 예측 public, seed별) | 오판 정답 label(seed 합) | 오판 프로젝트(seed 합) | unknown ∧ 예측 public ∧ 정답≠public(seed별) |\n|---|---:|---:|---:|---|---|---:|\n"
        for g in order:
            v = [r[key]['public_misjudge'] for r in G[g]]
            tl = Counter(); pj = Counter()
            for x in v: tl.update(x['truth_labels_new']); pj.update(x['projects_new'])
            t += f"| {g} | {' / '.join(str(x['count_new']) for x in v)} | {ms([x['rate_new'] for x in v])} | {' / '.join(str(x['count_old']) for x in v)} | {', '.join(f'{k} {n}' for k, n in tl.most_common()) or '-'} | {', '.join(f'{k} {n}' for k, n in pj.most_common()) or '-'} | {' / '.join(str(x['unknown_pred_public']) for x in v)} |\n"
        t += '\n'
    t += CONCLUSION
    t += '\n원자료: reports/eval/lora_v4/supplementary_metrics.json (run별 전체 수치, 예측 파일 해시). 스크립트: scripts/eval_lora_v4_supplementary.py.\n'
    (EV / 'supplementary_metrics.md').write_text(t, encoding='utf-8')
    assert_data_v1('end')
    for p, h in ((TEST30, TEST30_SHA), (SUPP, SUPP_SHA), (SEG, SEG_SHA)): assert sha(p) == h, f'[end] hash mismatch: {p}'
    print("written:", EV / "supplementary_metrics.md")


if __name__ == '__main__': main()
