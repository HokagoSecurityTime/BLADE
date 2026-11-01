"""Ensure the harness really writes and selects by the authenticated identity."""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from training.experiments.self_account_binding import ROOT, RAW, build_harness

pytestmark=pytest.mark.skipif(
    not (RAW/'manifest.json').exists() or not (ROOT/'verification/self_account_wheels/manifest.json').exists(),
    reason='Pinned external snapshot and isolated dependencies required')


def test_bob_updates_bob_despite_alice_id():
    app,repo,db=build_harness()
    try:
        with TestClient(app) as client:
            response=client.put('/user?id=1',headers={'x-actor':'bob'},json={'user':{'id':1,'bio':'bob-updated'}})
        assert response.status_code==200
        assert repo.calls[0]['username']=='bob'
        assert db.execute('SELECT bio FROM users WHERE id=1').fetchone()['bio']=='original-alice'
        assert db.execute('SELECT bio FROM users WHERE id=2').fetchone()['bio']=='bob-updated'
    finally:db.close()


def test_rename_keeps_original_database_identity():
    app,repo,db=build_harness()
    try:
        with TestClient(app) as client:
            response=client.put('/user',headers={'x-actor':'bob'},json={'user':{'username':'bob_new','bio':'updated'}})
        assert response.status_code==200
        assert repo.calls[0]['username']=='bob'
        assert repo.calls[0]['new_username']=='bob_new'
        assert db.execute('SELECT username FROM users WHERE id=2').fetchone()['username']=='bob_new'
    finally:db.close()
