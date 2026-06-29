"""OData catalogue commands: search and download."""

from __future__ import annotations

import json
from datetime import datetime
from itertools import islice
from pathlib import Path
from typing import Annotated

import typer

from cdse.cli._common import authenticated_client
from cdse.odata.models import Product
from cdse.odata.query import FilterBuilder

app = typer.Typer(help="Search and download products from the OData catalogue.")


@app.command()
def search(
    collection: Annotated[str | None, typer.Option(help="Collection name.")] = None,
    name_contains: Annotated[
        str | None, typer.Option("--name-contains", help="Substring of the name.")
    ] = None,
    start: Annotated[
        datetime | None, typer.Option(help="Start of the sensing date range.")
    ] = None,
    end: Annotated[
        datetime | None, typer.Option(help="End of the sensing date range.")
    ] = None,
    cloud_cover_max: Annotated[
        float | None,
        typer.Option("--cloud-cover-max", help="Maximum cloud cover percentage."),
    ] = None,
    intersects: Annotated[
        str | None, typer.Option(help="WKT geometry to intersect.")
    ] = None,
    raw_filter: Annotated[
        str | None,
        typer.Option("--filter", help="Raw OData $filter, overriding other options."),
    ] = None,
    order_by: Annotated[
        str | None,
        typer.Option("--order-by", help="Order clause, e.g. 'ContentDate/Start desc'."),
    ] = None,
    limit: Annotated[
        int, typer.Option(help="Maximum number of results to return.")
    ] = 20,
    as_json: Annotated[
        bool, typer.Option("--json", help="Print results as JSON.")
    ] = False,
) -> None:
    """Search the catalogue and print the matching products."""
    builder = FilterBuilder()
    if collection:
        builder.collection(collection)
    if name_contains:
        builder.name_contains(name_contains)
    if start is not None and end is not None:
        builder.acquired_between(start, end)
    if cloud_cover_max is not None:
        builder.attribute("cloudCover", "le", cloud_cover_max)
    if intersects:
        builder.intersects(intersects)
    query: str | FilterBuilder = raw_filter if raw_filter else builder

    with authenticated_client() as client:
        products = list(
            islice(client.odata.products.search(query, order_by=order_by), limit)
        )
    _print_products(products, as_json=as_json)


@app.command()
def download(
    product_id: Annotated[str, typer.Argument(help="Product UUID.")],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output path. Defaults to <id>.zip."),
    ] = None,
    resume: Annotated[
        bool, typer.Option(help="Resume a partial download if one exists.")
    ] = False,
) -> None:
    """Download a product to disk by its UUID."""
    destination = output if output is not None else Path(f"{product_id}.zip")
    with authenticated_client() as client:
        result = client.odata.products.download(product_id, destination, resume=resume)
    typer.secho(f"Downloaded to {result}.", fg=typer.colors.GREEN)


def _print_products(products: list[Product], *, as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps([p.model_dump(mode="json") for p in products], indent=2))
        return
    if not products:
        typer.echo("No products found.")
        return
    for product in products:
        sensed = product.content_date.start.isoformat() if product.content_date else "-"
        typer.echo(f"{product.id}  {sensed}  {product.name}")
