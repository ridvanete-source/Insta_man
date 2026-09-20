"""One-off test: does instagrapi's native media_share_to_story render correctly?

CONFIRMED STILL BROKEN (2026-09-20, instagrapi 3.0.2): posts a plain black
story with no tap-through sticker - same failure as the original 2026-08-04
finding that made boost_visibility.py switch to a disconnected re-upload
instead (and that reshare path has now been disabled entirely as a result,
see RESHARE_ENABLED in boost_visibility.py - it can't drive real views to
the original post either). Kept here in case a future instagrapi release is
worth re-testing. This script does NOT modify boost_visibility.py - it just
posts one test Story via the native call so the result can be inspected,
then leaves cleanup to the operator (scripts/delete_stories.py).

Usage: python scripts/test_native_reshare.py <platform_post_id>
"""

from __future__ import annotations

import sys

from insta_man.config import load_config
from insta_man.publishers import get_publisher
from insta_man.publishers.instagrapi_adapter import InstagrapiPublisher


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_native_reshare.py <platform_post_id>")
        return
    media_pk = sys.argv[1]

    config = load_config()
    publisher = get_publisher(config)
    if not isinstance(publisher, InstagrapiPublisher):
        print("This script only supports the instagrapi backend.")
        return

    publisher.authenticate()
    client = publisher._get_client()

    story = client.media_share_to_story(media_pk)
    print(f"[native-reshare] posted story pk={story.pk}")

    stories = client.user_stories(client.user_id)
    match = next((s for s in stories if str(s.pk) == str(story.pk)), None)
    if match:
        print(f"thumbnail_url={match.thumbnail_url}")
    else:
        print("Story not found in user_stories() right after posting (unexpected).")


if __name__ == "__main__":
    main()
