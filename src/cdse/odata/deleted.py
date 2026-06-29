"""The DeletedProducts resource of the OData API.

This mirrors the Products resource but targets the catalogue of removed
products, which carries the additional ``DeletionDate`` and ``DeletionCause``
fields. Use :meth:`cdse.odata.query.FilterBuilder.deleted_between` and
``deletion_cause`` to filter on them.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from cdse.odata.models import DeletedProduct, DeletedProductPage
from cdse.odata.query import FilterBuilder, resolve_filter
from cdse.transport import Transport


class DeletedProductsResource:
    """Access the ``DeletedProducts`` collection of the OData catalogue."""

    def __init__(self, transport: Transport, base_url: str) -> None:
        self._transport = transport
        self._url = f"{base_url.rstrip('/')}/DeletedProducts"

    def search(
        self,
        query: str | FilterBuilder | None = None,
        *,
        order_by: str | None = None,
        top: int | None = None,
        skip: int | None = None,
        expand: Sequence[str] | None = None,
        select: Sequence[str] | None = None,
    ) -> Iterator[DeletedProduct]:
        """Yield deleted products matching the query, following paging links."""
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
            page = DeletedProductPage.model_validate(response.json())

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
    ) -> DeletedProductPage:
        """Return a single page of deleted products."""
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

        response = self._transport.request("GET", self._url, params=params)
        return DeletedProductPage.model_validate(response.json())

    def count(self, query: str | FilterBuilder | None = None) -> int:
        """Return the number of deleted products matching the query."""
        params: dict[str, str] = {}
        filter_value = resolve_filter(query)
        if filter_value:
            params["$filter"] = filter_value
        response = self._transport.request(
            "GET", f"{self._url}/$count", params=params or None
        )
        return int(response.text.strip())
