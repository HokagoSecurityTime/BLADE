"""Authorized two-message Slack verification; never persist the webhook URL."""
import asyncio
import json
import os
from pathlib import Path
import time
from urllib.parse import urlparse

from aiohttp import ClientSession, ClientTimeout
from aiohttp.test_utils import TestServer
import httpx
import jwt

from admin_api.main import create_app
from admin_api.workers.alerts import AlertWorker, message
from admin_api.workers.explain import explain
from demo_backend.main import create_app as backend_app
from pipeline.classifier import llm
from proxy.server import create_app as proxy_app
from scripts.load_test import serve
from tests.test_proxy import policy, SECRET


async def main() -> None:
    output = Path('verification/phase2') / time.strftime('slack-live-%Y%m%d-%H%M%S')
    output.mkdir()
    secret_file = Path('verification/phase2/slack-webhook.local.txt')
    async with httpx.AsyncClient() as client:
        settings = (await client.get('http://127.0.0.1:18100/settings/alerts')).json()
    webhook = secret_file.read_text(encoding='utf-8-sig').strip() if secret_file.exists() else settings['slack_webhook']
    assert urlparse(webhook).hostname in {'hooks.slack.com', 'hooks.slack-gov.com'}
    settings = dict(slack_webhook=webhook, discord_webhook='', min_severity='observe')
    os.environ.update(BLADE_PHASE2_ENABLED='true', BLADE_REDIS_ENABLED='false', BLADE_RAG_ENABLED='false',
        BLADE_EXPLAIN_ENABLED='true', BLADE_ALERTS_ENABLED='true', BLADE_JWT_SECRET=SECRET,
        BLADE_LLM_PROVIDER='ollama', BLADE_LLM_MODEL='qwen2.5:7b', BLADE_POLICY_POLL_SEC='.05',
        BLADE_DB_DSN='sqlite:///'+str((output/'demo.db').resolve()))
    api = create_app(output/'blade.db', output/'policies', output/'detections.jsonl')
    results = []
    completions = []
    original = llm.complete

    def capture(system: str, user: str, **kwargs: object) -> str:
        answer = original(system, user, **kwargs)
        completions.append(dict(system=system, user=json.loads(user), response=answer))
        (output/'llm.json').write_text(json.dumps(completions, ensure_ascii=False, indent=2), encoding='utf-8')
        return answer
    llm.complete = capture
    try:
        async with serve(api) as admin, serve(backend_app(output/'demo.db')) as target, ClientSession(timeout=ClientTimeout(total=15)) as client:
            p = policy()
            p.params.owner_lookup.tenant_col = None
            api.state.store.insert_many([p])
            os.environ.update(BLADE_ADMIN_URL=admin, BLADE_TARGET_URL=target)
            worker = AlertWorker()
            async with TestServer(proxy_app()) as proxy:
                for mode, expected in [('observe', 200), ('enforce', 403)]:
                    # Distinct, explicit test subjects avoid the documented
                    # same-subject 60-second suppression without disabling it.
                    subject = 'blade_test_' + mode
                    async with client.post(admin+'/policies/'+p.id+'/mode', json={'mode': mode}) as response:
                        assert response.status == 200
                    await asyncio.sleep(.2)
                    token = jwt.encode(dict(sub=subject, roles=['user'], tenant_id='org_2', membership='basic',
                        exp=int(time.time())+3600), SECRET, algorithm='HS256')
                    async with client.get(proxy.make_url('/orders/1042'), headers={'Authorization': 'Bearer '+token}) as response:
                        assert response.status == expected
                        identifier = response.headers['X-Blade-Request-Id']
                        await response.read()
                    for _ in range(100):
                        row = next((r for r in api.state.store.list_detections(100) if r.request_id == identifier), None)
                        if row is not None: break
                        await asyncio.sleep(.05)
                    assert row is not None
                    assert row.verdict == ('OBSERVE' if mode == 'observe' else 'BLOCK')
                    assert row.would_block == (mode == 'observe')
                    print(f'{mode}: HTTP {expected}; requesting real LLM explanation', flush=True)
                    explanation = await explain(row, client, admin)
                    assert explanation
                    row.explanation = explanation
                    delivered = await worker.notify(row, client, settings)
                    assert delivered, 'Slack delivery failed (URL omitted)'
                    results.append(dict(mode=mode, http_status=expected, verdict=row.verdict.value,
                        would_block=row.would_block, slack_http_success=delivered, request_id=identifier,
                        explanation=explanation, message=message(row), channel='blade-alert'))
                    (output/'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
                    print(f'{mode}: Slack accepted message; request_id={identifier}', flush=True)
    finally:
        llm.complete = original
    print(f'Results: {output}', flush=True)


if __name__ == '__main__': asyncio.run(main())
