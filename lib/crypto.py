import base64

class CryptoResult:
    def __init__(self, ok: bool, data: bytes = b"", status: str = ""):
        self.ok = ok
        self.data = data
        self.status = status
    def __str__(self):
        # represent encrypted data as base64 string
        return base64.b64encode(self.data).decode('utf-8')


def encrypt_secret(plaintext: str, passphrase: str) -> CryptoResult:
    # NOTE: This is a simple placeholder for tests only. Do not use in production.
    try:
        data = plaintext.encode('utf-8')
        return CryptoResult(True, data=data)
    except Exception as e:
        return CryptoResult(False, status=str(e))


def decrypt_secret(encrypted_text: str, passphrase: str) -> CryptoResult:
    try:
        data = base64.b64decode(encrypted_text.encode('utf-8'))
        return CryptoResult(True, data=data)
    except Exception as e:
        return CryptoResult(False, status=str(e))
