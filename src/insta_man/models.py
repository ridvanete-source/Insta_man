"""Core data models shared across the queue, hashtag engine and publishers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    REEL = "reel"
    CAROUSEL = "carousel"


class PostStatus(str, Enum):
    PENDING = "pending"
    PUBLISHING = "publishing"
    POSTED = "posted"
    FAILED = "failed"
    SKIPPED = "skipped"


class PostTarget(str, Enum):
    """Where the post goes: the normal feed grid, or an ephemeral Story."""

    FEED = "feed"
    STORY = "story"


@dataclass
class MediaItem:
    path: str
    media_type: MediaType = MediaType.IMAGE


@dataclass
class ContentPost:
    """A single scheduled Instagram post loaded from the content queue."""

    id: str
    caption: str
    media: list[MediaItem]
    scheduled_at: datetime
    topics: list[str] = field(default_factory=list)
    """Topic/niche tags used to pick relevant hashtags at publish time."""
    extra_hashtags: list[str] = field(default_factory=list)
    """Hashtags to always include regardless of the topic-based selection."""
    max_hashtags: int | None = None
    target: PostTarget = PostTarget.FEED
    status: PostStatus = PostStatus.PENDING
    published_at: datetime | None = None
    platform_post_id: str | None = None
    error: str | None = None


@dataclass
class PublishResult:
    success: bool
    platform_post_id: str | None = None
    error: str | None = None
