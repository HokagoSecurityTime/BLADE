"""Browser smoke check against actual admin API and built UI, isolated SQLite."""
import asyncio
import json
import os
from pathlib import Path
import tempfile

from aiohttp import web
from aiohttp.test_utils import TestServer
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from playwright.async_api import async_playwright

from admin_api.main import create_app
from tests.test_e2e import serve
from tests.test_proxy import policy

OUT = Path('verification/phase2')


async def main() -> None:
    os.environ.update(BLADE_PHASE2_ENABLED='true', BLADE_REDIS_ENABLED='false')
    received = []
    async def hook(request: web.Request) -> web.Response:
        received.append(await request.json())
        return web.Response(text='ok')
    hooks = web.Application(); hooks.router.add_post('/', hook)
    with tempfile.TemporaryDirectory(dir=OUT) as directory:
        root = Path(directory)
        admin = create_app(root/'blade.db', root/'policies', root/'logs.jsonl')
        admin.state.store.initialize()
        admin.state.store.insert_many([policy()])
        app = FastAPI(); app.mount('/api', admin); app.mount('/', StaticFiles(directory=OUT/'ui-dist', html=True))
        async with serve(app) as url, TestServer(hooks) as webhook, async_playwright() as pw:
            browser = await pw.chromium.launch(channel='msedge', headless=True)
            page = await browser.new_page(viewport={'width': 1440, 'height': 1000})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            await page.goto(url)
            await page.get_by_role('button', name='알림 설정').click()
            await page.get_by_label('slack_webhook').fill(str(webhook.make_url('/')))
            await page.get_by_role('button', name='저장 후 테스트 전송').click()
            await page.get_by_text('테스트 알림이 전송되었습니다.').wait_for()
            await page.screenshot(path=str(OUT/'stage5-settings.png'), full_page=True)
            assert len(received) == 1 and not errors, errors
            (OUT/'stage5-browser.json').write_text(json.dumps(dict(errors=errors, local_webhook_messages=received), ensure_ascii=False, indent=2), encoding='utf-8')
            await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
