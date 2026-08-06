import argparse
from urllib.parse import urlparse

from menu_courier.config import settings
from menu_courier.messenger.client import MessengerClient
from menu_courier.pipeline import run
from menu_courier.storage.db import SessionLocal
from menu_courier.storage.models import Subscription


def _print_database_target() -> None:
    host = urlparse(settings.database_url).hostname
    print(f"Operating on database: {host}")


def _confirm_database_target() -> None:
    _print_database_target()
    if input("Continue? [y/N] ").strip().lower() != "y":
        raise SystemExit("Aborted.")


def list_recipients() -> None:
    for name, psid in MessengerClient().list_recipients():
        print(f"{name} — {psid}")


def list_subscriptions() -> None:
    _print_database_target()
    with SessionLocal() as session:
        for sub in session.query(Subscription).all():
            status = "active" if sub.active else "inactive"
            print(f"{sub.id}  {sub.recipient_label!r}  {sub.source_handle}  [{status}]")


def add_subscription(
    platform: str,
    source_handle: str,
    recipient_psid: str,
    recipient_label: str,
    text_filter: str | None = None,
    send_images: bool = True,
) -> None:
    _confirm_database_target()
    with SessionLocal() as session:
        session.add(
            Subscription(
                platform=platform,
                source_handle=source_handle,
                recipient_psid=recipient_psid,
                recipient_label=recipient_label,
                text_filter=text_filter,
                send_images=send_images,
            )
        )
        session.commit()


def deactivate_subscription(subscription_id: int) -> None:
    _confirm_database_target()
    with SessionLocal() as session:
        sub = session.get(Subscription, subscription_id)
        if sub is None:
            print(f"No subscription with id {subscription_id}")
            return
        sub.active = False
        session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(prog="menu-courier")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("run")
    subparsers.add_parser("list-recipients")
    subparsers.add_parser("list-subscriptions")

    deactivate_parser = subparsers.add_parser("deactivate-subscription")
    deactivate_parser.add_argument(
        "--id", required=True, type=int, dest="subscription_id"
    )

    add_parser = subparsers.add_parser("add-subscription")
    add_parser.add_argument("--platform", required=True)
    add_parser.add_argument("--source-handle", required=True)
    add_parser.add_argument("--recipient-psid", required=True)
    add_parser.add_argument("--recipient-label", required=True)
    add_parser.add_argument("--text-filter", default=None)
    add_parser.add_argument("--no-images", action="store_true")

    args = parser.parse_args()

    if args.command == "run":
        _print_database_target()
        run()
    elif args.command == "list-recipients":
        list_recipients()
    elif args.command == "list-subscriptions":
        list_subscriptions()
    elif args.command == "deactivate-subscription":
        deactivate_subscription(args.subscription_id)
    elif args.command == "add-subscription":
        add_subscription(
            args.platform,
            args.source_handle,
            args.recipient_psid,
            args.recipient_label,
            args.text_filter,
            not args.no_images,
        )


if __name__ == "__main__":
    main()
