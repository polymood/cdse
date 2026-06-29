"""Tests for the Subscriptions resource."""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest

from cdse.subscriptions import SubscriptionsResource
from cdse.transport import Transport
from tests.conftest import token_response

BASE_URL = "https://catalogue.example/odata/v1"

TransportFactory = Callable[[httpx.MockTransport], Transport]
Handler = Callable[[httpx.Request], httpx.Response]


def _resource(
    handler: Handler, make_transport: TransportFactory
) -> SubscriptionsResource:
    return SubscriptionsResource(make_transport(httpx.MockTransport(handler)), BASE_URL)


def test_create_pull_subscription(make_transport: TransportFactory) -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        assert request.method == "POST"
        captured.update(json.loads(request.content))
        return httpx.Response(
            201, json={"Id": "sub-1", "Status": "running", "SubscriptionType": "pull"}
        )

    resource = _resource(handler, make_transport)
    subscription = resource.create("Collection/Name eq 'SENTINEL-1'")
    assert subscription.id == "sub-1"
    assert captured["SubscriptionType"] == "pull"
    assert captured["SubscriptionEvent"] == ["created"]
    assert captured["FilterParam"] == "Collection/Name eq 'SENTINEL-1'"


def test_push_subscription_requires_endpoint(make_transport: TransportFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return token_response()

    resource = _resource(handler, make_transport)
    with pytest.raises(ValueError, match="notification_endpoint"):
        resource.create(subscription_type="push")


def test_read_notifications(make_transport: TransportFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        assert request.url.path.endswith("/Subscriptions(sub-1)/Read")
        assert request.url.params["$top"] == "5"
        return httpx.Response(
            200,
            json=[
                {
                    "SubscriptionEvent": "created",
                    "ProductName": "S2B_X",
                    "AckId": "ack-123",
                }
            ],
        )

    resource = _resource(handler, make_transport)
    notifications = resource.read("sub-1", top=5)
    assert notifications[0].product_name == "S2B_X"
    assert notifications[0].ack_id == "ack-123"


def test_set_status_falls_back_to_get(make_transport: TransportFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        if request.method == "PATCH":
            return httpx.Response(204)
        return httpx.Response(200, json={"Id": "sub-1", "Status": "paused"})

    resource = _resource(handler, make_transport)
    subscription = resource.set_status("sub-1", "paused")
    assert subscription.status == "paused"


def test_list_and_delete(make_transport: TransportFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        if request.method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(200, json={"value": [{"Id": "sub-1"}, {"Id": "sub-2"}]})

    resource = _resource(handler, make_transport)
    assert [s.id for s in resource.list()] == ["sub-1", "sub-2"]
    resource.delete("sub-1")
