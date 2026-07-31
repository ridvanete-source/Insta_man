"""YAML-backed content queue.

The queue file (see content_library/queue.example.yaml) is where future
content gets scheduled: caption, media paths/URLs, topics for hashtag
selection and a scheduled_at timestamp. This module only manages state
transitions (pending -> posted/failed); it never invents content.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

from insta_man.models import ContentPost, MediaItem, MediaType, PostStatus, PostTarget


class ContentQueue:
    def __init__(self, queue_file: Path) -> None:
        self.queue_file = queue_file
        self.posts: list[ContentPost] = self._load()

    def _load(self) -> list[ContentPost]:
        if not self.queue_file.exists():
            return []
        with self.queue_file.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or []

        posts = []
        for item in raw:
            posts.append(
                ContentPost(
                    id=item["id"],
                    caption=item["caption"],
                    media=[
                        MediaItem(path=m["path"], media_type=MediaType(m.get("type", "image")))
                        for m in item["media"]
                    ],
                    scheduled_at=_parse_dt(item["scheduled_at"]),
                    topics=item.get("topics", []),
                    extra_hashtags=item.get("extra_hashtags", []),
                    max_hashtags=item.get("max_hashtags"),
                    target=PostTarget(item.get("target", "feed")),
                    source_credit=item.get("source_credit"),
                    status=PostStatus(item.get("status", "pending")),
                    published_at=_parse_dt(item["published_at"]) if item.get("published_at") else None,
                    platform_post_id=item.get("platform_post_id"),
                    error=item.get("error"),
                )
            )
        return posts

    def save(self) -> None:
        raw = []
        for post in self.posts:
            raw.append(
                {
                    "id": post.id,
                    "caption": post.caption,
                    "media": [{"path": m.path, "type": m.media_type.value} for m in post.media],
                    "scheduled_at": post.scheduled_at.isoformat(),
                    "topics": post.topics,
                    "extra_hashtags": post.extra_hashtags,
                    "max_hashtags": post.max_hashtags,
                    "target": post.target.value,
                    "source_credit": post.source_credit,
                    "status": post.status.value,
                    "published_at": post.published_at.isoformat() if post.published_at else None,
                    "platform_post_id": post.platform_post_id,
                    "error": post.error,
                }
            )
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        with self.queue_file.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(raw, fh, allow_unicode=True, sort_keys=False)

    def due_posts(self, now: datetime | None = None) -> list[ContentPost]:
        now = now or datetime.now(tz=self.posts[0].scheduled_at.tzinfo if self.posts else None)
        return [
            p for p in self.posts if p.status == PostStatus.PENDING and p.scheduled_at <= now
        ]

    def recent_hashtags(self, limit: int = 5) -> list[str]:
        """Hashtags used in the most recently posted items, to avoid repeats."""
        posted = sorted(
            (p for p in self.posts if p.status == PostStatus.POSTED and p.published_at),
            key=lambda p: p.published_at,
            reverse=True,
        )[:limit]
        tags: list[str] = []
        for p in posted:
            tags.extend(p.extra_hashtags)
        return tags


def _parse_dt(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)
