import asyncio
from pathlib import Path
import sqlite3

from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer
import jwt
import pytest

from proxy.server import create_app
from tests.test_proxy import SECRET, claims, policy


@pytest.mark.parametrize('mode', ['open', 'closed'])
def test_snapshot_retained_during_outage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    monkeypatch.setenv('BLADE_JWT_SECRET', SECRET)
    monkeypatch.setenv('BLADE_FAIL_MODE', mode)
    monkeypatch.setenv('BLADE_POLICY_POLL_SEC', '0.03')
    monkeypatch.setenv('BLADE_CACHE_TTL', '0.2')
    monkeypatch.setenv('BLADE_DB_DSN', 'sqlite:///' + str(tmp_path/'absent.db'))
    state = {'available': True}

    async def scenario() -> None:
        async def policies(request: web.Request) -> web.Response:
            if not state['available']:
                return web.json_response({'detail':'test outage'}, status=503)
            return web.json_response([policy('role_required').model_dump(mode='json')])
        async def upstream(request: web.Request) -> web.Response:
            return web.json_response({'forwarded':True})
        admin = web.Application()
        admin.router.add_get('/policies',policies)
        admin.router.add_post('/detections',upstream)
        target = web.Application()
        target.router.add_get('/orders/1042',upstream)
        async with TestServer(admin) as a, TestServer(target) as t:
            monkeypatch.setenv('BLADE_ADMIN_URL', str(a.make_url('/')).rstrip('/'))
            monkeypatch.setenv('BLADE_TARGET_URL', str(t.make_url('/')).rstrip('/'))
            async with TestServer(create_app()) as proxy, ClientSession() as client:
                headers = {'Authorization':'Bearer '+jwt.encode(claims().model_dump(),SECRET,algorithm='HS256')}

                async def status() -> int:
                    async with client.get(proxy.make_url('/orders/1042'),headers=headers) as response:
                        await response.read()
                        return response.status

                assert await status() == 403
                state['available'] = False
                await asyncio.sleep(.3)
                assert await status() == 403
                state['available'] = True
                async with asyncio.timeout(3):
                    while await status() != 403:
                        await asyncio.sleep(.03)
    asyncio.run(scenario())


@pytest.mark.parametrize('mode', ['open','closed'])
def test_database_failure_and_log_outage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    monkeypatch.setenv('BLADE_JWT_SECRET', SECRET)
    monkeypatch.setenv('BLADE_FAIL_MODE', mode)
    monkeypatch.setenv('BLADE_DB_DSN', 'sqlite:///' + str(tmp_path/'missing.db'))

    async def scenario() -> None:
        async def policies(request: web.Request) -> web.Response:
            return web.json_response([policy().model_dump(mode='json')])
        async def failed_log(request: web.Request) -> web.Response:
            return web.Response(status=503)
        async def upstream(request: web.Request) -> web.Response:
            return web.Response(text='ok')
        admin = web.Application()
        admin.router.add_get('/policies',policies)
        admin.router.add_post('/detections',failed_log)
        target = web.Application()
        target.router.add_get('/orders/1042',upstream)
        async with TestServer(admin) as a, TestServer(target) as t:
            monkeypatch.setenv('BLADE_ADMIN_URL',str(a.make_url('/')).rstrip('/'))
            monkeypatch.setenv('BLADE_TARGET_URL',str(t.make_url('/')).rstrip('/'))
            async with TestServer(create_app()) as proxy, ClientSession() as client:
                headers={'Authorization':'Bearer '+jwt.encode(claims().model_dump(),SECRET,algorithm='HS256')}
                async with client.get(proxy.make_url('/orders/1042'),headers=headers) as response:
                    assert response.status == (200 if mode=='open' else 403)
                # JWT errors must not turn into fail-open forwarding.
                async with client.get(proxy.make_url('/orders/1042')) as response:
                    assert response.status == 403
        assert not (tmp_path/'missing.db').exists()
    asyncio.run(scenario())
