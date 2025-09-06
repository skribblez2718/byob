import json
import os
from flask import Blueprint, request, jsonify, current_app
from app.utils.image import save_validated_image_to_uploads
from flask_login import current_user, login_required
from pydantic import ValidationError

from app.decorators import admin_required, mfa_required
from app.schemas.resume import (
    ResumePayload,
    ResumeSkillInput,
    WorkHistoryInput,
    WorkAccomplishmentInput,
    CertificationInput,
    ProfessionalDevelopmentInput
)
from app.repositories.resume import (
    replace_resume_data,
    list_resume_data,
)
from app.extensions import db

bp = Blueprint('admin_resume', __name__, url_prefix='/api/admin/resume')

@bp.route('', methods=['GET'])
@login_required
@admin_required
@mfa_required
def get_resume_data():
    """Get all resume data for the current admin user"""
    try:
        skills, work_items, certs, profdev, education = list_resume_data(current_user.id)

        # Serialize models explicitly
        skills_data = [
            {
                'skill_title': s.skill_title,
                'skill_description': s.skill_description,
            }
            for s in skills
        ]

        work_items_data = []
        for work in work_items:
            work_items_data.append({
                'work_history_company_name': work.work_history_company_name,
                'work_history_dates': work.work_history_dates,
                'work_history_role': work.work_history_role,
                'work_history_role_description': work.work_history_role_description,
                'work_history_image_url': work.work_history_image_url,
                'accomplishments': [
                    {'accomplishment_text': a.accomplishment_text}
                    for a in (work.accomplishments or [])
                ],
            })

        certifications_data = [
            {
                'certification_title': c.certification_title,
                'certification_description': c.certification_description,
                'certification_image_url': c.certification_image_url,
            }
            for c in certs
        ]

        profdev_data = [
            {
                'professional_development_title': p.professional_development_title,
                'professional_development_description': p.professional_development_description,
                'professional_development_image_url': p.professional_development_image_url,
            }
            for p in profdev
        ]

        education_data = [
            {
                'education_title': e.education_title,
                'education_description': e.education_description,
                'education_image_url': e.education_image_url,
            }
            for e in education
        ]

        return jsonify({
            'skills': skills_data,
            'work_history': work_items_data,
            'certifications': certifications_data,
            'professional_development': profdev_data,
            'education': education_data,
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching resume data: {str(e)}")
        return jsonify({"error": "An error occurred while fetching resume data"}), 500

@bp.route('', methods=['POST'])
@login_required
@admin_required
@mfa_required
def update_resume(resume_data, files): 
    """Update resume data for the current admin user"""
    try:
        
        # Log incoming request for debugging
        current_app.logger.debug(f"Received resume update request: {resume_data}")

        # Helper: strip deleted items in raw dict before validation
        def strip_deleted_items(data: dict) -> dict:
            if not isinstance(data, dict):
                return data
            # Skills
            if isinstance(data.get('skills'), list):
                data['skills'] = [s for s in data['skills'] if not (isinstance(s, dict) and s.get('delete'))]
            # Work history + nested accomplishments
            if isinstance(data.get('work_history'), list):
                cleaned_wh = []
                for item in data['work_history']:
                    if not isinstance(item, dict) or item.get('delete'):
                        continue
                    # Normalize keys used by forms to schema keys
                    if 'work_history_company_name' in item and 'company_name' not in item:
                        item['company_name'] = item.get('work_history_company_name')
                    if 'work_history_dates' in item and 'dates' not in item:
                        item['dates'] = item.get('work_history_dates')
                    if 'work_history_role' in item and 'role' not in item:
                        item['role'] = item.get('work_history_role')
                    if 'work_history_role_description' in item and 'role_description' not in item:
                        item['role_description'] = item.get('work_history_role_description')
                    if 'work_history_image_url' in item and 'image_url' not in item:
                        item['image_url'] = item.get('work_history_image_url')
                    # accomplishments
                    if isinstance(item.get('accomplishments'), list):
                        item['accomplishments'] = [
                            a for a in item['accomplishments'] if not (isinstance(a, dict) and a.get('delete'))
                        ]
                    cleaned_wh.append(item)
                data['work_history'] = cleaned_wh
            # Certifications
            if isinstance(data.get('certifications'), list):
                data['certifications'] = [c for c in data['certifications'] if not (isinstance(c, dict) and c.get('delete'))]
            # Professional development
            if isinstance(data.get('professional_development'), list):
                data['professional_development'] = [p for p in data['professional_development'] if not (isinstance(p, dict) and p.get('delete'))]
            # Education
            if isinstance(data.get('education'), list):
                data['education'] = [e for e in data['education'] if not (isinstance(e, dict) and e.get('delete'))]
            return data

        resume_data = strip_deleted_items(resume_data)

        # Validate input data against schema
        try:
            payload = ResumePayload.model_validate(resume_data)
        except ValidationError as e:
            error_message = "Invalid resume data format"
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
        for i, wh in enumerate(payload.work_history):
            file_key = f'work_history-{i}-work_history_image'
            file = files.get(file_key)
            if file and file.filename:
                image_bytes = file.read()
                ok, err, info, static_path = save_validated_image_to_uploads(image_bytes, file.filename)
                if ok:
                    wh.image_url = static_path
                else:
                    current_app.logger.error(f"Image upload failed for work_history[{i}]: {err} {info}")
                    image_errors.append({
                        "field": f"work_history/{i}/image",
                        "message": err or "invalid_image",
                        "info": info,
                    })
            else:
                # keep existing unless explicitly removed
                if getattr(wh, 'remove_image', False):
                    wh.image_url = None

        for i, cert in enumerate(payload.certifications):
            file_key = f'certifications-{i}-image'
            file = files.get(file_key)
            if file and file.filename:
                image_bytes = file.read()
                ok, err, info, static_path = save_validated_image_to_uploads(image_bytes, file.filename)
                if ok:
                    cert.image_url = static_path
                else:
                    current_app.logger.error(f"Image upload failed for certifications[{i}]: {err} {info}")
                    image_errors.append({
                        "field": f"certifications/{i}/image",
                        "message": err or "invalid_image",
                        "info": info,
                    })
            else:
                if getattr(cert, 'remove_image', False):
                    cert.image_url = None

        for i, prof in enumerate(payload.professional_development):
            file_key = f'professional_development-{i}-image'
            file = files.get(file_key)
            if file and file.filename:
                image_bytes = file.read()
                ok, err, info, static_path = save_validated_image_to_uploads(image_bytes, file.filename)
                if ok:
                    prof.image_url = static_path
                else:
                    current_app.logger.error(f"Image upload failed for professional_development[{i}]: {err} {info}")
                    image_errors.append({
                        "field": f"professional_development/{i}/image",
                        "message": err or "invalid_image",
                        "info": info,
                    })
            else:
                if getattr(prof, 'remove_image', False):
                    prof.image_url = None

        # Education images
        for i, edu in enumerate(payload.education):
            file_key = f'education-{i}-image'
            file = files.get(file_key)
            if file and file.filename:
                image_bytes = file.read()
                ok, err, info, static_path = save_validated_image_to_uploads(image_bytes, file.filename)
                if ok:
                    edu.image_url = static_path
                else:
                    current_app.logger.error(f"Image upload failed for education[{i}]: {err} {info}")
                    image_errors.append({
                        "field": f"education/{i}/image",
                        "message": err or "invalid_image",
                        "info": info,
                    })
            else:
                if getattr(edu, 'remove_image', False):
                    edu.image_url = None

        # If any image errors occurred, return them for UI display
        if image_errors:
            return jsonify({
                "error": "Image validation failed",
                "details": image_errors
            }), 400

        # After successful image processing, delete only images no longer referenced
        try:
            _skills_old, existing_work_old, existing_certs_old, existing_profdev_old, existing_edu_old = list_resume_data(current_user.id)
            old_images = set(filter(None, [
                *(w.work_history_image_url for w in existing_work_old),
                *(c.certification_image_url for c in existing_certs_old),
                *(p.professional_development_image_url for p in existing_profdev_old),
                *(e.education_image_url for e in existing_edu_old),
            ]))
            new_images = set(filter(None, [
                *(wh.image_url for wh in payload.work_history),
                *(c.image_url for c in payload.certifications),
                *(p.image_url for p in payload.professional_development),
                *(e.image_url for e in payload.education),
            ]))
            for path in old_images - new_images:
                delete_image(path)
        except Exception as e:
            current_app.logger.error(f"Failed deleting unreferenced images: {e}")

        # Convert Pydantic models to dictionaries for the repository, mapping to DB field names
        skills_data = [s.model_dump() for s in payload.skills]
        # Map work history fields to DB column-style keys expected by repository
        work_items_data = [
            {
                'work_history_company_name': wh.company_name,
                'work_history_dates': wh.dates,
                'work_history_role': wh.role,
                'work_history_role_description': wh.role_description,
                'work_history_image_url': wh.image_url,
                'accomplishments': [
                    {'accomplishment_text': a.accomplishment_text} for a in wh.accomplishments
                ],
            }
            for wh in payload.work_history
        ]
        certifications_data = [
            {
                'certification_title': c.title,
                'certification_description': c.description,
                'certification_image_url': c.image_url
            }
            for c in payload.certifications
        ]
        professional_development_data = [
            {
                'professional_development_title': pd.title,
                'professional_development_description': pd.description,
                'professional_development_image_url': pd.image_url
            }
            for pd in payload.professional_development
        ]
        education_data = [
            {
                'education_title': ed.title,
                'education_description': ed.description,
                'education_image_url': ed.image_url,
            }
            for ed in payload.education
        ]

        # Save to the database
        try:
            replace_resume_data(
                user_id=current_user.id,
                skills=skills_data,
                work_items=work_items_data,
                certs=certifications_data,
                profdev=professional_development_data,
                education=education_data,
            )
            return jsonify({"message": "Resume updated successfully"}), 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error updating resume: {e}", exc_info=True)
            return jsonify({"error": "A database error occurred."}), 500
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in update_resume: {str(e)}", exc_info=True)
        return jsonify({
            "error": "An unexpected error occurred while processing your request"
        }), 500
