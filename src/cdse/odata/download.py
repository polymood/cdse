"""OData specific download helpers.

The generic streaming logic lives in :mod:`cdse.transfer`; this module adds the
OData node listing parser and re-exports the shared helper for convenience.
"""

from __future__ import annotations

from typing import Any

from cdse.odata.models import Node
from cdse.transfer import DEFAULT_CHUNK_SIZE, download_to_file

__all__ = ["DEFAULT_CHUNK_SIZE", "download_to_file", "parse_nodes"]


def parse_nodes(payload: dict[str, Any]) -> list[Node]:
    """Parse a node listing response into :class:`Node` objects.

    The list is published under the ``result`` key, but ``value`` is accepted as
    a fallback so that a different wrapper does not break parsing.
    """
    raw = payload.get("result")
    if raw is None:
        raw = payload.get("value", [])
    return [Node.model_validate(item) for item in raw]
