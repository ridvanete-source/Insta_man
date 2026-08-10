"""Unofficial backend using the `instagrapi` library (private mobile API).

WARNING - Terms of Service risk: this backend automates a regular user
account rather than going through Meta's approved Graph API. It violates
Instagram's Terms of Use, and accounts using it can be rate-limited,
action-blocked, or permanently disabled with no appeal path. Use only if
you have accepted that risk (see CLAUDE.md). Prefer `graph_api` otherwise.

`instagrapi` is an optional dependency (not installed by default); it is
imported lazily so the rest of the project works without it.

Login from a new device/IP is usually challenged by Instagram: either a
verification code (SMS/email) via the "checkpoint" challenge flow, or a
2FA code for accounts with two-factor auth enabled. Both are handled here
by blocking on `input()` - this is normally a one-time hurdle, since a
successful login is cached in IG_SESSION_FILE and reused (with the same
device fingerprint) on subsequent runs, so the prompt should not repeat on
every scheduled run. Not exercised against a live account in this
repository - see CLAUDE.md.
"""

from __future__ import annotations

import logging

from insta_man.config import Config
from insta_man.models import ContentPost, MediaItem, MediaType, PostTarget, PublishResult

from .base import BasePublisher

logger = logging.getLogger("insta_man.publishers.instagrapi")


def _prompt_for_code(prompt: str) -> str:
    while True:
        try:
            code = input(prompt).strip()
        except EOFError as exc:
            raise RuntimeError(
                "Instagram bir dogrulama kodu istedi ama bu ortam etkilesimli degil "
                "(ör. GitHub Actions) - kod girilemedi. Yerel makinede "
                "`python -m insta_man.cli run` calistirip session'i (.ig_session.json) "
                "tazeleyin, ardindan IG_SESSION_B64 secret'ini guncelleyin."
            ) from exc
        if code.isdigit():
            return code
        print("Code must be numeric digits only, try again.")


class InstagrapiPublisher(BasePublisher):
    def __init__(self, config: Config) -> None:
        self._config = config
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from instagrapi import Client
                from instagrapi.mixins.challenge import ChallengeChoice
            except ImportError as exc:
                raise RuntimeError(
                    "instagrapi is not installed. Run: pip install instagrapi"
                ) from exc

            client = Client()

            def challenge_code_handler(username: str, choice) -> str:
                method = "SMS" if choice == ChallengeChoice.SMS else "email"
                logger.info("Instagram requested a %s verification code for %s", method, username)
                return _prompt_for_code(
                    f"Enter the {method} verification code Instagram sent to {username}: "
                )

            client.challenge_code_handler = challenge_code_handler
            self._client = client
        return self._client

    def authenticate(self) -> None:
        if not self._config.ig_username or not self._config.ig_password:
            raise RuntimeError("IG_USERNAME and IG_PASSWORD must be set for the instagrapi publisher")

        from instagrapi.exceptions import ChallengeRequired, TwoFactorRequired

        client = self._get_client()
        session_file = self._config.ig_session_file
        if session_file.exists():
            client.load_settings(session_file)

        username, password = self._config.ig_username, self._config.ig_password
        try:
            client.login(username, password)
        except TwoFactorRequired:
            code = _prompt_for_code(f"Instagram requested a 2FA code for {username}: ")
            client.login(username, password, verification_code=code)
        except ChallengeRequired:
            # challenge_code_handler above should normally intercept this
            # mid-login; this is a fallback for flows that surface it as an
            # exception instead of calling the handler directly.
            client.challenge_resolve(client.last_json)

        client.dump_settings(session_file)

    def publish(self, post: ContentPost, caption_with_hashtags: str) -> PublishResult:
        client = self._get_client()
        try:
            if post.target == PostTarget.STORY:
                return self._publish_story(client, post)

            usertags = self._build_usertags(client, post)
            location = self._resolve_location(client, post.location)

            if len(post.media) > 1:
                paths = [m.path for m in post.media]
                result = client.album_upload(
                    paths, caption_with_hashtags, usertags=usertags, location=location
                )
            else:
                media = post.media[0]
                if media.media_type == MediaType.REEL:
                    result = client.clip_upload(
                        media.path, caption_with_hashtags, usertags=usertags, location=location
                    )
                elif media.media_type == MediaType.VIDEO:
                    result = client.video_upload(
                        media.path, caption_with_hashtags, usertags=usertags, location=location
                    )
                else:
                    result = client.photo_upload(
                        media.path, caption_with_hashtags, usertags=usertags, location=location
                    )
            return PublishResult(success=True, platform_post_id=str(result.pk))
        except Exception as exc:  # instagrapi raises many distinct exception types
            return PublishResult(success=False, error=str(exc))

    def _build_usertags(self, client, post: ContentPost) -> list:
        """Real tap-to-reveal photo tags for feed posts (not caption text -
        that credit line is added separately in runner.py)."""
        from instagrapi.types import Usertag

        if not post.source_credit:
            return []
        user = self._resolve_user_short(client, post.source_credit)
        if user is None:
            return []
        return [Usertag(user=user, x=0.5, y=0.9)]

    def _resolve_user_short(self, client, username: str):
        from instagrapi.types import UserShort

        try:
            user_id = client.user_id_from_username(username.lstrip("@"))
            return UserShort(pk=str(user_id), username=username.lstrip("@"))
        except Exception:
            logger.warning("Could not resolve Instagram user @%s for tagging", username, exc_info=True)
            return None

    def _resolve_location(self, client, location_name: str | None):
        if not location_name:
            return None
        try:
            candidates = client.location_search_name(location_name)
            if not candidates:
                logger.warning("No Instagram location match for %r, posting without a location tag", location_name)
                return None
            return client.location_complete(candidates[0])
        except Exception:
            logger.warning("Location lookup failed for %r, posting without a location tag", location_name, exc_info=True)
            return None

    def reshare_to_story(self, media: MediaItem) -> str:
        """Reshare an existing feed post to Story by re-uploading its original file.

        Gives older posts a second wave of visibility without any
        follow/like/comment automation. Deliberately does NOT use instagrapi's
        `media_share_to_story` (the native "Share to Story" reshare) - that
        private-API call is unreliable and was observed producing a blank/
        black story on the account. Re-uploading through the same
        photo/video-to-story path used for scheduled Story posts
        (`_publish_story`) avoids that failure mode.
        """
        client = self._get_client()
        if media.media_type in (MediaType.VIDEO, MediaType.REEL):
            result = client.video_upload_to_story(media.path)
        else:
            result = client.photo_upload_to_story(media.path)
        return str(result.pk)

    def get_engagement(self, media_pk: str) -> dict:
        """Fetch current like/comment counts for a posted media item."""
        client = self._get_client()
        info = client.media_info(client.media_pk(media_pk))
        return {"like_count": info.like_count, "comment_count": info.comment_count}

    def _publish_story(self, client, post: ContentPost) -> PublishResult:
        # Stories are ephemeral single-media items - only the first media
        # entry is used even if the post lists more than one.
        from instagrapi.types import StoryLocation, StoryMention

        media = post.media[0]

        mentions = []
        if post.source_credit:
            user = self._resolve_user_short(client, post.source_credit)
            if user is not None:
                mentions = [StoryMention(user=user, x=0.5, y=0.9, width=0.5, height=0.15)]

        locations = []
        resolved_location = self._resolve_location(client, post.location)
        if resolved_location is not None:
            locations = [StoryLocation(location=resolved_location, x=0.5, y=0.15, width=0.4, height=0.1)]

        if media.media_type == MediaType.VIDEO or media.media_type == MediaType.REEL:
            result = client.video_upload_to_story(media.path, mentions=mentions, locations=locations)
        else:
            result = client.photo_upload_to_story(media.path, mentions=mentions, locations=locations)
        return PublishResult(success=True, platform_post_id=str(result.pk))
