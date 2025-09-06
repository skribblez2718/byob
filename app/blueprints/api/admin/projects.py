import json
import os
from flask import Blueprint, request, jsonify, current_app
from app.utils.image import save_validated_image_to_subdir
from flask_login import current_user, login_required
from pydantic import ValidationError

from app.decorators import admin_required, mfa_required
from app.schemas.projects import (
    ProjectsPayload,
    ProjectInput,
)
from app.repositories.project import (
    replace_project_data,
    list_project_data,
    create_project,
)
from app.extensions import db

bp = Blueprint('admin_projects', __name__, url_prefix='/api/admin/projects')

@bp.route('', methods=['GET'])
@login_required
@admin_required
@mfa_required
def get_projects_data():
    """Get all projects data for the current admin user"""
    try:
        projects = list_project_data(current_user.id)

        # Serialize models explicitly
        projects_data = [
            {
                'hex_id': p.hex_id,
                'project_title': p.project_title,
                'project_description': p.project_description,
                'project_url': p.project_url,
                'project_image_url': p.project_image_url,
            }
            for p in projects
        ]

        return jsonify({
            'projects': projects_data,
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching projects data: {str(e)}")
        return jsonify({"error": "An error occurred while fetching projects data"}), 500

@bp.route('', methods=['POST'])
@login_required
@admin_required
@mfa_required
def update_projects(projects_data, files): 
    """Update projects data for the current admin user"""
    try:
        
        # Log incoming request for debugging
        current_app.logger.debug(f"Received projects update request: {projects_data}")

        # Helper: strip deleted items in raw dict before validation
        def strip_deleted_items(data: dict) -> dict:
            if not isinstance(data, dict):
                return data
            # Projects
            if isinstance(data.get('projects'), list):
                cleaned_projects = []
                for item in data['projects']:
                    if not isinstance(item, dict) or item.get('delete'):
                        continue
                    # Normalize keys used by forms to schema keys
                    if 'project_image_url' in item and 'image_url' not in item:
                        item['image_url'] = item.get('project_image_url')
                    cleaned_projects.append(item)
                data['projects'] = cleaned_projects
            return data

        projects_data = strip_deleted_items(projects_data)

        # Validate input data against schema
        try:
            payload = ProjectsPayload.model_validate(projects_data)
        except ValidationError as e:
            error_message = "Invalid projects data format"
            current_app.logger.error(f"{error_message}: {e.errors()}")
            return jsonify({
                "error": error_message,
                "details": [{"field": "/".join(map(str, err["loc"])), "message": err["msg"]} 
                           for err in e.errors()]
            }), 400
        
        def delete_image(static_path):
            if not static_path:
                return
            try:
                # Ensure static_path is relative to the static folder
                if os.path.isabs(static_path):
                    current_app.logger.warning(f"Refusing to delete absolute image path: {static_path}")
                    return
                safe_rel = static_path.lstrip(os.sep)
                path = os.path.join(current_app.static_folder, safe_rel)
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                current_app.logger.error(f"Error deleting image {static_path}: {e}")

        # Collect image processing errors to surface to UI
        image_errors: list[dict] = []

        # Process images after validation. Preserve existing image_url when no new file is provided
        # unless the corresponding remove_image flag is set.
        for i, project in enumerate(payload.projects):
            file_key = f'projects-{i}-project_image'
            file = files.get(file_key)
            if file and file.filename:
                image_bytes = file.read()
                ok, err, info, static_path = save_validated_image_to_subdir(image_bytes, file.filename, subdir="uploads/project")
                if ok:
                    project.image_url = static_path
                else:
                    current_app.logger.error(f"Image upload failed for projects[{i}]: {err} {info}")
                    image_errors.append({
                        "field": f"projects/{i}/image",
                        "message": err or "invalid_image",
                        "info": info,
                    })
            else:
                # keep existing unless explicitly removed
                if getattr(project, 'remove_image', False):
                    project.image_url = None

        # If any image errors occurred, return them for UI display
        if image_errors:
            return jsonify({
                "error": "Image validation failed",
                "details": image_errors
            }), 400

        # After successful image processing, delete only images no longer referenced
        try:
            existing_projects_old = list_project_data(current_user.id)
            old_images = set(filter(None, [p.project_image_url for p in existing_projects_old]))
            new_images = set(filter(None, [p.image_url for p in payload.projects]))
            for path in old_images - new_images:
                delete_image(path)
        except Exception as e:
            current_app.logger.error(f"Failed deleting unreferenced images: {e}")

        # Convert Pydantic models to dictionaries for the repository, mapping to DB field names
        projects_data = [
            {
                'project_title': p.project_title,
                'project_description': p.project_description,
                'project_url': p.project_url,
                'project_image_url': p.image_url,
            }
            for p in payload.projects
        ]

        # Save to the database
        try:
            replace_project_data(
                user_id=current_user.id,
                projects=projects_data,
            )
            return jsonify({"message": "Projects updated successfully"}), 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error updating projects: {e}", exc_info=True)
            return jsonify({"error": "A database error occurred."}), 500
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in update_projects: {str(e)}", exc_info=True)
        return jsonify({
            "error": "An unexpected error occurred while processing your request"
        }), 500


@bp.route('/create', methods=['POST'])
@login_required
@admin_required
@mfa_required
def create_single_project(project_data=None, files=None):
    """Create a single new project for the current admin user"""
    try:
        # Use provided data or get from request
        if project_data is None:
            project_data = request.get_json() or {}
        if files is None:
            files = request.files

        # Log incoming request for debugging
        current_app.logger.debug(f"Received project creation request: {project_data}")

        # Validate input data against schema
        try:
            # Wrap single project in projects array for validation
            wrapped_data = {"projects": [project_data]}
            payload = ProjectsPayload.model_validate(wrapped_data)
            project = payload.projects[0]  # Extract the single project
        except ValidationError as e:
            error_message = "Invalid project data format"
            current_app.logger.error(f"{error_message}: {e.errors()}")
            return jsonify({
                "error": error_message,
                "details": [{"field": "/".join(map(str, err["loc"])), "message": err["msg"]} 
                           for err in e.errors()]
            }), 400

        # Process image upload if provided
        file_key = 'project_image'
        file = files.get(file_key)
        if file and file.filename:
            image_bytes = file.read()
            ok, err, info, static_path = save_validated_image_to_subdir(image_bytes, file.filename, subdir="uploads/project")
            if ok:
                project.image_url = static_path
            else:
                current_app.logger.error(f"Image upload failed for new project: {err} {info}")
                return jsonify({
                    "error": "Image validation failed",
                    "details": [{
                        "field": "project/image",
                        "message": err or "invalid_image",
                        "info": info,
                    }]
                }), 400

        # Convert Pydantic model to dictionary for the repository
        project_data = {
            'project_title': project.project_title,
            'project_description': project.project_description,
            'project_url': project.project_url,
            'project_image_url': project.image_url,
        }

        # Save to the database
        try:
            new_project = create_project(
                user_id=current_user.id,
                project_data=project_data,
            )
            return jsonify({
                "message": "Project created successfully",
                "project": {
                    "hex_id": new_project.hex_id,
                    "project_title": new_project.project_title,
                    "project_description": new_project.project_description,
                    "project_url": new_project.project_url,
                    "project_image_url": new_project.project_image_url,
                }
            }), 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error creating project: {e}", exc_info=True)
            return jsonify({"error": "A database error occurred."}), 500
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in create_single_project: {str(e)}", exc_info=True)
        return jsonify({
            "error": "An unexpected error occurred while processing your request"
        }), 500
