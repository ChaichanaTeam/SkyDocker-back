from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from backend_src.models.enum import GeoZoneType
from backend_src.models.model import GeoZone
from backend_src.api.shared_schemas import FeatureProperties


class ActivityTime(BaseModel):
    starts_at: datetime
    ends_at: datetime


class GeozoneProperties(FeatureProperties):
    country_id: int
    country: str
    type: GeoZoneType
    tag: str
    strength: int
    height_agl: Optional[int] = Field(gt=0)
    activity_time: Optional[list[ActivityTime]] = None


    @classmethod
    def from_geozone(cls, geozone: GeoZone) -> "GeozoneProperties":
        return cls(
            country_id=geozone.country.id,
            country=geozone.country.name,
            type=geozone.type,
            tag=geozone.tag,
            strength=geozone.strength,
            height_agl=geozone.height_agl
        )