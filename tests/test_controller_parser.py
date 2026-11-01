import builtins
import json
from pathlib import Path

import pytest

from pipeline.parsers.controller import parse_controller
from pipeline.parsers.erd import parse_erd
from pipeline.parsers.oas import parse_oas
from pipeline.classifier.prompt import build_user_prompt, system_prompt, SYSTEM_PROMPT

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT/'tests/fixtures/controllers'


def test_vulnerable_backend_has_no_auth() -> None:
    result = parse_controller((ROOT/'demo_backend/main.py').read_text(encoding='utf-8'))
    assert len(result) == 7
    assert all(not row['has_auth_check'] for row in result.values())
    assert 'GET /orders/{orderId}' in result and 'DELETE /orders/{orderId}' in result


def test_fastapi_signals() -> None:
    result = parse_controller((FIXTURES/'fastapi_auth.py').read_text())
    assert len(result) == 3 and all(row['has_auth_check'] for row in result.values())
    assert result['GET /users/{userId}']['admin_bypass']
    assert result['GET /orgs/{orgId}/docs']['tenant_check']
    assert result['GET /orders/{orderId}']['owner_filter']
    assert not result['GET /orders/{orderId}']['admin_bypass']


def test_demo_fixture_changes_only_users_authorization() -> None:
    result = parse_controller((FIXTURES/'demo_with_admin.py').read_text(encoding='utf-8'))
    assert len(result) == 7
    assert result['GET /users/{userId}']['admin_bypass']
    assert sum(row['has_auth_check'] for row in result.values()) == 1


def test_express_and_nest() -> None:
    result = parse_controller((FIXTURES/'express_auth.js').read_text(), 'js')
    assert len(result) == 2
    assert result['GET /users/{userId}']['admin_bypass']
    assert result['GET /orgs/{orgId}/docs']['tenant_check']
    nest = parse_controller('''@Controller('users')
class UsersController {
 @Get(':userId')
 @UseGuards(AuthGuard)
 getUser(userId: string) { if (user.is_admin) return db.get(userId); }
}''', 'ts')
    assert nest['GET /users/{userId}']['has_auth_check']
    assert nest['GET /users/{userId}']['admin_bypass']


def test_express_named_handler_and_middleware() -> None:
    result = parse_controller('''
function auth(req, res, next) { if (!req.user) return res.sendStatus(403); next(); }
const getUser = (req, res) => { if (req.user.roles.includes('admin')) return res.json({}); };
app.get('/users/:id', auth, getUser);
app.get('/health', (req, res) => res.json({ok: true}));
''', 'js')
    assert result['GET /users/{id}']['has_auth_check']
    assert result['GET /users/{id}']['admin_bypass']
    assert not result['GET /health']['has_auth_check']


def test_regex_fallback(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    original = builtins.__import__
    def without_tree(name: str, *args: object, **kwargs: object) -> object:
        if name == 'tree_sitter':
            raise ImportError('optional dependency absent')
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', without_tree)
    result = parse_controller((FIXTURES/'express_auth.js').read_text())
    assert len(result) == 2 and result['GET /users/{userId}']['admin_bypass']
    assert 'regex' in caplog.text
    nest = parse_controller("@Controller('users') class Users { @Get(':id') find() { if (user.is_admin) return true; } }", 'ts')
    assert nest['GET /users/{id}']['admin_bypass']


@pytest.mark.parametrize('source', ['@app.get("/")\ndef broken(', 'puts "hello"', 'not a controller'])
def test_invalid_or_unknown(source: str, caplog: pytest.LogCaptureFixture) -> None:
    assert parse_controller(source) == {}
    assert caplog.records


def test_prompt_scopes_signals_and_off_is_identical(monkeypatch: pytest.MonkeyPatch) -> None:
    endpoints = parse_oas((ROOT/'demo_backend/openapi.json').read_text())
    erd = parse_erd((ROOT/'demo_backend/schema.sql').read_text())
    code = (FIXTURES/'fastapi_auth.py').read_text()
    endpoint = next(e for e in endpoints if e.path == '/users/{userId}')
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'false')
    original = build_user_prompt(endpoint, erd, code)
    assert system_prompt() == SYSTEM_PROMPT
    monkeypatch.setenv('BLADE_PHASE2_ENABLED', 'true')
    structured = json.loads(build_user_prompt(endpoint, erd, code))
    signals = next(v for k, v in structured.items() if k not in json.loads(original))
    assert signals['admin_bypass'] and 'Q4' in system_prompt()
    assert structured['object_bindings'][0]['owner_col'] == 'id'
    missing = next(e for e in endpoints if e.method == 'DELETE')
    assert json.loads(build_user_prompt(missing, erd, code))['controller_text'] is None
    monkeypatch.setenv('BLADE_CONTROLLER_ENABLED', 'false')
    assert build_user_prompt(endpoint, erd, code).encode() == original.encode()
    assert system_prompt() == SYSTEM_PROMPT
