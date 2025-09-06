from __future__ import annotations

import os
from flask import render_template, request, flash, redirect, url_for, current_app
from flask_login import current_user
from pydantic import ValidationError

from app.decorators import admin_required, mfa_required
from app.forms.projects import ProjectsForm, DeleteProjectForm
from app.repositories.project import (
    list_project_data,
    get_project_by_hex_id,
    delete_project,
    update_project,
)

from app.blueprints.admin import bp
from app.utils.image import save_validated_image_to_subdir


@bp.route("/projects", methods=["GET", "POST"]) 
@admin_required
@mfa_required
def projects_editor():
    # Initialize form; only used during POST submission
    form = ProjectsForm()

    # GET: always list the projects (no query-param based edit mode)
    if request.method == "GET":
        projects = list_project_data(current_user.id)
        delete_form = DeleteProjectForm()
        return render_template(
            'admin/projects.html',
            title='Manage Projects',
            projects=projects,
            delete_form=delete_form,
        )
    
    # Common context for rendering edit view after POST (validation errors)
    context = {
        'title': 'Edit Projects',
        'js_modules': {'admin_projects': True},
        'form': form,
    }
    
    # Handle form submission
    if form.validate_on_submit():
        try:
            from app.blueprints.api.admin.projects import update_projects

            # Pre-filter deleted items and normalize shape before sending to API
            raw = form.data
            def strip_deleted(d: dict) -> dict:
                data = dict(d)
                # Projects
                cleaned_projects = []
                for item in data.get('projects', []):
                    if item.get('delete'):
                        continue
                    # Preserve remove_image toggle
                    item['remove_image'] = bool(item.get('remove_image'))
                    cleaned_projects.append(item)
                data['projects'] = cleaned_projects
                return data

            cleaned = strip_deleted(raw)

            # Pass the cleaned data and files directly to the API function
            response, status_code = update_projects(cleaned, request.files)

            if status_code == 200:
                flash('Projects updated successfully!', 'success')
                return redirect(url_for('admin.projects_editor'))
            else:
                try:
                    error_data = response.get_json()
                    # Prefer structured details: list of {field, message, info?}
                    if isinstance(error_data, dict) and isinstance(error_data.get('details'), list):
                        for detail in error_data['details']:
                            field = detail.get('field', 'unknown field')
                            message = detail.get('message', 'An error occurred')
                            info = detail.get('info')
                            extra = ''
                            if isinstance(info, dict):
                                # Surface common hints like extension mismatch or limits
                                if 'extension_mismatch' in info:
                                    em = info['extension_mismatch']
                                    extra = f" (ext mismatch: provided {em.get('provided_ext')}, suggested {em.get('suggested_ext')})"
                                elif 'max_bytes' in info:
                                    extra = f" (max size {int(info['max_bytes']) // (1024*1024)}MB)"
                                elif 'format' in info:
                                    extra = f" (format {info['format']})"
                            flash(f"{field}: {message}{extra}", 'danger')
                    else:
                        error_msg = error_data.get('error', 'An unknown error occurred') if isinstance(error_data, dict) else 'An unknown error occurred'
                        flash(f'Failed to update projects: {error_msg}', 'danger')
                except Exception as e:
                    flash(f'An unexpected API error occurred (Status: {status_code}). Please try again.', 'danger')
                    current_app.logger.error(f"Error processing API response: {e}")
                
        except ValidationError as e:
            flash(f'Validation error: {str(e)}', 'danger')
        except Exception as e:
            current_app.logger.error(f"Error updating projects: {str(e)}")
            flash('An error occurred while updating the projects', 'danger')
    elif request.method == 'POST':
        # Surface validation errors to help debug silent failures
        try:
            for field_name, errs in (form.errors or {}).items():
                for err in errs:
                    flash(f"{field_name}: {err}", 'danger')
            if not form.errors:
                flash('Failed to submit projects form. Please try again.', 'danger')
        except Exception:
            pass
    
    # Render the template with the context (edit view)
    return render_template('admin/projects_form.html', **context)


@bp.route("/projects/<string:project_hex_id>/edit", methods=["GET", "POST"], endpoint="project_edit")
@admin_required
@mfa_required
def project_edit(project_hex_id: str):
    """Render the projects edit view directly for a specific project without redirecting.

    Note: We preload all projects into the form (consistent with the existing editor),
    but pass `target_id` so the template/JS can focus the requested project. This avoids
    the prior redirect to /admin/projects?edit=1&target_id=... while preserving the
    current update flow that expects the full projects list on submit.
    """
    form = ProjectsForm()

    # Fetch the target project and guard access
    project = get_project_by_hex_id(project_hex_id)
    if not project or getattr(project, 'user_id', None) != current_user.id:
        flash('Project not found.', 'danger')
        return redirect(url_for('admin.projects_editor'))

    # On GET: preload only the target project into the form
    if request.method == 'GET':
        form.projects.append_entry({
            "project_image_url": project.project_image_url,
            "project_title": project.project_title,
            "project_description": project.project_description or "",
            "project_url": project.project_url or "",
        })

        context = {
            'title': 'Edit Project',
            'form': form,
            'js_modules': {},
            'target_id': project.id,
        }
        return render_template('admin/project_form.html', **context)

    # On POST: validate and update only this project
    if form.validate_on_submit():
        try:
            if len(form.projects.entries) == 0:
                flash('No project data submitted.', 'danger')
                return redirect(url_for('admin.project_edit', project_hex_id=project_hex_id))

            sub = form.projects.entries[0].form

            # Handle image upload/removal
            image_field_key = 'projects-0-project_image'
            file = request.files.get(image_field_key)
            new_image_url = None
            if file and file.filename:
                image_bytes = file.read()
                ok, err, info, static_path = save_validated_image_to_subdir(image_bytes, file.filename, subdir="uploads/project")
                if not ok:
                    extra = ''
                    if isinstance(info, dict):
                        if 'extension_mismatch' in info:
                            em = info['extension_mismatch']
                            extra = f" (ext mismatch: provided {em.get('provided_ext')}, suggested {em.get('suggested_ext')})"
                        elif 'max_bytes' in info:
                            extra = f" (max size {int(info['max_bytes']) // (1024*1024)}MB)"
                        elif 'format' in info:
                            extra = f" (format {info['format']})"
                    flash(f"Image upload failed: {err or 'invalid_image'}{extra}", 'danger')
                    return redirect(url_for('admin.project_edit', project_hex_id=project_hex_id))
                new_image_url = static_path

            # Retain existing image if no new upload; only replace (and delete old) when a new image is provided
            final_image_url = new_image_url if new_image_url is not None else project.project_image_url

            # If replacing, attempt to delete old file
            if (new_image_url is not None) and project.project_image_url:
                try:
                    old_rel = project.project_image_url.lstrip(os.sep)
                    abs_path = os.path.join(current_app.static_folder, old_rel)
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                except Exception as e:
                    current_app.logger.warning(f"Failed to delete old project image for {project.hex_id}: {e}")

            # Update single project
            update_project(
                project,
                project_title=sub.project_title.data,
                project_description=sub.project_description.data,
                project_url=sub.project_url.data,
                project_image_url=final_image_url,
            )

            flash('Project updated successfully!', 'success')
            return redirect(url_for('admin.projects_editor'))
        except Exception as e:
            current_app.logger.error(f"Error updating project {project.hex_id}: {str(e)}")
            flash('An error occurred while updating the project', 'danger')

    # If POST invalid, re-render with errors and the single project data
    if len(form.projects.entries) == 0:
        form.projects.append_entry({
            "project_image_url": project.project_image_url,
            "project_title": project.project_title,
            "project_description": project.project_description or "",
            "project_url": project.project_url or "",
        })

    context = {
        'title': 'Edit Project',
        'form': form,
        'js_modules': {},
        'target_id': project.id,
    }
    return render_template('admin/project_form.html', **context)


@bp.route("/projects/new", methods=["GET", "POST"], endpoint="project_new")
@admin_required
@mfa_required
def project_new():
    """Render a new-project editor view (single empty entry) and handle save via the same API."""
    form = ProjectsForm()

    if request.method == 'GET':
        # Show a single empty project entry to create
        if len(form.projects.entries) == 0:
            form.projects.append_entry({})
        context = {
            'title': 'New Project',
            'form': form,
            'js_modules': {'admin_projects': True},
            'target_id': None,
        }
        return render_template('admin/projects_form.html', **context)

    # POST: process using the single project creation API
    if form.validate_on_submit():
        try:
            from app.blueprints.api.admin.projects import create_single_project
            
            if len(form.projects.entries) == 0:
                flash('No project data submitted.', 'danger')
                return redirect(url_for('admin.project_new'))

            # Get the single project data from the form
            project_form = form.projects.entries[0].form
            project_data = {
                'project_title': project_form.project_title.data,
                'project_description': project_form.project_description.data,
                'project_url': project_form.project_url.data,
            }
            
            # Handle image upload
            image_field_key = 'projects-0-project_image'
            files = {
                'project_image': request.files.get(image_field_key)
            } if request.files.get(image_field_key) else {}

            response, status_code = create_single_project(project_data, files)
            
            if status_code == 200:
                flash('Project created successfully!', 'success')
                return redirect(url_for('admin.projects_editor'))
            else:
                try:
                    error_data = response.get_json()
                    if isinstance(error_data, dict) and isinstance(error_data.get('details'), list):
                        for detail in error_data['details']:
                            field = detail.get('field', 'unknown field')
                            message = detail.get('message', 'An error occurred')
                            info = detail.get('info')
                            extra = ''
                            if isinstance(info, dict):
                                if 'extension_mismatch' in info:
                                    em = info['extension_mismatch']
                                    extra = f" (ext mismatch: provided {em.get('provided_ext')}, suggested {em.get('suggested_ext')})"
                                elif 'max_bytes' in info:
                                    extra = f" (max size {int(info['max_bytes']) // (1024*1024)}MB)"
                                elif 'format' in info:
                                    extra = f" (format {info['format']})"
                            flash(f"{field}: {message}{extra}", 'danger')
                    else:
                        error_msg = error_data.get('error', 'An unknown error occurred') if isinstance(error_data, dict) else 'An unknown error occurred'
                        flash(f'Failed to save project: {error_msg}', 'danger')
                except Exception:
                    flash(f'An unexpected API error occurred (Status: {status_code}). Please try again.', 'danger')
        except Exception as e:
            current_app.logger.error(f"Error creating new project: {str(e)}")
            flash('An error occurred while saving the project', 'danger')

    # If invalid, re-render form
    if len(form.projects.entries) == 0:
        form.projects.append_entry({})
    context = {
        'title': 'New Project',
        'form': form,
        'js_modules': {'admin_projects': True},
        'target_id': None,
    }
    return render_template('admin/projects_form.html', **context)


@bp.post("/projects/<string:project_hex_id>/delete")
@admin_required
@mfa_required
def project_delete(project_hex_id: str):
    form = DeleteProjectForm()
    if form.validate_on_submit():
        project = get_project_by_hex_id(project_hex_id)
        if not project:
            flash("Project not found.", "error")
            return redirect(url_for("admin.projects_editor"))
        # Attempt to delete associated image file from static if present
        try:
            img_path = (project.project_image_url or '').strip()
            if img_path:
                import os
                if os.path.isabs(img_path):
                    current_app.logger.warning(f"Refusing to delete absolute path: {img_path}")
                else:
                    safe_rel = img_path.lstrip(os.sep)
                    abs_path = os.path.join(current_app.static_folder, safe_rel)
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
        except Exception as e:
            current_app.logger.error(f"Failed to delete project image for {project.hex_id}: {e}")

        delete_project(project)
        flash("Project deleted.", "success")
        return redirect(url_for("admin.projects_editor"))
    flash("Invalid delete request.", "error")
    return redirect(url_for("admin.projects_editor"))
