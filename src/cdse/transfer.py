"""Generic streaming download helper shared by the API modules.

Downloads can be very large, so the body is streamed to disk in chunks rather
than held in memory. Partial downloads can be resumed with an HTTP range
request, which matters because of the monthly transfer quota: restarting a large
download from scratch wastes the allowance.

The download endpoints often redirect to a separate download host, so redirects
are followed for the streaming request.
"""

from __future__ import annotations

from pathlib import Path

import httpx

from cdse.transport import Transport

#: Default streaming chunk size in bytes (one mebibyte).
DEFAULT_CHUNK_SIZE = 1024 * 1024


def download_to_file(
    transport: Transport,
    url: str,
    destination: Path,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    resume: bool = False,
) -> Path:
    """Stream the body at ``url`` to ``destination`` and return the path.

    Args:
        transport: The transport used to send the authenticated request.
        url: The URL to download.
        destination: Where to write the file.
        chunk_size: Number of bytes to read at a time.
        resume: When true and a partial file already exists, request only the
            remaining bytes with a range header and append to it. If the server
            ignores the range and returns the whole file, it is written afresh.
    """
    destination = Path(destination)
    existing = destination.stat().st_size if resume and destination.exists() else 0

    headers = {"Range": f"bytes={existing}-"} if existing else {}
    with transport.stream(
        "GET", url, headers=headers, follow_redirects=True
    ) as response:
        append = existing > 0 and response.status_code == httpx.codes.PARTIAL_CONTENT
        with destination.open("ab" if append else "wb") as handle:
            for chunk in response.iter_bytes(chunk_size):
                handle.write(chunk)
    return destination
