from __future__ import annotations

from flask import render_template, request, jsonify, abort

from app.extensions import limiter
from app.repositories.blog import get_post_by_slug

from app.blueprints.blog import bp


@bp.get("/post/<slug>", endpoint="post")
@limiter.limit("120 per minute")
def post_detail(slug: str):
    p = get_post_by_slug(slug)
    if not p:
        if request.args.get("format") == "json":
            return jsonify({"error": "not_found"}), 404
        abort(404)
    if request.args.get("format") == "json":
        return jsonify({
            "status": "ok",
            "page": "post",
            "post": {
                "id": p.id,
                "title": p.title,
                "slug": p.slug,
                "content_blocks": p.content_blocks or [],
                "excerpt": p.excerpt,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            },
        })
    return render_template("post.html", post=p)
