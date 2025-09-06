from __future__ import annotations

import io
import qrcode
from flask import send_file
from flask_login import login_required, current_user

from app.services import auth as auth_svc

from app.blueprints.auth import bp


@bp.route("/qr-code")
@login_required
def qr_code():
    """Generate QR code for MFA setup"""
    if not current_user.is_authenticated or current_user.mfa_setup_completed:
        return "Unauthorized", 403

    secret_b32, otp_uri = auth_svc.ensure_totp_secret(current_user)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(otp_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png', as_attachment=False)
