"""Authentication commands: login, status, and logout."""

from __future__ import annotations

from typing import Annotated

import typer

from cdse.auth.providers import PasswordAuth
from cdse.cli._common import credentials_path, token_store
from cdse.client import Client
from cdse.config import Settings
from cdse.exceptions import AuthError

app = typer.Typer(help="Authenticate with the Copernicus Data Space Ecosystem.")


@app.command()
def login(
    username: Annotated[
        str, typer.Option(prompt=True, envvar="CDSE_USERNAME", help="Account email.")
    ],
    password: Annotated[
        str,
        typer.Option(
            prompt=True,
            hide_input=True,
            envvar="CDSE_PASSWORD",
            help="Account password.",
        ),
    ],
    totp: Annotated[
        str | None, typer.Option(help="Two factor authentication code, if enabled.")
    ] = None,
) -> None:
    """Log in with a username and password and store the session tokens."""
    settings = Settings()
    store = token_store()
    provider = PasswordAuth(username, password, totp=totp, client_id=settings.client_id)
    client = Client(provider, settings=settings, store=store)
    try:
        client.auth.authorization_header()
    except AuthError as error:
        typer.secho(f"Login failed: {error}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error
    finally:
        client.close()
    typer.secho(
        f"Logged in. Session stored at {credentials_path()}.",
        fg=typer.colors.GREEN,
    )


@app.command()
def status() -> None:
    """Show whether a stored session is still valid."""
    tokens = token_store().load()
    if tokens is None:
        typer.echo("Not authenticated.")
        raise typer.Exit(code=1)
    typer.echo(f"Access token valid: {tokens.access_valid()}")
    typer.echo(f"Access token expiry: {tokens.access_expiry.isoformat()}")
    typer.echo(f"Refresh token valid: {tokens.refresh_valid()}")
    if tokens.refresh_expiry is not None:
        typer.echo(f"Refresh token expiry: {tokens.refresh_expiry.isoformat()}")


@app.command()
def logout() -> None:
    """Remove the stored session."""
    token_store().clear()
    typer.echo("Logged out.")
