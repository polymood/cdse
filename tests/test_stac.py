"""Tests for the STAC search, browse, and download resource."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from cdse.exceptions import CdseError
from cdse.stac.api import Stac
from cdse.stac.models import Asset, Item
from cdse.transport import Transport
from tests.conftest import token_response

BASE_URL = "https://stac.example/v1"

TransportFactory = Callable[[httpx.MockTransport], Transport]
Handler = Callable[[httpx.Request], httpx.Response]


def _stac(handler: Handler, make_transport: TransportFactory) -> Stac:
    return Stac(make_transport(httpx.MockTransport(handler)), BASE_URL)


def test_search_posts_body_and_follows_next(
    make_transport: TransportFactory,
) -> None:
    bodies: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        body = json.loads(request.content)
        bodies.append(body)
        if "token" not in body:
            return httpx.Response(
                200,
                json={
                    "type": "FeatureCollection",
                    "features": [{"type": "Feature", "id": "item-1"}],
                    "links": [
                        {
                            "rel": "next",
                            "href": f"{BASE_URL}/search",
                            "method": "POST",
                            "body": {"token": "page2"},
                        }
                    ],
                },
            )
        return httpx.Response(
            200,
            json={
                "type": "FeatureCollection",
                "features": [{"type": "Feature", "id": "item-2"}],
                "links": [],
            },
        )

    stac = _stac(handler, make_transport)
    items = list(
        stac.search(
            collections=["sentinel-2-l2a"],
            bbox=[4.0, 50.0, 5.0, 51.0],
            filter={"op": "<=", "args": [{"property": "eo:cloud_cover"}, 10]},
            filter_lang="cql2-json",
        )
    )
    assert [item.id for item in items] == ["item-1", "item-2"]
    assert bodies[0]["collections"] == ["sentinel-2-l2a"]
    assert bodies[0]["bbox"] == [4.0, 50.0, 5.0, 51.0]
    assert bodies[0]["filter-lang"] == "cql2-json"
    assert bodies[1] == {"token": "page2"}


def test_collections_and_single_collection(
    make_transport: TransportFactory,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        if request.url.path.endswith("/collections"):
            return httpx.Response(
                200,
                json={"collections": [{"id": "sentinel-2-l2a", "title": "S2 L2A"}]},
            )
        assert request.url.path.endswith("/collections/sentinel-2-l2a")
        return httpx.Response(200, json={"id": "sentinel-2-l2a", "license": "various"})

    stac = _stac(handler, make_transport)
    collections = stac.collections()
    assert collections[0].id == "sentinel-2-l2a"
    assert stac.collection("sentinel-2-l2a").license == "various"


def test_item_and_properties(make_transport: TransportFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        assert request.url.path.endswith("/collections/c/items/i")
        return httpx.Response(
            200,
            json={
                "type": "Feature",
                "id": "i",
                "collection": "c",
                "properties": {
                    "datetime": "2024-05-01T00:00:00Z",
                    "eo:cloud_cover": 8.5,
                },
            },
        )

    stac = _stac(handler, make_transport)
    item = stac.item("c", "i")
    assert item.datetime == "2024-05-01T00:00:00Z"
    assert item.cloud_cover == 8.5


def test_queryables_for_collection(make_transport: TransportFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        assert request.url.path.endswith("/collections/c/queryables")
        return httpx.Response(200, json={"properties": {"eo:cloud_cover": {}}})

    stac = _stac(handler, make_transport)
    assert "properties" in stac.queryables("c")


def test_download_asset_http(make_transport: TransportFactory, tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        return httpx.Response(200, content=b"product-bytes")

    stac = _stac(handler, make_transport)
    item = Item(id="i", assets={"PRODUCT": Asset(href=f"{BASE_URL}/download/i")})
    destination = tmp_path / "out.zip"
    stac.download_asset(item, "PRODUCT", destination)
    assert destination.read_bytes() == b"product-bytes"


def test_download_asset_s3_is_rejected(
    make_transport: TransportFactory, tmp_path: Path
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return token_response()

    stac = _stac(handler, make_transport)
    item = Item(id="i", assets={"PRODUCT": Asset(href="s3://eodata/x")})
    with pytest.raises(CdseError, match="S3"):
        stac.download_asset(item, "PRODUCT", tmp_path / "out.zip")


def test_download_missing_asset_raises(
    make_transport: TransportFactory, tmp_path: Path
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return token_response()

    stac = _stac(handler, make_transport)
    item = Item(id="i", assets={})
    with pytest.raises(CdseError, match="no asset"):
        stac.download_asset(item, "PRODUCT", tmp_path / "out.zip")
