"""Typed models for STAC API responses.

These follow the STAC 1.1.0 specification. Item properties are open ended, so
they are kept as a dictionary while a few common ones are exposed through
convenience accessors. Unknown fields are ignored so that responses validate
across collections.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_CONFIG = ConfigDict(populate_by_name=True, extra="ignore")


class Link(BaseModel):
    """A hypermedia link, used for navigation and pagination."""

    model_config = _CONFIG

    rel: str
    href: str
    type: str | None = None
    title: str | None = None
    method: str | None = None
    body: dict[str, Any] | None = None
    merge: bool = False


class Asset(BaseModel):
    """A downloadable asset attached to an item."""

    model_config = _CONFIG

    href: str
    title: str | None = None
    description: str | None = None
    type: str | None = None
    roles: list[str] = Field(default_factory=list)


class Item(BaseModel):
    """A STAC item, representing a single product."""

    model_config = _CONFIG

    type: str = "Feature"
    stac_version: str | None = None
    id: str
    collection: str | None = None
    geometry: dict[str, Any] | None = None
    bbox: list[float] | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    assets: dict[str, Asset] = Field(default_factory=dict)
    links: list[Link] = Field(default_factory=list)

    @property
    def datetime(self) -> str | None:
        """The item's ``datetime`` property, when present."""
        value = self.properties.get("datetime")
        return value if isinstance(value, str) else None

    @property
    def cloud_cover(self) -> float | None:
        """The ``eo:cloud_cover`` property, when present."""
        value = self.properties.get("eo:cloud_cover")
        return float(value) if isinstance(value, int | float) else None


class ItemCollection(BaseModel):
    """A GeoJSON FeatureCollection of STAC items, as returned by search."""

    model_config = _CONFIG

    type: str = "FeatureCollection"
    features: list[Item] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)
    context: dict[str, Any] | None = None
    number_matched: int | None = Field(default=None, alias="numberMatched")
    number_returned: int | None = Field(default=None, alias="numberReturned")


class Collection(BaseModel):
    """A STAC collection description."""

    model_config = _CONFIG

    type: str | None = None
    id: str
    title: str | None = None
    description: str | None = None
    license: str | None = None
    extent: dict[str, Any] | None = None
    keywords: list[str] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)


class CollectionList(BaseModel):
    """The response of the ``/collections`` endpoint."""

    model_config = _CONFIG

    collections: list[Collection] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)
