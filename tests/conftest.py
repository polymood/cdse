"""Shared test fixtures."""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from cdse.auth.manager import TokenManager
from cdse.auth.providers import PasswordAuth
from cdse.config import Settings
from cdse.transport import Transport

TOKEN_URL = "https://identity.example/token"


def token_response() -> httpx.Response:
    """A minimal successful token response for use inside mock handlers."""
    return httpx.Response(
        200,
        json={"access_token": "access", "expires_in": 600, "token_type": "Bearer"},
    )


@pytest.fixture
def make_transport() -> Callable[[httpx.MockTransport], Transport]:
    """Return a factory that builds a Transport around a mock request handler."""

    def factory(handler: httpx.MockTransport) -> Transport:
        http = httpx.Client(transport=handler)
        tokens = TokenManager(PasswordAuth("u", "p"), http=http, token_url=TOKEN_URL)
        settings = Settings(backoff_factor=0.0, backoff_max=0.0)
        return Transport(http, tokens, settings=settings)

    return factory
