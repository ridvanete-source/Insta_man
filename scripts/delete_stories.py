"""One-off diagnostic: delete specific Instagram Stories by pk.

Only deletes the exact pks passed on the command line - never auto-detects
what to remove. Meant to be used after reviewing the output of
scripts/list_current_stories.py (2026-09-10 duplicate-Story cleanup, see
scripts/boost_visibility.py fix).

Usage: python scripts/delete_stories.py <pk1> [pk2 ...]
"""

from __future__ import annotations

import sys

from insta_man.config import load_config
from insta_man.publishers import get_publisher
from insta_man.publishers.instagrapi_adapter import InstagrapiPublisher


def main() -> None:
    pks = [p for p in sys.argv[1:] if p.strip()]
    if not pks:
        print("No pks given, nothing to delete.")
        return

    config = load_config()
    publisher = get_publisher(config)
    if not isinstance(publisher, InstagrapiPublisher):
        print("This script only supports the instagrapi backend.")
        return

    publisher.authenticate()
    client = publisher._get_client()

    for pk in pks:
        try:
            if hasattr(client, "story_delete"):
                client.story_delete(pk)
            else:
                client.media_delete(pk)
            print(f"[deleted] {pk}")
        except Exception as exc:
            print(f"[failed] {pk}: {exc}")


if __name__ == "__main__":
    main()
