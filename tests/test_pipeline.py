from datetime import datetime, timezone
from unittest.mock import MagicMock

from menu_courier import pipeline
from menu_courier.scraping.base import Post
from menu_courier.storage.models import Subscription


def _make_subscription() -> Subscription:
    return Subscription(
        id=1,
        platform="facebook",
        source_handle="https://www.facebook.com/example",
        recipient_psid="psid123",
        recipient_label="Test",
    )


def _make_post(**overrides) -> Post:
    defaults = dict(
        post_id="1",
        source_name="Example Page",
        text="menu",
        image_urls=["https://example.com/a.jpg"],
        posted_at=datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc),
    )
    return Post(**{**defaults, **overrides})


def test_sends_and_records_sent_when_post_is_new(monkeypatch):
    post = _make_post()
    fake_source = MagicMock(get_latest_post=MagicMock(return_value=post))
    monkeypatch.setattr(pipeline, "get_post_source", lambda platform: fake_source)
    monkeypatch.setattr(pipeline.repository, "is_already_sent", lambda *a, **k: False)
    record_mock = MagicMock()
    monkeypatch.setattr(pipeline.repository, "record_sent_menu", record_mock)
    messenger = MagicMock()

    pipeline._process_subscription(MagicMock(), _make_subscription(), messenger)

    messenger.send_text.assert_called_once_with("psid123", "🍽️ Example Page\n\nmenu")
    messenger.send_image.assert_called_once_with("psid123", "https://example.com/a.jpg")
    assert record_mock.call_args.kwargs["status"] == "sent"


def test_skips_when_already_sent(monkeypatch):
    fake_source = MagicMock(get_latest_post=MagicMock(return_value=_make_post()))
    monkeypatch.setattr(pipeline, "get_post_source", lambda platform: fake_source)
    monkeypatch.setattr(pipeline.repository, "is_already_sent", lambda *a, **k: True)
    record_mock = MagicMock()
    monkeypatch.setattr(pipeline.repository, "record_sent_menu", record_mock)
    messenger = MagicMock()

    pipeline._process_subscription(MagicMock(), _make_subscription(), messenger)

    messenger.send_text.assert_not_called()
    record_mock.assert_not_called()


def test_skips_when_no_post_found(monkeypatch):
    fake_source = MagicMock(get_latest_post=MagicMock(return_value=None))
    monkeypatch.setattr(pipeline, "get_post_source", lambda platform: fake_source)
    record_mock = MagicMock()
    monkeypatch.setattr(pipeline.repository, "record_sent_menu", record_mock)
    messenger = MagicMock()

    pipeline._process_subscription(MagicMock(), _make_subscription(), messenger)

    messenger.send_text.assert_not_called()
    record_mock.assert_not_called()


def test_records_failed_status_when_send_raises(monkeypatch):
    fake_source = MagicMock(get_latest_post=MagicMock(return_value=_make_post()))
    monkeypatch.setattr(pipeline, "get_post_source", lambda platform: fake_source)
    monkeypatch.setattr(pipeline.repository, "is_already_sent", lambda *a, **k: False)
    record_mock = MagicMock()
    monkeypatch.setattr(pipeline.repository, "record_sent_menu", record_mock)
    messenger = MagicMock()
    messenger.send_text.side_effect = RuntimeError("boom")

    pipeline._process_subscription(MagicMock(), _make_subscription(), messenger)

    assert record_mock.call_args.kwargs["status"] == "failed"