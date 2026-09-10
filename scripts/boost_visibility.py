"""Safe, ToS-compliant visibility actions for already-posted content.

Deliberately does NOT do follow/unfollow, liking, or commenting on other
accounts - those are classic "growth bot" patterns that violate Instagram's
Terms of Use and raise the same account-restriction risk already seen on
this project (see CLAUDE.md). Instead this script only:

1. Logs like/comment counts for posted items over time (content-strategy
   signal - which topics/hashtags actually perform).
2. (DISABLED 2026-09-10, see RESHARE_ENABLED below) Reshares an older,
   well-cooled-down post to Story by re-uploading its original media file
   through the same story-publish path used for scheduled Story posts (NOT
   instagrapi's native `media_share_to_story`, which was observed rendering
   as a blank/black story on the account - see
   InstagrapiPublisher.reshare_to_story). Rate-limited to at most once per
   run and at least MIN_GAP_BETWEEN_RESHARES apart, picking the
   least-recently-reshared eligible post first. Posts with
   `reshare_eligible: false` in queue.yaml (time-sensitive content such as
   match-day graphics) are never picked.

State is kept in content_library/visibility_state.json (committed to git,
same pattern as queue.yaml) so history survives across runs/machines.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from insta_man import health
from insta_man.config import load_config
from insta_man.models import PostStatus, PostTarget
from insta_man.publishers import get_publisher
from insta_man.publishers.instagrapi_adapter import InstagrapiPublisher
from insta_man.queue.content_queue import ContentQueue

STATE_FILE = Path("content_library/visibility_state.json")
MIN_POST_AGE_FOR_RESHARE = timedelta(days=3)
MIN_GAP_BETWEEN_RESHARES = timedelta(hours=20)

# Re-enabled 2026-09-10 after the root cause (fixed in commit 1f6acec - the
# cooldown timestamp was only recorded on a *successful* reshare, so a
# swallowed network exception let the same post get reshared to Story every
# hour overnight instead of every 20h) was fixed and the user approved
# resuming. See CLAUDE.md for the incident writeup.
RESHARE_ENABLED = True


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
    # Shares insta_man.cli's circuit breaker (see health.py docstring) -
    # this script also calls authenticate()/login(), so it must back off
    # the same way once the shared failure counter has tripped, otherwise
    # it keeps hammering the login endpoint even while `insta_man run` has
    # already given up.
    if health.should_skip_run() is not None:
        print("Skipping visibility actions: automation is paused by the circuit breaker.")
        return

    config = load_config()
    publisher = get_publisher(config)
    if not isinstance(publisher, InstagrapiPublisher):
        print("Visibility actions only support the instagrapi backend, skipping.")
        return

    try:
        publisher.authenticate()
    except Exception as exc:
        health.record_failure(config, f"{type(exc).__name__}: {exc}")
        raise
    health.record_success()
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

    if not RESHARE_ENABLED:
        print("[reshare] disabled by RESHARE_ENABLED=False, skipping")
        _save_state(state)
        return

    last_reshare_at = (
        datetime.fromisoformat(state["last_reshare_at"]) if state.get("last_reshare_at") else None
    )
    can_reshare_now = last_reshare_at is None or (now - last_reshare_at) >= MIN_GAP_BETWEEN_RESHARES

    if can_reshare_now:
        candidates = [
            p
            for p in feed_posted
            if p.reshare_eligible
            and p.published_at
            and (now - p.published_at) >= MIN_POST_AGE_FOR_RESHARE
        ]

        def _last_reshared(p):
            entry = state["posts"].get(p.platform_post_id, {})
            ts = entry.get("last_reshared_at")
            return datetime.fromisoformat(ts) if ts else datetime.min.replace(tzinfo=timezone.utc)

        candidates.sort(key=_last_reshared)
        if candidates:
            chosen = candidates[0]
            # Record this as "reshared now" *before* attempting the upload,
            # not just on success. A client-side exception (timeout, dropped
            # connection) doesn't mean Instagram's server didn't already
            # accept the upload - if we only recorded successes, that one
            # ambiguous failure would leave the cooldown/candidate-ordering
            # untouched forever, and this same post would be picked again
            # (and re-uploaded) on every subsequent run with no backoff at
            # all. See the 2026-09-10 hourly-duplicate-Story incident.
            entry = state["posts"].setdefault(
                chosen.platform_post_id, {"id": chosen.id, "history": []}
            )
            entry["last_reshared_at"] = now.isoformat()
            state["last_reshare_at"] = now.isoformat()
            try:
                publisher.reshare_to_story(chosen.media[0])
                print(f"[reshare] {chosen.id} -> story")
            except Exception as exc:
                print(f"[reshare] {chosen.id}: failed ({exc}) - will not retry for {MIN_GAP_BETWEEN_RESHARES}")
        else:
            print("[reshare] no eligible (cooled-down) post found")
    else:
        print("[reshare] skipped, rate-limited")

    _save_state(state)


if __name__ == "__main__":
    main()
