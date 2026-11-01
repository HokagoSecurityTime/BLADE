"""Local HTTP webhook evidence; no Slack/Discord account is contacted."""
import asyncio
import json
import os
from pathlib import Path

from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer

from admin_api.workers.alerts import AlertWorker
from tests.test_alerts import record


async def main() -> None:
    os.environ['BLADE_PHASE2_ENABLED'] = 'true'
    received = []
    async def hook(request: web.Request) -> web.Response:
        received.append(dict(method=request.method, path=request.path, body=await request.json(), response_status=200))
        return web.Response(text='ok')
    app = web.Application(); app.router.add_post('/{provider}', hook)
    async with TestServer(app) as server, ClientSession() as client:
        settings = dict(slack_webhook=str(server.make_url('/slack')), discord_webhook=str(server.make_url('/discord')), min_severity='observe')
        worker = AlertWorker()
        assert await worker.notify(record().model_copy(update={'mode': 'enforce', 'explanation': '테스트 예시: 타인의 주문 요청이 차단되었습니다.'}), client, settings)
        assert await worker.notify(record('OBSERVE').model_copy(update={'would_block': True, 'sub': 'user_88'}), client, settings)
    Path('verification/phase2/stage5-webhooks.json').write_text(json.dumps(received, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    asyncio.run(main())
