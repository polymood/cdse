#!/usr/bin/env python
"""Subscribe over a random ROI and print new Sentinel-2 products as they arrive.

A pull subscription notifies you about products created *after* the subscription
is made, so this prints nothing until the next acquisition over the chosen area
is published (which can take from minutes to a day or two depending on the
region's revisit). Press Ctrl+C to stop; the subscription is deleted on exit.

Run it with your Copernicus Data Space Ecosystem credentials:

    export CDSE_USERNAME=you@example.com
    export CDSE_PASSWORD=...
    python examples/subscription_demo.py
"""

from __future__ import annotations

import os
import random
import time

from cdse import Client, PasswordAuth
from cdse.exceptions import CdseError

# A few land regions to choose from, as (name, centre lon, centre lat).
REGIONS: list[tuple[str, float, float]] = [
    ("Benelux", 4.5, 51.0),
    ("Italian Alps", 11.0, 46.3),
    ("Andalusia", -4.5, 37.2),
    ("Nile Delta", 31.0, 30.8),
    ("California Central Valley", -120.5, 36.8),
    ("Java", 110.0, -7.3),
]

COLLECTION = "SENTINEL-2"
POLL_SECONDS = 60


def random_roi() -> tuple[str, str]:
    """Return a region name and a small WKT box around a random region."""
    name, lon, lat = random.choice(REGIONS)
    d = 0.5  # half-width in degrees, roughly a 100 km box
    polygon = (
        f"POLYGON(({lon - d} {lat - d},{lon + d} {lat - d},"
        f"{lon + d} {lat + d},{lon - d} {lat + d},{lon - d} {lat - d}))"
    )
    return name, polygon


def roi_filter(polygon: str) -> str:
    return (
        f"Collection/Name eq '{COLLECTION}' and "
        f"OData.CSC.Intersects(area=geography'SRID=4326;{polygon}')"
    )


def main() -> None:
    username = os.environ.get("CDSE_USERNAME")
    password = os.environ.get("CDSE_PASSWORD")
    if not username or not password:
        raise SystemExit("Set CDSE_USERNAME and CDSE_PASSWORD in the environment.")

    name, polygon = random_roi()
    print(f"Watching for new {COLLECTION} products over: {name}")

    with Client(PasswordAuth(username, password)) as client:
        subscription = client.subscriptions.create(
            roi_filter(polygon), subscription_type="pull", events=["created"]
        )
        print(f"Created subscription {subscription.id}. Press Ctrl+C to stop.\n")
        try:
            while True:
                try:
                    batch = client.subscriptions.read(subscription.id, top=20)
                    for notification in batch:
                        print(
                            f"[{notification.notification_date}] new product: "
                            f"{notification.product_name}"
                        )
                    if batch and batch[-1].ack_id:
                        client.subscriptions.acknowledge(
                            subscription.id, batch[-1].ack_id
                        )
                except CdseError as error:
                    # Tolerate transient failures so the watcher runs forever.
                    print(f"transient error, will retry: {error}")
                    batch = []
                if not batch:
                    time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            print("\nStopping.")
        finally:
            try:
                client.subscriptions.delete(subscription.id)
                print(f"Deleted subscription {subscription.id}.")
            except CdseError as error:
                print(f"Could not delete subscription: {error}")


if __name__ == "__main__":
    main()
