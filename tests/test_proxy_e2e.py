"""Real demo/admin HTTP servers, isolated SQLite, approvals via the admin API."""
import asyncio
import json
import sqlite3
from contextlib import asynccontextmanager

import jwt
import pytest
from aiohttp import ClientSession
from aiohttp.test_utils import TestServer

from admin_api.main import create_app as admin_app
from demo_backend.main import create_app as demo_app
from proxy.server import create_app
from tests.test_e2e import serve
from tests.test_proxy import policy, claims, SECRET


@pytest.fixture
def approved_stack(tmp_path, monkeypatch):
    @asynccontextmanager
    async def stack():
        db = tmp_path / 'demo.db'
        logs = tmp_path / 'detections.jsonl'
        api = admin_app(tmp_path / 'blade.db', tmp_path / 'policies', logs)
        policies = []
        for method, path, label, param, table, owner in [
            ('GET', '/orders/{orderId}', 'owner_match', 'orderId', 'orders', 'user_id'),
            ('DELETE', '/orders/{orderId}', 'owner_match', 'orderId', 'orders', 'user_id'),
            ('GET', '/users/{userId}', 'owner_or_admin', 'userId', 'users', 'id'),
            ('GET', '/admin/reports', 'role_required', None, None, None),
        ]:
            p = policy(label)
            p.id = f'pol_{len(policies)}'
            p.status = type(p.status).PENDING
            p.endpoint.method, p.endpoint.path = method, path
            p.params.object_param = param
            if table:
                p.params.owner_lookup.table = table
                p.params.owner_lookup.owner_col = owner
                p.params.owner_lookup.tenant_col = None
            else:
                p.params.owner_lookup = None
            policies.append(p)
        async with serve(demo_app(db)) as target, serve(api) as admin, ClientSession() as client:
            api.state.store.insert_many(policies)
            for p in policies:
                async with client.post(admin + '/policies/' + p.id + '/approve') as response:
                    assert response.status == 200
                    assert (await response.json())['status'] == 'ACTIVE'
            for key, value in dict(BLADE_JWT_SECRET=SECRET, BLADE_TARGET_URL=target,
                BLADE_ADMIN_URL=admin, BLADE_DB_DSN='sqlite:///' + str(db),
                BLADE_FAIL_MODE='closed').items():
                monkeypatch.setenv(key, value)
            async with TestServer(create_app()) as proxy:
                yield client, str(proxy.make_url('/')).rstrip('/'), db
        records = [json.loads(line) for line in logs.read_text().splitlines()]
        assert len(records) == 6
        assert sum(r['verdict'] == 'BLOCK' for r in records) == 3
        assert len({r['request_id'] for r in records}) == 6
    return stack


def test_enforcement(approved_stack):
    async def scenario():
        async with approved_stack() as (client, base, db):
            cases = [
                ('GET', '/orders/1042', 'user_99', 403),
                ('GET', '/orders/1042', 'user_77', 200),
                ('DELETE', '/orders/1042', 'user_99', 403),
                ('GET', '/users/user_99', 'admin_1', 200),
                ('GET', '/admin/reports', 'user_99', 403),
                ('GET', '/orders/9999', 'user_99', 404),
            ]
            for method, path, user, expected in cases:
                token = jwt.encode(claims(user, roles=['admin'] if user == 'admin_1' else ['user']).model_dump(), SECRET, algorithm='HS256')
                async with client.request(method, base + path, headers={'Authorization': 'Bearer ' + token}) as response:
                    assert response.status == expected, await response.text()
                    assert response.headers['X-Blade-Policy']
                    if expected == 403:
                        body = await response.json()
                        assert body == dict(error='forbidden', policy_id=response.headers['X-Blade-Policy'],
                                            request_id=response.headers['X-Blade-Request-Id'])
                if method == 'DELETE':
                    with sqlite3.connect(db) as conn:
                        assert conn.execute('SELECT user_id FROM orders WHERE id=1042').fetchone() == ('user_77',)
    asyncio.run(scenario())

