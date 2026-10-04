from datetime import datetime, timezone
from unittest.mock import ANY, MagicMock

from menu_courier import pipeline
from menu_courier.scraping.base import Post
from menu_courier.storage.models import Subscription


def _make_subscription(**overrides) -> Subscription:
    defaults = dict(
        id=1,
        platform="facebook",
        source_handle="https://www.facebook.com/example",
        recipient_psid="psid123",
        recipient_label="Test",
        send_images=True,
    )
    return Subscription(**{**defaults, **overrides})


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
    monkeypatch.setattr(pipeline.repository, "is_already_sent", lambda *a, **k: False)
    record_mock = MagicMock()
    monkeypatch.setattr(pipeline.repository, "record_sent_menu", record_mock)
    messenger = MagicMock()

    pipeline._process_subscription(MagicMock(), _make_subscription(), post, messenger)

    messenger.send_text.assert_called_once_with("psid123", "🍽️ Example Page\n\nmenu")
    messenger.send_image.assert_called_once_with("psid123", "https://example.com/a.jpg")
    assert record_mock.call_args.kwargs["status"] == "sent"


def test_skips_images_when_send_images_is_false(monkeypatch):
    monkeypatch.setattr(pipeline.repository, "is_already_sent", lambda *a, **k: False)
    monkeypatch.setattr(pipeline.repository, "record_sent_menu", MagicMock())
    messenger = MagicMock()

    pipeline._process_subscription(
        MagicMock(), _make_subscription(send_images=False), _make_post(), messenger
    )

    messenger.send_text.assert_called_once()
    messenger.send_image.assert_not_called()


def test_dedupes_by_post_id_not_post_date(monkeypatch):
    # Regression test: a subscription that already got today's post must not
    # swallow a *different* post that happens to land on the same calendar
    # date (e.g. published just before midnight for the next day's menu).
    post = _make_post(post_id="distinct-post-id")
    is_already_sent_mock = MagicMock(return_value=False)
    monkeypatch.setattr(pipeline.repository, "is_already_sent", is_already_sent_mock)
    monkeypatch.setattr(pipeline.repository, "record_sent_menu", MagicMock())
    messenger = MagicMock()

    pipeline._process_subscription(MagicMock(), _make_subscription(), post, messenger)

    is_already_sent_mock.assert_called_once_with(ANY, 1, "distinct-post-id")


def test_skips_when_already_sent(monkeypatch):
    monkeypatch.setattr(pipeline.repository, "is_already_sent", lambda *a, **k: True)
    record_mock = MagicMock()
    monkeypatch.setattr(pipeline.repository, "record_sent_menu", record_mock)
    messenger = MagicMock()

    pipeline._process_subscription(
        MagicMock(), _make_subscription(), _make_post(), messenger
    )

    messenger.send_text.assert_not_called()
    record_mock.assert_not_called()


def _patch_run(monkeypatch, subscriptions, source):
    monkeypatch.setattr(pipeline, "SessionLocal", MagicMock())
    monkeypatch.setattr(
        pipeline.repository, "get_active_subscriptions", lambda s: subscriptions
    )
    monkeypatch.setattr(pipeline, "get_post_source", lambda platform: source)
    monkeypatch.setattr(pipeline.repository, "is_already_sent", lambda *a, **k: False)
    monkeypatch.setattr(pipeline.repository, "record_sent_menu", MagicMock())
    messenger = MagicMock()
    monkeypatch.setattr(pipeline, "MessengerClient", lambda: messenger)
    return messenger


def test_run_fetches_once_per_source_for_shared_subscriptions(monkeypatch):
    source = MagicMock(get_recent_posts=MagicMock(return_value=[_make_post()]))
    subscriptions = [
        _make_subscription(id=1, recipient_psid="a"),
        _make_subscription(id=2, recipient_psid="b"),
        _make_subscription(id=3, recipient_psid="c"),
    ]
    messenger = _patch_run(monkeypatch, subscriptions, source)

    pipeline.run()

    source.get_recent_posts.assert_called_once_with("https://www.facebook.com/example")
    assert [c.args[0] for c in messenger.send_text.call_args_list] == ["a", "b", "c"]


def test_run_applies_each_subscriptions_own_text_filter(monkeypatch):
    posts = [
        _make_post(post_id="1", text="lunch menu"),
        _make_post(post_id="2", text="dinner menu"),
    ]
    source = MagicMock(get_recent_posts=MagicMock(return_value=posts))
    subscriptions = [
        _make_subscription(id=1, recipient_psid="a", text_filter="lunch"),
        _make_subscription(id=2, recipient_psid="b", text_filter="dinner"),
    ]
    messenger = _patch_run(monkeypatch, subscriptions, source)

    pipeline.run()

    source.get_recent_posts.assert_called_once()
    sent = {c.args[0]: c.args[1] for c in messenger.send_text.call_args_list}
    assert "lunch menu" in sent["a"]
    assert "dinner menu" in sent["b"]


def test_run_fetches_separately_for_different_sources(monkeypatch):
    source = MagicMock(get_recent_posts=MagicMock(return_value=[_make_post()]))
    subscriptions = [
        _make_subscription(id=1, source_handle="https://www.facebook.com/one"),
        _make_subscription(id=2, source_handle="https://www.facebook.com/two"),
    ]
    _patch_run(monkeypatch, subscriptions, source)

    pipeline.run()

    assert source.get_recent_posts.call_count == 2


def test_run_continues_after_fetch_failure(monkeypatch):
    source = MagicMock(
        get_recent_posts=MagicMock(side_effect=[RuntimeError("boom"), [_make_post()]])
    )
    subscriptions = [
        _make_subscription(id=1, source_handle="https://www.facebook.com/one"),
        _make_subscription(id=2, source_handle="https://www.facebook.com/two"),
    ]
    messenger = _patch_run(monkeypatch, subscriptions, source)

    pipeline.run()

    messenger.send_text.assert_called_once()


def test_records_failed_status_when_send_raises(monkeypatch):
    monkeypatch.setattr(pipeline.repository, "is_already_sent", lambda *a, **k: False)
    record_mock = MagicMock()
    monkeypatch.setattr(pipeline.repository, "record_sent_menu", record_mock)
    messenger = MagicMock()
    messenger.send_text.side_effect = RuntimeError("boom")

    pipeline._process_subscription(
        MagicMock(), _make_subscription(), _make_post(), messenger
    )

    assert record_mock.call_args.kwargs["status"] == "failed"
