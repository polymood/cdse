"""Tests for the S3 archive client."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from cdse.cli import app
from cdse.exceptions import CdseConfigError
from cdse.s3 import S3Client


class _FakePaginator:
    def __init__(self, keys: list[str]) -> None:
        self._keys = keys

    def paginate(self, **_: Any) -> list[dict[str, Any]]:
        return [{"Contents": [{"Key": key} for key in self._keys]}]


class _FakeS3:
    def __init__(self, keys: list[str]) -> None:
        self._keys = keys
        self.downloaded: list[tuple[str, str]] = []

    def get_paginator(self, _name: str) -> _FakePaginator:
        return _FakePaginator(self._keys)

    def download_file(self, _bucket: str, key: str, target: str) -> None:
        self.downloaded.append((key, target))
        Path(target).write_text("data")


def test_object_key_normalisation() -> None:
    client = S3Client(client=_FakeS3([]))
    assert client.object_key("s3://eodata/Sentinel-2/x") == "Sentinel-2/x"
    assert client.object_key("/eodata/Sentinel-2/x") == "Sentinel-2/x"
    assert client.object_key("Sentinel-2/x") == "Sentinel-2/x"


def test_download_preserves_structure(tmp_path: Path) -> None:
    keys = [
        "Sentinel-2/2024/PROD.SAFE/MTD.xml",
        "Sentinel-2/2024/PROD.SAFE/GRANULE/a.jp2",
    ]
    fake = _FakeS3(keys)
    client = S3Client(client=fake)

    result = client.download("/eodata/Sentinel-2/2024/PROD.SAFE/", tmp_path)

    assert result == tmp_path
    assert (tmp_path / "PROD.SAFE" / "MTD.xml").read_text() == "data"
    assert (tmp_path / "PROD.SAFE" / "GRANULE" / "a.jp2").exists()
    assert len(fake.downloaded) == 2


def test_download_missing_prefix_raises(tmp_path: Path) -> None:
    client = S3Client(client=_FakeS3([]))
    with pytest.raises(FileNotFoundError):
        client.download("s3://eodata/nothing/here/", tmp_path)


def test_missing_credentials_raise() -> None:
    with pytest.raises(CdseConfigError, match="access key"):
        S3Client()


def test_cli_s3_download_without_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("CDSE_S3_ACCESS_KEY", raising=False)
    monkeypatch.delenv("CDSE_S3_SECRET_KEY", raising=False)
    runner = CliRunner()
    result = runner.invoke(
        app, ["s3", "download", "s3://eodata/x", "-o", str(tmp_path)]
    )
    assert result.exit_code == 1
    assert "access key" in result.output
