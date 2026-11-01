"""Build reports/eval/lora_v1/lora_v1_report.md from the Colab run outputs (metrics.json, predictions_*.jsonl, logs, hashes.json) and test_v30 metadata.
Read-only on inputs. The Colab-written report.md is kept untouched."""
import json, hashlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]; D = ROOT / 'reports/eval/lora_v1'; TEST = ROOT / 'datasets/blade/processed/test_v30.jsonl'
L = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']; MANUAL = 'manual_review_required'
CONDS = ['oas/base_v301', 'oas/lora_v1', 'oas_code/base_v301', 'oas_code/lora_v1']; NAME = {'base_v301': '(a) 베이스 + v3.0.1', 'lora_v1': '(b) LoRA v1'}
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]

def table(rows, header, align_right_from=1):
    return '| ' + ' | '.join(header) + ' |\n|' + '|'.join('---' if i < align_right_from else '---:' for i in range(len(header))) + '|\n' + ''.join('| ' + ' | '.join(str(c) for c in r) + ' |\n' for r in rows)

def prf(rows):
    out = {}
    for l in L:
        tp = sum(r['label'] == l and r['pred'] == l for r in rows); fp = sum(r['label'] != l and r['pred'] == l for r in rows); fn = sum(r['label'] == l and r['pred'] != l for r in rows)
        p = tp / (tp + fp) if tp + fp else 0.; rc = tp / (tp + fn) if tp + fn else 0.; f = 2 * p * rc / (p + rc) if p + rc else 0.
        out[l] = dict(support=sum(r['label'] == l for r in rows), p=round(p, 3), r=round(rc, 3), f1=round(f, 3))
    sup = [l for l in L if out[l]['support']]
    return out, (round(sum(out[l]['f1'] for l in sup) / len(sup), 4) if sup else None), len(sup)

def main():
    m = json.loads((D / 'metrics.json').read_text(encoding='utf-8')); hp = m['hp']; hashes = json.loads((D / 'hashes.json').read_text(encoding='utf-8'))
    cfg = json.loads((D / 'config.json').read_text(encoding='utf-8')); tr = json.loads((D / 'logs/train_result.json').read_text(encoding='utf-8')); log = rd(D / 'logs/train_log.jsonl')
    meta = {r['id']: r for r in rd(TEST)}
    preds = {}
    for c in CONDS:
        cond, model = c.split('/'); rows = rd(D / f'predictions_{cond}_{model}.jsonl')
        for r in rows:
            r['pred'] = r['prediction']['label'] if r.get('prediction') else 'output_error'; mm = meta.get(r['id'], {}).get('meta', {})
            r['oas_status'] = mm.get('oas_status', '?'); r['has_code'] = bool(meta.get(r['id'], {}).get('controller_text'))
        preds[c] = rows
    t = f"# LoRA v1 (data-v1) — test_v30 평가 최종 보고서\n\n"
    t += f"run `{m['run']}`, GPU {m['gpu']}, 베이스 `{hp['base_model']}`, 프롬프트 v3.0.1(고정). 학습·평가 모두 같은 Colab 세션(A100)에서 실행했고 라벨 생성에는 API를 쓰지 않았다. Colab이 쓴 원본 보고서는 같은 폴더의 report.md, 원시 예측은 predictions_*.jsonl.\n\n"
    t += f"**data-v1 해시 검증**: hashes.json의 원본 해시(train_v30 `{hashes['sources']['train_v30.jsonl'][:16]}…`, val_v30 `{hashes['sources']['val_v30.jsonl'][:16]}…`, test_v30 `{hashes['sources']['test_v30.jsonl'][:16]}…`, 프롬프트 `{hashes['sources']['policy_label_v3.0.1.md'][:16]}…`)가 AGENTS.md data-v1 기록과 일치(노트북 셀 4에서 assert 통과, verified_at {hashes.get('verified_at')}).\n\n"
    t += f"**하이퍼파라미터**: QLoRA 4bit, r={hp['lora_r']}, alpha={hp['lora_alpha']}, dropout={hp['lora_dropout']}, target={','.join(hp['target_modules'])}, epochs={hp['epochs']}, lr={hp['lr']}, batch={hp['batch']}×grad_acc={hp['grad_acc']}, max_seq_len={hp['max_seq_len']}, seed={hp['seed']}. 학습 {tr.get('steps')} step, {round(tr.get('train_runtime', 0)/60, 1)}분, 최종 train_loss {round(tr.get('train_loss', 0), 4)}, 재개 {tr.get('resumed_from')}.\n\n"
    losses = [(e['step'], e['loss']) for e in log if 'loss' in e and 'eval_loss' not in e]; evals = [(e['step'], e['eval_loss']) for e in log if 'eval_loss' in e]
    if losses: t += f"train loss: step {losses[0][0]} {losses[0][1]:.3f} → step {losses[-1][0]} {losses[-1][1]:.3f}" + (f"; val loss: {', '.join(f'step {s} {v:.3f}' for s, v in evals)}" if evals else '') + '.\n\n'
    t += '어댑터는 Drive `blade_lora_v1/runs/lora_v1_run1/adapter/`에만 있고 로컬·git에는 없다(reports/untracked_artifacts.md에 경로 기록, 해시 미확인).\n\n'
    t += '## 1. 요약\n\n입력 조건: `oas` = 명세만(269건), `oas_code` = 명세 + 핸들러 원문(controller_text 있는 265건). public 오판 = security_state=declared인 건을 public으로 예측한 수(declared 64건). macro-F1은 support가 있는 label 평균(7종 모두 support 있음).\n\n'
    rows = []
    for c in CONDS:
        v = m['results'][c]; cond, model = c.split('/')
        rows.append([cond, NAME[model], v['macro_f1_supported'], len(v['supported_labels']), f"{v['manual_ratio']:.1%}", f"{v['public_misjudged_security_declared']}/{v['declared_records']}", v['output_errors'], v['mean_inference_ms'], f"{v['by_source']['synthetic']['accuracy']:.1%}", f"{v['by_source']['vuln']['accuracy']:.1%}"])
    rows.append(['oas', '참고: gpt-4o-mini + v3.0.1 (로컬 API)', 'N/A', '', '', '', '', '', '', ''])
    rows.append(['oas', '참고: qwen2.5:7b Ollama CPU + v3.0.1', 'N/A', '', '', '', '', '', '', ''])
    t += table(rows, ['조건', '모델', 'macro-F1', 'label 수', 'manual 비율', 'public 오판', '출력 오류', '평균 ms', '합성 정확도(58)', '취약 API 정확도(211/207)'], 2)
    t += '\n참고 열의 로컬 베이스라인(gpt-4o-mini·qwen CPU)은 test_v30 + v3.0.1 조합으로 아직 실행되지 않았다(기존 baseline_summary.md는 test.jsonl + v2.0 런타임이라 같은 표에 넣지 않는다).\n\n'
    # per-condition tables
    for c in CONDS:
        rows_c = preds[c]; per, mf, n = prf(rows_c); cond, model = c.split('/')
        t += f"## 2. {cond} / {NAME[model]} — label별 P/R/F1 (macro-F1 {mf}, label {n}종)\n\n" + table([[l, d['support'], d['p'], d['r'], d['f1']] for l, d in per.items()], ['label', 'support', 'P', 'R', 'F1'])
        cols = L + ['output_error']
        t += '\n혼동행렬(행=정답, 열=예측):\n\n| 정답\\예측 | ' + ' | '.join(cols) + ' |\n|---|' + '---:|' * len(cols) + '\n'
        for a in L: t += '| ' + a + ' | ' + ' | '.join(str(sum(r['label'] == a and r['pred'] == b for r in rows_c)) for b in cols) + ' |\n'
        mis = [r['id'] for r in rows_c if r['pred'] == 'public' and r['security_state'] == 'declared']
        t += f"\npublic 오판 {len(mis)}건" + (': ' + ', '.join(mis) if mis else '') + '\n\n'
    # splits
    t += '## 3. 출처·OAS 유형별 정확도\n\n취약 API 211건 중 route_only(명세 없음, 경로만) 109건·repository_spec 102건, 합성 58건(quill_blog·folio_wiki·beacon_iot·summit_club, OAS 원본 export).\n\n'
    rows = []
    for c in CONDS:
        for key, name in (('synthetic', '합성'), ('route_only', '취약 route_only'), ('repository_spec', '취약 repository_spec')):
            rs = [r for r in preds[c] if (r['source'] == 'synthetic' if key == 'synthetic' else (r['source'] == 'vuln' and r['oas_status'] == key))]
            if not rs: continue
            per, mf, n = prf(rs)
            rows.append([c, name, len(rs), f"{sum(r['label'] == r['pred'] for r in rs)/len(rs):.1%}", mf, f"{sum(r['pred'] == MANUAL for r in rs)/len(rs):.1%}", sum(r['pred'] == 'public' and r['security_state'] == 'declared' for r in rs)])
    t += table(rows, ['조건/모델', '구간', 'N', '정확도', 'macro-F1(support 있는 label)', 'manual 예측 비율', 'public 오판'], 2)
    # what LoRA sent to manual
    t += '\n## 4. LoRA v1이 manual로 보낸 건의 정답 분포 (보류 편향 분석)\n\n'
    rows = []
    for c in ('oas/lora_v1', 'oas_code/lora_v1', 'oas/base_v301', 'oas_code/base_v301'):
        man = [r for r in preds[c] if r['pred'] == MANUAL]; dist = Counter(r['label'] for r in man)
        rows.append([c, len(man), dist.get(MANUAL, 0), ' / '.join(f"{l} {dist[l]}" for l in L if l != MANUAL and dist[l])])
    t += table(rows, ['조건/모델', 'manual 예측 수', '그중 정답도 manual', '정답이 구체 label인 건(과보류)'], 1)
    # concrete-only view
    t += '\n## 5. 구체 label 6종만의 성능 (manual 제외, 보류 비용과 분리해 보기)\n\n'
    rows = []
    for c in CONDS:
        rs = [r for r in preds[c] if r['label'] != MANUAL]; conc = [r for r in rs if r['pred'] not in (MANUAL, 'output_error')]
        rows.append([c, len(rs), len(conc), f"{len(conc)/len(rs):.1%}", f"{sum(r['label'] == r['pred'] for r in conc)/len(conc):.1%}" if conc else 'N/A', f"{sum(r['label'] == r['pred'] for r in rs)/len(rs):.1%}"])
    t += table(rows, ['조건/모델', '정답 구체 N', '구체로 예측한 수', '구체 응답률', '구체 응답 중 정답률(정밀도)', '전체 정답률(재현율)'], 1)
    t += '\n## 6. 해석\n\n'
    t += '- LoRA v1은 macro-F1을 올리지 못했다(oas 0.572→0.564, oas_code 0.646→0.576). 대신 출력 형식 오류를 없앴고(35→0, 11→1), security 선언 건의 public 오판을 크게 줄였다(27→11, 33→7).\n'
    t += '- 그 대가로 보류가 늘었다(oas 28.6%→68.4%, oas_code 9.4%→29.4%). 4절처럼 보류 중 다수가 정답이 구체 label인 과보류다. data-v1이 manual 25% + "OAS만으로 관계 확인 불가 → 보류" 규칙으로 라벨된 데이터라 보류를 강하게 학습했다.\n'
    t += '- 베이스 모델의 oas F1은 "모르면 public"으로 찍어 얻은 public recall(0.79, precision 0.45)에 기대고 있다. 같은 F1이라도 안전성은 반대다(LoRA public precision 0.96).\n'
    t += '- 합성 58건은 두 조건 모두 LoRA가 100%로 올렸지만(베이스 91.4%), 합성 train 서비스와 템플릿을 공유하므로 낙관 편향이 있다. 취약 API 211건에서는 oas 조건에서 LoRA가 더 나빠졌고(23.2%→13.3%), oas_code 조건에서는 비슷하다(31.9%→33.3%).\n'
    t += '- 취약 API 중 route_only 109건은 명세가 없어 oas 조건은 정보가 거의 없다. 의미 있는 비교는 oas_code 열이며, 거기서 LoRA의 약점은 코드가 있는 구체 사례가 train에 60건(합성)뿐인 점이다. data-v2(Gitea 구체 93건 + 코드 변형 129건)가 이 부분을 겨냥한다.\n'
    t += '- tenant_match 8·membership_required 4·owner_or_admin 11건은 support가 작아 해당 label 점수는 불안정하다. membership·tenant 정답은 전부 합성이다.\n'
    t += '\n## 7. 한계\n\n- 단일 run(seed 42), 반복 없음. val_v30 52건은 조기 종료·선택에 쓰지 않았다(eval loss만 기록).\n- 어댑터 파일은 Drive에만 있어 해시를 확인하지 못했다. 재현하려면 같은 노트북·같은 data-v1·seed 42로 다시 학습해야 한다.\n- 로컬 베이스라인(gpt-4o-mini, qwen CPU)의 test_v30 + v3.0.1 수치는 아직 없다.\n'
    (D / 'lora_v1_report.md').write_text(t, encoding='utf-8'); print(t[:2500]); print('...written', D / 'lora_v1_report.md')

if __name__ == '__main__': main()
