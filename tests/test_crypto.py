import base64
from lib import crypto


def test_encrypt_decrypt_roundtrip():
    res = crypto.encrypt_secret('hello world', 's3cr3t')
    assert res.ok is True
    enc_str = str(res)

    dec = crypto.decrypt_secret(enc_str, 's3cr3t')
    assert dec.ok is True
    assert dec.data.decode('utf-8') == 'hello world'


def test_different_ciphertexts_for_same_passphrase():
    r1 = crypto.encrypt_secret('same', 'p')
    r2 = crypto.encrypt_secret('same', 'p')
    assert r1.ok and r2.ok
    assert str(r1) != str(r2)


def test_wrong_passphrase_fails():
    r = crypto.encrypt_secret('secret', 'good')
    assert r.ok
    dec = crypto.decrypt_secret(str(r), 'bad')
    assert dec.ok is False
