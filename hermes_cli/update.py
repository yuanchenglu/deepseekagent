"""
Release-based update and rollback for DeepAgent.

Handles tarball-based updates from R2/GitHub releases, including:
- Version query and comparison
- Download with dual-source fallback (R2 → GitHub)
- SHA256 verification
- Backup and rollback
- uv sync for Python dependencies

For source-install (git) setups, updates are handled by the existing
git-based flow in main.py's cmd_update.

This module has NO imports from hermes_cli.main — safe from circular imports.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---- Constants ----

GH_REPO = "yuanchenglu/deepseekagent"
R2_BASE_URL = "https://deepseekagent.starseas.org/releases"
GH_BASE_URL = f"https://github.com/{GH_REPO}/releases/download"
GH_API_LATEST = f"https://api.github.com/repos/{GH_REPO}/releases/latest"

# Resolve PROJECT_ROOT to avoid circular import from hermes_cli.main
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


# ---- Detection ----


def _detect_install_mode() -> str:
    """Detect whether this is a release install or source (git) install.

    Returns:
        "release" if running from a tarball-based install (DEEPAGENT_HOME set,
        VERSION file present, no .git directory at PROJECT_ROOT).
        "source" if running from a git clone.
        "unknown" if neither can be determined.
    """
    # If PROJECT_ROOT has a .git directory, it's a source install
    if (PROJECT_ROOT / ".git").exists():
        return "source"

    # Check if DEEPAGENT_HOME is set and VERSION file exists
    from hermes_constants import get_deepagent_home
    hermes_home = get_deepagent_home()
    version_file = hermes_home / "VERSION"
    if version_file.exists():
        return "release"

    # Fallback: check PROJECT_ROOT/VERSION (source install without .git, or
    # edge case where user cloned without --recursive or .git was removed)
    if (PROJECT_ROOT / "VERSION").exists():
        return "release"

    return "unknown"


def is_release_install() -> bool:
    """Check if running in release-install mode."""
    return _detect_install_mode() == "release"


# ---- Version helpers ----


def _get_deepagent_home() -> Path:
    """Get DEEPAGENT_HOME directory."""
    from hermes_constants import get_deepagent_home
    return get_deepagent_home()


def get_current_version() -> str:
    """Read current version from authoritative source.

    Priority:
      1. DEEPAGENT_HOME/VERSION (release install)
      2. PROJECT_ROOT/VERSION (source install / fallback)
      3. hermes_cli.__version__ (package metadata)

    Returns:
        Version string without leading "v" (e.g. "0.9.0-alpha.1") or "unknown".
    """
    # Priority 1: DEEPAGENT_HOME/VERSION
    try:
        hermes_home = _get_deepagent_home()
        version_file = hermes_home / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip().lstrip("v")
    except Exception:
        pass

    # Priority 2: PROJECT_ROOT/VERSION
    version_file = PROJECT_ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip().lstrip("v")

    # Priority 3: package metadata
    try:
        from hermes_cli import __version__
        return __version__
    except ImportError:
        return "unknown"


def fetch_latest_version() -> Optional[str]:
    """Query GitHub API for the latest release version.

    Returns:
        Version string without leading "v" (e.g. "0.9.1"), or None on failure.
    """
    try:
        req = urllib.request.Request(
            GH_API_LATEST,
            headers={
                "Accept": "application/json",
                "User-Agent": "DeepAgent-update/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            tag = data.get("tag_name", "")
            return tag.lstrip("v") if tag else None
    except Exception:
        return None


def compare_versions(current: str, latest: str) -> int:
    """Compare two version strings.

    Follows SemVer precedence rules:
    - Numeric identifiers compared numerically
    - String identifiers compared lexicographically (ASCII)
    - A full release (no pre-release suffix) is GREATER than any
      pre-release of the same major.minor.patch
      (e.g. "0.9.0" > "0.9.0-alpha.1" > "0.9.0-alpha")

    Returns:
        -1 if current < latest, 0 if equal, 1 if current > latest.
    """
    def _parse(v: str):
        parts = []
        for p in v.replace("-", ".").split("."):
            try:
                parts.append(int(p))
            except ValueError:
                parts.append(p)
        return parts

    cur = _parse(current)
    lat = _parse(latest)

    for i in range(min(len(cur), len(lat))):
        c = cur[i]
        l = lat[i]
        if isinstance(c, int) and isinstance(l, int):
            if c < l:
                return -1
            if c > l:
                return 1
        else:
            c_str, l_str = str(c), str(l)
            if c_str < l_str:
                return -1
            if c_str > l_str:
                return 1

    # One version is a prefix of the other.  In SemVer, a full release
    # (all numeric parts, no pre-release suffix) outranks any pre-release
    # of the same major.minor.patch, e.g. "1.0.0" > "1.0.0-alpha.1".
    # If both have pre-release parts, the longer one is greater.
    if len(cur) < len(lat):
        return 1 if all(isinstance(p, int) for p in cur) else -1
    if len(lat) < len(cur):
        return -1 if all(isinstance(p, int) for p in lat) else 1
    return 0


# ---- Download helpers ----


def _download_file(url: str, dest: Path, desc: str = "") -> bool:
    """Download a file with progress display.

    Args:
        url: Source URL.
        dest: Destination path.
        desc: Human-readable description for logging.

    Returns:
        True on success, False on failure.
    """
    try:
        print(f"  ↓ Downloading {desc}...")
        req = urllib.request.Request(
            url, headers={"User-Agent": "DeepAgent-update/1.0"}
        )
        with urllib.request.urlopen(req, timeout=180) as response:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 8192
            with open(dest, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = int(downloaded * 100 / total)
                        print(f"\r  ↓ Downloading {desc}... {pct}%", end="", flush=True)
            if total > 0:
                print()  # newline after progress
        return True
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        return False


def _verify_sha256(file_path: Path, expected_hash: str) -> bool:
    """Verify SHA256 checksum of a file.

    Args:
        file_path: Path to the file to verify.
        expected_hash: Expected SHA256 hex digest.

    Returns:
        True if checksum matches, False otherwise.
    """
    try:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        actual = h.hexdigest()
        if actual == expected_hash:
            print("  ✓ Checksum verified")
            return True
        print(f"  ✗ Checksum mismatch")
        print(f"    Expected: {expected_hash}")
        print(f"    Actual:   {actual}")
        return False
    except Exception as e:
        print(f"  ⚠ Cannot verify checksum: {e}")
        return False


def _fetch_checksum(version: str) -> Optional[str]:
    """Fetch SHA256 checksum for a release from GitHub.

    The checksum file is hosted on GitHub (a different trust domain from R2),
    providing defense in depth against compromised CDN storage.

    Args:
        version: Version string (without leading "v").

    Returns:
        Hex-encoded SHA256 digest, or None if unavailable.
    """
    sha_url = f"{GH_BASE_URL}/v{version}/deepagent-{version}.sha256"
    try:
        req = urllib.request.Request(
            sha_url, headers={"User-Agent": "DeepAgent-update/1.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode().strip()
            # Format: "hash  filename"  or just "hash"
            return content.split()[0] if content else None
    except Exception:
        return None


def _download_release_tarball(version: str, tmp_dir: Path) -> Optional[Path]:
    """Download release tarball, trying primary then fallback source.

    Strategy:
      1. Try Cloudflare R2 (primary, fast CDN)
      2. Fallback to GitHub Releases

    Args:
        version: Version to download (without leading "v").
        tmp_dir: Temporary directory for download.

    Returns:
        Path to downloaded tarball, or None on complete failure.
    """
    tarball_name = f"deepagent-{version}.tar.gz"
    tarball_path = tmp_dir / tarball_name

    # Primary source: Cloudflare R2
    r2_url = f"{R2_BASE_URL}/{tarball_name}"
    print(f"  Primary source: Cloudflare R2")
    if _download_file(r2_url, tarball_path, f"deepagent-{version}.tar.gz (R2)"):
        return tarball_path

    # Fallback: GitHub Releases
    gh_url = f"{GH_BASE_URL}/v{version}/{tarball_name}"
    print(f"  Primary source failed, trying fallback: GitHub Releases")
    if _download_file(gh_url, tarball_path, f"deepagent-{version}.tar.gz (GitHub)"):
        return tarball_path

    print("  ✗ Both download sources failed")
    return None


# ---- Backup and install ----


def _get_backup_dir() -> Path:
    """Get the backup directory path."""
    return _get_deepagent_home() / ".backup"


def _backup_current_install() -> Optional[Path]:
    """Backup current installation to .backup/{timestamp}/.

    Backs up: deepagent/, webui/, VERSION, skills/.bundled_manifest,
    plus read-only copies of .env, config.yaml, sessions.db.

    Returns:
        Path to backup directory, or None on failure.
    """
    hermes_home = _get_deepagent_home()
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    backup_dir = _get_backup_dir() / timestamp

    print(f"  Backing up current installation to {backup_dir}...")

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup core directories and files
        items_to_backup = [
            "deepagent",
            "webui",
            "VERSION",
            "skills/.bundled_manifest",
        ]
        for item in items_to_backup:
            src = hermes_home / item
            if src.exists():
                dst = backup_dir / item
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.is_dir():
                    shutil.copytree(
                        src,
                        dst,
                        ignore=shutil.ignore_patterns(
                            "__pycache__", "*.pyc", ".venv", "venv", "node_modules"
                        ),
                    )
                else:
                    shutil.copy2(src, dst)

        # Backup config files (for rollback context, not overwritten during update)
        for cfg in (".env", "config.yaml"):
            cfg_path = hermes_home / cfg
            if cfg_path.exists():
                shutil.copy2(cfg_path, backup_dir / cfg)

        # Backup sessions.db (not essential but helps full rollback)
        sessions_db = hermes_home / "sessions.db"
        if sessions_db.exists():
            shutil.copy2(sessions_db, backup_dir / "sessions.db")

        print(f"  ✓ Backup created: {backup_dir}")
        return backup_dir
    except Exception as e:
        print(f"  ✗ Backup failed: {e}")
        return None


def _extract_and_install(tarball_path: Path, version: str) -> bool:
    """Extract tarball and install files to DEEPAGENT_HOME.

    Preserves existing .env, config.yaml, user skills, and sessions.db
    by only copying specific directories from the tarball.

    Args:
        tarball_path: Path to the release tarball.
        version: Version string (without leading "v").

    Returns:
        True on success, False on failure.
    """
    hermes_home = _get_deepagent_home()
    tmp_extract = tarball_path.parent / "extract"

    try:
        print("  Extracting tarball...")
        tmp_extract.mkdir(parents=True, exist_ok=True)

        with tarfile.open(tarball_path, "r:gz") as tar:
            tar.extractall(path=tmp_extract)

        # Find the extracted directory (tarball root: deepagent-{version}/)
        extract_dir = tmp_extract / f"deepagent-{version}"
        if not extract_dir.exists():
            # Fallback: find a single top-level directory
            entries = [d for d in tmp_extract.iterdir() if d.is_dir()]
            if len(entries) == 1:
                extract_dir = entries[0]
            else:
                print(f"  ✗ Cannot find extracted directory in {tmp_extract}")
                return False

        # -- Copy deepagent Python package --
        src_pkg = extract_dir / "deepagent"
        if src_pkg.exists():
            dst_pkg = hermes_home / "deepagent"
            dst_pkg.mkdir(parents=True, exist_ok=True)
            print("  Installing deepagent Python package...")
            for item in src_pkg.iterdir():
                name = item.name
                if name in ("__pycache__", ".venv", "venv", "node_modules"):
                    continue
                dst = dst_pkg / name
                if dst.exists():
                    if dst.is_dir():
                        shutil.rmtree(dst)
                    else:
                        dst.unlink()
                if item.is_dir():
                    shutil.copytree(
                        item, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
                    )
                else:
                    shutil.copy2(item, dst)

        # -- Copy webui (pre-built) --
        src_webui = extract_dir / "webui"
        if src_webui.exists():
            dst_webui = hermes_home / "webui"
            dst_webui.mkdir(parents=True, exist_ok=True)
            print("  Installing WebUI...")
            for item in src_webui.iterdir():
                if item.name == "node_modules":
                    continue
                dst = dst_webui / item.name
                if dst.exists():
                    if dst.is_dir():
                        shutil.rmtree(dst)
                    else:
                        dst.unlink()
                if item.is_dir():
                    shutil.copytree(item, dst)
                else:
                    shutil.copy2(item, dst)

        # -- Copy bundled skills --
        src_skills = extract_dir / "skills"
        if src_skills and src_skills.exists():
            dst_skills = hermes_home / "skills"
            dst_skills.mkdir(parents=True, exist_ok=True)
            print("  Installing system skills...")
            for item in src_skills.iterdir():
                dst = dst_skills / item.name
                if dst.exists():
                    if dst.is_dir():
                        shutil.rmtree(dst)
                    else:
                        dst.unlink()
                if item.is_dir():
                    shutil.copytree(item, dst)
                else:
                    shutil.copy2(item, dst)

        # Write VERSION file (with "v" prefix for consistency with install-release.sh)
        (hermes_home / "VERSION").write_text(f"v{version}\n")
        print(f"  ✓ Version file updated: v{version}")

        return True
    except Exception as e:
        print(f"  ✗ Installation failed: {e}")
        return False
    finally:
        # Cleanup extracted files
        if tmp_extract.exists():
            shutil.rmtree(tmp_extract, ignore_errors=True)


def _run_uv_sync() -> bool:
    """Run uv sync in the deepagent package directory.

    Falls back gracefully if uv is not available or sync fails.

    Returns:
        True if sync succeeded or was skipped, False on critical failure.
    """
    hermes_home = _get_deepagent_home()
    pkg_dir = hermes_home / "deepagent"

    if not (pkg_dir / "pyproject.toml").exists():
        print("  ⚠ No pyproject.toml found in deepagent package, skipping uv sync")
        return True

    uv_bin = shutil.which("uv")
    if not uv_bin:
        print("  ⚠ uv not found in PATH, skipping Python dependency sync")
        return True

    try:
        print("  Running uv sync (Python dependencies)...")
        result = subprocess.run(
            [uv_bin, "sync"],
            cwd=pkg_dir,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            print("  ✓ Python dependencies updated")
            return True
        else:
            print(f"  ✗ uv sync failed (exit code {result.returncode})")
            stderr_lines = result.stderr.strip().splitlines()
            if stderr_lines:
                for line in stderr_lines[-5:]:
                    print(f"    {line}")
            return False
    except subprocess.TimeoutExpired:
        print("  ✗ uv sync timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"  ✗ uv sync error: {e}")
        return False


# ---- Rollback ----


def list_backups() -> list[tuple[str, Path]]:
    """List available backups, sorted by timestamp (newest first).

    Returns:
        List of (timestamp, path) tuples. Each path is verified to be a
        valid backup directory (containing a VERSION file).
    """
    backup_dir = _get_backup_dir()
    if not backup_dir.exists():
        return []

    backups = []
    for entry in sorted(backup_dir.iterdir(), reverse=True):
        if entry.is_dir() and (entry / "VERSION").exists():
            backups.append((entry.name, entry))
    return backups


def _do_rollback(backup_path: Path) -> bool:
    """Restore from a specific backup directory.

    Replaces deepagent/, webui/ and VERSION with backed-up versions,
    then runs uv sync.

    Args:
        backup_path: Path to the backup directory to restore from.

    Returns:
        True on success, False on failure.
    """
    hermes_home = _get_deepagent_home()

    print(f"  Restoring from {backup_path}...")

    try:
        # Restore deepagent package
        src_pkg = backup_path / "deepagent"
        if src_pkg.exists():
            dst_pkg = hermes_home / "deepagent"
            print("  Restoring deepagent Python package...")
            if dst_pkg.exists():
                shutil.rmtree(dst_pkg)
            shutil.copytree(src_pkg, dst_pkg)

        # Restore webui
        src_webui = backup_path / "webui"
        if src_webui.exists():
            dst_webui = hermes_home / "webui"
            print("  Restoring WebUI...")
            if dst_webui.exists():
                shutil.rmtree(dst_webui)
            shutil.copytree(src_webui, dst_webui)

        # Restore VERSION file
        src_version = backup_path / "VERSION"
        if src_version.exists():
            ver = src_version.read_text().strip()
            (hermes_home / "VERSION").write_text(ver + "\n")
            print(f"  ✓ Version restored: {ver}")

        # Run uv sync
        print()
        uv_ok = _run_uv_sync()

        if uv_ok:
            restored_ver = "unknown"
            if src_version.exists():
                restored_ver = src_version.read_text().strip()
            print(f"  ✓ Rollback complete — restored to {restored_ver}")
        else:
            print(f"  ⚠ Rollback files restored but uv sync had issues")

        return True
    except Exception as e:
        print(f"  ✗ Rollback failed: {e}")
        return False


# ===========================================================================
# Public commands — called from hermes_cli.main cmd_update()
# ===========================================================================


def cmd_check(args) -> None:
    """Check current version and compare with latest release.

    Invoked via ``deepagent update --check``.
    """
    current = get_current_version()
    print(f"DeepAgent version check")
    print("=" * 40)
    print(f"Current version: v{current}")

    print("\nChecking for updates...")
    latest = fetch_latest_version()

    if latest is None:
        print("  ⚠ Could not check for updates (network issue)")
        return

    print(f"Latest version:  v{latest}")

    cmp = compare_versions(current, latest)
    if cmp < 0:
        print(f"\n  ✦ Update available: v{current} → v{latest}")
        print(f"  Run 'deepagent update' to upgrade")
    elif cmp == 0:
        print(f"\n  ✓ Already up to date")
    else:
        print(f"\n  Current version is newer than latest release")
        print(f"  (You may be on a development/pre-release version)")


def cmd_update_release(args) -> None:
    """Perform a tarball-based update for release installs.

    Workflow:
      1. Check current version
      2. Fetch latest version from GitHub API
      3. Compare versions (skip if current >= latest, unless --force)
      4. Download tarball from R2 (fallback to GitHub)
      5. Verify SHA256 checksum
      6. Backup current installation to .backup/{timestamp}/
      7. Extract and install new files
      8. Run uv sync
    """
    force = getattr(args, "force", False)

    current = get_current_version()
    print(f"DeepAgent Release Update")
    print("=" * 40)
    print(f"Current version: v{current}")

    print("\n→ Checking for latest version...")
    latest = fetch_latest_version()

    if latest is None:
        print("  ✗ Could not fetch latest version info.")
        print("  Please check your network connection and try again.")
        sys.exit(1)

    print(f"  Latest version: v{latest}")

    if not force:
        cmp = compare_versions(current, latest)
        if cmp >= 0:
            print("\n  ✓ Already up to date!")
            return
        print(f"\n  ✦ Update available: v{current} → v{latest}")
    else:
        print(f"\n  Force update to v{latest} (--force)")

    # Step 1 — Download tarball
    print("\n→ Downloading release tarball...")
    with tempfile.TemporaryDirectory(prefix="deepagent-update-") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)

        tarball = _download_release_tarball(latest, tmp_dir)
        if tarball is None:
            print("  ✗ Download failed. Please try again later.")
            sys.exit(1)

        # Step 2 — Verify checksum
        print("\n→ Verifying checksum...")
        expected_hash = _fetch_checksum(latest)
        if expected_hash:
            if not _verify_sha256(tarball, expected_hash):
                print("  ✗ Checksum verification failed.")
                print("  The download may be corrupted or incomplete.")
                print("  Try again or report the issue.")
                sys.exit(1)
        else:
            print("  ⚠ Could not fetch checksum from GitHub, skipping verification")

        # Step 3 — Backup
        print("\n→ Backing up current installation...")
        backup_path = _backup_current_install()
        if backup_path is None:
            print("  ✗ Backup failed. Aborting update to avoid data loss.")
            sys.exit(1)

        # Step 4 — Extract and install
        print("\n→ Installing new version...")
        if not _extract_and_install(tarball, latest):
            print("\n  ✗ Installation failed. Attempting rollback...")
            if backup_path:
                _do_rollback(backup_path)
            sys.exit(1)

        # Step 5 — uv sync
        print("\n→ Updating Python dependencies...")
        _run_uv_sync()

        print()
        print("=" * 40)
        print(f"  ✓ Update complete! v{current} → v{latest}")
        print()
        print("  Changes will take effect next time you start DeepAgent.")
        print("  If you experience issues, run: deepagent update --rollback")


def cmd_rollback(args) -> None:
    """Rollback to a previous backup.

    Invoked via ``deepagent update --rollback [--to TIMESTAMP]``.

    Lists available backups, verifies integrity, restores deepagent/
    and webui/, then runs uv sync.
    """
    to_timestamp = getattr(args, "to", None)

    print("DeepAgent Rollback")
    print("=" * 40)

    backups = list_backups()

    if not backups:
        print("  No backups found.")
        print(f"  Backups are stored in: {_get_backup_dir()}")
        print("  Backups are only created during 'deepagent update'.")
        return

    target_backup: Optional[Path] = None

    if to_timestamp:
        # Find specific backup by timestamp
        for ts, path in backups:
            if ts == to_timestamp:
                target_backup = path
                break
        if target_backup is None:
            print(f"  Backup '{to_timestamp}' not found.")
            print("  Available backups:")
            for ts, path in backups:
                ver = (
                    (path / "VERSION").read_text().strip()
                    if (path / "VERSION").exists()
                    else "unknown"
                )
                print(f"    {ts}  (v{ver})")
            return
    else:
        # Use the latest (newest first) backup
        target_backup = backups[0][1]

    # Verify backup integrity
    if not (target_backup / "deepagent").exists():
        print(f"  ✗ Backup is incomplete: missing 'deepagent/' directory")
        return

    # Read version from backup
    backup_ver = "unknown"
    vf = target_backup / "VERSION"
    if vf.exists():
        backup_ver = vf.read_text().strip()

    current_ver = get_current_version()

    if to_timestamp:
        print(f"  Target backup: {to_timestamp} (v{backup_ver})")
    else:
        print(f"  Latest backup: {target_backup.name} (v{backup_ver})")

    print(f"  Current: v{current_ver} → Restore to: {backup_ver}")
    print()
    print(f"  Restoring from: {target_backup}")
    print()

    success = _do_rollback(target_backup)
    if not success:
        print("  ✗ Rollback failed.")
        sys.exit(1)
