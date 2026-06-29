#!/usr/bin/env python
"""Search the STAC catalogue and download an item asset.

export CDSE_USERNAME=you@example.com
export CDSE_PASSWORD=...
python examples/stac_search_download.py
"""

from __future__ import annotations

import os

from cdse import Client, PasswordAuth


def main() -> None:
    auth = PasswordAuth(os.environ["CDSE_USERNAME"], os.environ["CDSE_PASSWORD"])
    with Client(auth) as client:
        items = list(
            client.stac.search(
                collections=["sentinel-2-l2a"],
                bbox=[4.0, 50.0, 5.0, 51.0],
                datetime="2024-05-01/2024-05-08",
                filter={"op": "<=", "args": [{"property": "eo:cloud_cover"}, 20]},
                filter_lang="cql2-json",
            )
        )
        print(f"Found {len(items)} items:")
        for item in items[:10]:
            print(f"  {item.id}  {item.datetime}  cloud={item.cloud_cover}")

        if items:
            item = items[0]
            print(f"Assets on {item.id}: {sorted(item.assets)}")
            # Download the small thumbnail preview as a demonstration.
            if "thumbnail" in item.assets:
                client.stac.download_asset(item, "thumbnail", f"{item.id}.jpg")
                print(f"Saved thumbnail to {item.id}.jpg")


if __name__ == "__main__":
    main()
