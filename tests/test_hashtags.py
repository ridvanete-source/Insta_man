import random

from insta_man.hashtags.manager import HashtagManager


def make_manager():
    return HashtagManager(rng=random.Random(42))


def test_select_respects_max_hashtags():
    mgr = make_manager()
    tags = mgr.select(topics=["general"], max_hashtags=10)
    assert 0 < len(tags) <= 10


def test_select_excludes_banned_tags():
    mgr = make_manager()
    tags = mgr.select(topics=["general"], max_hashtags=25)
    assert "workflow" not in tags  # present in banned_hashtags.yaml


def test_select_includes_extra_tags_first():
    mgr = make_manager()
    tags = mgr.select(topics=["general"], max_hashtags=5, extra=["mybrand"])
    assert "mybrand" in tags


def test_select_deduplicates():
    mgr = make_manager()
    tags = mgr.select(topics=["general", "lifestyle"], max_hashtags=30)
    assert len(tags) == len(set(tags))


def test_select_unknown_topic_falls_back_to_general():
    mgr = make_manager()
    tags = mgr.select(topics=["does-not-exist"], max_hashtags=10)
    assert len(tags) > 0


def test_format_for_caption():
    assert HashtagManager.format_for_caption(["a", "b"]) == "#a #b"
