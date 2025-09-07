from __future__ import annotations

from typing import Optional

from app.extensions import db
from app.models.project import Project


def get_project_by_id(project_id: int) -> Optional[Project]:
    """Fetch a single project by id"""
    return db.session.execute(db.select(Project).filter_by(id=project_id)).scalar_one_or_none()


def get_project_by_hex_id(hex_id: str) -> Optional[Project]:
    """Fetch a single project by hex_id"""
    return db.session.execute(db.select(Project).filter_by(hex_id=hex_id)).scalar_one_or_none()


def update_project(
    project: Project,
    *,
    project_title: str,
    project_description: str | None,
    project_url: str | None,
    project_image_url: str | None = None,
) -> Project:
    """Update fields on a single Project and commit."""
    project.project_title = (project_title or '').strip()
    project.project_description = project_description
    project.project_url = project_url
    if project_image_url is not None:
        project.project_image_url = project_image_url
    db.session.add(project)
    db.session.commit()
    return project


def delete_project(project: Project) -> None:
    """Delete a single project"""
    db.session.delete(project)
    db.session.commit()


def list_project_data(user_id: int) -> list[Project]:
    """Get all projects for a user"""
    return list(
        db.session.execute(
            db.select(Project)
            .filter_by(user_id=user_id)
            .order_by(Project.display_order, Project.id)
        ).scalars()
    )


def create_project(user_id: int, project_data: dict) -> Project:
    """Create a new project for a user"""
    # Get the next display order
    max_order = db.session.execute(
        db.select(db.func.coalesce(db.func.max(Project.display_order), -1))
        .filter_by(user_id=user_id)
    ).scalar()
    
    project = Project(
        user_id=user_id,
        project_image_url=project_data.get("project_image_url"),
        project_title=project_data.get("project_title", "").strip(),
        project_description=project_data.get("project_description"),
        project_url=project_data.get("project_url"),
        display_order=max_order + 1,
    )
    
    db.session.add(project)
    db.session.commit()
    return project


def replace_project_data(user_id: int, projects: list[dict]) -> None:
    """Replace all project data for a user"""
    # Delete existing projects
    db.session.execute(db.delete(Project).filter_by(user_id=user_id))
    
    # Add new projects
    order = 0
    for p in projects:
        db.session.add(
            Project(
                user_id=user_id,
                project_image_url=p.get("project_image_url"),
                project_title=p.get("project_title", "").strip(),
                project_description=p.get("project_description"),
                project_url=p.get("project_url"),
                display_order=order,
            )
        )
        order += 1
    
    # Commit all changes to the database
    db.session.commit()


def reorder_projects(user_id: int, project_hex_ids: list[str]) -> None:
    """Reorder projects by updating their display_order based on the provided hex_id list"""
    # Get all projects for the user
    projects = list(
        db.session.execute(
            db.select(Project)
            .filter_by(user_id=user_id)
        ).scalars()
    )
    
    # Create a mapping of hex_id to project
    project_map = {p.hex_id: p for p in projects}
    
    # Update display_order based on the order in the hex_ids list
    for order, hex_id in enumerate(project_hex_ids):
        if hex_id in project_map:
            project_map[hex_id].display_order = order
    
    # Commit the changes
    db.session.commit()
