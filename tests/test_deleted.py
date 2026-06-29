"""Tests for the DeletedProducts resource."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import httpx

from cdse.odata.deleted import DeletedProductsResource
from cdse.odata.query import FilterBuilder
from cdse.transport import Transport
from tests.conftest import token_response

BASE_URL = "https://catalogue.example/odata/v1"

TransportFactory = Callable[[httpx.MockTransport], Transport]


def test_deletion_filter_helpers_build_expected_expression() -> None:
    expression = (
        FilterBuilder()
        .deleted_between(
            datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 2, 1, tzinfo=UTC)
        )
        .deletion_cause("Duplicated product")
        .build()
    )
    assert expression == (
        "DeletionDate ge 2024-01-01T00:00:00Z and "
        "DeletionDate le 2024-02-01T00:00:00Z and "
        "DeletionCause eq 'Duplicated product'"
    )


def test_search_returns_deleted_products(make_transport: TransportFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        assert request.url.path.endswith("/DeletedProducts")
        return httpx.Response(
            200,
            json={
                "value": [
                    {
                        "Id": "1",
                        "Name": "OLD",
                        "DeletionDate": "2024-01-15T00:00:00Z",
                        "DeletionCause": "Duplicated product",
                    }
                ]
            },
        )

    resource = DeletedProductsResource(
        make_transport(httpx.MockTransport(handler)), BASE_URL
    )
    deleted = list(
        resource.search(FilterBuilder().deletion_cause("Duplicated product"))
    )
    assert deleted[0].name == "OLD"
    assert deleted[0].deletion_cause == "Duplicated product"
    assert deleted[0].deletion_date == datetime(2024, 1, 15, tzinfo=UTC)


def test_count(make_transport: TransportFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        assert request.url.path.endswith("/DeletedProducts/$count")
        return httpx.Response(200, text="7")

    resource = DeletedProductsResource(
        make_transport(httpx.MockTransport(handler)), BASE_URL
    )
    assert resource.count() == 7
