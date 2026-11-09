import asyncio
import signal

from loguru import logger
from redis.asyncio import Redis

from backend_src.cache import AsyncRedisSession, beat_worker_heartbeat, is_worker_alive
from backend_src.core.config import Settings
from backend_src.core.logger import setup_logging
from .constants import HEARTBEAT_INTERVAL_SECONDS, HEARTBEAT_TTL_SECONDS, STOP_TIMEOUT_SECONDS, WORKER_LOG_FILE
from .jobs import SyncJobs
from .scheduler import create_scheduler


async def serve() -> None:
    """Runs the scheduled syncs until the worker is stopped."""
    setup_logging(WORKER_LOG_FILE)
    redis = Redis.from_url(Settings.REDIS_URL) # type: ignore[arg-type]
    scheduler = create_scheduler()
    SyncJobs(scheduler, redis).register()
    scheduler.add_job(_beat, "interval", seconds=HEARTBEAT_INTERVAL_SECONDS, args=[redis], id="heartbeat", name="heartbeat")

    await _beat(redis)
    scheduler.start()
    logger.info("Worker started")
    try:
        await _wait_for_stop()
    finally:
        # cancels running syncs, they release their locks while Redis is still open
        scheduler.shutdown(wait=False)
        await _wait_for_running_jobs()
        await redis.aclose()
        logger.info("Worker stopped")
        await logger.complete()


async def _wait_for_running_jobs() -> None:
    running = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if running:
        await asyncio.wait(running, timeout=STOP_TIMEOUT_SECONDS)


async def is_alive() -> bool:
    """Whether a running worker refreshed its heartbeat lately."""
    redis = Redis.from_url(Settings.REDIS_URL) # type: ignore[arg-type]
    try:
        return await is_worker_alive(redis)
    finally:
        await redis.aclose()


async def _beat(redis: AsyncRedisSession) -> None:
    try:
        await beat_worker_heartbeat(redis, HEARTBEAT_TTL_SECONDS)
    except Exception:
        logger.exception("Worker heartbeat cannot be saved")


async def _wait_for_stop() -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()

    for stop_signal in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(stop_signal, stop.set)
        except NotImplementedError:
            # no asyncio signal handlers on Windows, Ctrl+C still ends asyncio.run there
            pass

    await stop.wait()
