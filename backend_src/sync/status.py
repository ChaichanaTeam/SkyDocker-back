from datetime import datetime, timezone
from typing import Literal, Optional

from loguru import logger
from pydantic import BaseModel, Field

from backend_src.cache import AsyncRedisSession, get_sync_status, save_sync_status


RunStatus = Literal["running", "ok", "skipped", "retrying", "failed"]

# Who started a run: the schedule, a retry of a failed run, the worker start, an admin endpoint or the CLI
Trigger = Literal["schedule", "retry", "startup", "admin", "cli"]


class SyncStatus(BaseModel):
    """Last run of a sync, kept in Redis."""

    status: RunStatus
    trigger: Trigger
    started_at: datetime
    finished_at: Optional[datetime] = None
    retry_at: Optional[datetime] = None
    summary: Optional[str] = Field(None, description="Counts of the report or why the run failed, only for the logs")


async def record_status(
    redis: AsyncRedisSession, job: str, status: RunStatus, trigger: Trigger, started_at: datetime,
    summary: Optional[str] = None,
) -> None:
    finished_at = None if status == "running" else datetime.now(timezone.utc)
    run = SyncStatus(status=status, trigger=trigger, started_at=started_at, finished_at=finished_at, summary=summary)
    await _save(redis, job, run)


async def record_retry(redis: AsyncRedisSession, job: str, retry_at: datetime) -> None:
    """Marks the failed last run as one that will be tried again."""
    try:
        stored = await get_sync_status(redis, job)
    except Exception:
        logger.exception(f"Status of sync {job} cannot be read")
        return

    if stored is not None:
        await _save(redis, job, SyncStatus(**{**stored, "status": "retrying", "retry_at": retry_at}))


async def _save(redis: AsyncRedisSession, job: str, run: SyncStatus) -> None:
    # the status is only informative, a sync must not fail because Redis did not take it
    try:
        await save_sync_status(redis, job, run.model_dump(mode="json"))
    except Exception:
        logger.exception(f"Status of sync {job} cannot be saved")
