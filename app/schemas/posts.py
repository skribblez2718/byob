from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=220)
    content_blocks: list[dict] = Field(min_length=1)
    excerpt: str = Field(min_length=1, max_length=300)
    category_id: int

    @field_validator("slug")
    @classmethod
    def slug_lower(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("content_blocks")
    @classmethod
    def validate_blocks(cls, v: list[dict]):
        # Require at least one paragraph block
        has_paragraph = any((isinstance(b, dict) and b.get("type") == "paragraph") for b in v)
        if not has_paragraph:
            raise ValueError("content_blocks must include at least one paragraph block")
        return v


class PostUpdate(PostCreate):
    pass
