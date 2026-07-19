from datetime import datetime

import requests

from menu_courier.config import settings
from menu_courier.scraping.base import Post

_ACTOR_ID = "apify~facebook-posts-scraper"
_RUN_SYNC_URL = f"https://api.apify.com/v2/actors/{_ACTOR_ID}/run-sync-get-dataset-items"


class ApifySource:
    def get_latest_post(self, source_handle: str, text_filter: str | None = None) -> Post | None:
        response = requests.post(
            _RUN_SYNC_URL,
            headers={"Authorization": f"Bearer {settings.apify_api_token}"},
            json={
                "startUrls": [{"url": source_handle}],
                "onlyPostsNewerThan": "2 days",
                "resultsLimit": 5,
            },
            timeout=120,
        )
        response.raise_for_status()
        items = response.json()

        for item in items:
            if text_filter is None or text_filter.lower() in (item.get("text") or "").lower():
                return _to_post(item)

        return None


def _to_post(item: dict) -> Post:
    image_urls = [
        media["photo_image"]["uri"]
        for media in item.get("media", [])
        if media.get("__typename") == "Photo"
    ]
    return Post(
        post_id=item["postId"],
        source_name=item.get("user", {}).get("name"),
        text=item.get("text"),
        image_urls=image_urls,
        posted_at=datetime.fromisoformat(item["time"]),
    )