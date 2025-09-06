from __future__ import annotations

from flask import render_template, redirect, url_for, flash
from flask_login import login_user, current_user

from app.services import auth as auth_svc
from app.forms.auth import LoginForm
from app import db
from app.extensions import limiter

from app.blueprints.auth import bp


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute; 20 per hour")
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user, error_message = auth_svc.authenticate(form.username.data, form.password.data)
        if not user:
            flash(error_message or 'Invalid credentials', 'error')
            return render_template("auth/login.html", form=form)

        from datetime import datetime, timezone
        user.last_login = datetime.now(timezone.utc)

        if getattr(user, "is_admin", False):
            user.mfa_passed = False
            db.session.commit()

            login_user(user, remember=False)
            return redirect(url_for('auth.mfa'))

        user.mfa_passed = True
        db.session.commit()
        login_user(user, remember=False)
        return redirect(url_for('blog.home'))

    return render_template("auth/login.html", form=form)
