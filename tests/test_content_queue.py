from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from insta_man.queue.content_queue import ContentQueue


def write_queue(path: Path, entries: list[dict]) -> None:
    path.write_text(yaml.safe_dump(entries, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_due_posts_only_returns_pending_and_past_scheduled(tmp_path):
    now = datetime.now(timezone.utc)
    queue_file = tmp_path / "queue.yaml"
    write_queue(
        queue_file,
        [
            {
                "id": "past-pending",
                "caption": "hello",
                "media": [{"path": "img1.jpg", "type": "image"}],
                "scheduled_at": (now - timedelta(hours=1)).isoformat(),
                "status": "pending",
            },
            {
                "id": "future-pending",
                "caption": "hello",
                "media": [{"path": "img2.jpg", "type": "image"}],
                "scheduled_at": (now + timedelta(hours=1)).isoformat(),
                "status": "pending",
            },
            {
                "id": "past-posted",
                "caption": "hello",
                "media": [{"path": "img3.jpg", "type": "image"}],
                "scheduled_at": (now - timedelta(hours=2)).isoformat(),
                "status": "posted",
            },
        ],
    )

    queue = ContentQueue(queue_file)
    due = queue.due_posts(now=now)

    assert [p.id for p in due] == ["past-pending"]


def test_save_round_trips(tmp_path):
    now = datetime.now(timezone.utc)
    queue_file = tmp_path / "queue.yaml"
    write_queue(
        queue_file,
        [
            {
                "id": "post-1",
                "caption": "hello",
                "media": [{"path": "img1.jpg", "type": "image"}],
                "scheduled_at": now.isoformat(),
                "status": "pending",
                "topics": ["general"],
                "extra_hashtags": ["brand"],
            }
        ],
    )

    queue = ContentQueue(queue_file)
    queue.posts[0].status.__class__  # sanity: enum type present
    from insta_man.models import PostStatus

    queue.posts[0].status = PostStatus.POSTED
    queue.posts[0].platform_post_id = "12345"
    queue.save()

    reloaded = ContentQueue(queue_file)
    assert reloaded.posts[0].status == PostStatus.POSTED
    assert reloaded.posts[0].platform_post_id == "12345"
    assert reloaded.posts[0].topics == ["general"]
    assert reloaded.posts[0].extra_hashtags == ["brand"]


def test_source_credit_round_trips(tmp_path):
    now = datetime.now(timezone.utc)
    queue_file = tmp_path / "queue.yaml"
    write_queue(
        queue_file,
        [
            {
                "id": "reshared-post",
                "caption": "hello",
                "media": [{"path": "img1.jpg", "type": "image"}],
                "scheduled_at": now.isoformat(),
                "status": "pending",
                "source_credit": "original_creator",
            }
        ],
    )

    queue = ContentQueue(queue_file)
    assert queue.posts[0].source_credit == "original_creator"

    queue.save()
    reloaded = ContentQueue(queue_file)
    assert reloaded.posts[0].source_credit == "original_creator"


def test_reshare_eligible_defaults_true_and_round_trips(tmp_path):
    now = datetime.now(timezone.utc)
    queue_file = tmp_path / "queue.yaml"
    write_queue(
        queue_file,
        [
            {
                "id": "default-post",
                "caption": "hello",
                "media": [{"path": "img1.jpg", "type": "image"}],
                "scheduled_at": now.isoformat(),
                "status": "pending",
            },
            {
                "id": "time-sensitive-post",
                "caption": "hello",
                "media": [{"path": "img2.jpg", "type": "image"}],
                "scheduled_at": now.isoformat(),
                "status": "pending",
                "reshare_eligible": False,
            },
        ],
    )

    queue = ContentQueue(queue_file)
    assert queue.posts[0].reshare_eligible is True
    assert queue.posts[1].reshare_eligible is False

    queue.save()
    reloaded = ContentQueue(queue_file)
    assert reloaded.posts[0].reshare_eligible is True
    assert reloaded.posts[1].reshare_eligible is False


def test_recent_hashtags_only_considers_posted(tmp_path):
    now = datetime.now(timezone.utc)
    queue_file = tmp_path / "queue.yaml"
    write_queue(
        queue_file,
        [
            {
                "id": "posted-1",
                "caption": "hello",
                "media": [{"path": "img1.jpg", "type": "image"}],
                "scheduled_at": (now - timedelta(hours=2)).isoformat(),
                "status": "posted",
                "published_at": (now - timedelta(hours=1)).isoformat(),
                "extra_hashtags": ["foo", "bar"],
            },
            {
                "id": "pending-1",
                "caption": "hello",
                "media": [{"path": "img2.jpg", "type": "image"}],
                "scheduled_at": (now + timedelta(hours=1)).isoformat(),
                "status": "pending",
                "extra_hashtags": ["shouldnotappear"],
            },
        ],
    )

    queue = ContentQueue(queue_file)
    tags = queue.recent_hashtags()

    assert "foo" in tags and "bar" in tags
    assert "shouldnotappear" not in tags


def test_empty_queue_file_returns_no_posts(tmp_path):
    queue_file = tmp_path / "missing.yaml"
    queue = ContentQueue(queue_file)
    assert queue.posts == []
    assert queue.due_posts() == []
