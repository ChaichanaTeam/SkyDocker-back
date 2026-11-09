from functools import partial
from typing import Awaitable, Callable

from loguru import logger
from pydantic import BaseModel
from redis.asyncio import Redis

from backend_src import sync
from backend_src.cache import AsyncRedisSession
from backend_src.core.config import Settings
from backend_src.core.logger import setup_logging
from backend_src.db import AsyncDBSession, AsyncSessionMaker, Queries
from .constants import EXIT_BUSY, EXIT_FAILED, WORKER_LOG_FILE


Action = Callable[[AsyncDBSession], Awaitable[BaseModel]]

# job -> lock, its TTL and the sync; borders are run per country
_SYNCS: dict[str, tuple[str, int, Action]] = {
    "catalog": (sync.GEO_ZONE_LOCK, sync.CATALOG_LOCK_TTL_SECONDS, sync.sync_catalog),
    "terrain": (sync.GEO_ZONE_LOCK, sync.TERRAIN_LOCK_TTL_SECONDS, sync.sync_terrain),
    "activity": (sync.GEO_ZONE_LOCK, sync.ACTIVITY_LOCK_TTL_SECONDS, sync.sync_activity),
}

# The same order as the worker start: borders and activity need the catalog, the catalog is followed by the terrain
RUN_ORDER = {
    "catalog": ("catalog", "terrain"),
    "terrain": ("terrain",),
    "activity": ("activity",),
    "border": ("border",),
    "all": ("catalog", "terrain", "border", "activity"),
}


async def run_once(job: str) -> int:
    """Runs the syncs of the job right away, without retries; the exit code of the first one that did not succeed."""
    setup_logging(WORKER_LOG_FILE)
    redis = Redis.from_url(Settings.REDIS_URL) # type: ignore[arg-type]
    try:
        for step in RUN_ORDER[job]:
            code = await _run_step(step, redis)
            if code:
                return code
        return 0
    finally:
        await redis.aclose()
        await logger.complete()


async def _run_step(step: str, redis: AsyncRedisSession) -> int:
    if step != "border":
        lock, lock_ttl_seconds, action = _SYNCS[step]
        return await _run_sync(step, lock, lock_ttl_seconds, action, redis)

    async with AsyncSessionMaker() as db:
        country_tags = [country.country_tag for country in await Queries.Country.get_with_geo_zones(db)]

    if not country_tags:
        logger.error("No country has geo-zones yet, run the catalog sync first")
        return EXIT_FAILED

    codes = []
    for country_tag in country_tags:
        lock = sync.border_lock(country_tag)
        codes.append(await _run_sync(
            lock, lock, sync.BORDER_LOCK_TTL_SECONDS, partial(sync.sync_border_by_tag, country_tag), redis,
        ))
    return max(codes)


async def _run_sync(job: str, lock: str, lock_ttl_seconds: int, action: Action, redis: AsyncRedisSession) -> int:
    async with AsyncSessionMaker() as db:
        try:
            await sync.run_sync(job, lock, lock_ttl_seconds, lambda: action(db), redis, "cli")
        except sync.SyncBusy:
            return EXIT_BUSY
        except Exception:
            # run_sync has logged it
            return EXIT_FAILED

    return 0
