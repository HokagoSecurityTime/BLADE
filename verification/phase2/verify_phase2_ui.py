"""Real browser/API/proxy flow; proposal contents are an explicit UI fixture."""
import asyncio
import json
import os
from pathlib import Path
import tempfile

from aiohttp import ClientSession
from aiohttp.test_utils import TestServer
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import jwt
from playwright.async_api import async_playwright

from admin_api.main import create_app
from admin_api.proposals import Proposals
from common.labels import Label
from demo_backend.main import create_app as demo_app
from proxy.server import create_app as proxy_app
from scripts.load_test import serve
from tests.test_proxy import policy, claims, SECRET

OUT=Path('verification/phase2')


async def main() -> None:
    os.environ.update(BLADE_PHASE2_ENABLED='true',BLADE_REDIS_ENABLED='false',BLADE_JWT_SECRET=SECRET,BLADE_POLICY_POLL_SEC='.05')
    with tempfile.TemporaryDirectory(dir=OUT) as directory:
        root=Path(directory);os.environ['BLADE_DB_DSN']='sqlite:///'+str((root/'demo.db').resolve())
        admin=create_app(root/'blade.db',root/'policies',root/'logs.jsonl');store=admin.state.store;store.initialize()
        p=policy();p.params.owner_lookup.tenant_col=None;store.insert_many([p])
        app=FastAPI();app.mount('/api',admin);app.mount('/',StaticFiles(directory=OUT/'ui-dist',html=True))
        async with serve(app) as url,serve(demo_app(root/'demo.db')) as target,async_playwright() as pw,ClientSession() as client:
            os.environ.update(BLADE_TARGET_URL=target,BLADE_ADMIN_URL=url+'/api')
            async with TestServer(proxy_app()) as proxy:
                token=jwt.encode(claims('user_99').model_dump(),SECRET,algorithm='HS256')
                async def status() -> int:
                    async with client.get(proxy.make_url('/orders/1042'),headers={'Authorization':'Bearer '+token}) as r:
                        await r.read();return r.status
                assert await status()==200
                browser=await pw.chromium.launch(channel='msedge',headless=True)
                page=await browser.new_page(viewport={'width':1600,'height':1100});errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                await page.goto(url)
                await page.get_by_role('button',name=p.id+' 모드 전환').click()
                for _ in range(100):
                    if store.get(p.id).mode=='enforce':break
                    await asyncio.sleep(.05)
                await asyncio.sleep(.2);assert await status()==403
                base=store.get(p.id)
                proposed=base.model_copy(update={'label':Label.OWNER_OR_ADMIN,'version':2,'mode':'observe','source':'reanalysis','evidence':'UI verification fixture: allow owner or administrator'})
                item=Proposals(store).create(base,proposed,'UI fixture: review the administrator bypass')
                await page.get_by_role('button',name='YAML 보기·편집').click()
                await page.get_by_role('button',name='근거 CVE',exact=True).click()
                await page.get_by_text('인용한 CVE 근거가 없습니다.').wait_for()
                await page.get_by_role('button',name='제안',exact=True).click()
                await page.get_by_role('button',name='제안 수락').wait_for()
                assert await page.locator('.diffrow.added').count()>0
                await page.screenshot(path=str(OUT/'stage8-proposal-diff.png'),full_page=True)
                await page.get_by_role('button',name='제안 수락').click()
                await page.get_by_text('제안을 반영했습니다. observe 모드로 전환되었습니다.').wait_for()
                assert store.get(p.id).version==2 and store.get(p.id).mode=='observe'
                await asyncio.sleep(.2);assert await status()==200
                await page.get_by_role('button',name='닫기',exact=True).click()
                current=store.get(p.id);Proposals(store).create(current,current,'UI fixture: dismiss unchanged proposal')
                await page.get_by_role('button',name='YAML 보기·편집').click()
                await page.get_by_role('button',name='제안',exact=True).click()
                await page.get_by_role('button',name='제안 기각').click()
                await page.get_by_text('제안을 기각했습니다.').wait_for()
                assert Proposals(store).list(p.id)[0]['status']=='DISMISSED'
                await page.get_by_role('button',name='닫기',exact=True).click()
                await page.locator('nav').get_by_role('button',name='탐지 로그').click()
                await page.get_by_role('button',name='↻ 새로고침').click()
                await page.get_by_label('verdict 필터').select_option('would_block')
                await page.screenshot(path=str(OUT/'stage8-detections.png'),full_page=True)
                await page.set_viewport_size({'width':390,'height':844})
                await page.screenshot(path=str(OUT/'stage8-mobile.png'),full_page=True)
                assert not errors,errors
                (OUT/'stage8-browser.json').write_text(json.dumps(dict(errors=errors,ui_enforce_status=403,ui_accept_status=200,version=2,dismissed=True),indent=2),encoding='utf-8')
                await browser.close()


if __name__=='__main__':asyncio.run(main())
