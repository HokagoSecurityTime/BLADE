import ast
import json
from training.experiments.external_paired_v29 import OUT, RAW, function_span, freeze, harness


def test_multiline_function_span():
    raw=function_span(RAW/'backend/app/api/routes/items.py','update_item')
    module=ast.parse(raw['code'])
    assert len(module.body)==1
    assert module.body[0].name=='update_item'
    assert 'session.get(Item, id)' in raw['code']
    assert 'Not enough permissions' in raw['code']


def test_frozen_protocol():
    freeze()


def test_same_ids_no_reference_leak():
    rows=json.loads((OUT/'inputs.json').read_text(encoding='utf8'))
    assert len(rows)==23 and len({r['id'] for r in rows})==23
    for row in rows:
        a=row['inputs']['oas']; b=row['inputs']['oas_code']
        assert {k:v for k,v in a.items() if k!='description'}=={k:v for k,v in b.items() if k!='description'}
        assert 'reference_label' not in json.dumps(row['inputs'])
        assert 'def ' not in a['description']
        assert 'FILE backend/app/api/routes/' in b['description']
        assert a['security_state']!='explicitly_anonymous'


def test_original_handler_boundaries():
    harness()
    checks=json.loads((OUT/'handler_checks.json').read_text(encoding='utf8'))
    assert checks['passed']==22
