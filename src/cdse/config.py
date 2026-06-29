"""Configuration for the CDSE client.

The defaults reflect the public Copernicus Data Space Ecosystem endpoints and
the documented account limits. Every value can be overridden either by passing
a :class:`Settings` instance to the client or through environment variables
prefixed with ``CDSE_`` (for example ``CDSE_USERNAME``).
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

#: OpenID Connect token endpoint of the CDSE Keycloak realm.
DEFAULT_TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu"
    "/auth/realms/CDSE/protocol/openid-connect/token"
)

#: Base URL of the OData catalogue API (without a trailing slash).
DEFAULT_ODATA_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"

#: Base URL of the STAC API (without a trailing slash). The earlier
#: ``catalogue.dataspace.copernicus.eu/stac`` host was deprecated in 2025.
DEFAULT_STAC_URL = "https://stac.dataspace.copernicus.eu/v1"

#: Public Keycloak client identifier used for the password and refresh grants.
DEFAULT_CLIENT_ID = "cdse-public"

#: S3 endpoint for direct access to the ``eodata`` bucket.
DEFAULT_S3_ENDPOINT_URL = "https://eodata.dataspace.copernicus.eu"

#: Name of the S3 bucket holding the product archive.
DEFAULT_S3_BUCKET = "eodata"


class Settings(BaseSettings):
    """Runtime configuration, populated from arguments or the environment."""

    model_config = SettingsConfigDict(
        env_prefix="CDSE_",
        env_file=".env",
        extra="ignore",
    )

    token_url: str = DEFAULT_TOKEN_URL
    odata_url: str = DEFAULT_ODATA_URL
    stac_url: str = DEFAULT_STAC_URL
    client_id: str = DEFAULT_CLIENT_ID

    # Optional credentials, convenient for command line and continuous
    # integration use. The library can also be given an auth provider directly.
    username: str | None = None
    password: str | None = None
    totp: str | None = None

    # Transport behaviour.
    request_timeout: float = 30.0
    max_retries: int = 5
    backoff_factor: float = 0.5
    backoff_max: float = 60.0

    # Refresh the access token this many seconds before it actually expires, to
    # absorb clock skew and request latency. The access token is valid for
    # roughly ten minutes and the refresh token for roughly sixty.
    expiry_skew: float = 30.0

    # The documented limit is four concurrent connections for immediately
    # available data.
    max_concurrent_downloads: int = 4

    # The per minute request ceiling for OData is not published, so proactive
    # throttling is opt in. When set, the transport keeps requests under this
    # rate; otherwise it relies on reactive handling of rate limit responses.
    requests_per_minute: int | None = None

    # Direct S3 access uses credentials generated separately from the account
    # password, through the S3 keys manager portal.
    s3_endpoint_url: str = DEFAULT_S3_ENDPOINT_URL
    s3_bucket: str = DEFAULT_S3_BUCKET
    s3_region: str = "default"
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
