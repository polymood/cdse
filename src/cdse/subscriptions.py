"""The Subscriptions API.

A subscription is a standing query that notifies you when products matching a
filter are created, modified, or deleted. Two delivery modes exist:

- ``pull``: notifications are queued and you poll them with :meth:`read` and
  confirm them with :meth:`acknowledge`.
- ``push``: notifications are posted to a ``notification_endpoint`` you provide.

The service enforces account limits (at most two running and ten total
subscriptions). All requests use the standard bearer token.
"""

from __future__ import annotations

import builtins
from collections.abc import Sequence
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from cdse.odata.query import FilterBuilder, resolve_filter
from cdse.transport import Transport

_CONFIG = ConfigDict(populate_by_name=True, extra="ignore")

#: Delivery mode of a subscription.
SubscriptionType = Literal["pull", "push"]

#: The lifecycle status of a subscription.
SubscriptionStatus = Literal["running", "paused", "cancelled"]

#: The product events a subscription can react to.
SubscriptionEvent = Literal["created", "modified", "deleted"]


class Subscription(BaseModel):
    """A subscription entity."""

    model_config = _CONFIG

    id: str = Field(alias="Id")
    status: str | None = Field(default=None, alias="Status")
    subscription_type: str | None = Field(default=None, alias="SubscriptionType")
    subscription_event: list[str] = Field(
        default_factory=list, alias="SubscriptionEvent"
    )
    filter_param: str | None = Field(default=None, alias="FilterParam")
    stage_order: bool | None = Field(default=None, alias="StageOrder")
    priority: int | None = Field(default=None, alias="Priority")
    notification_endpoint: str | None = Field(
        default=None, alias="NotificationEndpoint"
    )
    submission_date: datetime | None = Field(default=None, alias="SubmissionDate")
    last_notification_date: datetime | None = Field(
        default=None, alias="LastNotificationDate"
    )
    ack_messages_num: int | None = Field(default=None, alias="AckMessagesNum")
    current_queue_length: int | None = Field(default=None, alias="CurrentQueueLength")
    max_queue_length: int | None = Field(default=None, alias="MaxQueueLength")


class Notification(BaseModel):
    """A single notification delivered to a pull subscription queue."""

    model_config = _CONFIG

    subscription_event: str | None = Field(default=None, alias="SubscriptionEvent")
    product_id: str | None = Field(default=None, alias="ProductId")
    product_name: str | None = Field(default=None, alias="ProductName")
    subscription_id: str | None = Field(default=None, alias="SubscriptionId")
    notification_date: datetime | None = Field(default=None, alias="NotificationDate")
    ack_id: str | None = Field(default=None, alias="AckId")
    value: dict[str, Any] | None = None


class SubscriptionsResource:
    """Create, manage, and poll subscriptions."""

    def __init__(self, transport: Transport, base_url: str) -> None:
        self._transport = transport
        self._url = f"{base_url.rstrip('/')}/Subscriptions"

    def create(
        self,
        filter_param: str | FilterBuilder | None = None,
        *,
        subscription_type: SubscriptionType = "pull",
        events: Sequence[SubscriptionEvent] = ("created",),
        status: SubscriptionStatus = "running",
        stage_order: bool = True,
        priority: int = 1,
        notification_endpoint: str | None = None,
        notification_epsg: int | None = None,
    ) -> Subscription:
        """Create a subscription and return it.

        For a push subscription, ``notification_endpoint`` is required.
        """
        if subscription_type == "push" and not notification_endpoint:
            raise ValueError("A push subscription requires a notification_endpoint.")
        body: dict[str, Any] = {
            "SubscriptionType": subscription_type,
            "SubscriptionEvent": list(events),
            "Status": status,
            "StageOrder": stage_order,
            "Priority": priority,
        }
        resolved = resolve_filter(filter_param)
        if resolved:
            body["FilterParam"] = resolved
        if notification_endpoint:
            body["NotificationEndpoint"] = notification_endpoint
        if notification_epsg is not None:
            body["NotificationEpsg"] = notification_epsg

        response = self._transport.request("POST", self._url, json=body)
        return Subscription.model_validate(response.json())

    def list(self) -> builtins.list[Subscription]:
        """List the caller's subscriptions."""
        response = self._transport.request("GET", self._url)
        payload = response.json()
        items = payload.get("value", []) if isinstance(payload, dict) else payload
        return [Subscription.model_validate(item) for item in items]

    def get(self, subscription_id: str) -> Subscription:
        """Fetch a single subscription by id."""
        response = self._transport.request("GET", f"{self._url}({subscription_id})")
        return Subscription.model_validate(response.json())

    def read(
        self, subscription_id: str, *, top: int = 1
    ) -> builtins.list[Notification]:
        """Read pending notifications from a pull subscription's queue.

        The server returns at most twenty notifications per call.
        """
        response = self._transport.request(
            "GET", f"{self._url}({subscription_id})/Read", params={"$top": str(top)}
        )
        return [Notification.model_validate(item) for item in response.json()]

    def acknowledge(self, subscription_id: str, ack_id: str) -> None:
        """Acknowledge a notification and all preceding ones in the queue.

        The documentation does not publish the exact acknowledgement endpoint,
        so the CSC standard ``Ack`` action is used; confirm against the live API.
        """
        self._transport.request(
            "POST",
            f"{self._url}({subscription_id})/Ack",
            params={"$ackid": ack_id},
        )

    def set_status(
        self, subscription_id: str, status: SubscriptionStatus
    ) -> Subscription:
        """Change a subscription's status (running, paused, or cancelled)."""
        response = self._transport.request(
            "PATCH", f"{self._url}({subscription_id})", json={"Status": status}
        )
        if response.content:
            return Subscription.model_validate(response.json())
        return self.get(subscription_id)

    def delete(self, subscription_id: str) -> None:
        """Delete a subscription."""
        self._transport.request("DELETE", f"{self._url}({subscription_id})")
