import os
import json
from cryptography.fernet import Fernet

STATE_DIR = 'server_state'
SESSIONS_DIR = os.path.join(STATE_DIR, 'sessions')
MASTER_KEY_FILE = os.path.join(STATE_DIR, 'master.key')

os.makedirs(SESSIONS_DIR, exist_ok=True)


def _load_master_key() -> bytes:
    # Prefer env var for key
    env_key = os.environ.get('MASTER_KEY')
    if env_key:
        return env_key.encode('utf-8')

    if os.path.exists(MASTER_KEY_FILE):
        with open(MASTER_KEY_FILE, 'rb') as f:
            return f.read().strip()

    # Generate and persist a new key (restrict permissions)
    key = Fernet.generate_key()
    with open(MASTER_KEY_FILE, 'wb') as f:
        f.write(key)
    try:
        os.chmod(MASTER_KEY_FILE, 0o600)
    except Exception:
        pass
    return key


_MASTER_KEY = _load_master_key()
_fernet = Fernet(_MASTER_KEY)


def save_session_credentials(session_id: str, username: str, password: str) -> None:
    # Ensure sessions dir exists for current working directory
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    enc = _fernet.encrypt(password.encode('utf-8')).decode('utf-8')
    data = {'username': username, 'encrypted_password': enc}
    filename = os.path.join(SESSIONS_DIR, session_id + '.json')
    with open(filename, 'w') as f:
        json.dump(data, f)


def get_session_password(session_id: str):
    filename = os.path.join(SESSIONS_DIR, session_id + '.json')
    if not os.path.exists(filename):
        return None
    with open(filename, 'r') as f:
        data = json.load(f)
    enc = data.get('encrypted_password')
    try:
        return _fernet.decrypt(enc.encode('utf-8')).decode('utf-8')
    except Exception:
        return None


def clear_session(session_id: str) -> None:
    filename = os.path.join(SESSIONS_DIR, session_id + '.json')
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass
