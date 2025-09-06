from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List


class ProjectInput(BaseModel):
    model_config = ConfigDict(extra='ignore')
    id: Optional[int] = None
    project_title: str = Field(..., min_length=1, max_length=200)
    project_description: Optional[str] = None
    project_url: Optional[str] = None
    image_url: Optional[str] = None
    remove_image: bool = False
    delete: Optional[bool] = False


class ProjectsPayload(BaseModel):
    projects: List[ProjectInput] = Field(default_factory=list)

    @field_validator('projects')
    @classmethod
    def no_empty_objects(cls, v):
        # Ensure lists are well-formed
        return v or []


# Force Pydantic to rebuild the model to resolve all forward references
ProjectsPayload.model_rebuild()
