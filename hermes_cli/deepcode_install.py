"""Verified installer for the product-managed DeepCode runtime."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any

from hermes_constants import get_deepagent_home


RELEASE_BASE_URL = "https://deepseekagent.starseas.org/releases"
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_ARTIFACT_BYTES = 1024 * 1024 * 1024
INSTALL_MARKER = ".deepagent-deepcode-install.json"
ARCHIVE_BINARY = PurePosixPath("embedded/opencode/macos-arm64/opencode")
ARCHIVE_LICENSE = PurePosixPath("embedded/opencode/src/LICENSE")


class DeepCodeInstallError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path, max_bytes: int) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "DeepAgent-DeepCode/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response, destination.open("wb") as output:
        expected = response.headers.get("Content-Length")
        if expected and int(expected) > max_bytes:
            raise DeepCodeInstallError("Download exceeds the declared safety limit")
        received = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            received += len(chunk)
            if received > max_bytes:
                raise DeepCodeInstallError("Download exceeds the declared safety limit")
            output.write(chunk)


def _artifact_url(value: str) -> str:
    if value.startswith("https://"):
        return value
    if value.startswith("/"):
        return f"{RELEASE_BASE_URL}{value}"
    return f"{RELEASE_BASE_URL}/{value}"


def _validate_artifact(manifest: dict[str, Any], version: str) -> dict[str, Any]:
    if manifest.get("schema_version") != 1 or manifest.get("product") != "deepagent":
        raise DeepCodeInstallError("Release manifest product or schema mismatch")
    if manifest.get("channel") != "beta":
        raise DeepCodeInstallError("DeepCode is available only from the verified beta channel")
    if manifest.get("version") != version:
        raise DeepCodeInstallError("Release manifest version mismatch")
    if manifest.get("platform") != {"os": "darwin", "arch": "arm64"}:
        raise DeepCodeInstallError("Release manifest platform mismatch")
    artifact = manifest.get("artifacts", {}).get("deepcode")
    if not isinstance(artifact, dict):
        raise DeepCodeInstallError("Release manifest does not contain deepcode")
    filename = artifact.get("filename")
    size = artifact.get("size")
    digest = artifact.get("sha256")
    url = artifact.get("url")
    if not isinstance(filename, str) or not filename or "/" in filename or ".." in filename:
        raise DeepCodeInstallError("DeepCode artifact filename is unsafe")
    if not isinstance(size, int) or size <= 0 or size > MAX_ARTIFACT_BYTES:
        raise DeepCodeInstallError("DeepCode artifact size is invalid")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
        raise DeepCodeInstallError("DeepCode artifact SHA-256 is invalid")
    if not isinstance(url, str) or not url:
        raise DeepCodeInstallError("DeepCode artifact URL is invalid")
    return artifact


def _safe_extract_deepcode(archive: Path, destination: Path) -> None:
    expected = {ARCHIVE_BINARY: "opencode", ARCHIVE_LICENSE: "LICENSE"}
    seen: set[PurePosixPath] = set()
    extracted = 0
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            path = PurePosixPath(member.name)
            if path not in expected or not member.isfile() or member.issym() or member.islnk():
                raise DeepCodeInstallError(f"Unexpected DeepCode archive entry: {member.name}")
            if path in seen:
                raise DeepCodeInstallError(f"Duplicate DeepCode archive entry: {member.name}")
            seen.add(path)
            extracted += member.size
            if extracted > MAX_ARTIFACT_BYTES:
                raise DeepCodeInstallError("DeepCode archive expands beyond the safety limit")
            source = bundle.extractfile(member)
            if source is None:
                raise DeepCodeInstallError(f"Cannot read DeepCode archive entry: {member.name}")
            target = destination / expected[path]
            with source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
            target.chmod(0o755 if path == ARCHIVE_BINARY else 0o644)
    if seen != set(expected):
        raise DeepCodeInstallError("DeepCode artifact is missing the binary or license")


def _selected_version(root: Path, version: str | None) -> str:
    version_file = root / "VERSION"
    if not version_file.is_file() and version is None:
        raise DeepCodeInstallError("DeepAgent Core is not installed")
    selected = (version or version_file.read_text(encoding="utf-8").strip()).removeprefix("v")
    if not selected or ".." in selected or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in selected):
        raise DeepCodeInstallError("Requested DeepCode version is invalid")
    return selected


def _activate_version(runtime_root: Path, selected: str) -> None:
    current = runtime_root / "current"
    if current.exists() and not current.is_symlink():
        raise DeepCodeInstallError("Existing DeepCode current path is unmanaged; refusing to overwrite")
    if current.is_symlink():
        target = (current.parent / os.readlink(current)).resolve()
        try:
            target.relative_to(runtime_root.resolve())
        except ValueError as exc:
            raise DeepCodeInstallError("Existing DeepCode current link escapes the product runtime") from exc
    temporary = runtime_root / f".current-{os.getpid()}-{os.urandom(4).hex()}"
    temporary.symlink_to(selected, target_is_directory=True)
    os.replace(temporary, current)


def install_deepcode(version: str | None = None, home: Path | None = None) -> Path:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise DeepCodeInstallError("DeepCode Experimental currently supports macOS Apple Silicon only")

    root = (home or get_deepagent_home()).expanduser().resolve()
    selected = _selected_version(root, version)
    runtime_root = root / "runtime" / "deepcode"
    destination = runtime_root / selected
    if destination.exists() and not (destination / INSTALL_MARKER).is_file():
        raise DeepCodeInstallError("Existing DeepCode version is not managed by DeepAgent; refusing to overwrite")

    runtime_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if destination.exists():
        _activate_version(runtime_root, selected)
        return destination

    with tempfile.TemporaryDirectory(prefix="deepcode-install-", dir=runtime_root) as temp_name:
        temporary = Path(temp_name)
        manifest_file = temporary / "manifest.json"
        _download(f"{RELEASE_BASE_URL}/manifests/{selected}.json", manifest_file, MAX_MANIFEST_BYTES)
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DeepCodeInstallError("Release manifest is not valid JSON") from exc
        artifact = _validate_artifact(manifest, selected)

        archive = temporary / artifact["filename"]
        _download(_artifact_url(artifact["url"]), archive, artifact["size"])
        if archive.stat().st_size != artifact["size"]:
            raise DeepCodeInstallError("DeepCode artifact size mismatch")
        if _sha256(archive).lower() != artifact["sha256"].lower():
            raise DeepCodeInstallError("DeepCode artifact SHA-256 mismatch")

        staged = temporary / "staged"
        staged.mkdir(mode=0o700)
        _safe_extract_deepcode(archive, staged)
        (staged / INSTALL_MARKER).write_text(
            json.dumps({"schema_version": 1, "product": "deepagent-deepcode", "version": selected}) + "\n",
            encoding="utf-8",
        )
        os.replace(staged, destination)
    _activate_version(runtime_root, selected)
    return destination


def deepcode_status(home: Path | None = None) -> tuple[bool, str | None]:
    runtime_root = (home or get_deepagent_home()).expanduser().resolve() / "runtime" / "deepcode"
    current = runtime_root / "current"
    if not current.is_symlink():
        return False, None
    try:
        destination = current.resolve(strict=True)
        destination.relative_to(runtime_root.resolve())
    except (OSError, ValueError):
        return False, None
    marker = destination / INSTALL_MARKER
    binary = destination / "opencode"
    return marker.is_file() and binary.is_file(), destination.name


def uninstall_deepcode(home: Path | None = None) -> bool:
    """Remove managed DeepCode binaries while preserving data and caches."""
    root = (home or get_deepagent_home()).expanduser().resolve()
    runtime_root = root / "runtime" / "deepcode"
    if not runtime_root.exists():
        return False
    if runtime_root.is_symlink() or not runtime_root.is_dir():
        raise DeepCodeInstallError("DeepCode runtime path is not a managed directory")
    try:
        runtime_root.resolve().relative_to(root)
    except ValueError as exc:
        raise DeepCodeInstallError("DeepCode runtime path escapes the product directory") from exc

    managed: list[Path] = []
    for entry in runtime_root.iterdir():
        if entry.name == "current" and entry.is_symlink():
            continue
        if entry.is_symlink() or not entry.is_dir():
            raise DeepCodeInstallError(f"Unknown DeepCode runtime entry: {entry.name}")
        try:
            marker = json.loads((entry / INSTALL_MARKER).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DeepCodeInstallError(f"DeepCode version is not managed: {entry.name}") from exc
        if marker.get("product") != "deepagent-deepcode" or marker.get("schema_version") != 1:
            raise DeepCodeInstallError(f"DeepCode version metadata is invalid: {entry.name}")
        managed.append(entry)

    current = runtime_root / "current"
    if current.exists() and not current.is_symlink():
        raise DeepCodeInstallError("DeepCode current path is unmanaged")
    if current.is_symlink():
        current.unlink()
    for entry in managed:
        shutil.rmtree(entry)
    try:
        runtime_root.rmdir()
    except OSError:
        pass
    return bool(managed)
