from __future__ import annotations

# Re-export common forms for convenience
from .auth import LoginForm, MFAForm  # noqa: F401
from .categories import CategoryForm  # noqa: F401
from .posts import BlogPostForm  # noqa: F401
from .resume import (  # noqa: F401
    SkillItemForm,
    WorkAccomplishmentForm,
    WorkHistoryItemForm,
    CertificationItemForm,
    ProfessionalDevelopmentItemForm,
    ResumeForm,
)

__all__ = [
    # auth
    "LoginForm",
    "MFAForm",
    # categories
    "CategoryForm",
    # posts
    "BlogPostForm",
    # resume
    "SkillItemForm",
    "WorkAccomplishmentForm",
    "WorkHistoryItemForm",
    "CertificationItemForm",
    "ProfessionalDevelopmentItemForm",
    "ResumeForm",
]
