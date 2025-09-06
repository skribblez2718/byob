from __future__ import annotations

import secrets


def generate_hex_id(length: int = 32) -> str:
    """Generate a secure random hex string of specified length."""
    return secrets.token_hex(length // 2)


# Import all models to maintain compatibility
from app.models.user import User
from app.models.blog import Category, Post
from app.models.resume import (
    ResumeSkill,
    WorkHistory,
    WorkAccomplishment,
    Certification,
    ProfessionalDevelopment,
    Education,
)
from app.models.project import Project

__all__ = [
    "generate_hex_id",
    "User",
    "Category",
    "Post",
    "ResumeSkill",
    "WorkHistory",
    "WorkAccomplishment",
    "Certification",
    "ProfessionalDevelopment",
    "Education",
    "Project",
]
