import asyncio
import sqlite3
from unittest.mock import AsyncMock

import pytest
from multidict import MultiDict
from proxy.cache import LookupCache, MISSING
from proxy.evaluator import evaluate
from proxy.lookup import Lookup, LookupError
from tests.test_proxy import policy, claims


@pytest.mark.parametrize('label,valid,expected', [
    (label, valid, ('PASS' if label == 'public' else 'OBSERVE' if label == 'manual_review_required'
                   else 'PASS' if valid else 'BLOCK'))
    for label in ('public', 'manual_review_required', 'owner_match', 'owner_or_admin',
                  'tenant_match', 'role_required', 'membership_required')
    for valid in (True, False)
])
def test_labels(label, valid, expected):
    user = claims() if valid else claims('user_99', tenant_id='org_2')
    if valid and label == 'role_required':
        user = claims(roles=['admin'])
    if valid and label == 'membership_required':
        user = claims(membership='premium')
    lookup = AsyncMock()
    lookup.get.return_value = {'user_id': 'user_77', 'org_id': 'org_1'}
    result = asyncio.run(evaluate(policy(label), user, {'orderId': '1042'}, {}, lookup=lookup))
    assert result.verdict == expected


@pytest.mark.parametrize('label', ['public', 'manual_review_required', 'owner_match',
    'owner_or_admin', 'tenant_match', 'role_required', 'membership_required'])
def test_no_token(label):
    result = asyncio.run(evaluate(policy(label), None, {}, {}))
    assert result.verdict == ('PASS' if label == 'public' else 'BLOCK')
    assert result.reason == ('public' if label == 'public' else 'no_token')


@pytest.mark.parametrize('mode,expected', [('open', 'OBSERVE'), ('closed', 'BLOCK')])
def test_lookup_failure(mode, expected):
    lookup = AsyncMock()
    lookup.get.side_effect = LookupError('offline')
    result = asyncio.run(evaluate(policy(), claims(), {'orderId': '1042'}, {}, lookup=lookup, fail_mode=mode))
    assert (result.verdict, result.reason) == (expected, 'lookup_failed')


def test_missing_row_and_cache():
    async def scenario():
        lookup = AsyncMock()
        lookup.get.return_value = None
        cache = LookupCache()
        for _ in range(2):
            result = await evaluate(policy(), claims(), {}, {'orderId': 'missing'}, lookup=lookup, cache=cache)
            assert (result.verdict, result.reason) == ('PASS', 'object_not_found')
        lookup.get.assert_awaited_once()
    asyncio.run(scenario())


def test_admin_bypass_and_ambiguous_query():
    async def scenario():
        lookup = AsyncMock()
        result = await evaluate(policy('owner_or_admin'), claims('admin_1', roles=['admin']), {}, {}, lookup=lookup)
        assert result.verdict == 'PASS'
        lookup.get.assert_not_awaited()
        result = await evaluate(policy(), claims(), {}, MultiDict([('orderId', '1'), ('orderId', '2')]), lookup=lookup)
        assert result.verdict == 'BLOCK'
    asyncio.run(scenario())


def test_cache_expiry(monkeypatch):
    now = [1.0]
    monkeypatch.setattr('proxy.cache.time.monotonic', lambda: now[0])
    cache = LookupCache(2)
    key = ('orders', '1042')
    assert cache.get(key) is MISSING
    cache.set(key, None)
    assert cache.get(key) is None
    now[0] = 3.0
    assert cache.get(key) is MISSING
    cache.set(key, {'user_id': 'user_77'})
    cache.clear()
    assert cache.get(key) is MISSING


def test_readonly_lookup_projection_and_identifiers(tmp_path):
    db = tmp_path / 'demo.db'
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE orders(id TEXT, user_id TEXT, org_id TEXT, private TEXT)')
        conn.execute("INSERT INTO orders VALUES('1042','user_77','org_1','secret')")
    lookup = Lookup('sqlite:///' + str(db))
    spec = policy().params.owner_lookup
    assert asyncio.run(lookup.get(spec, '1042')) == {'user_id': 'user_77', 'org_id': 'org_1'}
    assert asyncio.run(lookup.get(spec, "1042' OR 1=1--")) is None
    with sqlite3.connect(lookup.uri, uri=True) as conn:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute('DELETE FROM orders')
    for field in ('table', 'id_col', 'owner_col', 'tenant_col'):
        invalid = spec.model_copy(update={field: 'id; DROP TABLE orders'})
        with pytest.raises(LookupError):
            asyncio.run(lookup.get(invalid, '1042'))
