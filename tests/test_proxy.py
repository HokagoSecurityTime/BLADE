import asyncio
import time
from pathlib import Path
import sqlite3
import jwt
import pytest
from common.schema import Policy, JWTClaims
from proxy.jwt_auth import authenticate
from proxy.router import Router
from proxy.lookup import Lookup
from proxy.evaluator import evaluate
from proxy.server import create_app
from aiohttp import web, ClientSession
from aiohttp.test_utils import TestServer

SECRET = 'test-secret-at-least-thirty-two-bytes'


def policy(label: str = 'owner_match') -> Policy:
    return Policy.model_validate(dict(id='pol_orders_get_by_orderId', endpoint=dict(method='GET', path='/orders/{orderId}'),
        label=label, params=dict(object_param='orderId', owner_lookup=dict(table='orders', id_col='id', owner_col='user_id', tenant_col='org_id'),
                                roles=['admin'], allowed_membership=['premium']),
        confidence=1, evidence='test', status='ACTIVE', created_at='2026-09-09T00:00:00Z'))


def claims(sub: str = 'user_77', **updates: object) -> JWTClaims:
    return JWTClaims.model_validate(dict(sub=sub, roles=['user'], tenant_id='org_1', membership='basic', exp=int(time.time())+3600) | updates)


def test_jwt() -> None:
    token = jwt.encode(claims().model_dump(), SECRET, algorithm='HS256')
    assert authenticate('Bearer '+token, SECRET).sub == 'user_77'
    for header in (None, 'Bearer bad', 'Bearer '+jwt.encode(claims(exp=1).model_dump(), SECRET, algorithm='HS256'),
                   'Bearer '+jwt.encode(claims().model_dump(), 'different-secret-at-least-32-bytes', algorithm='HS256')):
        assert authenticate(header, SECRET) is None


def test_router() -> None:
    p = policy()
    router = Router([p])
    assert router.match('GET', '/orders/1042')[1] == {'orderId':'1042'}
    assert router.match('HEAD', '/orders/1042')
    assert router.match('DELETE', '/orders/1042') is None
    assert Router([p.model_copy(update={'status':'PENDING'})]).match('GET','/orders/1042') is None
    with pytest.raises(ValueError):
        Router([p,p])


@pytest.mark.parametrize('label,user,expected', [
    ('public', None, 'PASS'), ('manual_review_required', None, 'BLOCK'),
    ('owner_match', claims(), 'PASS'), ('owner_match', claims('user_99'), 'BLOCK'),
    ('owner_match', None, 'BLOCK'), ('tenant_match', claims(), 'PASS'),
    ('tenant_match', claims(tenant_id='org_2'), 'BLOCK'),
    ('owner_or_admin', claims('admin_1', roles=['admin']), 'PASS'),
    ('role_required', claims(), 'BLOCK'), ('role_required', claims(roles=['admin']), 'PASS'),
    ('membership_required', claims(), 'BLOCK'), ('membership_required', claims(membership='premium'), 'PASS'),
])
def test_evaluate(tmp_path: Path, label: str, user: JWTClaims | None, expected: str) -> None:
    db = tmp_path/'demo.db'
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE orders(id INTEGER, user_id TEXT, org_id TEXT)')
        conn.execute("INSERT INTO orders VALUES(1042,'user_77','org_1')")
    decision = asyncio.run(evaluate(policy(label), user, {'orderId': '1042'}, {}, lookup=Lookup('sqlite:///'+str(db))))
    assert decision.verdict == expected


@pytest.mark.parametrize('mode', ['open','closed'])
def test_proxy_http(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    db=tmp_path/'demo.db'
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE orders(id INTEGER, user_id TEXT, org_id TEXT)')
        conn.execute("INSERT INTO orders VALUES(1042,'user_77','org_1')")
    monkeypatch.setenv('BLADE_JWT_SECRET',SECRET)
    monkeypatch.setenv('BLADE_DB_DSN','sqlite:///'+str(db))
    monkeypatch.setenv('BLADE_FAIL_MODE',mode)
    received=[]

    async def scenario() -> None:
        async def upstream_handler(request: web.Request) -> web.Response:
            return web.json_response({'path':request.path,'query':request.query_string})
        async def policies_handler(request: web.Request) -> web.Response:
            return web.json_response([policy().model_dump(mode='json')])
        async def detection_handler(request: web.Request) -> web.Response:
            received.append(await request.json())
            return web.json_response({})
        target=web.Application()
        target.router.add_route('*','/{path:.*}',upstream_handler)
        admin=web.Application()
        admin.router.add_get('/policies',policies_handler)
        admin.router.add_post('/detections',detection_handler)
        async with TestServer(target) as target_server, TestServer(admin) as admin_server:
            monkeypatch.setenv('BLADE_TARGET_URL',str(target_server.make_url('/')).rstrip('/'))
            monkeypatch.setenv('BLADE_ADMIN_URL',str(admin_server.make_url('/')).rstrip('/'))
            async with TestServer(create_app()) as proxy, ClientSession() as client:
                url=str(proxy.make_url('/orders/1042'))
                for user,status in [('user_77',200),('user_99',403)]:
                    token=jwt.encode(claims(user).model_dump(),SECRET,algorithm='HS256')
                    async with client.get(url,headers={'Authorization':'Bearer '+token}) as response:
                        assert response.status==status
                async with client.get(url) as response:
                    assert response.status==403
                async with client.get(proxy.make_url('/unknown?a=1')) as response:
                    assert response.status==200
                    if mode=='open':
                        assert (await response.json())['query']=='a=1'
        assert any(row['sub']=='user_99' and row['verdict']=='BLOCK' for row in received)
    asyncio.run(scenario())
