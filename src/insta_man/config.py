"""Environment-driven configuration for the poster.

All secrets (tokens, passwords) come from environment variables / .env,
never from files committed to the repository.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    publisher: str = os.getenv("INSTA_MAN_PUBLISHER", "graph_api")  # "graph_api" | "instagrapi"
    queue_file: Path = Path(os.getenv("INSTA_MAN_QUEUE_FILE", "content_library/queue.yaml"))
    max_hashtags: int = int(os.getenv("INSTA_MAN_MAX_HASHTAGS", "25"))
    timezone: str = os.getenv("INSTA_MAN_TIMEZONE", "Europe/Istanbul")

    # Instagram Graph API (official)
    graph_api_user_id: str | None = os.getenv("IG_GRAPH_USER_ID")
    graph_api_access_token: str | None = os.getenv("IG_GRAPH_ACCESS_TOKEN")
    graph_api_version: str = os.getenv("IG_GRAPH_API_VERSION", "v21.0")

    # instagrapi (unofficial)
    ig_username: str | None = os.getenv("IG_USERNAME")
    ig_password: str | None = os.getenv("IG_PASSWORD")
    ig_session_file: Path = Path(os.getenv("IG_SESSION_FILE", ".ig_session.json"))


def load_config() -> Config:
    return Config()
