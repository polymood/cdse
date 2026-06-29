"""Exception hierarchy for the CDSE client.

Callers should be able to react to failures by catching meaningful types rather
than inspecting raw HTTP status codes. Every exception raised by the library
derives from :class:`CdseError`.
"""

from __future__ import annotations


class CdseError(Exception):
    """Base class for every error raised by the library."""


class CdseConfigError(CdseError):
    """The client was configured incorrectly, for example missing credentials."""


class AuthError(CdseError):
    """Authentication or token handling failed."""


class TokenRefreshError(AuthError):
    """An access token could not be refreshed."""


class ReauthRequiredError(AuthError):
    """The session expired and cannot be renewed without new credentials.

    This is raised when the refresh token is no longer valid and the configured
    auth provider does not hold the credentials needed to authenticate again,
    which is the case when the client was created from an existing refresh token.
    """


class TransportError(CdseError):
    """A network level failure occurred and could not be recovered by retrying."""


class CdseHTTPError(CdseError):
    """The server returned an unsuccessful HTTP response.

    Attributes:
        status_code: The HTTP status code of the response.
        url: The URL that was requested.
        body: The response body, truncated for readability.
    """

    def __init__(
        self, message: str, *, status_code: int, url: str, body: str = ""
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.url = url
        self.body = body


class RateLimitError(CdseHTTPError):
    """The request was rejected because a rate limit was exceeded.

    Attributes:
        retry_after: Seconds to wait before retrying, when the server provides
            a ``Retry-After`` header.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        url: str,
        body: str = "",
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, url=url, body=body)
        self.retry_after = retry_after


class QuotaExceededError(CdseHTTPError):
    """An account quota, such as the monthly transfer limit, was exceeded."""


class NotFoundError(CdseHTTPError):
    """The requested resource does not exist."""


class ServerError(CdseHTTPError):
    """The server reported an internal error."""
