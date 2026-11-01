import sqlite3
import time

import jwt
import pytest
from fastapi.testclient import TestClient
from training.experiments.ownership_backend import create_app


@pytest.fixture
def setup(tmp_path):
    secret = 'development-only-secret-with-at-least-32-bytes'
    path = tmp_path/'ownership.sqlite'
    app = create_app(path, secret)
    with sqlite3.connect(path) as db:
        db.executemany('INSERT INTO profiles VALUES (?,?)', [('alice','A'),('bob','B')])
    def auth(user='alice', key=secret, expires=300):
        token = jwt.encode(dict(sub=user, exp=int(time.time())+expires,
            aud='ownership-experiment',iss='local-development'),key,algorithm='HS256')
        return {'Authorization':'Bearer '+token}
    with TestClient(app) as client:
        yield client, path, auth


def test_persistence_cross_user_update_and_read(setup):
    client,path,auth = setup
    result = client.post('/entries',headers=auth(),json={'title':'original'})
    assert result.status_code == 201
    ident = result.json()['id']
    assert client.get(f'/entries/{ident}',headers=auth('bob')).status_code == 404
    assert client.put(f'/entries/{ident}',headers=auth('bob'),json={'title':'stolen'}).status_code == 404
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT principal,title FROM entries').fetchall() == [('alice','original')]
    assert client.put(f'/entries/{ident}',headers=auth(),json={'title':'updated'}).status_code == 200
    assert client.get(f'/entries/{ident}',headers=auth()).json()['title'] == 'updated'


@pytest.mark.parametrize('owner', ['bob', None, '', "alice' OR 1=1 --"])
def test_create_forgery_never_persists(setup, owner):
    client,path,auth = setup
    assert client.post('/entries',headers=auth(),json={'title':'x','principal':owner}).status_code == 403
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT count(*) FROM entries').fetchone()[0] == 0


def test_collection_filters_before_pagination_and_count(setup):
    client,path,auth = setup
    for user in ['bob','alice','bob','alice','bob']:
        assert client.post('/entries',headers=auth(user),json={'title':user}).status_code == 201
    for offset in [0,1]:
        result = client.get(f'/entries?principal=bob&offset={offset}&limit=1',headers=auth()).json()
        assert result['total'] == 2 and len(result['items']) == 1
        assert result['items'][0]['principal'] == 'alice'
    assert client.get('/entries?offset=2',headers=auth()).json()['items'] == []


def test_subject_comes_from_verified_token_not_client_selector(setup):
    client,path,auth = setup
    assert client.get('/profile?principal=bob',headers={**auth(),'X-User':'bob'}).json() == {'principal':'alice','nickname':'A'}
    assert client.get('/profile').status_code == 401
    assert client.get('/profile',headers=auth(key='different-development-signing-secret-32')).status_code == 401
    assert client.get('/profile',headers=auth(expires=-20)).status_code == 401
    assert client.post('/entries',headers=auth(),json={'title':'x','nested':{'principal':'bob'}}).status_code == 422


def test_owner_transfer_is_rejected(setup):
    client,path,auth = setup
    ident = client.post('/entries',headers=auth(),json={'title':'x','principal':'alice'}).json()['id']
    assert client.put(f'/entries/{ident}',headers=auth(),json={'title':'x','principal':'bob'}).status_code == 403
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT principal FROM entries WHERE id=?',(ident,)).fetchone()[0] == 'alice'
