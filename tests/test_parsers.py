import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from pipeline.parsers.erd import parse_erd
from pipeline.parsers.oas import parse_oas


ROOT = Path(__file__).resolve().parents[1]


def test_demo_oas() -> None:
    endpoints = parse_oas((ROOT / 'demo_backend/openapi.json').read_text(encoding='utf-8'))
    assert {(e.method, e.path) for e in endpoints} == {
        ('GET', '/public/health'), ('GET', '/orders/{orderId}'),
        ('DELETE', '/orders/{orderId}'), ('GET', '/users/{userId}'),
        ('GET', '/admin/reports'), ('GET', '/orgs/{orgId}/docs'),
        ('GET', '/premium/content'),
    }
    assert len(endpoints) == 7
    order = next(e for e in endpoints if e.method == 'GET' and e.path == '/orders/{orderId}')
    assert order.path_params == ['orderId']
    assert order.query_params == []
    assert order.operation_id


def test_demo_erd() -> None:
    tables = parse_erd((ROOT / 'demo_backend/schema.sql').read_text(encoding='utf-8'))
    assert tables['orders'].owner_col == 'user_id'
    assert tables['orders'].pk == ['id']
    assert tables['orders'].fks[0].ref_table == 'users'
    assert tables['orders'].fks[0].ref_columns == ['id']
    assert tables['users'].tenant_col == 'org_id'
    assert tables['orgs'].tenant_col == 'id'
    assert tables['orgs'].owner_col is None


@pytest.mark.parametrize('serialize', [json.dumps, yaml.safe_dump])
def test_oas_parameters_refs_and_metadata(serialize: Callable[[Any], str]) -> None:
    document = {
        'openapi': '3.1.0',
        'components': {'parameters': {'q/x': {'name': 'search', 'in': 'query'}}},
        'paths': {'/items/{itemId}': {
            'parameters': [{'$ref': '#/components/parameters/q~1x'}],
            'get': {'parameters': [{'name': 'search', 'in': 'query'}, {'name': 'page', 'in': 'query'},
                                   {'name': 'Authorization', 'in': 'header'}],
                    'operationId': 'getItem', 'tags': ['items'], 'summary': 'Read item'},
            'post': {}, 'x-note': 'ignore',
        }},
    }
    get, post = parse_oas(serialize(document))
    assert get.path_params == ['itemId']
    assert get.query_params == ['search', 'page']
    assert (get.operation_id, get.tags, get.summary) == ('getItem', ['items'], 'Read item')
    assert post.query_params == ['search']
    assert post.operation_id is None and post.tags == [] and post.summary is None


@pytest.mark.parametrize('ref', ['https://example.com/params', '#/missing', '#/components/parameters/loop'])
def test_oas_rejects_unresolvable_refs(ref: str) -> None:
    document = {'openapi': '3.0.3', 'components': {'parameters': {'loop': {'$ref': ref}}},
                'paths': {'/x': {'get': {'parameters': [{'$ref': ref}]}}}}
    with pytest.raises(ValueError):
        parse_oas(json.dumps(document))


def test_erd_fk_fallback_and_priority() -> None:
    tables = parse_erd('''
    CREATE TABLE documents (
        id INT PRIMARY KEY,
        writer INT REFERENCES users(id),
        workspace INT,
        CONSTRAINT fk_org FOREIGN KEY (workspace) REFERENCES orgs(id)
    );
    CREATE TABLE priorities (
        author_id INT, created_by INT, owner_id INT, user_id INT,
        company_id INT, organization_id INT, org_id INT, tenant_id INT
    );
    ''')
    assert tables['documents'].owner_col == 'writer'
    assert tables['documents'].tenant_col == 'workspace'
    assert tables['priorities'].owner_col == 'user_id'
    assert tables['priorities'].tenant_col == 'tenant_id'


def test_erd_quotes_comments_composite_keys_and_defaults() -> None:
    tables = parse_erd('''
    -- CREATE TABLE fake (id INT);
    CREATE TABLE "app"."records" (
        "record_id" INT, [version] INT,
        `writer` INT REFERENCES "app"."users"("id"),
        amount DECIMAL(10, 2),
        note TEXT DEFAULT 'commas, REFERENCES users(id); -- literal',
        CHECK (amount IN (1, 2)),
        /* ignored, comment */
        CONSTRAINT pk PRIMARY KEY ("record_id", [version]),
        FOREIGN KEY (record_id, version) REFERENCES revisions(id, version)
    );
    ''')
    info = tables['app.records']
    assert info.pk == ['record_id', 'version']
    assert info.columns == ['record_id', 'version', 'writer', 'amount', 'note']
    assert info.owner_col == 'writer'
    assert info.tenant_col is None
    assert len(info.fks) == 2
    assert info.fks[1].columns == ['record_id', 'version']


@pytest.mark.parametrize('ddl', ['CREATE TABLE x (id INT', 'ALTER TABLE x ADD id INT;',
                                'CREATE TABLE x (id INT, PRIMARY KEY (missing));'])
def test_erd_rejects_unsupported_or_invalid_ddl(ddl: str) -> None:
    with pytest.raises(ValueError):
        parse_erd(ddl)


def test_oas_rejects_old_version() -> None:
    with pytest.raises(ValueError):
        parse_oas('swagger: "2.0"\npaths: {}')
