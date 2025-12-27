import os
import json
from typing import Optional, Tuple

DB_DIR = 'db'


def store_payload(username: str, app_name: str, user_password: str, payload: dict) -> str:
    # simple file-based storage
    app_dir = os.path.join(DB_DIR, username, app_name)
    os.makedirs(app_dir, exist_ok=True)
    filename = os.path.join(app_dir, 'secret.json')
    with open(filename, 'w') as f:
        json.dump(payload, f)
    return filename


def retrieve_latest_payload(username: str, app_name: str, user_password: str) -> Optional[Tuple[str, str]]:
    filename = os.path.join(DB_DIR, username, app_name, 'secret.json')
    if not os.path.exists(filename):
        return None
    with open(filename, 'r') as f:
        data = f.read()
    return (data, filename)
