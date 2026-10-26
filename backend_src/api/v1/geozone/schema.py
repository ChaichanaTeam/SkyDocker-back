from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from backend_src.models.enum import GeoZoneType
from backend_src.models.model import GeoZone
from backend_src.api.shared_schemas import FeatureProperties


class ActivityTime(BaseModel):
    starts_at: datetime
    ends_at: datetime


class CatalogSyncReport(BaseModel):
    fetched: int = Field(description="Zones returned by PANSA")
    inserted: int
    updated: int
    unchanged: int
    deleted: int = Field(description="Zones no longer published by PANSA")
    skipped: int = Field(description="Zones with invalid data, see errors")
    parents_linked: int = Field(description="Zones whose parent zone was set or changed")
    errors: list[str]


class ActivitySyncReport(BaseModel):
    activations: int = Field(description="AUP/UUP reservations returned by PANSA")
    notams: int = Field(description="NOTAMs returned by PANSA")
    windows: int = Field(description="Activity windows stored after the sync")
    inserted: int
    deleted: int = Field(description="Windows that ended or are no longer published")
    unchanged: int
    zones_with_windows: int
    ignored: int = Field(description="Windows of zones that are not scheduled, e.g. CTR hours of service")
    unmatched: list[str] = Field(description="Designators missing from the zone catalog, e.g. reserved sub-sectors")


class GeozoneProperties(FeatureProperties):
    country_id: int
    country: str
    type: GeoZoneType
    tag: str
    activity_time: Optional[list[ActivityTime]] = None


    @classmethod
    def from_geozone(cls, geozone: GeoZone) -> "GeozoneProperties":
        return cls(
            country_id=geozone.country.id,
            country=geozone.country.name,
            type=geozone.type,
            tag=geozone.tag
        )