"""Python client for the Copernicus Data Space Ecosystem (CDSE) APIs."""

from __future__ import annotations

from cdse.auth import (
    ClientCredentialsAuth,
    PasswordAuth,
    RefreshTokenAuth,
)
from cdse.client import Client
from cdse.config import Settings
from cdse.exceptions import (
    AuthError,
    CdseError,
    CdseHTTPError,
    NotFoundError,
    QuotaExceededError,
    RateLimitError,
    ReauthRequiredError,
    ServerError,
    TransportError,
)

__version__ = "0.1.0"

__all__ = [
    "AuthError",
    "CdseError",
    "CdseHTTPError",
    "Client",
    "ClientCredentialsAuth",
    "NotFoundError",
    "PasswordAuth",
    "QuotaExceededError",
    "RateLimitError",
    "ReauthRequiredError",
    "RefreshTokenAuth",
    "ServerError",
    "Settings",
    "TransportError",
    "__version__",
]
