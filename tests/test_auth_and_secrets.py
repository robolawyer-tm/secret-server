import os
import json
import tempfile
import sys
import pytest
# Ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from web_server import app

@pytest.fixture
def client(tmp_path, monkeypatch):
    # Use a temp server_state and db for tests
    # Use a valid base64 Fernet key for tests
    from cryptography.fernet import Fernet
    os.environ['MASTER_KEY'] = Fernet.generate_key().decode('utf-8')  # ephemeral key for tests
    test_db = tmp_path / 'db'
    test_state = tmp_path / 'server_state'
    monkeypatch.chdir(tmp_path)
    os.makedirs(str(test_db), exist_ok=True)
    os.makedirs(str(test_state), exist_ok=True)

    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_register_login_check_no_password(client):
    # register
    r = client.post('/api/auth/register', json={'username': 'bob', 'password': 'pw'})
    assert r.status_code == 200
    data = r.get_json()
    assert 'password' not in data
    # login
    r = client.post('/api/auth/login', json={'username': 'bob', 'password': 'pw'})
    assert r.status_code == 200
    data = r.get_json()
    assert 'password' not in data
    # check
    r = client.get('/api/auth/check')
    assert r.status_code == 200
    assert r.get_json().get('authenticated') is True


def test_secret_flow_with_session_credentials(client):
    # register and login
    client.post('/api/auth/register', json={'username': 'carol', 'password': 's3'})
    client.post('/api/auth/login', json={'username': 'carol', 'password': 's3'})
    # store should succeed now
    r = client.post('/api/secrets/store', json={'app_name': 'demo', 'secret_text': 'top', 'passphrase': 'p'},)
    assert r.status_code == 200
    j = r.get_json()
    assert j.get('success') is True

    # retrieve
    r = client.post('/api/secrets/retrieve', json={'app_name': 'demo', 'passphrase': 'p'})
    assert r.status_code == 200
    jr = r.get_json()
    assert jr.get('success') is True
    assert jr.get('secret') == 'top'

    # logout then store should fail
    client.post('/api/auth/logout')
    r = client.post('/api/secrets/store', json={'app_name': 'demo', 'secret_text': 'x', 'passphrase': 'p'})
    assert r.status_code == 401
