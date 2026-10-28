import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from backend_src.models.enum import GeoZoneType


OPEN_CATEGORY_MAX_M = 120


@dataclass(frozen=True)
class HeightRule:
    """Heights above ground for an active zone, after PANSA rules for the open category.

    Up to ``free_m`` the flight needs only a check-in, between ``free_m`` and ``max_m``
    it needs the zone manager consent or an approved mission plan, above ``max_m`` it is not allowed.
    """

    free_m: int
    # free_m applies only to drones up to this take-off mass, None means any mass
    free_max_mass_g: Optional[int]
    max_m: int


PROHIBITED = HeightRule(free_m=0, free_max_mass_g=None, max_m=0)
CONSENT = HeightRule(free_m=0, free_max_mass_g=None, max_m=OPEN_CATEGORY_MAX_M)
INFORMATION = HeightRule(free_m=OPEN_CATEGORY_MAX_M, free_max_mass_g=None, max_m=OPEN_CATEGORY_MAX_M)

CLASS_RULES: dict[GeoZoneType, HeightRule] = {
    GeoZoneType.DRA_P: PROHIBITED,
    GeoZoneType.DRA_R: CONSENT,
    GeoZoneType.DRA_RH: CONSENT,
    GeoZoneType.DRA_RM: CONSENT,
    GeoZoneType.DRA_RL: CONSENT,
    GeoZoneType.DRA_T: CONSENT,
    GeoZoneType.DRA_U: CONSENT,
    GeoZoneType.DRA_I: INFORMATION,
}

# Airport zones where part of the flights needs no consent
SOURCE_TYPE_RULES: dict[str, HeightRule] = {
    "CTR": HeightRule(free_m=100, free_max_mass_g=25_000, max_m=OPEN_CATEGORY_MAX_M),
    "ATZ": HeightRule(free_m=100, free_max_mass_g=25_000, max_m=OPEN_CATEGORY_MAX_M),
    "CTR6KM": HeightRule(free_m=30, free_max_mass_g=900, max_m=OPEN_CATEGORY_MAX_M),
    "ATZ6KM": HeightRule(free_m=30, free_max_mass_g=900, max_m=OPEN_CATEGORY_MAX_M),
}

# DTM zones: VLOS/FPV up to 50 m AGL with a check-in, higher with a mission plan
DTM_RULE = HeightRule(free_m=50, free_max_mass_g=None, max_m=OPEN_CATEGORY_MAX_M)

# RPA descriptions, e.g. "UAVs with a take-off mass of up to 900 g, up to a height of 30 m above ground level (AGL)
# - you do not need to submit a mission plan"
_RPA_FREE_FLIGHT = re.compile(
    r"take-off mass of up to (\d+)\s*(g|kg),? up to a height of (\d+) m above ground level \(AGL\)\s*[-–]\s*"
    r"you do not need to submit a mission plan"
)


def height_rule(zone_type: GeoZoneType, source_type: str, tag: str, description_en: Optional[str]) -> HeightRule:
    if source_type == "RPA":
        return _rpa_rule(description_en) or CLASS_RULES.get(zone_type, CONSENT)

    if "DTM" in tag.split() and zone_type is not GeoZoneType.DRA_P:
        return DTM_RULE

    if source_type in SOURCE_TYPE_RULES:
        return SOURCE_TYPE_RULES[source_type]

    return CLASS_RULES.get(zone_type, CONSENT)


@lru_cache(maxsize=64)
def _rpa_rule(description_en: Optional[str]) -> Optional[HeightRule]:
    matches = _RPA_FREE_FLIGHT.findall(description_en or "")
    if not matches:
        return None

    mass, unit, height = max(matches, key=lambda match: int(match[2]))
    return HeightRule(
        free_m=min(int(height), OPEN_CATEGORY_MAX_M),
        free_max_mass_g=int(mass) * (1000 if unit == "kg" else 1),
        max_m=OPEN_CATEGORY_MAX_M,
    )
