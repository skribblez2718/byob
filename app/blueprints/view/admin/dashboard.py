from __future__ import annotations

from flask import render_template

from app.decorators import admin_required, mfa_required
from app.repositories.blog import list_categories, list_posts

from app.blueprints.admin import bp


@bp.get("/")
@admin_required
@mfa_required
def dashboard():
    """HTML-based admin dashboard"""
    cats = list_categories()
    posts, total = list_posts(page=1, per_page=5)
    return render_template(
        "admin/dashboard.html",
        categories=cats,
        posts=posts,
        total_posts=total,
    )
