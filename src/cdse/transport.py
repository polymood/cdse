"""HTTP transport layer.

This is the only layer that talks to the network for resource requests. It owns
the cross cutting concerns that every API shares: attaching the bearer token,
refreshing it after an unexpected ``401``, retrying transient failures with
backoff, honouring rate limit responses, throttling proactively, and mapping
unsuccessful responses to the library exception hierarchy.

Keeping all input and output here is what allows an asynchronous transport to be
added later without changing any of the layers above it.
"""

from __future__ import annotations

import random
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import httpx

from cdse.auth.manager import TokenManager
from cdse.config import Settings
from cdse.exceptions import (
    CdseHTTPError,
    NotFoundError,
    QuotaExceededError,
    RateLimitError,
    ServerError,
    TransportError,
)
from cdse.ratelimit import RateLimiter

#: Status codes that are safe to retry after a delay.
_RETRY_STATUS = frozenset({httpx.codes.TOO_MANY_REQUESTS, 502, 503, 504})


class Transport:
    """Send authenticated HTTP requests with retries and error mapping."""

    def __init__(
        self,
        http: httpx.Client,
        tokens: TokenManager,
        *,
        settings: Settings,
    ) -> None:
        self._http = http
        self._tokens = tokens
        self._settings = settings
        self._rate_limiter = RateLimiter(settings.requests_per_minute)
        self._download_semaphore = threading.Semaphore(
            settings.max_concurrent_downloads
        )

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Send a request, retrying transient failures, and return the response.

        Raises:
            CdseHTTPError: For unsuccessful responses, using the most specific
                subclass that applies.
            TransportError: When the network repeatedly fails.
        """
        base_headers = dict(headers or {})
        attempt = 0
        refreshed_after_401 = False

        while True:
            self._rate_limiter.acquire()
            request_headers = {
                **base_headers,
                "Authorization": self._tokens.authorization_header(),
            }
            try:
                response = self._http.request(
                    method,
                    url,
                    headers=request_headers,
                    timeout=self._settings.request_timeout,
                    **kwargs,
                )
            except httpx.TransportError as exc:
                attempt += 1
                if attempt > self._settings.max_retries:
                    raise TransportError(
                        f"Network request to {url} failed after "
                        f"{self._settings.max_retries} retries: {exc}"
                    ) from exc
                time.sleep(self._backoff_delay(attempt))
                continue

            if (
                response.status_code == httpx.codes.UNAUTHORIZED
                and not refreshed_after_401
            ):
                refreshed_after_401 = True
                self._tokens.force_refresh()
                continue

            if response.status_code in _RETRY_STATUS:
                attempt += 1
                if attempt > self._settings.max_retries:
                    _raise_for_status(response)
                time.sleep(self._retry_delay(response, attempt))
                continue

            if response.is_error:
                _raise_for_status(response)

            return response

    @contextmanager
    def stream(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Iterator[httpx.Response]:
        """Open a streaming response, used for product downloads.

        The download concurrency limit is enforced for the duration of the
        stream. The bearer token is attached but streaming bodies are not
        retried, since a partial download should be resumed with a range request
        rather than restarted blindly.
        """
        request_headers = {
            **dict(headers or {}),
            "Authorization": self._tokens.authorization_header(),
        }
        with (
            self._download_semaphore,
            self._http.stream(
                method,
                url,
                headers=request_headers,
                timeout=self._settings.request_timeout,
                **kwargs,
            ) as response,
        ):
            if response.is_error:
                response.read()
                _raise_for_status(response)
            yield response

    def _backoff_delay(self, attempt: int) -> float:
        """Exponential backoff with full jitter, capped at the configured max."""
        ceiling = min(
            self._settings.backoff_max,
            self._settings.backoff_factor * (2 ** (attempt - 1)),
        )
        return random.uniform(0.0, ceiling)

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        """Prefer the server's ``Retry-After`` header, else use backoff."""
        retry_after = _parse_retry_after(response)
        if retry_after is not None:
            return retry_after
        return self._backoff_delay(attempt)


def _parse_retry_after(response: httpx.Response) -> float | None:
    """Return the ``Retry-After`` delay in seconds, when present and numeric."""
    value = response.headers.get("Retry-After")
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        # The header may also be an HTTP date; supporting that is not worth the
        # complexity here, so fall back to backoff instead.
        return None


def _raise_for_status(response: httpx.Response) -> None:
    """Map an unsuccessful response to the appropriate exception and raise it."""
    status = response.status_code
    url = str(response.request.url)
    body = response.text[:500]
    message = f"Request to {url} failed with status {status}."

    if status == httpx.codes.TOO_MANY_REQUESTS:
        raise RateLimitError(
            message,
            status_code=status,
            url=url,
            body=body,
            retry_after=_parse_retry_after(response),
        )
    if status == httpx.codes.FORBIDDEN and "quota" in body.lower():
        raise QuotaExceededError(message, status_code=status, url=url, body=body)
    if status == httpx.codes.NOT_FOUND:
        raise NotFoundError(message, status_code=status, url=url, body=body)
    if status >= httpx.codes.INTERNAL_SERVER_ERROR:
        raise ServerError(message, status_code=status, url=url, body=body)
    raise CdseHTTPError(message, status_code=status, url=url, body=body)
