"""The STAC API namespace.

Exposes search and browse together with asset download as a single object,
reached as ``client.stac``.
"""

from __future__ import annotations

from pathlib import Path

from cdse.stac.download import download_asset, download_href
from cdse.stac.models import Item
from cdse.stac.search import StacSearch
from cdse.transfer import DEFAULT_CHUNK_SIZE


class Stac(StacSearch):
    """Entry point for the STAC catalogue: search, browse, and download."""

    def download_asset(
        self,
        item: Item,
        asset_key: str,
        destination: str | Path,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        resume: bool = False,
    ) -> Path:
        """Download a named asset of an item to ``destination``."""
        return download_asset(
            self._transport,
            item,
            asset_key,
            destination,
            chunk_size=chunk_size,
            resume=resume,
        )

    def download_href(
        self,
        href: str,
        destination: str | Path,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        resume: bool = False,
    ) -> Path:
        """Download an asset by its href directly."""
        return download_href(
            self._transport,
            href,
            destination,
            chunk_size=chunk_size,
            resume=resume,
        )
