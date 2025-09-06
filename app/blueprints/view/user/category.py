from __future__ import annotations

from flask import render_template, request, jsonify, abort

from app.extensions import limiter
from app.repositories.blog import list_posts_by_category

from app.blueprints.blog import bp


@bp.get("/category/<slug>", endpoint="category")
@limiter.limit("120 per minute")
def by_category(slug: str):
    from app.repositories.blog import get_category_by_slug

    category = get_category_by_slug(slug)
    if not category:
        if request.args.get("format") == "json":
            return jsonify({"error": "not_found"}), 404
        abort(404)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(50, max(1, int(request.args.get("per_page", 10))))
    posts, total = list_posts_by_category(slug, page=page, per_page=per_page)

    if request.args.get("format") == "json":
        items = [
            {
                "id": p.id,
                "title": p.title,
                "slug": p.slug,
                "excerpt": p.excerpt,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in posts
        ]
        return jsonify({"status": "ok", "page": "category", "slug": slug, "items": items, "total": total, "page": page, "per_page": per_page})
    pages = max(1, (total + per_page - 1) // per_page)
    return render_template(
        "category.html",
        slug=slug,
        category=category,
        posts=posts,
        page=page,
        per_page=per_page,
        total=total,
        pages=pages,
    )
