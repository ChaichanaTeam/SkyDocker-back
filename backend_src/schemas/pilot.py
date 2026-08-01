from pydantic import BaseModel, EmailStr, Field, model_validator, ConfigDict
from typing import Optional
from datetime import datetime

from backend_src.models.enum import UserActivity

class PilotLogin(BaseModel):
    email: EmailStr
    password: str


class PilotRegister(BaseModel):
    email: EmailStr
    phone_number: str = Field(min_length=1, max_length=15)

    password: str = Field(min_length=8)

    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)


class PilotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    first_name: str
    last_name: str

    email: EmailStr
    phone_number: str
    pilot_number: Optional[str] = None

    country_id: int
    show_to_public: bool
    activity: Optional[UserActivity] = None
    flight_time: int

    verified: bool
    created_at: datetime


class PilotUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=255)

    phone_number: Optional[str] = Field(default=None, min_length=1, max_length=15)
    pilot_number: Optional[str] = Field(default=None, max_length=255)

    country_id: Optional[int] = None
    show_to_public: Optional[bool] = None


class PilotPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    first_name: str
    last_name: str

    country_id: int
    activity: Optional[UserActivity] = None
    flight_time: int


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class RegisterVerifyOTP(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetTokenRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)