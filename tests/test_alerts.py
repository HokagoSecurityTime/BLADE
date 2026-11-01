import asyncio
import logging
from pathlib import Path
import sqlite3

from aiohttp import ClientSession, ClientTimeout, web
from aiohttp.test_utils import TestServer
import pytest

from admin_api.alerts import message, notify, read_batch, save_cursor
from common.schema import DetectionLog


def record(verdict: str = 'BLOCK') -> DetectionLog:
    return DetectionLog.model_validate(dict(ts='2026-09-10T00:00:00Z',request_id='r1',sub='user_99',method='GET',
        path='/orders/1042',policy_id='pol_orders_get_by_orderId',label='owner_match',verdict=verdict,reason='policy_mismatch'))


def test_only_block_both_webhooks_and_failure(caplog: pytest.LogCaptureFixture) -> None:
    received = []
    async def scenario() -> None:
        async def endpoint(request: web.Request) -> web.Response:
            received.append((request.path, await request.json()))
            return web.Response(status=503 if request.path=='/discord' else 200)
        app = web.Application(); app.router.add_post('/{provider}', endpoint)
        async with TestServer(app) as server, ClientSession(timeout=ClientTimeout(total=1)) as session:
            for verdict in ('PASS','OBSERVE','BLOCK'):
                await notify(record(verdict),session,str(server.make_url('/slack')),str(server.make_url('/discord')))
    with caplog.at_level(logging.WARNING): asyncio.run(scenario())
    assert len(received)==2
    payloads = dict(received)
    assert payloads['/slack']['text'] == message(record())
    assert payloads['/discord']['content'] == message(record())
    assert payloads['/discord']['allowed_mentions'] == {'parse':[]}
    assert 'discord delivery failed' in caplog.text
    assert 'http://' not in caplog.text


def test_cursor_no_history_and_restart(tmp_path: Path) -> None:
    db=tmp_path/'blade.db'; checkpoint=tmp_path/'cursor'
    fields=list(record().model_dump())
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE detections (' + ','.join(f'{key} TEXT' for key in fields) + ')')
        conn.execute('INSERT INTO detections VALUES (?,?,?,?,?,?,?,?,?)',tuple(record().model_dump(mode='json').values()))
    cursor, rows=read_batch(db,None)
    assert cursor==1 and rows==[]
    save_cursor(checkpoint,cursor)
    with sqlite3.connect(db) as conn:
        data=record().model_dump(mode='json');data['request_id']='r2'
        conn.execute('INSERT INTO detections VALUES (?,?,?,?,?,?,?,?,?)',tuple(data.values()))
    _, rows=read_batch(db,int(checkpoint.read_text()))
    assert len(rows)==1 and rows[0][1].request_id=='r2'
    save_cursor(checkpoint,rows[0][0])
    assert read_batch(db,int(checkpoint.read_text()))[1]==[]
