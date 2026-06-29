"""Tests for downloads and node traversal."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import httpx

from cdse.odata.download import download_to_file, parse_nodes
from cdse.odata.products import ProductsResource
from cdse.transport import Transport
from tests.conftest import token_response

BASE_URL = "https://catalogue.example/odata/v1"

TransportFactory = Callable[[httpx.MockTransport], Transport]


def test_download_streams_full_body(
    make_transport: TransportFactory, tmp_path: Path
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        return httpx.Response(200, content=b"hello world")

    transport = make_transport(httpx.MockTransport(handler))
    destination = tmp_path / "product.zip"
    result = download_to_file(transport, f"{BASE_URL}/x", destination)
    assert result == destination
    assert destination.read_bytes() == b"hello world"


def test_download_resumes_with_range(
    make_transport: TransportFactory, tmp_path: Path
) -> None:
    seen_range: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        seen_range.append(request.headers["Range"])
        return httpx.Response(206, content=b"world")

    destination = tmp_path / "product.zip"
    destination.write_bytes(b"hello ")

    transport = make_transport(httpx.MockTransport(handler))
    download_to_file(transport, f"{BASE_URL}/x", destination, resume=True)
    assert seen_range == ["bytes=6-"]
    assert destination.read_bytes() == b"hello world"


def test_resume_rewrites_when_server_ignores_range(
    make_transport: TransportFactory, tmp_path: Path
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        # Server ignores the range and returns the whole body with status 200.
        return httpx.Response(200, content=b"complete")

    destination = tmp_path / "product.zip"
    destination.write_bytes(b"partial")

    transport = make_transport(httpx.MockTransport(handler))
    download_to_file(transport, f"{BASE_URL}/x", destination, resume=True)
    assert destination.read_bytes() == b"complete"


def test_parse_nodes_accepts_result_wrapper() -> None:
    nodes = parse_nodes(
        {
            "result": [
                {"Name": "manifest.safe", "ContentLength": 1234},
                {"Name": "GRANULE", "ChildrenNumber": 3},
            ]
        }
    )
    assert [n.name for n in nodes] == ["manifest.safe", "GRANULE"]
    assert nodes[0].is_directory is False
    assert nodes[1].is_directory is True


def test_list_nodes_builds_nested_path(make_transport: TransportFactory) -> None:
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        seen_paths.append(request.url.path)
        return httpx.Response(200, json={"result": [{"Name": "child"}]})

    resource = ProductsResource(make_transport(httpx.MockTransport(handler)), BASE_URL)
    nodes = resource.list_nodes("abc-123", "GRANULE", "L2A")
    assert [n.name for n in nodes] == ["child"]
    assert seen_paths[-1].endswith("/Products(abc-123)/Nodes(GRANULE)/Nodes(L2A)/Nodes")


def test_download_node_targets_value_endpoint(
    make_transport: TransportFactory, tmp_path: Path
) -> None:
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return token_response()
        seen_paths.append(request.url.path)
        return httpx.Response(200, content=b"file-bytes")

    resource = ProductsResource(make_transport(httpx.MockTransport(handler)), BASE_URL)
    destination = tmp_path / "manifest.safe"
    resource.download_node("abc-123", "manifest.safe", destination=destination)
    assert destination.read_bytes() == b"file-bytes"
    assert seen_paths[-1].endswith("/Products(abc-123)/Nodes(manifest.safe)/$value")
