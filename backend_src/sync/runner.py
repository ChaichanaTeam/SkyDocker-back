import time
from typing import Awaitable, Callable, TypeVar

from loguru import logger
from pydantic import BaseModel

from backend_src.cache import AsyncRedisSession, acquire_sync_lock, release_sync_lock
from .errors import SyncBusy, SyncError


Report = TypeVar("Report", bound=BaseModel)


async def run_sync(
    job: str, lock: str, lock_ttl_seconds: int, action: Callable[[], Awaitable[Report]], redis: AsyncRedisSession,
) -> Report:
    """Runs the sync while holding the lock and logs how it went, SyncBusy when another run holds the lock."""
    token = await acquire_sync_lock(redis, lock, lock_ttl_seconds)
    if token is None:
        held_by = f"the {job} sync is" if job == lock else f"another {lock} sync is"
        logger.warning(f"Sync {job} skipped, {held_by} already running")
        raise SyncBusy(f"Sync did not start, {held_by} already running")

    started = time.monotonic()
    try:
        report = await action()
    except SyncError as exc:
        logger.error(f"Sync {job} failed after {time.monotonic() - started:.1f}s: {exc}")
        raise
    except Exception:
        logger.exception(f"Sync {job} crashed after {time.monotonic() - started:.1f}s")
        raise
    finally:
        await release_sync_lock(redis, lock, token)

    logger.info(f"Sync {job} ok in {time.monotonic() - started:.1f}s: {summarize(report)}")
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
