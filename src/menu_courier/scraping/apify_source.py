from datetime import datetime

import requests

from menu_courier.config import settings
from menu_courier.scraping.base import Post

_ACTOR_ID = "apify~facebook-posts-scraper"
_RUN_SYNC_URL = f"https://api.apify.com/v2/actors/{_ACTOR_ID}/run-sync-get-dataset-items"


class ApifySource:
    def get_latest_post(self, source_handle: str) -> Post | None:
        response = requests.post(
            _RUN_SYNC_URL,
            headers={"Authorization": f"Bearer {settings.apify_api_token}"},
            json={
                "startUrls": [{"url": source_handle}],
                "resultsLimit": 1,
            },
            timeout=120,
        )
        response.raise_for_status()
        items = response.json()
        if not items:
            return None

        latest = items[0]
        image_urls = [
            media["photo_image"]["uri"]
            for media in latest.get("media", [])
            if media.get("__typename") == "Photo"
        ]

        return Post(
            post_id=latest["postId"],
            text=latest.get("text"),
            image_urls=image_urls,
            posted_at=datetime.fromisoformat(latest["time"]),
        )