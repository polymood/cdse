"""The public client facade.

This ties the transport and authentication layers together behind a single
object. Resource groups such as OData are attached here as they are built, so
that callers interact with one client rather than wiring the layers themselves.
"""

from __future__ import annotations

from types import TracebackType

import httpx

from cdse.auth.manager import TokenManager
from cdse.auth.providers import AuthProvider
from cdse.auth.store import TokenStore
from cdse.config import Settings
from cdse.odata.api import OData
from cdse.s3 import S3Client
from cdse.stac.api import Stac
from cdse.transport import Transport


class Client:
    """Entry point for talking to the Copernicus Data Space Ecosystem APIs.

    Args:
        auth: The authentication provider describing how to obtain tokens.
        settings: Optional configuration; sensible defaults are used otherwise.
        store: Optional token store; tokens are kept in memory by default.

    The client owns an :class:`httpx.Client` and should be closed when finished,
    either explicitly with :meth:`close` or by using it as a context manager.
    """

    def __init__(
        self,
        auth: AuthProvider,
        *,
        settings: Settings | None = None,
        store: TokenStore | None = None,
    ) -> None:
        self._settings = settings if settings is not None else Settings()
        self._http = httpx.Client()
        self._tokens = TokenManager(
            auth,
            http=self._http,
            token_url=self._settings.token_url,
            store=store,
            expiry_skew=self._settings.expiry_skew,
        )
        self._transport = Transport(self._http, self._tokens, settings=self._settings)

        #: Access to the OData catalogue endpoints (products, deleted
        #: products, and attributes).
        self.odata = OData(self._transport, self._settings.odata_url)

        #: Access to the STAC catalogue: search, browse, and asset download.
        self.stac = Stac(self._transport, self._settings.stac_url)

        self._s3: S3Client | None = None

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def transport(self) -> Transport:
        return self._transport

    @property
    def auth(self) -> TokenManager:
        return self._tokens

    @property
    def s3(self) -> S3Client:
        """Direct S3 access to the product archive.

        Requires S3 credentials in the settings and the optional ``s3`` extra.
        """
        if self._s3 is None:
            self._s3 = S3Client.from_settings(self._settings)
        return self._s3

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
