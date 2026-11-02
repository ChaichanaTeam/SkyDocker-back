from __future__ import annotations
from datetime import datetime, timedelta
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator, field_validator
from pydantic_extra_types.country import CountryAlpha2
from shapely.geometry import Point

from backend_src.models import MissionStatus, Checkin, FlyingPrivileges
from backend_src.api.shared_schemas import FeatureProperties, E164PhoneNumber, Coordinate
from backend_src.core.security import TokenPayload, TokenType


# Categories that need an approved mission plan, a check-in alone is not enough
MISSION_ONLY_CATEGORIES = frozenset({FlyingPrivileges.STS01, FlyingPrivileges.STS02})


class CheckinPreviewRequest(BaseModel):
    """What the pilot plans: either a mission to take the flight properties from, or the properties themselves."""

    country_tag: CountryAlpha2 = Field(description="Country whose rules the flight follows, ISO 3166-1 alpha-2")
    home_point: Coordinate
    drone_id: int
    mission_id: Optional[int] = Field(None, description="Takes the flight properties from the mission. Excludes them")
    category: Optional[FlyingPrivileges] = Field(None, description="Flight property. Excludes mission_id")
    height: Optional[int] = Field(None, ge=5, le=120, description="Metres above ground. Flight property. Excludes mission_id")
    range: Optional[int] = Field(None, ge=5, le=500, description="Metres from the home point. Flight property. Excludes mission_id")
    duration: Optional[int] = Field(None, ge=5, le=180, description="Minutes. Flight property. Excludes mission_id")

    @property
    def is_mission_related(self) -> bool:
        return self.mission_id is not None

    @property
    def has_properties(self) -> bool:
        return all(value is not None for value in (self.category, self.height, self.range, self.duration))

    @property
    def has_any_property(self) -> bool:
        return any(value is not None for value in (self.category, self.height, self.range, self.duration))

    @field_validator("category")
    @classmethod
    def validate_category(cls, category: Optional[FlyingPrivileges]) -> Optional[FlyingPrivileges]:
        if category is FlyingPrivileges.UNKNOWN:
            raise ValueError("Unknown category")
        if category in MISSION_ONLY_CATEGORIES:
            raise ValueError("This category needs a mission, pass mission_id instead")
        return category

    @model_validator(mode="after")
    def validate_exclusions(self):
        if self.is_mission_related and self.has_any_property:
            raise ValueError("mission_id excludes category, height, range and duration")

        if not self.is_mission_related and not self.has_properties:
            raise ValueError("Pass either mission_id or all of category, height, range and duration")

        return self


class CheckinPlan(BaseModel):
    """Verified flight, the only data the check-in token carries and the check-in is created from."""

    country_tag: CountryAlpha2
    home_point: Coordinate
    drone_id: int
    mission_id: Optional[int]
    category: FlyingPrivileges
    height: int = Field(description="Metres above ground")
    range: int = Field(description="Metres from the home point")
    duration: int = Field(description="Minutes")

    def to_model(self, pilot_id: int, country_id: int, starts_at: datetime) -> Checkin:
        return Checkin(
            pilot_id=pilot_id,
            mission_id=self.mission_id,
            drone_id=self.drone_id,
            flying_privilege=self.category,
            home_point=Point(self.home_point.lon, self.home_point.lat),
            country_id=country_id,
            height=self.height,
            range=self.range,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(minutes=self.duration),
            time=self.duration * 60,
        )


class CheckinTokenPayload(TokenPayload):
    type: Literal[TokenType.CHECKIN] = TokenType.CHECKIN
    checkin: CheckinPlan


class CheckinTokenResponse(BaseModel):
    checkin_token: str = Field(..., description="Pass this token to POST /check-in to start the flight")
    expires_in: int = Field(..., description="Seconds the token stays valid")


class CheckinCreateRequest(BaseModel):
    checkin_token: str = Field(..., description="Token issued by POST /check-in/preview")


class CheckinProperties(FeatureProperties):
    country_tag: CountryAlpha2
    country: str
    status: MissionStatus
    contact: E164PhoneNumber
    range: int
    height: int
    start_at: datetime
    time: int


    @classmethod
    def from_checkin(cls, checkin: Checkin) -> CheckinProperties:
        return cls(
            country_tag=checkin.country.country_tag, # type: ignore
            country=checkin.country.name,
            status=checkin.status,
            contact=checkin.pilot.phone_number, # type: ignore
            range=checkin.range,
            height=checkin.height,
            start_at=checkin.starts_at,
            time=checkin.time,
        )
