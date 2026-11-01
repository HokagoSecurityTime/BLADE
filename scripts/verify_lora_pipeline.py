"""Step-4 check of the 2-stage LoRA pipeline on demo_backend (live Ollama, no test-set data).

For BLADE_CLASSIFIER=llm and =lora: POST /generate (demo OAS + ERD + demo_backend/main.py as controller) on a fresh
admin API, timing the batch. For lora, every generated PENDING policy is approved, the proxy loads them, and
BOLA / tenant / role requests are sent through it. Writes reports/eval/lora_v4_gguf/pipeline_compare.{json,md}.

Usage: python -X utf8 scripts/verify_lora_pipeline.py   (needs Ollama with blade-qwen-lora-v4 and BLADE_LLM_MODEL)
"""
import asyncio, json, os, sys, tempfile, time
from pathlib import Path

import httpx, jwt
from aiohttp import ClientSession, FormData
from aiohttp.test_utils import TestServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from admin_api.main import create_app as admin_app  # noqa: E402
from demo_backend.main import create_app as demo_app  # noqa: E402
from proxy.server import create_app as proxy_app  # noqa: E402
from tests.test_e2e import serve  # noqa: E402

OUT = Path(os.getenv('BLADE_VERIFY_OUT') or ROOT / 'reports/eval/lora_v4_gguf')   # C-5: BLADE_VERIFY_OUT=reports/eval/lora_v5_gguf keeps the v4 record intact
SECRET = 'verify-lora-pipeline-secret-at-least-32-bytes'
FILES = dict(oas=ROOT / 'demo_backend/openapi.json', erd=ROOT / 'demo_backend/schema.sql', controller=ROOT / 'demo_backend/main.py')
INTENDED = {('GET', '/public/health'): 'public', ('GET', '/orders/{orderId}'): 'owner_match', ('DELETE', '/orders/{orderId}'): 'owner_match',
            ('GET', '/users/{userId}'): 'owner_or_admin', ('GET', '/admin/reports'): 'role_required',
            ('GET', '/orgs/{orgId}/docs'): 'tenant_match', ('GET', '/premium/content'): 'membership_required'}  # demo descriptions
# (case, method, path, user, expected status if the route's policy enforces its label; 200 when it is manual/OBSERVE)
REQUESTS = [('BOLA: other user reads order', 'GET', '/orders/1042', 'user_99', 403), ('owner reads own order', 'GET', '/orders/1042', 'user_77', 200),
            ('BOLA: other user deletes order', 'DELETE', '/orders/1042', 'user_99', 403), ('other tenant reads org docs', 'GET', '/orgs/org_1/docs', 'user_99', 403),
            ('same tenant reads org docs', 'GET', '/orgs/org_1/docs', 'user_77', 200), ('non-admin reads admin reports', 'GET', '/admin/reports', 'user_99', 403),
            ('admin reads admin reports', 'GET', '/admin/reports', 'admin_1', 200), ('other user reads user record', 'GET', '/users/user_77', 'user_99', 403),
            ('public health without JWT', 'GET', '/public/health', None, 200)]


def token(user: str) -> str:
    admin = user == 'admin_1'
    return jwt.encode(dict(sub=user, roles=['admin'] if admin else ['user'], tenant_id='org_2' if user == 'user_99' else 'org_1',
                           membership='premium' if admin else 'basic', exp=int(time.time()) + 3600), SECRET, algorithm='HS256')


def ollama_ps() -> list[dict]:
    url = os.getenv('BLADE_OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
    models = httpx.get(url + '/api/ps', timeout=10).json().get('models', [])
    return [dict(name=m['name'], size=m.get('size'), size_vram=m.get('size_vram')) for m in models]


async def run(classifier: str, work: Path) -> dict:
    os.environ['BLADE_CLASSIFIER'] = classifier
    api = admin_app(work / 'blade.db', work / 'policies', work / 'detections.jsonl')
    out: dict = dict(classifier=classifier)
    async with serve(demo_app(work / 'demo.db')) as target, serve(api) as admin, ClientSession() as client:
        form = FormData()
        for name, path in FILES.items():
            form.add_field(name, path.read_bytes(), filename=path.name)
        t0 = time.perf_counter()
        async with client.post(admin + '/generate', data=form, timeout=None) as response:
            assert response.status == 200, await response.text()
            policies = await response.json()
        seconds = time.perf_counter() - t0
        out.update(policies=policies, seconds=round(seconds, 1), seconds_per_policy=round(seconds / len(policies), 1), ollama_ps=ollama_ps())
        assert all(p['status'] == 'PENDING' for p in policies)
        if classifier != 'lora':
            return out
        for p in policies:
            async with client.post(admin + '/policies/' + p['id'] + '/approve') as response:
                assert response.status == 200 and (await response.json())['status'] == 'ACTIVE'
        os.environ.update(BLADE_JWT_SECRET=SECRET, BLADE_TARGET_URL=target, BLADE_ADMIN_URL=admin,
                          BLADE_DB_DSN='sqlite:///' + str(work / 'demo.db'), BLADE_FAIL_MODE='closed', BLADE_POLICY_POLL_SEC='0.05')
        labels = {(p['endpoint']['method'], p['endpoint']['path']): p['label'] for p in policies}
        checks = []
        async with TestServer(proxy_app()) as proxy:
            base = str(proxy.make_url('/')).rstrip('/')
            await asyncio.sleep(0.5)  # first policy poll
            for case, method, path, user, enforced in REQUESTS:
                route = next(k for k in labels if k[0] == method and k[1].split('/')[1] == path.split('/')[1])
                expected = 200 if labels[route] == 'manual_review_required' else enforced
                headers = {'Authorization': 'Bearer ' + token(user)} if user else {}
                async with client.request(method, base + path, headers=headers) as response:
                    status = response.status
                    await response.read()
                checks.append(dict(case=case, method=method, path=path, user=user, policy_label=labels[route], expected=expected, actual=status, ok=status == expected))
        out['proxy_checks'] = checks
        logs = work / 'detections.jsonl'
        out['detections'] = [json.loads(line) for line in logs.read_text(encoding='utf-8').splitlines()] if logs.exists() else []
    return out


def lookup(p: dict | None) -> str:
    l = (p or {}).get('params', {}).get('owner_lookup')
    return '-' if not l else f"{l['table']}.{l['id_col']} owner={l['owner_col']} tenant={l['tenant_col']}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    runs = {}
    for classifier in ('llm', 'lora'):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as work:
            runs[classifier] = asyncio.run(run(classifier, Path(work)))
    (OUT / 'pipeline_compare.json').write_text(json.dumps(runs, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    by = {c: {(p['endpoint']['method'], p['endpoint']['path']): p for p in r['policies']} for c, r in runs.items()}
    rows = ['| endpoint | 의도(데모 설명) | llm label | lora label | label 일치 | llm owner_lookup | lora owner_lookup | owner_lookup 일치 | lora roles |', '|---|---|---|---|---|---|---|---|---|']
    for key, intended in INTENDED.items():
        a, b = by['llm'].get(key), by['lora'].get(key)
        rows.append(f"| {key[0]} {key[1]} | {intended} | {a['label']} | {b['label']} | {'O' if a['label'] == b['label'] else 'X'} | {lookup(a)} | {lookup(b)} | "
                    f"{'O' if lookup(a) == lookup(b) else 'X'} | {b['params']['roles']} |")
    checks = ['| 요청 | 사용자 | 정책 label | 기대 | 실제 | 결과 |', '|---|---|---|---:|---:|---|'] + [
        f"| {c['case']} ({c['method']} {c['path']}) | {c['user'] or '-'} | {c['policy_label']} | {c['expected']} | {c['actual']} | {'OK' if c['ok'] else 'FAIL'} |" for c in runs['lora']['proxy_checks']]
    timing = [f"- {c}: {r['seconds']}s / {len(r['policies'])} policies = {r['seconds_per_policy']}s per policy; ollama ps {r['ollama_ps']}" for c, r in runs.items()]
    evidence = [f"- {k[0]} {k[1]}: {p['evidence']}" for k, p in by['lora'].items()]
    (OUT / 'pipeline_compare.md').write_text('\n'.join(['# demo_backend: llm vs lora 경로 정책 비교', '', *rows, '', '## lora 정책 승인 → 프록시 요청', '', *checks, '',
                                                     '## 소요 시간', '', *timing, '', '## lora evidence', '', *evidence, '']), encoding='utf-8')
    print((OUT / 'pipeline_compare.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    main()
