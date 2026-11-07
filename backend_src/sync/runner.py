import asyncio
import time
from datetime import datetime, timezone
from typing import Awaitable, Callable, TypeVar

from loguru import logger
from pydantic import BaseModel

from backend_src.cache import AsyncRedisSession, acquire_sync_lock, release_sync_lock
from .errors import SyncBusy, SyncError
from .status import Trigger, record_status


Report = TypeVar("Report", bound=BaseModel)


async def run_sync(
    job: str, lock: str, lock_ttl_seconds: int, action: Callable[[], Awaitable[Report]], redis: AsyncRedisSession,
    trigger: Trigger,
) -> Report:
    """Runs the sync while holding the lock, logs how it went and keeps it as the last run of the job.

    SyncBusy when another run holds the lock. Whatever it raises is already logged.
    """
    started_at = datetime.now(timezone.utc)
    try:
        token = await acquire_sync_lock(redis, lock, lock_ttl_seconds)
    except Exception:
        logger.exception(f"Sync {job} did not start, the {lock} lock cannot be taken")
        raise

    if token is None:
        held_by = f"the {job} sync is" if job == lock else f"another {lock} sync is"
        logger.warning(f"Sync {job} skipped, {held_by} already running")
        await record_status(redis, job, "skipped", trigger, started_at, f"{held_by} already running")
        raise SyncBusy(f"Sync did not start, {held_by} already running")

    await record_status(redis, job, "running", trigger, started_at)
    started = time.monotonic()
    try:
        report = await action()
    except SyncError as exc:
        logger.error(f"Sync {job} failed after {time.monotonic() - started:.1f}s: {exc}")
        await record_status(redis, job, "failed", trigger, started_at, str(exc))
        raise
    except Exception as exc:
        logger.exception(f"Sync {job} crashed after {time.monotonic() - started:.1f}s")
        await record_status(redis, job, "failed", trigger, started_at, f"crashed: {exc!r}")
        raise
    except asyncio.CancelledError:
        logger.warning(f"Sync {job} stopped after {time.monotonic() - started:.1f}s, the worker is stopping")
        await record_status(redis, job, "failed", trigger, started_at, "stopped with the worker")
        raise
    finally:
        await release_sync_lock(redis, lock, token)

    summary = summarize(report)
    logger.info(f"Sync {job} ok in {time.monotonic() - started:.1f}s: {summary}")
    await record_status(redis, job, "ok", trigger, started_at, summary)
    return report


def summarize(report: BaseModel) -> str:
    """Counts of a sync report on one line, lists by their length, e.g. "fetched 3159, inserted 0, errors 0"."""
    parts = []
    for name, value in report:
        if isinstance(value, BaseModel):
            parts.append(f"{name} ({summarize(value)})")
        elif isinstance(value, list):
            parts.append(f"{name} {len(value)}")
        elif isinstance(value, int):
            parts.append(f"{name} {value}")

    return ", ".join(parts)
