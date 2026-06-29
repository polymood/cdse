#!/usr/bin/env python
"""Search the OData catalogue and download the first matching product.

export CDSE_USERNAME=you@example.com
export CDSE_PASSWORD=...
python examples/odata_search_download.py
"""

from __future__ import annotations

import os

from cdse import Client, FilterBuilder, PasswordAuth


def main() -> None:
    auth = PasswordAuth(os.environ["CDSE_USERNAME"], os.environ["CDSE_PASSWORD"])
    query = (
        FilterBuilder()
        .collection("SENTINEL-2")
        .acquired_between("2024-05-01", "2024-05-08")
        .attribute("cloudCover", "le", 20.0)
        .intersects("POLYGON((4 50, 5 50, 5 51, 4 51, 4 50))")
    )

    with Client(auth) as client:
        products = list(client.odata.products.search(query, top=10))
        print(f"Found {len(products)} products:")
        for product in products:
            sensed = product.content_date.start if product.content_date else "?"
            print(f"  {product.id}  {sensed}  {product.name}")

        if products:
            target = f"{products[0].name}.zip"
            print(f"Downloading {products[0].name} -> {target}")
            client.odata.products.download(products[0].id, target, resume=True)
            print("Done.")


if __name__ == "__main__":
    main()
