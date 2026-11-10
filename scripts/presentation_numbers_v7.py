"""발표용 수치 표 — LoRA v7 (사용자 결정 2026-11-09: S9 사전 기준 3개 충족 → v7 채택, 발표 주 수치를 v7로 전환; 2026-11-10 표 형식 변경: test_v6 하나, Base vs BLADE LoRA, 지표 4개).
모든 수치는 기존 채점 JSON에서 읽는다(재추론 없음). 출력: reports/eval/lora_v7/presentation_numbers_v7.md + .json. v5 표(reports/eval/lora_v5/presentation_numbers_v5.*)는 기록으로 보존.
- 발표 표(md): test_v6 oas_code 289 — Base(unsloth/Qwen2.5-7B-Instruct-bnb-4bit 어댑터 없음, S9-base 단일 run) vs BLADE LoRA(v7, 3 seed 평균 ± sd): macro-F1·정확도·구체 정밀도·public 오판(/265).
  읽기: reports/eval/lora_v7/s9/scores_test_v6.json(scripts/eval_test_v6.py, testv6_guard BLADE_TESTV6_STAGE=S9).
- json에만 보존: v5 열(test_v6·test_v30), test_v30 207(base/v4/v5/v7), test_v5·test_v31_supp v5 시점 참고값(v7 학습 데이터라 v7 수치 없음).
"""
from __future__ import annotations
import hashlib, json, statistics as st, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from scripts.testv6_guard import assert_allowed
S30_5 = 'reports/eval/lora_v5/scores_test_v30.json'; S30_7 = 'reports/eval/lora_v7/scores_test_v30.json'; S6 = 'reports/eval/lora_v7/s9/scores_test_v6.json'; P5 = 'reports/eval/lora_v5/presentation_numbers_v5.json'
SEG = 'reports/eval_v30_redef/segments.json'; OUT = ROOT / 'reports/eval/lora_v7'
SEEDS = (42, 43, 44); L = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']
PROJECTS6 = ['seahub', 'redash', 'glitchtip', 'penpot']; STATUSES = ['human_confirmed', 'ai_double_confirmed', 'ai_single']
load = lambda p: json.load(open(ROOT / p, encoding='utf-8'))
MODELS30 = {'base': (S30_5, ['base_qwen_runpod']), 'v4': (S30_5, [f'lora_v4_s{s}_final' for s in SEEDS]), 'v5': (S30_5, [f'lora_v5_s{s}_final' for s in SEEDS]), 'v7': (S30_7, [f'lora_v7_s{s}_final' for s in SEEDS])}
GROUP6 = {'base': 'base_qwen7b', 'v5': 'lora_v5', 'v7': 'lora_v7'}


def pick(rows, model, **kw):
    out = [e for e in rows if e['model'] == model and all(e.get(k) == v for k, v in kw.items())]; assert len(out) == 1, (model, kw, len(out)); return out[0]


def agg(vals): return (st.mean(vals), st.stdev(vals) if len(vals) > 1 else None)


def fmt(v, sd=None, pct=False, intlike=False):
    if v is None: return '-'
    if intlike: return f'{v:.0f}' if sd is None else f'{v:.1f} ± {sd:.1f}'
    if pct: return f'{v*100:.1f}%' if sd is None else f'{v*100:.1f} ± {sd*100:.1f}%'
    return f'{v:.3f}' if sd is None else f'{v:.3f} ± {sd:.3f}'


def main():
    man = assert_allowed('presentation numbers'); synthetic = set(load(SEG)['ids']['synthetic']); s6 = load(S6); p5 = load(P5)
    scores = {S30_5: load(S30_5), S30_7: load(S30_7)}
    T30 = {}
    for k, (src, models) in MODELS30.items():
        es = [pick(scores[src], m, condition='oas_code', eval_def='v2') for m in models]; mx = [e['main_excl_synthetic'] for e in es]
        pub = [len([i for i in e['public_misjudge_new']['ids'] if i not in synthetic]) for e in es]
        T30[k] = dict(precision=agg([m['concrete']['precision'] for m in mx]), recall=agg([m['concrete']['recall'] for m in mx]), macro_f1=agg([m['macro_f1'] for m in mx]), accuracy=agg([m['accuracy'] for m in mx]), manual=agg([m['manual_ratio'] for m in mx]),
                      public_misjudge=agg(pub), output_errors=[m['output_errors'] for m in mx], public_ids={m: [i for i in e['public_misjudge_new']['ids'] if i not in synthetic] for m, e in zip(models, es)}, n=len(models))
    assert abs(T30['v7']['precision'][0] - 0.824) < 0.001 and abs(T30['v5']['precision'][0] - 0.796) < 0.001 and abs(T30['base']['accuracy'][0] - 0.319) < 0.001
    T6 = {}
    for k, g in GROUP6.items():
        es = [e for e in s6 if e['condition'] == 'oas_code' and e['group'] == g]; assert len(es) == (1 if k == 'base' else 3), (k, len(es))
        T6[k] = dict(macro_f1=agg([e['macro_f1'] for e in es]), accuracy=agg([e['accuracy'] for e in es]), manual=agg([e['manual_ratio'] for e in es]), precision=agg([e['concrete']['precision'] for e in es]), recall=agg([e['concrete']['recall'] for e in es]),
                     answer_rate=agg([e['concrete']['answer_rate'] for e in es]), public_misjudge=agg([e['public_misjudge']['count'] for e in es]), public_den=es[0]['public_misjudge']['denominator'], per_label={l: agg([e['per_label'][l]['f1'] for e in es]) for l in L}, support={l: es[0]['per_label'][l]['support'] for l in L},
                     per_project={p: agg([e['per_project'][p]['accuracy'] for e in es]) for p in PROJECTS6}, project_n={p: es[0]['per_project'][p]['n'] for p in PROJECTS6},
                     per_status={s_: agg([e['per_label_status'][s_]['accuracy'] for e in es]) for s_ in STATUSES}, status_n={s_: es[0]['per_label_status'][s_]['n'] for s_ in STATUSES}, output_errors=[e['output_errors'] for e in es], models=[e['model'] for e in es])
    assert abs(T6['v7']['macro_f1'][0] - 0.650) < 0.001 and abs(T6['base']['macro_f1'][0] - 0.214) < 0.001
    msha = hashlib.sha256((ROOT / 'datasets/blade/processed/data_v6/test_v6_manifest.json').read_bytes()).hexdigest()
    b, v = T6['base'], T6['v7']
    o = []; w = o.append
    w('# 발표용 수치 표 — BLADE LoRA (LoRA v7, S9 채택 2026-11-09; 표 형식 2026-11-10)\n')
    w(f"hold-out **test_v6** 289건(seahub·Redash·GlitchTip·Penpot, 동결 {man['frozen']}, manifest `{msha[:12]}…`), 입력 조건 oas_code(OpenAPI 명세 + 핸들러 코드), 기본 디코딩(greedy, max_new_tokens 256), 프롬프트 v3.0.1. Base = unsloth/Qwen2.5-7B-Instruct-bnb-4bit 어댑터 없음(단일 run, S9-base 2026-11-09, 참고용). BLADE LoRA = LoRA v7(data-v7, QLoRA r16) 3 seed(42·43·44) 평균 ± 표본 표준편차. 두 모델 모두 같은 Pod·같은 라이브러리(torch 2.13.0+cu129·transformers 5.17.0·unsloth 2026.11.3)에서 추론. 수치는 presentation_numbers_v7.json에서 그대로 읽을 수 있다(생성 scripts/presentation_numbers_v7.py).\n")
    w('| 모델 | macro-F1 | 정확도 | 구체 정밀도 | public 오판 (/265) |\n|---|---:|---:|---:|---:|')
    w(f"| Base (Qwen2.5-7B-Instruct, 미학습) | {fmt(*b['macro_f1'])} | {fmt(*b['accuracy'])} | {fmt(*b['precision'])} | {fmt(*b['public_misjudge'], intlike=True)} |")
    w(f"| **BLADE LoRA (v7)** | **{fmt(*v['macro_f1'])}** | **{fmt(*v['accuracy'])}** | **{fmt(*v['precision'])}** | **{fmt(*v['public_misjudge'], intlike=True)}** |")
    w('\n지표 정의: macro-F1 = support>0 label 7종의 F1 평균. 정확도 = label 일치율(289). 구체 정밀도 = 정답이 구체 label(manual 제외, 237건)인 건 중 구체 label로 답한 건의 정답률(보류·출력 오류 제외). public 오판 = security 선언이 있고 정답이 public이 아닌 265건 중 public으로 예측한 건수.')
    w(f"\n- 부가: manual 비율 Base {fmt(*b['manual'], pct=True)} / BLADE {fmt(*v['manual'], pct=True)}, 구체 응답률 {fmt(*b['answer_rate'])} / {fmt(*v['answer_rate'])}, 구체 재현율 {fmt(*b['recall'])} / {fmt(*v['recall'])}, 출력 오류(JSON 파싱 실패) Base {b['output_errors'][0]}건 / BLADE {' / '.join(map(str, v['output_errors']))}건(seed별). Base는 보류(manual)를 한 번도 내지 않고 role_required 173·public 59로 답해 public 오판이 많다.")
    w('- 근거: reports/eval/lora_v7/s9/scores_test_v6.json(condition oas_code; group base_qwen7b·lora_v7), eval_test_v6.md, report.md(S9 판정), base_qwen7b_s9/(S9-base run). 예측 s9/base_qwen7b_s9/eval/v6test_predictions_oas_code_base_qwen7b_s9.jsonl, s9/lora_v7_s4*/eval/v6test_predictions_oas_code_*.jsonl. 채점기 scripts/eval_test_v6.py. 정답 test_v6.jsonl(SHA 87267595…).')
    w('- 채택 근거(사전 등록 기준, 비교 기준 v5 → v7): (1) test_v6 macro-F1 +0.064 ≥ 0.016, (2) test_v30 207 구체 정밀도 +0.028(하락 ≤ 0.025), (3) test_v30 207 public 오판 평균 1.33 ≤ 2.0. v5 수치와 test_v30 표는 이 파일의 json(`test_v6_289.v5`, `test_v30_207`)에 보존하며 발표 표에는 넣지 않는다.\n')
    w('## 정답 출처 한계 (발표에 함께 명시)\n')
    w('- test_v6 라벨은 A안(2026-11-08, 마감 사유): AI(Claude) 1차 확정 + 독립 AI 2차 검수(블라인드 감사 41건 일치 38 = 92.7%, **AI 간 일치율**) + 불일치·저확신 건만 사람 확정. 289건 중 사람 확정 5(1.7%), AI 이중 확정 67(23.2%), AI 단독 217(75.1%). 사람 대비 정확도는 측정되지 않았다. Base·BLADE 비교는 같은 정답·입력·환경이므로 상대 비교는 유효하나 절대 수치에는 정답 오류가 포함된다.')
    w(f"- 정답 출처별 정확도(Base / BLADE): human_confirmed(5) {fmt(*b['per_status']['human_confirmed'])} / {fmt(*v['per_status']['human_confirmed'])}, ai_double_confirmed(67) {fmt(*b['per_status']['ai_double_confirmed'])} / {fmt(*v['per_status']['ai_double_confirmed'])}, ai_single(217) {fmt(*b['per_status']['ai_single'])} / {fmt(*v['per_status']['ai_single'])}.")
    w('- label 편중: tenant_match 38 중 Redash 27, membership_required 37 중 GlitchTip 27, owner_or_admin 17 중 Redash 13. Redash G1-b 경계 18건은 Base·v5·v7 모두 0/18(role_required 예측). 프로젝트별 정확도(Base / BLADE): ' + ', '.join(f"{p} {fmt(*b['per_project'][p])} / {fmt(*v['per_project'][p])}" for p in PROJECTS6) + '.')
    w('- label별 F1(Base / BLADE): ' + ', '.join(f"{l} {fmt(*b['per_label'][l])} / {fmt(*v['per_label'][l])}" for l in L) + '.')
    w('- 참고(발표 표 밖): 회귀·안전 지표 test_v30 207(v7 학습 미포함) 구체 정밀도 Base 0.353 → BLADE 0.824, public 오판(/35) 17 → 1.3, 정확도 0.319 → 0.630 — json `test_v30_207`. test_v5·test_v31_supp는 v7 학습 데이터라 v7 수치가 없다(v5 시점 값은 json `*_v5_reference`).\n')
    w('## 모델·데이터 요약\n')
    w('- BLADE LoRA v7: 베이스 unsloth/Qwen2.5-7B-Instruct-bnb-4bit, QLoRA r16/α16, 3 epoch, lr 2e-4, batch 2×4, cosine, adamw_8bit, max_seq_len 4096, 프롬프트 v3.0.1(`d0913c27…`), completion-only 마스킹, seed 42·43·44. 학습 데이터 data-v7(train 1,540 / val 159). 학습 29.2분/seed(H100). 상세 reports/data_v7/stop5_build_report.md, reports/eval/lora_v7/report.md(1단계), s9/report.md(S9).')
    w('- 중간 실험 S4(문맥 보강)·S5(v3.1 프롬프트)·S8(14B)·C′(라벨 36건 교정)는 사전 기준 미달로 불채택(reports/eval/{context_aug_v5,lora_v6a,lora_v6c,lora_v6d}/report.md). 배포 전환(GGUF Q4_K_M·Ollama blade-qwen-lora-v7·MIN_CONFIDENCE)은 사용자 결정 후 C-5 절차; 그때까지 런타임 기본값은 v5.')
    (OUT / 'presentation_numbers_v7.md').write_text('\n'.join(o) + '\n', encoding='utf-8', newline='\n')
    strip = lambda d: json.loads(json.dumps(d, default=lambda x: list(x) if isinstance(x, tuple) else x))
    json.dump(dict(main_numbers='LoRA v7 (user decision 2026-11-09, S9); presentation table = test_v6 only, Base vs BLADE LoRA, 4 metrics (2026-11-10)', scoring_time_kst='2026-11-09 18:44 (pre-registered deadline 18:00 exceeded by 44 min; user accepted)',
                   presentation_table=dict(test_set='test_v6 289 oas_code', base=strip({k: b[k] for k in ('macro_f1', 'accuracy', 'precision', 'public_misjudge', 'public_den', 'manual', 'output_errors', 'models')}), blade_lora_v7=strip({k: v[k] for k in ('macro_f1', 'accuracy', 'precision', 'public_misjudge', 'public_den', 'manual', 'output_errors', 'models')})),
                   test_v6_289=strip(T6), test_v30_207=strip(T30), test_v5_283_v5_reference=p5['test_v5_283'], test_v31_supp_222_v5_reference=p5['test_v31_supp_222'],
                   test_v6_label_status=dict(human_confirmed=5, ai_double_confirmed=67, ai_single=217, audit41_agreement='38/41 (AI vs AI)'), sources=dict(test_v30=[S30_5, S30_7], test_v6=S6, v5_reference=P5)), open(OUT / 'presentation_numbers_v7.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print((OUT / 'presentation_numbers_v7.md').read_text(encoding='utf-8')[:2600])


if __name__ == '__main__': main()
