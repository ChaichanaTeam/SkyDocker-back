from typing import Literal
from pydantic import BaseModel, Field


class TokenPair(BaseModel):
    access_token: str = Field(..., description="Pass this token in Authorization header for endpoints which requires it")
    refresh_token: str = Field(..., description="Pass this token in /refresh to get new access token")
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Token issued after login. Pass for getting new access token")


class BearerToken(BaseModel):
    token: str = Field(..., description="Token issued by endpoint. Can be Refresh / Verify / Reset / Access - depending on endpoint")
    token_type: Literal["bearer"] = "bearer"
