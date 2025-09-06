from __future__ import annotations

import json
import os
import secrets
from typing import Iterable, Tuple

import pyotp
from flask import current_app

from app.extensions import db
from app.models.user import User
from app.repositories.user import (
    get_user_by_username,
    increment_failed_login_attempts,
    reset_failed_login_attempts,
    increment_failed_mfa_attempts,
    reset_failed_mfa_attempts,
    is_user_login_locked,
    is_user_mfa_locked,
)
from app.utils.crypto import (
    encrypt_bytes,
    decrypt_bytes,
    hash_password,
    verify_password,
    hash_backup_code,
    verify_backup_code,
)


def find_user_by_username(username: str) -> User | None:
    return get_user_by_username(username)


def authenticate(username: str, password: str) -> Tuple[User | None, str | None]:
    """
    Authenticate user with rate limiting.
    Returns (user, error_message) tuple.
    """
    user = find_user_by_username(username)
    if not user:
        return None, "Invalid username or password"
    
    # Check if user is locked out from login attempts
    if is_user_login_locked(user):
        from datetime import datetime, timezone
        lockout_time = user.login_locked_until
        current_time = datetime.now(timezone.utc)
        
        # Handle timezone compatibility
        if lockout_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=None)
        
        remaining_seconds = (lockout_time - current_time).total_seconds()
        
        # If lockout has expired, reset and continue
        if remaining_seconds <= 0:
            reset_failed_login_attempts(user)
        else:
            remaining_minutes = max(1, int(remaining_seconds / 60))
            # Cap at 15 minutes to prevent display errors
            remaining_minutes = min(remaining_minutes, 15)
            return None, f"Account locked due to 3 failed login attempts. Please try again in {remaining_minutes} minutes."
    
    # Verify password
    if not verify_password(password, user.password_hash):
        increment_failed_login_attempts(user)
        attempts_remaining = 3 - user.failed_login_attempts
        if attempts_remaining > 0:
            return None, f"Invalid username or password. {attempts_remaining} attempts remaining before account lockout."
        else:
            return None, "Invalid username or password. Account has been locked for 15 minutes due to too many failed attempts."
    
    # Successful login - reset failed attempts
    reset_failed_login_attempts(user)
    return user, None


def verify_mfa_with_rate_limiting(user: User, code: str) -> Tuple[bool, str | None]:
    """
    Verify MFA code with rate limiting.
    Returns (success, error_message) tuple.
    """
    # Check if user is locked out from MFA attempts
    if is_user_mfa_locked(user):
        from datetime import datetime, timezone
        remaining_seconds = (user.mfa_locked_until - datetime.now(timezone.utc)).total_seconds()
        
        # If lockout has expired, reset and continue
        if remaining_seconds <= 0:
            reset_failed_mfa_attempts(user)
        else:
            remaining_minutes = max(1, int(remaining_seconds / 60))
            # Cap at 15 minutes to prevent display errors
            remaining_minutes = min(remaining_minutes, 15)
            return False, f"MFA locked due to 3 failed attempts. Please try again in {remaining_minutes} minutes."
    
    # Verify the code
    if verify_totp_code(user, code):
        reset_failed_mfa_attempts(user)
        return True, None
    
    # Failed MFA attempt
    increment_failed_mfa_attempts(user)
    attempts_remaining = 3 - user.failed_mfa_attempts
    if attempts_remaining > 0:
        return False, f"Invalid MFA code. {attempts_remaining} attempts remaining before MFA lockout."
    else:
        return False, "Invalid MFA code. MFA has been locked for 15 minutes due to too many failed attempts."


def ensure_totp_secret(user: User) -> Tuple[str, str]:
    """Ensure user has a TOTP secret. Returns (base32_secret, otpauth_uri)."""
    if user.totp_secret_encrypted:
        secret_b32 = decrypt_bytes(user.totp_secret_encrypted).decode("utf-8")
    else:
        secret_b32 = pyotp.random_base32()
        user.totp_secret_encrypted = encrypt_bytes(secret_b32.encode("utf-8"))
        db.session.add(user)
        db.session.commit()
    issuer = current_app.config.get("TOTP_ISSUER", "portfolio_blog")
    otp_uri = pyotp.totp.TOTP(secret_b32).provisioning_uri(name=user.email, issuer_name=issuer)
    return secret_b32, otp_uri


def verify_totp_code(user: User, code: str) -> bool:
    if not user.totp_secret_encrypted:
        return False

    # Normalize input: remove spaces and trim
    try:
        normalized = (code or "").strip().replace(" ", "")
    except Exception:
        return False
    if not normalized.isdigit() or len(normalized) < 6:
        return False

    secret_b32 = decrypt_bytes(user.totp_secret_encrypted).decode("utf-8")
    totp = pyotp.TOTP(secret_b32)

    # Use pyotp's built-in verification with a small valid_window to tolerate slight skew
    # valid_window=1 allows previous/next step
    return bool(totp.verify(normalized, valid_window=1))


def generate_backup_codes(n: int = 8) -> list[str]:
    return [secrets.token_hex(4) for _ in range(n)]  # 8 hex chars (~32 bits)


def set_backup_codes(user: User, codes: Iterable[str]) -> None:
    hashed = [hash_backup_code(c) for c in codes]
    user.backup_codes_hash = json.dumps(hashed)
    db.session.add(user)
    db.session.commit()


def consume_backup_code(user: User, code: str) -> bool:
    if not user.backup_codes_hash:
        return False
    try:
        hashes: list[str] = json.loads(user.backup_codes_hash)
    except Exception:
        return False
    idx = next((i for i, h in enumerate(hashes) if verify_backup_code(code, h)), None)
    if idx is None:
        return False
    # Remove used code
    hashes.pop(idx)
    user.backup_codes_hash = json.dumps(hashes)
    db.session.add(user)
    db.session.commit()
    return True
