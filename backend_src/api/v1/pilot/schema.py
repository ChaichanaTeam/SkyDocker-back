from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

from backend_src.models.enum import UserActivity
from backend_src.api.shared_schemas import E164PhoneNumber


class PilotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    first_name: str
    last_name: str

    email: EmailStr
    phone_number: E164PhoneNumber
    pilot_number: Optional[str] = None

    country_id: Optional[int]
    show_to_public: bool = Field(default=False, description="[Could have] Whether the profile is visible in public")
    activity: Optional[UserActivity] = Field(default=None, description="[Could have] Pilot's occupation/hobby")
    flight_time: int = Field(description="Total flight time")

    verified: bool
    created_at: datetime


class PilotUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=255)
    last_name: Optional[str] = Field(default=None, max_length=255)

    phone_number: Optional[E164PhoneNumber]
    pilot_number: Optional[str] = Field(default=None, max_length=255)

    country_id: Optional[int] = None
    show_to_public: Optional[bool] = Field(default=None, description="Whether the profile should be visible publicly")


class PilotPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    first_name: str
    last_name: str

    country_id: Optional[int]
    activity: Optional[UserActivity] = None
    flight_time: int
