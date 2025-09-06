from __future__ import annotations

from flask import jsonify
from flask_login import login_required, current_user

from app.services import auth as auth_svc

from app.blueprints.auth import bp


@bp.route("/setup-mfa", methods=["GET", "POST"])
@login_required
def setup_mfa():
    from flask import request

    if request.method == "GET":
        needs_setup = not current_user.totp_secret_encrypted

        if needs_setup:
            secret_b32, otp_uri = auth_svc.ensure_totp_secret(current_user)
            return jsonify({
                "status": "ok",
                "needs_setup": True,
                "qr_uri": otp_uri,
                "secret": secret_b32,
            })
        else:
            return jsonify({
                "status": "ok",
                "needs_setup": False,
            })

    codes = auth_svc.generate_backup_codes()
    auth_svc.set_backup_codes(current_user, codes)
    return jsonify({"status": "ok", "backup_codes": codes})
