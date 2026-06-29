"""Top level Typer application for the ``cdse`` command."""

from __future__ import annotations

import typer

from cdse.cli.auth import app as auth_app
from cdse.cli.odata import app as odata_app
from cdse.cli.stac import app as stac_app

app = typer.Typer(
    help="Command line client for the Copernicus Data Space Ecosystem.",
    no_args_is_help=True,
)
app.add_typer(auth_app, name="auth")
app.add_typer(odata_app, name="odata")
app.add_typer(stac_app, name="stac")


def main() -> None:
    """Console script entry point."""
    app()
