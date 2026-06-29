"""The OData API namespace.

Groups the OData resources behind a single object so that callers reach them as
``client.odata.products``, ``client.odata.deleted_products``, and
``client.odata.attributes``.
"""

from __future__ import annotations

from cdse.odata.attributes import AttributesResource
from cdse.odata.deleted import DeletedProductsResource
from cdse.odata.products import ProductsResource
from cdse.transport import Transport


class OData:
    """Entry point for the OData catalogue resources."""

    def __init__(self, transport: Transport, base_url: str) -> None:
        self.products = ProductsResource(transport, base_url)
        self.deleted_products = DeletedProductsResource(transport, base_url)
        self.attributes = AttributesResource(transport, base_url)
