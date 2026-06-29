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
from cdse.odata import (
    FilterBuilder,
    Product,
    ProductPage,
    build_orderby,
)
from cdse.stac import (
    Collection,
    Item,
    ItemCollection,
)

__version__ = "0.1.0"

__all__ = [
    "AuthError",
    "CdseError",
    "CdseHTTPError",
    "Client",
    "ClientCredentialsAuth",
    "Collection",
    "FilterBuilder",
    "Item",
    "ItemCollection",
    "NotFoundError",
    "PasswordAuth",
    "Product",
    "ProductPage",
    "QuotaExceededError",
    "RateLimitError",
    "ReauthRequiredError",
    "RefreshTokenAuth",
    "ServerError",
    "Settings",
    "TransportError",
    "__version__",
    "build_orderby",
]
