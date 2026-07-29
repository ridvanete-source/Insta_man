"""Topic-based, tiered hashtag selection.

Instagram caps a single post at 30 hashtags and over-using identical tag
sets across posts is a common trigger for reduced reach ("shadow-limiting").
This module picks a randomized mix across reach tiers (mega/medium/niche)
for the post's topics, filters out banned/flagged tags, and de-duplicates.
"""

from __future__ import annotations

import random
from pathlib import Path

import yaml

DEFAULT_SEED_FILE = Path(__file__).parent / "seed_hashtags.yaml"
DEFAULT_BANNED_FILE = Path(__file__).parent / "banned_hashtags.yaml"

# Default mix across tiers when picking `max_hashtags` tags for a topic set.
DEFAULT_TIER_RATIOS = {"mega": 0.15, "medium": 0.55, "niche": 0.30}


class HashtagManager:
    def __init__(
        self,
        seed_file: Path = DEFAULT_SEED_FILE,
        banned_file: Path = DEFAULT_BANNED_FILE,
        tier_ratios: dict[str, float] | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self._pools: dict[str, dict[str, list[str]]] = self._load_yaml(seed_file)
        self._banned: set[str] = {
            tag.lower().lstrip("#") for tag in self._load_yaml(banned_file).get("banned", [])
        }
        self._tier_ratios = tier_ratios or DEFAULT_TIER_RATIOS
        self._rng = rng or random.Random()

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}

    def _topic_pool(self, topic: str) -> dict[str, list[str]]:
        return self._pools.get(topic, {})

    def select(
        self,
        topics: list[str],
        max_hashtags: int = 25,
        extra: list[str] | None = None,
        exclude_recent: list[str] | None = None,
    ) -> list[str]:
        """Return a deduplicated, banned-filtered, tier-balanced hashtag list.

        `extra` tags are always included first (e.g. a branded/account tag).
        `exclude_recent` lets the scheduler avoid repeating the exact same
        set used in recent posts.
        """
        topics = topics or ["general"]
        excluded = {t.lower().lstrip("#") for t in (exclude_recent or [])}

        result: list[str] = []
        seen: set[str] = set()

        for tag in extra or []:
            clean = tag.lower().lstrip("#")
            if clean not in self._banned and clean not in seen:
                result.append(clean)
                seen.add(clean)

        remaining = max_hashtags - len(result)
        if remaining <= 0:
            return result[:max_hashtags]

        for tier, ratio in self._tier_ratios.items():
            quota = max(1, round(remaining * ratio))
            candidates: list[str] = []
            for topic in topics:
                candidates.extend(self._topic_pool(topic).get(tier, []))
            candidates = [
                c.lower().lstrip("#")
                for c in candidates
                if c.lower().lstrip("#") not in self._banned
                and c.lower().lstrip("#") not in seen
                and c.lower().lstrip("#") not in excluded
            ]
            self._rng.shuffle(candidates)
            for tag in candidates[:quota]:
                if len(result) >= max_hashtags:
                    break
                result.append(tag)
                seen.add(tag)

        # Fill any leftover slots from the general pool if topics ran dry.
        if len(result) < max_hashtags:
            fallback = [
                c.lower().lstrip("#")
                for tier_tags in self._topic_pool("general").values()
                for c in tier_tags
                if c.lower().lstrip("#") not in self._banned and c.lower().lstrip("#") not in seen
            ]
            self._rng.shuffle(fallback)
            for tag in fallback:
                if len(result) >= max_hashtags:
                    break
                result.append(tag)
                seen.add(tag)

        return result[:max_hashtags]

    @staticmethod
    def format_for_caption(hashtags: list[str]) -> str:
        return " ".join(f"#{tag}" for tag in hashtags)
