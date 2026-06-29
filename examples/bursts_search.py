#!/usr/bin/env python
"""Search Sentinel-1 SLC bursts and show their parent products.

export CDSE_USERNAME=you@example.com
export CDSE_PASSWORD=...
python examples/bursts_search.py
"""

from __future__ import annotations

import os

from cdse import Client, PasswordAuth


def main() -> None:
    auth = PasswordAuth(os.environ["CDSE_USERNAME"], os.environ["CDSE_PASSWORD"])
    with Client(auth) as client:
        bursts = list(
            client.odata.bursts.search(
                swath="IW1",
                polarisation="VH",
                intersects="POLYGON((12 41, 13 41, 13 42, 12 42, 12 41))",
            )
        )
        print(f"Found {len(bursts)} bursts:")
        for burst in bursts[:10]:
            print(
                f"  burst {burst.burst_id} {burst.swath_identifier} "
                f"{burst.polarisation_channels}  parent={burst.parent_product_name}"
            )
        # A single burst has no download endpoint; fetch its parent product:
        # client.odata.products.download(bursts[0].parent_product_id, "parent.zip")


if __name__ == "__main__":
    main()
