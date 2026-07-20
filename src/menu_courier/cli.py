import argparse

from menu_courier.pipeline import run
from menu_courier.storage.db import SessionLocal
from menu_courier.storage.models import Subscription


def add_subscription(
    platform: str,
    source_handle: str,
    recipient_psid: str,
    recipient_label: str,
    text_filter: str | None = None,
    send_images: bool = True,
) -> None:
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


def main() -> None:
    parser = argparse.ArgumentParser(prog="menu-courier")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("run")

    add_parser = subparsers.add_parser("add-subscription")
    add_parser.add_argument("--platform", required=True)
    add_parser.add_argument("--source-handle", required=True)
    add_parser.add_argument("--recipient-psid", required=True)
    add_parser.add_argument("--recipient-label", required=True)
    add_parser.add_argument("--text-filter", default=None)
    add_parser.add_argument("--no-images", action="store_true")

    args = parser.parse_args()

    if args.command == "run":
        run()
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
