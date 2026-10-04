import logging
from collections import defaultdict
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
        # Fetch once per source, not once per subscription: scraping is the
        # paid step, and subscriptions sharing a source see the same posts.
        by_source: dict[tuple[str, str], list[Subscription]] = defaultdict(list)
        for subscription in repository.get_active_subscriptions(session):
            by_source[(subscription.platform, subscription.source_handle)].append(
                subscription
            )

        for (platform, source_handle), subscriptions in by_source.items():
            try:
                posts = get_post_source(platform).get_recent_posts(source_handle)
            except Exception:
                logger.exception(
                    "Failed to fetch posts for %s (subscriptions %s)",
                    source_handle,
                    [s.id for s in subscriptions],
                )
                continue

            for subscription in subscriptions:
                post = next(
                    (p for p in posts if p.matches(subscription.text_filter)), None
                )
                if post is not None:
                    _process_subscription(session, subscription, post, messenger)


def _process_subscription(
    session, subscription: Subscription, post: Post, messenger: MessengerClient
) -> None:
    if repository.is_already_sent(session, subscription.id, post.post_id):
        return

    post_date = post.posted_at.astimezone(ZoneInfo(settings.timezone)).date()

    try:
        if post.text:
            messenger.send_text(subscription.recipient_psid, _build_message_text(post))
        if subscription.send_images:
            for image_url in post.image_urls:
                messenger.send_image(subscription.recipient_psid, image_url)
        status = "sent"
    except Exception:
        logger.exception(
            "Failed to deliver post %s for subscription %s",
            post.post_id,
            subscription.id,
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
        return post.text or ""
    return f"🍽️ {post.source_name}\n\n{post.text}"
