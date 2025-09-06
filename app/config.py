from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env if present
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
561

class Config:
    SECRET_KEY: str = os.getenv("SECRET_KEY", os.urandom(32).hex())

    SITE_NAME=os.getenv("SITE_NAME", "Site Name")

    # Database
    # Read from environment and then unset for security
    SQLALCHEMY_DATABASE_URI: str | None = os.environ.pop("DATABASE_URL", None)
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Ensure we use the 'blog' schema in Postgres
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "options": "-c search_path=blog"
        }
    }


    # Sessions - Production security settings
    SESSION_COOKIE_HTTPONLY = True   # Prevent XSS access to session cookies
    SESSION_COOKIE_SECURE = os.getenv("FLASK_ENV", "production") == "production"  # HTTPS only in production
    SESSION_COOKIE_SAMESITE = "Strict"  # CSRF protection while allowing normal navigation
    SESSION_COOKIE_DOMAIN = None     # Let Flask auto-detect
    SESSION_COOKIE_PATH = "/"        # Explicit path
    # 4 hours absolute session age as per spec
    ABSOLUTE_SESSION_MAX_AGE_SECONDS = int(os.getenv("ABSOLUTE_SESSION_MAX_AGE_SECONDS", str(4 * 60 * 60)))

    # Uploads and limits
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(5 * 1024 * 1024)))

    # Caching (simple for dev)
    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")

    # Rate limiting
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "100 per minute")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")

    # Security headers
    # Use {nonce} placeholder for per-request nonce substitution in app.security.apply_security_headers
    SECURITY_CSP = (
        "default-src 'self'; "
        # Scripts: use nonce and strict-dynamic; omit 'self' to avoid browser warning
        "script-src 'nonce-{nonce}' 'strict-dynamic' ;"
        # Styles from self only - no external CDNs used
        "style-src 'self'; "
        # Images from self and inline SVGs
        "img-src 'self'; "
        # Webfonts from self only - no external CDNs used
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    )
    SECURITY_HSTS_SECONDS = 31536000
    
    # Permissions Policy - restrict dangerous browser features not needed by the blog
    SECURITY_PERMISSIONS_POLICY = (
        "geolocation=(), microphone=(), camera=(), payment=(), usb=(), "
        "magnetometer=(), gyroscope=(), accelerometer=(), ambient-light-sensor=(), "
        "autoplay=(), encrypted-media=(), fullscreen=(), midi=(), "
        "picture-in-picture=(), sync-xhr=(), web-share=()"
    )

    # TOTP issuer label
    TOTP_ISSUER = os.getenv("TOTP_ISSUER", "portfolio_blog")

    # Flask env
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV != "production"
