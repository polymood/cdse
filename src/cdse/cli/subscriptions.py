"""Subscription management commands."""

from __future__ import annotations

import json
from typing import Annotated, cast

import typer

from cdse.cli._common import authenticated_client
from cdse.subscriptions import (
    Notification,
    Subscription,
    SubscriptionEvent,
    SubscriptionStatus,
    SubscriptionType,
)

app = typer.Typer(help="Create and manage product subscriptions.")


@app.command(name="list")
def list_subscriptions(
    as_json: Annotated[
        bool, typer.Option("--json", help="Print results as JSON.")
    ] = False,
) -> None:
    """List your subscriptions."""
    with authenticated_client() as client:
        subscriptions = client.subscriptions.list()
    if as_json:
        typer.echo(
            json.dumps([s.model_dump(mode="json") for s in subscriptions], indent=2)
        )
        return
    if not subscriptions:
        typer.echo("No subscriptions.")
        return
    for subscription in subscriptions:
        _print_subscription(subscription)


@app.command()
def create(
    filter_param: Annotated[
        str | None, typer.Option("--filter", help="OData filter for the subscription.")
    ] = None,
    subscription_type: Annotated[
        str, typer.Option("--type", help="Delivery mode: pull or push.")
    ] = "pull",
    event: Annotated[
        list[str] | None,
        typer.Option("--event", help="Event to react to (repeatable)."),
    ] = None,
    endpoint: Annotated[
        str | None, typer.Option(help="Notification endpoint for push subscriptions.")
    ] = None,
) -> None:
    """Create a subscription."""
    events = event or ["created"]
    with authenticated_client() as client:
        subscription = client.subscriptions.create(
            filter_param,
            subscription_type=cast(SubscriptionType, subscription_type),
            events=cast("list[SubscriptionEvent]", events),
            notification_endpoint=endpoint,
        )
    typer.secho(f"Created subscription {subscription.id}.", fg=typer.colors.GREEN)


@app.command()
def read(
    subscription_id: Annotated[str, typer.Argument(help="Subscription id.")],
    top: Annotated[int, typer.Option(help="Number of notifications (max 20).")] = 10,
    acknowledge: Annotated[
        bool,
        typer.Option(help="Acknowledge the notifications after reading them."),
    ] = False,
) -> None:
    """Read pending notifications from a pull subscription."""
    with authenticated_client() as client:
        notifications = client.subscriptions.read(subscription_id, top=top)
        for notification in notifications:
            _print_notification(notification)
        if acknowledge and notifications:
            last = notifications[-1]
            if last.ack_id is not None:
                client.subscriptions.acknowledge(subscription_id, last.ack_id)
                typer.secho("Acknowledged.", fg=typer.colors.GREEN)


@app.command(name="set-status")
def set_status(
    subscription_id: Annotated[str, typer.Argument(help="Subscription id.")],
    status: Annotated[str, typer.Argument(help="running, paused, or cancelled.")],
) -> None:
    """Change a subscription's status."""
    if status not in ("running", "paused", "cancelled"):
        raise typer.BadParameter("status must be running, paused, or cancelled.")
    with authenticated_client() as client:
        subscription = client.subscriptions.set_status(
            subscription_id, cast(SubscriptionStatus, status)
        )
    typer.secho(
        f"Subscription {subscription.id} is now {subscription.status}.",
        fg=typer.colors.GREEN,
    )


@app.command()
def delete(
    subscription_id: Annotated[str, typer.Argument(help="Subscription id.")],
) -> None:
    """Delete a subscription."""
    with authenticated_client() as client:
        client.subscriptions.delete(subscription_id)
    typer.secho(f"Deleted subscription {subscription_id}.", fg=typer.colors.GREEN)


def _print_subscription(subscription: Subscription) -> None:
    typer.echo(
        f"{subscription.id}  {subscription.status or '-'}  "
        f"{subscription.subscription_type or '-'}  {subscription.filter_param or ''}"
    )


def _print_notification(notification: Notification) -> None:
    typer.echo(
        f"{notification.notification_date}  {notification.subscription_event}  "
        f"{notification.product_name}  (ack: {notification.ack_id})"
    )
