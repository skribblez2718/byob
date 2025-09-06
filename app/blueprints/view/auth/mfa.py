from __future__ import annotations

from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.services import auth as auth_svc
from app.forms.auth import MFAForm, LoginForm
from app import db
from app.extensions import limiter

from app.blueprints.auth import bp


@bp.route("/mfa", methods=["GET", "POST"])
@login_required
@limiter.limit("10 per minute")
def mfa():
    form = LoginForm()

    if not current_user.is_authenticated:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('auth.login'))

    if not getattr(current_user, 'is_admin', False):
        return redirect(url_for('admin.dashboard'))

    if getattr(current_user, 'mfa_passed', False):
        return redirect(url_for('admin.dashboard'))

    needs_setup = not current_user.mfa_setup_completed

    if needs_setup:
        secret_b32, otp_uri = auth_svc.ensure_totp_secret(current_user)

        form = MFAForm()
        if form.validate_on_submit():
            success, error_message = auth_svc.verify_mfa_with_rate_limiting(current_user, form.code.data)
            if success:
                current_user.mfa_passed = True
                current_user.mfa_setup_completed = True
                db.session.commit()
                flash('MFA setup completed successfully!', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                flash(error_message or 'Invalid authentication code. Please check your authenticator app.', 'error')

        return render_template("auth/mfa.html", form=form, needs_setup=True, 
                             secret=secret_b32, qr_uri=otp_uri, otp_uri=otp_uri)

    else:
        form = MFAForm()

        if form.validate_on_submit():
            success, error_message = auth_svc.verify_mfa_with_rate_limiting(current_user, form.code.data)
            if success:
                current_user.mfa_passed = True
                db.session.commit()
                return redirect(url_for('admin.dashboard'))
            else:
                flash(error_message or 'Invalid authentication code', 'error')

        return render_template("auth/mfa.html", form=form, needs_setup=False)
