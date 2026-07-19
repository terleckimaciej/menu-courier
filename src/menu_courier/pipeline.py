import logging
from zoneinfo import ZoneInfo

from menu_courier.config import settings
from menu_courier.messenger.client import MessengerClient
from menu_courier.scraping.factory import get_post_source
from menu_courier.storage import repository
from menu_courier.storage.db import SessionLocal
from menu_courier.scraping.base import Post
from menu_courier.storage.models import Subscription

logger = logging.getLogger(__name__)


def run() -> None:
    messenger = MessengerClient()
    with SessionLocal() as session:
        for subscription in repository.get_active_subscriptions(session):
            _process_subscription(session, subscription, messenger)


def _process_subscription(session, subscription: Subscription, messenger: MessengerClient) -> None:
    source = get_post_source(subscription.platform)
    try:
        post = source.get_latest_post(subscription.source_handle, subscription.text_filter)
    except Exception:
        logger.exception("Failed to fetch post for subscription %s", subscription.id)
        return

    if post is None:
        return

    post_date = post.posted_at.astimezone(ZoneInfo(settings.timezone)).date()
    if repository.is_already_sent(session, subscription.id, post_date):
        return

    try:
        if post.text:
            messenger.send_text(subscription.recipient_psid, _build_message_text(post))
        if subscription.send_images:
            for image_url in post.image_urls:
                messenger.send_image(subscription.recipient_psid, image_url)
        status = "sent"
    except Exception:
        logger.exception(
            "Failed to deliver post %s for subscription %s", post.post_id, subscription.id
        )
        status = "failed"

    repository.record_sent_menu(
        session,
        subscription_id=subscription.id,
        post_id=post.post_id,
        post_date=post_date,
        text=post.text,
        image_urls=post.image_urls,
        status=status,
    )


def _build_message_text(post: Post) -> str:
    if not post.source_name:
        return post.text
    return f"🍽️ {post.source_name}\n\n{post.text}"