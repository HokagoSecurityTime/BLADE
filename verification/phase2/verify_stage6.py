"""Real Ollama + E5 + Chroma reanalysis; explicitly seeded manual-review fixture."""
import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

from aiohttp import ClientSession
from aiohttp.test_utils import TestServer
import jwt

from admin_api.main import create_app
from admin_api.workers.reanalysis import run_once
from common.schema import Policy
from demo_backend.main import create_app as demo_app
from pipeline.classifier import llm
from pipeline.parsers.oas import parse_oas
from pipeline.parsers.erd import parse_erd
from proxy.server import create_app as proxy_app
from tests.test_e2e import serve
from tests.test_proxy import claims, SECRET

OUT = Path('verification/phase2')


async def main() -> None:
    os.environ.update(BLADE_PHASE2_ENABLED='true', BLADE_RAG_ENABLED='true', BLADE_RAG_KINDS='code,idiom',
        BLADE_CONTROLLER_ENABLED='true', BLADE_REDIS_ENABLED='false', BLADE_LLM_PROVIDER='ollama',
        BLADE_LLM_MODEL='qwen2.5:7b', BLADE_JWT_SECRET=SECRET, BLADE_POLICY_POLL_SEC='.1',
        BLADE_CHROMA_PATH=str((OUT/'stage6-index').resolve()), BLADE_MODEL_CACHE=str(Path('.cache/models').resolve()))
    from pipeline.rag.index import Index
    from pipeline.rag.corpus import load_code, load_idioms
    code=Path('tests/fixtures/controllers/demo_with_admin.py').read_text(encoding='utf-8')
    index=await asyncio.to_thread(Index)
    await asyncio.to_thread(index.replace,'code',load_code(code,'demo_with_admin.py'))
    await asyncio.to_thread(index.replace,'idiom',load_idioms())
    ep=next(e for e in parse_oas(Path('demo_backend/openapi.json').read_text()) if e.path=='/users/{userId}')
    tables=parse_erd(Path('demo_backend/schema.sql').read_text())
    original=llm.complete
    def capture(system: str,user: str,**kwargs) -> str:
        result=original(system,user,**kwargs)
        (OUT/'stage6-llm.json').write_text(json.dumps(dict(system=system,user=json.loads(user),response=result),ensure_ascii=False,indent=2),encoding='utf-8')
        return result
    llm.complete=capture
    transcript=[]
    with tempfile.TemporaryDirectory(dir=OUT) as directory:
        root=Path(directory);os.environ['BLADE_DB_DSN']='sqlite:///'+str((root/'demo.db').resolve())
        app=create_app(root/'blade.db',root/'policies',root/'logs.jsonl')
        async with serve(app) as admin,serve(demo_app(root/'demo.db')) as backend,ClientSession() as client:
            p=Policy(id='pol_users_get_by_userId',endpoint=dict(method='GET',path=ep.path),label='manual_review_required',params={},confidence=.5,
                evidence='Explicit manual-review setup fixture for the Phase 2 trigger test',status='PENDING',created_at=datetime.now(timezone.utc))
            app.state.store.insert_many([p],{p.id:dict(endpoint=asdict(ep),erd={k:asdict(v) for k,v in tables.items()},controller=code)})
            async def request(method: str,url: str,**kwargs) -> dict:
                async with client.request(method,url,**kwargs) as response:
                    body=await response.text();transcript.append(dict(method=method,url=url,request=kwargs,status=response.status,headers=dict(response.headers),body=body))
                    response.raise_for_status();return json.loads(body)
            await request('POST',admin+'/policies/'+p.id+'/approve')
            os.environ.update(BLADE_TARGET_URL=backend,BLADE_ADMIN_URL=admin)
            async with TestServer(proxy_app()) as proxy:
                token=jwt.encode(claims('user_99').model_dump(),SECRET,algorithm='HS256')
                for _ in range(20):
                    await request('GET',str(proxy.make_url('/users/user_77')),headers={'Authorization':'Bearer '+token})
                for _ in range(100):
                    if len(app.state.store.list_detections(100))==20:break
                    await asyncio.sleep(.05)
                records=app.state.store.list_detections(100)
                assert len(records)==20 and all(r.verdict=='OBSERVE' for r in records)
                print('20 actual proxy OBSERVE requests collected; starting real reanalysis',flush=True)
                created=await asyncio.to_thread(run_once,app.state.store)
                result=await request('GET',admin+'/policies/'+p.id+'/proposals')
                (OUT/'stage6-proposals.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
                (OUT/'stage6-http.json').write_text(json.dumps(transcript,ensure_ascii=False,indent=2),encoding='utf-8')
                from common.schema import policy_from_yaml
                actual=policy_from_yaml(created[0]['proposed_yaml']).label.value if created else None
                report=dict(observe_requests=len(records),proposal_count=len(created),label=actual,expected='owner_or_admin',
                    original_unchanged=app.state.store.get(p.id).label=='manual_review_required',passed=actual=='owner_or_admin')
                (OUT/'stage6-result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
                print(json.dumps(report),flush=True)
                assert report['passed']


if __name__=='__main__':
    asyncio.run(main())
