"""The Attributes resource of the OData API.

This endpoint lists the attributes that can be used in filter expressions,
either across all collections or for a single collection. The exact response
shape is not documented in detail, so the listing is parsed leniently.
"""

from __future__ import annotations

from typing import Any

from cdse.odata.models import AttributeDefinition
from cdse.transport import Transport


class AttributesResource:
    """Access the ``Attributes`` collection of the OData catalogue."""

    def __init__(self, transport: Transport, base_url: str) -> None:
        self._transport = transport
        self._url = f"{base_url.rstrip('/')}/Attributes"

    def list(self, collection: str | None = None) -> list[AttributeDefinition]:
        """List queryable attributes, optionally scoped to a collection.

        Args:
            collection: A collection name such as ``SENTINEL-1``. When omitted,
                attributes for all collections are returned.
        """
        url = self._url if collection is None else f"{self._url}({collection})"
        response = self._transport.request("GET", url)
        return _parse_attributes(response.json())


def _parse_attributes(payload: Any) -> list[AttributeDefinition]:
    """Parse an attributes response, tolerating a list or a wrapped object."""
    raw: Any = payload
    if isinstance(payload, dict):
        raw = payload.get("value")
        if raw is None:
            raw = payload.get("result")
    if not isinstance(raw, list):
        return []
    return [AttributeDefinition.model_validate(item) for item in raw]
