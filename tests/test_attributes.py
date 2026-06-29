"""Tests for the Attributes resource."""

from __future__ import annotations

from collections.abc import Callable

import httpx

from cdse.odata.attributes import AttributesResource
from cdse.transport import Transport
from tests.conftest import token_response

BASE_URL = "https://catalogue.example/odata/v1"

TransportFactory = Callable[[httpx.MockTransport], Transport]


def test_list_all_attributes(make_transport: TransportFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        assert request.url.path.endswith("/Attributes")
        return httpx.Response(
            200,
            json={"value": [{"Name": "cloudCover", "ValueType": "Double"}]},
        )

    resource = AttributesResource(
        make_transport(httpx.MockTransport(handler)), BASE_URL
    )
    attributes = resource.list()
    assert attributes[0].name == "cloudCover"
    assert attributes[0].value_type == "Double"


def test_list_attributes_for_collection(make_transport: TransportFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        assert request.url.path.endswith("/Attributes(SENTINEL-1)")
        return httpx.Response(200, json={"value": []})

    resource = AttributesResource(
        make_transport(httpx.MockTransport(handler)), BASE_URL
    )
    assert resource.list("SENTINEL-1") == []
