"""Unit tests for hermes_cli/update.py — version check, comparison, release detection.

Covers: compare_versions, _detect_install_mode, is_release_install,
get_current_version, and cmd_check output formatting.

All network and subprocess boundaries are mocked.
"""

import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import hermes_cli.update as update_mod


@pytest.fixture(autouse=True)
def isolate_update_home(tmp_path, monkeypatch):
    home = tmp_path / "deepagent-home"
    home.mkdir()
    monkeypatch.setattr(update_mod, "_get_deepagent_home", lambda: home)
    return home


# =========================================================================
#  compare_versions — pure logic, no mocking required
# =========================================================================


class TestCompareVersions:
    """SemVer comparison logic — all edge cases."""

    def test_compare_versions_equal(self):
        """0.9.0 vs 0.9.0 → 0"""
        assert update_mod.compare_versions("0.9.0", "0.9.0") == 0

    def test_compare_versions_newer(self):
        """0.8.0 (current) vs 0.9.0 (latest) → -1 (current < latest)"""
        assert update_mod.compare_versions("0.8.0", "0.9.0") == -1

    def test_compare_versions_older(self):
        """0.9.0 (current) vs 0.8.0 (latest) → 1 (current > latest)"""
        assert update_mod.compare_versions("0.9.0", "0.8.0") == 1

    def test_compare_versions_release_vs_pre_release(self):
        """0.9.0 (full release) vs 0.9.0-alpha.1 (pre-release) → 1 (release > pre-release)"""
        assert update_mod.compare_versions("0.9.0", "0.9.0-alpha.1") == 1

    def test_compare_versions_same_pre_release(self):
        """0.9.0-alpha.1 vs 0.9.0-alpha.1 → 0"""
        assert update_mod.compare_versions("0.9.0-alpha.1", "0.9.0-alpha.1") == 0

    def test_compare_versions_different_pre_release(self):
        """0.9.0-alpha.1 vs 0.9.0-beta.1 → -1 (alpha < beta, ASCII order)"""
        result = update_mod.compare_versions("0.9.0-alpha.1", "0.9.0-beta.1")
        assert result == -1, f"Expected -1, got {result}"

    def test_compare_versions_major(self):
        """1.0.0 vs 2.0.0 → -1 (major version bump)"""
        assert update_mod.compare_versions("1.0.0", "2.0.0") == -1

    def test_compare_versions_patch(self):
        """0.9.0 vs 0.9.1 → -1 (patch bump)"""
        assert update_mod.compare_versions("0.9.0", "0.9.1") == -1

    def test_compare_versions_pre_release_less_than_release(self):
        """0.9.0-alpha vs 0.9.0 → -1 (pre-release < full release)"""
        assert update_mod.compare_versions("0.9.0-alpha", "0.9.0") == -1

    def test_compare_versions_longer_pre_release(self):
        """0.9.0-alpha.1 vs 0.9.0-alpha.1.extra → -1 (extra segment = greater)"""
        result = update_mod.compare_versions("0.9.0-alpha.1", "0.9.0-alpha.1.extra")
        assert result == -1, f"Expected -1, got {result}"

    def test_compare_versions_pre_release_with_numbers(self):
        """0.9.0-alpha.2 vs 0.9.0-alpha.10 → -1 (numeric comparison, not lexicographic)"""
        assert update_mod.compare_versions("0.9.0-alpha.2", "0.9.0-alpha.10") == -1

    def test_compare_versions_mixed_identifiers(self):
        """0.9.0-rc.1 vs 0.9.0 → -1 (release candidate < full release)"""
        assert update_mod.compare_versions("0.9.0-rc.1", "0.9.0") == -1


# =========================================================================
#  _detect_install_mode — file-system detection logic
# =========================================================================


class TestDetectInstallMode:
    """Detection of release vs source vs unknown install mode."""

    def test_detect_install_mode_source(self, tmp_path):
        """Returns 'source' when PROJECT_ROOT contains a .git directory."""
        with patch.object(update_mod, "PROJECT_ROOT", tmp_path):
            (tmp_path / ".git").mkdir()
            assert update_mod._detect_install_mode() == "source"

    def test_detect_install_mode_release(self, tmp_path, isolate_update_home):
        """Returns 'release' when VERSION file exists at DEEPAGENT_HOME and no .git."""
        with patch.object(update_mod, "PROJECT_ROOT", tmp_path):
            (isolate_update_home / "VERSION").write_text("v0.9.0\n")
            assert update_mod._detect_install_mode() == "release"

    def test_detect_install_mode_unknown(self, tmp_path):
        """Returns 'unknown' when neither .git nor VERSION file is found."""
        with patch.object(update_mod, "PROJECT_ROOT", tmp_path):
            assert update_mod._detect_install_mode() == "unknown"

    def test_is_release_install_true(self, tmp_path, isolate_update_home):
        """is_release_install() returns True when operating in release mode."""
        with patch.object(update_mod, "PROJECT_ROOT", tmp_path):
            (isolate_update_home / "VERSION").write_text("v0.9.0\n")
            assert update_mod.is_release_install() is True

    def test_is_release_install_source(self, tmp_path):
        """is_release_install() returns False when .git is present (source install)."""
        with patch.object(update_mod, "PROJECT_ROOT", tmp_path):
            (tmp_path / ".git").mkdir()
            assert update_mod.is_release_install() is False


# =========================================================================
#  get_current_version — VERSION file and package metadata resolution
# =========================================================================


class TestGetCurrentVersion:
    """Version resolution: DEEPAGENT_HOME/VERSION > PROJECT_ROOT/VERSION > __version__."""

    def test_get_current_version_from_home(self, isolate_update_home):
        """Reads version from DEEPAGENT_HOME/VERSION (priority 1)."""
        (isolate_update_home / "VERSION").write_text("v0.9.0-alpha.1\n")
        assert update_mod.get_current_version() == "0.9.0-alpha.1"

    def test_get_current_version_from_project_root(self, tmp_path):
        """Falls back to PROJECT_ROOT/VERSION when DEEPAGENT_HOME/VERSION absent."""
        with patch.object(update_mod, "PROJECT_ROOT", tmp_path):
            (tmp_path / "VERSION").write_text("v1.0.0\n")
            assert update_mod.get_current_version() == "1.0.0"

    def test_get_current_version_from_package_metadata(self, tmp_path, monkeypatch):
        """Falls back to hermes_cli.__version__ when no VERSION file exists anywhere."""
        import hermes_cli
        monkeypatch.delattr(hermes_cli, "__version__", raising=False)
        with patch.object(update_mod, "PROJECT_ROOT", tmp_path):
            # Ensure no VERSION exists at DEEPAGENT_HOME (conftest guarantees this)
            # Ensure no VERSION exists at PROJECT_ROOT (tmp_path is clean)
            result = update_mod.get_current_version()
            # Without __version__ and without VERSION files, should return "unknown"
            assert result == "unknown"

    def test_get_current_version_strips_v_prefix(self, isolate_update_home):
        """The leading 'v' is stripped from the version string."""
        (isolate_update_home / "VERSION").write_text("v0.9.0\n")
        assert update_mod.get_current_version() == "0.9.0"


# =========================================================================
#  cmd_check — output formatting
# =========================================================================


class TestCmdCheck:
    """CLI output formatting for version check command."""

    def test_cmd_check_update_available(self, capsys, isolate_update_home):
        """Prints 'Update available' when current < latest."""
        (isolate_update_home / "VERSION").write_text("v0.9.0\n")
        with patch.object(update_mod, "fetch_latest_version", return_value="0.10.0"):
            update_mod.cmd_check(None)
        captured = capsys.readouterr()
        assert "Update available" in captured.out
        assert "v0.9.0" in captured.out
        assert "v0.10.0" in captured.out

    def test_cmd_check_up_to_date(self, capsys, isolate_update_home):
        """Prints 'Already up to date' when current == latest."""
        (isolate_update_home / "VERSION").write_text("v0.9.0\n")
        with patch.object(update_mod, "fetch_latest_version", return_value="0.9.0"):
            update_mod.cmd_check(None)
        captured = capsys.readouterr()
        assert "Already up to date" in captured.out

    def test_cmd_check_current_newer(self, capsys, isolate_update_home):
        """Prints 'newer than latest' when current > latest (dev/pre-release version)."""
        (isolate_update_home / "VERSION").write_text("v0.10.0\n")
        with patch.object(update_mod, "fetch_latest_version", return_value="0.9.0"):
            update_mod.cmd_check(None)
        captured = capsys.readouterr()
        assert "newer than latest" in captured.out

    def test_cmd_check_network_error(self, capsys):
        """Prints network error message when fetch_latest_version returns None."""
        with patch.object(update_mod, "fetch_latest_version", return_value=None):
            update_mod.cmd_check(None)
        captured = capsys.readouterr()
        assert "Could not check for updates" in captured.out


class TestReleaseChannel:
    def test_fetch_latest_version_reads_promoted_alpha_channel(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"schema_version": 1, "product": "deepagent", "channel": "alpha", "version": "v0.9.1-alpha.2"}
        ).encode()
        with patch("hermes_cli.update.urllib.request.urlopen", return_value=response) as urlopen:
            assert update_mod.fetch_latest_version() == "0.9.1-alpha.2"
        assert urlopen.call_args.args[0].full_url == update_mod.ALPHA_CHANNEL_URL

    def test_fetch_latest_version_fails_closed_on_invalid_json(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b"not-json"
        with patch("hermes_cli.update.urllib.request.urlopen", return_value=response):
            assert update_mod.fetch_latest_version() is None

    def test_fetch_latest_version_reads_promoted_beta_channel(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"schema_version": 1, "product": "deepagent", "channel": "beta", "version": "0.9.1-beta.2"}
        ).encode()
        with patch("hermes_cli.update.urllib.request.urlopen", return_value=response) as urlopen:
            assert update_mod.fetch_latest_version("beta") == "0.9.1-beta.2"
        assert urlopen.call_args.args[0].full_url == update_mod.BETA_CHANNEL_URL

    def test_update_channel_uses_managed_install_channel(self, isolate_update_home):
        (isolate_update_home / "install-manifest.json").write_text(json.dumps({
            "schema_version": 1,
            "product": "deepagent",
            "channel": "beta",
        }))

        assert update_mod._update_channel(SimpleNamespace(channel=None)) == "beta"


class TestReleaseUpdate:
    def test_release_update_invokes_verified_installer_with_explicit_version(self, tmp_path):
        installer = tmp_path / "scripts" / "install-release.sh"
        installer.parent.mkdir()
        installer.write_text("#!/bin/sh\n")
        home = tmp_path / "home"
        home.mkdir()
        completed = SimpleNamespace(returncode=0)

        with patch.object(update_mod, "PROJECT_ROOT", tmp_path), \
             patch.object(update_mod, "get_current_version", return_value="0.9.0-alpha.1"), \
             patch.object(update_mod, "fetch_latest_version", return_value="0.9.0-alpha.2"), \
             patch.object(update_mod, "_get_deepagent_home", return_value=home), \
             patch.object(update_mod.subprocess, "run", return_value=completed) as run:
            update_mod.cmd_update_release(SimpleNamespace(force=False))

        assert run.call_args.args[0] == [
            "bash", str(installer), "--version", "0.9.0-alpha.2",
            "--dir", str(home), "--skip-setup", "--channel", "alpha",
        ]

    def test_release_update_preserves_current_when_installer_fails(self, tmp_path):
        installer = tmp_path / "scripts" / "install-release.sh"
        installer.parent.mkdir()
        installer.write_text("#!/bin/sh\n")
        home = tmp_path / "home"
        home.mkdir()

        with patch.object(update_mod, "PROJECT_ROOT", tmp_path), \
             patch.object(update_mod, "get_current_version", return_value="0.9.0-alpha.1"), \
             patch.object(update_mod, "fetch_latest_version", return_value="0.9.0-alpha.2"), \
             patch.object(update_mod, "_get_deepagent_home", return_value=home), \
             patch.object(update_mod.subprocess, "run", return_value=SimpleNamespace(returncode=23)), \
             pytest.raises(SystemExit) as exc:
            update_mod.cmd_update_release(SimpleNamespace(force=False))
        assert exc.value.code == 23


def _managed_install(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    versions = home / "versions"
    for version in ("0.9.0-alpha.1", "0.9.0-alpha.2"):
        cli = versions / version / ".venv" / "bin" / "deepagent"
        cli.parent.mkdir(parents=True)
        cli.write_text("#!/bin/sh\nexit 0\n")
    (home / "current").symlink_to(Path("versions") / "0.9.0-alpha.2")
    (home / "VERSION").write_text("0.9.0-alpha.2\n")
    (home / "install-manifest.json").write_text(json.dumps({
        "schema_version": 1,
        "product": "deepagent",
        "current_version": "0.9.0-alpha.2",
    }))
    return home


class TestRollback:
    def test_rollback_switches_symlink_and_metadata(self, tmp_path):
        home = _managed_install(tmp_path)
        with patch.object(update_mod, "_get_deepagent_home", return_value=home), \
             patch.object(update_mod.subprocess, "run", return_value=SimpleNamespace(returncode=0)):
            update_mod.cmd_rollback(SimpleNamespace(to="0.9.0-alpha.1"))

        assert os.readlink(home / "current") == "versions/0.9.0-alpha.1"
        assert (home / "VERSION").read_text() == "0.9.0-alpha.1\n"
        manifest = json.loads((home / "install-manifest.json").read_text())
        assert manifest["current_version"] == "0.9.0-alpha.1"

    def test_rollback_restores_current_when_smoke_test_fails(self, tmp_path):
        home = _managed_install(tmp_path)
        with patch.object(update_mod, "_get_deepagent_home", return_value=home), \
             patch.object(update_mod.subprocess, "run", return_value=SimpleNamespace(returncode=1)), \
             pytest.raises(SystemExit):
            update_mod.cmd_rollback(SimpleNamespace(to="0.9.0-alpha.1"))

        assert os.readlink(home / "current") == "versions/0.9.0-alpha.2"
        assert (home / "VERSION").read_text() == "0.9.0-alpha.2\n"
        manifest = json.loads((home / "install-manifest.json").read_text())
        assert manifest["current_version"] == "0.9.0-alpha.2"

    def test_rollback_refuses_invalid_install_manifest(self, tmp_path):
        home = _managed_install(tmp_path)
        (home / "install-manifest.json").write_text("not json")
        with patch.object(update_mod, "_get_deepagent_home", return_value=home), \
             pytest.raises(SystemExit):
            update_mod.cmd_rollback(SimpleNamespace(to="0.9.0-alpha.1"))
        assert os.readlink(home / "current") == "versions/0.9.0-alpha.2"
