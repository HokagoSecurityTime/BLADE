import hashlib
import json
from pathlib import Path

import pytest

from training.data.resignal import OWNER_ROOTS, TENANT_ROOTS, matches, path_signals, reclassify, run
from training.data.sources.naming import resource_name


def candidate(columns: list[str], path: str = '/items/{id}', security: list | None = None) -> dict:
    return dict(id='fixture', service='example', method='GET', path=path,
                oas_snippet=json.dumps(dict(path_params=[], security=security or [])),
                erd_snippet='CREATE TABLE old (\n' + ',\n'.join('  ' + name + ' TEXT' for name in columns) + '\n);',
                label=None, rationale=None, controller_signals=None,
                meta=dict(has_owner_col=False, has_tenant_col=False, has_security=bool(security), source_file='fixture'))


@pytest.mark.parametrize('name', ['author', 'ownerName', 'user_a', 'userB', 'creatorUUID',
                                  'uploaded_by', 'submittedByEmail', 'requester_id', 'ASSIGNEE', 'created_by'])
def test_extended_owner_names(name: str) -> None:
    assert matches(name, OWNER_ROOTS)


def test_exact_matching_and_account_overlap() -> None:
    assert matches('account_id', OWNER_ROOTS) and matches('account_id', TENANT_ROOTS)
    assert matches('merchantName', TENANT_ROOTS)
    assert not matches('user_count', OWNER_ROOTS)
    assert not matches('some_owner_id', OWNER_ROOTS)
    assert not matches('site_name_extra', TENANT_ROOTS)


def test_path_depth_terminal_segments_and_parameters() -> None:
    assert path_signals('/a/{x}/b/{y}', []) == (False, False, 2)
    assert path_signals('/users/{id}', []) == (True, False, 1)
    assert path_signals('/me', []) == (True, False, 0)
    assert path_signals('/orgs/{id}/items/{item}', []) == (False, True, 2)
    assert path_signals('/x/{identifier}', ['owner_name']) == (True, False, 1)
    assert path_signals('/x/{username}', []) == (True, False, 1)
    assert path_signals('/projects/{id}/users/{id}', []) == (True, True, 2)


def test_path_only_precedence_and_mixed_signals() -> None:
    assert reclassify(candidate(['id'], '/projects/{id}/users/{uid}'))['meta']['signal_class'] == 'path_only'
    assert reclassify(candidate(['owner'], '/teams/{id}/items'))['meta']['signal_class'] == 'both'
    assert reclassify(candidate(['account']))['meta']['signal_class'] == 'both'
    assert reclassify(candidate(['id']))['meta']['signal_class'] == 'none'


def test_security_scope_values_not_scheme_names() -> None:
    result = reclassify(candidate(['id'], security=[{'admin_scheme': []}, {'oauth': ['read', 'conversations_write', 'read']}]))
    assert result['meta']['security_scopes'] == ['conversations_write', 'read']
    assert result['meta']['has_admin_scope']
    assert not reclassify(candidate(['id'], security=[{'admin_scheme': []}]))['meta']['has_admin_scope']


def test_resource_verb_fix_and_fields_preserved() -> None:
    assert resource_name('/mosaik/tokenburn/get/{uuid}') == 'tokenburn'
    assert resource_name('/analysis/retrieve') == 'analysis'
    assert resource_name('/get/{id}') == 'resource'
    original = candidate(['user', 'account'], '/mosaik/tokenburn/get/{uuid}')
    updated = reclassify(original)
    assert updated['erd_snippet'].startswith('CREATE TABLE tokenburn (\n')
    assert updated['erd_snippet'].partition('\n')[2] == original['erd_snippet'].partition('\n')[2]
    assert all(updated[key] == value for key, value in original.items() if key not in {'meta', 'erd_snippet'})
    assert all(updated['meta'][key] == value for key, value in original['meta'].items())


def test_run_preserves_raw_order_and_duplicates(tmp_path: Path) -> None:
    source = tmp_path / 'raw.jsonl'
    rows = [candidate(['owner']), candidate(['id'], '/me'), candidate(['owner'])]
    source.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    output = tmp_path / 'processed/out.jsonl'
    report = run(source, output, tmp_path / 'report')
    assert report['records'] == 3 and report['information_poor_with_signal'] == 3
    assert len(report['combinations']) == 10
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before == report['input_sha256']
    assert [json.loads(line)['path'] for line in output.read_text(encoding='utf-8').splitlines()] == [r['path'] for r in rows]
    with pytest.raises(ValueError):
        run(source, source, tmp_path / 'report')
