from __future__ import annotations

from typing import Optional

from app.extensions import db
from app.models.user import User


def get_user_by_hex_id(hex_id: str) -> Optional[User]:
    return db.session.execute(db.select(User).filter_by(hex_id=hex_id)).scalar_one_or_none()


def get_user_by_username(username: str) -> Optional[User]:
    return db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()


def increment_failed_login_attempts(user: User) -> None:
    """Increment failed login attempts and set lockout if needed."""
    from datetime import datetime, timedelta, timezone
    
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= 3:
        # Since database column is timezone-aware, store as UTC timezone-aware datetime
        lockout_time = datetime.now(timezone.utc) + timedelta(minutes=15)
        user.login_locked_until = lockout_time
    db.session.commit()


def reset_failed_login_attempts(user: User) -> None:
    """Reset failed login attempts and clear lockout."""
    user.failed_login_attempts = 0
    user.login_locked_until = None
    db.session.commit()


def increment_failed_mfa_attempts(user: User) -> None:
    """Increment failed MFA attempts and set lockout if needed."""
    from datetime import datetime, timedelta, timezone
    
    user.failed_mfa_attempts += 1
    if user.failed_mfa_attempts >= 3:
        # Since database column is timezone-aware, store as UTC timezone-aware datetime
        lockout_time = datetime.now(timezone.utc) + timedelta(minutes=15)
        user.mfa_locked_until = lockout_time
    db.session.commit()


def reset_failed_mfa_attempts(user: User) -> None:
    """Reset failed MFA attempts and clear lockout."""
    user.failed_mfa_attempts = 0
    user.mfa_locked_until = None
    db.session.commit()


def is_user_login_locked(user: User) -> bool:
    """Check if user is currently locked out from login attempts."""
    from datetime import datetime, timezone
    
    if user.login_locked_until is None:
        return False
    
    # Always work with UTC for comparison
    current_utc = datetime.now(timezone.utc)
    lockout_time = user.login_locked_until
    
    # Convert lockout time to UTC if it has timezone info
    if lockout_time.tzinfo is not None:
        # Convert to UTC
        lockout_utc = lockout_time.astimezone(timezone.utc)
    else:
        # Assume naive datetime is already UTC
        lockout_utc = lockout_time.replace(tzinfo=timezone.utc)
    
    # Compare timezone-aware datetimes
    if current_utc >= lockout_utc:
        reset_failed_login_attempts(user)
        return False
    
    return True


def is_user_mfa_locked(user: User) -> bool:
    """Check if user is currently locked out from MFA attempts."""
    from datetime import datetime, timezone
    
    if user.mfa_locked_until is None:
        return False
    
    # Always work with UTC for comparison
    current_utc = datetime.now(timezone.utc)
    lockout_time = user.mfa_locked_until
    
    # Since database stores timezone-aware datetimes, convert to UTC properly
    if lockout_time.tzinfo is not None:
        # Convert timezone-aware datetime to UTC
        lockout_utc = lockout_time.astimezone(timezone.utc)
    else:
        # If somehow naive, assume it's UTC
        lockout_utc = lockout_time.replace(tzinfo=timezone.utc)
    
    # Compare timezone-aware datetimes
    if current_utc >= lockout_utc:
        reset_failed_mfa_attempts(user)
        return False
    
    return True


def clear_all_lockouts(user: User) -> None:
    """Clear all lockouts for debugging purposes."""
    user.failed_login_attempts = 0
    user.login_locked_until = None
    user.failed_mfa_attempts = 0
    user.mfa_locked_until = None
    db.session.commit()
