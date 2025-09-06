from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.decorators import admin_required, mfa_required
from app.extensions import limiter
from app.repositories.blog import (
    create_category,
    create_post,
    delete_category,
    delete_post,
    get_category_by_slug,
    get_post_by_id,
    get_post_by_slug,
    list_categories,
    list_posts,
    update_category,
    update_post,
    set_post_image,
)
from app.schemas.categories import CategoryCreate, CategoryUpdate
from app.schemas.posts import PostCreate, PostUpdate
from app.utils.image import validate_and_rewrite

bp = Blueprint("admin", __name__)

import app.blueprints.view.admin 
import app.blueprints.api.admin.blog 




@bp.get("/api")
@admin_required
@mfa_required
def api_dashboard():
    """JSON API dashboard (original)"""
    cats = list_categories()
    posts, total = list_posts(page=1, per_page=5)
    return jsonify(
        {
            "status": "ok",
            "page": "admin_dashboard",
            "stats": {"categories": len(cats), "posts": total},
        }
    )


@bp.post("/api/categories")
@limiter.limit("10 per minute; 150 per hour")
@admin_required
@mfa_required
def category_create():
    data = request.get_json(silent=True) or {}
    try:
        payload = CategoryCreate.model_validate(data)
    except Exception:
        return jsonify({"error": "bad_request"}), 400
    try:
        cat = create_category(
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            display_order=payload.display_order,
        )
    except ValueError:
        return jsonify({"error": "conflict", "message": "slug already exists"}), 409
    return jsonify({"status": "ok", "id": cat.id}), 201


@bp.patch("/api/categories/<slug>")
@limiter.limit("10 per minute; 150 per hour")
@admin_required
@mfa_required
def category_update(slug: str):
    cat = get_category_by_slug(slug)
    if not cat:
        return jsonify({"error": "not_found"}), 404
    data = request.get_json(silent=True) or {}
    try:
        payload = CategoryUpdate.model_validate(data)
    except Exception:
        return jsonify({"error": "bad_request"}), 400
    try:
        update_category(cat, name=payload.name, slug=payload.slug, description=payload.description, display_order=payload.display_order)
    except ValueError:
        return jsonify({"error": "conflict", "message": "slug already exists"}), 409
    return jsonify({"status": "ok"}), 200


@bp.delete("/api/categories/<slug>")
@limiter.limit("10 per minute; 150 per hour")
@admin_required
@mfa_required
def category_delete(slug: str):
    cat = get_category_by_slug(slug)
    if not cat:
        return jsonify({"error": "not_found"}), 404
    delete_category(cat)
    return jsonify({"status": "ok"}), 200


@bp.post("/api/posts")
@limiter.limit("10 per minute; 150 per hour")
@admin_required
@mfa_required
def post_create():
    data = request.get_json(silent=True) or {}
    try:
        payload = PostCreate.model_validate(data)
    except Exception:
        return jsonify({"error": "bad_request"}), 400
    try:
        p = create_post(
            title=payload.title,
            slug=payload.slug,
            excerpt=payload.excerpt or "",
            category_id=payload.category_id,
            author_id=current_user.id,
            content_blocks=data.get("content_blocks", []),
        )
    except ValueError:
        return jsonify({"error": "conflict", "message": "slug already exists"}), 409
    return jsonify({"status": "ok", "id": p.id}), 201


# Removed legacy POST /posts route; use /api/posts


@bp.patch("/api/posts/<slug>")
@limiter.limit("10 per minute; 150 per hour")
@admin_required
@mfa_required
def post_update(slug: str):
    p = get_post_by_slug(slug)
    if not p:
        return jsonify({"error": "not_found"}), 404
    data = request.get_json(silent=True) or {}
    try:
        payload = PostUpdate.model_validate(data)
    except Exception:
        return jsonify({"error": "bad_request"}), 400
    try:
        update_post(
            p,
            title=payload.title,
            slug=payload.slug,
            excerpt=payload.excerpt or "",
            category_id=payload.category_id,
            content_blocks=data.get("content_blocks", p.content_blocks or []),
        )
    except ValueError:
        return jsonify({"error": "conflict", "message": "slug already exists"}), 409
    return jsonify({"status": "ok"}), 200


@bp.delete("/api/posts/<slug>")
@limiter.limit("10 per minute; 150 per hour")
@admin_required
@mfa_required
def post_delete_api(slug: str):
    p = get_post_by_slug(slug)
    if not p:
        return jsonify({"error": "not_found"}), 404
    delete_post(p)
    return jsonify({"status": "ok"}), 200


@bp.post("/api/posts/<int:post_id>/image")
@limiter.limit("5 per minute; 50 per hour")
@admin_required
@mfa_required
def post_image_upload(post_id: int):
    if "file" not in request.files:
        return jsonify({"error": "bad_request", "message": "file missing"}), 400
    p = get_post_by_id(post_id)
    if not p:
        return jsonify({"error": "not_found"}), 404
    f = request.files["file"]
    data = f.read()
    ok, err, info, rewritten, fmt, suggested_ext, safe_filename = validate_and_rewrite(
        data, original_filename=f.filename
    )
    if not ok or rewritten is None:
        return jsonify({"error": err or "invalid_image", "info": info}), 400

    p = set_post_image(p, image_data=rewritten, image_mime=info.get("mime"))
    return (
        jsonify(
            {
                "status": "ok",
                "post_id": p.id,
                "format": fmt,
                "suggested_ext": suggested_ext,
                "safe_filename": safe_filename,
                "image_mime": p.image_mime,
            }
        ),
        200,
    )


