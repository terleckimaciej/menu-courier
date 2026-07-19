import json

import pytest
import responses

from menu_courier.messenger import client as client_module
from menu_courier.messenger.client import MessengerClient


@responses.activate
def test_send_text_posts_expected_payload():
    responses.add(responses.POST, client_module._BASE_URL, json={"message_id": "abc"}, status=200)

    MessengerClient().send_text("psid123", "hello")

    request = responses.calls[0].request
    assert request.headers["Authorization"].startswith("Bearer ")
    assert json.loads(request.body) == {
        "recipient": {"id": "psid123"},
        "message": {"text": "hello"},
    }


@responses.activate
def test_send_raises_with_response_body_on_error():
    responses.add(
        responses.POST,
        client_module._BASE_URL,
        json={"error": {"message": "bad token"}},
        status=400,
    )

    with pytest.raises(RuntimeError, match="bad token"):
        MessengerClient().send_text("psid123", "hello")