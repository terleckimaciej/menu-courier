from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class Post:
    post_id: str
    source_name: str | None
    text: str | None
    image_urls: list[str]
    posted_at: datetime

    def matches(self, text_filter: str | None) -> bool:
        return text_filter is None or text_filter.lower() in (self.text or "").lower()


class PostSource(Protocol):
    def get_recent_posts(self, source_handle: str) -> list[Post]: ...
