"""Typed models for OData responses.

The OData API returns JSON with PascalCase field names. These models expose the
data with idiomatic snake_case attributes while accepting the original names on
input. Fields that only appear when requested through ``$expand`` or that depend
on the product are optional, so a partial response still validates.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_CONFIG = ConfigDict(populate_by_name=True, extra="ignore")


class ContentDate(BaseModel):
    """The sensing time span of a product."""

    model_config = _CONFIG

    start: datetime = Field(alias="Start")
    end: datetime = Field(alias="End")


class Checksum(BaseModel):
    """A checksum entry for a product."""

    model_config = _CONFIG

    algorithm: str | None = Field(default=None, alias="Algorithm")
    value: str | None = Field(default=None, alias="Value")
    checksum_date: datetime | None = Field(default=None, alias="ChecksumDate")


class Attribute(BaseModel):
    """A single product attribute, returned when expanding ``Attributes``."""

    model_config = _CONFIG

    odata_type: str | None = Field(default=None, alias="@odata.type")
    name: str = Field(alias="Name")
    value: int | float | str | bool | None = Field(default=None, alias="Value")
    value_type: str | None = Field(default=None, alias="ValueType")


class Location(BaseModel):
    """A physical location of the product data, from ``$expand=Locations``."""

    model_config = _CONFIG

    format: str | None = Field(default=None, alias="Format")
    protocol: str | None = Field(default=None, alias="Protocol")
    path: str | None = Field(default=None, alias="Path")
    content_length: int | None = Field(default=None, alias="ContentLength")


class Asset(BaseModel):
    """An asset such as a quicklook, from ``$expand=Assets``."""

    model_config = _CONFIG

    type: str | None = Field(default=None, alias="Type")
    id: str | None = Field(default=None, alias="Id")
    download_link: str | None = Field(default=None, alias="DownloadLink")
    s3_path: str | None = Field(default=None, alias="S3Path")


class Product(BaseModel):
    """A catalogue product.

    Only ``id`` and ``name`` are guaranteed to be present. Everything else is
    optional so that responses narrowed with ``$select`` still validate.
    """

    model_config = _CONFIG

    id: str = Field(alias="Id")
    name: str = Field(alias="Name")
    content_type: str | None = Field(default=None, alias="ContentType")
    content_length: int | None = Field(default=None, alias="ContentLength")
    origin_date: datetime | None = Field(default=None, alias="OriginDate")
    publication_date: datetime | None = Field(default=None, alias="PublicationDate")
    modification_date: datetime | None = Field(default=None, alias="ModificationDate")
    online: bool | None = Field(default=None, alias="Online")
    eviction_date: datetime | None = Field(default=None, alias="EvictionDate")
    s3_path: str | None = Field(default=None, alias="S3Path")
    content_date: ContentDate | None = Field(default=None, alias="ContentDate")
    footprint: str | None = Field(default=None, alias="Footprint")
    geo_footprint: dict[str, Any] | None = Field(default=None, alias="GeoFootprint")
    checksum: list[Checksum] = Field(default_factory=list, alias="Checksum")
    attributes: list[Attribute] = Field(default_factory=list, alias="Attributes")
    assets: list[Asset] = Field(default_factory=list, alias="Assets")
    locations: list[Location] = Field(default_factory=list, alias="Locations")


class DeletedProduct(Product):
    """A product that has been removed from the catalogue."""

    model_config = _CONFIG

    deletion_date: datetime | None = Field(default=None, alias="DeletionDate")
    deletion_cause: str | None = Field(default=None, alias="DeletionCause")


class ProductPage(BaseModel):
    """A single page of a products query."""

    model_config = _CONFIG

    value: list[Product] = Field(default_factory=list)
    next_link: str | None = Field(default=None, alias="@odata.nextLink")
    count: int | None = Field(default=None, alias="@odata.count")


class DeletedProductPage(BaseModel):
    """A single page of a deleted products query."""

    model_config = _CONFIG

    value: list[DeletedProduct] = Field(default_factory=list)
    next_link: str | None = Field(default=None, alias="@odata.nextLink")
    count: int | None = Field(default=None, alias="@odata.count")


class NodeLink(BaseModel):
    """A link to the children of a node."""

    model_config = _CONFIG

    uri: str | None = Field(default=None, alias="uri")


class Node(BaseModel):
    """A node in a product's internal file tree.

    The exact response shape for node listings is not fully documented; the
    fields here are parsed leniently and unknown keys are ignored, so the shape
    should be confirmed against the live API before relying on it.
    """

    model_config = _CONFIG

    name: str = Field(alias="Name")
    id: str | None = Field(default=None, alias="Id")
    content_length: int | None = Field(default=None, alias="ContentLength")
    children_number: int | None = Field(default=None, alias="ChildrenNumber")
    nodes: NodeLink | None = Field(default=None, alias="Nodes")

    @property
    def is_directory(self) -> bool:
        """Whether this node has children and is therefore a directory."""
        return bool(self.children_number)


class AttributeDefinition(BaseModel):
    """A queryable attribute exposed by the ``Attributes`` endpoint.

    The response shape for this endpoint is not documented in detail, so the
    model is lenient and should be confirmed against the live API.
    """

    model_config = _CONFIG

    name: str | None = Field(default=None, alias="Name")
    value_type: str | None = Field(default=None, alias="ValueType")
    odata_type: str | None = Field(default=None, alias="@odata.type")
