"""Direct S3 access to the product archive.

Products are also available from the ``eodata`` S3 bucket, which is the most
efficient way to download large volumes or individual files from inside a
product. S3 access uses credentials generated separately from the account
password through the S3 keys manager portal:
https://eodata-s3keysmanager.dataspace.copernicus.eu/

This module depends on :mod:`boto3`, which is installed with the optional
``s3`` extra (``pip install 'cdse[s3]'``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cdse.config import DEFAULT_S3_BUCKET, DEFAULT_S3_ENDPOINT_URL
from cdse.exceptions import CdseConfigError


class S3Client:
    """Download products and files from the CDSE S3 archive.

    Args:
        access_key: S3 access key from the keys manager portal.
        secret_key: S3 secret key from the keys manager portal.
        endpoint_url: S3 endpoint, defaulting to the public one.
        region: S3 region name, ``default`` for CDSE.
        bucket: Bucket name, ``eodata`` for CDSE.
        client: A preconfigured boto3 S3 client, mainly for testing. When given,
            the credentials are not required and boto3 is not imported here.
    """

    def __init__(
        self,
        access_key: str | None = None,
        secret_key: str | None = None,
        *,
        endpoint_url: str = DEFAULT_S3_ENDPOINT_URL,
        region: str = "default",
        bucket: str = DEFAULT_S3_BUCKET,
        client: Any | None = None,
    ) -> None:
        self._bucket = bucket
        if client is not None:
            self._client = client
            return
        if not access_key or not secret_key:
            raise CdseConfigError(
                "S3 access requires an access key and a secret key. Generate "
                "them at https://eodata-s3keysmanager.dataspace.copernicus.eu/ "
                "and pass them in or set CDSE_S3_ACCESS_KEY and "
                "CDSE_S3_SECRET_KEY."
            )
        try:
            import boto3
        except ImportError as error:
            raise CdseConfigError(
                "S3 support requires the 's3' extra. Install it with "
                "pip install 'cdse[s3]'."
            ) from error
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    def object_key(self, path: str) -> str:
        """Normalise an S3 path to a bucket relative key.

        Accepts an ``s3://eodata/...`` URI, an OData ``S3Path`` such as
        ``/eodata/Sentinel-2/...``, or an already relative key.
        """
        value = path
        if value.startswith("s3://"):
            value = value[len("s3://") :]
        value = value.lstrip("/")
        prefix = f"{self._bucket}/"
        if value.startswith(prefix):
            value = value[len(prefix) :]
        return value

    def list_objects(self, prefix: str) -> list[str]:
        """List every object key under a prefix."""
        keys: list[str] = []
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            for entry in page.get("Contents", []):
                keys.append(entry["Key"])
        return keys

    def download_file(self, key: str, destination: str | Path) -> Path:
        """Download a single object to ``destination``."""
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._client.download_file(self._bucket, key, str(target))
        return target

    def download(self, path: str, destination: str | Path) -> Path:
        """Download a product or file from its S3 path.

        A product is stored as a prefix containing many objects, so every object
        under the prefix is downloaded into ``destination`` while preserving the
        directory structure below the product folder. Returns the local path
        that was written to.
        """
        key = self.object_key(path)
        objects = self.list_objects(key)
        if not objects:
            raise FileNotFoundError(f"No S3 objects found under {key!r}.")

        destination = Path(destination)
        # The product folder name is the last non empty segment of the prefix.
        base_prefix = key.rstrip("/")
        parent_prefix = (
            base_prefix.rsplit("/", 1)[0] + "/" if "/" in base_prefix else ""
        )
        for object_key in objects:
            relative = (
                object_key[len(parent_prefix) :]
                if parent_prefix and object_key.startswith(parent_prefix)
                else object_key
            )
            self.download_file(object_key, destination / relative)
        return destination

    @classmethod
    def from_settings(cls, settings: Any) -> S3Client:
        """Build a client from a :class:`cdse.config.Settings` instance."""
        return cls(
            settings.s3_access_key,
            settings.s3_secret_key,
            endpoint_url=settings.s3_endpoint_url,
            region=settings.s3_region,
            bucket=settings.s3_bucket,
        )
