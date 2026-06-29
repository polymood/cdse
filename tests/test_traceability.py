"""Tests for the Traceability resource."""

from __future__ import annotations

import httpx
import pytest

from cdse.exceptions import NotFoundError
from cdse.traceability import TraceabilityResource

BASE_URL = "https://trace.example/api/v1"


def _resource(handler: httpx.MockTransport) -> TraceabilityResource:
    return TraceabilityResource(httpx.Client(transport=handler), BASE_URL)


def test_get_by_name_returns_trace() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/traces/name/S2A_X.SAFE.zip")
        # No Authorization header: the service is public.
        assert "Authorization" not in request.headers
        return httpx.Response(
            200,
            json={
                "id": "trace-1",
                "obj": "S2A_X.SAFE.zip",
                "hash": "abc123",
                "hashAlgorithm": "SHA3-256",
            },
        )

    resource = _resource(httpx.MockTransport(handler))
    trace = resource.get_by_name("S2A_X.SAFE.zip")
    assert trace.id == "trace-1"
    assert trace.product_name == "S2A_X.SAFE.zip"
    assert trace.hash_algorithm == "SHA3-256"


def test_get_by_name_unwraps_list() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"id": "trace-1", "obj": "P"}])

    resource = _resource(httpx.MockTransport(handler))
    assert resource.get_by_name("P").id == "trace-1"


def test_get_by_name_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    resource = _resource(httpx.MockTransport(handler))
    with pytest.raises(NotFoundError):
        resource.get_by_name("missing")


def test_empty_list_is_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    resource = _resource(httpx.MockTransport(handler))
    with pytest.raises(NotFoundError):
        resource.get_by_name("missing")
