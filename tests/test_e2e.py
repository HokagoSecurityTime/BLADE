"""Real HTTP/SQLite lifecycle regression; no LLM or external network calls."""
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import socket
import sqlite3
import time

from aiohttp import ClientSession
from aiohttp.test_utils import TestServer
from fastapi import FastAPI
import jwt
import pytest
import uvicorn

from admin_api.main import create_app as admin_app
from demo_backend.main import create_app as demo_app
from pipeline.classifier.schema import ClassificationResult
from pipeline.generator import build_policy
from pipeline.parsers.oas import parse_oas
from proxy.server import create_app as proxy_app

ROOT = Path(__file__).resolve().parents[1]
SECRET = 'isolated-e2e-secret-at-least-thirty-two-bytes'


@asynccontextmanager
async def serve(app: FastAPI) -> AsyncIterator[str]:
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    server = uvicorn.Server(uvicorn.Config(app, log_level='error', access_log=False))
    task = asyncio.create_task(server.serve(sockets=[listener]))
    try:
        async with asyncio.timeout(10):
            while not server.started:
                if task.done():
                    await task
                    raise RuntimeError('Server failed to start')
                await asyncio.sleep(0.02)
        yield f'http://127.0.0.1:{listener.getsockname()[1]}'
    finally:
        server.should_exit = True
        try:
            await asyncio.wait_for(task, 10)
        finally:
            listener.close()


def test_full_policy_lifecycle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report: list[dict[str, object]] = []
    db = tmp_path / 'demo.db'
    admin_db = tmp_path / 'blade.db'
    jsonl = tmp_path / 'detections.jsonl'
    api = admin_app(admin_db, tmp_path / 'policies', jsonl)
    monkeypatch.setenv('BLADE_JWT_SECRET', SECRET)
    monkeypatch.setenv('BLADE_DB_DSN', 'sqlite:///' + str(db))
    monkeypatch.setenv('BLADE_FAIL_MODE', 'closed')
    monkeypatch.setenv('BLADE_POLICY_POLL_SEC', '0.05')
    monkeypatch.setenv('BLADE_CACHE_TTL', '1')

    def token(user: str, *, expired: bool = False) -> str:
        admin = user == 'admin_1'
        data = dict(sub=user, roles=['admin'] if admin else ['user'],
                    tenant_id='org_2' if user == 'user_99' else 'org_1',
                    membership='premium' if admin else 'basic',
                    exp=int(time.time()) + (-60 if expired else 600))
        return jwt.encode(data, SECRET, algorithm='HS256')

    async def scenario() -> None:
        async with serve(demo_app(db)) as target, serve(api) as admin:
            endpoints = parse_oas((ROOT / 'demo_backend/openapi.json').read_text(encoding='utf-8'))
            saved = json.loads((ROOT / 'verification/classifier-ollama-live.json').read_text(encoding='utf-8'))
            results = {(r['method'], r['path']): r['result'] for r in saved['results']}
            policies = [build_policy(e, ClassificationResult.model_validate(results[(e.method, e.path)])) for e in endpoints]
            api.state.store.insert_many(policies)
            monkeypatch.setenv('BLADE_TARGET_URL', target)
            monkeypatch.setenv('BLADE_ADMIN_URL', admin)
            async with TestServer(proxy_app()) as proxy, ClientSession() as client:
                base = str(proxy.make_url('/')).rstrip('/')

                async def check(name: str, path: str, expected: int, user: str | None = None,
                                method: str = 'GET', *, direct: bool = False, expired: bool = False,
                                poll: bool = False) -> None:
                    headers = {'Authorization': 'Bearer ' + token(user, expired=expired)} if user else {}
                    async with asyncio.timeout(5):
                        while True:
                            async with client.request(method, (target if direct else base) + path, headers=headers) as response:
                                status = response.status
                                await response.read()
                            if not poll or status == expected:
                                break
                            await asyncio.sleep(0.05)
                    assert status == expected, (name, status, expected)
                    report.append(dict(case=name, method=method, path=path, expected=expected, actual=status))

                async def transition(identifier: str, action: str) -> None:
                    async with client.post(admin + '/policies/' + identifier + '/' + action) as response:
                        assert response.status == 200, await response.text()

                await check('direct BOLA remains vulnerable', '/orders/1042', 200, 'user_99', direct=True)
                await check('PENDING is not enforced; uncovered route observed', '/orders/1042', 200, 'user_77')
                for policy in policies:
                    await transition(policy.id, 'approve')
                await check('approval propagates without restart', '/orders/1042', 403, 'user_99', poll=True)
                await check('owner permitted', '/orders/1042', 200, 'user_77')
                await check('public without JWT', '/public/health', 200)
                await check('owner mismatch', '/orders/1042', 403, 'user_99')
                await check('missing JWT', '/orders/1042', 403)
                await check('expired JWT', '/orders/1042', 403, 'user_77', expired=True)
                await check('manual review observes authenticated request', '/users/user_77', 200, 'user_77')

                # Simulate explicit human review through the documented API.
                user_id = 'pol_users_get_by_userId'
                async with client.get(admin + '/policies/' + user_id) as response:
                    edited = await response.json()
                edited.pop('status')
                edited.update(label='owner_or_admin', evidence='E2E reviewed policy: user owns own record; admin bypass.',
                              confidence=1.0, params=dict(object_param='userId', owner_lookup=dict(
                                  table='users', id_col='id', owner_col='id', tenant_col=None),
                                  roles=['admin'], allowed_membership=[]))
                await transition(user_id, 'rollback')
                async with client.put(admin + '/policies/' + user_id, json=edited) as response:
                    assert response.status == 200, await response.text()
                await transition(user_id, 'approve')
                await check('reviewed policy now blocks other owner', '/users/user_77', 403, 'user_99', poll=True)
                await check('reviewed policy permits owner', '/users/user_77', 200, 'user_77')
                await check('admin ownership bypass', '/users/user_77', 200, 'admin_1')
                await check('role denies basic user', '/admin/reports', 403, 'user_77')
                await check('role permits admin', '/admin/reports', 200, 'admin_1')
                await check('tenant matches', '/orgs/org_1/docs', 200, 'user_77')
                await check('tenant mismatch', '/orgs/org_1/docs', 403, 'user_99')
                await check('membership denies basic', '/premium/content', 403, 'user_77')
                await check('membership permits premium', '/premium/content', 200, 'admin_1')
                await check('unauthorized delete blocked', '/orders/1042', 403, 'user_99', method='DELETE')
                await check('blocked delete preserved row', '/orders/1042', 200, 'user_77')
                await check('authorized delete', '/orders/2001', 200, 'user_99', method='DELETE')
                await check('authorized delete reached backend', '/orders/2001', 404, direct=True)
                order_id = 'pol_orders_get_by_orderId'
                await transition(order_id, 'rollback')
                await check('rollback propagates', '/orders/1042', 200, 'user_99', poll=True)
                await transition(order_id, 'reject')
                async with client.post(admin + '/policies/' + order_id + '/approve') as response:
                    assert response.status == 409
                    report.append(dict(case='REJECTED cannot be approved', expected=409, actual=response.status))
            # Proxy cleanup drains the async log queue before checking persistence.
            with sqlite3.connect(admin_db) as conn:
                columns = [r[1] for r in conn.execute('PRAGMA table_info(detections)')]
                logs = [dict(zip(columns, row)) for row in conn.execute('SELECT * FROM detections ORDER BY rowid')]
            lines = [json.loads(line) for line in jsonl.read_text(encoding='utf-8').splitlines()]
            assert logs == lines
            assert {'PASS','BLOCK','OBSERVE'} <= {r['verdict'] for r in logs}
            assert any(r['path']=='/users/user_77' and r['verdict']=='OBSERVE' for r in logs)
            assert any(r['sub']=='user_99' and r['path']=='/orders/1042' and r['verdict']=='BLOCK' for r in logs)
            report.append(dict(case='SQLite and JSONL log equality; PASS/BLOCK/OBSERVE', count=len(logs), passed=True))

    asyncio.run(scenario())
    destination = os.getenv('BLADE_E2E_REPORT')
    if destination:
        Path(destination).write_text(json.dumps({'passed':True, 'cases':report}, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
