"""Shared helpers for the command line interface."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import platformdirs
import typer

from cdse.auth.providers import RefreshTokenAuth
from cdse.auth.store import FileTokenStore
from cdse.client import Client
from cdse.config import Settings
from cdse.exceptions import CdseError

#: Environment variable that overrides the configuration directory, mainly for
#: testing.
CONFIG_DIR_ENV = "CDSE_CONFIG_DIR"


def config_dir() -> Path:
    """Return the directory where the CLI stores its state."""
    override = os.environ.get(CONFIG_DIR_ENV)
    if override:
        return Path(override)
    return Path(platformdirs.user_config_dir("cdse"))


def credentials_path() -> Path:
    """Return the path of the stored credentials file."""
    return config_dir() / "credentials.json"


def token_store() -> FileTokenStore:
    """Return the file backed token store used by the CLI."""
    return FileTokenStore(credentials_path())


def require_login() -> Client:
    """Build a client from stored credentials or exit with guidance."""
    store = token_store()
    tokens = store.load()
    if tokens is None or tokens.refresh_token is None:
        typer.secho(
            "Not authenticated. Run 'cdse auth login' first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)
    settings = Settings()
    provider = RefreshTokenAuth(tokens.refresh_token, client_id=settings.client_id)
    return Client(provider, settings=settings, store=store)


@contextmanager
def authenticated_client() -> Iterator[Client]:
    """Yield a logged in client, mapping library errors to clean CLI failures."""
    client = require_login()
    try:
        yield client
    except CdseError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error
    finally:
        client.close()
