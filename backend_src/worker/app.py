import asyncio
import signal

from loguru import logger

from backend_src.core.logger import setup_logging
from .constants import WORKER_LOG_FILE
from .scheduler import create_scheduler


async def serve() -> None:
    """Runs the scheduled syncs until the worker is stopped."""
    setup_logging(WORKER_LOG_FILE)
    scheduler = create_scheduler()

    scheduler.start()
    logger.info("Worker started")
    try:
        await _wait_for_stop()
    finally:
        scheduler.shutdown(wait=False)
        logger.info("Worker stopped")


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
