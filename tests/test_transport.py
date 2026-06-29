"""Tests for the HTTP transport layer."""

from __future__ import annotations

import httpx
import pytest

from cdse.auth.manager import TokenManager
from cdse.auth.providers import PasswordAuth
from cdse.config import Settings
from cdse.exceptions import NotFoundError, RateLimitError
from cdse.transport import Transport

TOKEN_URL = "https://identity.example/token"
API_URL = "https://api.example/resource"


def _token_response() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "access_token": "access",
            "expires_in": 600,
            "refresh_token": "refresh",
            "refresh_expires_in": 3600,
            "token_type": "Bearer",
        },
    )


def _build(handler: httpx.MockTransport) -> Transport:
    http = httpx.Client(transport=handler)
    tokens = TokenManager(PasswordAuth("user", "pass"), http=http, token_url=TOKEN_URL)
    settings = Settings(max_retries=3, backoff_factor=0.0, backoff_max=0.0)
    return Transport(http, tokens, settings=settings)


def test_successful_request_attaches_bearer() -> None:
    seen_auth: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        seen_auth.append(request.headers["Authorization"])
        return httpx.Response(200, json={"ok": True})

    transport = _build(httpx.MockTransport(handler))
    response = transport.request("GET", API_URL)
    assert response.json() == {"ok": True}
    assert seen_auth == ["Bearer access"]


def test_rate_limit_is_retried_then_succeeds() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        if request.url.path.endswith("/token"):
            return _token_response()
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, text="slow down")
        return httpx.Response(200, json={"ok": True})

    transport = _build(httpx.MockTransport(handler))
    response = transport.request("GET", API_URL)
    assert response.status_code == 200
    assert attempts == 2


def test_rate_limit_exhausts_retries_and_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        return httpx.Response(429, headers={"Retry-After": "0"}, text="slow down")

    transport = _build(httpx.MockTransport(handler))
    with pytest.raises(RateLimitError) as info:
        transport.request("GET", API_URL)
    assert info.value.status_code == 429
    assert info.value.retry_after == 0.0


def test_unauthorized_triggers_single_refresh_and_retry() -> None:
    api_calls = 0
    token_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal api_calls, token_calls
        if request.url.path.endswith("/token"):
            token_calls += 1
            return _token_response()
        api_calls += 1
        if api_calls == 1:
            return httpx.Response(401, text="expired")
        return httpx.Response(200, json={"ok": True})

    transport = _build(httpx.MockTransport(handler))
    response = transport.request("GET", API_URL)
    assert response.status_code == 200
    assert api_calls == 2
    # One token call for the initial grant, one for the forced refresh.
    assert token_calls == 2


def test_not_found_maps_to_exception() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        return httpx.Response(404, text="missing")

    transport = _build(httpx.MockTransport(handler))
    with pytest.raises(NotFoundError):
        transport.request("GET", API_URL)
