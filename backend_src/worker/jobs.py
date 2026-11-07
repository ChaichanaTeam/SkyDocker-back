from typing import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import BaseModel

from backend_src import sync
from backend_src.cache import AsyncRedisSession
from backend_src.db import AsyncDBSession, AsyncSessionMaker, Queries
from .config import WorkerSettings
from .scheduler import cron, every, schedule


def register_jobs(scheduler: AsyncIOScheduler, redis: AsyncRedisSession) -> None:
    schedule(scheduler, "catalog", catalog_job, cron(WorkerSettings.CATALOG_CRON), redis)
    schedule(scheduler, "activity", activity_job, every(WorkerSettings.ACTIVITY_INTERVAL_MINUTES), redis)

    if WorkerSettings.RUN_ON_START:
        # without a trigger the job runs once right away
        scheduler.add_job(startup_job, args=[redis], id="startup", name="startup")


async def startup_job(redis: AsyncRedisSession) -> None:
    """Syncs what the database lacks, so a new database fills up without manual runs."""
    async with AsyncSessionMaker() as db:
        has_zones = await Queries.GeoZone.any_stored(db)

    if has_zones:
        # skips stored tiles and measures only zones without a value, cheap when nothing is missing
        await terrain_job(redis)
    elif WorkerSettings.CATALOG_CRON:
        has_zones = await catalog_job(redis)

    # activity windows are matched to stored zones
    if has_zones and WorkerSettings.ACTIVITY_INTERVAL_MINUTES:
        await activity_job(redis)


async def catalog_job(redis: AsyncRedisSession) -> bool:
    """Catalog sync, then the terrain sync loads tiles for zones in new places and measures new zones."""
    if not await _run_job("catalog", sync.GEO_ZONE_LOCK, sync.CATALOG_LOCK_TTL_SECONDS, sync.sync_catalog, redis):
        return False

    await terrain_job(redis)
    return True


async def terrain_job(redis: AsyncRedisSession) -> None:
    await _run_job("terrain", sync.GEO_ZONE_LOCK, sync.TERRAIN_LOCK_TTL_SECONDS, sync.sync_terrain, redis)


async def activity_job(redis: AsyncRedisSession) -> None:
    await _run_job("activity", sync.GEO_ZONE_LOCK, sync.ACTIVITY_LOCK_TTL_SECONDS, sync.sync_activity, redis)


async def _run_job(
    job: str, lock: str, lock_ttl_seconds: int, action: Callable[[AsyncDBSession], Awaitable[BaseModel]],
    redis: AsyncRedisSession,
) -> bool:
    """Whether the sync succeeded; a failed one is logged by run_sync and tried again at its next run."""
    async with AsyncSessionMaker() as db:
        try:
            await sync.run_sync(job, lock, lock_ttl_seconds, lambda: action(db), redis)
        except Exception:
            return False

    return True
