#!/usr/bin/env python
"""Minimal quickstart: authenticate and count catalogue products.

export CDSE_USERNAME=you@example.com
export CDSE_PASSWORD=...
python examples/quickstart.py
"""

from __future__ import annotations

import os

from cdse import Client, FilterBuilder, PasswordAuth


def main() -> None:
    auth = PasswordAuth(os.environ["CDSE_USERNAME"], os.environ["CDSE_PASSWORD"])
    with Client(auth) as client:
        total = client.odata.products.count()
        print(f"Catalogue holds {total} products in total.")

        recent = FilterBuilder().collection("SENTINEL-2")
        first = next(iter(client.odata.products.search(recent, top=1)), None)
        if first is not None:
            print(f"A Sentinel-2 product: {first.id} {first.name}")


if __name__ == "__main__":
    main()
