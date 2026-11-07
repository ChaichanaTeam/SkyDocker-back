from pathlib import Path


DEFAULT_COUNTRY_NAME = "Poland"
DEFAULT_COUNTRY_TAG = "PL"

# Raw PANSA responses of the last sync, kept for debugging
PANSA_SNAPSHOT_DIR = Path("data") / "pansa"

# A much shorter zone list from PANSA means a broken response, not removed zones
MIN_ZONES_RATIO = 0.7

MAX_REPORTED_ERRORS = 20

# How far ahead repeating NOTAM schedules are expanded into windows
ACTIVITY_HORIZON_DAYS = 7

# Catalog, activity and terrain write the same zones and windows, the catalog deletes zones with their windows
GEO_ZONE_LOCK = "geo-zone"

# A lock outlives a crashed run only by its TTL, long enough for a slow run to finish first
CATALOG_LOCK_TTL_SECONDS = 30 * 60
TERRAIN_LOCK_TTL_SECONDS = 30 * 60
ACTIVITY_LOCK_TTL_SECONDS = 10 * 60
BORDER_LOCK_TTL_SECONDS = 10 * 60


def border_lock(country_tag: str) -> str:
    return f"border:{country_tag}"
