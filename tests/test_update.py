"""Unit tests for hermes_cli/update.py — version check, comparison, release detection.

Covers: compare_versions, _detect_install_mode, is_release_install,
get_current_version, and cmd_check output formatting.

This test file has NO network-dependent tests (fetch_latest_version,
cmd_update_release, cmd_rollback are integration-level).
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

import hermes_cli.update as update_mod


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

    def test_detect_install_mode_release(self, tmp_path):
        """Returns 'release' when VERSION file exists at DEEPAGENT_HOME and no .git."""
        with patch.object(update_mod, "PROJECT_ROOT", tmp_path):
            hermes_home = Path(os.environ["HERMES_HOME"])
            (hermes_home / "VERSION").write_text("v0.9.0\n")
            assert update_mod._detect_install_mode() == "release"

    def test_detect_install_mode_unknown(self, tmp_path):
        """Returns 'unknown' when neither .git nor VERSION file is found."""
        with patch.object(update_mod, "PROJECT_ROOT", tmp_path):
            assert update_mod._detect_install_mode() == "unknown"

    def test_is_release_install_true(self, tmp_path):
        """is_release_install() returns True when operating in release mode."""
        with patch.object(update_mod, "PROJECT_ROOT", tmp_path):
            hermes_home = Path(os.environ["HERMES_HOME"])
            (hermes_home / "VERSION").write_text("v0.9.0\n")
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

    def test_get_current_version_from_home(self):
        """Reads version from DEEPAGENT_HOME/VERSION (priority 1)."""
        hermes_home = Path(os.environ["HERMES_HOME"])
        (hermes_home / "VERSION").write_text("v0.9.0-alpha.1\n")
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

    def test_get_current_version_strips_v_prefix(self):
        """The leading 'v' is stripped from the version string."""
        hermes_home = Path(os.environ["HERMES_HOME"])
        (hermes_home / "VERSION").write_text("v0.9.0\n")
        assert update_mod.get_current_version() == "0.9.0"


# =========================================================================
#  cmd_check — output formatting
# =========================================================================


class TestCmdCheck:
    """CLI output formatting for version check command."""

    def test_cmd_check_update_available(self, capsys):
        """Prints 'Update available' when current < latest."""
        hermes_home = Path(os.environ["HERMES_HOME"])
        (hermes_home / "VERSION").write_text("v0.9.0\n")
        with patch.object(update_mod, "fetch_latest_version", return_value="0.10.0"):
            update_mod.cmd_check(None)
        captured = capsys.readouterr()
        assert "Update available" in captured.out
        assert "v0.9.0" in captured.out
        assert "v0.10.0" in captured.out

    def test_cmd_check_up_to_date(self, capsys):
        """Prints 'Already up to date' when current == latest."""
        hermes_home = Path(os.environ["HERMES_HOME"])
        (hermes_home / "VERSION").write_text("v0.9.0\n")
        with patch.object(update_mod, "fetch_latest_version", return_value="0.9.0"):
            update_mod.cmd_check(None)
        captured = capsys.readouterr()
        assert "Already up to date" in captured.out

    def test_cmd_check_current_newer(self, capsys):
        """Prints 'newer than latest' when current > latest (dev/pre-release version)."""
        hermes_home = Path(os.environ["HERMES_HOME"])
        (hermes_home / "VERSION").write_text("v0.10.0\n")
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
