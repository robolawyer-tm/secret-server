import base64
import os
from typing import Optional

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet


class CryptoResult:
    def __init__(self, ok: bool, data: bytes = b"", status: str = ""):
        self.ok = ok
        self.data = data
        self.status = status

    def __str__(self):
        # represent encrypted data as base64 string
        return base64.b64encode(self.data).decode('utf-8')


# Crypto parameters
_SALT_SIZE = 16  # bytes
_KDF_ITERATIONS = 600_000  # PBKDF2 iterations (adjustable)


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 32-byte key from the given passphrase and salt using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_KDF_ITERATIONS,
        backend=default_backend(),
    )
    key = kdf.derive(passphrase.encode('utf-8'))
    # Fernet expects a URL-safe base64-encoded 32-byte key
    return base64.urlsafe_b64encode(key)


def encrypt_secret(plaintext: str, passphrase: str) -> CryptoResult:
    """Encrypt plaintext using a key derived from the passphrase.

    Returns a CryptoResult whose `data` is (salt || fernet_token) as raw bytes.
    The `__str__` method encodes that to base64 for safe JSON/text transport.
    """
    if passphrase is None or passphrase == "":
        return CryptoResult(False, status="Passphrase required")

    try:
        salt = os.urandom(_SALT_SIZE)
        fernet_key = _derive_key(passphrase, salt)
        f = Fernet(fernet_key)
        token = f.encrypt(plaintext.encode('utf-8'))
        return CryptoResult(True, data=salt + token)
    except Exception as e:
        return CryptoResult(False, status=str(e))


def decrypt_secret(encrypted_text: str, passphrase: str) -> CryptoResult:
    """Decrypt a base64-encoded (salt || token) value using the passphrase."""
    if passphrase is None or passphrase == "":
        return CryptoResult(False, status="Passphrase required")

    try:
        combined = base64.b64decode(encrypted_text.encode('utf-8'))
        if len(combined) <= _SALT_SIZE:
            return CryptoResult(False, status="Invalid encrypted payload")
        salt = combined[:_SALT_SIZE]
        token = combined[_SALT_SIZE:]
        fernet_key = _derive_key(passphrase, salt)
        f = Fernet(fernet_key)
        plaintext = f.decrypt(token)
        return CryptoResult(True, data=plaintext)
    except Exception as e:
        return CryptoResult(False, status=str(e))
