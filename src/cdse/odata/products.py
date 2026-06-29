"""The Products resource of the OData API.

This wraps the catalogue endpoints for searching products, fetching a single
product, counting matches, and resolving a list of product names. Searching
returns a lazy iterator that follows the server's paging links so that callers
can stream through arbitrarily large result sets.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path
from urllib.parse import quote

from cdse.odata.download import DEFAULT_CHUNK_SIZE, download_to_file, parse_nodes
from cdse.odata.models import Node, Product, ProductPage
from cdse.odata.query import FilterBuilder, resolve_filter
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
        filter_value = resolve_filter(query)
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
        filter_value = resolve_filter(query)
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

    def download(
        self,
        product_id: str,
        destination: str | Path,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        resume: bool = False,
    ) -> Path:
        """Download a whole product to ``destination`` as a zip archive."""
        url = f"{self._products_url}({product_id})/$value"
        return download_to_file(
            self._transport,
            url,
            Path(destination),
            chunk_size=chunk_size,
            resume=resume,
        )

    def list_nodes(self, product_id: str, *path: str) -> list[Node]:
        """List the nodes inside a product, optionally at a nested path.

        Calling without a path lists the product root; passing node names
        descends into the file tree.
        """
        url = f"{self._products_url}{_node_segments(product_id, path)}/Nodes"
        response = self._transport.request("GET", url)
        return parse_nodes(response.json())

    def download_node(
        self,
        product_id: str,
        *path: str,
        destination: str | Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        resume: bool = False,
    ) -> Path:
        """Download a single file node from inside a product."""
        if not path:
            raise ValueError("A node path is required to download a node.")
        url = f"{self._products_url}{_node_segments(product_id, path)}/$value"
        return download_to_file(
            self._transport,
            url,
            Path(destination),
            chunk_size=chunk_size,
            resume=resume,
        )


def _node_segments(product_id: str, path: Sequence[str]) -> str:
    """Build the URL path for a product node, escaping each node name."""
    segments = f"({product_id})"
    for name in path:
        segments += f"/Nodes({quote(name, safe='')})"
    return segments
