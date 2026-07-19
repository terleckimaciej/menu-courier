from datetime import date, datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str]
    source_handle: Mapped[str]
    text_filter: Mapped[str | None]
    recipient_psid: Mapped[str]
    recipient_label: Mapped[str]
    send_images: Mapped[bool] = mapped_column(default=True)
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    sent_menus: Mapped[list["SentMenu"]] = relationship(back_populates="subscription")


class SentMenu(Base):
    __tablename__ = "sent_menus"
    __table_args__ = (
        UniqueConstraint("subscription_id", "post_date", name="uq_subscription_post_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"))
    post_id: Mapped[str]
    post_date: Mapped[date]
    text: Mapped[str | None]
    image_urls: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    status: Mapped[str]
    sent_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    subscription: Mapped["Subscription"] = relationship(back_populates="sent_menus")
