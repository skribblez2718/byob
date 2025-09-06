from __future__ import annotations

import base64
from hashlib import sha256

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app
import bcrypt


def _fernet() -> Fernet:
    secret = current_app.config.get("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY not configured")
    
    # Ensure consistent string representation regardless of type
    if isinstance(secret, bytes):
        secret_str = secret.decode("utf-8")
    else:
        secret_str = str(secret)
    
    # Derive 32-byte key from SECRET_KEY using SHA-256, then urlsafe base64-encode for Fernet
    key = sha256(secret_str.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_bytes(data: bytes) -> bytes:
    return _fernet().encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    try:
        return _fernet().decrypt(token)
    except InvalidToken as e:
        # Log the error for debugging but don't expose internal details
        current_app.logger.error(f"Fernet decryption failed: {str(e)}")
        raise ValueError("Invalid encrypted data") from e
    except Exception as e:
        # Catch any other encryption-related errors
        current_app.logger.error(f"Unexpected decryption error: {str(e)}")
        raise ValueError("Decryption failed") from e


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def hash_backup_code(code: str) -> str:
    # Backup codes are short; use bcrypt with salt
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(code.encode("utf-8"), salt).decode("utf-8")


def verify_backup_code(code: str, code_hash: str) -> bool:
    try:
        return bcrypt.checkpw(code.encode("utf-8"), code_hash.encode("utf-8"))
    except Exception:
        return False
