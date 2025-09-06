from __future__ import annotations

from flask import render_template, request, jsonify

from app.extensions import limiter
from app.repositories.blog import list_posts

from app.blueprints.blog import bp


@bp.get("/")
@limiter.limit("120 per minute")
def home():
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(50, max(1, int(request.args.get("per_page", 10))))
    posts, total = list_posts(page=page, per_page=per_page)
    if request.args.get("format") == "json":
        items = [
            {
                "id": p.id,
                "title": p.title,
                "slug": p.slug,
                "excerpt": p.excerpt,
                "category": p.category.name if p.category else None,
                "created_at": p.created_at.isoformat(),
            }
            for p in posts
        ]
        return jsonify({"posts": items, "total": total, "page": page, "per_page": per_page})

    pages = (total + per_page - 1) // per_page
    return render_template(
        "home.html",
        posts=posts,
        page=page,
        per_page=per_page,
        total=total,
        pages=pages,
    )
