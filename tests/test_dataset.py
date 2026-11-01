"""Dataset guardrails, including a read boundary for reserved test sources."""
import json
from pathlib import Path
import pytest
from training.data import build_train as b

def row(id, service, label='owner_match', confidence=.9, **meta):
    return dict(id=id,service=service,method='GET',path='/records/{id}',label=label,
                confidence=confidence,oas_snippet='{}',erd_snippet='CREATE TABLE records(id INT);',
                controller_signals={},rationale='test evidence',meta={'source':'apisguru',**meta})

def test_quality_pools_and_demo_pattern():
    rows=[row('good','a'),row('low','a',confidence=.4),row('flag','a',flag_review=True),
          row('invalid','a',evidence_invalid=True),row('manual','a',b.MANUAL,.4)]
    eligible,low,reasons=b.prepare(rows,[],set())
    assert [r['id'] for r in eligible]==['good','manual']
    assert [r['id'] for r in low]==['low']
    assert reasons['flag_review']==reasons['evidence_invalid']==1
    assert not b.prepare(rows,[],{('GET',b.pattern('/records/{other_id}'))})[0]

def test_manual_quota_counts_synthetic_and_preserves_service_isolation():
    rows=[]
    for s in range(20):
        rows += [row(f'{s}_c{i}',str(s)) for i in range(9)]
        rows += [row(f'{s}_m{i}',str(s),b.MANUAL,.4) for i in range(20)]
        rows += [row(f'{s}_synthetic',str(s),b.MANUAL,1,source='synthetic')]
    train,val,details=b.split_rows(rows)
    assert not {r['service'] for r in train}&{r['service'] for r in val}
    assert len({r['service'] for r in train})==18
    for name,part in [('train',train),('val',val)]:
        assert sum(r['label']==b.MANUAL for r in part)/len(part)==.25
        assert sum(r['meta']['source']=='synthetic' for r in part)==len({r['service'] for r in part})
    assert b.split_rows(rows)==(train,val,details)

def test_synthetic_loader_never_reads_test_sources(monkeypatch):
    partition=json.loads((b.HERE/'synthetic_partition.json').read_text(encoding='utf8'))
    original=Path.read_text
    def guarded(path,*args,**kwargs):
        assert 'vuln_apis' not in path.parts
        assert not set(partition['test_services'])&set(path.parts)
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',guarded)
    rows,hashes=b.synthetic_rows(partition)
    assert len(rows)==42
    assert {r['service'] for r in rows}==set(partition['train_services'])
    assert all(r['controller_signals']['raw_snippet'] for r in rows)
    assert any(r['controller_signals']['owner_filter'] for r in rows)

def test_generated_dataset_contract():
    if not (b.DATA/'train.jsonl').exists(): pytest.skip('Full API labeling has not completed')
    train,val=b.read(b.DATA/'train.jsonl'),b.read(b.DATA/'val.jsonl')
    partition=json.loads((b.HERE/'synthetic_partition.json').read_text(encoding='utf8'))
    b.validate(train,val,partition)
    assert {r['service'] for r in train+val if r['meta']['source']=='synthetic'}==set(partition['train_services'])
    for r in train+val:
        if r['meta']['source']=='apisguru':
            assert not r['meta'].get('evidence_invalid') and not r['meta'].get('flag_review')
            assert r['label']==b.MANUAL or r['confidence']>=.6
