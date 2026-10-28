from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from backend_src.models.enum import GeoZoneActivityMode, GeoZoneActivitySource, GeoZoneType
from backend_src.models.model import ActivityTime, GeoZone
from backend_src.integrations.pansa import HeightRule
from backend_src.api.shared_schemas import FeatureProperties


class ActivityWindow(BaseModel):
    source: GeoZoneActivitySource
    starts_at: datetime
    ends_at: datetime
    lower_limit_ft: int = Field(description="Reserved lower limit, feet above mean sea level")
    upper_limit_ft: int = Field(description="Reserved upper limit, feet above mean sea level")

    @classmethod
    def from_activity_time(cls, window: ActivityTime, geozone: GeoZone) -> "ActivityWindow":
        # a window without own limits reserves the whole zone
        return cls(
            source=window.source,
            starts_at=window.start_at,
            ends_at=window.ends_at,
            lower_limit_ft=geozone.lower_limit_ft if window.lower_limit_ft is None else window.lower_limit_ft,
            upper_limit_ft=geozone.upper_limit_ft if window.upper_limit_ft is None else window.upper_limit_ft,
        )


class HeightRules(BaseModel):
    free_m: int = Field(description="Up to this height above ground the flight needs only a check-in")
    free_max_mass_g: Optional[int] = Field(
        description="free_m applies only to drones up to this take-off mass, null means any mass"
    )
    max_m: int = Field(
        description="Highest allowed height above ground, above free_m the flight needs the zone manager consent "
                    "or an approved mission plan, 0 means flights are prohibited"
    )

    @classmethod
    def from_rule(cls, rule: HeightRule) -> "HeightRules":
        return cls(free_m=rule.free_m, free_max_mass_g=rule.free_max_mass_g, max_m=rule.max_m)


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
    id: int
    parent_id: Optional[int] = Field(description="Zone this one belongs to, e.g. ATZ EPKP for ATZEPKP1KM")
    country_id: int
    country: str
    type: GeoZoneType
    source_type: str = Field(description="PANSA zone type, e.g. CTR, ATZ6KM, TRA, RPA")
    tag: str
    lower_limit_ft: int = Field(description="Feet above mean sea level")
    upper_limit_ft: int = Field(description="Feet above mean sea level")
    valid_from: Optional[datetime] = Field(description="Null means the zone has no start date")
    valid_to: Optional[datetime] = Field(description="Null means the zone has no end date")
    activity_mode: GeoZoneActivityMode = Field(
        description="permanent zones are always active, scheduled ones only in their activity windows, "
                    "inherited ones in the windows of the parent zone"
    )
    active_now: bool
    activity_time: list[ActivityWindow] = Field(description="Current and upcoming activity windows")
    height_rule: HeightRules = Field(description="Applies while the zone is active")
    description_pl: Optional[str]
    description_en: Optional[str]
    contact: Optional[str] = Field(description="Zone manager to ask for the flight consent")


    @classmethod
    def from_geozone(cls, geozone: GeoZone, windows: list[ActivityWindow], active_now: bool, rule: HeightRule) -> "GeozoneProperties":
        return cls(
            id=geozone.id,
            parent_id=geozone.parent_id,
            country_id=geozone.country.id,
            country=geozone.country.name,
            type=geozone.type,
            source_type=geozone.source_type,
            tag=geozone.tag,
            lower_limit_ft=geozone.lower_limit_ft,
            upper_limit_ft=geozone.upper_limit_ft,
            valid_from=geozone.valid_from,
            valid_to=geozone.valid_to,
            activity_mode=geozone.activity_mode,
            active_now=active_now,
            activity_time=windows,
            height_rule=HeightRules.from_rule(rule),
            description_pl=geozone.description_pl,
            description_en=geozone.description_en,
            contact=geozone.contact,
        )
