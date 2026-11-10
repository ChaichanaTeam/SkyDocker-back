from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend_src.core.security import IssuedToken
from .constants import ACCESS_TTL_SECONDS


class ModeratorLogin(BaseModel):
    email: EmailStr
    password: str


class ModeratorAccessToken(BaseModel):
    access_token: str = Field(..., description="Pass this token in Authorization header for moderator endpoints")
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(..., description="Access token lifetime in seconds")

    @classmethod
    def from_token(cls, access: IssuedToken) -> ModeratorAccessToken:
        return cls(access_token=access.token, expires_in=ACCESS_TTL_SECONDS)


class ModeratorProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: str
