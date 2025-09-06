from __future__ import annotations

from flask import current_app, g, request
from werkzeug.wrappers.response import Response


def apply_security_headers(response: Response) -> Response:
    # HSTS (only meaningful over HTTPS)
    hsts_seconds = current_app.config.get("SECURITY_HSTS_SECONDS", 31536000)
    response.headers.setdefault("Strict-Transport-Security", f"max-age={hsts_seconds}; includeSubDomains")

    # Basic security headers
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    
    # XSS Protection (legacy but still recommended for older browsers)
    response.headers.setdefault("X-XSS-Protection", "1; mode=block")
    
    # Permissions Policy - restrict dangerous browser features
    permissions_policy = current_app.config.get("SECURITY_PERMISSIONS_POLICY", 
        "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()")
    response.headers.setdefault("Permissions-Policy", permissions_policy)

    # Cache-Control for sensitive admin/auth routes
    if any(path in request.path for path in ['/admin', '/auth']):
        response.headers.setdefault("Cache-Control", "no-store, no-cache, must-revalidate, private")
        response.headers.setdefault("Pragma", "no-cache")
        response.headers.setdefault("Expires", "0")

    # CSP
    csp = current_app.config.get("SECURITY_CSP")
    if csp:
        # If CSP contains a {nonce} placeholder, substitute with per-request nonce
        try:
            if "{nonce}" in csp and getattr(g, "script_nonce", None):
                csp_value = csp.replace("{nonce}", g.script_nonce)
            else:
                csp_value = csp
        except Exception:
            csp_value = csp
        response.headers.setdefault("Content-Security-Policy", csp_value)

    return response
