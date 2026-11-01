import asyncio
import json
from unittest.mock import Mock

from aiohttp import ClientSession
import pytest

from admin_api.main import create_app
from admin_api.workers.explain import explain
from tests.test_alerts import record
from tests.test_e2e import serve


@pytest.mark.parametrize('observe', [False, True])
def test_contradictory_llm_outcome_is_not_stored(tmp_path, monkeypatch, observe):
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    text = '차단되었습니다. 실제 차단이 아닙니다.'
    complete = Mock(return_value=json.dumps({'explanation': text}))
    monkeypatch.setattr('pipeline.classifier.llm.complete', complete)
    row = record('OBSERVE' if observe else 'BLOCK').model_copy(update={
        'mode': 'observe' if observe else 'enforce', 'would_block': observe})
    app = create_app(tmp_path/'db', tmp_path/'policies', tmp_path/'log')

    async def run():
        async with serve(app) as url, ClientSession() as session:
            app.state.store.append_detection(row)
            result = await explain(row, session, url)
            assert result != text
            assert ('차단하지 않았습니다' if observe else '요청을 차단했습니다') in result
            assert app.state.store.list_detections(1)[0].explanation == result
    asyncio.run(run())
