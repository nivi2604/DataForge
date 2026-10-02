import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings

def _get_fernet() -> Fernet:
    # Hash the secret_key to guarantee 32 bytes, then base64url encode it for Fernet
    key_bytes = hashlib.sha256(settings.secret_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)

def encrypt_value(value: str) -> str:
    if not value:
        return value
    f = _get_fernet()
    return f.encrypt(value.encode()).decode()

def decrypt_value(encrypted_value: str) -> str:
    if not encrypted_value:
        return encrypted_value
    f = _get_fernet()
    return f.decrypt(encrypted_value.encode()).decode()
