"""Explicit local browser verification against the Docker demo; creates screenshots."""
import json
import os
from pathlib import Path
import time

import httpx
import jwt
from playwright.sync_api import sync_playwright


def main() -> None:
    secret = os.environ['BLADE_JWT_SECRET']
    poll = float(os.getenv('BLADE_POLICY_POLL_SEC','5'))
    token = jwt.encode(dict(sub='user_99',roles=['user'],tenant_id='org_2',membership='basic',exp=int(time.time())+600),secret,algorithm='HS256')
    results = []
    with httpx.Client() as client, sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1540,'height':1020},device_scale_factor=1)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://localhost:3000')
        page.get_by_role('heading',name='정책 목록',exact=True).first.wait_for()
        row=page.get_by_role('row').filter(has_text='pol_orders_get_by_orderId')
        row.wait_for()
        def response_status() -> int:
            return client.get('http://localhost:8080/orders/1042',headers={'Authorization':'Bearer '+token}).status_code
        def wait_status(expected: int, start: float) -> float:
            while time.monotonic()-start < poll+1:
                if response_status()==expected:return time.monotonic()-start
                time.sleep(.05)
            raise AssertionError(f'Proxy did not change to {expected}')
        # Normalize through the UI if a prior run left this policy active.
        if row.get_by_role('button',name='pol_orders_get_by_orderId 롤백',exact=True).count():
            row.get_by_role('button',name='pol_orders_get_by_orderId 롤백',exact=True).click()
            wait_status(200,time.monotonic())
        assert response_status()==200
        row.get_by_role('button',name='pol_orders_get_by_orderId 승인',exact=True).click()
        elapsed=wait_status(403,time.monotonic())
        results.append(dict(case='dashboard approve -> proxy BLOCK',status=403,elapsed_sec=elapsed))
        row.get_by_role('button',name='YAML 보기·편집',exact=True).click()
        editor=page.get_by_role('textbox',name='정책 YAML',exact=True)
        original=editor.input_value();assert 'owner_match' in original
        editor.fill(original)
        page.get_by_role('button',name='YAML 저장',exact=True).click()
        page.get_by_role('dialog').wait_for(state='hidden')
        page.screenshot(path='verification/dashboard-policies.png',full_page=True)
        row.get_by_role('button',name='pol_orders_get_by_orderId 롤백',exact=True).click()
        elapsed=wait_status(200,time.monotonic())
        results.append(dict(case='dashboard rollback -> proxy OBSERVE',status=200,elapsed_sec=elapsed))
        row.get_by_role('button',name='pol_orders_get_by_orderId 승인',exact=True).click()
        wait_status(403,time.monotonic())  # Leave the demo protected for the attack matrix.
        page.get_by_role('button',name='≋ 탐지 로그').click()
        page.get_by_label('verdict 필터').select_option('BLOCK')
        page.screenshot(path='verification/dashboard-detections.png',full_page=True)
        page.get_by_role('button',name='◇ 수동 검토 큐').click()
        page.get_by_role('heading',name='수동 검토 큐',exact=True).first.wait_for()
        page.screenshot(path='verification/dashboard-review.png',full_page=True)
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path='verification/dashboard-mobile.png',full_page=True)
        assert not errors, errors
        browser.close()
    Path('verification/dashboard-browser.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2))


if __name__=='__main__':main()
