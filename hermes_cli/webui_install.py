"""Verified, atomic installer for the separately licensed WebUI artifact."""

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
MAX_EXTRACTED_BYTES = 1024 * 1024 * 1024
INSTALL_MARKER = ".deepagent-webui-install.json"


class WebUiInstallError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path, max_bytes: int) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "DeepAgent-WebUI/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response, destination.open("wb") as output:
        expected_header = response.headers.get("Content-Length")
        if expected_header and int(expected_header) > max_bytes:
            raise WebUiInstallError("Download exceeds the declared safety limit")
        received = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            received += len(chunk)
            if received > max_bytes:
                raise WebUiInstallError("Download exceeds the declared safety limit")
            output.write(chunk)


def _artifact_url(value: str) -> str:
    if value.startswith("https://"):
        return value
    if value.startswith("/"):
        return f"{RELEASE_BASE_URL}{value}"
    return f"{RELEASE_BASE_URL}/{value}"


def _validate_artifact(manifest: dict[str, Any], version: str, key: str) -> dict[str, Any]:
    if manifest.get("schema_version") != 1 or manifest.get("product") != "deepagent":
        raise WebUiInstallError("Release manifest product or schema mismatch")
    if manifest.get("channel") != "beta":
        raise WebUiInstallError("WebUI is available only from the verified beta channel")
    if manifest.get("version") != version:
        raise WebUiInstallError("Release manifest version mismatch")
    if manifest.get("platform") != {"os": "darwin", "arch": "arm64"}:
        raise WebUiInstallError("Release manifest platform mismatch")
    artifact = manifest.get("artifacts", {}).get(key)
    if not isinstance(artifact, dict):
        raise WebUiInstallError(f"Release manifest does not contain {key}")
    filename = artifact.get("filename")
    size = artifact.get("size")
    digest = artifact.get("sha256")
    url = artifact.get("url")
    if not isinstance(filename, str) or not filename or "/" in filename or ".." in filename:
        raise WebUiInstallError("WebUI artifact filename is unsafe")
    if not isinstance(size, int) or size <= 0:
        raise WebUiInstallError("WebUI artifact size is invalid")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
        raise WebUiInstallError("WebUI artifact SHA-256 is invalid")
    if not isinstance(url, str) or not url:
        raise WebUiInstallError("WebUI artifact URL is invalid")
    return artifact


def _safe_extract_webui(archive: Path, destination: Path) -> None:
    extracted_bytes = 0
    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getmembers()
        if not members:
            raise WebUiInstallError("WebUI archive is empty")
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "webui":
                raise WebUiInstallError(f"Unsafe WebUI archive path: {member.name}")
            if member.issym() or member.islnk() or member.isdev() or not (member.isdir() or member.isfile()):
                raise WebUiInstallError(f"Unsupported WebUI archive entry: {member.name}")
            extracted_bytes += member.size
            if extracted_bytes > MAX_EXTRACTED_BYTES:
                raise WebUiInstallError("WebUI archive expands beyond the safety limit")

        for member in members:
            relative = Path(*PurePosixPath(member.name).parts[1:])
            if not relative.parts:
                continue
            target = (destination / relative).resolve()
            try:
                target.relative_to(destination.resolve())
            except ValueError as exc:
                raise WebUiInstallError(f"WebUI archive escapes destination: {member.name}") from exc
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True, mode=0o755)
                continue
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            source = bundle.extractfile(member)
            if source is None:
                raise WebUiInstallError(f"Cannot read WebUI archive entry: {member.name}")
            with source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
            target.chmod(member.mode & 0o755 or 0o644)


def install_webui(version: str | None = None, home: Path | None = None) -> Path:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise WebUiInstallError("WebUI Beta currently supports macOS Apple Silicon only")

    root = (home or get_deepagent_home()).expanduser().resolve()
    version_file = root / "VERSION"
    if not version_file.is_file():
        raise WebUiInstallError("DeepAgent Core is not installed")
    selected = (version or version_file.read_text(encoding="utf-8").strip()).removeprefix("v")
    if not selected or ".." in selected or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in selected):
        raise WebUiInstallError("Requested WebUI version is invalid")

    destination = root / "webui"
    if destination.exists() and not (destination / INSTALL_MARKER).is_file():
        raise WebUiInstallError("Existing WebUI directory is not managed by DeepAgent; refusing to overwrite")

    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="webui-install-", dir=root) as temp_name:
        temporary = Path(temp_name)
        manifest_file = temporary / "manifest.json"
        _download(
            f"{RELEASE_BASE_URL}/manifests/{selected}.json",
            manifest_file,
            MAX_MANIFEST_BYTES,
        )
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WebUiInstallError("Release manifest is not valid JSON") from exc
        artifact = _validate_artifact(manifest, selected, "webui")

        archive = temporary / artifact["filename"]
        _download(_artifact_url(artifact["url"]), archive, artifact["size"])
        if archive.stat().st_size != artifact["size"]:
            raise WebUiInstallError("WebUI artifact size mismatch")
        if _sha256(archive).lower() != artifact["sha256"].lower():
            raise WebUiInstallError("WebUI artifact SHA-256 mismatch")

        staged = temporary / "staged"
        staged.mkdir(mode=0o755)
        _safe_extract_webui(archive, staged)
        if (
            not (staged / "bin" / "hermes-web-ui.mjs").is_file()
            or not (staged / "dist" / "server" / "index.js").is_file()
            or not (staged / "runtime" / "node" / "bin" / "node").is_file()
            or not (staged / "runtime" / "node" / "LICENSE").is_file()
            or not (staged / "node_modules" / "socket.io" / "package.json").is_file()
            or not (staged / "node_modules" / "node-pty" / "package.json").is_file()
        ):
            raise WebUiInstallError("WebUI artifact is missing required runtime files")
        (staged / INSTALL_MARKER).write_text(
            json.dumps({"schema_version": 1, "product": "deepagent-webui", "version": selected}) + "\n",
            encoding="utf-8",
        )

        backup = root / f".webui-backup-{secrets_token()}"
        replaced = False
        try:
            if destination.exists():
                os.replace(destination, backup)
                replaced = True
            os.replace(staged, destination)
        except Exception:
            if replaced and not destination.exists() and backup.exists():
                os.replace(backup, destination)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    return destination


def uninstall_webui(home: Path | None = None) -> bool:
    """Remove only the marker-managed WebUI package; retain user data."""
    root = (home or get_deepagent_home()).expanduser().resolve()
    destination = root / "webui"
    if not destination.exists():
        return False
    if destination.is_symlink() or not destination.is_dir():
        raise WebUiInstallError("WebUI package path is not a managed directory")
    try:
        destination.resolve().relative_to(root)
        marker = json.loads((destination / INSTALL_MARKER).read_text(encoding="utf-8"))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        raise WebUiInstallError("WebUI package is missing valid management metadata") from exc
    if marker.get("product") != "deepagent-webui" or marker.get("schema_version") != 1:
        raise WebUiInstallError("WebUI package management metadata is invalid")
    shutil.rmtree(destination)
    return True


def secrets_token() -> str:
    return hashlib.sha256(os.urandom(32)).hexdigest()[:16]
