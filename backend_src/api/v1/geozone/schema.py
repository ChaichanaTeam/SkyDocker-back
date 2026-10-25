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