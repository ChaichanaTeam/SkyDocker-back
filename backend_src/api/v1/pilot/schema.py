from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

from backend_src.models.enum import UserActivity
from backend_src.api.shared_schemas import StoredPhoneNumber


class PilotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    first_name: Optional[str]
    last_name: Optional[str]

    email: EmailStr
    phone_number: Optional[str]
    pilot_number: Optional[str]

    show_to_public: bool = Field(description="[Could have] Whether the profile is visible in public")
    activity: Optional[UserActivity] = Field(description="[Could have] Pilot's occupation/hobby")
    flight_time: int = Field(description="Total flight time")

    created_at: datetime


class PilotUpdate(BaseModel):
    """Partial update: a field can be left out, but not set to null."""

    phone_number: StoredPhoneNumber = Field(default=None, description="Pilot's contact, a check-in shows it")
    show_to_public: bool = Field(default=None, description="Whether the profile should be visible publicly")


class PilotPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    first_name: Optional[str]
    last_name: Optional[str]

    activity: Optional[UserActivity]
    flight_time: int
