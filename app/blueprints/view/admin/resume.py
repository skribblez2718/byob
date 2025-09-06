from __future__ import annotations

from flask import render_template, request, flash, redirect, url_for, current_app
from flask_login import current_user
from pydantic import ValidationError

from app.decorators import admin_required, mfa_required
from app.forms.resume import ResumeForm
from app.repositories.resume import list_resume_data

from app.blueprints.admin import bp


@bp.route("/resume", methods=["GET", "POST"])
@admin_required
@mfa_required
def resume_editor():
    # Initialize form
    form = ResumeForm()
    
    # Set up template context with js_modules
    context = {
        'js_modules': {
            'admin_resume': True
        },
        'title': 'Edit Resume'
    }

    # Preload existing data on GET
    if request.method == "GET":
        skills, work_items, certs, profdev, education = list_resume_data(current_user.id)

        # Add skills
        for skill in skills:
            form.skills.append_entry({
                "skill_title": skill.skill_title,
                "skill_description": skill.skill_description,
            })

        # Add work history with accomplishments
        for work in work_items:
            wi_form = {
                "work_history_image_url": work.work_history_image_url,
                "work_history_company_name": work.work_history_company_name,
                "work_history_dates": work.work_history_dates,
                "work_history_role": work.work_history_role,
                "work_history_role_description": work.work_history_role_description or "",
            }
            form.work_history.append_entry(wi_form)
            
            # Add accomplishments for this work item
            for accomplishment in work.accomplishments:
                form.work_history[-1].accomplishments.append_entry({
                    "accomplishment_text": accomplishment.accomplishment_text
                })
        
        # Add certifications
        for cert in certs:
            form.certifications.append_entry({
                "image_url": cert.certification_image_url,
                "title": cert.certification_title,
                "description": cert.certification_description or "",
            })

        # Add professional development
        for prof in profdev:
            form.professional_development.append_entry({
                "image_url": prof.professional_development_image_url,
                "title": prof.professional_development_title,
                "description": prof.professional_development_description or "",
            })
        
        # Add education
        for ed in education:
            form.education.append_entry({
                "image_url": ed.education_image_url,
                "title": ed.education_title,
                "description": ed.education_description or "",
            })
        
        # Ensure there is at least one entry per section when no data exists
        if len(form.skills.entries) == 0:
            form.skills.append_entry({})
        if len(form.work_history.entries) == 0:
            form.work_history.append_entry({})
            form.work_history[-1].accomplishments.append_entry({"accomplishment_text": ""})
        if len(form.certifications.entries) == 0:
            form.certifications.append_entry({})
        if len(form.professional_development.entries) == 0:
            form.professional_development.append_entry({})
        if len(form.education.entries) == 0:
            form.education.append_entry({})
    
    # Add form to context
    context['form'] = form
    
    # Handle form submission
    if form.validate_on_submit():
        try:
            from app.blueprints.api.admin.resume import update_resume

            # Pre-filter deleted items and normalize shape before sending to API
            raw = form.data
            def strip_deleted(d: dict) -> dict:
                data = dict(d)
                # Skills
                data['skills'] = [s for s in data.get('skills', []) if not s.get('delete')]
                # Work history and nested accomplishments
                cleaned_wh = []
                for item in data.get('work_history', []):
                    if item.get('delete'):
                        continue
                    # Normalize keys for API/schema convenience too
                    item['company_name'] = item.get('work_history_company_name')
                    item['dates'] = item.get('work_history_dates')
                    item['role'] = item.get('work_history_role')
                    item['role_description'] = item.get('work_history_role_description')
                    item['image_url'] = item.get('work_history_image_url')
                    # Preserve remove_image toggle
                    item['remove_image'] = bool(item.get('remove_image'))
                    # accomplishments
                    item['accomplishments'] = [a for a in item.get('accomplishments', []) if not a.get('delete')]
                    cleaned_wh.append(item)
                data['work_history'] = cleaned_wh
                # Certifications
                certs_clean = []
                for c in data.get('certifications', []):
                    if c.get('delete'):
                        continue
                    # Keep remove_image if present
                    c['remove_image'] = bool(c.get('remove_image'))
                    certs_clean.append(c)
                data['certifications'] = certs_clean
                # Professional development
                pd_clean = []
                for p in data.get('professional_development', []):
                    if p.get('delete'):
                        continue
                    p['remove_image'] = bool(p.get('remove_image'))
                    pd_clean.append(p)
                data['professional_development'] = pd_clean
                # Education
                edu_clean = []
                for e in data.get('education', []):
                    if e.get('delete'):
                        continue
                    e['remove_image'] = bool(e.get('remove_image'))
                    edu_clean.append(e)
                data['education'] = edu_clean
                return data

            cleaned = strip_deleted(raw)

            # Pass the cleaned data and files directly to the API function
            response, status_code = update_resume(cleaned, request.files)

            if status_code == 200:
                flash('Resume updated successfully!', 'success')
                return redirect(url_for('admin.resume_editor'))
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
                        flash(f'Failed to update resume: {error_msg}', 'danger')
                except Exception as e:
                    flash(f'An unexpected API error occurred (Status: {status_code}). Please try again.', 'danger')
                    current_app.logger.error(f"Error processing API response: {e}")
                
        except ValidationError as e:
            flash(f'Validation error: {str(e)}', 'danger')
        except Exception as e:
            current_app.logger.error(f"Error updating resume: {str(e)}")
            flash('An error occurred while updating the resume', 'danger')
    
    # Render the template with the context
    return render_template('admin/resume_form.html', **context)
