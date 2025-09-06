from __future__ import annotations

import os
from flask import render_template, redirect, url_for, flash, request, current_app, Response
from flask_login import current_user

from app.decorators import admin_required, mfa_required
from app.forms import BlogPostForm
from app.forms.posts import DeletePostForm
from app.repositories.blog import create_post, update_post, get_post_by_hex_id, list_categories, set_post_image, list_posts, delete_post
from app.schemas.posts import PostCreate, PostUpdate
from app.utils.slug import slugify
from app.utils.image import validate_and_rewrite, save_validated_image_to_subdir
import base64
import re

from app.blueprints.admin import bp


def _process_featured_image(file) -> tuple[bytes, str] | tuple[None, None]:
    """Validate and rewrite the uploaded image, returning (bytes, mime)."""
    if not file or file.filename == '':
        return None, None
    data = file.read()
    ok, err, info, rewritten, fmt, suggested_ext, safe_filename = validate_and_rewrite(
        data, original_filename=file.filename
    )
    if not ok or not rewritten:
        raise ValueError(err or "invalid_image")
    mime = info.get("mime", "image/jpeg")
    return rewritten, mime


def _rewrite_inline_images(content_html: str) -> tuple[str, int, list[str]]:
    """Find <img src="data:image/...">, validate+save to static/uploads/blog, replace src with static URL.
    Returns (new_html, saved_count, errors).
    """
    if not content_html:
        return content_html or "", 0, []

    pattern = re.compile(r'<img([^>]+)src=["\'](data:image/[^;]+;base64,([^"\']+))["\']', re.IGNORECASE)
    errors: list[str] = []
    saved = 0

    def repl(match: re.Match) -> str:
        nonlocal saved, errors
        attrs = match.group(1) or ""
        data_url = match.group(2) or ""
        b64_part = match.group(3) or ""
        try:
            data_bytes = base64.b64decode(b64_part, validate=True)
        except Exception:
            errors.append("Invalid image data encountered; skipped one inline image")
            return match.group(0)  # leave unchanged

        ok, err, info, static_path = save_validated_image_to_subdir(
            data_bytes, original_filename=None, subdir="uploads/blog"
        )
        if not ok or not static_path:
            errors.append(f"Image save failed ({err or 'invalid_image'}); skipped one inline image")
            return match.group(0)

        saved += 1
        # Build new <img ... src="/static/<static_path>"
        new_src = url_for('static', filename=static_path)
        return f'<img{attrs}src="{new_src}"'

    new_html = pattern.sub(repl, content_html)
    return new_html, saved, errors


@bp.route("/posts/new", methods=["GET", "POST"])
@admin_required
@mfa_required
def post_new():
    """HTML form to create new blog post"""
    form = BlogPostForm()

    # Populate category choices
    categories = list_categories()
    form.category_id.choices = [(cat.id, cat.name) for cat in categories]

    if form.validate_on_submit():
        try:
            # Build ordered content blocks from form
            blocks: list[dict] = []
            saved_count = 0
            img_errors: list[str] = []
            for entry in form.content_blocks:
                b = entry.form
                if b.delete.data:
                    continue
                b_type = (b.type.data or '').strip()
                order = int(b.order.data or 0)
                if b_type == 'heading':
                    level = int(b.heading_level.data or 2)
                    blocks.append({
                        'type': 'heading', 'level': min(max(level, 2), 5), 'text': (b.text.data or '').strip(), 'order': order
                    })
                elif b_type == 'paragraph':
                    blocks.append({'type': 'paragraph', 'text': (b.text.data or '').strip(), 'order': order})
                elif b_type == 'image':
                    src_url: str | None = None
                    file = b.image.data
                    if file and getattr(file, 'filename', ''):
                        data = file.read()
                        ok, err, info, static_path = save_validated_image_to_subdir(
                            data, original_filename=file.filename, subdir="uploads/blog"
                        )
                        if ok and static_path:
                            src_url = url_for('static', filename=static_path)
                            saved_count += 1
                        else:
                            img_errors.append(f"Image block skipped: {err or 'invalid_image'}")
                    else:
                        # carry existing src if present
                        if b.existing_src.data:
                            src_url = b.existing_src.data
                    if src_url:
                        blocks.append({'type': 'image', 'src': src_url, 'alt': (b.alt.data or '').strip(), 'order': order})
            # sort by order
            blocks.sort(key=lambda x: int(x.get('order', 0)))

            # Validation: require at least one block and at least one paragraph
            if not blocks or not any(b.get('type') == 'paragraph' for b in blocks):
                flash('Post must include at least one paragraph block.', 'danger')
                return render_template(
                    'admin/post_form.html',
                    form=form,
                    title='Create New Blog Post',
                    action_url=url_for('admin.post_new'),
                    page_scripts=["js/admin_post_form.js"],
                )

            payload = PostCreate.model_validate({
                "title": form.title.data,
                "slug": slugify(form.title.data),
                "content_blocks": blocks,
                "excerpt": form.excerpt.data or None,
                "category_id": form.category_id.data,
            })
            new_post = create_post(
                title=payload.title,
                slug=payload.slug,
                excerpt=payload.excerpt or "",
                category_id=payload.category_id,
                author_id=current_user.id,
                content_blocks=blocks,
            )
            for msg in img_errors:
                flash(msg, "warning")
            if saved_count:
                flash(f"Saved {saved_count} inline image(s).", "success")
            
            # Handle featured image upload
            if form.featured_image.data:
                try:
                    image_bytes, image_mime = _process_featured_image(form.featured_image.data)
                    if image_bytes:
                        set_post_image(new_post, image_data=image_bytes, image_mime=image_mime)
                except Exception as img_error:
                    flash(f"Post created but image upload failed: {str(img_error)}", "warning")
            
            flash(f'Blog post "{new_post.title}" created successfully!', "success")
            return redirect(url_for("admin.post_edit", post_hex_id=new_post.hex_id))
        except ValueError as e:
            if str(e) == "slug_conflict":
                flash("A post with this title already exists. Please choose a different title.", "error")
            else:
                flash(f"Error creating post: {str(e)}", "error")
        except Exception as e:
            flash(f"Error creating post: {str(e)}", "error")

    return render_template(
        "admin/post_form.html",
        form=form,
        title="Create New Blog Post",
        action_url=url_for("admin.post_new"),
        page_scripts=["js/admin_post_form.js"],
    )


@bp.route("/posts/<string:post_hex_id>/edit", methods=["GET", "POST"])
@admin_required
@mfa_required
def post_edit(post_hex_id: str):
    """HTML form to edit existing blog post"""
    post = get_post_by_hex_id(post_hex_id)
    if not post:
        flash("Post not found.", "error")
        return redirect(url_for("admin.dashboard"))
    
    form = BlogPostForm(obj=post)
    
    # Populate category choices
    categories = list_categories()
    form.category_id.choices = [(cat.id, cat.name) for cat in categories]
    
    # Set form data for editing
    if request.method == 'GET':
        form.title.data = post.title
        form.excerpt.data = post.excerpt
        form.category_id.data = post.category_id
        form.post_id.data = post.id
        # populate content_blocks
        form.content_blocks.entries = []
        if post.content_blocks:
            for blk in sorted(post.content_blocks, key=lambda x: int(x.get('order', 0))):
                entry = {}
                if blk.get('type') == 'heading':
                    entry = {
                        'type': 'heading',
                        'heading_level': str(min(max(int(blk.get('level', 2)), 2), 5)),
                        'text': blk.get('text', ''),
                        'order': int(blk.get('order', 0)),
                    }
                elif blk.get('type') == 'paragraph':
                    entry = {
                        'type': 'paragraph',
                        'text': blk.get('text', ''),
                        'order': int(blk.get('order', 0)),
                    }
                elif blk.get('type') == 'image':
                    entry = {
                        'type': 'image',
                        'existing_src': blk.get('src', ''),
                        'alt': blk.get('alt', ''),
                        'order': int(blk.get('order', 0)),
                    }
                form.content_blocks.append_entry(entry)

    if form.validate_on_submit():
        try:
            blocks: list[dict] = []
            saved_count = 0
            img_errors: list[str] = []
            for entry in form.content_blocks:
                b = entry.form
                if b.delete.data:
                    continue
                b_type = (b.type.data or '').strip()
                order = int(b.order.data or 0)
                if b_type == 'heading':
                    level = int(b.heading_level.data or 2)
                    blocks.append({'type': 'heading', 'level': min(max(level, 2), 5), 'text': (b.text.data or '').strip(), 'order': order})
                elif b_type == 'paragraph':
                    blocks.append({'type': 'paragraph', 'text': (b.text.data or '').strip(), 'order': order})
                elif b_type == 'image':
                    src_url: str | None = None
                    file = b.image.data
                    if file and getattr(file, 'filename', ''):
                        data = file.read()
                        ok, err, info, static_path = save_validated_image_to_subdir(
                            data, original_filename=file.filename, subdir="uploads/blog"
                        )
                        if ok and static_path:
                            src_url = url_for('static', filename=static_path)
                            saved_count += 1
                        else:
                            img_errors.append(f"Image block skipped: {err or 'invalid_image'}")
                    else:
                        if b.existing_src.data:
                            src_url = b.existing_src.data
                    if src_url:
                        blocks.append({'type': 'image', 'src': src_url, 'alt': (b.alt.data or '').strip(), 'order': order})
            blocks.sort(key=lambda x: int(x.get('order', 0)))

            # Validate with schema
            payload = PostUpdate.model_validate({
                "title": form.title.data,
                "slug": slugify(form.title.data),
                "content_blocks": blocks,
                "excerpt": form.excerpt.data or None,
                "category_id": form.category_id.data,
            })
            updated_post = update_post(
                post,
                title=payload.title,
                slug=payload.slug,
                excerpt=payload.excerpt or "",
                category_id=payload.category_id,
                content_blocks=blocks,
            )
            for msg in img_errors:
                flash(msg, "warning")
            if saved_count:
                flash(f"Saved {saved_count} inline image(s).", "success")
            
            # Handle featured image upload
            if form.featured_image.data:
                try:
                    image_bytes, image_mime = _process_featured_image(form.featured_image.data)
                    if image_bytes:
                        set_post_image(updated_post, image_data=image_bytes, image_mime=image_mime)
                except Exception as img_error:
                    flash(f"Post updated but image upload failed: {str(img_error)}", "warning")
            
            flash(f'Blog post "{updated_post.title}" updated successfully!', "success")
            return redirect(url_for("admin.post_edit", post_hex_id=updated_post.hex_id))
        except ValueError as e:
            if str(e) == "slug_conflict":
                flash("A post with this title already exists. Please choose a different title.", "error")
            else:
                flash(f"Error updating post: {str(e)}", "error")
        except Exception as e:
            flash(f"Error updating post: {str(e)}", "error")

    return render_template(
        "admin/post_form.html",
        form=form,
        post=post,
        title=f"Edit: {post.title}",
        action_url=url_for("admin.post_edit", post_hex_id=post.hex_id),
        page_scripts=["js/admin_post_form.js"],
    )


@bp.route("/posts")
@admin_required
@mfa_required
def posts_list():
    """List all blog posts for admin management"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    posts, total = list_posts(page=page, per_page=per_page)
    
    delete_form = DeletePostForm()
    return render_template(
        "admin/posts_list.html",
        posts=posts,
        total=total,
        page=page,
        per_page=per_page,
        title="Manage Blog Posts",
        delete_form=delete_form,
    )


@bp.post("/posts/<string:post_hex_id>/delete")
@admin_required
@mfa_required
def post_delete(post_hex_id: str):
    form = DeletePostForm()
    if form.validate_on_submit():
        post = get_post_by_hex_id(post_hex_id)
        if not post:
            flash("Post not found.", "error")
            return redirect(url_for("admin.posts_list"))
        # Delete inline images saved under static/uploads/blog referenced by this post
        try:
            blocks = post.content_blocks or []
            rel_paths = set()
            for blk in (blocks or []):
                if isinstance(blk, dict) and blk.get('type') == 'image':
                    src = (blk.get('src') or '').strip()
                    prefix = '/static/uploads/blog/'
                    if src.startswith(prefix):
                        rel_paths.add(src[len('/static/'):])
            for rel in rel_paths:
                try:
                    if os.path.isabs(rel):
                        current_app.logger.warning(f"Refusing to delete absolute path: {rel}")
                        continue
                    safe_rel = rel.lstrip(os.sep)
                    abs_path = os.path.join(current_app.static_folder, safe_rel)
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                except Exception as e:
                    current_app.logger.error(f"Failed to delete blog image {rel}: {e}")
        except Exception as e:
            current_app.logger.error(f"Cleanup error for post {post.hex_id}: {e}")

        delete_post(post)
        flash("Post deleted.", "success")
        return redirect(url_for("admin.posts_list"))
    flash("Invalid delete request.", "error")
    return redirect(url_for("admin.posts_list"))


@bp.route("/posts/<string:post_hex_id>/image")
def post_image(post_hex_id: str):
    """Serve post featured image"""
    post = get_post_by_hex_id(post_hex_id)
    if not post or not post.image_data:
        return "", 404
    
    return Response(
        post.image_data,
        mimetype=post.image_mime or 'image/jpeg',
        headers={
            'Cache-Control': 'public, max-age=31536000',  # Cache for 1 year
            'Content-Disposition': f'inline; filename="post_{post.hex_id}_image"'
        }
    )
