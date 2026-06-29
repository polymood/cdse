#!/usr/bin/env python
"""Find a product with OData, then download it directly from S3.

Needs S3 credentials from https://eodata-s3keysmanager.dataspace.copernicus.eu/

    export CDSE_USERNAME=you@example.com
    export CDSE_PASSWORD=...
    export CDSE_S3_ACCESS_KEY=...
    export CDSE_S3_SECRET_KEY=...
    python examples/s3_download.py
"""

from __future__ import annotations

import os

from cdse import Client, FilterBuilder, PasswordAuth


def main() -> None:
    auth = PasswordAuth(os.environ["CDSE_USERNAME"], os.environ["CDSE_PASSWORD"])
    query = FilterBuilder().collection("SENTINEL-2").attribute("cloudCover", "le", 10.0)

    with Client(auth) as client:
        product = next(iter(client.odata.products.search(query, top=1)), None)
        if product is None or not product.s3_path:
            print("No product with an S3 path found.")
            return
        print(f"Downloading {product.name} from {product.s3_path}")
        # client.s3 reads CDSE_S3_ACCESS_KEY / CDSE_S3_SECRET_KEY from settings.
        client.s3.download(product.s3_path, "downloads/")
        print("Done. Files written under downloads/")


if __name__ == "__main__":
    main()
