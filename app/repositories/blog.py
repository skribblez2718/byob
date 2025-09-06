from __future__ import annotations

from typing import Optional

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.blog import Category, Post


# Category repositories
def get_category_by_slug(slug: str) -> Optional[Category]:
    return db.session.execute(db.select(Category).filter_by(slug=slug)).scalar_one_or_none()


def list_categories() -> list[Category]:
    return list(db.session.execute(db.select(Category).order_by(Category.display_order, Category.name)).scalars())


def get_category_by_id(category_id: int) -> Optional[Category]:
    return db.session.execute(db.select(Category).filter_by(id=category_id)).scalar_one_or_none()


def get_category_by_hex_id(hex_id: str) -> Optional[Category]:
    return db.session.execute(db.select(Category).filter_by(hex_id=hex_id)).scalar_one_or_none()


def create_category(*, name: str, slug: str, description: str | None, display_order: int) -> Category:
    cat = Category(name=name, slug=slug, description=description, display_order=display_order)
    db.session.add(cat)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("slug_conflict")
    return cat


def update_category(cat: Category, *, name: str, slug: str, description: str | None, display_order: int) -> Category:
    cat.name = name
    cat.slug = slug
    cat.description = description
    cat.display_order = display_order
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("slug_conflict")
    return cat


def delete_category(cat: Category) -> None:
    db.session.delete(cat)
    db.session.commit()


# Post repositories
def get_post_by_slug(slug: str) -> Optional[Post]:
    return db.session.execute(db.select(Post).filter_by(slug=slug)).scalar_one_or_none()


def get_post_by_id(post_id: int) -> Optional[Post]:
    return db.session.execute(db.select(Post).filter_by(id=post_id)).scalar_one_or_none()


def get_post_by_hex_id(hex_id: str) -> Optional[Post]:
    return db.session.execute(db.select(Post).filter_by(hex_id=hex_id)).scalar_one_or_none()


def list_posts(page: int = 1, per_page: int = 10) -> tuple[list[Post], int]:
    stmt = db.select(Post).order_by(Post.created_at.desc())
    pag = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
    return list(pag.items), pag.total


def list_posts_by_category(
    category_slug: str,
    page: int = 1,
    per_page: int = 10,
) -> tuple[list[Post], int]:
    cat = get_category_by_slug(category_slug)
    if not cat:
        return [], 0
    stmt = db.select(Post).filter_by(category_id=cat.id).order_by(Post.created_at.desc())
    pag = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
    return list(pag.items), pag.total


def create_post(
    *,
    title: str,
    slug: str,
    excerpt: str | None,
    category_id: int | None,
    author_id: int,
    content_blocks: list[dict] | None = None,
) -> Post:
    p = Post(
        title=title,
        slug=slug,
        excerpt=excerpt,
        category_id=category_id,
        author_id=author_id,
    )
    # Persist content blocks if provided
    if content_blocks is not None:
        p.content_blocks = content_blocks
    db.session.add(p)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("slug_conflict")
    return p


def update_post(
    p: Post,
    *,
    title: str,
    slug: str,
    excerpt: str | None,
    category_id: int | None,
    content_blocks: list[dict] | None = None,
) -> Post:
    p.title = title
    p.slug = slug
    p.excerpt = excerpt
    p.category_id = category_id
    if content_blocks is not None:
        p.content_blocks = content_blocks
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("slug_conflict")
    return p


def delete_post(p: Post) -> None:
    db.session.delete(p)
    db.session.commit()




def set_post_image(p: Post, *, image_data: bytes, image_mime: str) -> Post:
    p.image_data = image_data
    p.image_mime = image_mime
    db.session.add(p)
    db.session.commit()
    return p
