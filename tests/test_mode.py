"""Phase 2 opt-in: exercise real admin/backend HTTP, hot reload and persistence."""
import asyncio
import json
from pathlib import Path
import sqlite3
from unittest.mock import AsyncMock

from aiohttp import ClientSession
from aiohttp.test_utils import TestServer
import httpx
import jwt
import pytest

from admin_api.main import create_app as admin_app
from common.schema import PolicyStatus, Verdict, policy_from_yaml, policy_to_yaml
from demo_backend.main import create_app as demo_app
from proxy.evaluator import evaluate
from proxy.observability import Observability
from proxy.server import create_app as proxy_app
from tests.test_e2e import serve
from tests.test_proxy import claims, policy, SECRET


@pytest.fixture(autouse=True)
def disable_unrelated_rag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_RAG_ENABLED', 'false')


@pytest.mark.parametrize('events,expected', [([], (0, 0, 0, 0)),
    ([(False, False)], (1, 0, 0, 0)),
    ([(True, True), (False, False), (True, False)], (3, 2, 1, 2/3))])
def test_rolling_metrics(events: list, expected: tuple) -> None:
    now = [100.0]
    counters = Observability(lambda: now[0])
    for matched, lookup in events:
        counters.record(matched, lookup)
    assert tuple(counters.snapshot().values()) == expected
    now[0] += 60
    assert tuple(counters.snapshot().values()) == (0, 0, 0, 0)


def test_observe_enforce_and_reapproval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in {'BLADE_PHASE2_ENABLED': 'true', 'BLADE_JWT_SECRET': SECRET,
                        'BLADE_POLICY_POLL_SEC': '.02', 'BLADE_DB_DSN': 'sqlite:///' + str(tmp_path/'demo.db')}.items():
        monkeypatch.setenv(name, value)

    async def scenario() -> None:
        api = admin_app(tmp_path/'blade.db', tmp_path/'policies', tmp_path/'detections.jsonl')
        p = policy()
        p.params.owner_lookup.tenant_col = None
        p.status = PolicyStatus.PENDING
        token = jwt.encode(claims('user_99').model_dump(), SECRET, algorithm='HS256')
        async with serve(demo_app(tmp_path/'demo.db')) as target, serve(api) as admin, ClientSession() as client:
            api.state.store.insert_many([p])
            monkeypatch.setenv('BLADE_TARGET_URL', target)
            monkeypatch.setenv('BLADE_ADMIN_URL', admin)
            url = admin + '/policies/' + p.id

            async def action(action: str, data: dict | None = None, expected: int = 200) -> dict:
                async with client.post(url + '/' + action, json=data) as response:
                    assert response.status == expected, await response.text()
                    return await response.json()

            await action('mode', {'mode': 'enforce'}, 409)
            assert (await action('approve'))['mode'] == 'observe'
            async with TestServer(proxy_app()) as proxy:
                async def request(expected: int, verdict: str, would_block: bool) -> None:
                    # Allow the policy poller to acquire the new snapshot.
                    await asyncio.sleep(.08)
                    async with client.get(proxy.make_url('/orders/1042'), headers={'Authorization': 'Bearer '+token}) as response:
                        assert response.status == expected, await response.text()
                        identifier = response.headers['X-Blade-Request-Id']
                    for _ in range(100):
                        async with client.get(admin+'/detections') as response:
                            rows = await response.json()
                        row = next((row for row in rows if row['request_id'] == identifier), None)
                        if row:
                            assert row['verdict'] == verdict and row['would_block'] == would_block
                            assert row['mode'] == ('enforce' if expected == 403 else 'observe')
                            return
                        await asyncio.sleep(.02)
                    pytest.fail('Detection was not delivered')

                await request(200, 'OBSERVE', True)
                assert (await action('mode', {'mode': 'enforce'}))['mode'] == 'enforce'
                await request(403, 'BLOCK', False)
                assert (await action('rollback'))['status'] == 'PENDING'
                await action('mode', {'mode': 'enforce'}, 409)
                assert (await action('approve'))['mode'] == 'observe'
                await request(200, 'OBSERVE', True)
                for _ in range(100):
                    async with client.get(admin+'/metrics/observability') as response:
                        metric = await response.json()
                    if metric['total'] == 3:
                        assert metric == dict(total=3, with_policy=3, lookup_ok=3, rate=1.0)
                        break
                    await asyncio.sleep(.02)
                else:
                    pytest.fail('Metrics were not delivered')
        with sqlite3.connect(tmp_path/'blade.db') as conn:
            assert conn.execute('SELECT mode,would_block FROM detections ORDER BY rowid').fetchall() == [
                ('observe', 1), ('enforce', 0), ('observe', 1)]
        records = [json.loads(line) for line in (tmp_path/'detections.jsonl').read_text().splitlines()]
        assert [r['would_block'] for r in records] == [True, False, True]
    asyncio.run(scenario())


def test_off_and_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    p = policy()
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    result = asyncio.run(evaluate(p, None, {}, {}))
    assert result.verdict == Verdict.OBSERVE and result.would_block and result.reason == 'no_token'
    monkeypatch.setenv('BLADE_MODE_ENABLED', 'false')
    result = asyncio.run(evaluate(p, None, {}, {}))
    assert result.verdict == Verdict.BLOCK and not result.would_block


def test_lookup_success_definition(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    p = policy()
    missing = AsyncMock()
    missing.get.return_value = None
    result = asyncio.run(evaluate(p, claims(), {'orderId': '999'}, {}, lookup=missing))
    assert result.lookup_ok and result.reason == 'object_not_found'
    missing.get.side_effect = TimeoutError()
    result = asyncio.run(evaluate(p, claims(), {'orderId': '999'}, {}, lookup=missing, fail_mode='closed'))
    assert not result.lookup_ok and result.would_block and result.verdict == Verdict.OBSERVE


def test_metrics_api_and_legacy_migration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    api = admin_app(tmp_path/'blade.db', tmp_path/'policies', tmp_path/'logs.jsonl')
    with sqlite3.connect(tmp_path/'blade.db') as conn:
        conn.execute('CREATE TABLE detections(ts TEXT,request_id TEXT,sub TEXT,method TEXT,path TEXT,policy_id TEXT,label TEXT,verdict TEXT,reason TEXT)')
        conn.execute("INSERT INTO detections VALUES ('2026-01-01T00:00:00Z','old','','GET','/','', 'public','PASS','public')")
    async def scenario() -> None:
        async with api.router.lifespan_context(api), httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url='http://test') as client:
            row = (await client.get('/detections')).json()[0]
            assert row['mode'] == 'observe' and row['would_block'] is False
            for name, total, matched, lookup in [('a', 4, 2, 1), ('b', 2, 1, 0), ('a', 4, 2, 1)]:
                assert (await client.post('/metrics/observability', json=dict(reporter=name, total=total, with_policy=matched, lookup_ok=lookup))).status_code == 200
            assert (await client.get('/metrics/observability')).json() == dict(total=6, with_policy=3, lookup_ok=1, rate=.5)
            assert (await client.post('/metrics/observability', json=dict(reporter='x', total=1, with_policy=2, lookup_ok=0))).status_code == 422
            monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'false')
            assert (await client.get('/metrics/observability')).status_code == 404
    asyncio.run(scenario())
    legacy = '\n'.join(line for line in policy_to_yaml(policy()).splitlines() if not line.startswith(('mode:', 'version:', 'source:', 'evidence_refs:')))
    assert policy_from_yaml(legacy).mode == 'observe'


def test_phase2_seven_step_driver(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tests.test_compose_demo import test_seven_step_driver
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    test_seven_step_driver(tmp_path, monkeypatch)
