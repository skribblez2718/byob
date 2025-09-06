from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
import secrets


def generate_hex_id(length: int = 32) -> str:
    """Generate a secure random hex string of specified length."""
    return secrets.token_hex(length // 2)


class Category(db.Model):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    hex_id: Mapped[str] = mapped_column(db.String(32), unique=True, nullable=False, index=True, default=generate_hex_id)
    name: Mapped[str] = mapped_column(db.String(80), nullable=False)
    slug: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(db.Text, nullable=True)
    display_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(db.DateTime(timezone=True), onupdate=func.now())

    posts: Mapped[list["Post"]] = relationship(back_populates="category")

    __table_args__ = (
        Index("ix_categories_display_order", "display_order"),
    )


class Post(db.Model):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    hex_id: Mapped[str] = mapped_column(db.String(32), unique=True, nullable=False, index=True, default=generate_hex_id)
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    slug: Mapped[str] = mapped_column(db.String(220), unique=True, nullable=False, index=True)
    content_blocks: Mapped[list[dict] | None] = mapped_column(db.JSON, nullable=True)
    excerpt: Mapped[str | None] = mapped_column(db.String(300), nullable=True)
    image_data: Mapped[bytes | None] = mapped_column(db.LargeBinary, nullable=True)
    image_mime: Mapped[str | None] = mapped_column(db.String(100), nullable=True)
    category_id: Mapped[int | None] = mapped_column(db.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    author_id: Mapped[int] = mapped_column(db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(db.DateTime(timezone=True), onupdate=func.now())
    
    author: Mapped["User"] = relationship(back_populates="posts")
    category: Mapped[Category | None] = relationship(back_populates="posts")


