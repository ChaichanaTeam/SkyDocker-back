from typing import Literal
from pydantic import BaseModel


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class BearerToken(BaseModel):
    token: str
    token_type: Literal["bearer"] = "bearer"
