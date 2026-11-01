import argparse
import asyncio
from collections import defaultdict
import json
from pathlib import Path
import tempfile
import time

from proxy import server
from proxy.cache import LookupCache
from proxy.lookup import BatchedLookup
from admin_api.store import Store
from scripts.load_test import scenario
from scripts.attack_sim import percentile

timings = defaultdict(list)

def asynchronous(original, name):
    async def wrapped(*args, **kwargs):
        started = time.perf_counter()
        try:
            return await original(*args, **kwargs)
        finally:
            timings[name].append((time.perf_counter()-started)*1000)
    return wrapped

def synchronous(original, name):
    def wrapped(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            timings[name].append((time.perf_counter()-started)*1000)
    return wrapped

async def main():
    server.evaluate = asynchronous(server.evaluate, 'evaluate')
    LookupCache.aget = asynchronous(LookupCache.aget, 'redis_get')
    LookupCache.aset = asynchronous(LookupCache.aset, 'redis_set')
    BatchedLookup.get = asynchronous(BatchedLookup.get, 'owner_lookup')
    Store.append_detections = synchronous(Store.append_detections, 'detection_commit')
    args = argparse.Namespace(redis_url='redis://127.0.0.1:16382/8', duration=5)
    with tempfile.TemporaryDirectory(dir='verification/phase2') as directory:
        result = await scenario(Path(directory), 2, 50, 'warm', args)
    report = dict(result=result, timings={k:dict(count=len(v),p50=percentile(v,.5),p95=percentile(v,.95)) for k,v in timings.items()})
    Path('verification/phase2/profile-improvements.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__ == '__main__': asyncio.run(main())
