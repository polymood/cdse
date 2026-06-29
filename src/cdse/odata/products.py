"""The Products resource of the OData API.

This wraps the catalogue endpoints for searching products, fetching a single
product, counting matches, and resolving a list of product names. Searching
returns a lazy iterator that follows the server's paging links so that callers
can stream through arbitrarily large result sets.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from cdse.odata.models import Product, ProductPage
from cdse.odata.query import FilterBuilder
from cdse.transport import Transport


class ProductsResource:
    """Access the ``Products`` collection of the OData catalogue."""

    def __init__(self, transport: Transport, base_url: str) -> None:
        self._transport = transport
        self._products_url = f"{base_url.rstrip('/')}/Products"

    def search(
        self,
        query: str | FilterBuilder | None = None,
        *,
        order_by: str | None = None,
        top: int | None = None,
        skip: int | None = None,
        expand: Sequence[str] | None = None,
        select: Sequence[str] | None = None,
    ) -> Iterator[Product]:
        """Yield products matching the query, following paging links lazily.

        Args:
            query: A :class:`FilterBuilder` or a raw ``$filter`` string.
            order_by: An ``$orderby`` clause such as ``"ContentDate/Start desc"``.
            top: Page size for the first request.
            skip: Number of leading results to skip.
            expand: Related data to include, for example ``["Attributes"]``.
            select: Specific fields to return.
        """
        page = self.search_page(
            query,
            order_by=order_by,
            top=top,
            skip=skip,
            expand=expand,
            select=select,
        )
        while True:
            yield from page.value
            if page.next_link is None:
                return
            response = self._transport.request("GET", page.next_link)
            page = ProductPage.model_validate(response.json())

    def search_page(
        self,
        query: str | FilterBuilder | None = None,
        *,
        order_by: str | None = None,
        top: int | None = None,
        skip: int | None = None,
        expand: Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        count: bool = False,
    ) -> ProductPage:
        """Return a single page of results, optionally including the total count."""
        params: dict[str, str] = {}
        filter_value = _filter_value(query)
        if filter_value:
            params["$filter"] = filter_value
        if order_by is not None:
            params["$orderby"] = order_by
        if top is not None:
            params["$top"] = str(top)
        if skip is not None:
            params["$skip"] = str(skip)
        if expand:
            params["$expand"] = ",".join(expand)
        if select:
            params["$select"] = ",".join(select)
        if count:
            params["$count"] = "true"

        response = self._transport.request("GET", self._products_url, params=params)
        return ProductPage.model_validate(response.json())

    def get(self, product_id: str, *, expand: Sequence[str] | None = None) -> Product:
        """Fetch a single product by its UUID."""
        params: dict[str, str] = {}
        if expand:
            params["$expand"] = ",".join(expand)
        response = self._transport.request(
            "GET", f"{self._products_url}({product_id})", params=params or None
        )
        return Product.model_validate(response.json())

    def count(self, query: str | FilterBuilder | None = None) -> int:
        """Return the number of products matching the query."""
        params: dict[str, str] = {}
        filter_value = _filter_value(query)
        if filter_value:
            params["$filter"] = filter_value
        response = self._transport.request(
            "GET", f"{self._products_url}/$count", params=params or None
        )
        return int(response.text.strip())

    def filter_list(self, names: Sequence[str]) -> list[Product]:
        """Resolve a list of product names in a single bulk request."""
        body = {"FilterProducts": [{"Name": name} for name in names]}
        response = self._transport.request(
            "POST", f"{self._products_url}/OData.CSC.FilterList", json=body
        )
        return ProductPage.model_validate(response.json()).value


def _filter_value(query: str | FilterBuilder | None) -> str | None:
    """Resolve a query argument to a filter string, or ``None`` when empty."""
    if query is None:
        return None
    if isinstance(query, FilterBuilder):
        return query.build() or None
    return query or None
