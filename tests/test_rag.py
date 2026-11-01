import asyncio
import io
import json
import math
from pathlib import Path
import zipfile

import httpx
import pytest

from admin_api.main import create_app
from common.schema import EvidenceRef, PolicyStatus
from pipeline.classifier import classify, llm
from pipeline.classifier.prompt import build_user_prompt, system_prompt
from pipeline.parsers.oas import parse_oas
from pipeline.parsers.erd import parse_erd
from pipeline.rag.corpus import Chunk, load_code, load_zip, load_idioms, load_policies, load_cves
from pipeline.rag.index import Index
from tests.test_proxy import policy

ROOT = Path(__file__).resolve().parents[1]


class TestEncoder:
    """Deterministic vectors for storage/ranking tests; live ablation uses E5."""
    name = 'unit-test-encoder'

    def encode(self, texts: list[str], *, query: bool = False) -> list[list[float]]:
        vectors = []
        for text in texts:
            vector = [float(text.lower().count(word)) + .01 for word in ['user', 'role', 'tenant', 'public']]
            norm = math.sqrt(sum(v*v for v in vector))
            vectors.append([v/norm for v in vector])
        return vectors


def test_loaders(tmp_path: Path) -> None:
    code = load_code('@app.get("/users")\ndef users():\n    return current_user\n', 'api.py')
    assert len(code) == 1 and code[0].text.startswith('@app.get')
    assert len(load_idioms()) == 6
    active, pending = policy(), policy()
    pending.status = PolicyStatus.PENDING
    assert len(load_policies([active, pending])) == 1
    path = tmp_path/'cve.jsonl'
    assert load_cves(path) == []
    path.write_text(json.dumps(dict(cve_id='CVE-2025-12345', summary='Fixture only: missing object authorization', cwe=['CWE-639'], published='2025-01-01', refs=[])))
    assert load_cves(path)[0].kind == 'cve'
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('api.py', 'def users():\n return current_user')
    assert load_zip(stream.getvalue())[0].ref.startswith('api.py')
    bad = io.BytesIO()
    with zipfile.ZipFile(bad, 'w') as archive:
        archive.writestr('../api.py', 'def f(): pass')
    with pytest.raises(ValueError, match='Unsafe'):
        load_zip(bad.getvalue())


def test_persistent_retrieval_and_remove_stale(tmp_path: Path) -> None:
    index = Index(tmp_path/'chroma', TestEncoder())
    index.replace('idiom', load_idioms())
    index.replace('code', [Chunk('code', 'sample.py', 'def user(): return current_user')])
    endpoints = parse_oas((ROOT/'demo_backend/openapi.json').read_text())
    erd = parse_erd((ROOT/'demo_backend/schema.sql').read_text())
    result = index.retrieve(next(e for e in endpoints if e.path == '/users/{userId}'), erd)
    assert len(result) == 5 and any(ref.kind == 'idiom' for ref in result)
    assert Index(tmp_path/'chroma', TestEncoder()).collections['idiom'].count() == 6
    index.replace('code', [])
    assert index.collections['code'].count() == 0


def test_disabled_prompt_is_phase1_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    golden = json.loads((ROOT/'tests/fixtures/phase1_prompt.json').read_text())
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    monkeypatch.setenv('BLADE_CONTROLLER_ENABLED', 'false')
    monkeypatch.setenv('BLADE_RAG_ENABLED', 'false')
    endpoint = parse_oas((ROOT/'demo_backend/openapi.json').read_text())[0]
    erd = parse_erd((ROOT/'demo_backend/schema.sql').read_text())
    ref = EvidenceRef(kind='idiom', ref='ignored', snippet='ignored')
    assert system_prompt(rag=True).encode() == golden['system'].encode()
    assert build_user_prompt(endpoint, erd, evidence_refs=[ref]).encode() == golden['user'].encode()
    from pipeline.rag import retrieve
    assert retrieve(endpoint, erd) == []


def test_only_provided_evidence_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    monkeypatch.setenv('BLADE_RAG_ENABLED', 'true')
    endpoint = parse_oas((ROOT/'demo_backend/openapi.json').read_text())[0]
    ref = EvidenceRef(kind='idiom', ref='idioms/test', snippet='Actual reference text')
    output = dict(label='public', confidence=.95, evidence='Health probe', object_param=None, owner_lookup=None,
                  roles=[], allowed_membership=[], evidence_refs=[dict(kind='idiom', ref=ref.ref, snippet='Invented quote')])
    monkeypatch.setattr(llm, 'complete', lambda *args: json.dumps(output))
    result = classify(endpoint, {}, evidence_refs=[ref])
    assert result.evidence_refs == [ref]
    output['evidence_refs'][0]['ref'] = 'invented/ref'
    assert classify(endpoint, {}, evidence_refs=[ref]).label == 'manual_review_required'


def test_evidence_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    app = create_app(tmp_path/'blade.db', tmp_path/'policies', tmp_path/'logs.jsonl')
    p = policy()
    p.evidence_refs = [EvidenceRef(kind='code', ref='api.py#L1', snippet='def f(): pass')]
    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            app.state.store.insert_many([p])
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                assert (await client.get('/evidence/'+p.id)).json() == [ref.model_dump() for ref in p.evidence_refs]
                assert (await client.get('/evidence/missing')).status_code == 404
                monkeypatch.setenv('BLADE_RAG_ENABLED', 'false')
                assert (await client.get('/evidence/'+p.id)).status_code == 404
    asyncio.run(scenario())
