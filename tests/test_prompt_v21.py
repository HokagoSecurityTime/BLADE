import json
from pipeline.classifier.security import security_context
from training.data import label
from tests.test_label_data import rows


def test_missing_empty_and_alternatives():
    assert security_context(None)['status'] == 'unknown'
    assert security_context([])['anonymous_alternative'] is True
    requirements = [{'oauth': ['admin:write'], 'key': []}, {}]
    context = security_context(requirements)
    assert context['requirements'] == requirements
    assert context['scopes'] == ['admin:write']
    assert context['anonymous_alternative'] is True
    assert security_context({'oauth': 'invalid'})['status'] == 'invalid'


def test_label_v21_security_and_runtime_version_restored(monkeypatch):
    monkeypatch.setenv('BLADE_PROMPT_VERSION', 'v2.0')
    row = rows()[0]
    oas = json.loads(row['oas_snippet'])
    oas['security'] = [{'oauth': ['manage:items']}, {}]
    row['oas_snippet'] = json.dumps(oas)
    user, _ = label.assemble(row)
    context = json.loads(user)['security_context']
    assert context['requirements'] == oas['security']
    assert context['scopes'] == ['manage:items']
    assert 'unverified' in context['erd_provenance']
    import os
    assert os.environ['BLADE_PROMPT_VERSION'] == 'v2.0'
