"""S5 1단계: data-v6a 준비 (학습·추론 없음, test_v6 미사용, 커밋 금지).
v6a = data-v5 train/val 그대로(label·rationale 불변) + 프롬프트 v3.1(policy_label_v3.1.md, 새 파일; v3.0.1 수정 금지) + 출력 키 순서
{evidence_fields, rationale, label, confidence}. 사전 기록 AGENTS.md "작업 S5" 절.

  python scripts/build_data_v6a.py prompt   # label_defs_v3.1_draft.md의 네 절을 v3.0.1에 반영 → training/data/prompts/policy_label_v3.1.md (+ diff 보고)
  python scripts/build_data_v6a.py sft      # training/lora/data_v6a/{train_sft_v6a,val_sft_v6a}.jsonl, 입력 사본, data_v6a_hashes.json, 토큰 길이 분포
  python scripts/build_data_v6a.py check    # label 동일 diff, 채점기 파싱 순서 무관 확인, label 토큰 접두 표 → reports/eval/lora_v6a/data_prep.{md,json}
"""
from __future__ import annotations
import difflib, hashlib, json, os, re, shutil, statistics as st, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
P301 = ROOT / 'training/data/prompts/policy_label_v3.0.1.md'; P31 = ROOT / 'training/data/prompts/policy_label_v3.1.md'
DRAFT = ROOT / 'reports/eval/human_agreement_v5/label_defs_v3.1_draft.md'
D5 = ROOT / 'training/lora/data_v5'; D6 = ROOT / 'training/lora/data_v6a'; REP = ROOT / 'reports/eval/lora_v6a'
SHA301 = 'd0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef'
H5 = dict(hashes='39c302c5fb33d1b1506487678cd15f40cc83ffd59435449522786388554753ac', train='2351afe93518f6e29c95ab9305a15b5a1cda7bd6e3c6d18bec7e8e3d45c3216b',
          val='0df4642f439c812d4e7b9f5ca968c89fd966703bfc59229d6f7ea7f83115748f', test_v30='d65f25b966f61131c0ba5a2341798e56dcd2d3b8da73e9f5d03eb3cd6b0f119a',
          manifest_v5='57fd384f46e89e905209e627a7ff7fb9f312e22a7bed222639e91a80bd05fccd', test_v5='9103cd3d5276ab425f577a2866291bf8e27e7a06a18bd725701989673dbe5d82')
ORDER = ['evidence_fields', 'rationale', 'label', 'confidence']
LABELS = ['public', 'role_required', 'membership_required', 'tenant_match', 'owner_match', 'owner_or_admin', 'manual_review_required']
MAX_SEQ = 4096
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
TAG = re.compile(r'\s*\[(?:v3\.0\.1|G\d|변경|신설|정지 지점)[^\]]*\]')


def section(text, title):
    """Body of '## title' up to the next '## '."""
    m = re.search(rf'^## {re.escape(title)}\n(.*?)(?=^## |\Z)', text, re.S | re.M); assert m, title; return m.group(1)


def reorder_json(s, compact=False):
    o = json.loads(s); assert set(o) == set(ORDER), sorted(o)
    return json.dumps({k: o[k] for k in ORDER}, ensure_ascii=False, separators=(',', ':') if compact else (', ', ': '))


def build_prompt():
    assert sha(P301) == SHA301, 'v3.0.1 prompt hash changed'
    v301 = P301.read_text(encoding='utf-8'); draft = DRAFT.read_text(encoding='utf-8')
    # four sections from the draft, tags stripped
    new = {t: TAG.sub('', section(draft, t)).strip().replace('owner_match다(G4-c).', 'owner_match다.') + '\n\n' for t in ('고정 라벨', '보류가 필수인 경우', '판단 절차')}
    sec = TAG.sub('', section(draft, '보안과 근거')).strip().split('\n\n')[0]   # first paragraph is the rewritten one; the draft says the other two stay as in v3.0.1
    old_sec = section(v301, '보안과 근거').strip().split('\n\n'); assert len(old_sec) == 3
    new['보안과 근거'] = '\n\n'.join([sec] + old_sec[1:]) + '\n\n'
    out = v301
    for t, body in new.items(): out = re.sub(rf'^## {re.escape(t)}\n.*?(?=^## )', f'## {t}\n\n{body}', out, count=1, flags=re.S | re.M)
    out = out.replace('# 정책 라벨 프롬프트 v3.0.1', '# 정책 라벨 프롬프트 v3.1', 1)
    out = out.replace('이 버전은 v3.0에 인증 관련 두 문장만 추가했다. v2.9의 라벨 정의와 판단 절차를 유지한다. 사람 교정 예시는 포함하지 않는다. 예시는 설계 의도가 기록된 합성 서비스에서만 가져왔다.',
                      '출력은 근거(evidence_fields, rationale)를 먼저 적고 그 근거에서 label을 고른 뒤 confidence를 적는다. 사람 교정 예시는 포함하지 않는다. 예시는 설계 의도가 기록된 합성 서비스에서만 가져왔다.', 1)   # 버전 이력 문장 없음(사용자 지시 2026-11-04)
    # examples: same content, new key order
    out = re.sub(r'^출력: (\{.*\})$', lambda m: '출력: ' + reorder_json(m.group(1), compact=True), out, flags=re.M)
    assert '(G4-c)' not in out and '[' not in section(out, '보류가 필수인 경우')
    old_out = '{"label":"7종 중 하나","confidence":0.0,"rationale":"필드: 실제 근거; 판단: 선택 또는 보류 이유","evidence_fields":["description"]}'
    assert old_out in out
    out = out.replace('JSON 객체 하나만 출력한다. 추가 키나 코드 펜스는 금지한다.\n' + old_out,
                      'JSON 객체 하나만 출력한다. 추가 키나 코드 펜스는 금지한다. 키 순서는 evidence_fields, rationale, label, confidence로 고정한다. 근거를 먼저 적고 그 근거에서 label을 고른다.\n'
                      '{"evidence_fields":["description"],"rationale":"필드: 실제 근거; 판단: 선택 또는 보류 이유","label":"7종 중 하나","confidence":0.0}')
    assert '[v3.0.1' not in out and '[G' not in out and '[변경' not in out and '[신설' not in out
    P31.write_text(out, encoding='utf-8', newline='\n')
    diff = list(difflib.unified_diff(v301.splitlines(), out.splitlines(), 'policy_label_v3.0.1.md', 'policy_label_v3.1.md', lineterm='', n=0))
    REP.mkdir(parents=True, exist_ok=True); (REP / 'prompt_v31_diff.txt').write_text('\n'.join(diff) + '\n', encoding='utf-8', newline='\n')
    print('wrote', P31, sha(P31), '| diff lines', len(diff), '| v3.0.1 unchanged:', sha(P301) == SHA301)


def to_v6(r):
    o = dict(r); o['assistant'] = reorder_json(r['assistant']); o.pop('tokens', None); return o


def build_sft():
    assert sha(D5 / 'data_v5_hashes.json') == H5['hashes'] and sha(D5 / 'train_sft_v5.jsonl') == H5['train'] and sha(D5 / 'val_sft_v5.jsonl') == H5['val'], 'data-v5 frozen files changed'
    assert sha(D5 / 'test_v30_inputs.jsonl') == H5['test_v30'] and sha(D5 / 'test_v5_inputs.jsonl') == H5['test_v5'], 'test inputs changed'
    assert sha(ROOT / 'datasets/blade/processed/data_v5/test_v5_manifest.json') == H5['manifest_v5']
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained('unsloth/Qwen2.5-7B-Instruct-bnb-4bit', local_files_only=True); system = P31.read_text(encoding='utf-8'); s301 = P301.read_text(encoding='utf-8')
    ntok = lambda sysm, s: len(tok.apply_chat_template([{'role': 'system', 'content': sysm}, {'role': 'user', 'content': s['user']}, {'role': 'assistant', 'content': s['assistant']}], tokenize=True))
    D6.mkdir(parents=True, exist_ok=True); stats = {}
    for split in ('train', 'val'):
        rows5 = rd(D5 / f'{split}_sft_v5.jsonl'); rows6 = [to_v6(r) for r in rows5]
        for r in rows6: r['tokens'] = ntok(system, r)
        toks = [r['tokens'] for r in rows6]; toks5 = [r['tokens'] for r in rows5]
        over = [r['id'] for r in rows6 if r['tokens'] > MAX_SEQ]
        with open(D6 / f'{split}_sft_v6a.jsonl', 'w', encoding='utf-8', newline='\n') as f:
            for r in rows6: f.write(json.dumps(r, ensure_ascii=False) + '\n')
        stats[split] = dict(rows=len(rows6), tokens_mean=round(st.mean(toks), 1), tokens_median=st.median(toks), tokens_max=max(toks), tokens_p95=sorted(toks)[int(0.95 * len(toks)) - 1],
                            over_4096=len(over), over_4096_ids=over, v5_tokens_mean=round(st.mean(toks5), 1), v5_tokens_max=max(toks5), delta_mean=round(st.mean(toks) - st.mean(toks5), 1),
                            histogram={f'{lo}-{lo + 511}': sum(lo <= t < lo + 512 for t in toks) for lo in range(0, 4608, 512)},
                            labels=dict(Counter(r['label'] for r in rows6)), conditions=dict(Counter(r['condition'] for r in rows6)))
    for n in ('test_v30_inputs.jsonl', 'test_v5_inputs.jsonl'): shutil.copyfile(D5 / n, D6 / n)
    shutil.copyfile(ROOT / 'datasets/blade/processed/data_v5/test_v5_manifest.json', D6 / 'test_v5_manifest.json')   # TESTV5 gate file (hash 57fd384f…), not in generated hashes
    shutil.copyfile(P31, D6 / 'policy_label_v3.1.md')
    sys_tokens = dict(v301=len(tok(s301).input_ids), v31=len(tok(system).input_ids))
    gen = {n: sha(D6 / n) for n in ('train_sft_v6a.jsonl', 'val_sft_v6a.jsonl', 'test_v30_inputs.jsonl', 'policy_label_v3.1.md')}
    hashes = dict(data_version='data-v6a', note='data-v5 rows (train_sft_v5 / val_sft_v5, byte-verified) with the assistant JSON re-serialised in the order evidence_fields, rationale, label, confidence; '
                  'labels, rationales, evidence_fields, confidence values and user inputs unchanged. System prompt policy_label_v3.1.md. test_v5_inputs.jsonl is verified separately against data_v5/test_v5_manifest.json (run_train_v6.py TESTV5).',
                  sources=dict(data_v5_hashes_json=H5['hashes'], train_sft_v5=H5['train'], val_sft_v5=H5['val'], policy_label_v301=SHA301, test_v5_manifest=H5['manifest_v5'], test_v5_inputs=H5['test_v5']),
                  generated=gen, counts={s: stats[s]['rows'] for s in stats}, over_4096={s: stats[s]['over_4096'] for s in stats}, max_seq_len=MAX_SEQ, system_prompt_tokens=sys_tokens,
                  format='system=prompt v3.1; user="Return JSON.\\n"+payload (unchanged); assistant=JSON {evidence_fields, rationale, label, confidence}', output_order=ORDER)
    (D6 / 'data_v6a_hashes.json').write_text(json.dumps(hashes, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    REP.mkdir(parents=True, exist_ok=True); (REP / 'sft_stats.json').write_text(json.dumps(dict(stats=stats, system_prompt_tokens=sys_tokens, hashes=hashes, hashes_file_sha=sha(D6 / 'data_v6a_hashes.json')), ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({s: {k: v for k, v in stats[s].items() if k not in ('over_4096_ids', 'histogram', 'labels', 'conditions')} for s in stats}, ensure_ascii=False)); print('system prompt tokens', sys_tokens); print('hashes file', sha(D6 / 'data_v6a_hashes.json'))


def check():
    """label equality diff, parser order independence, label-token prefix table -> data_prep.md/json"""
    from training.lora.runpod.run_train import parse
    res = dict(label_equality={}, parser={}, label_tokens={})
    for split in ('train', 'val'):
        a, b = rd(D5 / f'{split}_sft_v5.jsonl'), rd(D6 / f'{split}_sft_v6a.jsonl'); assert len(a) == len(b)
        diffs = [dict(id=x['id'], field=k) for x, y in zip(a, b) for k in ('id', 'label', 'user', 'source', 'condition', 'security_state', 'rationale_source') if x[k] != y[k]]
        vals = [x['id'] for x, y in zip(a, b) if json.loads(x['assistant']) != json.loads(y['assistant'])]   # dict equality ignores key order
        order_ok = all(list(json.loads(y['assistant'])) == ORDER for y in b); label_ok = all(json.loads(y['assistant'])['label'] == y['label'] for y in b)
        res['label_equality'][split] = dict(rows=len(a), field_diffs=diffs, assistant_value_diffs=vals, order_all_new=order_ok, label_field_consistent=label_ok, labels=dict(Counter(x['label'] for x in b)))
    # parser: reorder a real v5 prediction raw and check parse() / scorer label extraction
    pred = rd(ROOT / 'reports/eval/lora_v5/lora_v5_s42/eval/v5test_predictions_oas_code_lora_v5_s42_final.jsonl'); n_ok = 0; n = 0
    for r in pred:
        if not r.get('prediction'): continue
        o = json.loads(re.search(r'\{.*\}', r['raw'], re.S).group(0)); new_raw = json.dumps({k: o[k] for k in ORDER if k in o}, ensure_ascii=False); p = parse(new_raw); n += 1; n_ok += bool(p) and p['label'] == r['prediction']['label']
    samples = ['{"evidence_fields": ["description"], "rationale": "x; 판단: y", "label": "owner_match", "confidence": 0.9}', '{"evidence_fields":["description"],"rationale":"x","label":"public","confidence":0.6}',
               '{"evidence_fields": ["description"], "rationale": "x", "label": "owner_match"}', '{"rationale": "x", "label": "not_a_label", "confidence": 0.9}']
    res['parser'] = dict(reordered_v5_s42_predictions=dict(n=n, same_label=n_ok), samples={s: (parse(s) or {}).get('label') for s in samples},
                         note='run_train.parse(): regex {.*} + json.loads + label in LABELS — key order irrelevant; scorers (eval_test_v5.py, eval_v30.py, eval_combined_v5.py, score_ctx.py) read prediction["label"] only.')
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained('unsloth/Qwen2.5-7B-Instruct-bnb-4bit', local_files_only=True)
    pre = '{"evidence_fields": ["description"], "rationale": "x", "label": "'; ids_pre = tok(pre).input_ids
    tt = {}
    for l in LABELS:
        ids = tok(pre + l + '", "confidence": 0.9}').input_ids; assert ids[:len(ids_pre)] == ids_pre
        lab = tok(l, add_special_tokens=False).input_ids; assert ids[len(ids_pre):len(ids_pre) + len(lab)] == lab
        tt[l] = dict(ids=lab, pieces=[tok.decode([i]) for i in lab])
    firsts = Counter(v['ids'][0] for v in tt.values()); dist = {}
    for l, v in tt.items():
        k = 1
        while any(o != l and tt[o]['ids'][:k] == v['ids'][:k] for o in tt): k += 1
        dist[l] = dict(distinguishing_prefix_tokens=k, pieces=v['pieces'][:k])
    res['label_tokens'] = dict(prefix_tail=[tok.decode([i]) for i in ids_pre[-3:]], tokens=tt, first_token_groups=len(firsts), shared_first_token={l: v['pieces'][0] for l, v in tt.items() if firsts[v['ids'][0]] > 1}, distinguishing=dist)
    sft = json.loads((REP / 'sft_stats.json').read_text(encoding='utf-8')); res['sft'] = sft
    system = P31.read_text(encoding='utf-8'); ti = {}
    for n, key in (('test_v5_inputs.jsonl', 'oas_code_user'), ('test_v30_inputs.jsonl', 'oas_code_user'), ('test_v30_inputs.jsonl', 'oas_user')):
        rows = [r for r in rd(D6 / n) if key in r]; lens = [len(tok.apply_chat_template([{'role': 'system', 'content': system}, {'role': 'user', 'content': r[key]}], tokenize=True, add_generation_prompt=True)) for r in rows]
        ti[f'{n}|{key}'] = dict(n=len(rows), mean=round(st.mean(lens), 1), max=max(lens), over_4096=sum(l > 4096 for l in lens), over_6144=sum(l > 6144 for l in lens))
    res['test_prompt_tokens'] = ti
    secs = {}
    for name, p in (('v301', P301), ('v31', P31)):
        txt = p.read_text(encoding='utf-8'); head = txt.split('\n## ')[0]; secs[name] = {'(머리글)': len(tok(head).input_ids)}
        for t in ('고정 라벨', '보류가 필수인 경우', '판단 절차', '보안과 근거', '예시', '출력'): secs[name][t] = len(tok(section(txt, t)).input_ids)
    res['prompt'] = dict(v301_sha=sha(P301), v31_sha=sha(P31), v301_unchanged=sha(P301) == SHA301, diff_file='reports/eval/lora_v6a/prompt_v31_diff.txt', diff_lines=len((REP / 'prompt_v31_diff.txt').read_text(encoding='utf-8').splitlines()),
                         bytes=dict(v301=P301.stat().st_size, v31=P31.stat().st_size), section_tokens=secs)
    (REP / 'data_prep.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8'); write_md(res)


def write_md(res):
    s = res['sft']['stats']; t = ['# S5 1단계 — data-v6a 데이터 준비 보고 (2026-11-04, 학습·추론 없음)', '']
    t += ['## 1. 프롬프트 v3.1', '', f"- 새 파일 training/data/prompts/policy_label_v3.1.md SHA-256 `{res['prompt']['v31_sha']}`. v3.0.1(`{res['prompt']['v301_sha'][:12]}…`)은 수정하지 않았다({'확인' if res['prompt']['v301_unchanged'] else '**변경됨**'}).",
          f"- 반영: label_defs_v3.1_draft.md의 네 절(고정 라벨·보류가 필수인 경우·판단 절차·보안과 근거 첫 문단)을 근거 태그(`[Gn]`, `[v3.0.1]`, `[변경]`, `[신설]`) 없이 그대로 넣었다. 예시 8개는 내용 그대로 키 순서만 바꿨고, 출력 절에 키 순서 고정 문장을 넣었다. diff {res['prompt']['diff_lines']}줄: reports/eval/lora_v6a/prompt_v31_diff.txt.",
          f"- 시스템 프롬프트 토큰: v3.0.1 {res['sft']['system_prompt_tokens']['v301']} → v3.1 {res['sft']['system_prompt_tokens']['v31']} (+{res['sft']['system_prompt_tokens']['v31'] - res['sft']['system_prompt_tokens']['v301']}; 바이트 {res['prompt']['bytes']['v301']:,} → {res['prompt']['bytes']['v31']:,}). 절별:", '',
          '| 절 | v3.0.1 토큰 | v3.1 토큰 | 증가 |', '|---|---:|---:|---:|']
    for k in res['prompt']['section_tokens']['v301']: t.append(f"| {k} | {res['prompt']['section_tokens']['v301'][k]} | {res['prompt']['section_tokens']['v31'][k]} | {res['prompt']['section_tokens']['v31'][k] - res['prompt']['section_tokens']['v301'][k]:+d} |")
    t.append('')
    t += ['## 2. SFT train/val 재생성 (training/lora/data_v6a/)', '', '| 파일 | 행 | SHA-256 |', '|---|---:|---|']
    for n, h in res['sft']['hashes']['generated'].items(): t.append(f"| {n} | {res['sft']['hashes']['counts'].get(n.split('_sft')[0], '-') if '_sft' in n else '-'} | `{h}` |")
    t += [f"| data_v6a_hashes.json | - | `{res['sft']['hashes_file_sha']}` |", '', f"- 원본 data-v5 SFT(train `{H5['train'][:12]}…`, val `{H5['val'][:12]}…`)·data_v5_hashes.json(`{H5['hashes'][:12]}…`) 해시 검증 뒤 assistant JSON만 키 순서 재직렬화. user 입력·label·rationale·evidence_fields·confidence 값 불변.",
          "- test_v30_inputs.jsonl은 data_v5와 바이트 동일 사본, test_v5_inputs.jsonl은 사본이되 해시 목록에 넣지 않고 run_train_v6.py가 test_v5_manifest.json으로 별도 검증한다(v5와 같은 게이트).", '']
    t += ['### label 동일 확인', '']
    for sp, d in res['label_equality'].items():
        t.append(f"- {sp}: {d['rows']}행, id·label·user·source·condition·security_state 필드 차이 {len(d['field_diffs'])}건, assistant 값(키 순서 무시) 차이 {len(d['assistant_value_diffs'])}건, 새 순서 전부 적용 {d['order_all_new']}, assistant.label == label 필드 {d['label_field_consistent']}. label 분포 {d['labels']}.")
    t += ['', '### 토큰 길이 분포 (시스템 v3.1 + user + assistant, Qwen2.5 chat template)', '', '| split | 행 | 평균 | 중앙값 | p95 | 최대 | v5 평균 | 증가 | 4096 초과 |', '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for sp, d in s.items(): t.append(f"| {sp} | {d['rows']} | {d['tokens_mean']} | {d['tokens_median']} | {d['tokens_p95']} | {d['tokens_max']} | {d['v5_tokens_mean']} | +{d['delta_mean']} | {d['over_4096']} |")
    t += ['', '히스토그램(512 구간): ' + '; '.join(f"{sp}: " + ', '.join(f'{k} {v}' for k, v in d['histogram'].items() if v) for sp, d in s.items())]
    over = {sp: d['over_4096_ids'] for sp, d in s.items() if d['over_4096']}
    n_over = {sp: d['over_4096'] for sp, d in s.items()}; mx = max(d['tokens_max'] for d in s.values())
    t += [f"- **4096 초과: train {n_over['train']}/{s['train']['rows']}, val {n_over['val']}/{s['val']['rows']}** (id 목록 sft_stats.json). v3.1 시스템 프롬프트가 +{res['sft']['system_prompt_tokens']['v31'] - res['sft']['system_prompt_tokens']['v301']} 토큰이라 거의 모든 행이 기존 max_seq_len 4096을 넘는다. "
          "v5 전례(초과 행 제외)를 그대로 적용하면 학습 데이터가 거의 남지 않으므로 적용할 수 없고, SFTTrainer 절단은 assistant 목표를 잘라 부적합하다. **사용자 결정(2026-11-04): A안 승인.**",
          f"  - (A안, 승인) max_seq_len을 4096 → 6144로 올린다(학습·추론 동일). 최대 길이 {mx}로 6144 안에 들어 제외 0건. 하이퍼파라미터 중 이것만 v5와 달라지며(메모리·시간 약 1.4배, H100 80GB에서 QLoRA batch 2×4 가능), 추론 입력도 같은 상한을 쓴다. S4의 ctx6144 우려(학습 길이 밖)는 학습 자체를 6144로 하므로 해당 없다. 배포 시(S5 채택 → GGUF 변환 단계) 시스템 프롬프트 KV 캐시 확인이 필요하다(프롬프트 3,798 토큰).",
          '  - (B안) v3.1 문구를 축약해 4096 안에 들어오게 한다. 늘어난 토큰의 대부분은 고정 라벨·보류 절의 규약 문장이라 축약하면 사용자가 확정한 v3.1 정의가 바뀐다. 축약본을 만들려면 별도 승인이 필요하다.',
          '  - (C안) 4096 초과 행 제외 — 사실상 불가(위 건수).', '',
          '추론 입력(시스템 v3.1 + user, 생성 프롬프트 포함, 출력 제외) 토큰:', '', '| 입력 | n | 평균 | 최대 | 4096 초과 | 6144 초과 |', '|---|---:|---:|---:|---:|---:|']
    for k, d in res['test_prompt_tokens'].items(): t.append(f"| {k} | {d['n']} | {d['mean']} | {d['max']} | {d['over_4096']} | {d['over_6144']} |")
    t += ['', '- 추론도 상한 4096이면 test_v5 oas_code 입력 대부분이 잘리므로(왼쪽 절단 = 시스템 프롬프트 손실) A안의 6144 상한은 추론에도 필요하다. 출력 512 토큰을 더해도 6144 + 512 < 32k 컨텍스트.', '']
    t += ['', '## 3. 채점기 파싱 — 키 순서 무관 확인', '', f"- run_train.parse()는 `{{.*}}` 정규식 + json.loads + label 7종 검사라 키 순서와 무관하다. v5 s42 test_v5 예측 {res['parser']['reordered_v5_s42_predictions']['n']}건의 raw를 새 순서로 재직렬화해 다시 parse한 결과 label 동일 {res['parser']['reordered_v5_s42_predictions']['same_label']}건.",
          f"- 표본: {json.dumps(res['parser']['samples'], ensure_ascii=False)} (confidence 누락도 파싱되고, label이 7종 밖이면 출력 오류).",
          '- 채점기(scripts/eval_test_v5.py, eval_v30.py, eval_combined_v5.py, score_ctx.py)는 prediction["label"]만 읽는다. v6a 예측 파일에는 추가 키(label_prob)가 붙지만 기존 키는 그대로라 기존 채점기를 그대로 쓴다.', '']
    lt = res['label_tokens']
    t += ['## 4. label 토큰 확률 추출 방식 (run_train_v6.py)', '', f"JSON 문맥 `… \"label\": \"` 다음에 오는 label 토큰(접두 토큰 `{lt['prefix_tail']}` 뒤). 토큰화는 접두-안정이다(접두를 먼저 토큰화한 결과가 전체 토큰화의 접두와 같음).", '', '| label | 토큰열 | 구별 가능한 최소 접두 |', '|---|---|---|']
    for l, v in lt['tokens'].items(): t.append(f"| {l} | {v['pieces']} | {lt['distinguishing'][l]['distinguishing_prefix_tokens']} 토큰 {lt['distinguishing'][l]['pieces']} |")
    t += ['', f"- 첫 토큰이 겹치는 label: {lt['shared_first_token']} → 첫 토큰만으로는 owner_match와 owner_or_admin을 구별할 수 없다. 따라서 \"첫 토큰 기준\"을 **구별 가능한 최소 접두(prefix) 기준**으로 확장한다: 5종은 첫 토큰 1개, owner 2종은 2개(`owner`+`_match` / `owner`+`_or`).",
          '- 추출: greedy 생성 시 `output_scores=True, return_dict_in_generate=True`로 각 생성 위치의 logits를 받는다(추가 forward 없음). 생성 토큰을 하나씩 디코드해 누적 문자열이 `"label": "`(공백 유무 모두)로 끝나는 위치 t를 찾고, 위치 t부터가 label 토큰이다. 기록값(예측 파일 `label_prob` 키):',
          '  - `p_first`: 위치 t의 vocab 전체 softmax에서 선택 label 첫 토큰의 확률.',
          '  - `p_prefix`: 구별 접두 토큰 확률의 곱(5종은 p_first와 같고, owner 2종은 p(owner)·p(_match|owner) 또는 p(owner)·p(_or|owner)).',
          '  - `p_norm` (**판정·문턱·곡선에 쓰는 값**): p_prefix를 7종 후보 질량으로 정규화. 분모 = 첫 토큰이 다른 5종의 p_first 합 + owner 묶음 질량. 선택 label이 owner 계열이면 owner 묶음 = p(owner)·(p(_match|owner)+p(_or|owner))로 정확히 계산되고, 아니면 두 번째 토큰 분포가 없어 p(owner)를 상한으로 쓴다(분모가 커져 p_norm은 보수적으로 작아짐). 후보 밖 토큰 질량은 분모에 넣지 않는다.',
          '  - `p_seq`: 선택 label 전체 토큰열 확률의 곱(참고), `candidates`: 7종 각각의 접두 확률(위 상한 규칙 포함), `label_token_pos`: t.',
          '  - 생성된 `confidence` 필드는 그대로 두고 기록만 한다. 출력 오류(label 위치 없음·7종 밖)는 `label_prob=null`.',
          '- 보류율 곡선: test_v5 283건에서 문턱 τ∈{0.5,0.55,…,0.95,0.99}에 대해 p_norm < τ인 구체 예측을 manual로 돌렸을 때의 정확도·구체 정밀도·보류율. 문턱 선택은 하지 않는다(곡선 보고만).', '']
    t += ['## 5. 손실 마스킹 (completion-only) 확인', '',
          '- v5 학습 코드 training/lora/runpod/run_train.py 119행: `trainer = train_on_responses_only(trainer, instruction_part=\'<|im_start|>user\\n\', response_part=\'<|im_start|>assistant\\n\')` — unsloth의 completion-only 마스킹으로 assistant 구간 토큰에만 손실을 건다(시스템·user 토큰 label = -100). LoRA v2 노트북(training/lora/build_notebook_v2.py 108행)도 같은 호출이다. v5 s42 run.log 머리(`run lora_v5_s42_final data=v5`)로 이 스크립트가 쓰였음을 확인했고, 로그 자체에는 마스킹 문구가 찍히지 않는다(코드 줄이 근거).',
          '- v6a(run_train_v6.py)도 같은 호출을 그대로 쓴다. 출력 순서가 바뀌어도 assistant 구간 전체(evidence_fields·rationale·label·confidence)가 손실 대상이라는 점은 같다.', '',
          '## 6. 변경하지 않은 것', '', '- data-v5·test_v30·test_v5·test_v31_supp 동결 파일, 프롬프트 v3.0.1, 하이퍼파라미터(LoRA r16·α16·3 epoch·lr 2e-4·batch 2×4·cosine·warmup 10·wd 0.01·seed 42/43/44). 변경은 max_seq_len 4096 → 6144(A안)와 max_new_tokens 256 → 512뿐.', '- 학습·추론은 실행하지 않았다. test_v6은 읽지 않는다. 커밋 없음.', '']
    (REP / 'data_prep.md').write_text('\n'.join(t) + '\n', encoding='utf-8'); print('\n'.join(t))


if __name__ == '__main__':
    {'prompt': build_prompt, 'sft': build_sft, 'check': check}[sys.argv[1]]()
