from __future__ import annotations

import os
from typing import Optional

from flask import current_app

from app.extensions import db
from app.models.user import User
from app.utils.crypto import hash_password
from sqlalchemy import inspect


def ensure_admin_user() -> Optional[str]:
    """
    Check if an admin user exists in the database.
    
    This function only checks for existing admin users and logs the status.
    Admin users should be created manually using the 'flask create-admin' CLI command.
    If there's any error during the check, it will be logged but won't prevent app startup.
    
    Returns:
        Status message if no admin user exists, None if admin exists or on error
    """
    try:
        # Skip check if the users table doesn't exist yet (e.g., during initial migrations)
        if not inspect(db.engine).has_table("users"):
            current_app.logger.info("Users table not found yet; skipping admin check")
            return None

        # Check if any admin user already exists
        existing_admin = db.session.execute(
            db.select(User).filter_by(is_admin=True)
        ).scalar_one_or_none()

        if existing_admin:
            current_app.logger.info(f"Admin user found: {existing_admin.username}")
            return None

        current_app.logger.warning(
            "No admin user exists. Create one using: flask create-admin"
        )
        return "No admin user found. Use 'flask create-admin' to create one."

    except Exception as e:
        current_app.logger.error(f"Error checking for admin user: {str(e)}")
        current_app.logger.info("Continuing application startup without admin check")
        return None


def check_admin_user_exists() -> bool:
    """
    Check if any admin user exists in the database.
    
    Returns:
        True if at least one admin user exists, False otherwise
    """
    # If the users table doesn't exist yet, there clearly isn't an admin user
    if not inspect(db.engine).has_table("users"):
        return False

    admin_count = db.session.execute(
        db.select(db.func.count(User.id)).filter_by(is_admin=True)
    ).scalar()

    return admin_count > 0
