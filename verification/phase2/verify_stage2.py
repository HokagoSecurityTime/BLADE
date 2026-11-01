"""Real Redis container kill/recovery, isolated demo/admin/proxy HTTP stack."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from aiohttp.test_utils import TestServer
import httpx
import jwt
import redis

from admin_api.main import create_app as admin_app
from demo_backend.main import create_app as demo_app
from proxy.server import create_app as proxy_app
from common.schema import PolicyStatus
from tests.test_e2e import serve
from tests.test_proxy import policy, claims, SECRET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'verification/phase2'
DOCKER = ['docker', 'compose', '-p', 'blade-phase2-redis', '-f', 'docker-compose.yml',
          '-f', 'docker-compose.phase2.yml', '-f', 'verification/phase2/redis-host.yml']


async def main() -> None:
    os.environ.update(BLADE_PHASE2_ENABLED='true', BLADE_REDIS_URL='redis://127.0.0.1:16379/0',
                      BLADE_JWT_SECRET=SECRET, BLADE_POLICY_POLL_SEC='3')
    remote = redis.Redis.from_url(os.environ['BLADE_REDIS_URL'], socket_timeout=.5, socket_connect_timeout=.5)
    assert await asyncio.to_thread(remote.ping)
    transcript: list[str] = []
    results: list[dict] = []

    async def docker(action: str) -> None:
        result = await asyncio.to_thread(subprocess.run, DOCKER + [action, 'redis'], cwd=ROOT,
                                         capture_output=True, text=True, timeout=30)
        transcript.append(f'$ docker compose ... {action} redis\n{result.stdout}\n{result.stderr}')
        result.check_returncode()

    try:
        with tempfile.TemporaryDirectory(prefix='stage2-', dir=OUT) as directory:
            work = Path(directory)
            os.environ['BLADE_DB_DSN'] = 'sqlite:///' + str(work/'demo.db')
            api = admin_app(work/'blade.db', work/'policies', work/'logs.jsonl')
            async with serve(demo_app(work/'demo.db')) as target, serve(api) as admin, httpx.AsyncClient(timeout=10) as client:
                p = policy()
                p.status = PolicyStatus.PENDING
                p.params.owner_lookup.tenant_col = None
                api.state.store.insert_many([p])
                os.environ.update(BLADE_TARGET_URL=target, BLADE_ADMIN_URL=admin)
                token = jwt.encode(claims('user_99').model_dump(), SECRET, algorithm='HS256')

                async def request(method: str, url: str, **kwargs: object) -> httpx.Response:
                    response = await client.request(method, url, **kwargs)
                    transcript.append(f'{method} {url}\n{response.request.headers}\n{response.request.content.decode()}\n'
                                      f'HTTP {response.status_code}\n{response.headers}\n{response.text}\n')
                    return response

                await request('POST', admin+'/policies/'+p.id+'/approve')
                async with TestServer(proxy_app()) as proxy:
                    url = str(proxy.make_url('/orders/1042'))
                    async def check(status: int, deadline_sec: float = 1, matched: bool | None = None) -> httpx.Response:
                        deadline = time.monotonic() + deadline_sec
                        while True:
                            response = await request('GET', url, headers={'Authorization': 'Bearer '+token})
                            match_ok = matched is None or bool(response.headers.get('X-Blade-Policy')) == matched
                            if response.status_code == status and match_ok:
                                return response
                            assert time.monotonic() < deadline, (status, response.status_code)
                            await asyncio.sleep(.03)

                    deadline = time.monotonic() + 5
                    while not (await asyncio.to_thread(remote.pubsub_numsub, 'blade:policy'))[0][1]:
                        assert time.monotonic() < deadline
                        await asyncio.sleep(.05)
                    await check(200)
                    start = time.monotonic()
                    await request('POST', admin+'/policies/'+p.id+'/mode', json={'mode': 'enforce'})
                    await check(403)
                    elapsed = time.monotonic()-start
                    assert elapsed < 1, 'Notification should arrive well before 3s polling'
                    results.append(dict(case='Redis pub/sub enforce update', passed=True, elapsed_sec=elapsed))
                    await request('POST', admin+'/policies/'+p.id+'/rollback')
                    await check(200, matched=False)
                    approved = await request('POST', admin+'/policies/'+p.id+'/approve')
                    assert approved.json()['mode'] == 'observe'
                    await check(200, matched=True)
                    results.append(dict(case='Redis pub/sub rollback and approval', passed=True))
                    await request('POST', admin+'/policies/'+p.id+'/mode', json={'mode': 'observe'})
                    await check(200)
                    await docker('kill')
                    response = await check(200)
                    identifier = response.headers['X-Blade-Request-Id']
                    for _ in range(100):
                        logs = (await request('GET', admin+'/detections')).json()
                        row = next((r for r in logs if r['request_id'] == identifier), None)
                        if row:
                            assert row['verdict'] == 'OBSERVE' and row['would_block'] is True
                            break
                        await asyncio.sleep(.03)
                    else:
                        raise AssertionError('Missing detection after Redis kill')
                    results.append(dict(case='Redis killed: memory fallback', status=200, verdict=row['verdict'],
                                        would_block=row['would_block'], passed=True))
                    await request('POST', admin+'/policies/'+p.id+'/mode', json={'mode': 'enforce'})
                    await check(403, 7)
                    results.append(dict(case='Redis killed: admin polling fallback', status=403, passed=True))
                    await docker('start')
                    await asyncio.sleep(1)
                    await request('POST', admin+'/policies/'+p.id+'/mode', json={'mode': 'observe'})
                    await check(200, 7)
                    assert await asyncio.to_thread(remote.ping)
                    results.append(dict(case='Redis restarted: requests recover', status=200, passed=True))
    finally:
        await docker('start')
        remote.close()
        (OUT/'stage2-http.txt').write_text('\n'.join(transcript), encoding='utf-8')
        (OUT/'stage2-live-result.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    for result in results:
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    asyncio.run(main())
