import json
from types import SimpleNamespace

import pytest

from hermes_cli.uninstall import _resolve_owned_path, run_uninstall


def _write_manifest(home, command_path, *, code_paths=None, data_paths=None):
    home.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "product": "deepagent",
        "current_version": "0.9.0-alpha.1",
        "command_path": str(command_path),
        "code_paths": code_paths or ["versions/0.9.0-alpha.1", "current"],
        "data_paths": data_paths or ["config", "data", "cache", "logs", "runtime"],
    }
    (home / "install-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_owned_path_rejects_escape(tmp_path):
    with pytest.raises(ValueError, match="Unsafe owned path"):
        _resolve_owned_path(tmp_path / ".deepagent", "../.hermes")


def test_owned_symlink_resolves_to_link_not_target(tmp_path):
    product_home = tmp_path / ".deepagent"
    version = product_home / "versions" / "v1"
    version.mkdir(parents=True)
    current = product_home / "current"
    current.symlink_to(version)

    assert _resolve_owned_path(product_home, "current") == current


def test_missing_manifest_refuses_to_remove_anything(tmp_path, monkeypatch):
    product_home = tmp_path / ".deepagent"
    product_home.mkdir()
    marker = product_home / "keep.txt"
    marker.write_text("user data")
    monkeypatch.setenv("DEEPAGENT_HOME", str(product_home))

    result = run_uninstall(SimpleNamespace(full=True, yes=True))

    assert result is False
    assert marker.exists()


def test_keep_data_removes_only_registered_code(tmp_path, monkeypatch):
    product_home = tmp_path / ".deepagent"
    command = tmp_path / ".local" / "bin" / "deepagent"
    command.parent.mkdir(parents=True)
    command.write_text("#!/bin/sh\n# DeepAgent managed launcher\n")
    version = product_home / "versions" / "0.9.0-alpha.1"
    version.mkdir(parents=True)
    (version / "app.py").write_text("pass")
    (product_home / "current").symlink_to(version)
    data = product_home / "data"
    data.mkdir(parents=True)
    (data / "session.db").write_text("session")
    _write_manifest(product_home, command)
    monkeypatch.setattr("hermes_cli.uninstall.Path.home", lambda: tmp_path)
    monkeypatch.setenv("DEEPAGENT_HOME", str(product_home))

    assert run_uninstall(SimpleNamespace(full=False, yes=True)) is True

    assert not command.exists()
    assert not version.exists()
    assert data.exists()
    manifest = json.loads((product_home / "install-manifest.json").read_text())
    assert manifest["code_paths"] == []


def test_full_uninstall_never_touches_hermes_or_opencode(tmp_path, monkeypatch):
    product_home = tmp_path / ".deepagent"
    command = tmp_path / ".local" / "bin" / "deepagent"
    command.parent.mkdir(parents=True)
    command.write_text("#!/bin/sh\n# DeepAgent managed launcher\n")
    for relative in ("versions/0.9.0-alpha.1", "config", "data", "cache", "logs", "runtime"):
        path = product_home / relative
        path.mkdir(parents=True)
        (path / "owned").write_text("yes")
    (product_home / "current").symlink_to(product_home / "versions" / "0.9.0-alpha.1")
    _write_manifest(product_home, command)
    hermes_marker = tmp_path / ".hermes" / "config.yaml"
    opencode_marker = tmp_path / ".config" / "opencode" / "config.json"
    hermes_marker.parent.mkdir(parents=True)
    opencode_marker.parent.mkdir(parents=True)
    hermes_marker.write_text("hermes")
    opencode_marker.write_text("opencode")
    monkeypatch.setattr("hermes_cli.uninstall.Path.home", lambda: tmp_path)
    monkeypatch.setenv("DEEPAGENT_HOME", str(product_home))
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))

    assert run_uninstall(SimpleNamespace(full=True, yes=True)) is True

    assert hermes_marker.read_text() == "hermes"
    assert opencode_marker.read_text() == "opencode"
