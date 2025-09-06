from __future__ import annotations

from flask import redirect, url_for, flash
from flask_login import logout_user, current_user

from app import db

from app.blueprints.auth import bp


@bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        current_user.mfa_passed = False
        db.session.commit()

    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
