"""Publisher interface. Every publishing backend implements this contract so
the scheduler never has to know which one is active."""

from __future__ import annotations

from abc import ABC, abstractmethod

from insta_man.models import ContentPost, PublishResult


class BasePublisher(ABC):
    @abstractmethod
    def authenticate(self) -> None:
        """Establish/refresh credentials. Called once before publishing."""

    @abstractmethod
    def publish(self, post: ContentPost, caption_with_hashtags: str) -> PublishResult:
        """Publish a single post and return the result."""
