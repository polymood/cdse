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
from cdse.s3 import S3Client
from cdse.stac import (
    Collection,
    Item,
    ItemCollection,
)
from cdse.subscriptions import (
    Notification,
    Subscription,
    SubscriptionsResource,
)
from cdse.traceability import Trace, TraceabilityResource

__version__ = "0.1.1"

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
    "Notification",
    "PasswordAuth",
    "Product",
    "ProductPage",
    "QuotaExceededError",
    "RateLimitError",
    "ReauthRequiredError",
    "RefreshTokenAuth",
    "S3Client",
    "ServerError",
    "Settings",
    "Subscription",
    "SubscriptionsResource",
    "Trace",
    "TraceabilityResource",
    "TransportError",
    "__version__",
    "build_orderby",
]
