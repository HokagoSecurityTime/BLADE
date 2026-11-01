import asyncio
from pathlib import Path
from unittest.mock import Mock

from aiohttp import ClientSession
import pytest

from admin_api.main import create_app
from admin_api.workers.explain import explain, masked_input
from pipeline.classifier import llm
from tests.test_alerts import record
from tests.test_e2e import serve


def test_explanation_async_api_and_off(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    complete = Mock(return_value='{"explanation":"타인의 주문에 대한 접근이 차단되었습니다."}')
    monkeypatch.setattr(llm, 'complete', complete)
    app = create_app(tmp_path/'blade.db', tmp_path/'policies', tmp_path/'detections.jsonl')
    async def scenario() -> None:
        async with serve(app) as url, ClientSession() as session:
            app.state.store.append_detection(record())
            assert await explain(record(), session, url)
            assert app.state.store.list_detections(1)[0].explanation == '타인의 주문에 대한 접근이 차단되었습니다.'
            monkeypatch.setenv('BLADE_EXPLAIN_ENABLED', 'false')
            assert await explain(record(), session, url) is None
    asyncio.run(scenario())
    assert complete.call_count == 1
    masked = masked_input(record().model_copy(update={'path': '/orders/1042?email=secret@example.org', 'reason': 'password=secret'}))
    assert masked['path'] == '/orders/1042' and masked['sub'] == 'user_99'
    assert 'secret' not in str(masked)
