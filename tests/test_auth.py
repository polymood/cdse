"""Tests for the authentication layer."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from cdse.auth.manager import TokenManager
from cdse.auth.providers import AuthProvider, PasswordAuth, RefreshTokenAuth
from cdse.auth.store import MemoryTokenStore, TokenSet, TokenStore
from cdse.exceptions import ReauthRequiredError, TokenRefreshError

TOKEN_URL = "https://identity.example/token"


def _now() -> datetime:
    return datetime.now(UTC)


def _token_payload(
    access: str, *, refresh: str | None = "refresh-1"
) -> dict[str, object]:
    payload: dict[str, object] = {
        "access_token": access,
        "expires_in": 600,
        "token_type": "Bearer",
    }
    if refresh is not None:
        payload["refresh_token"] = refresh
        payload["refresh_expires_in"] = 3600
    return payload


def _manager(
    handler: httpx.MockTransport,
    *,
    provider: AuthProvider | None = None,
    store: TokenStore | None = None,
) -> TokenManager:
    provider = provider or PasswordAuth("user", "pass")
    return TokenManager(
        provider,
        http=httpx.Client(transport=handler),
        token_url=TOKEN_URL,
        store=store,
    )


def test_token_set_validity_accounts_for_skew() -> None:
    tokens = TokenSet(
        access_token="a",
        access_expiry=_now() + timedelta(seconds=20),
        refresh_token="r",
        refresh_expiry=_now() + timedelta(seconds=20),
    )
    assert tokens.access_valid(skew=0.0) is True
    assert tokens.access_valid(skew=30.0) is False
    assert tokens.refresh_valid(skew=30.0) is False


def test_initial_grant_is_cached() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=_token_payload("access-1"))

    manager = _manager(httpx.MockTransport(handler))
    assert manager.authorization_header() == "Bearer access-1"
    # A second call reuses the cached, still valid token.
    assert manager.authorization_header() == "Bearer access-1"
    assert calls == 1


def test_password_grant_sends_credentials() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(dict(httpx.QueryParams(request.content.decode())))
        return httpx.Response(200, json=_token_payload("access-1"))

    manager = _manager(
        httpx.MockTransport(handler),
        provider=PasswordAuth("alice", "secret", totp="123456"),
    )
    manager.authorization_header()
    assert seen["grant_type"] == "password"
    assert seen["username"] == "alice"
    assert seen["password"] == "secret"
    assert seen["totp"] == "123456"


def test_force_refresh_uses_refresh_token_grant() -> None:
    grants: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        params = dict(httpx.QueryParams(request.content.decode()))
        grants.append(params["grant_type"])
        return httpx.Response(200, json=_token_payload(f"access-{len(grants)}"))

    manager = _manager(httpx.MockTransport(handler))
    assert manager.authorization_header() == "Bearer access-1"
    assert manager.force_refresh() == "Bearer access-2"
    assert grants == ["password", "refresh_token"]


def test_expired_refresh_token_requires_reauthentication() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("no token request expected")

    store = MemoryTokenStore()
    store.save(
        TokenSet(
            access_token="old",
            access_expiry=_now() - timedelta(seconds=10),
            refresh_token="old-refresh",
            refresh_expiry=_now() - timedelta(seconds=10),
        )
    )
    manager = _manager(
        httpx.MockTransport(handler),
        provider=RefreshTokenAuth("old-refresh"),
        store=store,
    )
    with pytest.raises(ReauthRequiredError):
        manager.authorization_header()


def test_token_error_response_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error_description": "invalid credentials"})

    manager = _manager(httpx.MockTransport(handler))
    with pytest.raises(TokenRefreshError, match="invalid credentials"):
        manager.authorization_header()
