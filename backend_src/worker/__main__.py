import argparse
import asyncio
import sys

from .app import is_alive, serve


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m backend_src.worker", description="Scheduled data syncs")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve", help="run the scheduled syncs until stopped")
    commands.add_parser("health", help="exit 0 while a running worker keeps its heartbeat, for the container healthcheck")

    args = parser.parse_args()
    if args.command == "serve":
        asyncio.run(serve())
    elif args.command == "health":
        sys.exit(0 if asyncio.run(is_alive()) else 1)


if __name__ == "__main__":
    main()
