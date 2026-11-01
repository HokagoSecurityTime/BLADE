import copy

from training.data.enrich_candidates import recover, resolve_pointer


ROW = {'id': 'example', 'method': 'GET', 'path': '/a/{id}'}


def test_security_override_and_absence_are_distinct():
    spec = {'openapi': '3.0.0', 'security': [{'oauth': ['write']}],
            'paths': {'/a/{id}': {'get': {'security': []}}}}
    untouched = copy.deepcopy(spec)
    result = recover(spec, ROW, 'x.yaml', 'sha')
    assert result['security']['origin'] == 'operation'
    assert result['security']['effective'] == []
    assert result['security']['anonymous_alternative'] is True
    assert spec == untouched
    del spec['paths']['/a/{id}']['get']['security']
    assert recover(spec, ROW, 'x.yaml', 'sha')['security']['origin'] == 'global'
    del spec['security']
    security = recover(spec, ROW, 'x.yaml', 'sha')['security']
    assert security['origin'] == 'unspecified'
    assert security['effective'] is None and security['anonymous_alternative'] is None


def test_swagger_nested_refs_cycle_external_and_exact_evidence():
    spec = {'swagger': '2.0', 'paths': {'/a/{id}': {'get': {
        'description': 'Only the creator may view this object.',
        'parameters': [{'in': 'body', 'schema': {'$ref': '#/definitions/A~1B~0C'}}],
        'responses': {'200': {'schema': {'$ref': '#/definitions/A~1B~0C'}},
                      'default': {'description': 'Unknown error'}}}}},
        'definitions': {'A/B~C': {'properties': {
            'Poster': {'properties': {'UserID': {'type': 'string', 'description': 'Original poster identifier'}}},
            'self': {'$ref': '#/definitions/A~1B~0C'},
            'external': {'$ref': 'https://example.invalid/schema.json'}}}}}
    result = recover(spec, ROW, 'source.yaml', 'abc')
    assert result['spec_version'] == '2.0'
    ref = result['references']['#/definitions/A~1B~0C']
    assert ref['properties']['Poster']['properties']['UserID']['type'] == 'string'
    assert {r['reason'] for r in result['unresolved_references']} == {'cycle', 'external_or_missing'}
    for fact in result['facts']:
        assert resolve_pointer(spec, fact['json_pointer']) == fact['text']
    assert any(f['kind'] == 'response_error_or_default' for f in result['facts'])
    assert result['verified_erd'] is None


def test_oas_request_response_and_scopes_do_not_flatten():
    spec = {'openapi': '3.1.0', 'paths': {'/a/{id}': {'get': {
        'security': [{'OAuth': ['records:write']}],
        'requestBody': {'content': {'application/json': {'schema': {'oneOf': [{'type':'string'}, {'type':'number'}]}}}},
        'responses': {'200': {'description':'Response description'}}}}},
        'components': {'securitySchemes': {'OAuth': {'type': 'oauth2', 'flows': {'implicit': {'scopes': {'records:write':'May modify records'}}}}}}}
    result = recover(spec, ROW, 'x', 'y')
    assert len(result['trees']['requestBody']['content']['application/json']['schema']['oneOf']) == 2
    assert any(f['text'] == 'May modify records' and f['kind'] == 'security_scope' for f in result['facts'])
    assert 'original_extraction_hash_unavailable' in result['revision_verification']


def test_missing_operation_is_explicit():
    assert recover({'paths': {}}, ROW, 'x', 'y')['status'] == 'operation_not_found'
