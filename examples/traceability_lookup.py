#!/usr/bin/env python
"""Look up a product's traceability record (public, no login required).

    python examples/traceability_lookup.py S2A_MSIL1C_..._.SAFE.zip

With an authenticated client you can also use ``client.traceability.get_by_name``.
"""

from __future__ import annotations

import sys

import httpx

from cdse.config import Settings
from cdse.traceability import TraceabilityResource


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: traceability_lookup.py <product-name>")
    product_name = sys.argv[1]

    # The traceability service is public, so a bare HTTP client is enough.
    http = httpx.Client()
    try:
        trace = TraceabilityResource(http, Settings().trace_url).get_by_name(
            product_name
        )
    finally:
        http.close()
    print(f"product:   {trace.product_name}")
    print(f"hash:      {trace.hash} ({trace.hash_algorithm})")
    print(f"timestamp: {trace.timestamp}")


if __name__ == "__main__":
    main()
