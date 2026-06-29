"""Token storage.

The :class:`TokenSet` holds the live credentials, and :class:`TokenStore`
defines how they are persisted. The library defaults to an in memory store so
that importing and using the client never touches the filesystem. The command
line layer provides a file backed store so that a login survives across
separate process invocations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel


def _now() -> datetime:
    return datetime.now(UTC)


class TokenSet(BaseModel):
    """A set of OAuth tokens together with their absolute expiry times."""

    access_token: str
    access_expiry: datetime
    refresh_token: str | None = None
    refresh_expiry: datetime | None = None
    token_type: str = "Bearer"

    def access_valid(self, skew: float = 0.0) -> bool:
        """Return whether the access token is still usable.

        Args:
            skew: Treat the token as expired this many seconds early.
        """
        return _now() < self.access_expiry - timedelta(seconds=skew)

    def refresh_valid(self, skew: float = 0.0) -> bool:
        """Return whether a refresh token grant can still succeed."""
        if self.refresh_token is None or self.refresh_expiry is None:
            return False
        return _now() < self.refresh_expiry - timedelta(seconds=skew)

    @property
    def authorization_header(self) -> str:
        """The value to send in the ``Authorization`` request header."""
        return f"{self.token_type} {self.access_token}"


class TokenStore(ABC):
    """Abstract storage for a :class:`TokenSet`."""

    @abstractmethod
    def load(self) -> TokenSet | None:
        """Return the stored tokens, or ``None`` when nothing is stored."""

    @abstractmethod
    def save(self, tokens: TokenSet) -> None:
        """Persist the given tokens, replacing anything stored before."""

    @abstractmethod
    def clear(self) -> None:
        """Remove any stored tokens."""


class MemoryTokenStore(TokenStore):
    """Keep tokens in memory for the lifetime of the process."""

    def __init__(self) -> None:
        self._tokens: TokenSet | None = None

    def load(self) -> TokenSet | None:
        return self._tokens

    def save(self, tokens: TokenSet) -> None:
        self._tokens = tokens

    def clear(self) -> None:
        self._tokens = None
