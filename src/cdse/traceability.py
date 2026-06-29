"""The Traceability API.

The traceability service records a signed trace for every product, which lets
you confirm a product's origin and integrity. The service is publicly readable,
so this client does not send a bearer token.

Only the lookup by product name is documented; other endpoints are described in
the service's OpenAPI page. The trace record schema is not published, so the
:class:`Trace` model keeps every returned field. Verifying the digital signature
of a trace involves certificate handling and is delegated to the official
``trace-cli`` tool (https://github.com/eu-cdse/trace-cli).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ConfigDict, Field

from cdse.exceptions import CdseHTTPError, NotFoundError


class Trace(BaseModel):
    """A traceability record for a product.

    Because the response schema is not published, unknown fields are retained
    and can be read with :meth:`pydantic.BaseModel.model_dump`. The few fields
    declared here are best effort and may be absent.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str | None = Field(default=None, alias="id")
    product_name: str | None = Field(default=None, alias="obj")
    hash: str | None = Field(default=None, alias="hash")
    hash_algorithm: str | None = Field(default=None, alias="hashAlgorithm")
    timestamp: str | None = Field(default=None, alias="timestamp")
    service_provider: str | None = Field(default=None, alias="serviceProvider")


class TraceabilityResource:
    """Look up product traceability records.

    This resource uses a plain HTTP client because the service is public.
    """

    def __init__(self, http: httpx.Client, base_url: str) -> None:
        self._http = http
        self._base_url = base_url.rstrip("/")

    def get_by_name(self, product_name: str) -> Trace:
        """Fetch the trace for a product by its name."""
        url = f"{self._base_url}/traces/name/{quote(product_name, safe='')}"
        payload = self._get(url)
        # Some deployments return a single object, others a list of traces.
        if isinstance(payload, list):
            if not payload:
                raise NotFoundError(
                    f"No trace found for {product_name!r}.",
                    status_code=404,
                    url=url,
                )
            payload = payload[0]
        return Trace.model_validate(payload)

    def get(self, endpoint: str) -> Any:
        """Call an arbitrary traceability endpoint and return parsed JSON.

        This is an escape hatch for endpoints not modelled here. ``endpoint`` is
        appended to the base URL.
        """
        return self._get(f"{self._base_url}/{endpoint.lstrip('/')}")

    def _get(self, url: str) -> Any:
        response = self._http.get(url, follow_redirects=True)
        if response.status_code == httpx.codes.NOT_FOUND:
            raise NotFoundError(
                f"Traceability request to {url} returned not found.",
                status_code=response.status_code,
                url=url,
                body=response.text[:500],
            )
        if response.is_error:
            raise CdseHTTPError(
                f"Traceability request to {url} failed with status "
                f"{response.status_code}.",
                status_code=response.status_code,
                url=url,
                body=response.text[:500],
            )
        return response.json()
