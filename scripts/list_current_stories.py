"""One-off diagnostic: list currently active Instagram Stories on the account.

Read-only - does not delete or modify anything. Used to identify duplicate
Story uploads left over from the 2026-09-10 hourly-reshare bug (see the fix
in scripts/boost_visibility.py) before deciding what to delete. This is a
personal account (not a dedicated bot account), so an automated delete-by-
guess is too risky - a human should look at this list and pick what to
remove via scripts/delete_stories.py.

Usage: python scripts/list_current_stories.py
"""

from __future__ import annotations

from insta_man.config import load_config
from insta_man.publishers import get_publisher
from insta_man.publishers.instagrapi_adapter import InstagrapiPublisher


def main() -> None:
    config = load_config()
    publisher = get_publisher(config)
    if not isinstance(publisher, InstagrapiPublisher):
        print("This script only supports the instagrapi backend.")
        return

    publisher.authenticate()
    client = publisher._get_client()

    stories = client.user_stories(client.user_id)
    if not stories:
        print("No active stories right now.")
        return

    print(f"{len(stories)} active stories (newest first):")
    for s in sorted(stories, key=lambda x: x.taken_at, reverse=True):
        print(
            f"pk={s.pk} taken_at={s.taken_at.isoformat()} media_type={s.media_type} "
            f"thumbnail={s.thumbnail_url}"
        )


if __name__ == "__main__":
    main()
