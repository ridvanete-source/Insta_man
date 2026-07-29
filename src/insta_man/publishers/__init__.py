from insta_man.config import Config

from .base import BasePublisher


def get_publisher(config: Config) -> BasePublisher:
    """Factory: returns the configured publisher backend."""
    if config.publisher == "graph_api":
        from .graph_api import GraphAPIPublisher

        return GraphAPIPublisher(config)
    if config.publisher == "instagrapi":
        from .instagrapi_adapter import InstagrapiPublisher

        return InstagrapiPublisher(config)
    raise ValueError(f"Unknown publisher backend: {config.publisher!r}")


__all__ = ["BasePublisher", "get_publisher"]
