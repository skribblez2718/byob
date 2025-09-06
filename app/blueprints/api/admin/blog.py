from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any

from flask import request, jsonify, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename
from app.utils.image import save_validated_image_to_subdir

from app.decorators import admin_required, mfa_required
from app.extensions import limiter
from app.repositories.blog import (
    create_post,
    update_post,
    get_post_by_id,
    get_post_by_hex_id,
    delete_post,
    list_posts,
    list_categories,
)
from app.utils.slug import slugify
from app.schemas.posts import PostCreate, PostUpdate

from app.blueprints.admin import bp

def _collect_blog_static_images(blocks: list[dict] | None) -> set[str]:
    """Return a set of static relative paths like 'uploads/blog/<file>' found in image blocks.
    We only consider images stored under the static uploads/blog directory.
    """
    results: set[str] = set()
    if not blocks:
        return results
    for blk in blocks:
        try:
            if not isinstance(blk, dict):
                continue
            if blk.get('type') != 'image':
                continue
            src = (blk.get('src') or '').strip()
            if not src:
                continue
            # Expected to be like '/static/uploads/blog/<file>'
            prefix = '/static/uploads/blog/'
            if src.startswith(prefix):
                rel = src[len('/static/'):]
                results.add(rel)
        except Exception:
            continue
    return results

def _delete_static_paths(paths: set[str]):
    """Delete static files given relative paths like 'uploads/blog/<file>'."""
    for rel in paths:
        try:
            if os.path.isabs(rel):
                current_app.logger.warning(f"Refusing to delete absolute path: {rel}")
                continue
            safe_rel = rel.lstrip(os.sep)
            abs_path = os.path.join(current_app.static_folder, safe_rel)
            if os.path.exists(abs_path):
                os.remove(abs_path)
        except Exception as e:
            current_app.logger.error(f"Failed to delete static file {rel}: {e}")



@bp.route("/api/blog/upload-image", methods=["POST"])
@admin_required
@mfa_required
@limiter.limit("10 per minute")
def upload_blog_image():
    """Upload image for blog post content"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        # Validate and persist using centralized image utility
        data = file.read()
        ok, err, info, static_path = save_validated_image_to_subdir(
            data, original_filename=file.filename, subdir="uploads/blog"
        )
        if not ok or not static_path:
            return jsonify({"error": err or "Upload failed"}), 400
        image_url = f"/static/{static_path}"
        return jsonify({
            "success": True,
            "url": image_url,
            "message": "Image uploaded successfully"
        })
    
    except Exception as e:
        current_app.logger.error(f"Blog image upload error: {e}")
        return jsonify({"error": "Upload failed"}), 500


@bp.route("/api/blog/posts", methods=["GET"])
@admin_required
@mfa_required
@limiter.limit("60 per minute")
def list_blog_posts():
    """List all blog posts for admin"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        posts, total = list_posts(page=page, per_page=per_page)
        
        posts_data = []
        for post in posts:
            posts_data.append({
                "id": post.id,
                "hex_id": post.hex_id,
                "title": post.title,
                "slug": post.slug,
                "excerpt": post.excerpt,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "updated_at": post.updated_at.isoformat() if post.updated_at else None,
                "category": {
                    "id": post.category.id,
                    "hex_id": post.category.hex_id,
                    "name": post.category.name
                } if post.category else None,
                "author": {
                    "id": post.author.id,
                    "hex_id": post.author.hex_id,
                    "username": post.author.username
                }
            })
        
        return jsonify({
            "success": True,
            "posts": posts_data,
            "total": total,
            "page": page,
            "per_page": per_page
        })
    
    except Exception as e:
        current_app.logger.error(f"List blog posts error: {e}")
        return jsonify({"error": "Failed to fetch posts"}), 500


@bp.route("/api/blog/posts/<string:post_hex_id>", methods=["GET"])
@admin_required
@mfa_required
@limiter.limit("60 per minute")
def get_blog_post(post_hex_id: str):
    """Get single blog post for editing"""
    try:
        post = get_post_by_hex_id(post_hex_id)
        if not post:
            return jsonify({"error": "Post not found"}), 404
        
        return jsonify({
            "success": True,
            "post": {
                "id": post.id,
                "hex_id": post.hex_id,
                "title": post.title,
                "slug": post.slug,
                "content_blocks": post.content_blocks or [],
                "excerpt": post.excerpt,
                "category_id": post.category_id,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "updated_at": post.updated_at.isoformat() if post.updated_at else None,
                "category": {
                    "id": post.category.id,
                    "hex_id": post.category.hex_id,
                    "name": post.category.name
                } if post.category else None
            }
        })
    
    except Exception as e:
        current_app.logger.error(f"Get blog post error: {e}")
        return jsonify({"error": "Failed to fetch post"}), 500


@bp.route("/api/blog/posts", methods=["POST"])
@admin_required
@mfa_required
@limiter.limit("10 per minute")
def create_blog_post():
    """Create new blog post via API"""
    try:
        data = request.get_json() or {}
        if not data:
            return jsonify({"error": "No data provided"}), 400
        # Auto-slug if not provided
        if not data.get('slug') and data.get('title'):
            data['slug'] = slugify(data['title'])
        # Validate against schema (enforces excerpt and blocks with paragraph)
        payload = PostCreate.model_validate(data)
        post = create_post(
            title=payload.title,
            slug=payload.slug,
            excerpt=payload.excerpt,
            category_id=payload.category_id,
            author_id=current_user.id,
            content_blocks=data.get('content_blocks', [])
        )
        
        return jsonify({
            "success": True,
            "message": "Post created successfully",
            "post": {
                "id": post.id,
                "hex_id": post.hex_id,
                "title": post.title,
                "slug": post.slug,
            }
        })
    
    except ValueError as e:
        if str(e) == "slug_conflict":
            return jsonify({"error": "A post with this title already exists"}), 400
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Create blog post error: {e}")
        return jsonify({"error": "Failed to create post"}), 500


@bp.route("/api/blog/posts/<string:post_hex_id>", methods=["PUT"])
@admin_required
@mfa_required
@limiter.limit("10 per minute")
def update_blog_post(post_hex_id: str):
    """Update existing blog post via API"""
    try:
        post = get_post_by_hex_id(post_hex_id)
        if not post:
            return jsonify({"error": "Post not found"}), 404
        
        data = request.get_json() or {}
        if not data:
            return jsonify({"error": "No data provided"}), 400
        # Merge with existing to satisfy required fields
        merged = {
            'title': data.get('title', post.title),
            'slug': data.get('slug') or slugify(data.get('title', post.title)),
            'excerpt': data.get('excerpt', post.excerpt or ''),
            'category_id': data.get('category_id', post.category_id),
            'content_blocks': data.get('content_blocks', post.content_blocks or []),
        }
        payload = PostUpdate.model_validate(merged)
        updated_post = update_post(
            post,
            title=payload.title,
            slug=payload.slug,
            excerpt=payload.excerpt,
            category_id=payload.category_id,
            content_blocks=merged['content_blocks']
        )
        # Cleanup unreferenced blog images in uploads/blog
        try:
            old_paths = _collect_blog_static_images(post.content_blocks or [])
            new_paths = _collect_blog_static_images(merged['content_blocks'] or [])
            to_delete = old_paths - new_paths
            if to_delete:
                _delete_static_paths(to_delete)
        except Exception as e:
            current_app.logger.error(f"Failed to cleanup old blog images on update: {e}")
        
        return jsonify({
            "success": True,
            "message": "Post updated successfully",
            "post": {
                "id": updated_post.id,
                "hex_id": updated_post.hex_id,
                "title": updated_post.title,
                "slug": updated_post.slug,
            }
        })
    
    except ValueError as e:
        if str(e) == "slug_conflict":
            return jsonify({"error": "A post with this title already exists"}), 400
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Update blog post error: {e}")
        return jsonify({"error": "Failed to update post"}), 500


@bp.route("/api/blog/posts/<string:post_hex_id>", methods=["DELETE"])
@admin_required
@mfa_required
@limiter.limit("5 per minute")
def delete_blog_post(post_hex_id: str):
    """Delete blog post via API"""
    try:
        post = get_post_by_hex_id(post_hex_id)
        if not post:
            return jsonify({"error": "Post not found"}), 404
        # Collect and delete all associated static images under uploads/blog
        try:
            all_paths = _collect_blog_static_images(post.content_blocks or [])
            if all_paths:
                _delete_static_paths(all_paths)
        except Exception as e:
            current_app.logger.error(f"Failed to delete blog images for post {post_hex_id}: {e}")

        delete_post(post)
        
        return jsonify({
            "success": True,
            "message": "Post deleted successfully"
        })
    
    except Exception as e:
        current_app.logger.error(f"Delete blog post error: {e}")
        return jsonify({"error": "Failed to delete post"}), 500
