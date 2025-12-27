import os
import json
import hashlib

DB_DIR = 'db'


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def save_auth(username: str, password: str) -> bool:
    user_dir = os.path.join(DB_DIR, username)
    try:
        os.makedirs(user_dir, exist_ok=True)
        auth_file = os.path.join(user_dir, 'auth.json')
        with open(auth_file, 'w') as f:
            json.dump({'password_hash': _hash_password(password)}, f)
        return True
    except Exception:
        return False


def check_auth(username: str, password: str) -> bool:
    auth_file = os.path.join(DB_DIR, username, 'auth.json')
    if not os.path.exists(auth_file):
        return False
    try:
        with open(auth_file, 'r') as f:
            data = json.load(f)
        return data.get('password_hash') == _hash_password(password)
    except Exception:
        return False
