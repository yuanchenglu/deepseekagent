"""Manifest-bound DeepAgent uninstaller.

Only paths recorded by a DeepAgent installer and contained by DEEPAGENT_HOME
may be removed. The current working tree and legacy Hermes variables never
establish file ownership.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from hermes_constants import get_deepagent_home
from hermes_cli.colors import Colors, color


MANIFEST_NAME = "install-manifest.json"
PRODUCT_NAME = "deepagent"


def log_info(msg: str) -> None:
    print(f"{color('→', Colors.CYAN)} {msg}")


def log_success(msg: str) -> None:
    print(f"{color('✓', Colors.GREEN)} {msg}")


def log_warn(msg: str) -> None:
    print(f"{color('⚠', Colors.YELLOW)} {msg}")


def _load_manifest(product_home: Path) -> dict[str, Any]:
    manifest_path = product_home / MANIFEST_NAME
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(
            f"No {MANIFEST_NAME} found in {product_home}; refusing to guess file ownership"
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read a valid install manifest: {exc}") from exc

    if manifest.get("product") != PRODUCT_NAME:
        raise ValueError("Install manifest does not belong to DeepAgent")
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported install manifest schema")
    return manifest


def _resolve_owned_path(product_home: Path, relative_path: str) -> Path:
    """Resolve a manifest path and prove it is below product_home."""
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise ValueError("Manifest contains an empty owned path")
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts or relative == Path("."):
        raise ValueError(f"Unsafe owned path in manifest: {relative_path!r}")

    root = product_home.resolve()
    # Resolve the parent to catch an intermediate symlink escape, but keep the
    # final component unresolved so removing ``current`` unlinks the symlink
    # itself rather than deleting its target directory.
    parent = (root / relative.parent).resolve(strict=False)
    try:
        parent.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Owned path escapes DEEPAGENT_HOME: {relative_path!r}") from exc
    candidate = parent / relative.name
    if candidate == root:
        raise ValueError("The product root cannot be an owned child path")
    return candidate


def _remove_owned_path(path: Path) -> bool:
    if path.is_symlink() or path.is_file():
        path.unlink()
        return True
    if path.is_dir():
        shutil.rmtree(path)
        return True
    return False


def _managed_launcher_path(manifest: dict[str, Any]) -> Path | None:
    raw = manifest.get("command_path")
    if not isinstance(raw, str) or not raw:
        return None
    candidate = Path(raw).expanduser().resolve(strict=False)
    expected = (Path.home() / ".local" / "bin" / "deepagent").resolve(strict=False)
    if candidate != expected:
        raise ValueError(f"Refusing unexpected command path: {candidate}")
    return candidate


def _remove_managed_launcher(manifest: dict[str, Any]) -> bool:
    launcher = _managed_launcher_path(manifest)
    if launcher is None or not launcher.exists():
        return False
    if launcher.is_symlink():
        launcher.unlink()
        return True
    try:
        content = launcher.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"Cannot verify DeepAgent launcher ownership: {exc}") from exc
    if "# DeepAgent managed launcher" not in content:
        raise ValueError(f"Refusing to remove an unmanaged launcher: {launcher}")
    launcher.unlink()
    return True


def _confirm(full_uninstall: bool) -> bool:
    action = (
        "delete registered DeepAgent code and data"
        if full_uninstall
        else "remove registered DeepAgent code but keep user data"
    )
    print(f"This will {action}.")
    try:
        return input("Type 'yes' to confirm: ").strip().lower() == "yes"
    except (KeyboardInterrupt, EOFError):
        return False


def _prune_empty_parents(product_home: Path) -> None:
    for relative in ("versions", "runtime", "cache", "logs", "data", "config"):
        try:
            (product_home / relative).rmdir()
        except OSError:
            pass
    try:
        product_home.rmdir()
    except OSError:
        pass


def run_uninstall(args) -> bool:
    """Remove only installer-owned DeepAgent paths."""
    product_home = get_deepagent_home().expanduser().resolve(strict=False)
    full_uninstall = bool(getattr(args, "full", False))
    assume_yes = bool(getattr(args, "yes", False))

    print()
    print(color("DeepAgent Uninstaller", Colors.MAGENTA, Colors.BOLD))
    print(f"Product home: {product_home}")

    try:
        manifest = _load_manifest(product_home)
        launcher = _managed_launcher_path(manifest)
        code_paths = manifest.get("code_paths", [])
        data_paths = manifest.get("data_paths", [])
        if not isinstance(code_paths, list) or not isinstance(data_paths, list):
            raise ValueError("Install manifest path lists are invalid")
        selected = code_paths + (data_paths if full_uninstall else [])
        resolved = [_resolve_owned_path(product_home, item) for item in selected]
    except ValueError as exc:
        log_warn(str(exc))
        log_warn("Nothing was removed. Reinstall DeepAgent to recreate a trusted manifest.")
        return False

    print(f"Command: {launcher or '(not registered)'}")
    for path in resolved:
        print(f"  - {path}")

    if not assume_yes and not _confirm(full_uninstall):
        log_info("Uninstall cancelled")
        return False

    try:
        if _remove_managed_launcher(manifest):
            log_success("Removed ~/.local/bin/deepagent")
        for path in sorted(resolved, key=lambda item: len(item.parts), reverse=True):
            if _remove_owned_path(path):
                log_success(f"Removed {path}")

        manifest_path = product_home / MANIFEST_NAME
        if full_uninstall:
            manifest_path.unlink(missing_ok=True)
            _prune_empty_parents(product_home)
        else:
            manifest["code_paths"] = []
            manifest["command_path"] = None
            manifest["current_version"] = None
            tmp_path = manifest_path.with_suffix(".tmp")
            tmp_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            os.replace(tmp_path, manifest_path)
        log_success("Uninstall complete")
        return True
    except (OSError, ValueError) as exc:
        log_warn(f"Uninstall stopped safely: {exc}")
        return False
