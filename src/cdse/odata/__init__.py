"""OData catalogue API: models, query builders, and resources."""

from __future__ import annotations

from cdse.odata.api import OData
from cdse.odata.attributes import AttributesResource
from cdse.odata.bursts import BurstsResource
from cdse.odata.deleted import DeletedProductsResource
from cdse.odata.models import (
    Asset,
    Attribute,
    AttributeDefinition,
    Burst,
    BurstPage,
    Checksum,
    ContentDate,
    DeletedProduct,
    DeletedProductPage,
    Location,
    Node,
    NodeLink,
    Product,
    ProductPage,
)
from cdse.odata.products import ProductsResource
from cdse.odata.query import (
    ComparisonOperator,
    FilterBuilder,
    SortDirection,
    build_orderby,
    escape_literal,
    resolve_filter,
)

__all__ = [
    "Asset",
    "Attribute",
    "AttributeDefinition",
    "AttributesResource",
    "Burst",
    "BurstPage",
    "BurstsResource",
    "Checksum",
    "ComparisonOperator",
    "ContentDate",
    "DeletedProduct",
    "DeletedProductPage",
    "DeletedProductsResource",
    "FilterBuilder",
    "Location",
    "Node",
    "NodeLink",
    "OData",
    "Product",
    "ProductPage",
    "ProductsResource",
    "SortDirection",
    "build_orderby",
    "escape_literal",
    "resolve_filter",
]
