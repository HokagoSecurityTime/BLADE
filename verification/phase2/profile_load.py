"""Diagnostic instrumentation only; does not edit/optimize the proxy."""
import argparse
import asyncio
from collections import defaultdict
import json
import os
from pathlib import Path
import tempfile
import time

from proxy import server
from proxy.cache import LookupCache
from proxy.lookup import Lookup
from scripts.load_test import scenario
from scripts.attack_sim import percentile

OUT=Path('verification/phase2')
timings=defaultdict(list)


def key(name: str) -> str:
    return os.getenv('BLADE_PHASE2_ENABLED','false')+'/'+name


def sync_wrapper(original,name: str):
    def wrapped(*args,**kwargs):
        start=time.perf_counter()
        try:return original(*args,**kwargs)
        finally:timings[key(name)].append((time.perf_counter()-start)*1000)
    return wrapped


def async_wrapper(original,name: str):
    async def wrapped(*args,**kwargs):
        start=time.perf_counter()
        try:return await original(*args,**kwargs)
        finally:timings[key(name)].append((time.perf_counter()-start)*1000)
    return wrapped


async def main() -> None:
    LookupCache.get=sync_wrapper(LookupCache.get,'cache.get execution (queue wait excluded)')
    LookupCache.set=sync_wrapper(LookupCache.set,'cache.set execution (queue wait excluded)')
    Lookup._get=sync_wrapper(Lookup._get,'SQLite execution (queue wait excluded)')
    Lookup.get=async_wrapper(Lookup.get,'SQLite await (queue wait included)')
    server.evaluate=async_wrapper(server.evaluate,'evaluate await (queue wait included)')
    args=argparse.Namespace(redis_url='redis://127.0.0.1:16379/9',duration=5)
    results=[]
    with tempfile.TemporaryDirectory(dir=OUT) as directory:
        for phase in (1,2):results.append(await scenario(Path(directory),phase,200,'warm',args))
    measures={k:dict(count=len(v),p50_ms=percentile(v,.5),p95_ms=percentile(v,.95)) for k,v in timings.items()}
    (OUT/'load-profile.json').write_text(json.dumps(dict(results=results,timings=measures),indent=2),encoding='utf-8')


if __name__=='__main__':asyncio.run(main())
