"""Failure matrix: local Redis double and real loopback HTTP servers."""
import asyncio
from unittest.mock import AsyncMock

from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer
import jwt
import pytest
import redis

from proxy.cache import LookupCache, MISSING
from proxy.evaluator import evaluate
from proxy.server import create_app
from tests.test_proxy import policy, claims, SECRET


class RedisDouble:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.down = False

    def check(self) -> None:
        if self.down:
            raise redis.ConnectionError('Test connection failure')

    def get(self, key: str) -> str | None:
        self.check()
        return self.values.get(key)

    def set(self, key: str, value: str, **kwargs: object) -> None:
        self.check()
        self.values[key] = value

    def pttl(self, key: str) -> int:
        self.check()
        return 1000

    def scan_iter(self, **kwargs: object) -> list[str]:
        self.check()
        return list(self.values)

    def delete(self, key: str) -> None:
        self.check()
        self.values.pop(key, None)


def test_redis_disconnect_memory_and_recovery(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    monkeypatch.setenv('BLADE_REDIS_URL', 'redis://test')
    remote = RedisDouble()
    monkeypatch.setattr(redis.Redis, 'from_url', lambda *args, **kwargs: remote)
    now = [100.0]
    monkeypatch.setattr('proxy.cache.time.monotonic', lambda: now[0])
    cache = LookupCache(1)
    key = ('orders', '1042')
    value = (('id', 'user_id', None), {'user_id': 'user_77'})
    cache.set(key, value)
    assert remote.values and cache.get(key) == value
    remote.down = True
    assert cache.get(key) == value  # failure falls back, never throws to the caller
    now[0] += 1.1
    assert cache.get(key) is MISSING
    cache.set(key, value)
    cache.clear()  # cache invalidation while disconnected must survive reconnect
    assert cache.get(key) is MISSING
    remote.down = False
    now[0] += 5
    assert cache.get(key) is MISSING and not remote.values
    cache.set(key, value)
    assert cache.get(key) == value


@pytest.mark.parametrize('fail_mode', ['open', 'closed'])
@pytest.mark.parametrize('policy_mode', ['observe', 'enforce'])
@pytest.mark.parametrize('exception', [TimeoutError('timeout'), RuntimeError('db failure')])
def test_database_errors(fail_mode: str, policy_mode: str, exception: Exception,
                         monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    p = policy()
    p.mode = policy_mode
    source = AsyncMock()
    source.get.side_effect = exception
    result = asyncio.run(evaluate(p, claims(), {'orderId': '1042'}, {}, lookup=source, fail_mode=fail_mode))
    blocked = fail_mode == 'closed' and policy_mode == 'enforce'
    assert result.verdict == ('BLOCK' if blocked else 'OBSERVE')
    assert result.reason == 'lookup_failed' and not result.lookup_ok
    assert result.would_block == (fail_mode == 'closed' and policy_mode == 'observe')


@pytest.mark.parametrize('fail_mode', ['open', 'closed'])
def test_missing_secret(fail_mode: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('BLADE_JWT_SECRET', raising=False)
    monkeypatch.setenv('BLADE_FAIL_MODE', fail_mode)
    with pytest.raises(ValueError, match='BLADE_JWT_SECRET'):
        create_app()


@pytest.mark.parametrize('fail_mode', ['open', 'closed'])
@pytest.mark.parametrize('fault', ['admin', 'yaml', 'backend'])
def test_http_failure_matrix(fail_mode: str, fault: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    monkeypatch.setenv('BLADE_OBSERVABILITY_ENABLED', 'false')
    monkeypatch.setenv('BLADE_JWT_SECRET', SECRET)
    monkeypatch.setenv('BLADE_FAIL_MODE', fail_mode)
    monkeypatch.setenv('BLADE_POLICY_POLL_SEC', '.02')
    monkeypatch.delenv('BLADE_REDIS_URL', raising=False)
    p = policy('public' if fault == 'backend' else 'role_required')
    p.mode = 'enforce'
    state = {'failed': False}
    logs: list[dict] = []

    async def scenario() -> None:
        async def policies(request: web.Request) -> web.Response:
            if state['failed'] and fault == 'admin':
                return web.Response(status=503)
            if state['failed'] and fault == 'yaml':
                return web.json_response([{'id': p.id, 'label': 'INVALID'}])
            return web.json_response([p.model_dump(mode='json')])

        async def log(request: web.Request) -> web.Response:
            logs.append(await request.json())
            return web.json_response({'accepted': True})

        async def backend(request: web.Request) -> web.Response:
            return web.json_response({'forwarded': True})

        api = web.Application()
        api.router.add_get('/policies', policies)
        api.router.add_post('/detections', log)
        target = web.Application()
        target.router.add_get('/orders/1042', backend)
        async with TestServer(api) as admin, TestServer(target) as upstream, ClientSession() as client:
            monkeypatch.setenv('BLADE_ADMIN_URL', str(admin.make_url('/')).rstrip('/'))
            monkeypatch.setenv('BLADE_TARGET_URL', str(upstream.make_url('/')).rstrip('/'))
            async with TestServer(create_app()) as proxy:
                headers = {'Authorization': 'Bearer ' + jwt.encode(claims().model_dump(), SECRET, algorithm='HS256')}
                async with client.get(proxy.make_url('/orders/1042'), headers=headers) as response:
                    assert response.status == (200 if fault == 'backend' else 403)
                state['failed'] = True
                if fault == 'backend':
                    await upstream.close()
                await asyncio.sleep(.1)
                async with client.get(proxy.make_url('/orders/1042'), headers=headers) as response:
                    assert response.status == (502 if fault == 'backend' else 403)
        assert logs[-1]['verdict'] == ('PASS' if fault == 'backend' else 'BLOCK')
        assert logs[-1]['reason'] == ('public' if fault == 'backend' else 'policy_mismatch')
    asyncio.run(scenario())


def test_redis_feature_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    monkeypatch.setenv('BLADE_REDIS_ENABLED', 'false')
    monkeypatch.setenv('BLADE_REDIS_URL', 'redis://unreachable:6379')
    def unexpected(*args: object, **kwargs: object) -> None:
        pytest.fail('Disabled Redis must not construct a client')
    monkeypatch.setattr(redis.Redis, 'from_url', unexpected)
    cache = LookupCache()
    cache.set(('a', 'b'), None)
    assert cache.get(('a', 'b')) is None
