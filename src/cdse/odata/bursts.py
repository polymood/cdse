"""The Bursts resource of the OData API (Sentinel-1 SLC bursts).

This is an OData collection like Products, so it shares the same query and
paging mechanics. Searching is fully supported. There is no per burst download
endpoint: extracting a single burst is done with an external GDAL based tool and
is out of scope here. The parent product can still be downloaded with
``client.odata.products.download(burst.parent_product_id)`` or from S3 using
``burst.s3_path``.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime

from cdse.odata.models import Burst, BurstPage
from cdse.odata.query import FilterBuilder, escape_literal, resolve_filter
from cdse.transport import Transport


class BurstsResource:
    """Access the ``Bursts`` collection of the OData catalogue."""

    def __init__(self, transport: Transport, base_url: str) -> None:
        self._transport = transport
        self._url = f"{base_url.rstrip('/')}/Bursts"

    def search(
        self,
        query: str | FilterBuilder | None = None,
        *,
        burst_id: int | None = None,
        parent_product_id: str | None = None,
        swath: str | None = None,
        polarisation: str | None = None,
        intersects: str | None = None,
        start: datetime | date | None = None,
        end: datetime | date | None = None,
        order_by: str | None = None,
        top: int | None = None,
        skip: int | None = None,
    ) -> Iterator[Burst]:
        """Yield bursts matching the query, following paging links lazily.

        The keyword arguments are convenience filters that are combined with a
        logical ``and``; ``query`` may add a raw expression or builder on top.
        """
        builder = _build_filter(
            burst_id=burst_id,
            parent_product_id=parent_product_id,
            swath=swath,
            polarisation=polarisation,
            intersects=intersects,
            start=start,
            end=end,
            extra=query,
        )
        page = self.search_page(builder, order_by=order_by, top=top, skip=skip)
        while True:
            yield from page.value
            if page.next_link is None:
                return
            response = self._transport.request("GET", page.next_link)
            page = BurstPage.model_validate(response.json())

    def search_page(
        self,
        query: str | FilterBuilder | None = None,
        *,
        order_by: str | None = None,
        top: int | None = None,
        skip: int | None = None,
        count: bool = False,
    ) -> BurstPage:
        """Return a single page of bursts."""
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
        if count:
            params["$count"] = "true"
        response = self._transport.request("GET", self._url, params=params)
        return BurstPage.model_validate(response.json())

    def get(self, burst_id: str) -> Burst:
        """Fetch a single burst by its UUID."""
        response = self._transport.request("GET", f"{self._url}({burst_id})")
        return Burst.model_validate(response.json())

    def count(self, query: str | FilterBuilder | None = None) -> int:
        """Return the number of bursts matching the query."""
        params: dict[str, str] = {}
        filter_value = resolve_filter(query)
        if filter_value:
            params["$filter"] = filter_value
        response = self._transport.request(
            "GET", f"{self._url}/$count", params=params or None
        )
        return int(response.text.strip())


def _build_filter(
    *,
    burst_id: int | None,
    parent_product_id: str | None,
    swath: str | None,
    polarisation: str | None,
    intersects: str | None,
    start: datetime | date | None,
    end: datetime | date | None,
    extra: str | FilterBuilder | None,
) -> FilterBuilder:
    """Combine the burst convenience filters into a single builder."""
    builder = FilterBuilder()
    if burst_id is not None:
        builder.raw(f"BurstId eq {burst_id}")
    if parent_product_id is not None:
        builder.raw(f"ParentProductId eq '{escape_literal(parent_product_id)}'")
    if swath is not None:
        builder.raw(f"SwathIdentifier eq '{escape_literal(swath)}'")
    if polarisation is not None:
        builder.raw(f"PolarisationChannels eq '{escape_literal(polarisation)}'")
    if intersects is not None:
        builder.intersects(intersects)
    if start is not None and end is not None:
        builder.acquired_between(start, end)
    extra_value = resolve_filter(extra)
    if extra_value:
        builder.raw(extra_value)
    return builder
