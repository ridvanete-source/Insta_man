"""Command-line entrypoint.

Usage:
    python -m insta_man.cli run        # publish whatever is due now
    python -m insta_man.cli list       # show queue status
    python -m insta_man.cli validate   # sanity-check config + queue file
"""

from __future__ import annotations

import argparse
import logging
import sys

from insta_man.config import load_config
from insta_man.queue import ContentQueue
from insta_man.scheduler import run_once


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(prog="insta_man")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run", help="Publish all posts currently due.")
    subparsers.add_parser("list", help="List queue entries and their status.")
    subparsers.add_parser("validate", help="Validate config and queue file without publishing.")

    args = parser.parse_args(argv)

    if args.command == "run":
        for line in run_once():
            print(line)
        return 0

    if args.command == "list":
        config = load_config()
        queue = ContentQueue(config.queue_file)
        if not queue.posts:
            print(f"Queue is empty ({config.queue_file}).")
            return 0
        for post in queue.posts:
            print(f"{post.id:20s} {post.status.value:10s} {post.scheduled_at.isoformat()}")
        return 0

    if args.command == "validate":
        config = load_config()
        queue = ContentQueue(config.queue_file)
        print(f"Publisher backend : {config.publisher}")
        print(f"Queue file        : {config.queue_file} ({'exists' if config.queue_file.exists() else 'MISSING'})")
        print(f"Posts in queue    : {len(queue.posts)}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
