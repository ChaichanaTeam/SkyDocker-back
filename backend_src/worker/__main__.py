import argparse
import asyncio
import sys

from .app import is_alive, serve
from .cli import RUN_ORDER, run_once
from .config import WorkerSettings
from .seed import SEED_TARGETS, run_seed


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m backend_src.worker", description="Scheduled data syncs")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve", help="run the scheduled syncs until stopped")
    run = commands.add_parser(
        "run", help="run a sync now and exit: 0 ok, 1 failed, 2 did not start because another sync is running",
    )
    run.add_argument("job", choices=RUN_ORDER, help="catalog is followed by terrain; all runs every sync in order")
    seed = commands.add_parser(
        "seed", help="create the missing profiles from a JSON file and exit: 0 ok, 1 failed; existing ones are kept",
    )
    seed.add_argument("target", choices=SEED_TARGETS)
    seed.add_argument("--file", default=WorkerSettings.SEED_MODERATORS_FILE, help="seed file (env: SEED_MODERATORS_FILE)")
    commands.add_parser("health", help="exit 0 while a running worker keeps its heartbeat, for the container healthcheck")

    args = parser.parse_args()
    if args.command == "serve":
        asyncio.run(serve())
    elif args.command == "run":
        sys.exit(asyncio.run(run_once(args.job)))
    elif args.command == "seed":
        sys.exit(asyncio.run(run_seed(args.target, args.file)))
    elif args.command == "health":
        sys.exit(0 if asyncio.run(is_alive()) else 1)


if __name__ == "__main__":
    main()
