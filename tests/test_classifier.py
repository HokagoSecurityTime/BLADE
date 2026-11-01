from dataclasses import asdict
import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import httpx
import pytest

from common.labels import Label
from pipeline.classifier import classify, llm
from pipeline.classifier.prompt import SYSTEM_PROMPT
from pipeline.classifier.run import EXPECTED
from pipeline.classifier.schema import ClassificationResult, parse_result
from pipeline.parsers.erd import parse_erd
from pipeline.parsers.oas import Endpoint, parse_oas

ROOT = Path(__file__).resolve().parents[1]
ENDPOINTS = parse_oas((ROOT / 'demo_backend/openapi.json').read_text(encoding='utf-8'))
ERD = parse_erd((ROOT / 'demo_backend/schema.sql').read_text(encoding='utf-8'))


def output(label: str = 'public', confidence: float = 0.95) -> dict[str, Any]:
    return dict(label=label, confidence=confidence, evidence='Input evidence', object_param=None,
                owner_lookup=None, roles=[], allowed_membership=[])


@pytest.mark.parametrize('endpoint', ENDPOINTS, ids=lambda e: f'{e.method} {e.path}')
def test_demo_labels(monkeypatch: pytest.MonkeyPatch, endpoint: Endpoint) -> None:
    expected = EXPECTED[(endpoint.method, endpoint.path)]
    data = output(expected)
    if expected in {'owner_match', 'owner_or_admin', 'tenant_match'}:
        table = endpoint.path.split('/')[1]
        data['object_param'] = endpoint.path_params[0]
        data['owner_lookup'] = dict(table=table, id_col='id',
                                    owner_col='user_id' if table == 'orders' else 'id' if table == 'users' else None,
                                    tenant_col='id' if table == 'orgs' else None)
    if expected in {'role_required', 'owner_or_admin'}:
        data['roles'] = ['admin']
    if expected == 'membership_required':
        data['allowed_membership'] = ['premium']
    completion = Mock(return_value=json.dumps(data))
    monkeypatch.setattr(llm, 'complete', completion)
    before = {name: asdict(table) for name, table in ERD.items()}
    result = classify(endpoint, ERD, '# controller input')
    assert result.label.value == expected
    completion.assert_called_once()
    system, user = completion.call_args.args
    assert system == SYSTEM_PROMPT
    assert json.loads(user)['endpoint'] == asdict(endpoint)
    assert json.loads(user)['output_format'] == 'json'
    assert json.loads(user)['controller_text'] == '# controller input'
    assert json.loads(user)['tables'] == before
    assert {name: asdict(table) for name, table in ERD.items()} == before


@pytest.mark.parametrize('raw', ['not json', '```json\n{}\n```', '[]', '{}',
    json.dumps(output('invented')), json.dumps(output(confidence=0.69)),
    json.dumps(output(confidence=1.1)), json.dumps({**output(), 'label': []}),
    json.dumps({**output(), 'roles': 'admin'}), json.dumps({**output(), 'confidence': True})])
def test_invalid_output_escapes(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    monkeypatch.setattr(llm, 'complete', Mock(return_value=raw))
    result = classify(ENDPOINTS[0], ERD)
    assert result.label is Label.MANUAL_REVIEW_REQUIRED
    assert result.owner_lookup is None


def test_confidence_boundary_and_direct_validation() -> None:
    assert parse_result(json.dumps(output(confidence=0.7))).label is Label.PUBLIC
    assert ClassificationResult.model_validate(output('unknown')).label is Label.MANUAL_REVIEW_REQUIRED
    assert ClassificationResult.model_validate(output(confidence=0.699)).label is Label.MANUAL_REVIEW_REQUIRED


def test_hallucinated_lookup_escapes(monkeypatch: pytest.MonkeyPatch) -> None:
    endpoint = next(e for e in ENDPOINTS if e.path == '/orders/{orderId}')
    data = {**output('owner_match'), 'object_param': 'orderId',
            'owner_lookup': dict(table='orders', id_col='id', owner_col='nonexistent', tenant_col=None)}
    monkeypatch.setattr(llm, 'complete', Mock(return_value=json.dumps(data)))
    assert classify(endpoint, ERD).label is Label.MANUAL_REVIEW_REQUIRED


def test_provider_failure_escapes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, 'complete', Mock(side_effect=llm.LLMError('unavailable')))
    assert classify(ENDPOINTS[0], ERD).label is Label.MANUAL_REVIEW_REQUIRED


def configure(monkeypatch: pytest.MonkeyPatch, provider: str = 'openai') -> None:
    monkeypatch.setenv('BLADE_LLM_PROVIDER', provider)
    monkeypatch.setenv('BLADE_LLM_MODEL', 'test-model')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-key')


@pytest.mark.parametrize('provider', ['openai', 'anthropic', 'ollama'])
def test_provider_wire_format(monkeypatch: pytest.MonkeyPatch, provider: str) -> None:
    configure(monkeypatch, provider)
    captured = []

    def handle(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        body = json.loads(request.content)
        assert body['model'] == 'test-model'
        assert request.extensions['timeout']['read'] == 60.0
        if provider == 'openai':
            assert request.url.path == '/v1/responses'
            assert body['instructions'] == 'system' and body['input'] == 'user'
            assert request.headers['authorization'] == 'Bearer test-key'
            data = {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': '{}'}]}]}
        elif provider == 'anthropic':
            assert request.url.path == '/v1/messages'
            assert body['system'] == 'system' and body['messages'] == [{'role': 'user', 'content': 'user'}]
            assert request.headers['x-api-key'] == 'test-key'
            data = {'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': '{}'}]}
        else:
            assert request.url.path == '/api/chat'
            assert body['format']['type'] == 'object' and body['stream'] is False
            assert all('owner_lookup' in branch['required'] for branch in body['format']['oneOf'])
            assert body['messages'] == [{'role': 'system', 'content': 'system'}, {'role': 'user', 'content': 'user'}]
            assert 'authorization' not in request.headers
            data = {'done': True, 'message': {'content': '{}'}}
        return httpx.Response(200, json=data)

    client_class = httpx.Client
    monkeypatch.setattr(llm.httpx, 'Client', lambda **kwargs: client_class(transport=httpx.MockTransport(handle), **kwargs))
    assert llm.complete('system', 'user') == '{}'
    assert len(captured) == 1


@pytest.mark.parametrize('failure', ['timeout', 429, 503, 401])
def test_retries(monkeypatch: pytest.MonkeyPatch, failure: str | int) -> None:
    configure(monkeypatch)
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if failure == 'timeout':
            raise httpx.ReadTimeout('secret provider detail', request=request)
        return httpx.Response(failure, text='secret provider detail')

    client_class = httpx.Client
    monkeypatch.setattr(llm.httpx, 'Client', lambda **kwargs: client_class(transport=httpx.MockTransport(handle), **kwargs))
    sleep = Mock()
    monkeypatch.setattr(llm.time, 'sleep', sleep)
    with pytest.raises(llm.LLMError) as error:
        llm.complete('system', 'user')
    assert len(requests) == (1 if failure == 401 else 3)
    assert sleep.call_count == (0 if failure == 401 else 2)
    assert 'secret' not in str(error.value)


def test_missing_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('BLADE_LLM_PROVIDER', raising=False)
    with pytest.raises(llm.LLMConfigurationError):
        llm.complete('system', 'user')


def test_retry_recovers(monkeypatch: pytest.MonkeyPatch) -> None:
    configure(monkeypatch, 'openai')
    calls = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={'status': 'completed', 'output': [
            {'type': 'message', 'content': [{'type': 'output_text', 'text': '{}'}]}]})

    client_class = httpx.Client
    monkeypatch.setattr(llm.httpx, 'Client', lambda **kwargs: client_class(transport=httpx.MockTransport(handle), **kwargs))
    monkeypatch.setattr(llm.time, 'sleep', Mock())
    assert llm.complete('system', 'user') == '{}'
    assert len(calls) == 2


@pytest.mark.parametrize('data', [{}, {'status': 'incomplete', 'output': []},
                                 {'status': 'completed', 'output': []}])
def test_incomplete_provider_response(monkeypatch: pytest.MonkeyPatch, data: dict[str, Any]) -> None:
    configure(monkeypatch, 'openai')
    client_class = httpx.Client
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=data))
    monkeypatch.setattr(llm.httpx, 'Client', lambda **kwargs: client_class(transport=transport, **kwargs))
    with pytest.raises(llm.LLMError, match='no complete text'):
        llm.complete('system', 'user')


def test_ollama_needs_no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    configure(monkeypatch, 'ollama')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    monkeypatch.setenv('BLADE_OLLAMA_URL', 'http://127.0.0.1:11435/')
    settings = llm.settings_from_env()
    assert settings.api_key == ''
    assert llm._request(settings, 'system', 'user')[0] == 'http://127.0.0.1:11435/api/chat'


@pytest.mark.parametrize('data', [
    {'done': False, 'message': {'content': '{}'}},
    {'done': True, 'done_reason': 'length', 'message': {'content': '{}'}},
    {'done': True, 'message': {'content': ''}},
])
def test_ollama_rejects_incomplete_text(data: dict[str, Any]) -> None:
    with pytest.raises(llm.LLMError, match='no complete text'):
        llm._text('ollama', data)


@pytest.mark.skipif(not os.getenv('BLADE_LLM_PROVIDER'), reason='BLADE_LLM_PROVIDER is not configured')
def test_real_llm_demo() -> None:
    llm.settings_from_env()
    results = []
    for endpoint in ENDPOINTS:
        result = classify(endpoint, ERD)
        results.append(result)
        print(f'{endpoint.method} {endpoint.path}: {result.label.value} '
              f'confidence={result.confidence:.2f} evidence={json.dumps(result.evidence, ensure_ascii=True)}', flush=True)
    correct = sum(result.label.value == EXPECTED[(endpoint.method, endpoint.path)]
                  for endpoint, result in zip(ENDPOINTS, results))
    assert correct >= 6, [(endpoint.path, result.model_dump()) for endpoint, result in zip(ENDPOINTS, results)]
