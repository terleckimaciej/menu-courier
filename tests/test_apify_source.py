import responses

from menu_courier.scraping.apify_source import _RUN_SYNC_URL, ApifySource


@responses.activate
def test_get_latest_post_parses_response():
    responses.add(
        responses.POST,
        _RUN_SYNC_URL,
        json=[
            {
                "postId": "123",
                "text": "hello",
                "time": "2026-07-17T12:00:00.000Z",
                "user": {"name": "Example Page"},
                "media": [
                    {"__typename": "Photo", "photo_image": {"uri": "https://example.com/a.jpg"}},
                    {"__typename": "Video", "photo_image": {"uri": "https://example.com/b.mp4"}},
                ],
            }
        ],
        status=200,
    )

    post = ApifySource().get_latest_post("https://www.facebook.com/example")

    assert post.post_id == "123"
    assert post.source_name == "Example Page"
    assert post.text == "hello"
    assert post.image_urls == ["https://example.com/a.jpg"]


@responses.activate
def test_get_latest_post_returns_none_when_no_items():
    responses.add(responses.POST, _RUN_SYNC_URL, json=[], status=200)

    post = ApifySource().get_latest_post("https://www.facebook.com/example")

    assert post is None


@responses.activate
def test_get_latest_post_skips_apify_error_items():
    responses.add(
        responses.POST,
        _RUN_SYNC_URL,
        json=[{"inputUrl": "https://www.facebook.com/example", "error": "no_items"}],
        status=200,
    )

    post = ApifySource().get_latest_post("https://www.facebook.com/example")

    assert post is None