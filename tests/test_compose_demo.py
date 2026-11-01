"""Run the exact demo driver on real HTTP servers; only classification is mocked."""
import asyncio
import json
import os
from pathlib import Path

from aiohttp.test_utils import TestServer
import pytest
import yaml

from admin_api.main import create_app as admin_app
from demo_backend.main import create_app as demo_app
from pipeline.classifier.schema import ClassificationResult
from proxy.server import create_app as proxy_app
from scripts.demo import run
from tests.test_e2e import serve
from tests.test_proxy import SECRET

ROOT = Path(__file__).resolve().parents[1]


def test_seven_step_driver(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    saved = json.loads((ROOT / 'verification/classifier-ollama-live.json').read_text(encoding='utf-8'))
    answers = {(row['method'], row['path']): row['result'] for row in saved['results']}
    monkeypatch.setattr('admin_api.main.classifier.classify',
                        lambda endpoint, *args: ClassificationResult.model_validate(answers[(endpoint.method, endpoint.path)]))
    db = tmp_path / 'demo.db'
    monkeypatch.setenv('BLADE_JWT_SECRET', SECRET)
    monkeypatch.setenv('BLADE_DB_DSN', 'sqlite:///' + str(db))
    monkeypatch.setenv('BLADE_POLICY_POLL_SEC', '0.5')
    monkeypatch.setenv('BLADE_FAIL_MODE', 'closed')

    async def scenario() -> list[dict]:
        api = admin_app(tmp_path / 'blade.db', tmp_path / 'policies', tmp_path / 'detections.jsonl')
        async with serve(demo_app(db)) as target, serve(api) as admin:
            monkeypatch.setenv('BLADE_TARGET_URL', target)
            monkeypatch.setenv('BLADE_ADMIN_URL', admin)
            async with TestServer(proxy_app()) as proxy:
                return await asyncio.to_thread(run, admin, str(proxy.make_url('/')).rstrip('/'),
                                               db, ROOT / 'demo_backend', .5)

    results = asyncio.run(scenario())
    assert [r['step'] for r in results] == list(range(1, 8))
    output = os.getenv('BLADE_COMPOSE_DEMO_REPORT')
    if output:
        Path(output).write_text(json.dumps(dict(validation='local HTTP, mocked classification; not Docker',
                                                results=results), indent=2), encoding='utf-8')


def test_compose_wiring() -> None:
    config = yaml.safe_load((ROOT / 'docker-compose.yml').read_text())
    services = config['services']
    assert set(services) == {'demo-backend', 'admin-api', 'proxy', 'dashboard', 'alerts'}
    assert set(services['proxy']['depends_on']) == {'demo-backend', 'admin-api'}
    assert services['proxy']['volumes'] == ['demo-data:/data:ro']
    assert services['admin-api']['env_file'] == '.env'
    assert services['proxy']['environment']['BLADE_PROXY_HOST'] == '0.0.0.0'
