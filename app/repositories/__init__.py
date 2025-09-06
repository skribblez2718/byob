# Import all repository functions to maintain compatibility
from app.repositories.user import (
    get_user_by_username,
    get_user_by_hex_id,
    increment_failed_login_attempts,
    reset_failed_login_attempts,
    increment_failed_mfa_attempts,
    reset_failed_mfa_attempts,
    is_user_login_locked,
    is_user_mfa_locked,
    clear_all_lockouts,
)
from app.repositories.blog import (
    get_category_by_hex_id,
    get_post_by_hex_id,
)
from app.repositories.resume import (
    get_resume_skill_by_hex_id,
    get_work_history_by_hex_id,
    get_work_accomplishment_by_hex_id,
    get_certification_by_hex_id,
    get_professional_development_by_hex_id,
    get_education_by_hex_id,
)
from app.repositories.project import (
    get_project_by_hex_id,
)

__all__ = [
    # User repositories
    "get_user_by_username",
    "get_user_by_hex_id",
    "increment_failed_login_attempts",
    "reset_failed_login_attempts",
    "increment_failed_mfa_attempts",
    "reset_failed_mfa_attempts",
    "is_user_login_locked",
    "is_user_mfa_locked",
    "clear_all_lockouts",
    # Blog repositories
    "get_category_by_hex_id",
    "get_post_by_hex_id",
    # Resume repositories
    "get_resume_skill_by_hex_id",
    "get_work_history_by_hex_id",
    "get_work_accomplishment_by_hex_id",
    "get_certification_by_hex_id",
    "get_professional_development_by_hex_id",
    "get_education_by_hex_id",
    # Project repositories
    "get_project_by_hex_id",
]
