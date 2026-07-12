from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from menu_courier.storage.models import SentMenu, Subscription


def get_active_subscriptions(session: Session) -> list[Subscription]:
    stmt = select(Subscription).where(Subscription.active.is_(True))
    return list(session.scalars(stmt))


def is_already_sent(session: Session, subscription_id: int, post_date: date) -> bool:
    stmt = select(SentMenu).where(
        SentMenu.subscription_id == subscription_id,
        SentMenu.post_date == post_date,
    )
    return session.scalars(stmt).first() is not None


def record_sent_menu(
    session: Session,
    *,
    subscription_id: int,
    post_id: str,
    post_date: date,
    text: str | None,
    image_url: str | None,
    status: str,
) -> SentMenu:
    sent_menu = SentMenu(
        subscription_id=subscription_id,
        post_id=post_id,
        post_date=post_date,
        text=text,
        image_url=image_url,
        status=status,
    )
    session.add(sent_menu)
    session.commit()
    return sent_menu
