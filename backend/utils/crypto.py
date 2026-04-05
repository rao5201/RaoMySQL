"""加密工具：AES-256-GCM 加密/解密 MySQL 连接密码"""
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64, os

def _derive_key(password: str, salt: bytes = b"RaoMySQLSalt2024") -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                     iterations=100000)
    return kdf.derive(password.encode())

def encrypt_password(plain: str, key_raw: str = None) -> str:
    if not plain:
        return ""
    key_raw = key_raw or os.getenv("ENCRYPTION_KEY", "32-byte-encryption-key-here!!")
    key = _derive_key(key_raw)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plain.encode(), None)
    return base64.b64encode(nonce + ct).decode()

def decrypt_password(encrypted: str, key_raw: str = None) -> str:
    if not encrypted:
        return ""
    key_raw = key_raw or os.getenv("ENCRYPTION_KEY", "32-byte-encryption-key-here!!")
    key = _derive_key(key_raw)
    aesgcm = AESGCM(key)
    data = base64.b64decode(encrypted)
    nonce, ct = data[:12], data[12:]
    return aesgcm.decrypt(nonce, ct, None).decode()
