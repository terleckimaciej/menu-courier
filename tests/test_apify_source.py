import responses

from menu_courier.scraping.apify_source import _RUN_SYNC_URL, ApifySource


@responses.activate
def test_get_recent_posts_parses_response():
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
                    {
                        "__typename": "Photo",
                        "photo_image": {"uri": "https://example.com/a.jpg"},
                    },
                    {
                        "__typename": "Video",
                        "photo_image": {"uri": "https://example.com/b.mp4"},
                    },
                ],
            }
        ],
        status=200,
    )

    posts = ApifySource().get_recent_posts("https://www.facebook.com/example")

    assert len(posts) == 1
    assert posts[0].post_id == "123"
    assert posts[0].source_name == "Example Page"
    assert posts[0].text == "hello"
    assert posts[0].image_urls == ["https://example.com/a.jpg"]


@responses.activate
def test_get_recent_posts_returns_all_posts():
    responses.add(
        responses.POST,
        _RUN_SYNC_URL,
        json=[
            {"postId": "1", "text": "a", "time": "2026-07-17T12:00:00.000Z"},
            {"postId": "2", "text": "b", "time": "2026-07-16T12:00:00.000Z"},
        ],
        status=200,
    )

    posts = ApifySource().get_recent_posts("https://www.facebook.com/example")

    assert [p.post_id for p in posts] == ["1", "2"]


@responses.activate
def test_get_recent_posts_returns_empty_when_no_items():
    responses.add(responses.POST, _RUN_SYNC_URL, json=[], status=200)

    posts = ApifySource().get_recent_posts("https://www.facebook.com/example")

    assert posts == []


@responses.activate
def test_get_recent_posts_skips_apify_error_items():
    responses.add(
        responses.POST,
        _RUN_SYNC_URL,
        json=[{"inputUrl": "https://www.facebook.com/example", "error": "no_items"}],
        status=200,
    )

    posts = ApifySource().get_recent_posts("https://www.facebook.com/example")

    assert posts == []
