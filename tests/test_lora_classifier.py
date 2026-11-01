"""BLADE_CLASSIFIER=lora: 2-a LoRA label + 2-b parameter extraction, without a model or network."""
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from common.labels import Label
from pipeline import param_extractor
from pipeline.classifier import classify, llm
from pipeline.classifier import lora
from pipeline.generator import build_policy
from pipeline.parsers.erd import parse_erd
from pipeline.parsers.oas import parse_oas

ROOT = Path(__file__).resolve().parents[1]
ENDPOINTS = {(e.method, e.path): e for e in parse_oas((ROOT / 'demo_backend/openapi.json').read_text(encoding='utf-8'))}
ERD = parse_erd((ROOT / 'demo_backend/schema.sql').read_text(encoding='utf-8'))
CONTROLLER = (ROOT / 'demo_backend/main.py').read_text(encoding='utf-8')


def reply(label: str, confidence: float = 0.9) -> str:
    return json.dumps(dict(label=label, confidence=confidence, rationale='description: 근거; 판단: ' + label,
                           evidence_fields=['description']), ensure_ascii=False)


@pytest.fixture
def lora_env(monkeypatch: pytest.MonkeyPatch) -> Mock:
    monkeypatch.setenv('BLADE_CLASSIFIER', 'lora')
    completion = Mock()
    monkeypatch.setattr(llm, 'complete', completion)
    return completion


def test_default_classifier_is_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('BLADE_CLASSIFIER', raising=False)
    completion = Mock(return_value=json.dumps(dict(label='public', confidence=0.95, evidence='e', object_param=None,
                                                   owner_lookup=None, roles=[], allowed_membership=[])))
    monkeypatch.setattr(llm, 'complete', completion)
    assert classify(ENDPOINTS['GET', '/public/health'], ERD).label == Label.PUBLIC
    assert 'settings' not in completion.call_args.kwargs


def test_user_message_matches_v301_training_format() -> None:
    user, has_code = lora.user_message(ENDPOINTS['GET', '/orders/{orderId}'], ERD, CONTROLLER)
    assert has_code and user.startswith('Return JSON.\n')
    payload = json.loads(user.split('\n', 1)[1])
    assert list(payload) == ['method', 'path', 'path_params', 'query_params', 'summary', 'description', 'security',
                             'security_state', 'schema_fields', 'schema_provenance', 'owner_cols', 'tenant_cols']
    assert payload['description'].startswith('Intended policy: owner_match; orders.user_id\n' + lora.CODE_HEADER + 'def get_order(')
    assert 'def delete_order' not in payload['description']  # only this route's handler
    assert payload['owner_cols'] == ['user_id'] and payload['security_state'] == 'unknown'
    no_code, has_code = lora.user_message(ENDPOINTS['GET', '/orders/{orderId}'], ERD, None)
    assert not has_code and json.loads(no_code.split('\n', 1)[1])['description'] == 'Intended policy: owner_match; orders.user_id'


def test_lora_request_uses_ollama_model_and_v301_prompt(lora_env: Mock) -> None:
    lora_env.return_value = reply('public')
    result = classify(ENDPOINTS['GET', '/public/health'], ERD, CONTROLLER)
    assert result.label == Label.PUBLIC and result.object_param is None
    system, _ = lora_env.call_args.args
    kwargs = lora_env.call_args.kwargs
    assert system == (ROOT / 'training/data/prompts/policy_label_v3.0.1.md').read_text(encoding='utf-8')
    assert kwargs['settings'].provider == 'ollama' and kwargs['settings'].model == 'blade-qwen-lora-v4'
    assert kwargs['json_format'] is False and kwargs['allow_truncated'] is True
    assert result.evidence.startswith('[blade-qwen-lora-v4 policy-label-v3.0.1 label=public confidence=0.9]')


@pytest.mark.parametrize('raw', ['not json', '{"label": "owner_match", "confidence": 0.9, "rationale": "cut',
                                 reply('invented'), json.dumps({'label': 'public'}), reply('public', 1.5)])
def test_unparsable_or_unknown_label_is_manual(lora_env: Mock, raw: str) -> None:
    lora_env.return_value = raw
    result = classify(ENDPOINTS['GET', '/public/health'], ERD, CONTROLLER)
    assert result.label == Label.MANUAL_REVIEW_REQUIRED
    lora_env.assert_called_once()  # no llm fallback for a bad model answer


def test_confidence_threshold(lora_env: Mock, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BLADE_LORA_MIN_CONFIDENCE', '0.88')
    lora_env.return_value = reply('public', 0.85)
    result = classify(ENDPOINTS['GET', '/public/health'], ERD, CONTROLLER)
    assert result.label == Label.MANUAL_REVIEW_REQUIRED and 'below the LoRA threshold' in result.evidence
    lora_env.return_value = reply('public', 0.9)
    assert classify(ENDPOINTS['GET', '/public/health'], ERD, CONTROLLER).label == Label.PUBLIC


def test_membership_is_demoted_with_original_label(lora_env: Mock) -> None:
    lora_env.return_value = reply('membership_required')
    result = classify(ENDPOINTS['GET', '/premium/content'], ERD, CONTROLLER)
    assert result.label == Label.MANUAL_REVIEW_REQUIRED and result.allowed_membership == []
    assert 'label=membership_required' in result.evidence and 'AGENTS.md v2.9' in result.evidence


@pytest.mark.parametrize('key,label,lookup', [
    (('GET', '/orders/{orderId}'), 'owner_match', dict(table='orders', id_col='id', owner_col='user_id', tenant_col=None)),
    (('DELETE', '/orders/{orderId}'), 'owner_match', dict(table='orders', id_col='id', owner_col='user_id', tenant_col=None)),
    (('GET', '/orgs/{orgId}/docs'), 'tenant_match', dict(table='orgs', id_col='id', owner_col=None, tenant_col='id')),
])
def test_rules_fill_object_parameters_without_llm(lora_env: Mock, key, label: str, lookup: dict) -> None:
    lora_env.return_value = reply(label)
    endpoint = ENDPOINTS[key]
    result = classify(endpoint, ERD, CONTROLLER)
    assert result.label == label and result.object_param == endpoint.path_params[0]
    assert result.owner_lookup.model_dump() == lookup
    lora_env.assert_called_once()  # only the LoRA call
    policy = build_policy(endpoint, result)
    assert policy.status == 'PENDING' and policy.params.owner_lookup.model_dump() == lookup


def test_missing_fields_go_to_llm_with_fixed_label(lora_env: Mock) -> None:
    filled = dict(label='role_required', confidence=0.9, evidence='e', object_param=None, owner_lookup=None,
                  roles=['admin'], allowed_membership=[])
    lora_env.side_effect = [reply('role_required'), json.dumps(filled)]
    result = classify(ENDPOINTS['GET', '/admin/reports'], ERD, CONTROLLER)
    assert result.label == Label.ROLE_REQUIRED and result.roles == ['admin']
    system, user = lora_env.call_args.args
    assert 'fixed the label to role_required' in system
    assert json.loads(user)['fixed_label'] == 'role_required' and json.loads(user)['fields_to_fill'] == ['roles']
    assert lora_env.call_args.kwargs['response_schema']['properties']['label'] == {'type': 'string', 'enum': ['role_required']}


def test_llm_disagreeing_or_empty_leaves_manual(lora_env: Mock) -> None:
    other = dict(label='public', confidence=0.9, evidence='e', object_param=None, owner_lookup=None, roles=[], allowed_membership=[])
    lora_env.side_effect = [reply('role_required'), json.dumps(other)]
    result = classify(ENDPOINTS['GET', '/admin/reports'], ERD, CONTROLLER)
    assert result.label == Label.MANUAL_REVIEW_REQUIRED and 'role_required requires roles' in result.evidence


def test_owner_col_required(lora_env: Mock) -> None:
    erd = parse_erd('CREATE TABLE orders (id INTEGER PRIMARY KEY, total INTEGER);')
    lora_env.side_effect = [reply('owner_match'), llm.LLMError('no llm configured')]
    result = classify(ENDPOINTS['GET', '/orders/{orderId}'], erd, CONTROLLER)
    assert result.label == Label.MANUAL_REVIEW_REQUIRED and 'owner_lookup.owner_col' in result.evidence


def test_tenant_col_required(lora_env: Mock) -> None:
    lora_env.side_effect = [reply('tenant_match'), llm.LLMError('no llm configured')]
    result = classify(ENDPOINTS['GET', '/orders/{orderId}'], ERD, CONTROLLER)
    assert result.label == Label.MANUAL_REVIEW_REQUIRED and 'owner_lookup.tenant_col' in result.evidence


def test_handler_roles() -> None:
    assert param_extractor.handler_roles("if 'admin' not in current_user.roles: raise") == ['admin']
    assert param_extractor.handler_roles('@PreAuthorize("hasRole(\'ADMIN\')")') == ['admin']
    assert param_extractor.handler_roles("@Roles('editor', 'admin')") == ['editor', 'admin']
    assert param_extractor.handler_roles("if (req.user.role === 'manager') next()") == ['manager']
    assert param_extractor.handler_roles('if user.is_admin: pass') == ['admin']
    assert param_extractor.handler_roles('return db.get(id)') == []


def test_unreachable_lora_falls_back_to_llm(lora_env: Mock, caplog: pytest.LogCaptureFixture) -> None:
    llm_answer = json.dumps(dict(label='public', confidence=0.95, evidence='llm path', object_param=None,
                                 owner_lookup=None, roles=[], allowed_membership=[]))
    lora_env.side_effect = [llm.LLMError('ollama transport failure after 3 attempts'), llm_answer]
    result = classify(ENDPOINTS['GET', '/public/health'], ERD, CONTROLLER)
    assert result.label == Label.PUBLIC and result.evidence == 'llm path'
    assert 'falling back to the llm classifier' in caplog.text
    assert 'settings' not in lora_env.call_args.kwargs


def test_missing_prompt_falls_back(lora_env: Mock, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv('BLADE_LORA_PROMPT_PATH', str(tmp_path / 'absent.md'))
    lora_env.return_value = json.dumps(dict(label='public', confidence=0.95, evidence='llm path', object_param=None,
                                            owner_lookup=None, roles=[], allowed_membership=[]))
    assert classify(ENDPOINTS['GET', '/public/health'], ERD, CONTROLLER).evidence == 'llm path'
