"""Official Instagram Graph API (Content Publishing API) backend.

Requirements:
  - Instagram account converted to a Business or Creator account.
  - Linked to a Facebook Page.
  - A Meta developer App with the `instagram_content_publish` permission,
    approved for the account (see CLAUDE.md for the full setup checklist).
  - Media MUST be reachable at a public HTTPS URL - the Graph API fetches
    it server-side, it does not accept raw file uploads. `ContentPost.media`
    items should therefore contain a public URL, not a local path, when
    this backend is used.

Flow: create a media container, poll it until ready (video/reel), then
publish the container.
"""

from __future__ import annotations

import time

import requests

from insta_man.config import Config
from insta_man.models import ContentPost, MediaType, PostTarget, PublishResult

from .base import BasePublisher

GRAPH_BASE_URL = "https://graph.facebook.com"


class GraphAPIPublisher(BasePublisher):
    def __init__(self, config: Config) -> None:
        self._config = config
        self._base = f"{GRAPH_BASE_URL}/{config.graph_api_version}"

    def authenticate(self) -> None:
        if not self._config.graph_api_user_id or not self._config.graph_api_access_token:
            raise RuntimeError(
                "IG_GRAPH_USER_ID and IG_GRAPH_ACCESS_TOKEN must be set for the graph_api publisher"
            )
        # Long-lived tokens still expire (~60 days); this call fails fast if invalid.
        resp = requests.get(
            f"{self._base}/{self._config.graph_api_user_id}",
            params={"fields": "id", "access_token": self._config.graph_api_access_token},
            timeout=15,
        )
        resp.raise_for_status()

    def publish(self, post: ContentPost, caption_with_hashtags: str) -> PublishResult:
        if post.target == PostTarget.STORY:
            return PublishResult(
                success=False,
                error="Story publishing is not implemented for the graph_api backend; use instagrapi.",
            )
        try:
            if len(post.media) > 1:
                container_id = self._create_carousel_container(post, caption_with_hashtags)
            else:
                container_id = self._create_single_media_container(post.media[0], caption_with_hashtags)

            self._wait_until_ready(container_id)
            media_id = self._publish_container(container_id)
            return PublishResult(success=True, platform_post_id=media_id)
        except (requests.HTTPError, requests.RequestException, RuntimeError) as exc:
            return PublishResult(success=False, error=str(exc))

    def _create_single_media_container(self, media, caption: str) -> str:
        params = {
            "caption": caption,
            "access_token": self._config.graph_api_access_token,
        }
        if media.media_type in (MediaType.VIDEO, MediaType.REEL):
            params["media_type"] = "REELS" if media.media_type == MediaType.REEL else "VIDEO"
            params["video_url"] = media.path
        else:
            params["image_url"] = media.path

        resp = requests.post(
            f"{self._base}/{self._config.graph_api_user_id}/media", data=params, timeout=30
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def _create_carousel_container(self, post: ContentPost, caption: str) -> str:
        child_ids = []
        for media in post.media:
            params = {
                "is_carousel_item": "true",
                "access_token": self._config.graph_api_access_token,
            }
            if media.media_type in (MediaType.VIDEO, MediaType.REEL):
                params["media_type"] = "VIDEO"
                params["video_url"] = media.path
            else:
                params["image_url"] = media.path
            resp = requests.post(
                f"{self._base}/{self._config.graph_api_user_id}/media", data=params, timeout=30
            )
            resp.raise_for_status()
            child_ids.append(resp.json()["id"])

        resp = requests.post(
            f"{self._base}/{self._config.graph_api_user_id}/media",
            data={
                "media_type": "CAROUSEL",
                "caption": caption,
                "children": ",".join(child_ids),
                "access_token": self._config.graph_api_access_token,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def _wait_until_ready(self, container_id: str, timeout_s: int = 120, poll_every_s: int = 5) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            resp = requests.get(
                f"{self._base}/{container_id}",
                params={"fields": "status_code", "access_token": self._config.graph_api_access_token},
                timeout=15,
            )
            resp.raise_for_status()
            status = resp.json().get("status_code")
            if status == "FINISHED":
                return
            if status == "ERROR":
                raise RuntimeError(f"Media container {container_id} failed processing")
            time.sleep(poll_every_s)
        raise RuntimeError(f"Media container {container_id} did not finish processing in time")

    def _publish_container(self, container_id: str) -> str:
        resp = requests.post(
            f"{self._base}/{self._config.graph_api_user_id}/media_publish",
            data={"creation_id": container_id, "access_token": self._config.graph_api_access_token},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["id"]
