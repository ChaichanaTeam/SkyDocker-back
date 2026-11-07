from typing import Awaitable, Callable, TypeVar

from backend_src.cache import AsyncRedisSession, acquire_sync_lock, release_sync_lock
from .errors import SyncBusy


Report = TypeVar("Report")


async def run_sync(
    job: str, lock: str, lock_ttl_seconds: int, action: Callable[[], Awaitable[Report]], redis: AsyncRedisSession,
) -> Report:
    """Runs the sync while holding the lock, SyncBusy when another run holds it."""
    token = await acquire_sync_lock(redis, lock, lock_ttl_seconds)
    if token is None:
        held_by = f"the {job} sync is" if job == lock else f"another {lock} sync is"
        raise SyncBusy(f"Sync did not start, {held_by} already running")

    try:
        return await action()
    finally:
        await release_sync_lock(redis, lock, token)
