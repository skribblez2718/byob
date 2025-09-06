from __future__ import annotations

# Compatibility shim: re-export forms from app.forms package submodules
from app.forms.auth import LoginForm, MFAForm  # noqa: F401
from app.forms.categories import CategoryForm  # noqa: F401
from app.forms.posts import BlogPostForm  # noqa: F401
from app.forms.resume import (  # noqa: F401
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
