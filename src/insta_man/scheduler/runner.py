"""Ties the queue, hashtag engine and publisher together for one run.

Designed to be invoked repeatedly by an external scheduler (cron, GitHub
Actions on a schedule, etc.) - each call publishes whatever is currently
due and exits. It holds no long-running state between invocations.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from insta_man.config import Config, load_config
from insta_man.hashtags import HashtagManager
from insta_man.models import PostStatus
from insta_man.publishers import get_publisher
from insta_man.queue import ContentQueue

logger = logging.getLogger("insta_man.scheduler")


def run_once(config: Config | None = None) -> list[str]:
    """Publish every post that is currently due. Returns a summary log per post."""
    config = config or load_config()
    queue = ContentQueue(config.queue_file)
    hashtag_manager = HashtagManager()
    publisher = get_publisher(config)

    summaries: list[str] = []
    due = queue.due_posts(now=datetime.now(timezone.utc))
    if not due:
        logger.info("No due posts.")
        return ["No due posts."]

    # Publish only the single earliest-due post per run. If a pause (outage,
    # paused automation, etc.) let several posts fall overdue, this run's
    # caller (an hourly cron/timer) will simply catch up one at a time on
    # subsequent runs instead of firing a burst of back-to-back posts in one
    # call - which reads as spammy/bot-like and risks platform rate limits.
    due.sort(key=lambda p: p.scheduled_at)
    post = due[0]
    if len(due) > 1:
        logger.info(
            "%d posts are due; publishing only the earliest (%s) this run.",
            len(due),
            post.id,
        )

    publisher.authenticate()

    max_tags = post.max_hashtags or config.max_hashtags
    hashtags = hashtag_manager.select(
        topics=post.topics,
        max_hashtags=max_tags,
        extra=post.extra_hashtags,
        exclude_recent=queue.recent_hashtags(),
    )
    caption_parts = [post.caption]
    if post.source_credit:
        caption_parts.append(f"🎥 via @{post.source_credit.lstrip('@')}")
    caption_parts.append(HashtagManager.format_for_caption(hashtags))
    caption = "\n\n".join(part for part in caption_parts if part).strip()

    post.status = PostStatus.PUBLISHING
    result = publisher.publish(post, caption)

    if result.success:
        post.status = PostStatus.POSTED
        post.published_at = datetime.now(timezone.utc)
        post.platform_post_id = result.platform_post_id
        summaries.append(f"[OK] {post.id} -> {result.platform_post_id}")
        logger.info("Published %s -> %s", post.id, result.platform_post_id)
    else:
        post.status = PostStatus.FAILED
        post.error = result.error
        summaries.append(f"[FAILED] {post.id}: {result.error}")
        logger.error("Failed to publish %s: %s", post.id, result.error)

    queue.save()
    return summaries
