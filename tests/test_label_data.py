import asyncio
import importlib.util
import json
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest

from training.data import label
from training.data.filter_candidates import select, endpoint_key
from pipeline.classifier import prompt, llm
from pipeline.parsers.oas import parse_oas
from pipeline.parsers.erd import parse_erd
from common.schema import EvidenceRef

ROOT = Path(__file__).resolve().parents[1]


def rows():
    return [json.loads(line) for line in (ROOT / 'datasets/blade/processed/apisguru_resignaled.jsonl').read_text(encoding='utf-8').splitlines()]


@pytest.mark.parametrize('controller', [False, True])
@pytest.mark.parametrize('rag', [False, True])
def test_snapshot_byte_equivalence(monkeypatch, controller, rag):
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    monkeypatch.setenv('BLADE_CONTROLLER_ENABLED', str(controller).lower())
    monkeypatch.setenv('BLADE_RAG_ENABLED', str(rag).lower())
    monkeypatch.setenv('BLADE_PROMPT_VERSION', 'v2.0')
    spec = importlib.util.spec_from_file_location('old_prompt', ROOT / 'verification/phase3/prompt_before_v2.py')
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    assert old.system_prompt(rag=rag).encode() == prompt.system_prompt(rag=rag).encode()
    endpoints = parse_oas((ROOT / 'demo_backend/openapi.json').read_text(encoding='utf-8'))
    erd = parse_erd((ROOT / 'demo_backend/schema.sql').read_text(encoding='utf-8'))
    refs = [EvidenceRef(kind='code', ref='fixture', snippet='owner check')]
    for endpoint in endpoints:
        for code in (None, '@app.get("/users/{userId}")\ndef get_user(userId, current_user):\n    assert current_user.id == userId'):
            assert old.build_user_prompt(endpoint, erd, code, refs).encode() == prompt.build_user_prompt(endpoint, erd, code, refs).encode()


def test_filter_constraints_and_reproducibility():
    source = rows()
    output, report = select(source, {True: 450, False: 350})
    assert output == select(source, {True: 450, False: 350})[0]
    assert len(output) == 2027
    assert len({endpoint_key(row) for row in output}) == len(output)
    from collections import Counter
    none = [row for row in output if row['meta']['signal_class'] == 'none']
    assert max(Counter(row['service'] for row in none).values()) <= 4
    assert Counter(row['meta']['has_security'] for row in none) == {True: 450, False: 350}
    assert {endpoint_key(row) for row in source if row['meta']['signal_class'] != 'none'} <= {endpoint_key(row) for row in output}
    assert all(not row['meta']['incomplete'] for row in none)
    assert sum(row['meta']['incomplete'] for row in output) == 125


def test_truncation_keeps_late_owner_and_id():
    row = rows()[0]
    columns = [f'field_{i}' for i in range(60)] + ['owner_id', 'tenant_id', 'id']
    row['erd_snippet'] = 'CREATE TABLE objects (\n' + ',\n'.join(f'  {name} TEXT' for name in columns) + '\n);'
    row['meta'].update(owner_cols=['owner_id'], tenant_cols=['tenant_id'])
    user, changed = label.assemble(row, truncate=True)
    assert changed
    kept = json.loads(user)['tables']['objects']['columns']
    assert kept == columns[:30] + columns[-3:]


def test_retries_and_low_conf_without_runtime_remap(monkeypatch):
    attempts = []
    output = dict(label='public', confidence=.55, evidence='test', object_param=None, owner_lookup=None, roles=[], allowed_membership=[])
    def respond(request):
        attempts.append(request)
        if len(attempts) < 4:
            return httpx.Response(429)
        return httpx.Response(200, json={'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps(output)}]}]})
    sleep = AsyncMock()
    monkeypatch.setattr(label.asyncio, 'sleep', sleep)
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as session:
            return await label.label_one(rows()[0], 'system', llm.Settings('openai', 'gpt-4o-mini', 'fake'), session, False, lambda *_: 1)
    result = asyncio.run(run())
    assert len(attempts) == 4
    assert [call.args[0] for call in sleep.call_args_list] == [1, 2, 4]
    assert result['label'] == 'public' and result['meta']['low_conf']


def test_checkpoint_resume_and_manifest_guard(tmp_path, monkeypatch):
    mocked = AsyncMock(side_effect=lambda row, *args: row)
    monkeypatch.setattr(label, 'label_one', mocked)
    source = rows()[:101]
    target = tmp_path / 'partial.jsonl'
    settings = llm.Settings('openai', 'gpt-4o-mini', 'fake')
    async def run(manifest):
        await label.execute(source, 'system', lambda *_: 1, target, manifest, 4, False, settings)
    asyncio.run(run({'version': 1}))
    assert mocked.await_count == 101
    asyncio.run(run({'version': 1}))
    assert mocked.await_count == 101
    assert len(target.read_text(encoding='utf-8').splitlines()) == 101
    with pytest.raises(ValueError, match='mismatch'):
        asyncio.run(run({'version': 2}))


def test_insufficient_quota_stops_without_retry(monkeypatch):
    sleep = AsyncMock()
    monkeypatch.setattr(label.asyncio, 'sleep', sleep)
    def respond(request):
        return httpx.Response(429, json={'error': {'type': 'insufficient_quota', 'code': 'credit_balance_exhausted'}})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as session:
            await label.label_one(rows()[0], 'system', llm.Settings('openai', 'gpt-4o-mini', 'fake'), session, False, lambda *_: 1)
    with pytest.raises(label.LabelQuotaExhausted):
        asyncio.run(run())
    sleep.assert_not_awaited()
