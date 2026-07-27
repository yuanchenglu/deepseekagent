import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest

from hermes_cli.webui_install import (
    INSTALL_MARKER,
    WebUiInstallError,
    _safe_extract_webui,
    install_webui,
    uninstall_webui,
)


def _build_webui_archive(path: Path) -> None:
    files = {
        "webui/bin/hermes-web-ui.mjs": b"console.log('webui')\n",
        "webui/dist/server/index.js": b"console.log('server')\n",
        "webui/dist/client/index.html": b"<html></html>\n",
        "webui/runtime/node/bin/node": b"managed-node\n",
        "webui/runtime/node/LICENSE": b"Node.js license\n",
        "webui/node_modules/socket.io/package.json": b'{"name":"socket.io"}\n',
        "webui/node_modules/node-pty/package.json": b'{"name":"node-pty"}\n',
        "webui/package.json": b'{"version":"1.2.3"}\n',
    }
    with tarfile.open(path, "w:gz") as archive:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mode = 0o755 if name.endswith(".mjs") or name.endswith("/node") else 0o644
            archive.addfile(info, io.BytesIO(content))


def test_verified_webui_install_is_atomic_and_managed(tmp_path, monkeypatch):
    home = tmp_path / "deepagent"
    home.mkdir()
    (home / "VERSION").write_text("v1.2.3\n")
    archive = tmp_path / "webui.tar.gz"
    _build_webui_archive(archive)
    manifest = {
        "schema_version": 1,
        "product": "deepagent",
        "channel": "beta",
        "version": "1.2.3",
        "platform": {"os": "darwin", "arch": "arm64"},
        "artifacts": {
            "webui": {
                "filename": "deepagent-webui-server-1.2.3.tar.gz",
                "url": "/deepagent-webui-server-1.2.3.tar.gz",
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

    monkeypatch.setattr("hermes_cli.webui_install.platform.system", lambda: "Darwin")
    monkeypatch.setattr("hermes_cli.webui_install.platform.machine", lambda: "arm64")
    monkeypatch.setattr("hermes_cli.webui_install._download", fake_download)

    destination = install_webui(home=home)

    assert (destination / "bin" / "hermes-web-ui.mjs").is_file()
    marker = json.loads((destination / INSTALL_MARKER).read_text())
    assert marker["version"] == "1.2.3"


def test_webui_installer_refuses_unmanaged_existing_directory(tmp_path, monkeypatch):
    home = tmp_path / "deepagent"
    (home / "webui").mkdir(parents=True)
    (home / "VERSION").write_text("1.2.3")
    monkeypatch.setattr("hermes_cli.webui_install.platform.system", lambda: "Darwin")
    monkeypatch.setattr("hermes_cli.webui_install.platform.machine", lambda: "arm64")

    with pytest.raises(WebUiInstallError, match="not managed"):
        install_webui(home=home)


def test_webui_extractor_rejects_path_traversal(tmp_path):
    archive = tmp_path / "unsafe.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        info = tarfile.TarInfo("webui/../../outside")
        info.size = 1
        bundle.addfile(info, io.BytesIO(b"x"))

    with pytest.raises(WebUiInstallError, match="Unsafe"):
        _safe_extract_webui(archive, tmp_path / "output")


def test_webui_uninstall_removes_only_managed_package(tmp_path):
    home = tmp_path / "deepagent"
    package = home / "webui"
    package.mkdir(parents=True)
    (package / INSTALL_MARKER).write_text(json.dumps({
        "schema_version": 1,
        "product": "deepagent-webui",
        "version": "1.2.3",
    }))
    data = home / "data" / "webui" / "hermes-web-ui.db"
    data.parent.mkdir(parents=True)
    data.write_text("user-data")

    assert uninstall_webui(home) is True
    assert not package.exists()
    assert data.read_text() == "user-data"


def test_webui_uninstall_refuses_unmanaged_package(tmp_path):
    home = tmp_path / "deepagent"
    (home / "webui").mkdir(parents=True)

    with pytest.raises(WebUiInstallError, match="management metadata"):
        uninstall_webui(home)
