import asyncio
import json
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest

from admin_api.main import create_app
from common.schema import policy_from_yaml
from common.schema import Policy
from pipeline import classifier, generator
from pipeline.classifier.schema import manual_review
from pipeline.parsers.oas import parse_oas

ROOT = Path(__file__).resolve().parents[1]


def uploads() -> dict[str, tuple[str, bytes, str]]:
    return {'oas': ('openapi.json', (ROOT / 'demo_backend/openapi.json').read_bytes(), 'application/json'),
            'erd': ('schema.sql', (ROOT / 'demo_backend/schema.sql').read_bytes(), 'text/plain')}


def test_generation_and_lifecycle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    completion = Mock(return_value=manual_review('Mock classification'))
    monkeypatch.setattr(classifier, 'classify', completion)
    app = create_app(tmp_path / 'blade.db', tmp_path / 'policies', tmp_path / 'detections.jsonl')

    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                files = uploads()
                files['controller'] = ('main.py', b'# test controller', 'text/plain')
                response = await client.post('/generate', files=files)
                assert response.status_code == 200, response.text
                policies = response.json()
                assert len(policies) == 7 and all(p['status'] == 'PENDING' for p in policies)
                assert len(list((tmp_path / 'policies').glob('*.yaml'))) == 7
                assert [call.args[0].path for call in completion.call_args_list] == [
                    e.path for e in parse_oas(files['oas'][1].decode())]
                assert all(call.args[2] == '# test controller' for call in completion.call_args_list)
                assert (await client.post('/generate', files=files)).status_code == 409
                assert completion.call_count == 7
                assert len((await client.get('/policies', params={'status': 'PENDING'})).json()) == 7
                policy = policies[0]
                url = '/policies/' + policy['id']
                assert (await client.get(url)).json() == policy
                assert (await client.post(url + '/rollback')).status_code == 409
                assert (await client.post(url + '/approve')).json()['status'] == 'ACTIVE'
                assert (await client.post(url + '/approve')).status_code == 409
                assert (await client.post(url + '/reject')).status_code == 409
                edited = {k: v for k, v in policy.items() if k != 'status'}
                edited['evidence'] = 'Reviewed evidence'
                result = await client.put(url, json=edited)
                assert result.status_code == 200 and result.json()['status'] == 'ACTIVE'
                assert (await client.put(url, json={**edited, 'status': 'PENDING'})).status_code == 422
                assert (await client.put(url, json={**edited, 'id': 'pol_changed'})).status_code == 409
                assert (await client.post(url + '/rollback')).json()['status'] == 'PENDING'
                assert (await client.post(url + '/reject')).json()['status'] == 'REJECTED'
                for action in ('approve', 'rollback', 'reject'):
                    assert (await client.post(url + '/' + action)).status_code == 409
                saved = policy_from_yaml((tmp_path / 'policies' / (policy['id'] + '.yaml')).read_text(encoding='utf-8'))
                assert saved.status == 'REJECTED' and saved.evidence == 'Reviewed evidence'
                assert (await client.get('/policies/missing')).status_code == 404
                assert (await client.post('/policies/missing/approve')).status_code == 404
                assert (await client.get('/policies?status=INVALID')).status_code == 422
        async with app.router.lifespan_context(app):
            assert len(app.state.store.list_policies()) == 7
    asyncio.run(scenario())


def test_detection_storage(tmp_path: Path) -> None:
    app = create_app(tmp_path / 'blade.db', tmp_path / 'policies', tmp_path / 'detections.jsonl')

    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                record = dict(ts='2026-09-09T00:00:00Z', request_id='req1', sub='user_99', method='GET',
                              path='/orders/1042', policy_id='pol_orders_get_by_orderId', label='owner_match',
                              verdict='BLOCK', reason='소유자 불일치')
                for identifier in ('req1', 'req2'):
                    response = await client.post('/detections', json={**record, 'request_id': identifier})
                    assert response.status_code == 200
                assert (await client.get('/detections?limit=1')).json()[0]['request_id'] == 'req2'
                assert len((await client.get('/detections')).json()) == 2
                assert (await client.post('/detections', json={**record, 'verdict': 'BAD'})).status_code == 422
                assert (await client.get('/detections?limit=0')).status_code == 422
        rows = [json.loads(line) for line in (tmp_path / 'detections.jsonl').read_text(encoding='utf-8').splitlines()]
        assert len(rows) == 2 and rows[0]['reason'] == record['reason']
    asyncio.run(scenario())


def test_invalid_upload_and_atomic_file_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(classifier, 'classify', Mock(return_value=manual_review('Mock')))
    app = create_app(tmp_path / 'blade.db', tmp_path / 'policies', tmp_path / 'detections.jsonl')
    original = generator.save_policy
    calls = 0

    def fail_second(policy: Policy, directory: str | Path) -> Path:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError('simulated disk failure')
        return original(policy, directory)

    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url='http://test') as client:
                bad = uploads()
                bad['oas'] = ('bad.json', b'not valid', 'application/json')
                assert (await client.post('/generate', files=bad)).status_code == 422
                monkeypatch.setattr(generator, 'save_policy', fail_second)
                assert (await client.post('/generate', files=uploads())).status_code == 500
                assert (await client.get('/policies')).json() == []
                assert list((tmp_path / 'policies').glob('*.yaml')) == []
    asyncio.run(scenario())


def test_generator_ids_and_yaml(tmp_path: Path) -> None:
    endpoints = parse_oas((ROOT / 'demo_backend/openapi.json').read_text(encoding='utf-8'))
    order = next(e for e in endpoints if e.method == 'GET' and e.path == '/orders/{orderId}')
    assert generator.policy_id(order) == 'pol_orders_get_by_orderId'
    assert generator.policy_id(endpoints[0]) == 'pol_public_health_get'
    policy = generator.generate_policy(order, manual_review('Needs review'), tmp_path)
    assert policy.status == 'PENDING'
    assert policy_from_yaml((tmp_path / f'{policy.id}.yaml').read_text(encoding='utf-8')) == policy
