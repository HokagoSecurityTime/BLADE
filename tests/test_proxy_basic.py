import asyncio
import gzip
import time
import jwt
import pytest
from yarl import URL
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer
from proxy.jwt_auth import authenticate
from proxy.router import Router
from proxy.server import create_app
from tests.test_proxy import policy, SECRET, claims


def test_jwt_parsing() -> None:
    valid = jwt.encode(claims().model_dump(), SECRET, algorithm='HS256')
    assert authenticate('Bearer '+valid, SECRET).sub == 'user_77'
    for value in (None, '', 'Basic abc', 'Bearer a b', 'Bearer broken',
                  'Bearer '+jwt.encode(claims(exp=1).model_dump(),SECRET,algorithm='HS256'),
                  'Bearer '+jwt.encode(claims().model_dump(),'another-secret-at-least-32-bytes',algorithm='HS256'),
                  'Bearer '+jwt.encode(claims().model_dump(),SECRET*2,algorithm='HS512')):
        assert authenticate(value, SECRET) is None


def test_route_priority() -> None:
    template = policy()
    specific = template.model_copy(deep=True)
    specific.id='pol_orders_special_get'
    specific.endpoint.path='/orders/special'
    router=Router([template,specific])
    assert router.match('GET','/orders/special')[0].id == specific.id
    assert router.match('GET','/orders/1042')[1] == {'orderId':'1042'}
    assert router.match('POST','/orders/1042') is None


@pytest.mark.parametrize('method',['GET','POST','PUT','PATCH','DELETE','OPTIONS'])
def test_forwarding(monkeypatch: pytest.MonkeyPatch, method: str) -> None:
    monkeypatch.setenv('BLADE_JWT_SECRET', SECRET)
    monkeypatch.setenv('BLADE_FAIL_MODE','closed')
    body=b'\x00\xffraw-body\n'
    compressed=gzip.compress(b'response\x00\xff')

    async def scenario() -> None:
        async def target(request: web.Request) -> web.Response:
            assert request.method==method
            assert request.raw_path=='/orders/1042?a=1&a=2&x=%2F'
            assert await request.read()==body
            assert request.headers['X-Custom']=='keep'
            assert request.headers['Authorization']=='Bearer invalid'
            assert 'X-Hop' not in request.headers
            response=web.Response(status=202,body=compressed,headers={'Content-Encoding':'gzip','Connection':'X-Response-Hop','X-Response-Hop':'remove','X-Keep':'yes'})
            response.headers.add('Set-Cookie','one=1')
            response.headers.add('Set-Cookie','two=2')
            return response
        p=policy('public')
        p.endpoint.method=method
        async def policies(request: web.Request) -> web.Response:
            assert request.query['status']=='ACTIVE'
            return web.json_response([p.model_dump(mode='json')])
        async def logs(request: web.Request) -> web.Response:
            assert (await request.json())['verdict']=='PASS'
            return web.json_response({})
        upstream=web.Application()
        upstream.router.add_route('*','/{path:.*}',target)
        admin=web.Application()
        admin.router.add_get('/policies',policies)
        admin.router.add_post('/detections',logs)
        async with TestServer(upstream) as u, TestServer(admin) as a:
            monkeypatch.setenv('BLADE_TARGET_URL',str(u.make_url('/')).rstrip('/'))
            monkeypatch.setenv('BLADE_ADMIN_URL',str(a.make_url('/')).rstrip('/'))
            async with TestServer(create_app()) as proxy, ClientSession(auto_decompress=False) as client:
                async with client.request(method,URL(str(proxy.make_url('/orders/1042'))+'?a=1&a=2&x=%2F', encoded=True),
                    headers={'Authorization':'Bearer invalid','X-Custom':'keep','Connection':'X-Hop','X-Hop':'remove'},data=body) as response:
                    assert response.status==202
                    assert await response.read()==compressed
                    assert response.headers['X-Blade-Policy']==p.id
                    assert response.headers['X-Blade-Request-Id']
                    assert response.headers.getall('Set-Cookie')==['one=1','two=2']
                    assert 'X-Response-Hop' not in response.headers
    asyncio.run(scenario())

