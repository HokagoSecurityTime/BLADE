"""Controlled local HTTP comparison, identical backend/policy under Phase 1 and 2.

Cold: unique existing object IDs (no cache hits). Warm: one primed existing ID.
The servers and client share one process, so this is a development regression
guard, not a production capacity claim. No LLM/embedding runs during measurement.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
from contextlib import asynccontextmanager, closing
import socket
import subprocess
import sys
import uuid

import aiohttp
from aiohttp.test_utils import TestServer
import jwt
import uvicorn

from admin_api.main import create_app as admin_app
from common.schema import Policy
from demo_backend.main import create_app as demo_app
from proxy.server import create_app as proxy_app
from scripts.attack_sim import percentile


@asynccontextmanager
async def serve(app):
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,log_level='error',access_log=False))
    task=asyncio.create_task(server.serve(sockets=[sock]))
    for _ in range(500):
        if server.started:break
        if task.done():await task
        await asyncio.sleep(.01)
    else:raise RuntimeError('HTTP server startup timeout')
    try:yield f'http://127.0.0.1:{port}'
    finally:
        server.should_exit=True
        await task
        sock.close()


@asynccontextmanager
async def service_process(role: str, db: Path):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    stop = db.parent / (role + '-' + uuid.uuid4().hex + '.stop')
    with (db.parent / (db.stem + '-' + role + '.log')).open('w', encoding='utf-8') as output:
        process = subprocess.Popen([sys.executable, '-m', 'scripts.load_test_service', role,
            '--db', str(db.resolve()), '--port', str(port), '--stop', str(stop.resolve())],
            stdout=output, stderr=subprocess.STDOUT, env=os.environ.copy(),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        try:
            for _ in range(300):
                if process.poll() is not None:
                    raise RuntimeError(f'{role} exited during startup: {process.returncode}')
                try:
                    _, writer = await asyncio.open_connection('127.0.0.1', port)
                    writer.close()
                    await writer.wait_closed()
                    break
                except OSError:
                    await asyncio.sleep(.1)
            else:
                raise RuntimeError(f'{role} startup timeout')
            yield f'http://127.0.0.1:{port}'
        finally:
            stop.write_text('stop', encoding='utf-8')
            try:
                await asyncio.to_thread(process.wait, 60)
            except subprocess.TimeoutExpired:
                process.terminate()
                await asyncio.to_thread(process.wait, 10)
                raise RuntimeError(f'{role} did not shut down cleanly')
            if process.returncode:
                raise RuntimeError(f'{role} exit code {process.returncode}')


@asynccontextmanager
async def proxy_service(directory: Path, processes: bool):
    if processes:
        async with service_process('proxy', directory/'proxy.db') as url:
            yield url
    else:
        async with TestServer(proxy_app()) as proxy:
            yield str(proxy.make_url('/')).rstrip('/')


async def measure(url: str, token: str, concurrency: int, duration: float, cache: str) -> dict:
    latencies=[];errors=0;counter=0
    connector=aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector,timeout=aiohttp.ClientTimeout(total=30),
                                    headers={'Authorization':'Bearer '+token}) as client:
        if cache=='warm':
            async with client.get(url+'/orders/1042') as response:
                await response.read()
                assert response.status==200
        start=time.perf_counter();end=start+duration
        async def worker() -> None:
            nonlocal errors,counter
            while time.perf_counter()<end:
                counter+=1
                identifier=10000+counter if cache=='cold' else 1042
                began=time.perf_counter()
                try:
                    async with client.get(url+f'/orders/{identifier}') as response:
                        await response.read()
                        errors+=response.status!=200
                except (aiohttp.ClientError,asyncio.TimeoutError):
                    errors+=1
                latencies.append((time.perf_counter()-began)*1000)
        await asyncio.gather(*(worker() for _ in range(concurrency)))
        elapsed=time.perf_counter()-start
    return dict(requests=len(latencies),errors=errors,error_rate=errors/len(latencies) if latencies else 0,
        p50_ms=percentile(latencies,.5),p95_ms=percentile(latencies,.95),p99_ms=percentile(latencies,.99),
        elapsed_sec=elapsed,throughput_rps=len(latencies)/elapsed)


async def scenario(directory: Path, phase: int, concurrency: int, cache: str, args: argparse.Namespace) -> dict:
    os.environ.update(BLADE_PHASE2_ENABLED=str(phase==2).lower(),BLADE_REDIS_URL=args.redis_url,
        BLADE_REDIS_ENABLED='true',BLADE_RAG_ENABLED='false',BLADE_REANALYSIS_ENABLED='false',
        BLADE_JWT_SECRET='phase2-load-test-local-secret-at-least-32-bytes',BLADE_POLICY_POLL_SEC='60',BLADE_CACHE_TTL='60',
        BLADE_DB_DSN='sqlite:///'+str((directory/'demo.db').resolve()))
    api=admin_app(directory/f'blade-{phase}-{concurrency}-{cache}.db',directory/'policies',directory/'logs.jsonl')
    processes = getattr(args, 'process_isolation', False)
    backend_context = service_process('backend', directory/'demo.db') if processes else serve(demo_app(directory/'demo.db'))
    admin_context = service_process('admin', api.state.store.db_path) if processes else serve(api)
    async with backend_context as target,admin_context as admin:
        with closing(sqlite3.connect(directory/'demo.db')) as conn:
            with conn:
                conn.executemany('INSERT OR IGNORE INTO orders(id,user_id) VALUES (?,?)',((i,'user_77') for i in range(10000,260001)))
        p=Policy(id='pol_orders_get_by_orderId',endpoint=dict(method='GET',path='/orders/{orderId}'),label='owner_match',
            params=dict(object_param='orderId',owner_lookup=dict(table='orders',id_col='id',owner_col='user_id')),
            confidence=1,evidence='Benchmark fixture',status='ACTIVE',mode='observe',created_at=datetime.now(timezone.utc))
        api.state.store.insert_many([p])
        os.environ.update(BLADE_TARGET_URL=target,BLADE_ADMIN_URL=admin)
        token=jwt.encode(dict(sub='user_77',roles=['user'],tenant_id='org_1',membership='basic',exp=int(time.time())+7200),os.environ['BLADE_JWT_SECRET'],algorithm='HS256')
        async with proxy_service(directory, processes) as proxy_url:
            result=await measure(proxy_url,token,concurrency,args.duration,cache)
        if phase == 2:
            from common.redis_detections import client as delivery_client, stream_name
            remote = delivery_client()
            if remote is not None:
                try:
                    deadline = time.monotonic() + 30
                    while await remote.xlen(stream_name()):
                        if time.monotonic() > deadline:
                            raise RuntimeError('Detection stream did not drain within 30 seconds')
                        await asyncio.sleep(.05)
                finally:
                    await remote.aclose()
        with closing(sqlite3.connect(api.state.store.db_path)) as conn:
            recorded = conn.execute('SELECT COUNT(*) FROM detections').fetchone()[0]
        result.update(detections_expected=result['requests'] + int(cache == 'warm'), detections_recorded=recorded)
    return dict(phase=phase,concurrency=concurrency,cache=cache,**result)


async def main(args: argparse.Namespace) -> None:
    args.output.parent.mkdir(parents=True,exist_ok=True)
    rows=[]
    # Preserve service logs in isolated mode; temporary databases are removed.
    directory_context = tempfile.TemporaryDirectory(prefix='load-',dir=args.output.parent)
    with directory_context as directory:
        for concurrency in args.concurrency:
            for cache in ('cold','warm'):
                for phase in (1,2):
                    row=await scenario(Path(directory),phase,concurrency,cache,args)
                    rows.append(row);print(json.dumps(row),flush=True)
                    args.output.write_text(json.dumps(dict(duration_sec=args.duration,redis_url=args.redis_url,
                        process_isolation=args.process_isolation,results=rows),indent=2),encoding='utf-8')
        if args.process_isolation:
            import shutil
            logs = args.output.with_suffix('')
            logs.mkdir(exist_ok=True)
            for path in Path(directory).glob('*.log'):
                shutil.copy2(path, logs/path.name)
    write_report(rows,args.output,processes=args.process_isolation)


def write_report(rows: list[dict],output: Path, *, processes: bool = False) -> None:
    topology = 'Separate client/proxy/admin/backend processes on the same host' if processes else 'Same-process local HTTP regression guard'
    lines=['# Phase 1 / Phase 2 load comparison','',topology + '; not production capacity. Cold uses unique existing rows; warm primes order 1042. Phase 2 Redis on, Phase 1 Redis off. No LLM worker runs.','',
        '| Phase | Concurrency | Cache | Requests | p50 ms | p95 ms | p99 ms | Errors |','|---|---|---|---|---|---|---|---|']
    for r in rows:lines.append(f'| {r["phase"]} | {r["concurrency"]} | {r["cache"]} | {r["requests"]} | {r["p50_ms"]:.2f} | {r["p95_ms"]:.2f} | {r["p99_ms"]:.2f} | {r["errors"]} ({r["error_rate"]:.2%}) |')
    lines+=['','| Concurrency | Cache | Phase 2 p95 minus Phase 1 ms | +5 ms guard |','|---|---|---|---|']
    for base,enhanced in zip(rows[::2],rows[1::2]):
        delta=enhanced['p95_ms']-base['p95_ms']
        lines.append(f'| {base["concurrency"]} | {base["cache"]} | {delta:+.2f} | {"FAIL" if delta>5 else "PASS"} |')
    if all('detections_expected' in r for r in rows):
        lines += ['', '| Phase | Concurrency | Cache | Expected detections | Stored detections |', '|---|---|---|---|---|']
        lines += [f'| {r["phase"]} | {r["concurrency"]} | {r["cache"]} | {r["detections_expected"]} | {r["detections_recorded"]} |' for r in rows]
    output.with_suffix('.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duration',type=float,default=30)
    parser.add_argument('--process-isolation', action='store_true')
    parser.add_argument('--concurrency',type=int,nargs='+',default=[50,100,200])
    parser.add_argument('--redis-url',default='redis://127.0.0.1:16379/8')
    parser.add_argument('--output',type=Path,default=Path('verification/phase2/load-results.json'))
    args=parser.parse_args()
    if args.duration<=0 or any(n<=0 for n in args.concurrency):parser.error('duration/concurrency must be positive')
    asyncio.run(main(args))
