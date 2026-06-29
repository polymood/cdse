#!/usr/bin/env python
"""Long-running watcher: reuse one subscription and print new products forever.

Unlike subscription_demo.py, this reuses a single subscription across restarts
(its id is cached in a file) instead of creating a new one each time, so it is
safe to run under a process supervisor such as systemd or Docker. Transient
errors are tolerated, and the access token is refreshed automatically.

    export CDSE_USERNAME=you@example.com
    export CDSE_PASSWORD=...
    python examples/subscription_watch.py
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from cdse import Client, PasswordAuth
from cdse.exceptions import CdseError

ROI = "POLYGON((4 50, 6 50, 6 52, 4 52, 4 50))"
COLLECTION = "SENTINEL-2"
POLL_SECONDS = 60
STATE_FILE = Path.home() / ".cache" / "cdse-watch-subscription-id"


def roi_filter() -> str:
    return (
        f"Collection/Name eq '{COLLECTION}' and "
        f"OData.CSC.Intersects(area=geography'SRID=4326;{ROI}')"
    )


def ensure_subscription(client: Client) -> str:
    """Return a stored subscription id if it still exists, else create one."""
    if STATE_FILE.exists():
        stored = STATE_FILE.read_text().strip()
        try:
            client.subscriptions.get(stored)
            return stored
        except CdseError:
            pass  # vanished; recreate
    subscription = client.subscriptions.create(
        roi_filter(), subscription_type="pull", events=["created"]
    )
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(subscription.id)
    return subscription.id


def main() -> None:
    auth = PasswordAuth(os.environ["CDSE_USERNAME"], os.environ["CDSE_PASSWORD"])
    with Client(auth) as client:
        subscription_id = ensure_subscription(client)
        print(f"Watching subscription {subscription_id}. Press Ctrl+C to stop.")
        while True:
            try:
                batch = client.subscriptions.read(subscription_id, top=20)
                for notification in batch:
                    print(
                        f"[{notification.notification_date}] "
                        f"{notification.product_name}"
                    )
                if batch and batch[-1].ack_id:
                    client.subscriptions.acknowledge(subscription_id, batch[-1].ack_id)
            except CdseError as error:
                print(f"transient error, will retry: {error}")
                batch = []
            if not batch:
                time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
