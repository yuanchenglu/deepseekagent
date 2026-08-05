"""Tests for hermes_constants module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

import hermes_constants
from hermes_constants import get_deepagent_home, get_default_hermes_root, get_hermes_home, is_container


@pytest.fixture(autouse=True)
def _clear_product_home(monkeypatch):
    """Do not let the developer shell choose a test's product namespace."""
    monkeypatch.delenv("DEEPAGENT_HOME", raising=False)


class TestProductHomeIsolation:
    def test_deepagent_home_ignores_existing_hermes_home(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DEEPAGENT_HOME", raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        assert get_deepagent_home() == tmp_path / ".deepagent"

    def test_internal_home_keeps_explicit_legacy_compatibility(self, tmp_path, monkeypatch):
        legacy = tmp_path / ".hermes"
        monkeypatch.delenv("DEEPAGENT_HOME", raising=False)
        monkeypatch.setenv("HERMES_HOME", str(legacy))

        assert get_hermes_home() == legacy

    def test_internal_compatibility_home_can_be_scoped_by_entrypoint(self, tmp_path, monkeypatch):
        product = tmp_path / ".deepagent"
        monkeypatch.setenv("DEEPAGENT_HOME", str(product))
        monkeypatch.setenv("HERMES_HOME", str(product))

        assert get_hermes_home() == product


class TestGetDefaultHermesRoot:
    """Tests for get_default_hermes_root() — Docker/custom deployment awareness."""

    def test_no_hermes_home_returns_native(self, tmp_path, monkeypatch):
        """When HERMES_HOME is not set, returns ~/.deepagent (post-rebrand)."""
        monkeypatch.delenv("HERMES_HOME", raising=False)
        monkeypatch.delenv("DEEPAGENT_HOME", raising=False)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        # Hermes → DeepAgent 品牌迁移后默认路径为 ~/.deepagent
        assert get_default_hermes_root() == tmp_path / ".deepagent"

    def test_hermes_home_is_native(self, tmp_path, monkeypatch):
        """When HERMES_HOME = ~/.deepagent, returns ~/.deepagent."""
        native = tmp_path / ".deepagent"
        native.mkdir()
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(native))
        assert get_default_hermes_root() == native

    def test_hermes_home_is_profile(self, tmp_path, monkeypatch):
        """When HERMES_HOME is a profile under ~/.deepagent, returns ~/.deepagent."""
        native = tmp_path / ".deepagent"
        profile = native / "profiles" / "coder"
        profile.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(profile))
        assert get_default_hermes_root() == native

    def test_hermes_home_is_docker(self, tmp_path, monkeypatch):
        """When HERMES_HOME points outside ~/.deepagent (Docker), returns HERMES_HOME."""
        docker_home = tmp_path / "opt" / "data"
        docker_home.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(docker_home))
        assert get_default_hermes_root() == docker_home

    def test_hermes_home_is_custom_path(self, tmp_path, monkeypatch):
        """Any HERMES_HOME outside ~/.deepagent is treated as the root."""
        custom = tmp_path / "my-deepagent-data"
        custom.mkdir()
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(custom))
        assert get_default_hermes_root() == custom

    def test_docker_profile_active(self, tmp_path, monkeypatch):
        """When a Docker profile is active (HERMES_HOME=<root>/profiles/<name>),
        returns the Docker root, not the profile dir."""
        docker_root = tmp_path / "opt" / "data"
        profile = docker_root / "profiles" / "coder"
        profile.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(profile))
        assert get_default_hermes_root() == docker_root


class TestIsContainer:
    """Tests for is_container() — Docker/Podman detection."""

    def _reset_cache(self, monkeypatch):
        """Reset the cached detection result before each test."""
        monkeypatch.setattr(hermes_constants, "_container_detected", None)

    def test_detects_dockerenv(self, monkeypatch, tmp_path):
        """/.dockerenv triggers container detection."""
        self._reset_cache(monkeypatch)
        monkeypatch.setattr(os.path, "exists", lambda p: p == "/.dockerenv")
        assert is_container() is True

    def test_detects_containerenv(self, monkeypatch, tmp_path):
        """/run/.containerenv triggers container detection (Podman)."""
        self._reset_cache(monkeypatch)
        monkeypatch.setattr(os.path, "exists", lambda p: p == "/run/.containerenv")
        assert is_container() is True

    def test_detects_cgroup_docker(self, monkeypatch, tmp_path):
        """/proc/1/cgroup containing 'docker' triggers detection."""
        import builtins
        self._reset_cache(monkeypatch)
        monkeypatch.setattr(os.path, "exists", lambda p: False)
        cgroup_file = tmp_path / "cgroup"
        cgroup_file.write_text("12:memory:/docker/abc123\n")
        _real_open = builtins.open
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: _real_open(str(cgroup_file), *a, **kw) if p == "/proc/1/cgroup" else _real_open(p, *a, **kw))
        assert is_container() is True

    def test_negative_case(self, monkeypatch, tmp_path):
        """Returns False on a regular Linux host."""
        import builtins
        self._reset_cache(monkeypatch)
        monkeypatch.setattr(os.path, "exists", lambda p: False)
        cgroup_file = tmp_path / "cgroup"
        cgroup_file.write_text("12:memory:/\n")
        _real_open = builtins.open
        monkeypatch.setattr("builtins.open", lambda p, *a, **kw: _real_open(str(cgroup_file), *a, **kw) if p == "/proc/1/cgroup" else _real_open(p, *a, **kw))
        assert is_container() is False

    def test_caches_result(self, monkeypatch):
        """Second call uses cached value without re-probing."""
        monkeypatch.setattr(hermes_constants, "_container_detected", True)
        assert is_container() is True
        # Even if we make os.path.exists return False, cached value wins
        monkeypatch.setattr(os.path, "exists", lambda p: False)
        assert is_container() is True
