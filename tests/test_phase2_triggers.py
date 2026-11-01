import asyncio
from pathlib import Path
from unittest.mock import Mock

from aiohttp import ClientSession
from aiohttp.test_utils import TestServer
import jwt
import pytest

from admin_api.workers.reanalysis import run_once
from admin_api.proposals import Proposals
from pipeline.classifier.schema import ClassificationResult
from demo_backend.main import create_app as demo_app
from proxy.server import create_app as proxy_app
from scripts.load_test import serve
from tests.test_proxy import claims, SECRET
from tests.test_reanalysis import setup


def test_proxy_would_block_and_admin_rollback_reach_worker(setup,tmp_path: Path,monkeypatch: pytest.MonkeyPatch) -> None:
    store,client,p=setup
    data=p.model_dump();data.update(label='owner_match',params=dict(object_param='orderId',owner_lookup=dict(table='orders',id_col='id',owner_col='user_id'),roles=[],allowed_membership=[]))
    store.update(p.id,changes={k:v for k,v in data.items() if k!='status'})
    result=ClassificationResult(label='owner_match',confidence=.9,evidence='same policy',object_param='orderId',
        owner_lookup=dict(table='orders',id_col='id',owner_col='user_id'),roles=[],allowed_membership=[])
    mock=Mock(return_value=result);monkeypatch.setattr('admin_api.workers.reanalysis.classify',mock)
    monkeypatch.setenv('BLADE_JWT_SECRET',SECRET)
    monkeypatch.setenv('BLADE_DB_DSN','sqlite:///'+str(tmp_path/'demo.db'))
    monkeypatch.setenv('BLADE_POLICY_POLL_SEC','.05')
    async def scenario() -> None:
        async with serve(demo_app(tmp_path/'demo.db')) as backend,serve(client.app) as admin,ClientSession() as session:
            monkeypatch.setenv('BLADE_TARGET_URL',backend);monkeypatch.setenv('BLADE_ADMIN_URL',admin)
            async with TestServer(proxy_app()) as proxy:
                for who in ('actor_a','actor_b','actor_c'):
                    token=jwt.encode(claims(who).model_dump(),SECRET,algorithm='HS256')
                    for _ in range(5):
                        async with session.get(proxy.make_url('/orders/1042'),headers={'Authorization':'Bearer '+token}) as response:
                            assert response.status==200;await response.read()
                for _ in range(100):
                    if len(store.list_detections(100))==15:break
                    await asyncio.sleep(.02)
    asyncio.run(scenario())
    assert all(r.would_block for r in store.list_detections(100))
    proposal=run_once(store)[0]
    assert proposal['reason']=='high_would_block_ratio'
    Proposals(store).decide(proposal['id'],False)
    assert client.post('/policies/'+p.id+'/rollback').status_code==200
    assert run_once(store)[0]['reason']=='rollback'
    assert mock.call_count==2
