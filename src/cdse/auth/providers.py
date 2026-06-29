"""Authentication providers.

A provider describes how to obtain the first token from the CDSE identity
service. It does not perform any network request itself; it only supplies the
form fields for the grant. The :class:`~cdse.auth.manager.TokenManager` owns the
actual exchange and the subsequent refreshes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from cdse.config import DEFAULT_CLIENT_ID


class AuthProvider(ABC):
    """Base class for the supported OAuth grant types."""

    #: The Keycloak client identifier used for the grant.
    client_id: str

    #: Whether a failed refresh can fall back to a full re authentication. This
    #: is true when the provider holds the original credentials.
    can_reauthenticate: bool

    @abstractmethod
    def grant_data(self) -> dict[str, str]:
        """Return the form fields for the initial token request."""


class PasswordAuth(AuthProvider):
    """Authenticate with a username and password (resource owner grant)."""

    can_reauthenticate = True

    def __init__(
        self,
        username: str,
        password: str,
        *,
        totp: str | None = None,
        client_id: str = DEFAULT_CLIENT_ID,
    ) -> None:
        self.client_id = client_id
        self._username = username
        self._password = password
        self._totp = totp

    def grant_data(self) -> dict[str, str]:
        data = {
            "client_id": self.client_id,
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
        }
        if self._totp is not None:
            data["totp"] = self._totp
        return data


class RefreshTokenAuth(AuthProvider):
    """Authenticate with a refresh token obtained elsewhere.

    A full re authentication is not possible because the original credentials
    are not held, so once the refresh token expires the session ends.
    """

    can_reauthenticate = False

    def __init__(
        self,
        refresh_token: str,
        *,
        client_id: str = DEFAULT_CLIENT_ID,
    ) -> None:
        self.client_id = client_id
        self._refresh_token = refresh_token

    def grant_data(self) -> dict[str, str]:
        return {
            "client_id": self.client_id,
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }


class ClientCredentialsAuth(AuthProvider):
    """Authenticate a registered machine client (client credentials grant).

    No refresh token is issued for this grant. When the access token expires
    the manager simply requests a new one, which this provider always can do.
    """

    can_reauthenticate = True

    def __init__(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id
        self._client_secret = client_secret

    def grant_data(self) -> dict[str, str]:
        return {
            "client_id": self.client_id,
            "client_secret": self._client_secret,
            "grant_type": "client_credentials",
        }
