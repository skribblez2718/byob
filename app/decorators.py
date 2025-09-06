from __future__ import annotations

from functools import wraps
from typing import Callable, Any

from flask import jsonify
from flask_login import current_user, login_required


def admin_required(fn: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if not getattr(current_user, "is_admin", False):
            return jsonify({"error": "forbidden", "message": "admin required"}), 403
        return fn(*args, **kwargs)

    return wrapper


def mfa_required(fn: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        # Check MFA status from database instead of session
        if not getattr(current_user, "mfa_passed", False):
            return jsonify({"error": "forbidden", "message": "mfa required"}), 403
        return fn(*args, **kwargs)

    return wrapper
