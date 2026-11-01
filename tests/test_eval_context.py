import json
from pathlib import Path

from pipeline.parsers.erd import parse_erd
from scripts.build_eval_context import ROOT, catalog, sha


def test_context_catalog_preserves_real_names_and_relationships():
    tables = catalog()
    def find(service, name):
        return next(t for t in tables if t['service'] == service and t['table'] == name)
    assert 'user_id' in find('VAmPI', 'books')['columns']
    assert find('VAmPI', 'books')['primary'] == ['id']
    basket = find('juice-shop', 'Baskets')
    assert 'UserId' in basket['columns'] and 'user_id' not in basket['columns']
    assert any(f['column'] == 'UserId' and f['table'] == 'Users' for f in basket['foreign_keys'])
    order = find('crAPI', 'order')
    assert {'user_id','product_id'} <= set(order['columns'])
    assert 'creator_id' in find('Pixi', 'pictures')['columns']
    assert 'owner_id' not in find('Pixi', 'pictures')['columns']


def test_overlay_has_no_gold_or_synthetic_overrides_and_sources_are_verifiable():
    path = ROOT/'reports/eval/context/source_overlay.jsonl'
    rows = [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]
    frozen = {r['id']:r for r in map(json.loads, (ROOT/'datasets/blade/processed/test.jsonl').read_text(encoding='utf-8').splitlines())}
    assert len(rows) == len({r['id'] for r in rows}) == 211
    for row in rows:
        assert frozen[row['id']]['source'] == 'vuln'
        assert set(row) <= {'id','erd_snippet','controller_text','provenance'}
        if 'erd_snippet' in row:
            assert parse_erd(row['erd_snippet'])
        for item in row['provenance']:
            refs = [item['controller']] if 'controller' in item else item['provenance']
            for ref in refs:
                source = ROOT/ref['file']
                assert source.is_relative_to(ROOT/'datasets/blade/raw/vuln_apis')
                assert sha(source) == ref['sha256']
                assert 1 <= ref['line'] <= len(source.read_text(encoding='utf-8-sig').splitlines())
    assert sha(ROOT/'datasets/blade/processed/test.jsonl') == 'bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa'
