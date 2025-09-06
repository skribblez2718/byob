from __future__ import annotations

# Re-export common schema classes for convenient imports
from .categories import CategoryCreate, CategoryUpdate  # noqa: F401
from .posts import PostCreate, PostUpdate  # noqa: F401
from .resume import (  # noqa: F401
    ResumeSkillInput,
    WorkAccomplishmentInput,
    WorkHistoryInput,
    CertificationInput,
    ProfessionalDevelopmentInput,
    ResumePayload,
)

__all__ = [
    # categories
    "CategoryCreate",
    "CategoryUpdate",
    # posts
    "PostCreate",
    "PostUpdate",
    # resume
    "ResumeSkillInput",
    "WorkAccomplishmentInput",
    "WorkHistoryInput",
    "CertificationInput",
    "ProfessionalDevelopmentInput",
    "ResumePayload",
]
