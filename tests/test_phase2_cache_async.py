import asyncio
from unittest.mock import Mock

import pytest

from proxy.cache import LookupCache, MISSING


class Remote:
    def __init__(self) -> None:
        self.values = {}
        self.calls = 0
        self.down = False
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self.release.set()

    async def eval(self, script, count, *keys):
        self.calls += 1
        snapshot = [[self.values.get(k), 1000] for k in keys]
        self.entered.set()
        await self.release.wait()
        if self.down:
            raise OSError('offline')
        return snapshot

    async def set(self, key, value, **kwargs):
        if self.down:
            raise OSError('offline')
        self.values[key] = value

    async def delete(self, key):
        self.values.pop(key, None)

    async def scan_iter(self, **kwargs):
        for key in list(self.values):
            yield key

    async def aclose(self):
        pass

    def pipeline(self, **kwargs):
        remote = self
        class Pipeline:
            def __init__(self): self.pending = []
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            def set(self, key, value, **options):
                self.pending.append((key, value, options))
            async def execute(self):
                for key, value, options in self.pending:
                    await remote.set(key, value, **options)
        return Pipeline()


def cache_pair(monkeypatch):
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    monkeypatch.setenv('BLADE_REDIS_URL', 'redis://test')
    monkeypatch.setattr('redis.Redis.from_url', Mock(return_value=Mock()))
    cache = LookupCache(1)
    remote = Remote()
    cache._async_redis = remote
    return cache, remote


@pytest.mark.parametrize('distinct', [False, True])
def test_burst_shares_network_without_persistent_local_hits(monkeypatch, distinct):
    async def run():
        cache, remote = cache_pair(monkeypatch)
        keys = [('orders', str(i if distinct else 1)) for i in range(100)]
        value = (('id', 'user_id', None), {'user_id': 'owner'})
        for key in set(keys):
            await cache.aset(key, value)
        assert await asyncio.gather(*(cache.aget(k) for k in keys)) == [value] * 100
        assert remote.calls == 1
        remote.values.clear()
        assert await cache.aget(keys[0]) is MISSING
        assert remote.calls == 2
        await cache.aclose()
    asyncio.run(run())


def test_clear_during_read_and_late_database_result(monkeypatch):
    async def run():
        cache, remote = cache_pair(monkeypatch)
        key = ('orders', '1')
        value = (('id', 'user_id', None), {'user_id': 'old_owner'})
        await cache.aset(key, value)
        generation = cache.generation
        remote.release.clear()
        reading = asyncio.create_task(cache.aget(key))
        await remote.entered.wait()
        await cache.aclear()
        remote.release.set()
        assert await reading is MISSING
        await cache.aset(key, value, generation=generation)
        assert await cache.aget(key) is MISSING
        await cache.aclose()
    asyncio.run(run())


def test_failure_fallback_expiry_and_repair(monkeypatch):
    async def run():
        cache, remote = cache_pair(monkeypatch)
        key = ('orders', '1')
        value = (('id', 'user_id', None), None)
        await cache.aset(key, value)
        remote.down = True
        assert await cache.aget(key) == value
        cache._entries[key] = (0, value)
        assert await cache.aget(key) is MISSING
        await cache.aclear()
        remote.down = False
        cache._retry_at = 0
        assert await cache.aget(key) is MISSING
        await cache.aclose()
    asyncio.run(run())
