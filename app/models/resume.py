from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models import generate_hex_id


class ResumeSkill(db.Model):
    __tablename__ = "resume_skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    hex_id: Mapped[str] = mapped_column(db.String(32), unique=True, nullable=False, index=True, default=generate_hex_id)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_title: Mapped[str] = mapped_column(db.String(120), nullable=False)
    skill_description: Mapped[str] = mapped_column(db.Text, nullable=False)
    display_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False, index=True)


class WorkHistory(db.Model):
    __tablename__ = "work_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    hex_id: Mapped[str] = mapped_column(db.String(32), unique=True, nullable=False, index=True, default=generate_hex_id)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    work_history_image_url: Mapped[str | None] = mapped_column(db.String(300), nullable=True)
    work_history_company_name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    work_history_dates: Mapped[str] = mapped_column(db.String(120), nullable=False)
    work_history_role: Mapped[str] = mapped_column(db.String(200), nullable=False)
    work_history_role_description: Mapped[str] = mapped_column(db.Text, nullable=True)
    display_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False, index=True)

    accomplishments: Mapped[list["WorkAccomplishment"]] = relationship(
        back_populates="work_history", cascade="all, delete-orphan", order_by="WorkAccomplishment.display_order"
    )


class WorkAccomplishment(db.Model):
    __tablename__ = "work_accomplishments"

    id: Mapped[int] = mapped_column(primary_key=True)
    hex_id: Mapped[str] = mapped_column(db.String(32), unique=True, nullable=False, index=True, default=generate_hex_id)
    work_history_id: Mapped[int] = mapped_column(db.ForeignKey("work_history.id", ondelete="CASCADE"), nullable=False, index=True)
    accomplishment_text: Mapped[str] = mapped_column(db.Text, nullable=False)
    display_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False, index=True)

    work_history: Mapped[WorkHistory] = relationship(back_populates="accomplishments")


class Certification(db.Model):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    hex_id: Mapped[str] = mapped_column(db.String(32), unique=True, nullable=False, index=True, default=generate_hex_id)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    certification_image_url: Mapped[str | None] = mapped_column(db.String(300), nullable=True)
    certification_title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    certification_description: Mapped[str] = mapped_column(db.Text, nullable=True)
    display_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False, index=True)


class ProfessionalDevelopment(db.Model):
    __tablename__ = "professional_development"

    id: Mapped[int] = mapped_column(primary_key=True)
    hex_id: Mapped[str] = mapped_column(db.String(32), unique=True, nullable=False, index=True, default=generate_hex_id)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    professional_development_image_url: Mapped[str | None] = mapped_column(db.String(300), nullable=True)
    professional_development_title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    professional_development_description: Mapped[str] = mapped_column(db.Text, nullable=True)
    display_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False, index=True)


class Education(db.Model):
    __tablename__ = "education"

    id: Mapped[int] = mapped_column(primary_key=True)
    hex_id: Mapped[str] = mapped_column(db.String(32), unique=True, nullable=False, index=True, default=generate_hex_id)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    education_image_url: Mapped[str | None] = mapped_column(db.String(300), nullable=True)
    education_title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    education_description: Mapped[str | None] = mapped_column(db.Text, nullable=True)
    display_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False, index=True)
