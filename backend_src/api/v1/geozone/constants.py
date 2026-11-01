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

FEET_PER_METRE = 1 / 0.3048

# The map height filter adds it to the highest ground of a zone: DEM error and flight-level limits
# that move with air pressure, better to show a zone than to hide one the drone can reach
MAP_HEIGHT_MARGIN_M = 50
