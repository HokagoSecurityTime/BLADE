import asyncio
from pathlib import Path
import sqlite3
from unittest.mock import Mock

from aiohttp import ClientSession
import pytest

from admin_api.main import create_app
from tests.test_alerts import record
from tests.test_e2e import serve


@pytest.mark.parametrize('batching', ['true', 'false'])
def test_all_http_acknowledgements_are_persisted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, batching: str) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    monkeypatch.setenv('BLADE_DETECTION_BATCH_ENABLED', batching)
    app = create_app(tmp_path/'db', tmp_path/'policies', tmp_path/'log')
    store = app.state.store
    commit = Mock(wraps=store.append_detections)
    monkeypatch.setattr(store, 'append_detections', commit)

    async def run() -> None:
        async with serve(app) as url, ClientSession() as session:
            async def send(index: int) -> None:
                data = record().model_copy(update={'request_id': str(index)}).model_dump(mode='json')
                async with session.post(url+'/detections', json=data) as response:
                    assert response.status == 200
                    assert (await response.json())['request_id'] == str(index)
            await asyncio.gather(*(send(i) for i in range(64)))
            assert {r.request_id for r in store.list_detections(100)} == {str(i) for i in range(64)}
        assert len((tmp_path/'log').read_text().splitlines()) == 64
    asyncio.run(run())
    if batching == 'true':
        assert any(len(call.args[0]) > 1 for call in commit.call_args_list)


def test_batch_constraint_failure_rolls_back_whole_batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    store = create_app(tmp_path/'db', tmp_path/'policies', tmp_path/'log').state.store
    store.initialize()
    store.append_detection(record())
    before = (tmp_path/'log').read_bytes()
    good = record().model_copy(update={'request_id': 'new'})
    invalid = record().model_copy(update={'verdict': 'invalid'})
    with pytest.raises(sqlite3.IntegrityError):
        store.append_detections([good, invalid])
    assert len(store.list_detections(100)) == 1
    assert (tmp_path/'log').read_bytes() == before
