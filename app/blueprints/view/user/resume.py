from __future__ import annotations

from flask import render_template, request, jsonify

from app.extensions import limiter, db
from app.repositories.resume import list_resume_data
from app.models.user import User

from app.blueprints.blog import bp


@bp.get("/resume")
@limiter.limit("120 per minute")
def resume():
    admin_user = db.session.execute(db.select(User).filter_by(is_admin=True).order_by(User.id.asc())).scalar_one_or_none()
    skills = work_items = certs = profdev = education = None
    if admin_user:
        skills, work_items, certs, profdev, education = list_resume_data(admin_user.id)

    if request.args.get("format") == "json":
        if skills is not None:
            return jsonify({
                "status": "ok",
                "page": "resume",
                "skills": [
                    {"skill_title": s.skill_title, "skill_description": s.skill_description} for s in skills
                ],
                "work_history": [
                    {
                        "work_history_image_url": w.work_history_image_url,
                        "work_history_company_name": w.work_history_company_name,
                        "work_history_dates": w.work_history_dates,
                        "work_history_role": w.work_history_role,
                        "work_history_role_description": w.work_history_role_description,
                        "accomplishments": [
                            {"accomplishment_text": a.accomplishment_text} for a in getattr(w, "accomplishments", [])
                        ],
                    }
                    for w in work_items
                ],
                "certifications": [
                    {
                        "certification_image_url": c.certification_image_url,
                        "certification_title": c.certification_title,
                        "certification_description": c.certification_description,
                    }
                    for c in certs
                ],
                "professional_development": [
                    {
                        "professional_development_image_url": p.professional_development_image_url,
                        "professional_development_title": p.professional_development_title,
                        "professional_development_description": p.professional_development_description,
                    }
                    for p in profdev
                ],
                "education": [
                    {
                        "education_title": e.education_title,
                        "education_description": e.education_description,
                        "education_image_url": e.education_image_url,
                    }
                    for e in education
                ],
            })
        return jsonify({
            "status": "ok",
            "page": "resume",
        })

    if skills is not None:
        return render_template(
            "resume.html",
            skills=skills,
            work_items=work_items,
            certs=certs,
            profdev=profdev,
            education=education,
        )

    return render_template("resume.html")
