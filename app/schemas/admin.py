from __future__ import annotations

# Backward-compatible re-exports for previously flat admin schema module
# New split modules live alongside this file.

from app.schemas.categories import CategoryCreate, CategoryUpdate  # noqa: F401
from app.schemas.posts import PostCreate, PostUpdate  # noqa: F401
from app.schemas.resume import (  # noqa: F401
    ResumeSkillInput,
    WorkAccomplishmentInput,
    WorkHistoryInput,
    CertificationInput,
    ProfessionalDevelopmentInput,
    ResumePayload,
)
