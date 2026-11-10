from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Any, Optional, Union
from datetime import date, datetime

from backend_src.models.enum import (
    DroneCategory, FlyingPrivileges, MissionFlightGoal, MissionStatus, OperationalCategory, UserActivity,
    VerificationDocumentType
)
from backend_src.models.model import Checkin, Mission
from backend_src.api.shared_schemas import FeatureProperties, StoredPhoneNumber


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


class OrganizerDocumentRead(BaseModel):
    document_type: VerificationDocumentType
    size: int = Field(description="Bytes")
    uploaded_at: datetime
    url: str = Field(description="Presigned download link, valid for 5 minutes")


class PrivilegeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    flying_privilege: FlyingPrivileges
    expires_at: Optional[date] = Field(description="Last day the privilege is valid, null means no expiry")


class DroneModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    manufacturer: str
    model_name: str
    category: OperationalCategory

    speed: int = Field(description="Metres per second")
    mtom: int = Field(description="Maximum take-off mass in grams")
    max_height: int = Field(description="Metres")
    max_range: int = Field(description="Metres")


class DroneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    serial_number: str
    category: DroneCategory

    is_drone_modified: bool
    mtom_override: Optional[int] = Field(description="Take-off mass in grams that replaces the model's one")
    flight_time: int

    model: DroneModelRead


class FlightProperties(FeatureProperties):
    id: int
    drone_id: int
    flying_privilege: FlyingPrivileges
    flight_goal: Optional[MissionFlightGoal]
    description: Optional[str]
    status: MissionStatus
    country_tag: str

    height: int = Field(description="Metres above ground")
    range: int = Field(description="Metres from the home point")
    starts_at: datetime
    ends_at: datetime
    time: int = Field(description="Seconds")
    created_at: datetime

    @staticmethod
    def common_fields(flight: Union[Mission, Checkin]) -> dict[str, Any]:
        return {
            "id": flight.id,
            "drone_id": flight.drone_id,
            "flying_privilege": flight.flying_privilege,
            "flight_goal": flight.flight_goal,
            "description": flight.description,
            "status": flight.status,
            "country_tag": flight.country.country_tag,
            "height": flight.height,
            "range": flight.range,
            "starts_at": flight.starts_at,
            "ends_at": flight.ends_at,
            "time": flight.time,
            "created_at": flight.created_at,
        }


class PilotMissionProperties(FlightProperties):
    category: OperationalCategory
    spotter_first_name: Optional[str]
    spotter_last_name: Optional[str]
    spotter_phone: Optional[str]

    @classmethod
    def from_mission(cls, mission: Mission) -> PilotMissionProperties:
        return cls(
            **cls.common_fields(mission),
            category=mission.category,
            spotter_first_name=mission.spotter_first_name,
            spotter_last_name=mission.spotter_last_name,
            spotter_phone=mission.spotter_phone,
        )


class PilotCheckinProperties(FlightProperties):
    mission_id: Optional[int]

    @classmethod
    def from_checkin(cls, checkin: Checkin) -> PilotCheckinProperties:
        return cls(**cls.common_fields(checkin), mission_id=checkin.mission_id)
