"""The STAC search and browse resource.

Implements catalogue access against the STAC API: free search through the
``/search`` endpoint, collection browsing, single item retrieval, and the
queryables endpoints. Searching returns a lazy iterator that follows the
``rel="next"`` paging links, re-issuing them as POST requests when the link
carries a body.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Any

from cdse.stac.models import (
    Collection,
    CollectionList,
    Item,
    ItemCollection,
    Link,
)
from cdse.transport import Transport


class StacSearch:
    """Access the STAC API search and browse endpoints."""

    def __init__(self, transport: Transport, base_url: str) -> None:
        self._transport = transport
        self._base_url = base_url.rstrip("/")

    def search(
        self,
        *,
        collections: Sequence[str] | None = None,
        ids: Sequence[str] | None = None,
        bbox: Sequence[float] | None = None,
        datetime: str | None = None,
        intersects: dict[str, Any] | None = None,
        limit: int | None = None,
        filter: dict[str, Any] | str | None = None,
        filter_lang: str | None = None,
        query: dict[str, Any] | None = None,
        sortby: list[dict[str, str]] | str | None = None,
        fields: dict[str, list[str]] | None = None,
    ) -> Iterator[Item]:
        """Search for items, following paging links lazily.

        Args:
            collections: Collection ids to restrict the search to.
            ids: Specific item ids to return.
            bbox: Bounding box as ``[minx, miny, maxx, maxy]``.
            datetime: An RFC 3339 instant or ``start/end`` interval.
            intersects: A GeoJSON geometry to intersect.
            limit: Page size.
            filter: A CQL2 filter, as JSON (dict) or text (str).
            filter_lang: The filter language, for example ``cql2-json``.
            query: A Query extension expression.
            sortby: A Sort extension expression.
            fields: A Fields extension include/exclude expression.
        """
        body = _build_search_body(
            collections=collections,
            ids=ids,
            bbox=bbox,
            datetime=datetime,
            intersects=intersects,
            limit=limit,
            filter=filter,
            filter_lang=filter_lang,
            query=query,
            sortby=sortby,
            fields=fields,
        )
        page = self.search_page(body)
        yield from self._paginate(page)

    def search_page(self, body: dict[str, Any] | None = None) -> ItemCollection:
        """Run a single POST search with the given request body."""
        response = self._transport.request(
            "POST", f"{self._base_url}/search", json=body or {}
        )
        return ItemCollection.model_validate(response.json())

    def collections(self) -> list[Collection]:
        """List all available collections."""
        response = self._transport.request("GET", f"{self._base_url}/collections")
        return CollectionList.model_validate(response.json()).collections

    def collection(self, collection_id: str) -> Collection:
        """Fetch a single collection by id."""
        response = self._transport.request(
            "GET", f"{self._base_url}/collections/{collection_id}"
        )
        return Collection.model_validate(response.json())

    def items(self, collection_id: str, *, limit: int | None = None) -> Iterator[Item]:
        """Iterate the items of a collection, following paging links."""
        params: dict[str, str] = {}
        if limit is not None:
            params["limit"] = str(limit)
        response = self._transport.request(
            "GET",
            f"{self._base_url}/collections/{collection_id}/items",
            params=params or None,
        )
        page = ItemCollection.model_validate(response.json())
        yield from self._paginate(page)

    def item(self, collection_id: str, item_id: str) -> Item:
        """Fetch a single item by collection and item id."""
        response = self._transport.request(
            "GET", f"{self._base_url}/collections/{collection_id}/items/{item_id}"
        )
        return Item.model_validate(response.json())

    def queryables(self, collection_id: str | None = None) -> dict[str, Any]:
        """Return the queryable properties, globally or for one collection."""
        if collection_id is None:
            url = f"{self._base_url}/queryables"
        else:
            url = f"{self._base_url}/collections/{collection_id}/queryables"
        response = self._transport.request("GET", url)
        result: dict[str, Any] = response.json()
        return result

    def _paginate(self, page: ItemCollection) -> Iterator[Item]:
        """Yield items across pages by following the ``next`` link."""
        while True:
            yield from page.features
            next_link = _next_link(page.links)
            if next_link is None:
                return
            if next_link.body is not None:
                response = self._transport.request(
                    "POST", next_link.href, json=next_link.body
                )
            else:
                response = self._transport.request("GET", next_link.href)
            page = ItemCollection.model_validate(response.json())


def _next_link(links: Sequence[Link]) -> Link | None:
    """Return the ``rel="next"`` link, if any."""
    for link in links:
        if link.rel == "next":
            return link
    return None


def _build_search_body(
    *,
    collections: Sequence[str] | None,
    ids: Sequence[str] | None,
    bbox: Sequence[float] | None,
    datetime: str | None,
    intersects: dict[str, Any] | None,
    limit: int | None,
    filter: dict[str, Any] | str | None,
    filter_lang: str | None,
    query: dict[str, Any] | None,
    sortby: list[dict[str, str]] | str | None,
    fields: dict[str, list[str]] | None,
) -> dict[str, Any]:
    """Assemble a STAC search request body, omitting unset parameters."""
    body: dict[str, Any] = {}
    if collections is not None:
        body["collections"] = list(collections)
    if ids is not None:
        body["ids"] = list(ids)
    if bbox is not None:
        body["bbox"] = list(bbox)
    if datetime is not None:
        body["datetime"] = datetime
    if intersects is not None:
        body["intersects"] = intersects
    if limit is not None:
        body["limit"] = limit
    if filter is not None:
        body["filter"] = filter
        if filter_lang is not None:
            body["filter-lang"] = filter_lang
    if query is not None:
        body["query"] = query
    if sortby is not None:
        body["sortby"] = sortby
    if fields is not None:
        body["fields"] = fields
    return body
