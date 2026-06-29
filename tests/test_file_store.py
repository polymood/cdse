"""Tests for the file backed token store."""

from __future__ import annotations

import os
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cdse.auth.store import FileTokenStore, TokenSet


def _tokens() -> TokenSet:
    now = datetime.now(UTC)
    return TokenSet(
        access_token="a",
        access_expiry=now + timedelta(minutes=5),
        refresh_token="r",
        refresh_expiry=now + timedelta(minutes=60),
    )


def test_roundtrip_and_clear(tmp_path: Path) -> None:
    store = FileTokenStore(tmp_path / "credentials.json")
    assert store.load() is None

    store.save(_tokens())
    loaded = store.load()
    assert loaded is not None
    assert loaded.access_token == "a"
    assert loaded.refresh_token == "r"

    store.clear()
    assert store.load() is None


def test_saved_file_is_owner_only(tmp_path: Path) -> None:
    path = tmp_path / "credentials.json"
    FileTokenStore(path).save(_tokens())
    if os.name == "posix":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_corrupt_file_loads_as_none(tmp_path: Path) -> None:
    path = tmp_path / "credentials.json"
    path.write_text("not json")
    assert FileTokenStore(path).load() is None
