"""Real isolated Redis: invalidation, TTL, stream retry, and idempotent commit."""
import asyncio
import json
import os
from pathlib import Path
import time
import uuid

from redis.asyncio import Redis

from admin_api.store import Store
from common.redis_detections import consume, stream_name
from proxy.cache import LookupCache, MISSING
from tests.test_alerts import record


async def main() -> None:
    output = Path('verification/phase2') / ('cache-stream-' + time.strftime('%Y%m%d-%H%M%S'))
    output.mkdir()
    os.environ.update(BLADE_PHASE2_ENABLED='true', BLADE_REDIS_ENABLED='true',
        BLADE_REDIS_LOCAL_CACHE_ENABLED='true', BLADE_DETECTION_STREAM_ENABLED='true',
        BLADE_REDIS_URL='redis://127.0.0.1:16382/12', BLADE_DB_DSN=str(output.resolve()))
    remote = Redis.from_url(os.environ['BLADE_REDIS_URL'], decode_responses=True)
    first, second = LookupCache(.4), LookupCache(.4)
    store = Store(output/'blade.db', output/'policies', output/'detections.jsonl')
    store.initialize()
    stop = asyncio.Event()
    worker = None
    try:
        await first.start()
        await second.start()
        assert first._tracking_ready and second._tracking_ready
        key = ('orders', '1')
        old = (('id', 'user_id', None), {'user_id': 'old'})
        new = (('id', 'user_id', None), {'user_id': 'new'})
        await first.aset(key, old)
        await asyncio.sleep(.03)
        assert await second.aget(key) == old
        # External write: actual Redis server-assisted invalidation, not a mock.
        await remote.set(first._key(key), json.dumps(new), px=400)
        for _ in range(100):
            if await second.aget(key) == new: break
            await asyncio.sleep(.01)
        else: raise AssertionError('Remote update did not invalidate local ownership')
        await first.aclear()
        for _ in range(100):
            if await second.aget(key) is MISSING: break
            await asyncio.sleep(.01)
        else: raise AssertionError('Cross-proxy clear did not invalidate local ownership')
        await first.aset(key, old)
        await asyncio.sleep(.03)
        assert await second.aget(key) == old
        await asyncio.sleep(.45)
        assert await second.aget(key) is MISSING
        original = store.append_detections
        attempts = 0

        def fail_once(records, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1: raise OSError('Explicit transient DB failure fixture')
            return original(records, **kwargs)
        store.append_detections = fail_once
        rows = [record().model_copy(update={'request_id': uuid.uuid4().hex}) for _ in range(100)]
        async with remote.pipeline(transaction=False) as pipeline:
            for row in rows + rows:  # Simulate uncertain producer-send replay.
                pipeline.xadd(stream_name(), {'record': row.model_dump_json()})
            pipeline.xadd(stream_name(), {'records': '[' + ','.join(row.model_dump_json() for row in rows) + ']'})
            await pipeline.execute()
        worker = asyncio.create_task(consume(store, stop))
        for _ in range(200):
            if await remote.xlen(stream_name()) == 0: break
            await asyncio.sleep(.025)
        else: raise AssertionError('Stream was not drained')
        assert len(store.list_detections(1000)) == 100
        assert len((output/'detections.jsonl').read_text().splitlines()) == 100
        assert attempts >= 2
        result = dict(redis_tracking=True, remote_update_invalidated=True, cross_proxy_clear=True,
            ttl_preserved=True, transient_db_failure_retried=True, sent_with_replays=300, stored_unique=100,
            stream_pending=0)
        (output/'results.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result), flush=True)
        print(output, flush=True)
    finally:
        stop.set()
        if worker: await worker
        await first.aclose()
        await second.aclose()
        await remote.aclose()


if __name__ == '__main__': asyncio.run(main())
