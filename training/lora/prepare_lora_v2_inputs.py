"""Build Drive-ready LoRA v2 inputs from data-v2 (train_v2 / val_v2 / test_v30) in the prompt v3.0.1 inference format.
Records whose system+user+assistant exceed 4096 Qwen2.5 tokens are excluded from train_sft and reported. val_sft carries `condition` (oas / oas_code).
Outputs training/lora/data_v2/. Read-only on datasets. No API/training."""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
from data_v1_guard import assert_data_v1
from training.data import label_v5 as base5
from training.data.label_gitea_v30 import payload as gitea_payload
from training.lora.prepare_lora_inputs import synthetic_payload, OVERRIDE_RATIONALE, SUBSCRIPTION_RATIONALE
P = ROOT / 'datasets/blade/processed'; OUT = ROOT / 'training/lora/data_v2'; PROMPT = ROOT / 'training/data/prompts/policy_label_v3.0.1.md'
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
MAX_SEQ = 4096

def row_to_sft(row, enriched, gitea_src):
    src = 'gitea' if row['id'].startswith('gitea:') else ('synthetic' if row['meta'].get('source') == 'synthetic' else 'apisguru')
    if src == 'apisguru':
        payload = base5.payload(enriched[row['id']]); ev = row.get('evidence_fields') or ['description']; rationale, rsrc = row['rationale'], 'model_v301'
        if row['meta'].get('v30_override_reason') == 'security_declared_public': rationale, rsrc, ev = OVERRIDE_RATIONALE, 'rule_security_declared_public', ['security_state', 'security']
        cond = 'oas'
    elif src == 'synthetic':
        payload = synthetic_payload(row); ev = ['description', 'path_params:item_id']; rationale, rsrc = row['rationale'], 'intended_labels'
        if row['meta'].get('v30_relabel_reason'): rationale, rsrc = SUBSCRIPTION_RATIONALE, 'rule_subscription_relabel'
        if (row['meta'].get('v2_relabel') or {}).get('rule_id') == 'variant_intended_policy': rationale, rsrc = f"description: 핸들러에 인가 검사가 없지만 경로·스키마로 의도된 정책({row['label']})이 드러남; 판단: test_v30 취약 API와 같은 기준으로 의도 정책을 선택", 'rule_variant_intended_policy'
        cond = 'oas_code'
    else:
        payload = gitea_payload(gitea_src[row['id']]); ev = row.get('evidence_fields') or ['description']; rationale, rsrc = row.get('rationale') or '', 'model_v301'
        rel = row['meta'].get('v2_relabel')
        if rel:
            rid = rel['rule_id']; rationale = f"description: {rel.get('evidence', '')[:160]}; 판단: {rid} 기준으로 {row['label']}"; rsrc = rid
        elif row['meta'].get('v30_override_reason') == 'visibility_dependent': rationale, rsrc = 'description: 저장소·조직 공개 여부에 따라 접근이 달라지는 조건부 접근; 판단: 단일 라벨로 표현되지 않아 보류', 'rule_visibility_dependent'
        cond = 'oas_code'
    conf = row.get('confidence') if isinstance(row.get('confidence'), (int, float)) else 0.9
    target = {'label': row['label'], 'confidence': conf, 'rationale': rationale, 'evidence_fields': ev}
    return dict(id=row['id'], source=src, condition=cond, label=row['label'], rationale_source=rsrc, security_state=payload['security_state'], user='Return JSON.\n' + json.dumps(payload, ensure_ascii=False), assistant=json.dumps(target, ensure_ascii=False))

def main():
    assert_data_v1('start'); OUT.mkdir(parents=True, exist_ok=True)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct', cache_dir=str(ROOT / '.cache/models')); system = PROMPT.read_text(encoding='utf-8')
    enriched = {r['id']: r for r in rd(P / 'apisguru_enriched_v2.jsonl')}; gitea_src = {r['id']: r for r in rd(P / 'opensource/gitea_v28.2.0_labeled_v301.jsonl')}
    def ntok(r): return len(tok.apply_chat_template([{'role': 'system', 'content': system}, {'role': 'user', 'content': r['user']}, {'role': 'assistant', 'content': r['assistant']}], tokenize=True))
    train = [row_to_sft(r, enriched, gitea_src) for r in rd(P / 'train_v2.jsonl')]; val = [row_to_sft(r, enriched, gitea_src) for r in rd(P / 'val_v2.jsonl')]
    over = []
    for r in train: r['tokens'] = ntok(r)
    for r in val: r['tokens'] = ntok(r)
    train_keep = [r for r in train if r['tokens'] <= MAX_SEQ]; over = [dict(id=r['id'], tokens=r['tokens'], split='train') for r in train if r['tokens'] > MAX_SEQ] + [dict(id=r['id'], tokens=r['tokens'], split='val') for r in val if r['tokens'] > MAX_SEQ]
    def dump(name, rows):
        with open(OUT / name, 'w', encoding='utf-8', newline='\n') as f:
            for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    dump('train_sft.jsonl', train_keep); dump('val_sft.jsonl', val)
    (OUT / 'test_v30_inputs.jsonl').write_bytes((ROOT / 'training/lora/data_v1/test_v30_inputs.jsonl').read_bytes()); (OUT / 'policy_label_v3.0.1.md').write_bytes(PROMPT.read_bytes())
    v2h = json.loads((OUT / 'data_v2_hashes.json').read_text(encoding='utf-8'))
    hashes = dict(data_version='data-v2', data_v2_sources=v2h['sources'], generated={n: sha(OUT / n) for n in ('train_sft.jsonl', 'val_sft.jsonl', 'test_v30_inputs.jsonl', 'policy_label_v3.0.1.md')},
                  counts=dict(train=len(train_keep), train_excluded_over_4096=len([o for o in over if o['split'] == 'train']), val=len(val), val_by_condition={c: sum(r['condition'] == c for r in val) for c in ('oas', 'oas_code')}, test=269, test_with_code=265),
                  excluded_over_4096=over, rationale_sources=dict(sorted(((k, sum(r['rationale_source'] == k for r in train_keep)) for k in {r['rationale_source'] for r in train_keep}))),
                  token_stats=dict(train_max=max(r['tokens'] for r in train_keep), train_median=sorted(r['tokens'] for r in train_keep)[len(train_keep) // 2], val_max=max(r['tokens'] for r in val)),
                  format='system=prompt v3.0.1; user="Return JSON.\\n"+payload JSON; assistant=label JSON one line; val carries condition', prompt_version='policy-label-v3.0.1', max_seq_len=MAX_SEQ)
    (OUT / 'data_v2_hashes.json').write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding='utf-8')
    assert_data_v1('end'); print(json.dumps({k: v for k, v in hashes.items() if k not in ('data_v2_sources', 'generated')}, ensure_ascii=False, indent=1))

if __name__ == '__main__': main()
