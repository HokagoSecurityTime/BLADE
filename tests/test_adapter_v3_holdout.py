import asyncio
import json
from training.experiments.adapter_v3_holdout import OUT, frozen, harness

def test_versions_and_inputs():
    frozen()
    rows=json.loads((OUT/'inputs.json').read_text(encoding='utf8'))
    assert len(rows)==5
    for r in rows:
        left=dict(r['inputs']['oas']);right=dict(r['inputs']['oas_code'])
        left.pop('description');right.pop('description')
        assert left==right
        assert 'reference_label' not in json.dumps(r['inputs'])

def test_original_authenticate():
    asyncio.run(harness())
    assert json.loads((OUT/'handler_checks.json').read_text())['passed']==8

def test_no_factory_support_claim():
    extraction=json.loads((OUT/'extracted.json').read_text(encoding='utf8'))
    assert len(extraction)==5
    assert all(not v['necessary_conditions'] and not v['complete_context'] for v in extraction.values())
