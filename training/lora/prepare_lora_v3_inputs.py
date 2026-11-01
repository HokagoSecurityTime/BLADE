"""Build LoRA v3 inputs from data-v3a / data-v3b (train_v3a / train_v3b / val_v3 / test_v30) in the prompt v3.0.1 inference format.
data-v2 rows go through prepare_lora_v2_inputs.row_to_sft unchanged (non-synthetic rows must reproduce data_v2/train_sft.jsonl exactly);
data-v3 code pairs use the test_v30 oas_code payload (prepare_lora_inputs.test_record). Rationales rewritten by scripts/freeze_data_v3.py (meta.rationale_v3) replace the target rationale.
Records over 4096 Qwen2.5 tokens are excluded and reported. Outputs training/lora/data_v3/. Read-only on datasets. No API/training."""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
from data_v1_guard import assert_data_v1
from data_v2_guard import assert_data_v2
from training.lora.prepare_lora_inputs import test_record
from training.lora.prepare_lora_v2_inputs import row_to_sft
P = ROOT / 'datasets/blade/processed'; OUT = ROOT / 'training/lora/data_v3'; V2 = ROOT / 'training/lora/data_v2'; PROMPT = ROOT / 'training/data/prompts/policy_label_v3.0.1.md'
rd = lambda p: [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
MAX_SEQ = 4096
def v3_pair_to_sft(row):
    rec = test_record(row)
    target = {'label': row['label'], 'confidence': 0.9, 'rationale': row['rationale'], 'evidence_fields': ['description', 'path_params']}
    rsrc = 'rule_' + row['meta']['rationale_v3']['rule']
    return dict(id=row['id'], source='opensource_v3', condition='oas_code', label=row['label'], rationale_source=rsrc, security_state=rec['security_state'],
                user=rec['oas_code_user'], assistant=json.dumps(target, ensure_ascii=False))


def main():
    assert_data_v1('start'); assert_data_v2('start'); OUT.mkdir(parents=True, exist_ok=True)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct', cache_dir=str(ROOT / '.cache/models')); system = PROMPT.read_text(encoding='utf-8')
    enriched = {r['id']: r for r in rd(P / 'apisguru_enriched_v2.jsonl')}; gitea_src = {r['id']: r for r in rd(P / 'opensource/gitea_v28.2.0_labeled_v301.jsonl')}
    def conv(r):
        if r['meta'].get('data_version') == 'data-v3-stage1b': return v3_pair_to_sft(r)
        s = row_to_sft(r, enriched, gitea_src); rw = r['meta'].get('rationale_v3')
        if rw:   # scripts/freeze_data_v3.py rewrote the rationale (template rules): the record rationale is the target rationale
            t = json.loads(s['assistant']); t['rationale'] = r['rationale']; s['assistant'] = json.dumps(t, ensure_ascii=False); s['rationale_source'] = 'rule_' + rw['rule']
        return s
    ntok = lambda r: len(tok.apply_chat_template([{'role': 'system', 'content': system}, {'role': 'user', 'content': r['user']}, {'role': 'assistant', 'content': r['assistant']}], tokenize=True))
    # reproducibility: data-v2 rows outside the neutralized synthetic set give the data_v2 SFT text exactly
    v2_sft = {r['id']: r for r in rd(V2 / 'train_sft.jsonl') + rd(V2 / 'val_sft.jsonl')}
    sets, over, changed = {}, [], {}
    for name, path in (('train_v3a', P / 'train_v3a.jsonl'), ('train_v3b', P / 'train_v3b.jsonl'), ('val_v3', P / 'val_v3.jsonl')):
        rows = rd(path); out = []
        for r in rows:
            s = conv(r); s['tokens'] = ntok(s)
            if r['id'] in v2_sft:
                same = (s['user'], s['assistant']) == (v2_sft[r['id']]['user'], v2_sft[r['id']]['assistant'])
                if r['meta'].get('neutralized_v3') or (r['meta'].get('rationale_v3') or {}).get('sft_changed'): changed[r['id']] = not same
                else: assert same, f'data-v2 row {r["id"]} no longer reproduces data_v2 SFT'
            if name.startswith('train') and s['tokens'] > MAX_SEQ: over.append(dict(id=r['id'], tokens=s['tokens'], split=name)); continue
            out.append(s)
        sets[name] = out
    names = {'train_v3a': 'train_sft_v3a.jsonl', 'train_v3b': 'train_sft_v3b.jsonl', 'val_v3': 'val_sft_v3.jsonl'}
    for k, n in names.items():
        with open(OUT / n, 'w', encoding='utf-8', newline='\n') as f:
            for r in sets[k]: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    (OUT / 'test_v30_inputs.jsonl').write_bytes((V2 / 'test_v30_inputs.jsonl').read_bytes()); (OUT / 'policy_label_v3.0.1.md').write_bytes(PROMPT.read_bytes())
    sources = {n: sha(P / n) for n in ('train_v3a.jsonl', 'train_v3b.jsonl', 'val_v3.jsonl', 'test_v30.jsonl')} | {'policy_label_v3.0.1.md': sha(PROMPT)}
    gen = {n: sha(OUT / n) for n in (*names.values(), 'test_v30_inputs.jsonl', 'policy_label_v3.0.1.md')}
    hashes = dict(data_version='data-v3a/data-v3b', data_v3_sources=sources, generated=gen,
                  counts={k: dict(records=len(v), by_condition={c: sum(r['condition'] == c for r in v) for c in ('oas', 'oas_code')}, by_source={s: sum(r['source'] == s for r in v) for s in sorted({r['source'] for r in v})},
                                  manual=sum(r['label'] == 'manual_review_required' for r in v)) for k, v in sets.items()} | dict(test=269, test_with_code=265),
                  excluded_over_4096=over, v2_rows_sft_changed=sum(changed.values()), v2_rows_rewritten_but_sft_unchanged=sum(not v for v in changed.values()),
                  rationale_sources={k: dict(sorted(((s, sum(r['rationale_source'] == s for r in v)) for s in {r['rationale_source'] for r in v}))) for k, v in sets.items()},
                  token_stats={k: dict(max=max(r['tokens'] for r in v), median=sorted(r['tokens'] for r in v)[len(v) // 2]) for k, v in sets.items()},
                  format='system=prompt v3.0.1; user="Return JSON.\\n"+payload JSON; assistant=label JSON one line; val carries condition', prompt_version='policy-label-v3.0.1', max_seq_len=MAX_SEQ)
    (OUT / 'data_v3_hashes.json').write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    assert_data_v1('end'); assert_data_v2('end')
    print(json.dumps({k: v for k, v in hashes.items() if k not in ('data_v3_sources', 'generated', 'rationale_sources')}, ensure_ascii=False, indent=1))


if __name__ == '__main__': main()
