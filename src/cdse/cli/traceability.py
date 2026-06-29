"""Traceability lookup command."""

from __future__ import annotations

import json
from typing import Annotated

import httpx
import typer

from cdse.config import Settings
from cdse.exceptions import CdseError
from cdse.traceability import TraceabilityResource

app = typer.Typer(help="Look up product traceability records.")


@app.command()
def get(
    product_name: Annotated[
        str, typer.Argument(help="Full product name, including the extension.")
    ],
) -> None:
    """Fetch and print the traceability record for a product.

    This is a public service, so no login is required.
    """
    settings = Settings()
    http = httpx.Client()
    try:
        trace = TraceabilityResource(http, settings.trace_url).get_by_name(product_name)
    except CdseError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error
    finally:
        http.close()
    typer.echo(json.dumps(trace.model_dump(mode="json", by_alias=True), indent=2))
