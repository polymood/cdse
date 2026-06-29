"""Token lifecycle management.

The :class:`TokenManager` is the single place that knows how to obtain, cache,
and refresh an access token. Everything above it simply asks for the current
authorization header and trusts that it is valid.
"""

from __future__ import annotations

import threading
from datetime import timedelta

import httpx

from cdse.auth.providers import AuthProvider
from cdse.auth.store import MemoryTokenStore, TokenSet, TokenStore, _now
from cdse.exceptions import AuthError, ReauthRequiredError, TokenRefreshError


class TokenManager:
    """Obtain and keep an access token valid for the configured provider."""

    def __init__(
        self,
        provider: AuthProvider,
        *,
        http: httpx.Client,
        token_url: str,
        store: TokenStore | None = None,
        expiry_skew: float = 30.0,
    ) -> None:
        self._provider = provider
        self._http = http
        self._token_url = token_url
        self._store = store if store is not None else MemoryTokenStore()
        self._skew = expiry_skew
        self._lock = threading.Lock()

    def authorization_header(self) -> str:
        """Return a valid ``Authorization`` header value, refreshing if needed."""
        with self._lock:
            tokens = self._store.load()
            if tokens is not None and tokens.access_valid(self._skew):
                return tokens.authorization_header
            tokens = self._renew(tokens)
            return tokens.authorization_header

    def force_refresh(self) -> str:
        """Force a token renewal, used after an unexpected ``401`` response."""
        with self._lock:
            tokens = self._renew(self._store.load())
            return tokens.authorization_header

    def clear(self) -> None:
        """Discard any cached tokens."""
        with self._lock:
            self._store.clear()

    def _renew(self, current: TokenSet | None) -> TokenSet:
        """Refresh with the refresh token when possible, otherwise re authenticate."""
        if current is not None and current.refresh_valid(self._skew):
            try:
                return self._grant(
                    {
                        "client_id": self._provider.client_id,
                        "grant_type": "refresh_token",
                        "refresh_token": current.refresh_token or "",
                    }
                )
            except AuthError:
                # The refresh token was rejected even though it looked valid;
                # fall through to a full re authentication when allowed.
                if not self._provider.can_reauthenticate:
                    raise

        if not self._provider.can_reauthenticate and current is not None:
            raise ReauthRequiredError(
                "The session has expired and cannot be renewed without new "
                "credentials. Authenticate again to continue."
            )
        return self._grant(self._provider.grant_data())

    def _grant(self, data: dict[str, str]) -> TokenSet:
        """Exchange the given grant fields for a token set and store it."""
        try:
            response = self._http.post(self._token_url, data=data)
        except httpx.TransportError as exc:
            raise AuthError(f"Could not reach the token endpoint: {exc}") from exc

        if response.status_code != httpx.codes.OK:
            detail = _error_detail(response)
            raise TokenRefreshError(
                f"Token request failed with status {response.status_code}: {detail}"
            )

        tokens = _parse_token_response(response.json())
        self._store.save(tokens)
        return tokens


def _parse_token_response(payload: dict[str, object]) -> TokenSet:
    """Build a :class:`TokenSet` from a Keycloak token response."""
    issued_at = _now()
    access_token = payload.get("access_token")
    expires_in = payload.get("expires_in")
    if not isinstance(access_token, str) or not isinstance(expires_in, int):
        raise TokenRefreshError("Token response did not contain a valid access token.")

    refresh_token = payload.get("refresh_token")
    refresh_token = refresh_token if isinstance(refresh_token, str) else None

    refresh_expires_in = payload.get("refresh_expires_in")
    refresh_expiry = None
    if isinstance(refresh_expires_in, int) and refresh_expires_in > 0 and refresh_token:
        refresh_expiry = issued_at + timedelta(seconds=refresh_expires_in)

    token_type = payload.get("token_type")
    token_type = token_type if isinstance(token_type, str) else "Bearer"

    return TokenSet(
        access_token=access_token,
        access_expiry=issued_at + timedelta(seconds=expires_in),
        refresh_token=refresh_token,
        refresh_expiry=refresh_expiry,
        token_type=token_type,
    )


def _error_detail(response: httpx.Response) -> str:
    """Extract a human readable error description from a token error response."""
    try:
        payload = response.json()
    except ValueError:
        return response.text[:200]
    if isinstance(payload, dict):
        description = payload.get("error_description") or payload.get("error")
        if isinstance(description, str):
            return description
    return response.text[:200]
