"""Nine-step isolated Phase 2 integration using real LLM/embeddings/Redis.

Real Slack is intentionally deferred; Slack-format payloads go to a local HTTP
receiver. --manual-fixture explicitly seeds a v1 manual-review policy if the
generated users policy is already classified, to exercise the requested queue.
Original /generate output and the fixture operation are both recorded.
"""
import argparse
import asyncio
from contextlib import AsyncExitStack
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from urllib.parse import urlparse

from aiohttp import ClientSession, ClientTimeout, web
from aiohttp.test_utils import TestServer
import httpx
import jwt

from admin_api.main import create_app
from admin_api.workers.__main__ import detection_worker
from admin_api.workers.reanalysis import run as reanalysis_worker
from common.labels import Label
from common.schema import PolicyParams, policy_to_yaml
from demo_backend.main import create_app as demo_app
from pipeline.classifier import llm
from proxy.server import create_app as proxy_app
from scripts.load_test import serve

ROOT=Path(__file__).resolve().parents[1]
SECRET='phase2-isolated-integration-secret-at-least-32-bytes'


async def run(args: argparse.Namespace) -> list[dict]:
    docker=shutil.which('docker') or str(Path(os.getenv('ProgramFiles','C:/Program Files'))/'Docker/Docker/resources/bin/docker.exe')
    inspected=await asyncio.to_thread(subprocess.run,[docker,'inspect',args.redis_container],capture_output=True,text=True,check=True)
    container=json.loads(inspected.stdout)[0]
    if container['Config'].get('Labels',{}).get('blade.verification')!='phase2-e2e':
        raise ValueError('Redis must have label blade.verification=phase2-e2e')
    endpoint=urlparse(args.redis_url)
    bindings=container['NetworkSettings']['Ports'].get('6379/tcp') or []
    if endpoint.hostname not in {'localhost','127.0.0.1'} or not any(
        b['HostIp']=='127.0.0.1' and int(b['HostPort'])==endpoint.port for b in bindings
    ):
        raise ValueError('Redis URL must match the dedicated container loopback port')
    container_id=container['Id']
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if (out/'blade.db').exists():
        raise ValueError('Use a new --output directory; existing verification DBs are never deleted')
    os.environ.update(BLADE_PHASE2_ENABLED='true',BLADE_MODE_ENABLED='true',BLADE_CONTROLLER_ENABLED='true',
        BLADE_RAG_ENABLED='true',BLADE_RAG_KINDS='code,idiom',BLADE_CHROMA_PATH=str(out/'chroma'),
        BLADE_MODEL_CACHE=str(ROOT/'.cache/models'),BLADE_REDIS_URL=args.redis_url,BLADE_REDIS_ENABLED='true',
        BLADE_ALERTS_ENABLED='true',BLADE_EXPLAIN_ENABLED='true',BLADE_REANALYSIS_ENABLED='true',
        BLADE_LLM_PROVIDER=args.provider,BLADE_LLM_MODEL=args.model,BLADE_JWT_SECRET=SECRET,
        BLADE_DB_DSN='sqlite:///'+str(out/'demo.db'),BLADE_POLICY_POLL_SEC='.2',BLADE_REANALYSIS_POLL_SEC='.5')
    import redis
    assert await asyncio.to_thread(redis.Redis.from_url(args.redis_url).ping)
    api=create_app(out/'blade.db',out/'policies',out/'detections.jsonl')
    received=[];results=[];step=1;tasks=[];redis_stopped=False
    real_complete=llm.complete;completions=[]
    def capture(system: str,user: str,**kwargs) -> str:
        started=time.monotonic()
        try:
            answer=real_complete(system,user,**kwargs)
            completions.append(dict(system=system,user=user,response=answer,elapsed_sec=time.monotonic()-started))
            return answer
        finally:
            (out/'llm.json').write_text(json.dumps(completions,ensure_ascii=False,indent=2),encoding='utf-8')
    llm.complete=capture
    def report(status: str,description: str,**extra) -> None:
        results.append(dict(step=step,status=status,description=description,**extra))
        (out/'results.json').write_text(json.dumps(dict(provider=args.provider,model=args.model,rag='code,idiom',
            slack='local HTTP only; external channel deferred by user',results=results),ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'STEP {step}: {status} {description}',flush=True)
    async def hook(request: web.Request) -> web.Response:
        received.append(dict(ts=time.time(),body=await request.json()))
        (out/'webhooks.json').write_text(json.dumps(received,ensure_ascii=False,indent=2),encoding='utf-8')
        return web.Response(text='ok')
    hooks=web.Application();hooks.router.add_post('/slack',hook)
    docker=shutil.which('docker') or str(Path(os.getenv('ProgramFiles','C:/Program Files'))/'Docker/Docker/resources/bin/docker.exe')
    async def redis_command(action: str) -> None:
        result=await asyncio.to_thread(subprocess.run,[docker,action,container_id],capture_output=True,text=True,check=True)
        with (out/'redis.txt').open('a',encoding='utf-8') as file:file.write(action+' '+args.redis_container+'\n'+result.stdout+result.stderr)
    async with AsyncExitStack() as stack:
        admin=await stack.enter_async_context(serve(api));target=await stack.enter_async_context(serve(demo_app(out/'demo.db')))
        webhook=await stack.enter_async_context(TestServer(hooks))
        client=await stack.enter_async_context(httpx.AsyncClient(timeout=httpx.Timeout(1800,connect=10)))
        control=await stack.enter_async_context(ClientSession(timeout=ClientTimeout(total=5)))
        os.environ.update(BLADE_TARGET_URL=target,BLADE_ADMIN_URL=admin)
        async def request(method: str,url: str,**kwargs) -> httpx.Response:
            req=client.build_request(method,url,**kwargs);body=await req.aread();res=await client.send(req)
            with (out/f'step{step}.txt').open('a',encoding='utf-8') as file:
                file.write(f'{req.method} {req.url}\n'+json.dumps(list(req.headers.multi_items()))+'\n\n'+body.decode('utf-8',errors='replace')+
                    f'\n\nHTTP {res.status_code}\n'+json.dumps(list(res.headers.multi_items()))+'\n\n'+res.text+'\n\n')
            return res
        async def post(path: str,data: dict | None=None) -> dict:
            res=await request('POST',admin+path,json=data);res.raise_for_status();return res.json()
        async def wait_for(check,timeout: float=30):
            deadline=time.monotonic()+timeout
            while time.monotonic()<deadline:
                value=await check()
                if value:return value
                await asyncio.sleep(.3)
            raise AssertionError('Timed out waiting for '+check.__name__)
        async def detection(identifier: str,explained: bool=False):
            res=await request('GET',admin+'/detections?limit=100')
            return next((r for r in res.json() if r['request_id']==identifier and (not explained or r['explanation'])),None)
        def token(sub: str) -> str:
            return jwt.encode(dict(sub=sub,roles=['user'],tenant_id='org_2',membership='basic',exp=int(time.time())+7200),SECRET,algorithm='HS256')
        try:
            print('STEP 1: real /generate with seven sequential LLM calls',flush=True)
            files={name:(Path(path).name,(ROOT/path).read_bytes()) for name,path in {
                'oas':'demo_backend/openapi.json','erd':'demo_backend/schema.sql','controller':'tests/fixtures/controllers/demo_with_admin.py'}.items()}
            res=await request('POST',admin+'/generate',files=files);res.raise_for_status();policies=res.json()
            (out/'generated-policies.json').write_text(json.dumps(policies,ensure_ascii=False,indent=2),encoding='utf-8')
            assert len(policies)==7 and all(p['status']=='PENDING' for p in policies)
            report('PASS','7 PENDING policies generated with real LLM/RAG/controller')
            users=next(p for p in policies if p['endpoint']['path']=='/users/{userId}')
            orders=next(p for p in policies if p['endpoint']==dict(method='GET',path='/orders/{orderId}'))
            if users['label']!='manual_review_required' and args.manual_fixture:
                original=api.state.store.get(users['id'])
                fixture=original.model_copy(update={'label':Label.MANUAL_REVIEW_REQUIRED,'params':PolicyParams(),
                    'confidence':.5,'evidence':'Explicit v1 manual-review integration fixture; original generated result retained in generated-policies.json'})
                with api.state.store.connection(write=True) as conn:
                    conn.execute('UPDATE policies SET yaml_text=? WHERE id=?',(policy_to_yaml(fixture),fixture.id))
                api.state.store._mirror(fixture,{})
                (out/'manual-fixture.md').write_text(f'# Explicit queue fixture\n\nGenerated users label: {users["label"]}. Seeded manual_review_required v1 before approval solely to exercise steps 5/6. This is not an LLM output. Generation context retained.\n',encoding='utf-8')
            step=2
            for policy in policies:assert (await post('/policies/'+policy['id']+'/approve'))['mode']=='observe'
            res=await request('GET',admin+'/policies?status=ACTIVE');assert len(res.json())==7
            report('PASS','7 ACTIVE policies, all observe')
            api.state.store.save_alert_settings(dict(slack_webhook=str(webhook.make_url('/slack')),discord_webhook='',min_severity='observe'))
            for kind in ('alerts','explain'):
                api.state.store.worker_batch(kind);tasks.append(asyncio.create_task(detection_worker(api.state.store,kind,control)))
            proxy=await stack.enter_async_context(TestServer(proxy_app()));proxy_url=str(proxy.make_url('/')).rstrip('/')
            async def order_request(expected: int) -> dict:
                response=await request('GET',proxy_url+'/orders/1042',headers={'Authorization':'Bearer '+token('user_99')})
                assert response.status_code==expected, f'orders HTTP {response.status_code}, expected {expected}'
                return await wait_for(lambda:detection(response.headers['X-Blade-Request-Id']))
            step=3;row=await order_request(200)
            assert row['verdict']=='OBSERVE' and row['would_block']
            report('PASS','200 + OBSERVE + would_block=true')
            async def observe_alert():return next((r for r in received if '[BLADE observe]' in r['body'].get('text','')),None)
            await wait_for(observe_alert)
            # Same (sub,policy) notification suppression is intentionally 60 s.
            print('Waiting 61 s for the documented alert dedup window',flush=True);await asyncio.sleep(61)
            step=4;await post('/policies/'+orders['id']+'/mode',dict(mode='enforce'));await asyncio.sleep(.6)
            row=await order_request(403)
            async def enforce_alert():return next((r for r in received if '[BLADE enforce]' in r['body'].get('text','')),None)
            await wait_for(enforce_alert)
            row=await wait_for(lambda:detection(row['request_id'],True),timeout=400)
            report('PASS','403 + local Slack-format webhook + real LLM explanation',explanation=row['explanation'],external_slack='DEFERRED')
            step=5
            assert api.state.store.get(users['id']).label=='manual_review_required','Use --manual-fixture when /generate already classifies users'
            os.environ['BLADE_REANALYSIS_ENABLED']='true';tasks.append(asyncio.create_task(reanalysis_worker(api.state.store)))
            for _ in range(20):
                response=await request('GET',proxy_url+'/users/user_77',headers={'Authorization':'Bearer '+token('user_99')});assert response.status_code==200
            async def proposal():
                response=await request('GET',admin+'/policies/'+users['id']+'/proposals')
                return next((p for p in response.json() if p['status']=='PENDING'),None)
            proposed=await wait_for(proposal,timeout=480)
            from common.schema import policy_from_yaml
            assert policy_from_yaml(proposed['proposed_yaml']).label=='owner_or_admin'
            report('PASS','20 OBSERVE requests -> real LLM owner_or_admin proposal')
            step=6;accepted=await post('/proposals/'+str(proposed['id'])+'/accept')
            assert accepted['version']==2 and accepted['label']=='owner_or_admin' and accepted['mode']=='observe'
            report('PASS','Proposal accepted via API: v2 / owner_or_admin / observe')
            step=7;await post('/policies/'+users['id']+'/rollback')
            # Trigger dispatch is verified by a new rollback proposal; no auto-apply.
            proposed=await wait_for(proposal,timeout=480);assert proposed['reason']=='rollback'
            report('PASS','Rollback triggered a separate review proposal')
            step=8
            await order_request(403);await asyncio.sleep(1.5)
            res=await request('GET',admin+'/metrics/observability');assert res.json()['rate']>0
            report('PASS','observability rate > 0',metrics=res.json())
            step=9
            await post('/policies/'+orders['id']+'/mode',dict(mode='observe'));await asyncio.sleep(.6)
            redis_stopped=True;await redis_command('stop')
            await asyncio.sleep(1);row=await order_request(200)
            assert row['verdict']=='OBSERVE' and row['would_block']
            report('PASS','Redis stopped: still 200 + OBSERVE + would_block')
        except Exception as exc:
            report('FAIL',str(exc))
            raise
        finally:
            if redis_stopped:
                await redis_command('start')
                recovery=redis.Redis.from_url(args.redis_url,socket_connect_timeout=2,socket_timeout=2)
                try:
                    for attempt in range(30):
                        try:
                            if await asyncio.to_thread(recovery.ping):break
                        except redis.RedisError:
                            pass
                        await asyncio.sleep(.5)
                    else:raise AssertionError('Dedicated Redis did not recover')
                    (out/'redis.txt').open('a',encoding='utf-8').write('Recovery PING: PONG\n')
                finally:
                    recovery.close()
            for task in tasks:task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
            llm.complete=real_complete
            lines=['# Phase 2 integration','','Real LLM/E5/Chroma/HTTP/SQLite/Redis. Local webhook receiver; external Slack deferred.','',
                '| Step | Result | Evidence |','|---|---|---|']+[f'| {r["step"]} | {r["status"]} | {r["description"]} |' for r in results]
            if (out/'manual-fixture.md').exists():lines+=['','Steps 5/6 use an explicitly seeded manual-review v1 fixture; original generated policy is preserved in generated-policies.json.']
            (out/'SUMMARY.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider',default='ollama');parser.add_argument('--model',default='qwen2.5:7b')
    parser.add_argument('--redis-url',required=True)
    parser.add_argument('--redis-container',required=True)
    parser.add_argument('--manual-fixture',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'verification/phase2'/('e2e-'+datetime.now().strftime('%Y%m%d-%H%M%S')))
    asyncio.run(run(parser.parse_args()))
