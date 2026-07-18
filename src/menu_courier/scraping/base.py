from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class Post:
    post_id: str
    text: str | None
    image_urls: list[str]
    posted_at: datetime


class PostSource(Protocol):
    def get_latest_post(self, source_handle: str) -> Post | None: ...
