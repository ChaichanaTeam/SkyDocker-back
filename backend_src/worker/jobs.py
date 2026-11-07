from typing import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import BaseModel

from backend_src import sync
from backend_src.cache import AsyncRedisSession
from backend_src.db import AsyncDBSession, AsyncSessionMaker, Queries
from .config import WorkerSettings
from .scheduler import cron, schedule


def register_jobs(scheduler: AsyncIOScheduler, redis: AsyncRedisSession) -> None:
    schedule(scheduler, "catalog", catalog_job, cron(WorkerSettings.CATALOG_CRON), redis)

    if WorkerSettings.RUN_ON_START:
        # without a trigger the job runs once right away
        scheduler.add_job(startup_job, args=[redis], id="startup", name="startup")


async def startup_job(redis: AsyncRedisSession) -> None:
    """Syncs what the database lacks, so a new database fills up without manual runs."""
    async with AsyncSessionMaker() as db:
        has_zones = await Queries.GeoZone.any_stored(db)

    if not has_zones and WorkerSettings.CATALOG_CRON:
        await catalog_job(redis)


async def catalog_job(redis: AsyncRedisSession) -> None:
    await _run_job("catalog", sync.GEO_ZONE_LOCK, sync.CATALOG_LOCK_TTL_SECONDS, sync.sync_catalog, redis)


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
