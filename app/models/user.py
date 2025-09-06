from __future__ import annotations

from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models import generate_hex_id


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    hex_id: Mapped[str] = mapped_column(db.String(32), unique=True, nullable=False, index=True, default=generate_hex_id)
    username: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    totp_secret_encrypted: Mapped[bytes | None] = mapped_column(db.LargeBinary, nullable=True)
    backup_codes_hash: Mapped[str | None] = mapped_column(db.Text, nullable=True)
    is_admin: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Authentication state tracking
    mfa_passed: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    mfa_setup_completed: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(db.DateTime(timezone=True), nullable=True)
    
    # Rate limiting fields
    failed_login_attempts: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    login_locked_until: Mapped[datetime | None] = mapped_column(db.DateTime(timezone=True), nullable=True)
    failed_mfa_attempts: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    mfa_locked_until: Mapped[datetime | None] = mapped_column(db.DateTime(timezone=True), nullable=True)

    posts: Mapped[list["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")

    def get_id(self) -> str:  # Flask-Login compatibility
        return str(self.id)
