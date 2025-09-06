from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models import generate_hex_id


class Project(db.Model):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    hex_id: Mapped[str] = mapped_column(db.String(32), unique=True, nullable=False, index=True, default=generate_hex_id)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_image_url: Mapped[str | None] = mapped_column(db.String(300), nullable=True)
    project_title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    project_description: Mapped[str | None] = mapped_column(db.Text, nullable=True)
    project_url: Mapped[str | None] = mapped_column(db.String(300), nullable=True)
    display_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(db.DateTime(timezone=True), onupdate=func.now())
