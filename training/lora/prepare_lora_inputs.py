"""Build Drive-ready LoRA v1 inputs from data-v1 (train_v30 / val_v30 / test_v30) with the exact prompt v3.0.1 inference format.
Read-only on data-v1; outputs go to training/lora/data_v1/. No API calls, no model execution."""
import hashlib, json, re
from pathlib import Path
from training.data import label_v30 as m
from training.data import label_v5 as base5

ROOT = m.ROOT; DATA = m.DATA; OUT = ROOT / 'training/lora/data_v1'; PROMPT = ROOT / 'training/data/prompts/policy_label_v3.0.1.md'
DATA_V1 = {'train_v30.jsonl': 'a99d30da2d29907e8e3fc2d1b8ef313c3d2aa24b1539251130bd08cf96b829e2', 'val_v30.jsonl': '62bdadb29cae7aaf814007ad8adec40115e8612d70f2911693219399c82b595c',
           'test_v30.jsonl': '9bd47216575afc602b03afa20e617308dd9a97476c94e67a117eb17009afd5e2', 'policy_label_v3.0.1.md': 'd0913c27b5de185e7dd5734c111cb731f45e28ebca81fed787ff3914d02833ef'}
OVERRIDE_RATIONALE = 'security_state: declared; 판단: security가 선언되어 인증이 필요하므로 public이 아니며, 요청자-객체 관계나 역할 검사가 확인되지 않아 보류'
SUBSCRIPTION_RATIONALE = 'description: premium 플랜이 아니면 403; 판단: 구독 등급 조건은 그룹 구성원 관계가 아니며 6종으로 표현되지 않으므로 보류'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def synthetic_payload(row, with_code=True):
    r = dict(row, code=(row.get('controller_signals') or {}).get('raw_snippet', ''), source_file=row['meta'].get('source_file', ''))
    return m.q_payload(r, 'oas_code' if with_code and r['code'] else 'oas')

def sft_rows(path, enriched):
    out = []
    for row in m.read(path):
        if row['meta'].get('source') == 'synthetic':
            payload = synthetic_payload(row); ev = ['description', 'path_params:item_id']
            if row['meta'].get('v30_relabel_reason'): rationale, src = SUBSCRIPTION_RATIONALE, 'rule_subscription_relabel'
            else: rationale, src = row['rationale'], 'intended_labels'
            conf = row['confidence']
        else:
            payload = base5.payload(enriched[row['id']]); ev = row['evidence_fields']; rationale, src, conf = row['rationale'], 'model_v301', row['confidence']
            if row['meta'].get('v30_override_reason'): rationale, src, ev = OVERRIDE_RATIONALE, 'rule_security_declared_public', ['security_state', 'security']
        target = {'label': row['label'], 'confidence': conf, 'rationale': rationale, 'evidence_fields': ev}
        out.append(dict(id=row['id'], source=row['meta'].get('source', 'apisguru'), label=row['label'], rationale_source=src, security_state=payload['security_state'],
                        user='Return JSON.\n' + json.dumps(payload, ensure_ascii=False), assistant=json.dumps(target, ensure_ascii=False)))
    return out

def schema_fields(spec, op):
    refs = spec.get('components', {}).get('schemas', {}) if 'components' in spec else spec.get('definitions', {}); names = []
    def resolve(ref):
        key = ref.split('/')[-1]; return refs.get(key, {})
    def visit(node, prefix='', active=()):
        if len(names) >= 40 or not isinstance(node, dict): return
        ref = node.get('$ref')
        if ref and ref not in active: visit(resolve(ref), prefix, (*active, ref))
        for name, value in (node.get('properties') or {}).items():
            if len(names) >= 40: return
            full = prefix + name
            if full not in names: names.append(full)
            visit(value, full + '.', active)
        visit(node.get('items'), prefix + '[].', active)
        for b in ('allOf', 'oneOf', 'anyOf'):
            for c in node.get(b, []): visit(c, prefix, active)
    for code, resp in (op.get('responses') or {}).items():
        if not str(code).startswith('2'): continue
        if '$ref' in resp: resp = resolve(resp['$ref'])
        visit(resp.get('schema'))
        for media in (resp.get('content') or {}).values(): visit(media.get('schema'))
    return names[:40]

def test_inputs():
    return [test_record(row) for row in m.read(DATA / 'test_v30.jsonl')]

def test_record(row):
    """One record in the test_v30 input format (oas_user, and oas_code_user when the row has controller_text). Also used for data-v3 code pairs."""
    spec = json.loads(row['oas_snippet']); item = spec['paths'][row['path']]; op = item[row['method'].lower()]
    params = list(item.get('parameters', [])) + list(op.get('parameters', []))
    names = lambda loc: [p['name'] for p in params if isinstance(p, dict) and p.get('in') == loc]
    if op.get('security') == [] and 'security' in spec: state = 'explicitly_anonymous'
    elif 'security' in op or 'security' in spec: state = 'declared'
    else: state = 'unknown'
    cols, owner, tenant = m.erd_cols(row.get('erd_snippet') or '')
    payload = dict(method=row['method'], path=row['path'], path_params=names('path') or re.findall(r'\{([^}]+)\}', row['path']), query_params=names('query'),
                   summary=op.get('summary') or '', description=op.get('description') or '', security=op.get('security', spec.get('security', [])), security_state=state,
                   schema_fields=schema_fields(spec, op), schema_provenance='Fields extracted from API response schema; not a verified database ERD', owner_cols=owner, tenant_cols=tenant)
    rec = dict(id=row['id'], source=row['source'], service=row['service'], label=row['label'], security_state=state, oas_user='Return JSON.\n' + json.dumps(payload, ensure_ascii=False))
    code = (row.get('controller_text') or '').strip()
    if code:
        loc = (row['meta'].get('source_locations') or [{}])[0].get('file', 'handler excerpt')
        p2 = dict(payload, description=(payload['description'] + '\n' if payload['description'] else '') + '핸들러 원문(근거). 해당 엔드포인트의 인가 관련 코드 발췌이며 다른 검사가 더 있을 수 있다.\nFILE ' + loc + '\n' + code)
        rec['oas_code_user'] = 'Return JSON.\n' + json.dumps(p2, ensure_ascii=False)
    return rec

def main():
    for name, expected in DATA_V1.items():
        p = (ROOT / 'training/data/prompts' / name) if name.endswith('.md') else DATA / name
        actual = sha(p)
        if name in ('test_v30.jsonl', 'policy_label_v3.0.1.md'): assert actual == expected, f'{name} hash mismatch with data-v1'
        DATA_V1[name] = actual  # train/val hashes are read from disk and must equal AGENTS.md data-v1 (checked below)
    OUT.mkdir(parents=True, exist_ok=True)
    enriched = {r['id']: r for r in m.read(DATA / 'apisguru_enriched_v2.jsonl')}
    train = sft_rows(DATA / 'train_v30.jsonl', enriched); val = sft_rows(DATA / 'val_v30.jsonl', enriched); test = test_inputs()
    def dump(name, rows):
        with open(OUT / name, 'w', encoding='utf-8', newline='\n') as f:
            for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    dump('train_sft.jsonl', train); dump('val_sft.jsonl', val); dump('test_v30_inputs.jsonl', test)
    with open(OUT / 'policy_label_v3.0.1.md', 'wb') as f: f.write(PROMPT.read_bytes())
    agents = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
    for name in ('train_v30.jsonl', 'val_v30.jsonl', 'test_v30.jsonl'): assert DATA_V1[name] in agents, f'{name} hash not found in AGENTS.md data-v1 section'
    hashes = dict(data_v1_sources=DATA_V1, generated={n: sha(OUT / n) for n in ('train_sft.jsonl', 'val_sft.jsonl', 'test_v30_inputs.jsonl', 'policy_label_v3.0.1.md')},
                  counts=dict(train=len(train), val=len(val), test=len(test), test_with_code=sum('oas_code_user' in r for r in test)),
                  rationale_sources=dict(train={k: sum(r['rationale_source'] == k for r in train) for k in sorted({r['rationale_source'] for r in train})}),
                  format='system=prompt v3.0.1; user="Return JSON.\\n"+payload JSON; assistant=label JSON one line', prompt_version='policy-label-v3.0.1')
    with open(OUT / 'data_v1_hashes.json', 'w', encoding='utf-8', newline='\n') as f: json.dump(hashes, f, ensure_ascii=False, indent=2)
    print(json.dumps(hashes, ensure_ascii=False, indent=1))

if __name__ == '__main__': main()
