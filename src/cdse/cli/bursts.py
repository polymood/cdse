"""Sentinel-1 SLC burst search command."""

from __future__ import annotations

import json
from datetime import datetime
from itertools import islice
from typing import Annotated

import typer

from cdse.cli._common import authenticated_client
from cdse.odata.models import Burst

app = typer.Typer(help="Search Sentinel-1 SLC bursts.")


@app.command()
def search(
    parent_product_id: Annotated[
        str | None, typer.Option("--parent-product-id", help="Parent product UUID.")
    ] = None,
    burst_id: Annotated[int | None, typer.Option(help="Burst id.")] = None,
    swath: Annotated[
        str | None, typer.Option(help="Swath identifier, e.g. IW1.")
    ] = None,
    polarisation: Annotated[
        str | None, typer.Option(help="Polarisation channel, e.g. VH.")
    ] = None,
    intersects: Annotated[
        str | None, typer.Option(help="WKT geometry to intersect.")
    ] = None,
    start: Annotated[datetime | None, typer.Option(help="Start of date range.")] = None,
    end: Annotated[datetime | None, typer.Option(help="End of date range.")] = None,
    limit: Annotated[int, typer.Option(help="Maximum number of results.")] = 20,
    as_json: Annotated[
        bool, typer.Option("--json", help="Print results as JSON.")
    ] = False,
) -> None:
    """Search the Bursts collection and print the matching bursts."""
    with authenticated_client() as client:
        bursts = list(
            islice(
                client.odata.bursts.search(
                    parent_product_id=parent_product_id,
                    burst_id=burst_id,
                    swath=swath,
                    polarisation=polarisation,
                    intersects=intersects,
                    start=start,
                    end=end,
                ),
                limit,
            )
        )
    _print_bursts(bursts, as_json=as_json)


def _print_bursts(bursts: list[Burst], *, as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps([b.model_dump(mode="json") for b in bursts], indent=2))
        return
    if not bursts:
        typer.echo("No bursts found.")
        return
    for burst in bursts:
        when = burst.content_date.start.isoformat() if burst.content_date else "-"
        typer.echo(
            f"{burst.id}  {when}  {burst.swath_identifier or '-'}  "
            f"{burst.polarisation_channels or '-'}  {burst.name}"
        )
