from __future__ import annotations

from flask import render_template, request, jsonify, abort

from app.extensions import limiter
from app.repositories.blog import list_categories, list_posts, get_post_by_slug, list_posts_by_category

from app.blueprints.blog import bp


@bp.get("/blog")
@limiter.limit("120 per minute")
def blog():
    """Blog listing page"""
    page = request.args.get('page', 1, type=int)
    per_page = 6
    
    categories = list_categories()
    posts, total = list_posts(page=page, per_page=per_page)
    
    if request.args.get("format") == "json":
        posts_data = [
            {
                "id": p.id,
                "title": p.title,
                "slug": p.slug,
                "excerpt": p.excerpt,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "category": {
                    "name": p.category.name,
                    "slug": p.category.slug
                } if p.category else None
            }
            for p in posts
        ]
        categories_data = [
            {
                "name": c.name,
                "slug": c.slug,
                "description": c.description,
                "display_order": c.display_order,
            }
            for c in categories
        ]
        return jsonify({
            "status": "ok", 
            "page": "blog", 
            "posts": posts_data,
            "categories": categories_data,
            "total": total,
            "current_page": page
        })
    
    return render_template(
        "blog.html", 
        categories=categories, 
        posts=posts, 
        total=total, 
        page=page, 
        per_page=per_page
    )


@bp.get("/blog/<slug>")
@limiter.limit("120 per minute")
def post_detail(slug: str):
    """Individual blog post page"""
    post = get_post_by_slug(slug)
    if not post:
        abort(404)
    
    # Get related posts from same category
    related_posts = []
    if post.category:
        related_posts, _ = list_posts_by_category(
            post.category.slug, 
            page=1, 
            per_page=3
        )
        # Remove current post from related posts
        related_posts = [p for p in related_posts if p.id != post.id][:3]
    
    if request.args.get("format") == "json":
        return jsonify({
            "status": "ok",
            "post": {
                "id": post.id,
                "title": post.title,
                "slug": post.slug,
                "content_blocks": post.content_blocks or [],
                "excerpt": post.excerpt,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "updated_at": post.updated_at.isoformat() if post.updated_at else None,
                "category": {
                    "name": post.category.name,
                    "slug": post.category.slug
                } if post.category else None,
                "author": {
                    "username": post.author.username
                }
            },
            "related_posts": [
                {
                    "title": p.title,
                    "slug": p.slug,
                    "excerpt": p.excerpt
                }
                for p in related_posts
            ]
        })
    
    return render_template(
        "blog_post.html", 
        post=post, 
        related_posts=related_posts
    )


@bp.get("/blog/category/<slug>")
@limiter.limit("120 per minute")
def by_category(slug: str):
    """Blog posts by category"""
    page = request.args.get('page', 1, type=int)
    per_page = 6
    
    posts, total = list_posts_by_category(slug, page=page, per_page=per_page)
    categories = list_categories()
    
    # Find current category
    current_category = None
    for cat in categories:
        if cat.slug == slug:
            current_category = cat
            break
    
    if not current_category:
        abort(404)
    
    if request.args.get("format") == "json":
        posts_data = [
            {
                "id": p.id,
                "title": p.title,
                "slug": p.slug,
                "excerpt": p.excerpt,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in posts
        ]
        return jsonify({
            "status": "ok",
            "category": {
                "name": current_category.name,
                "slug": current_category.slug,
                "description": current_category.description
            },
            "posts": posts_data,
            "total": total,
            "current_page": page
        })
    
    return render_template(
        "blog_category.html", 
        category=current_category,
        posts=posts, 
        categories=categories,
        total=total, 
        page=page, 
        per_page=per_page
    )
