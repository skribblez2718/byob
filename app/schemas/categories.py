from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    slug: str = Field(min_length=1, max_length=120)
    description: str | None = None
    display_order: int = 0

    @field_validator("slug")
    @classmethod
    def slug_lower(cls, v: str) -> str:
        return v.strip().lower()


class CategoryUpdate(CategoryCreate):
    pass
