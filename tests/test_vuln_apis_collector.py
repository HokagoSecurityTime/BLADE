"""Collector tests use source text only; no vulnerable application imports."""
import json
from pathlib import Path

from training.data.sources.vuln_apis import (
    collect, commit, java_routes, javascript_routes, location, python_handler,
    python_signals, vulnerability_docs,
)


def test_python_operation_mapping_never_imports(tmp_path):
    repo = tmp_path / 'VAmPI'
    (repo / 'api_views').mkdir(parents=True)
    target = repo / 'api_views/users.py'
    target.write_text("raise RuntimeError('MUST NOT EXECUTE')\n\ndef owned():\n    return session.query(Item).filter(Item.owner_id == current_user.id)\n", encoding='utf-8')
    mapped = python_handler(repo, 'api_views.users.owned')
    assert mapped['start_line'] == 3
    assert mapped['file'] == 'api_views/users.py'
    hints = python_signals(repo, 'api_views.users.owned', 'GET', '/owned/{id}')
    assert hints['owner_filter'] is True
    assert python_handler(repo, 'api_views.users.missing') is None


def test_java_comments_not_routes_and_prefix(tmp_path):
    target = tmp_path / 'Example.java'
    target.write_text('''// @GetMapping("/fake")
@RequestMapping("/identity/api")
public class Example {
  /* @PostMapping("/also-fake") */
  @GetMapping("/vehicles/{vehicleId}")
  public Object find() { return service.find(); }
}
''', encoding='utf-8')
    rows = java_routes(target, tmp_path)
    assert [(r['method'], r['path']) for r in rows] == [('GET', '/identity/api/vehicles/{vehicleId}')]
    assert rows[0]['source']['start_line'] == 5
    assert rows[0]['signals'] is None


def test_js_chains_reference_handler_and_ignore_comment(tmp_path):
    route = tmp_path / 'routes.js'
    route.write_text('''const controller = require('./controller');
// app.delete('/fake', bad)
router.route('/v2/notes/:noteId').get(controller.read).delete(controller.remove);
''', encoding='utf-8')
    (tmp_path / 'controller.js').write_text('exports.read = function(req, res) { return res.send(1); };\nexports.remove = function(req, res) { return res.send(2); };\n', encoding='utf-8')
    rows = javascript_routes(route, tmp_path)
    assert {(r['method'], r['path']) for r in rows} == {('GET', '/v2/notes/{noteId}'), ('DELETE', '/v2/notes/{noteId}')}
    assert all(r['handler_sources'] for r in rows)
    assert all(r['source']['start_line'] == 3 for r in rows)
    assert next(r for r in rows if r['method'] == 'DELETE')['handler_sources'][0]['start_line'] == 2
    assert all(len(r['handler_sources']) == 1 for r in rows)


def test_excerpt_bound_and_endpoint_specific_doc(tmp_path):
    source = tmp_path / 'source.py'
    source.write_text('\n'.join(f'line {n}' for n in range(70)), encoding='utf-8')
    excerpt = location(source, tmp_path, 12, 65, 'handler')
    assert len(excerpt['excerpt'].splitlines()) == 30
    assert excerpt['end_line'] == 41
    (tmp_path / 'README.md').write_text('This is a vulnerable API.\nGET /secret/{id} has IDOR.\nGET /safe has examples.\n', encoding='utf-8')
    assert vulnerability_docs(tmp_path, '/secret/{id}')[0]['line'] == 2
    assert vulnerability_docs(tmp_path, '/safe') == []
    assert vulnerability_docs(tmp_path, '/') == []


def test_js_object_export_handler_body_signals(tmp_path):
    route = tmp_path / 'routes.js'
    route.write_text("const controller = require('./controller');\nrouter.get('/owned/:id', controller.read);\n", encoding='utf-8')
    (tmp_path / 'controller.js').write_text('module.exports = { read: (req, res) => { return res.status(403).send(); } };', encoding='utf-8')
    row = javascript_routes(route, tmp_path)[0]
    assert row['handler_sources'][0]['file'] == 'controller.js'
    assert row['signals']['has_auth_check'] is True


def test_collect_unknown_not_false_and_no_labels(tmp_path):
    repo = tmp_path / 'VAmPI'
    (repo / 'openapi_specs').mkdir(parents=True)
    (repo / 'openapi_specs/openapi3.yml').write_text(json.dumps({'openapi': '3.0.0', 'paths': {'/missing/{id}': {'get': {'operationId': 'missing.handler'}}}}), encoding='utf-8')
    rows = collect(repo)
    assert len(rows) == 1
    assert set(rows[0]['controller_signals'].values()) == {None}
    assert rows[0]['proposed_label'] is None and rows[0]['confirmed_label'] is None
    assert rows[0]['meta']['source_mapped'] is False


def test_commit_read_only_packed_ref(tmp_path):
    (tmp_path / '.git').mkdir()
    (tmp_path / '.git/HEAD').write_text('ref: refs/heads/main\n')
    (tmp_path / '.git/packed-refs').write_text('a' * 40 + ' refs/heads/main\n')
    assert commit(tmp_path) == 'a' * 40
