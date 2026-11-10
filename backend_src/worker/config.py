import os
from dataclasses import dataclass
from typing import Optional

from backend_src.core.config import Settings  # noqa: F401, loads .env


def _cron(name: str, default: str) -> Optional[str]:
    """Cron expression of a job; set but empty disables the job."""
    return os.getenv(name, default).strip() or None


def _minutes(name: str, default: int) -> int:
    """Interval of a job in minutes; set but empty, or 0, disables the job."""
    value = os.getenv(name, str(default)).strip()
    return int(value) if value else 0


def _delays(name: str, default: str) -> list[int]:
    """Comma separated minutes, e.g. "5,15,45"; set but empty disables retries."""
    return [int(minutes) for minutes in os.getenv(name, default).split(",") if minutes.strip()]


@dataclass(frozen=True)
class WorkerSettings:
    # Cron expressions are read in this time zone
    TIMEZONE                        = os.getenv("SYNC_TIMEZONE") or "Europe/Warsaw"

    CATALOG_CRON                    = _cron("SYNC_CATALOG_CRON", "0 3 * * *")
    # PANSA got no answer about the API load yet, so activity is polled rarely by default
    ACTIVITY_INTERVAL_MINUTES       = _minutes("SYNC_ACTIVITY_INTERVAL_MINUTES", 360)
    BORDER_CRON                     = _cron("SYNC_BORDER_CRON", "0 4 1 * *")

    # Pauses before the retries of a sync whose data source failed, one retry per pause
    RETRY_DELAYS_MINUTES            = _delays("SYNC_RETRY_DELAYS_MINUTES", "5,15,45")
    # The next activity run comes soon anyway
    ACTIVITY_RETRY_DELAYS_MINUTES   = _delays("SYNC_ACTIVITY_RETRY_DELAYS_MINUTES", "15")

    # Sync what the database lacks when the worker starts, e.g. a new database
    RUN_ON_START                    = os.getenv("SYNC_RUN_ON_START", "1").strip().lower() in ("1", "true", "yes")

    # Moderator profiles for `python -m backend_src.worker seed moderators`, relative to the working directory
    SEED_MODERATORS_FILE            = os.getenv("SEED_MODERATORS_FILE") or "data/seed/moderators.json"
