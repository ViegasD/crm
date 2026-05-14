import base64
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


def _get_key() -> bytes:
    return base64.b64decode(settings.credential_encryption_key)


def encrypt_payload(data: dict) -> str:
    """Encrypt a dict to a base64 string (AES-256-GCM)."""
    key = _get_key()
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    plaintext = json.dumps(data).encode()
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    # nonce (12 bytes) prepended to ciphertext
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt_payload(encrypted: str) -> dict:
    """Decrypt a base64 string back to a dict."""
    key = _get_key()
    raw = base64.b64decode(encrypted)
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext)
