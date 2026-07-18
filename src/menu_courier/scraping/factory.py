from menu_courier.scraping.apify_source import ApifySource
from menu_courier.scraping.base import PostSource

_SOURCES: dict[str, PostSource] = {
    "facebook": ApifySource(),
}


def get_post_source(platform: str) -> PostSource:
    try:
        return _SOURCES[platform]
    except KeyError:
        raise ValueError(f"Unsupported platform: {platform!r}") from None
