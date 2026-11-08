import re
from dataclasses import dataclass
from typing import Optional

from backend_src.models.enum import GeoZoneActivityMode, GeoZoneType
from .schema import Zone


# Class of each PANSA zone type, after the PANSA table "Strefy geograficzne oraz ogólne zasady lotów"
# (pansa.pl/strefy-geograficzne) and the /v1/zones/types descriptions
TYPE_CLASS: dict[str, GeoZoneType] = {
    "DRAP": GeoZoneType.DRA_P,
    "TSA": GeoZoneType.DRA_P,
    "MRT": GeoZoneType.DRA_P,
    "TMA": GeoZoneType.DRA_P,
    "MTMA": GeoZoneType.DRA_P,
    "TFR": GeoZoneType.DRA_P,

    "DRAR": GeoZoneType.DRA_R,
    "TRA": GeoZoneType.DRA_R,
    "MCTR": GeoZoneType.DRA_R,
    "R": GeoZoneType.DRA_R,
    "P": GeoZoneType.DRA_R,
    "RPA": GeoZoneType.DRA_R,

    # CTR and ATZ further than 6 km from the airport
    "CTR": GeoZoneType.DRA_RH,
    "ATZ": GeoZoneType.DRA_RH,

    "CTR6KM": GeoZoneType.DRA_RM,
    "ATZ6KM": GeoZoneType.DRA_RM,

    "CTR1KM": GeoZoneType.DRA_RL,
    "ATZ1KM": GeoZoneType.DRA_RL,
    "MCTR2KM": GeoZoneType.DRA_RL,
    "D": GeoZoneType.DRA_RL,

    "DRAI": GeoZoneType.DRA_I,
    "RMZ": GeoZoneType.DRA_I,
    "AREA": GeoZoneType.DRA_I,
    "AAA": GeoZoneType.DRA_I,
    "NW": GeoZoneType.DRA_I,
    "ADIZ": GeoZoneType.DRA_I,
    "FIS": GeoZoneType.DRA_I,
    "ROL": GeoZoneType.DRA_I,
    "EA": GeoZoneType.DRA_I,
}

# Unknown types get the class that asks for the zone manager consent
UNKNOWN_TYPE_CLASS = GeoZoneType.DRA_R

# Flexible zones, active only within AUP/UUP reservations or NOTAM windows
SCHEDULED_TYPES = {"TRA", "TSA", "MRT", "D", "R", "ATZ"}

# 1 km and 6 km rings of an ATZ, active while the ATZ itself is active
INHERITED_TYPES = {"ATZ1KM", "ATZ6KM"}

_RESTRICTED_SUBCLASS = {"RH": GeoZoneType.DRA_RH, "RM": GeoZoneType.DRA_RM, "RL": GeoZoneType.DRA_RL}

# "DRA-RL 1840", "DRA-RL0766", "`DRA-RM 289 NBP ..."
_NAME_SUBCLASS = re.compile(r"^\W*DRA-(RH|RM|RL)(?![A-Z])")
# RPA descriptions start with "DRA-RH geozone." / "DRA-RL strefa geograficzna."
_DESCRIPTION_SUBCLASS = re.compile(r"^\s*DRA-(RH|RM|RL)(?![A-Z])")


@dataclass(frozen=True)
class Classification:
    type: GeoZoneType
    activity_mode: GeoZoneActivityMode


def classify(zone: Zone) -> Classification:
    return Classification(type=zone_class(zone), activity_mode=activity_mode(zone))


def zone_class(zone: Zone) -> GeoZoneType:
    zone_type = TYPE_CLASS.get(zone.type, UNKNOWN_TYPE_CLASS)

    # A plain DRA-R can be narrowed to RH/RM/RL by the zone itself, never widened from DRA-P
    if zone_type is GeoZoneType.DRA_R:
        subclass = _subclass(_NAME_SUBCLASS, zone.name) or _subclass(_DESCRIPTION_SUBCLASS, _description(zone))
        if subclass is not None:
            return subclass

    return zone_type


def activity_mode(zone: Zone) -> GeoZoneActivityMode:
    if zone.type in SCHEDULED_TYPES:
        return GeoZoneActivityMode.SCHEDULED

    # Without the parent we can't tell when the ring is active, so treat it as always active
    if zone.type in INHERITED_TYPES and zone.master:
        return GeoZoneActivityMode.INHERITED

    return GeoZoneActivityMode.PERMANENT


def _subclass(pattern: re.Pattern[str], text: Optional[str]) -> Optional[GeoZoneType]:
    match = pattern.match(text or "")
    return _RESTRICTED_SUBCLASS[match[1]] if match else None


def _description(zone: Zone) -> Optional[str]:
    if zone.description is None:
        return None
    return zone.description.pl or zone.description.en
