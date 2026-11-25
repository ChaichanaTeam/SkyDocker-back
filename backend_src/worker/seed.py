from pathlib import Path

from loguru import logger

from backend_src.core.logger import setup_logging
from backend_src.db import AsyncSessionMaker
from backend_src.seed import SeedError, load_moderators, seed_moderators
from backend_src.sync.runner import summarize
from .constants import EXIT_FAILED, WORKER_LOG_FILE


SEED_TARGETS = ("moderators",)


async def run_seed(target: str, file: str) -> int:
    """Seeds the profiles of the file and exits: 0 ok, 1 the file is invalid or the database failed."""
    setup_logging(WORKER_LOG_FILE)
    try:
        profiles = load_moderators(Path(file))
        async with AsyncSessionMaker() as db:
            report = await seed_moderators(profiles, db)
    except SeedError as exc:
        logger.error(f"Seed {target} failed: {exc}")
        return EXIT_FAILED
    except Exception:
        logger.exception(f"Seed {target} crashed")
        return EXIT_FAILED
    finally:
        await logger.complete()

    logger.info(f"Seed {target} ok: {summarize(report)}")
    for email in report.created:
        logger.info(f"Seed {target}: created {email}")
    await logger.complete()
    return 0
