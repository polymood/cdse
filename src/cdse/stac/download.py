"""STAC asset download helpers.

STAC items expose their data through assets. An asset's ``href`` may be an HTTP
URL served by the data space, which is downloaded here with the same bearer
token used everywhere else, or an ``s3://`` path, which requires separate S3
credentials and is therefore out of scope for this client.

Whether the HTTP asset href accepts the standard bearer token is assumed by
analogy with the OData download endpoint and should be confirmed against the
live API.
"""

from __future__ import annotations

from pathlib import Path

from cdse.exceptions import CdseError
from cdse.stac.models import Item
from cdse.transfer import DEFAULT_CHUNK_SIZE, download_to_file
from cdse.transport import Transport


def download_asset(
    transport: Transport,
    item: Item,
    asset_key: str,
    destination: str | Path,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    resume: bool = False,
) -> Path:
    """Download a named asset of ``item`` to ``destination``."""
    asset = item.assets.get(asset_key)
    if asset is None:
        available = ", ".join(sorted(item.assets)) or "none"
        raise CdseError(
            f"Item {item.id!r} has no asset {asset_key!r}. Available assets: "
            f"{available}."
        )
    return download_href(
        transport, asset.href, destination, chunk_size=chunk_size, resume=resume
    )


def download_href(
    transport: Transport,
    href: str,
    destination: str | Path,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    resume: bool = False,
) -> Path:
    """Download an asset href, rejecting S3 paths that need other credentials."""
    if href.startswith("s3://"):
        raise CdseError(
            "This asset is stored on S3 (href starts with 's3://'). Direct S3 "
            "download requires separate S3 credentials and is outside this "
            "client's scope. Use the HTTP asset href if the item provides one."
        )
    return download_to_file(
        transport, href, Path(destination), chunk_size=chunk_size, resume=resume
    )
