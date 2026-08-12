from pydantic import BaseModel, EmailStr, Field, model_validator, ConfigDict, StringConstraints
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional
from datetime import datetime

from backend_src.models.enum import UserActivity


PhoneNumber.phone_format = 'E164'


class PilotLogin(BaseModel):
    email: EmailStr
    password: str


class PilotRegister(BaseModel):
    email: EmailStr
    phone_number: PhoneNumber

    password: str = StringConstraints(min_length=8)

    first_name: str = StringConstraints(max_length=255)
    last_name: str = StringConstraints(max_length=255)


class PilotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    first_name: str
    last_name: str

    email: EmailStr
    phone_number: PhoneNumber
    pilot_number: Optional[str] = None

    country_id: int
    show_to_public: bool = Field(default=False, description="[Could have] Whether the profile is visible in public")
    activity: Optional[UserActivity] = Field(default=None, description="[Could have] Pilot's occupation/hobby")
    flight_time: int = Field(description="Total flight time")

    verified: bool
    created_at: datetime


class PilotUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=255)
    last_name: Optional[str] = Field(default=None, max_length=255)

    phone_number: Optional[PhoneNumber]
    pilot_number: Optional[str] = Field(default=None, max_length=255)

    country_id: Optional[int] = None
    show_to_public: Optional[bool] = Field(default=None, description="Whether the profile should be visible publicly")


class PilotPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    first_name: str
    last_name: str

    country_id: int
    activity: Optional[UserActivity] = None
    flight_time: int


class ChangePasswordRequest(BaseModel):
    current_password: str = StringConstraints(min_length=8)
    new_password: str = StringConstraints(min_length=8)


class RegisterVerifyOTP(BaseModel):
    code: str = StringConstraints(min_length=6, max_length=6)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetTokenRequest(BaseModel):
    code: str = StringConstraints(min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    new_password: str = StringConstraints(min_length=8)