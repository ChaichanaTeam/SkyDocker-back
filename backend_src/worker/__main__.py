import argparse
import asyncio

from .app import serve


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m backend_src.worker", description="Scheduled data syncs")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve", help="run the scheduled syncs until stopped")

    args = parser.parse_args()
    if args.command == "serve":
        asyncio.run(serve())


if __name__ == "__main__":
    main()
