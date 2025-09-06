from __future__ import annotations

from flask import render_template
from flask_login import current_user

from app.extensions import limiter
from app.repositories.project import list_project_data

from app.blueprints.blog import bp


@bp.get("/projects")
@limiter.limit("120 per minute")
def projects():
    # Get projects data from database - assuming admin user ID 1 for now
    # In a real app, you might want to get projects from a specific user or all public projects
    projects_list = []
    try:
        # Get the first admin user's projects (you may want to modify this logic)
        from app.models.user import User
        from app.extensions import db
        admin_user = db.session.execute(db.select(User).filter_by(is_admin=True)).scalar()
        if admin_user:
            projects_list = list_project_data(admin_user.id)
    except Exception:
        # Fallback to empty list if there's any error
        projects_list = []

    return render_template("project.html", projects=projects_list)
