from datetime import datetime
from typing import Optional

from backend_src.models import GeoZone, GeoZoneActivityMode


def schedule_owner(zone: GeoZone) -> Optional[int]:
    """Zone whose activity windows apply to this one, None for zones that are active all the time."""
    if zone.activity_mode is GeoZoneActivityMode.SCHEDULED:
        return zone.id

    # an inherited zone whose parent is missing from the catalog stays active, as a permanent one
    if zone.activity_mode is GeoZoneActivityMode.INHERITED:
        return zone.parent_id

    return None


def reachable(lower_limit_ft: int, ceiling_ft: Optional[int]) -> bool:
    """Whether a flight up to the ceiling enters a zone or an activity window starting at the lower limit."""
    return ceiling_ft is None or lower_limit_ft < ceiling_ft


def valid_between(zone: GeoZone, starts_at: datetime, ends_at: datetime) -> bool:
    """Whether the zone is published for at least part of the period."""
    return (zone.valid_from is None or zone.valid_from < ends_at) and (zone.valid_to is None or zone.valid_to > starts_at)
