from datetime import datetime, timezone

from menu_courier.scraping.base import Post


def _make_post(text: str | None) -> Post:
    return Post(
        post_id="1",
        source_name=None,
        text=text,
        image_urls=[],
        posted_at=datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc),
    )


def test_matches_without_filter():
    assert _make_post("anything").matches(None)
    assert _make_post(None).matches(None)


def test_matches_is_case_insensitive():
    assert _make_post("Menu na DZIŚ").matches("menu")


def test_does_not_match_when_filter_absent_from_text():
    assert not _make_post("Nothing here").matches("menu")


def test_does_not_match_post_without_text():
    assert not _make_post(None).matches("menu")
