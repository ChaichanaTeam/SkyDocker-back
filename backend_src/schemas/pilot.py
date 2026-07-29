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
    password_confirm: str

    pilot_number: Optional[str] = None

    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Password do not match")
        return self


class PilotVerifyCode(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


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
    new_password_confirm: str

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError("Password do not match")
        return self
