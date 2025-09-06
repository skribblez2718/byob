from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List

class ResumeSkillInput(BaseModel):
    model_config = ConfigDict(extra='ignore')
    skill_title: str = Field(..., min_length=1, max_length=120)
    skill_description: Optional[str] = Field(None, min_length=1)


class WorkAccomplishmentInput(BaseModel):
    model_config = ConfigDict(extra='ignore')
    accomplishment_text: str = Field(..., min_length=1, max_length=1000)


class WorkHistoryInput(BaseModel):
    model_config = ConfigDict(extra='ignore')
    id: Optional[int] = None
    company_name: str = Field(..., min_length=1, max_length=200)
    dates: str = Field(..., min_length=1, max_length=120)
    role: str = Field(..., min_length=1, max_length=200)
    role_description: Optional[str] = None
    image_url: Optional[str] = None
    remove_image: bool = False
    accomplishments: List[WorkAccomplishmentInput] = Field(default_factory=list)
    delete: Optional[bool] = False


class CertificationInput(BaseModel):
    model_config = ConfigDict(extra='ignore')
    id: Optional[int] = None
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    remove_image: bool = False
    delete: Optional[bool] = False


class ProfessionalDevelopmentInput(BaseModel):
    model_config = ConfigDict(extra='ignore')
    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    remove_image: bool = False
    delete: Optional[bool] = False


class EducationInput(BaseModel):
    model_config = ConfigDict(extra='ignore')
    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    remove_image: bool = False
    delete: Optional[bool] = False


class ResumePayload(BaseModel):
    skills: List[ResumeSkillInput] = Field(default_factory=list)
    work_history: List[WorkHistoryInput] = Field(default_factory=list)
    certifications: List[CertificationInput] = Field(default_factory=list)
    professional_development: List[ProfessionalDevelopmentInput] = Field(default_factory=list)
    education: List[EducationInput] = Field(default_factory=list)

    @field_validator('skills', 'work_history', 'certifications', 'professional_development', 'education')
    @classmethod
    def no_empty_objects(cls, v):
        # Ensure lists are well-formed
        return v or []

# Force Pydantic to rebuild the model to resolve all forward references
ResumePayload.model_rebuild()
