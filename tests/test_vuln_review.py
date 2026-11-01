import json
from pathlib import Path
from training.data.sources.review_vuln import BASE, ROOT, cite, render


def test_review_all_records_and_source_evidence():
    rows = [json.loads(x) for x in (ROOT / 'datasets/blade/processed/vuln_review_candidates.jsonl').read_text(encoding='utf8').splitlines()]
    assert len(rows) == len({r['id'] for r in rows}) == 275
    assert all(r['confirmed_label'] is None for r in rows)
    for row in rows:
        assert isinstance(row['meta']['exclude'], bool)
        assert bool(row['meta']['exclude_reason']) == row['meta']['exclude']
        for ref in row['review_evidence']:
            lines = (BASE / row['service'] / ref['file']).read_text(encoding='utf-8-sig', errors='replace').splitlines()
            assert ref['excerpt'] == '\n'.join(lines[ref['start_line']-1:ref['end_line']])
            assert len(ref['excerpt'].splitlines()) <= 3
    table = render(rows)
    assert sum(line.startswith('| ') for line in table.splitlines()) == 276
    assert all(line.endswith('|  |  |') for line in table.splitlines() if line.startswith('| ') and not line.startswith('| id'))


def test_citation_scoped_after_handler():
    base = cite('VAmPI', 'api_views/users.py', "user = User.query.filter_by(username=resp['sub']).first()")
    scoped = cite('VAmPI', 'api_views/users.py', "user = User.query.filter_by(username=resp['sub']).first()", 'def update_password(username):')
    assert scoped['start_line'] > base['start_line']


def test_effective_dvws_mount():
    rows = [json.loads(x) for x in (ROOT / 'datasets/blade/processed/vuln_review_candidates.jsonl').read_text(encoding='utf8').splitlines()]
    row = next(r for r in rows if r['service'] == 'DVWS-node' and r['path'] == '/v2/notes' and r['method'] == 'GET')
    assert row['effective_path'] == '/api/v2/notes'


def test_enhanced_static_review_provenance():
    rows = [json.loads(x) for x in (ROOT / 'datasets/blade/processed/vuln_review_candidates.jsonl').read_text(encoding='utf8').splitlines()]
    for row in rows:
        for ref in row['handler_excerpts_50']:
            lines = (BASE / row['service'] / ref['file']).read_text(encoding='utf-8-sig', errors='replace').splitlines()
            assert ref['excerpt'] == '\n'.join(lines[ref['start_line']-1:ref['end_line']])
            assert 1 <= len(ref['excerpt'].splitlines()) <= 50
        if row['meta'].get('proposal_basis') == 'path_heuristic_unverified_role':
            assert row['meta']['needs_human_judgment'] is True
    login = next(r for r in rows if r['service'] == 'crAPI' and r['path'] == '/identity/api/auth/login')
    assert login['proposed_label'] == 'public'
    assert any('permitAll' in e['excerpt'] for e in login['review_evidence'])
    community = [r for r in rows if r['service'] == 'crAPI' and r['path'].startswith('/community/')]
    assert len(community) == 6 and all(any(s['kind'] == 'go_handler' for s in r['source_locations']) for r in community)
