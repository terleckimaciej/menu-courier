import requests

from menu_courier.config import settings

_BASE_URL = f"https://graph.facebook.com/{settings.fb_graph_api_version}/me/messages"
_CONVERSATIONS_URL = (
    f"https://graph.facebook.com/{settings.fb_graph_api_version}/me/conversations"
)


class MessengerClient:
    def list_recipients(self) -> list[tuple[str, str]]:
        response = requests.get(
            _CONVERSATIONS_URL,
            headers={"Authorization": f"Bearer {settings.fb_page_access_token}"},
            params={"fields": "participants"},
            timeout=30,
        )
        if not response.ok:
            raise RuntimeError(
                f"Messenger API error ({response.status_code}): {response.text}"
            )

        recipients = []
        for conversation in response.json().get("data", []):
            for participant in conversation.get("participants", {}).get("data", []):
                recipients.append((participant["name"], participant["id"]))
        return recipients

    def send_text(self, recipient_psid: str, text: str) -> None:
        self._send(recipient_psid, {"text": text})

    def send_image(self, recipient_psid: str, image_url: str) -> None:
        self._send(
            recipient_psid,
            {
                "attachment": {
                    "type": "image",
                    "payload": {"url": image_url, "is_reusable": True},
                }
            },
        )

    def _send(self, recipient_psid: str, message: dict) -> None:
        response = requests.post(
            _BASE_URL,
            headers={"Authorization": f"Bearer {settings.fb_page_access_token}"},
            json={"recipient": {"id": recipient_psid}, "message": message},
            timeout=30,
        )
        if not response.ok:
            raise RuntimeError(
                f"Messenger API error ({response.status_code}): {response.text}"
            )
