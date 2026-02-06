import os
import json
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DB_DIR = 'db'

def _hash_password(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(password.encode('utf-8'))
    return key, salt

def save_auth(username: str, password: str) -> bool:
    user_dir = os.path.join(DB_DIR, username)
    try:
        os.makedirs(user_dir, exist_ok=True)
        auth_file = os.path.join(user_dir, 'auth.json')
        
        key, salt = _hash_password(password)
        
        data = {
            'hash': base64.b64encode(key).decode('utf-8'),
            'salt': base64.b64encode(salt).decode('utf-8'),
            'method': 'pbkdf2:sha256:100000'
        }
        
        with open(auth_file, 'w') as f:
            json.dump(data, f)
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
        
        if 'salt' not in data:
            return False
            
        stored_salt = base64.b64decode(data['salt'])
        stored_hash = base64.b64decode(data['hash'])
        
        derived_key, _ = _hash_password(password, stored_salt)
        return derived_key == stored_hash
    except Exception:
        return False
