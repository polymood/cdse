"""Tests for the Bursts resource."""

from __future__ import annotations

from collections.abc import Callable

import httpx

from cdse.odata.bursts import BurstsResource
from cdse.transport import Transport
from tests.conftest import token_response

BASE_URL = "https://catalogue.example/odata/v1"

TransportFactory = Callable[[httpx.MockTransport], Transport]
Handler = Callable[[httpx.Request], httpx.Response]


def _resource(handler: Handler, make_transport: TransportFactory) -> BurstsResource:
    return BurstsResource(make_transport(httpx.MockTransport(handler)), BASE_URL)


def test_search_builds_filter_and_pages(make_transport: TransportFactory) -> None:
    filters: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        assert request.url.path.endswith("/Bursts")
        filters.append(request.url.params.get("$filter", ""))
        skip = request.url.params.get("$skip")
        if skip is None:
            return httpx.Response(
                200,
                json={
                    "value": [{"Id": "1", "Name": "B1", "BurstId": 15805}],
                    "@odata.nextLink": f"{BASE_URL}/Bursts?$skip=1",
                },
            )
        return httpx.Response(200, json={"value": [{"Id": "2", "Name": "B2"}]})

    resource = _resource(handler, make_transport)
    bursts = list(
        resource.search(
            parent_product_id="e463365f-728b",
            swath="IW1",
            polarisation="VH",
        )
    )
    assert [b.id for b in bursts] == ["1", "2"]
    assert bursts[0].burst_id == 15805
    assert filters[0] == (
        "ParentProductId eq 'e463365f-728b' and "
        "SwathIdentifier eq 'IW1' and PolarisationChannels eq 'VH'"
    )


def test_get_single_burst(make_transport: TransportFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        assert request.url.path.endswith("/Bursts(abc)")
        return httpx.Response(
            200, json={"Id": "abc", "Name": "B", "SwathIdentifier": "IW2"}
        )

    resource = _resource(handler, make_transport)
    assert resource.get("abc").swath_identifier == "IW2"


def test_count(make_transport: TransportFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        assert request.url.path.endswith("/Bursts/$count")
        return httpx.Response(200, text="123")

    resource = _resource(handler, make_transport)
    assert resource.count() == 123
