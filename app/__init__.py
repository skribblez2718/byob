from __future__ import annotations

import os
from datetime import timedelta, datetime
from typing import Any, Dict

import click
from flask import Flask, jsonify, g, request, session
from flask_login import current_user

from app.config import Config
from app.extensions import (
    db,
    migrate,
    login_manager,
    csrf,
    limiter,
    cache,
)
from app.security import apply_security_headers
from app.models.user import User  # ensure models imported for migrations
from app.utils.crypto import hash_password
from app.utils.html_sanitizer import sanitize_html, sanitize_blog_paragraph


def create_app(config_overrides: Dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # Load config
    app.config.from_object(Config())
    if config_overrides:
        app.config.update(config_overrides)

    # Apply session configuration from Config class
    app.permanent_session_lifetime = timedelta(minutes=int(os.getenv("SESSION_LIFETIME_MINUTES", "30")))
    
    # Ensure session cookie settings are applied from config
    app.config['SESSION_COOKIE_HTTPONLY'] = app.config.get('SESSION_COOKIE_HTTPONLY', True)
    app.config['SESSION_COOKIE_SECURE'] = app.config.get('SESSION_COOKIE_SECURE', False)
    app.config['SESSION_COOKIE_SAMESITE'] = app.config.get('SESSION_COOKIE_SAMESITE', 'Strict')

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)

    # Rate limiter (in-memory for dev). Strict on auth/admin
    limiter.init_app(app)
    
    # Ensure admin user exists (auto-create from env vars if needed)
    with app.app_context():
        try:
            from app.utils.admin_setup import ensure_admin_user
            ensure_admin_user()
        except Exception as e:
            app.logger.error(f"Failed to ensure admin user: {str(e)}")
    
    # Configure HTTP client with the correct base URL
    if app.config.get('SERVER_NAME'):
        scheme = 'https' if app.config.get('PREFERRED_URL_SCHEME', 'http') == 'https' else 'http'
        app.config['HTTP_CLIENT_BASE_URL'] = f"{scheme}://{app.config['SERVER_NAME']}"
    else:
        app.config['HTTP_CLIENT_BASE_URL'] = 'http://localhost:8000'

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:  # type: ignore[name-defined]
        try:
            from app.models.user import User
            from app.utils.db_retry import safe_db_operation
            return safe_db_operation(db.session.get, User, int(user_id))
        except Exception as e:
            current_app.logger.error(f"Error loading user {user_id}: {str(e)}")
            return None
        
    # Template context processor for JS modules and script nonce
    @app.context_processor
    def template_context() -> dict:
        default_modules = {
            "admin_resume": False,
            "admin_blog": False,
            "admin_projects": False,
            "admin_dashboard": False,
        }
        
        # Merge with any module flags set in g.js_modules
        if hasattr(g, 'js_modules') and isinstance(g.js_modules, dict):
            default_modules.update(g.js_modules)
            
        return {
            "js_modules": default_modules,
            "page_scripts": [],
            "page_external_scripts": [],
            "script_nonce": getattr(g, "script_nonce", ""),
        }

    login_manager.login_view = "auth.login"

    # Register template filters for HTML sanitization
    @app.template_filter('safe_html')
    def safe_html_filter(html_content: str) -> str:
        """Template filter to sanitize HTML content for safe rendering."""
        from markupsafe import Markup
        return Markup(sanitize_html(html_content or ""))
    
    @app.template_filter('safe_paragraph')
    def safe_paragraph_filter(paragraph_content: str) -> str:
        """Template filter to sanitize paragraph content for safe rendering."""
        from markupsafe import Markup
        return Markup(sanitize_blog_paragraph(paragraph_content or ""))

    # Request context enrichment for logging and absolute session timeout enforcement
    @app.before_request
    def add_request_context() -> None:
        g.request_id = request.headers.get("X-Request-ID") or os.urandom(8).hex()
        # Per-request script nonce for CSP-compliant inline allowances (used on script tags)
        g.script_nonce = os.urandom(16).hex()
        # Absolute session timeout: end session if exceeded
        abs_max = app.config.get("ABSOLUTE_SESSION_MAX_AGE_SECONDS")
        if abs_max:
            now = int(datetime.utcnow().timestamp())
            start = session.get("_login_time")
            # If login time isn't set but user is authenticated, set it now
            if start is None and current_user.is_authenticated:
                session["_login_time"] = now
            elif isinstance(start, int) and now - start > int(abs_max):
                session.clear()

    # Security headers
    @app.after_request
    def set_headers(resp):
        return apply_security_headers(resp)

    # Blueprints
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.blog import bp as blog_bp
    from app.blueprints.admin import bp as admin_bp
    from app.blueprints.api.admin.resume import bp as admin_resume_bp
    from app.blueprints.api.admin.projects import bp as admin_projects_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(blog_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(admin_resume_bp)
    app.register_blueprint(admin_projects_bp)

    # Health route
    @app.get("/health")
    def health():
        try:
            db.session.execute(db.text("SELECT 1"))
            db_ok = "connected"
        except Exception:
            db_ok = "error"
        return jsonify({"status": "ok", "db": db_ok}), 200

    # Error handlers (JSON per spec)
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "bad_request", "message": str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "unauthorized", "message": str(e)}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "forbidden", "message": str(e)}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not_found", "message": "resource not found"}), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"error": "rate_limited", "message": "too many requests"}), 429

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "server_error", "message": "internal server error"}), 500


    # CLI: create admin user
    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username: str, password: str) -> None:
        with app.app_context():
            if db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none():
                click.echo("User already exists")
                return
            user = User(
                username=username,
                email="",  # Email not required for admin user
                password_hash=hash_password(password),
                is_admin=True,
            )
            db.session.add(user)
            db.session.commit()
            click.echo("Admin user created")

    return app
