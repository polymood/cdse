"""Tests for the command line interface."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cdse.auth.store import FileTokenStore, TokenSet
from cdse.cli import app

runner = CliRunner()


def _seed_tokens(config_dir: Path) -> FileTokenStore:
    now = datetime.now(UTC)
    store = FileTokenStore(config_dir / "credentials.json")
    store.save(
        TokenSet(
            access_token="a",
            access_expiry=now + timedelta(minutes=5),
            refresh_token="r",
            refresh_expiry=now + timedelta(minutes=60),
        )
    )
    return store


def test_status_not_authenticated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CDSE_CONFIG_DIR", str(tmp_path))
    result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 1
    assert "Not authenticated" in result.output


def test_status_authenticated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDSE_CONFIG_DIR", str(tmp_path))
    _seed_tokens(tmp_path)
    result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert "Access token valid: True" in result.output
    assert "Refresh token valid: True" in result.output


def test_logout_clears_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDSE_CONFIG_DIR", str(tmp_path))
    store = _seed_tokens(tmp_path)
    result = runner.invoke(app, ["auth", "logout"])
    assert result.exit_code == 0
    assert store.load() is None


def test_odata_search_requires_login(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CDSE_CONFIG_DIR", str(tmp_path))
    result = runner.invoke(app, ["odata", "search", "--collection", "SENTINEL-2"])
    assert result.exit_code == 1
    assert "Not authenticated" in result.output


def test_stac_search_requires_login(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CDSE_CONFIG_DIR", str(tmp_path))
    result = runner.invoke(app, ["stac", "search", "-c", "sentinel-2-l2a"])
    assert result.exit_code == 1
    assert "Not authenticated" in result.output


def test_login_stores_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDSE_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("CDSE_USERNAME", "user@example.com")
    monkeypatch.setenv("CDSE_PASSWORD", "secret")

    class FakeAuth:
        def __init__(self, store: FileTokenStore) -> None:
            self._store = store

        def authorization_header(self) -> str:
            now = datetime.now(UTC)
            self._store.save(
                TokenSet(
                    access_token="a",
                    access_expiry=now + timedelta(minutes=5),
                    refresh_token="r",
                    refresh_expiry=now + timedelta(minutes=60),
                )
            )
            return "Bearer a"

    class FakeClient:
        def __init__(self, provider, *, settings, store):
            self.auth = FakeAuth(store)

        def close(self) -> None:
            pass

    monkeypatch.setattr("cdse.cli.auth.Client", FakeClient)
    result = runner.invoke(app, ["auth", "login"])
    assert result.exit_code == 0, result.output
    assert "Logged in" in result.output
    assert FileTokenStore(tmp_path / "credentials.json").load() is not None
