import asyncio
from pathlib import Path

from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer
from fastapi.testclient import TestClient
import pytest

from admin_api.main import create_app
from admin_api.workers.alerts import AlertWorker, message
from tests.test_alerts import record


def test_retry_dedup_modes_and_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    received = []
    now = [0.0]
    async def scenario() -> None:
        async def hook(request: web.Request) -> web.Response:
            received.append(await request.json())
            return web.Response(status=503 if len(received) == 1 else 200)
        app = web.Application(); app.router.add_post('/', hook)
        async with TestServer(app) as server, ClientSession() as session:
            settings = dict(slack_webhook=str(server.make_url('/')), discord_webhook='', min_severity='observe')
            worker = AlertWorker(lambda: now[0])
            row = record().model_copy(update={'mode': 'enforce', 'explanation': '다른 사용자의 주문 접근이 차단되었습니다.'})
            assert await worker.notify(row, session, settings)
            assert not await worker.notify(row, session, settings)
            assert received[-1]['text'] == message(row)
            now[0] = 61
            observed = record('OBSERVE').model_copy(update={'would_block': True})
            assert await worker.notify(observed, session, settings)
            now[0] = 122
            assert not await worker.notify(observed, session, {**settings, 'min_severity': 'block'})
            monkeypatch.setenv('BLADE_ALERTS_ENABLED', 'false')
            assert not await worker.notify(row, session, settings)
    asyncio.run(scenario())
    assert len(received) == 3


def test_settings_and_persistent_cursor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    app = create_app(tmp_path/'blade.db', tmp_path/'policies', tmp_path/'detections.jsonl')
    with TestClient(app) as client:
        assert client.get('/settings/alerts').status_code == 200
        data = dict(slack_webhook='http://localhost:1234/hook', discord_webhook='', min_severity='block')
        assert client.put('/settings/alerts', json=data).json() == data
        assert client.get('/settings/alerts').json() == data
        assert client.put('/settings/alerts', json={**data, 'slack_webhook': 'file:///secret'}).status_code == 422
        store = app.state.store
        store.append_detection(record())
        assert store.worker_batch('alerts') == []  # no historical spam
        store.append_detection(record().model_copy(update={'request_id': 'new'}))
        batch = store.worker_batch('alerts')
        assert batch[0][1].request_id == 'new'
        store.checkpoint_worker('alerts', batch[0][0])
        assert store.worker_batch('alerts') == []
