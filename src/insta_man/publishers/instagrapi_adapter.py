"""Unofficial backend using the `instagrapi` library (private mobile API).

WARNING - Terms of Service risk: this backend automates a regular user
account rather than going through Meta's approved Graph API. It violates
Instagram's Terms of Use, and accounts using it can be rate-limited,
action-blocked, or permanently disabled with no appeal path. Use only if
you have accepted that risk (see CLAUDE.md). Prefer `graph_api` otherwise.

`instagrapi` is an optional dependency (not installed by default); it is
imported lazily so the rest of the project works without it.
"""

from __future__ import annotations

from insta_man.config import Config
from insta_man.models import ContentPost, MediaType, PublishResult

from .base import BasePublisher


class InstagrapiPublisher(BasePublisher):
    def __init__(self, config: Config) -> None:
        self._config = config
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from instagrapi import Client
            except ImportError as exc:
                raise RuntimeError(
                    "instagrapi is not installed. Run: pip install instagrapi"
                ) from exc
            self._client = Client()
        return self._client

    def authenticate(self) -> None:
        if not self._config.ig_username or not self._config.ig_password:
            raise RuntimeError("IG_USERNAME and IG_PASSWORD must be set for the instagrapi publisher")

        client = self._get_client()
        session_file = self._config.ig_session_file
        if session_file.exists():
            client.load_settings(session_file)
            client.login(self._config.ig_username, self._config.ig_password)
        else:
            client.login(self._config.ig_username, self._config.ig_password)
            client.dump_settings(session_file)

    def publish(self, post: ContentPost, caption_with_hashtags: str) -> PublishResult:
        client = self._get_client()
        try:
            if len(post.media) > 1:
                paths = [m.path for m in post.media]
                result = client.album_upload(paths, caption_with_hashtags)
            else:
                media = post.media[0]
                if media.media_type == MediaType.REEL:
                    result = client.clip_upload(media.path, caption_with_hashtags)
                elif media.media_type == MediaType.VIDEO:
                    result = client.video_upload(media.path, caption_with_hashtags)
                else:
                    result = client.photo_upload(media.path, caption_with_hashtags)
            return PublishResult(success=True, platform_post_id=str(result.pk))
        except Exception as exc:  # instagrapi raises many distinct exception types
            return PublishResult(success=False, error=str(exc))
