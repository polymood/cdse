"""Direct S3 archive download command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from cdse.config import Settings
from cdse.exceptions import CdseError
from cdse.s3 import S3Client

app = typer.Typer(help="Download products directly from the S3 archive.")


@app.command()
def download(
    path: Annotated[
        str,
        typer.Argument(help="Product S3 path, OData S3Path, or s3:// URI to download."),
    ],
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Destination directory.")
    ] = Path(),
) -> None:
    """Download a product or file from the S3 archive.

    Uses S3 credentials from CDSE_S3_ACCESS_KEY and CDSE_S3_SECRET_KEY, which
    are generated separately from the account password.
    """
    try:
        client = S3Client.from_settings(Settings())
        result = client.download(path, output)
    except (CdseError, FileNotFoundError) as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error
    typer.secho(f"Downloaded to {result}.", fg=typer.colors.GREEN)
