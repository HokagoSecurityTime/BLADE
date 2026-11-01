"""Local sequential latency experiment; not a load/capacity benchmark."""
import argparse
import asyncio
import json
import math
import os
from pathlib import Path
import statistics
import tempfile
import time

from aiohttp import ClientSession
from aiohttp.test_utils import TestServer
import jwt

from admin_api.main import create_app as admin_app
from demo_backend.main import create_app as demo_app
from proxy.server import create_app as proxy_app
from tests.test_e2e import serve
from tests.test_proxy import SECRET, claims, policy


async def benchmark(samples: int) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix='blade-benchmark-') as directory:
        root=Path(directory)
        api=admin_app(root/'blade.db',root/'policies',root/'detections.jsonl')
        async with serve(demo_app(root/'demo.db')) as target, serve(api) as admin:
            p=policy()
            p.params.owner_lookup.tenant_col=None
            api.state.store.insert_many([p])
            os.environ.update(BLADE_JWT_SECRET=SECRET, BLADE_DB_DSN='sqlite:///'+str(root/'demo.db'),
                              BLADE_TARGET_URL=target, BLADE_ADMIN_URL=admin, BLADE_FAIL_MODE='closed',
                              BLADE_POLICY_POLL_SEC='5',BLADE_CACHE_TTL='60')
            headers={'Authorization':'Bearer '+jwt.encode(claims().model_dump(),SECRET,algorithm='HS256')}
            durations: dict[str,list[float]]={'direct':[],'proxy':[]}
            async with TestServer(proxy_app()) as proxy, ClientSession() as client:
                urls={'direct':target+'/orders/1042','proxy':str(proxy.make_url('/orders/1042'))}
                for i in range(samples+5):
                    order=('direct','proxy') if i%2==0 else ('proxy','direct')
                    for name in order:
                        start=time.perf_counter()
                        async with client.get(urls[name],headers=headers) as response:
                            assert response.status==200
                            assert (await response.json())['user_id']=='user_77'
                        if i>=5:
                            durations[name].append((time.perf_counter()-start)*1000)
            summaries={}
            for name,values in durations.items():
                summaries[name]={'mean_ms':statistics.mean(values),'p50_ms':statistics.median(values),
                                 'p95_ms':sorted(values)[math.ceil(len(values)*.95)-1]}
            return dict(samples_per_path=samples,warmup_pairs=5,concurrency=1,
                        environment='Loopback HTTP, same Python process, real uvicorn/aiohttp/SQLite',
                        summary=summaries,mean_added_ms=summaries['proxy']['mean_ms']-summaries['direct']['mean_ms'],
                        measurements_ms=durations,notes='Includes JWT, fresh read-only lookup and log enqueue; asynchronous log persistence is not in response timing.')


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=50)
    args=parser.parse_args()
    if args.samples<1 or args.output.exists():
        parser.error('Use positive samples and a new output file')
    result=asyncio.run(benchmark(args.samples))
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='measurements_ms'}))


if __name__=='__main__':
    main()
