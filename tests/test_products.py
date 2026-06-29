"""Tests for the Products resource."""

from __future__ import annotations

import json

import httpx

from cdse.auth.manager import TokenManager
from cdse.auth.providers import PasswordAuth
from cdse.config import Settings
from cdse.odata.products import ProductsResource
from cdse.odata.query import FilterBuilder
from cdse.transport import Transport

TOKEN_URL = "https://identity.example/token"
BASE_URL = "https://catalogue.example/odata/v1"


def _token_response() -> httpx.Response:
    return httpx.Response(
        200,
        json={"access_token": "access", "expires_in": 600, "token_type": "Bearer"},
    )


def _resource(handler: httpx.MockTransport) -> ProductsResource:
    http = httpx.Client(transport=handler)
    tokens = TokenManager(PasswordAuth("u", "p"), http=http, token_url=TOKEN_URL)
    settings = Settings(backoff_factor=0.0, backoff_max=0.0)
    transport = Transport(http, tokens, settings=settings)
    return ProductsResource(transport, BASE_URL)


def test_search_follows_paging_links() -> None:
    captured_filter: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        skip = request.url.params.get("skip")
        if request.url.params.get("$filter"):
            captured_filter.append(request.url.params["$filter"])
        if skip is None:
            return httpx.Response(
                200,
                json={
                    "value": [{"Id": "1", "Name": "A"}, {"Id": "2", "Name": "B"}],
                    "@odata.nextLink": f"{BASE_URL}/Products?skip=2",
                },
            )
        return httpx.Response(200, json={"value": [{"Id": "3", "Name": "C"}]})

    resource = _resource(httpx.MockTransport(handler))
    products = list(resource.search(FilterBuilder().collection("SENTINEL-2"), top=2))
    assert [p.id for p in products] == ["1", "2", "3"]
    assert captured_filter == ["Collection/Name eq 'SENTINEL-2'"]


def test_search_page_includes_count() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        assert request.url.params["$count"] == "true"
        return httpx.Response(
            200, json={"value": [{"Id": "1", "Name": "A"}], "@odata.count": 137}
        )

    resource = _resource(httpx.MockTransport(handler))
    page = resource.search_page(top=1, count=True)
    assert page.count == 137
    assert page.value[0].name == "A"


def test_get_single_product_with_expand() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        assert request.url.path.endswith("/Products(abc-123)")
        assert request.url.params["$expand"] == "Attributes"
        return httpx.Response(
            200,
            json={
                "Id": "abc-123",
                "Name": "PRODUCT",
                "Online": True,
                "Attributes": [
                    {
                        "@odata.type": "#OData.CSC.DoubleAttribute",
                        "Name": "cloudCover",
                        "Value": 12.5,
                    }
                ],
            },
        )

    resource = _resource(httpx.MockTransport(handler))
    product = resource.get("abc-123", expand=["Attributes"])
    assert product.online is True
    assert product.attributes[0].name == "cloudCover"
    assert product.attributes[0].value == 12.5


def test_count_returns_integer() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        assert request.url.path.endswith("/Products/$count")
        return httpx.Response(200, text="42")

    resource = _resource(httpx.MockTransport(handler))
    assert resource.count(FilterBuilder().collection("SENTINEL-1")) == 42


def test_filter_list_posts_names() -> None:
    seen_body: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        seen_body.update(json.loads(request.content))
        return httpx.Response(200, json={"value": [{"Id": "1", "Name": "one"}]})

    resource = _resource(httpx.MockTransport(handler))
    products = resource.filter_list(["one", "two"])
    assert [p.name for p in products] == ["one"]
    assert seen_body == {"FilterProducts": [{"Name": "one"}, {"Name": "two"}]}
