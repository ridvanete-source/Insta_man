"""Safe, ToS-compliant visibility actions for already-posted content.

Deliberately does NOT do follow/unfollow, liking, or commenting on other
accounts - those are classic "growth bot" patterns that violate Instagram's
Terms of Use and raise the same account-restriction risk already seen on
this project (see CLAUDE.md). Instead this script only:

1. Logs like/comment counts for posted items over time (content-strategy
   signal - which topics/hashtags actually perform).
2. Reshares an older, well-cooled-down post to Story via instagrapi's native
   `media_share_to_story` - the same "share to story" action available in
   the app UI, just automated. Rate-limited to at most once per run and at
   least MIN_GAP_BETWEEN_RESHARES apart, picking the least-recently-reshared
   eligible post first.

State is kept in content_library/visibility_state.json (committed to git,
same pattern as queue.yaml) so history survives across runs/machines.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from insta_man.config import load_config
from insta_man.models import PostStatus, PostTarget
from insta_man.publishers import get_publisher
from insta_man.publishers.instagrapi_adapter import InstagrapiPublisher
from insta_man.queue.content_queue import ContentQueue

STATE_FILE = Path("content_library/visibility_state.json")
MIN_POST_AGE_FOR_RESHARE = timedelta(days=3)
MIN_GAP_BETWEEN_RESHARES = timedelta(hours=20)


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"posts": {}, "last_reshare_at": None}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )


def main() -> None:
    config = load_config()
    publisher = get_publisher(config)
    if not isinstance(publisher, InstagrapiPublisher):
        print("Visibility actions only support the instagrapi backend, skipping.")
        return

    publisher.authenticate()
    queue = ContentQueue(config.queue_file)
    state = _load_state()
    now = datetime.now(timezone.utc)

    posted = [p for p in queue.posts if p.status == PostStatus.POSTED and p.platform_post_id]
    # Stories are ephemeral (expire after 24h) - media_info/reshare don't apply.
    feed_posted = [p for p in posted if p.target == PostTarget.FEED]

    for post in feed_posted:
        try:
            eng = publisher.get_engagement(post.platform_post_id)
        except Exception as exc:
            print(f"[engagement] {post.id}: failed ({exc})")
            continue
        entry = state["posts"].setdefault(post.platform_post_id, {"id": post.id, "history": []})
        entry["history"].append({"at": now.isoformat(), **eng})
        entry["like_count"] = eng["like_count"]
        entry["comment_count"] = eng["comment_count"]
        print(f"[engagement] {post.id}: {eng['like_count']} likes, {eng['comment_count']} comments")

    last_reshare_at = (
        datetime.fromisoformat(state["last_reshare_at"]) if state.get("last_reshare_at") else None
    )
    can_reshare_now = last_reshare_at is None or (now - last_reshare_at) >= MIN_GAP_BETWEEN_RESHARES

    if can_reshare_now:
        candidates = [
            p
            for p in feed_posted
            if p.published_at and (now - p.published_at) >= MIN_POST_AGE_FOR_RESHARE
        ]

        def _last_reshared(p):
            entry = state["posts"].get(p.platform_post_id, {})
            ts = entry.get("last_reshared_at")
            return datetime.fromisoformat(ts) if ts else datetime.min.replace(tzinfo=timezone.utc)

        candidates.sort(key=_last_reshared)
        if candidates:
            chosen = candidates[0]
            try:
                publisher.reshare_to_story(chosen.platform_post_id)
                print(f"[reshare] {chosen.id} -> story")
                entry = state["posts"].setdefault(
                    chosen.platform_post_id, {"id": chosen.id, "history": []}
                )
                entry["last_reshared_at"] = now.isoformat()
                state["last_reshare_at"] = now.isoformat()
            except Exception as exc:
                print(f"[reshare] {chosen.id}: failed ({exc})")
        else:
            print("[reshare] no eligible (cooled-down) post found")
    else:
        print("[reshare] skipped, rate-limited")

    _save_state(state)


if __name__ == "__main__":
    main()
