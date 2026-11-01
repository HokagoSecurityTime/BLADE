import json
from pathlib import Path

from training.data.freeze_test import LABELS, oas_for


def test_route_only_input_does_not_copy_gold_or_review_reason():
    text, status = oas_for({'method': 'GET', 'path': '/items/{item_id}',
                            'label': 'owner_match', 'proposal_reason': 'GOLD_REASON'})
    assert status == 'route_only'
    assert 'GOLD_REASON' not in text and 'owner_match' not in text
    assert json.loads(text)['paths']['/items/{item_id}']['get']['parameters'][0]['name'] == 'item_id'


def test_review_draft_confirmations_and_inputs():
    root = Path(__file__).resolve().parents[1]
    path = root / 'verification/test_confirmed_draft.jsonl'
    if not path.exists():
        return
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    assert len(rows) == 211
    assert len({r['id'] for r in rows}) == 211
    assert all(r['label'] in LABELS for r in rows)
    assert all(r['meta']['label_source'] == 'workbook_confirmed' for r in rows)
    assert all(r['source'] == 'vuln' for r in rows)
    assert all('proposal_reason' not in r and 'rationale' not in r for r in rows)
    assert all(isinstance(json.loads(r['oas_snippet']), dict) for r in rows)
