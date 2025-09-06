from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=8, max_length=256)


class MfaVerifyRequest(BaseModel):
    code: str | None = Field(default=None, min_length=6, max_length=10)
    backup_code: str | None = Field(default=None, min_length=6, max_length=32)

    def has_any(self) -> bool:
        return bool(self.code or self.backup_code)
