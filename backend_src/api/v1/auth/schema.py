from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, EmailStr, field_validator

from backend_src.core.security import IssuedToken
from .constants import ACCESS_TTL_SECONDS
from backend_src.api.shared_schemas import E164PhoneNumber, NormalizedEmailStr, normalize_email


class PilotRegister(BaseModel):
    phone_number: E164PhoneNumber

    password: str = Field(min_length=8)

    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)


class PilotLogin(BaseModel):
    email: NormalizedEmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)


class RegisterRequestOTP(BaseModel):
    email: EmailStr

    # Original address is kept, but it must still be normalizable
    @field_validator("email")
    @classmethod
    def validate_normalizable(cls, email: str) -> str:
        normalize_email(email)
        return email


class RegisterVerifyOTP(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class ForgotPasswordRequest(BaseModel):
    email: NormalizedEmailStr


class VerifyResetTokenRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)


class TokenPair(BaseModel):
    access_token: str = Field(..., description="Pass this token in Authorization header for endpoints which requires it")
    refresh_token: str = Field(..., description="Pass this token in /refresh to get new access token")
    token_type: Literal["bearer"] = "bearer"
    expires_in: int

    @classmethod
    def from_tokens(cls, access: IssuedToken, refresh: IssuedToken) -> TokenPair:
        return TokenPair(
            access_token=access.token,
            refresh_token=refresh.token,
            expires_in=ACCESS_TTL_SECONDS,
        )


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Token issued after login. Pass for getting new access token")


class BearerToken(BaseModel):
    token: str = Field(..., description="Token issued by endpoint. Can be Refresh / Verify / Reset / Access - depending on endpoint")
    token_type: Literal["bearer"] = "bearer"
