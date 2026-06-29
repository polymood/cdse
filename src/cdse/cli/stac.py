"""STAC catalogue commands: search and download."""

from __future__ import annotations

import json
from itertools import islice
from pathlib import Path
from typing import Annotated

import typer

from cdse.cli._common import authenticated_client
from cdse.stac.models import Item

app = typer.Typer(help="Search and download items from the STAC catalogue.")


def _parse_bbox(value: str) -> list[float]:
    parts = [piece.strip() for piece in value.split(",")]
    if len(parts) != 4:
        raise typer.BadParameter("bbox must be 'minx,miny,maxx,maxy'.")
    try:
        return [float(piece) for piece in parts]
    except ValueError as error:
        raise typer.BadParameter("bbox values must be numbers.") from error


@app.command()
def search(
    collection: Annotated[
        list[str] | None,
        typer.Option("--collection", "-c", help="Collection id (repeatable)."),
    ] = None,
    bbox: Annotated[
        str | None, typer.Option(help="Bounding box 'minx,miny,maxx,maxy'.")
    ] = None,
    datetime_range: Annotated[
        str | None,
        typer.Option("--datetime", help="RFC 3339 instant or 'start/end' interval."),
    ] = None,
    cql_filter: Annotated[
        str | None, typer.Option("--filter", help="CQL2 text filter.")
    ] = None,
    limit: Annotated[int, typer.Option(help="Maximum number of items to return.")] = 20,
    as_json: Annotated[
        bool, typer.Option("--json", help="Print results as JSON.")
    ] = False,
) -> None:
    """Search the STAC catalogue and print the matching items."""
    box = _parse_bbox(bbox) if bbox else None
    with authenticated_client() as client:
        items = list(
            islice(
                client.stac.search(
                    collections=collection,
                    bbox=box,
                    datetime=datetime_range,
                    filter=cql_filter,
                    filter_lang="cql2-text" if cql_filter else None,
                ),
                limit,
            )
        )
    _print_items(items, as_json=as_json)


@app.command()
def download(
    collection: Annotated[str, typer.Argument(help="Collection id.")],
    item_id: Annotated[str, typer.Argument(help="Item id.")],
    asset: Annotated[str, typer.Option(help="Asset key to download.")] = "PRODUCT",
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output path. Defaults to <item>.zip."),
    ] = None,
    resume: Annotated[
        bool, typer.Option(help="Resume a partial download if one exists.")
    ] = False,
) -> None:
    """Download an asset of a STAC item."""
    destination = output if output is not None else Path(f"{item_id}.zip")
    with authenticated_client() as client:
        item = client.stac.item(collection, item_id)
        result = client.stac.download_asset(item, asset, destination, resume=resume)
    typer.secho(f"Downloaded to {result}.", fg=typer.colors.GREEN)


def _print_items(items: list[Item], *, as_json: bool) -> None:
    if as_json:
        typer.echo(
            json.dumps([item.model_dump(mode="json") for item in items], indent=2)
        )
        return
    if not items:
        typer.echo("No items found.")
        return
    for item in items:
        when = item.datetime or "-"
        typer.echo(f"{item.id}  {when}  {item.collection or '-'}")
