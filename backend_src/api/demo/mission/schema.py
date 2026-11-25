from __future__ import annotations

from typing import Literal, Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from backend_src.api.shared_schemas import Coordinate, NormalizedEmailStr, StoredPhoneNumber
from backend_src.models.enum import (
    FlyingPrivileges,
    MissionFlightGoal,
    MissionStatus,
)


# Decisions PANSA sends, the flight statuses are set by the check-ins
ImportedStatus = Literal["pending", "accepted", "rejected"]


class MissionImportProperties(BaseModel):
    """One mission of the import file, as PANSA decided it."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    external_id: str = Field(min_length=1, max_length=255, description="Number of the mission at PANSA, a repeated import updates it")
    pilot_email: NormalizedEmailStr
    drone_serial: str = Field(min_length=1, max_length=255, description="Serial number of a drone in the pilot's drone park")
    flying_privilege: FlyingPrivileges
    status: ImportedStatus
    decision_reason: Optional[str] = Field(None, min_length=1, description="Why PANSA rejected the mission, required when rejected")

    height: int = Field(ge=5, le=120, description="Metres above ground")
    range: int = Field(ge=5, le=2000, description="Metres from the home point, BVLOS of STS-02 reaches 2 km")
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    duration: int = Field(ge=5, description="Minutes of flight within the window")

    flight_goal: Optional[MissionFlightGoal] = None
    description: Optional[str] = None
    spotter_first_name: Optional[str] = Field(None, max_length=255)
    spotter_last_name: Optional[str] = Field(None, max_length=255)
    spotter_phone: Optional[StoredPhoneNumber] = None

    @field_validator("flying_privilege")
    @classmethod
    def validate_privilege(cls, privilege: FlyingPrivileges) -> FlyingPrivileges:
        if privilege is FlyingPrivileges.UNKNOWN:
            raise ValueError("Unknown flying privilege")
        return privilege

    @model_validator(mode="after")
    def validate_mission(self) -> "MissionImportProperties":
        if self.starts_at >= self.ends_at:
            raise ValueError("starts_at must be before ends_at")

        if self.duration * 60 > (self.ends_at - self.starts_at).total_seconds():
            raise ValueError("duration does not fit between starts_at and ends_at")

        if (self.status == "rejected") != (self.decision_reason is not None):
            raise ValueError("decision_reason is required for a rejected mission and only for it")

        return self


class MissionPoint(BaseModel):
    type: Literal["Point"]
    coordinates: tuple[float, float] = Field(description="Home point, [lon, lat]")

    @property
    def coordinate(self) -> Coordinate:
        lon, lat = self.coordinates
        return Coordinate(lon=lon, lat=lat)

    @model_validator(mode="after")
    def validate_region(self) -> "MissionPoint":
        lon, lat = self.coordinates
        Coordinate(lon=lon, lat=lat)  # raises outside the supported region
        return self


class MissionImportFeature(BaseModel):
    type: Literal["Feature"]
    geometry: MissionPoint
    properties: MissionImportProperties


class ImportedMission(BaseModel):
    external_id: str
    id: int
    status: MissionStatus


class MissionImportReport(BaseModel):
    created: int
    updated: int = Field(description="Missions of the file that were imported before, by external_id")
    missions: list[ImportedMission]
