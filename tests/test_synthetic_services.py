import importlib.util
from collections import Counter
from pathlib import Path

from fastapi.testclient import TestClient

from training.data.sources.synthetic import LABELS, SERVICES, generate


def test_synthetic_generation_and_evidence(tmp_path):
    records = generate(tmp_path)
    assert len(records) == 84
    assert len({r['path'] for r in records}) == 84
    assert Counter(r['service'] for r in records) == {s: 14 for s, _, _ in SERVICES}
    assert sum(r['known_vulnerable'] for r in records) == 30
    for service, _, _ in SERVICES:
        assert Counter(r['proposed_label'] for r in records if r['service'] == service) == dict.fromkeys(LABELS, 2)
    for row in records:
        assert row['confirmed_label'] is None
        evidence = row['evidence'][0]
        lines = (tmp_path / evidence['file']).read_text(encoding='utf-8').splitlines()
        assert evidence['code'] == '\n'.join(lines[evidence['line']-1:evidence['line']+2]).strip()
        assert row['path'].startswith('/fixtures/')
        assert not any(label in row['path'] for label in LABELS if label != 'public')
        assert not any(label in (tmp_path / evidence['file']).read_text(encoding='utf-8') for label in LABELS if label != 'public')


def test_fastapi_enforces_secure_and_exposes_deliberate_variant(tmp_path):
    records = generate(tmp_path)
    source = tmp_path / 'datasets/blade/raw/synthetic/quill_blog/app.py'
    spec = importlib.util.spec_from_file_location('quill_fixture', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    client = TestClient(module.app)
    rows = [r for r in records if r['service'] == 'quill_blog']
    for row in rows:
        path = row['path'].replace('{item_id}', '1')
        anonymous = client.get(path)
        assert anonymous.status_code == (200 if row['proposed_label'] == 'public' else 401)
        result = client.get(path, headers={'Authorization':'Bearer bob'})
        expected = 200 if row['proposed_label'] == 'public' or row['vulnerable'] else 403
        assert result.status_code == expected
    assert len(module.app.openapi()['paths']) == 14

