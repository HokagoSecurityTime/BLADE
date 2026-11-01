"""Reproducible live Ollama check against an isolated admin HTTP server."""
import asyncio
import argparse
import json
import os
from pathlib import Path
import tempfile
import time

import httpx

from admin_api.main import create_app
from pipeline.classifier import llm
from tests.test_e2e import serve

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'verification/phase2'


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--users-only', action='store_true', help='Target the required owner/admin regression through /generate')
    parser.add_argument('--controller', default='tests/fixtures/controllers/demo_with_admin.py')
    args = parser.parse_args()
    os.environ.update(BLADE_PHASE2_ENABLED='true', BLADE_CONTROLLER_ENABLED='true',
                      BLADE_RAG_ENABLED='false',
                      BLADE_LLM_PROVIDER='ollama', BLADE_LLM_MODEL='qwen2.5:7b',
                      BLADE_OLLAMA_URL='http://127.0.0.1:11434')
    files = {name: (filename, (ROOT/path).read_bytes()) for name, filename, path in [
        ('oas', 'openapi.json', 'demo_backend/openapi.json'),
        ('erd', 'schema.sql', 'demo_backend/schema.sql'),
        ('controller', Path(args.controller).name, args.controller)]}
    count = 7
    prefix = 'stage3'
    if args.users_only:
        oas = json.loads(files['oas'][1])
        oas['paths'] = {'/users/{userId}': oas['paths']['/users/{userId}']}
        files['oas'] = ('openapi.json', json.dumps(oas).encode())
        count = 1
        prefix = 'stage3-users-fixture'
    complete = llm.complete
    completions: list[dict[str, str]] = []

    def capture(system: str, user: str) -> str:
        # Delegate to the real adapter, retaining the unvalidated model output.
        response = complete(system, user)
        completions.append(dict(system=system, user=user, response=response))
        (OUT/f'{prefix}-llm.json').write_text(json.dumps(completions, ensure_ascii=False, indent=2), encoding='utf-8')
        return response

    llm.complete = capture
    with tempfile.TemporaryDirectory(prefix='stage3-', dir=OUT) as directory:
        work = Path(directory)
        async with serve(create_app(work/'blade.db', work/'policies', work/'logs.jsonl')) as admin:
            async with httpx.AsyncClient(timeout=1500) as client:
                request = client.build_request('POST', admin+'/generate', files=files)
                body = await request.aread()
                start = time.monotonic()
                print(f'Live /generate started: Ollama qwen2.5:7b, {count} sequential endpoints', flush=True)
                response = await client.send(request)
                (OUT/f'{prefix}-generate.txt').write_text(
                    f'{request.method} {request.url}\n{request.headers}\n\n'+body.decode('utf-8')+
                    f'\n\nHTTP {response.status_code}\n{response.headers}\n\n{response.text}\n', encoding='utf-8')
                response.raise_for_status()
                policies = response.json()
                (OUT/f'{prefix}-policies.json').write_text(json.dumps(policies, ensure_ascii=False, indent=2), encoding='utf-8')
                for policy in policies:
                    print(policy['endpoint']['method'], policy['endpoint']['path'], policy['label'], flush=True)
                target = next(p for p in policies if p['endpoint']['path'] == '/users/{userId}')
                report = dict(provider='ollama', model='qwen2.5:7b', elapsed_sec=time.monotonic()-start,
                              count=len(policies), expected='owner_or_admin', actual=target['label'],
                              controller=args.controller,
                              passed=len(policies) == count and target['label'] == 'owner_or_admin')
                (OUT/f'{prefix}-live-result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
                print(json.dumps(report), flush=True)
                if not report['passed']:
                    raise SystemExit(1)


if __name__ == '__main__':
    asyncio.run(main())
