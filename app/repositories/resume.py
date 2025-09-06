from __future__ import annotations

from typing import Optional

from app.extensions import db
from app.models.resume import (
    ResumeSkill,
    WorkHistory,
    WorkAccomplishment,
    Certification,
    ProfessionalDevelopment,
    Education,
)


def get_resume_skill_by_hex_id(hex_id: str) -> Optional[ResumeSkill]:
    return db.session.execute(db.select(ResumeSkill).filter_by(hex_id=hex_id)).scalar_one_or_none()


def get_work_history_by_hex_id(hex_id: str) -> Optional[WorkHistory]:
    return db.session.execute(db.select(WorkHistory).filter_by(hex_id=hex_id)).scalar_one_or_none()


def get_work_accomplishment_by_hex_id(hex_id: str) -> Optional[WorkAccomplishment]:
    return db.session.execute(db.select(WorkAccomplishment).filter_by(hex_id=hex_id)).scalar_one_or_none()


def get_certification_by_hex_id(hex_id: str) -> Optional[Certification]:
    return db.session.execute(db.select(Certification).filter_by(hex_id=hex_id)).scalar_one_or_none()


def get_professional_development_by_hex_id(hex_id: str) -> Optional[ProfessionalDevelopment]:
    return db.session.execute(db.select(ProfessionalDevelopment).filter_by(hex_id=hex_id)).scalar_one_or_none()


def get_education_by_hex_id(hex_id: str) -> Optional[Education]:
    return db.session.execute(db.select(Education).filter_by(hex_id=hex_id)).scalar_one_or_none()


def list_resume_data(user_id: int):
    skills = list(
        db.session.execute(
            db.select(ResumeSkill).filter_by(user_id=user_id).order_by(ResumeSkill.display_order, ResumeSkill.id)
        ).scalars()
    )
    work_items = list(
        db.session.execute(
            db.select(WorkHistory).filter_by(user_id=user_id).order_by(WorkHistory.display_order, WorkHistory.id)
        ).scalars()
    )
    # eager load accomplishments for convenience
    for wi in work_items:
        wi.accomplishments = list(
            db.session.execute(
                db.select(WorkAccomplishment)
                .filter_by(work_history_id=wi.id)
                .order_by(WorkAccomplishment.display_order, WorkAccomplishment.id)
            ).scalars()
        )
    certs = list(
        db.session.execute(
            db.select(Certification).filter_by(user_id=user_id).order_by(Certification.display_order, Certification.id)
        ).scalars()
    )
    profdev = list(
        db.session.execute(
            db.select(ProfessionalDevelopment)
            .filter_by(user_id=user_id)
            .order_by(ProfessionalDevelopment.display_order, ProfessionalDevelopment.id)
        ).scalars()
    )
    education = list(
        db.session.execute(
            db.select(Education)
            .filter_by(user_id=user_id)
            .order_by(Education.display_order, Education.id)
        ).scalars()
    )
    return skills, work_items, certs, profdev, education


def replace_resume_data(
    *,
    user_id: int,
    skills: list[dict],
    work_items: list[dict],  # dict includes accomplishments list
    certs: list[dict],
    profdev: list[dict],
    education: list[dict],
):
    # Delete existing
    db.session.execute(db.delete(WorkAccomplishment).where(WorkAccomplishment.work_history_id.in_(db.select(WorkHistory.id).filter_by(user_id=user_id))))
    db.session.execute(db.delete(WorkHistory).where(WorkHistory.user_id == user_id))
    db.session.execute(db.delete(ResumeSkill).where(ResumeSkill.user_id == user_id))
    db.session.execute(db.delete(Certification).where(Certification.user_id == user_id))
    db.session.execute(db.delete(ProfessionalDevelopment).where(ProfessionalDevelopment.user_id == user_id))
    db.session.execute(db.delete(Education).where(Education.user_id == user_id))

    # Insert new ordered data
    order = 0
    for s in skills:
        db.session.add(
            ResumeSkill(
                user_id=user_id,
                skill_title=s.get("skill_title", "").strip(),
                skill_description=s.get("skill_description", "").strip(),
                display_order=order,
            )
        )
        order += 1

    order = 0
    for w in work_items:
        wi = WorkHistory(
            user_id=user_id,
            work_history_image_url=w.get("work_history_image_url"),
            work_history_company_name=w.get("work_history_company_name", "").strip(),
            work_history_dates=w.get("work_history_dates", "").strip(),
            work_history_role=w.get("work_history_role", "").strip(),
            work_history_role_description=w.get("work_history_role_description"),
            display_order=order,
        )
        db.session.add(wi)
        db.session.flush()
        acc_order = 0
        for a in w.get("accomplishments", []):
            db.session.add(
                WorkAccomplishment(
                    work_history_id=wi.id,
                    accomplishment_text=a.get("accomplishment_text", "").strip(),
                    display_order=acc_order,
                )
            )
            acc_order += 1
        order += 1

    order = 0
    for c in certs:
        db.session.add(
            Certification(
                user_id=user_id,
                certification_image_url=c.get("certification_image_url"),
                certification_title=c.get("certification_title", "").strip(),
                certification_description=c.get("certification_description"),
                display_order=order,
            )
        )
        order += 1

    order = 0
    for p in profdev:
        db.session.add(
            ProfessionalDevelopment(
                user_id=user_id,
                professional_development_image_url=p.get("professional_development_image_url"),
                professional_development_title=p.get("professional_development_title", "").strip(),
                professional_development_description=p.get("professional_development_description"),
                display_order=order,
            )
        )
        order += 1

    order = 0
    for e in education:
        db.session.add(
            Education(
                user_id=user_id,
                education_image_url=e.get("education_image_url"),
                education_title=e.get("education_title", "").strip(),
                education_description=e.get("education_description"),
                display_order=order,
            )
        )
        order += 1
    
    # Commit all changes to the database
    db.session.commit()
