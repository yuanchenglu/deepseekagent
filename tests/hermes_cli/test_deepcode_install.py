import hashlib
import io
import json
import os
import tarfile
from pathlib import Path

import pytest

from hermes_cli.deepcode_install import (
    INSTALL_MARKER,
    DeepCodeInstallError,
    _safe_extract_deepcode,
    deepcode_status,
    install_deepcode,
    uninstall_deepcode,
)


def _archive(path: Path, *, unsafe: bool = False) -> None:
    files = {
        "embedded/opencode/macos-arm64/opencode": b"#!/bin/sh\n",
        "embedded/opencode/src/LICENSE": b"MIT License\n",
    }
    if unsafe:
        files["embedded/opencode/macos-arm64/extra"] = b"unexpected"
    with tarfile.open(path, "w:gz") as bundle:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mode = 0o755 if name.endswith("opencode") else 0o644
            bundle.addfile(info, io.BytesIO(content))


def test_verified_deepcode_install_is_versioned_and_product_scoped(tmp_path, monkeypatch):
    home = tmp_path / "deepagent"
    home.mkdir()
    (home / "VERSION").write_text("v1.2.3\n")
    archive = tmp_path / "deepcode.tar.gz"
    _archive(archive)
    manifest = {
        "schema_version": 1,
        "product": "deepagent",
        "channel": "beta",
        "version": "1.2.3",
        "platform": {"os": "darwin", "arch": "arm64"},
        "artifacts": {
            "deepcode": {
                "filename": "deepagent-deepcode-1.2.3.tar.gz",
                "url": "/deepagent-deepcode-1.2.3.tar.gz",
                "size": archive.stat().st_size,
                "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            },
        },
    }

    def fake_download(url, destination, _max_bytes):
        if url.endswith(".json"):
            destination.write_text(json.dumps(manifest))
        else:
            destination.write_bytes(archive.read_bytes())

    monkeypatch.setattr("hermes_cli.deepcode_install.platform.system", lambda: "Darwin")
    monkeypatch.setattr("hermes_cli.deepcode_install.platform.machine", lambda: "arm64")
    monkeypatch.setattr("hermes_cli.deepcode_install._download", fake_download)

    destination = install_deepcode(home=home)

    assert destination == home / "runtime" / "deepcode" / "1.2.3"
    assert os.access(destination / "opencode", os.X_OK)
    assert (destination / "LICENSE").read_text() == "MIT License\n"
    assert json.loads((destination / INSTALL_MARKER).read_text())["product"] == "deepagent-deepcode"
    assert (home / "runtime" / "deepcode" / "current").resolve() == destination.resolve()
    assert deepcode_status(home) == (True, "1.2.3")


def test_deepcode_installer_refuses_unmanaged_version(tmp_path, monkeypatch):
    home = tmp_path / "deepagent"
    (home / "runtime" / "deepcode" / "1.2.3").mkdir(parents=True)
    (home / "VERSION").write_text("1.2.3")
    monkeypatch.setattr("hermes_cli.deepcode_install.platform.system", lambda: "Darwin")
    monkeypatch.setattr("hermes_cli.deepcode_install.platform.machine", lambda: "arm64")

    with pytest.raises(DeepCodeInstallError, match="not managed"):
        install_deepcode(home=home)


def test_deepcode_extractor_rejects_unexpected_files(tmp_path):
    archive = tmp_path / "unsafe.tar.gz"
    _archive(archive, unsafe=True)
    destination = tmp_path / "output"
    destination.mkdir()

    with pytest.raises(DeepCodeInstallError, match="Unexpected"):
        _safe_extract_deepcode(archive, destination)


def test_deepcode_uninstall_removes_runtime_but_preserves_task_data(tmp_path):
    home = tmp_path / "deepagent"
    runtime = home / "runtime" / "deepcode"
    version = runtime / "1.2.3"
    version.mkdir(parents=True)
    (version / "opencode").write_text("binary")
    (version / INSTALL_MARKER).write_text(json.dumps({
        "schema_version": 1,
        "product": "deepagent-deepcode",
        "version": "1.2.3",
    }))
    (runtime / "current").symlink_to("1.2.3", target_is_directory=True)
    data = home / "data" / "deepcode" / "tasks.json"
    data.parent.mkdir(parents=True)
    data.write_text("tasks")

    assert uninstall_deepcode(home) is True
    assert not runtime.exists()
    assert data.read_text() == "tasks"


def test_deepcode_uninstall_refuses_unknown_runtime_entries(tmp_path):
    home = tmp_path / "deepagent"
    runtime = home / "runtime" / "deepcode"
    runtime.mkdir(parents=True)
    (runtime / "unknown.txt").write_text("user-owned")

    with pytest.raises(DeepCodeInstallError, match="Unknown"):
        uninstall_deepcode(home)
    assert (runtime / "unknown.txt").read_text() == "user-owned"
