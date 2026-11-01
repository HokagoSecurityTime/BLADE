import hashlib
from itertools import product
import json
from pathlib import Path
import subprocess
import sys

import pytest

from training.data.analyze_candidates import analyze, column_count, samples, unique_endpoints


def candidate(index: int, method: str = 'GET') -> dict:
    return dict(id=str(index), service=f'service-{index}', method=method, path='/items/{itemId}',
                oas_snippet='{"summary": "Original text"}',
                erd_snippet='CREATE TABLE items (\n  id TEXT,\n  owner_id TEXT -- owner candidate\n);',
                meta=dict(has_owner_col=True, has_tenant_col=False, has_security=True), label=None)


def test_pseudo_ddl_comments_and_empty_columns() -> None:
    assert column_count(candidate(0)['erd_snippet']) == 2
    assert column_count('CREATE TABLE example (\n\n);') == 0
    assert column_count('CREATE TABLE example (\n  owner_id TEXT -- owner candidate,\n  id INTEGER\n);') == 2
    with pytest.raises(ValueError):
        column_count('unexpected DDL')


def test_distinct_services_and_balanced_methods_are_reproducible() -> None:
    rows = [candidate(i, method) for i in range(12) for method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')]
    chosen = samples(rows)
    assert chosen == samples(rows)
    assert len(chosen) == len({row['service'] for row in chosen}) == 10
    assert {method: sum(row['method'] == method for row in chosen)
            for method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')} == {
                method: 2 for method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')}


def test_endpoint_duplicate_key_not_snippet_contents() -> None:
    first = candidate(0)
    changed = dict(first, oas_snippet='changed')
    assert unique_endpoints([first, changed]) == [first]


def test_source_extractor_accepts_nullable_type_arrays(tmp_path: Path) -> None:
    source = tmp_path / 'APIs' / 'example' / 'v1' / 'openapi.yaml'
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps({'paths': {'/items/{id}': {'get': {'responses': {
        '200': {'content': {'application/json': {'schema': {'type': 'object', 'properties': {
            'id': {'type': ['integer', 'null']}, 'owner_id': {'type': 'string'}}}}}}
    }}}}}), encoding='utf-8')
    output = tmp_path / 'candidates.jsonl'
    extractor = Path(__file__).resolve().parents[1] / 'training/data/sources/apisguru.py'
    subprocess.run([sys.executable, str(extractor), str(tmp_path / 'APIs'), str(output)],
                   check=True, capture_output=True, text=True, timeout=20)
    rows = [json.loads(line) for line in output.read_text(encoding='utf-8').splitlines()]
    assert len(rows) == 1 and rows[0]['meta']['has_owner_col']
    assert 'id INTEGER' in rows[0]['erd_snippet']


def test_source_extractor_preserves_plain_yaml_keys(tmp_path: Path) -> None:
    source = tmp_path / 'APIs' / 'example' / 'openapi.yaml'
    source.parent.mkdir(parents=True)
    source.write_text('''paths:
  /items/{id}:
    get:
      responses:
        200:
          schema:
            type: object
            properties:
              on: {type: boolean}
              off: {type: boolean}
              id: {type: integer}
''', encoding='utf-8')
    output = tmp_path / 'candidates.jsonl'
    extractor = Path(__file__).resolve().parents[1] / 'training/data/sources/apisguru.py'
    subprocess.run([sys.executable, str(extractor), str(tmp_path / 'APIs'), str(output)],
                   check=True, capture_output=True, text=True, timeout=20)
    row = json.loads(output.read_text(encoding='utf-8'))
    assert 'on BOOLEAN' in row['erd_snippet'] and 'off BOOLEAN' in row['erd_snippet']
    assert column_count(row['erd_snippet']) == 3


def test_analysis_eight_cells_full_snippets_and_raw_unchanged(tmp_path: Path) -> None:
    rows = []
    for index, flags in enumerate(product((False, True), repeat=3)):
        row = candidate(index)
        row['meta'] = dict(zip(('has_owner_col', 'has_tenant_col', 'has_security'), flags))
        rows.append(row)
    rows.append(dict(rows[0]))
    source = tmp_path / 'candidates.jsonl'
    source.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    report = analyze(source, tmp_path / 'reports')
    assert report['total_records'] == 9
    assert report['unique_endpoint_records'] == report['service_count'] == 8
    assert report['duplicate_endpoint_records'] == 1
    assert len(report['flag_combinations']) == 8
    assert sum(row['count'] for row in report['flag_combinations']) == 9
    assert report['information_poor_records'] == 9
    assert report['source_sha256'] == hashlib.sha256(source.read_bytes()).hexdigest() == before
    sample = (tmp_path / 'reports/candidates_sample.md').read_text(encoding='utf-8')
    assert rows[0]['oas_snippet'] in sample and rows[0]['erd_snippet'] in sample
    assert not (tmp_path / 'processed').exists()
