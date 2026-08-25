from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator

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
    height_agl: Optional[int] = Field(..., description="Optional, if only other height valid")
    height_amsl: Optional[int] = Field(..., description="Optional, if only other height valid")
    activity_time: Optional[list[ActivityTime]] = None


    @classmethod
    def from_geozone(cls, geozone: GeoZone) -> "GeozoneProperties":
        return cls(
            country_id=geozone.country.id,
            country=geozone.country.name,
            type=geozone.type,
            tag=geozone.tag,
            strength=geozone.strength,
            height_agl=geozone.height_agl,
            height_amsl=geozone.height_amsl,
        )


    @model_validator(mode="after")
    def validate_height(self):
        is_heights_null = self.height_agl is None and self.height_amsl is None
        is_geozone_forbidden = self.type == GeoZoneType.danger

        if not is_geozone_forbidden and is_heights_null:
            raise ValueError("Atleast one height must be valid")
        return self