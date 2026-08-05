"""DeepAgent-owned WebUI lifecycle and one-time browser login tickets."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Mapping

from hermes_constants import get_deepagent_home


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8648
MAX_PORT_ATTEMPTS = 100
TICKET_TTL_SECONDS = 60

_SAFE_ENV_NAMES = {
    "PATH",
    "HOME",
    "TMPDIR",
    "TMP",
    "TEMP",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "SHELL",
    "SystemRoot",
    "ComSpec",
    "PATHEXT",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "NODE_EXTRA_CA_CERTS",
    "HERMES_DESKTOP",
    "DEEPAGENT_RUNTIME_LEASE_SOCKET",
    "DEEPAGENT_RUNTIME_LEASE_TOKEN",
    "DEEPAGENT_RUNTIME_LEASE_TTL_MS",
}


class WebUiError(RuntimeError):
    """Fail-closed lifecycle error suitable for direct CLI display."""


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _product_paths(home: Path | None = None) -> tuple[Path, Path, Path]:
    root = (home or get_deepagent_home()).expanduser().resolve()
    data_dir = (root / "data" / "webui").resolve()
    runtime_dir = (root / "runtime" / "webui").resolve()
    if not _is_within(data_dir, root) or not _is_within(runtime_dir, root):
        raise WebUiError("WebUI paths escape DEEPAGENT_HOME")
    return root, data_dir, runtime_dir


def _package_dir(home: Path | None = None) -> Path:
    root, _, _ = _product_paths(home)
    installed = root / "webui"
    if (installed / "bin" / "hermes-web-ui.mjs").is_file():
        return installed

    # Source checkout fallback is development-only and never consults a global
    # Hermes/OpenCode installation.
    source_root = Path(__file__).resolve().parents[1]
    source_webui = source_root / "webui"
    if (source_root / ".git").exists() and (source_webui / "bin" / "hermes-web-ui.mjs").is_file():
        return source_webui

    raise WebUiError("WebUI is not installed. Run: deepagent webui install")


def build_webui_env(
    base_env: Mapping[str, str] | None = None,
    home: Path | None = None,
    port: int | None = None,
) -> dict[str, str]:
    """Build a minimal child environment without unrelated API credentials."""
    source = dict(base_env if base_env is not None else os.environ)
    root, data_dir, runtime_dir = _product_paths(home)
    env = {name: source[name] for name in _SAFE_ENV_NAMES if source.get(name)}
    env.update({
        "DEEPAGENT_HOME": str(root),
        # Legacy runtime code sees only the DeepAgent-owned root.
        "HERMES_HOME": str(root),
        "HERMES_WEB_UI_HOME": str(data_dir),
        "HERMES_WEBUI_STATE_DIR": str(data_dir),
        "DEEPAGENT_WEBUI_RUNTIME_DIR": str(runtime_dir),
        "BIND_HOST": DEFAULT_HOST,
        "HERMES_LAN_DISCOVERY_ENABLED": "false",
        "NODE_ENV": "production",
    })
    if port is not None:
        env["PORT"] = str(port)
    return env


def select_available_port(
    start: int = DEFAULT_PORT,
    attempts: int = MAX_PORT_ATTEMPTS,
    host: str = DEFAULT_HOST,
) -> int:
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
            candidate.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
            try:
                candidate.bind((host, port))
            except OSError:
                continue
            return port
    raise WebUiError(f"No local port is available in {start}-{start + attempts - 1}")


def _node_command(package_dir: Path, action: str, port: int | None = None) -> list[str]:
    bundled = package_dir / "runtime" / "node" / "bin" / "node"
    node = str(bundled) if bundled.is_file() and os.access(bundled, os.X_OK) else shutil.which("node")
    if not node:
        raise WebUiError("The managed WebUI Node.js runtime is missing")
    command = [node, str(package_dir / "bin" / "hermes-web-ui.mjs"), action]
    if port is not None:
        command.extend(["--port", str(port)])
    if action == "start":
        command.append("--no-open")
    return command


def _read_port(runtime_dir: Path) -> int | None:
    try:
        record = json.loads((runtime_dir / "port.json").read_text(encoding="utf-8"))
        port = int(record["port"])
        if record.get("product") != "deepagent-webui" or not 1 <= port <= 65535:
            return None
        return port
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None


def _write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, separators=(",", ":"), sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        path.chmod(0o600)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _health_ok(port: int, timeout: float = 1.0) -> bool:
    try:
        with urllib.request.urlopen(f"http://{DEFAULT_HOST}:{port}/health", timeout=timeout) as response:
            if response.status != 200:
                return False
            payload = json.loads(response.read().decode("utf-8"))
            return payload.get("status") == "ok"
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError):
        return False


def _run_node(
    package_dir: Path,
    action: str,
    *,
    home: Path,
    port: int | None = None,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _node_command(package_dir, action, port),
        cwd=package_dir,
        env=build_webui_env(home=home, port=port),
        check=False,
        text=True,
        capture_output=capture,
    )


def start_webui(home: Path | None = None) -> int:
    root, _, runtime_dir = _product_paths(home)
    package_dir = _package_dir(root)
    existing_port = _read_port(runtime_dir)
    if existing_port:
        status = _run_node(package_dir, "status", home=root, capture=True)
        if status.returncode == 0 and "is running" in (status.stdout or "") and _health_ok(existing_port):
            print(f"DeepAgent WebUI is already running at http://{DEFAULT_HOST}:{existing_port}")
            return existing_port

    port = select_available_port()
    result = _run_node(package_dir, "start", home=root, port=port)
    if result.returncode != 0 or not _health_ok(port, timeout=2.0):
        raise WebUiError(f"WebUI failed to start; see {runtime_dir / 'server.log'}")

    _write_json_atomic(runtime_dir / "port.json", {
        "schema_version": 1,
        "product": "deepagent-webui",
        "host": DEFAULT_HOST,
        "port": port,
    })
    print(f"DeepAgent WebUI started at http://{DEFAULT_HOST}:{port}")
    return port


def status_webui(home: Path | None = None) -> bool:
    root, _, runtime_dir = _product_paths(home)
    package_dir = _package_dir(root)
    port = _read_port(runtime_dir)
    result = _run_node(package_dir, "status", home=root, capture=True)
    owned_running = result.returncode == 0 and "is running" in (result.stdout or "")
    running = bool(port and owned_running and _health_ok(port))
    if running:
        print(f"DeepAgent WebUI is running at http://{DEFAULT_HOST}:{port}")
    else:
        print("DeepAgent WebUI is not running")
    return running


def stop_webui(home: Path | None = None) -> bool:
    root, _, runtime_dir = _product_paths(home)
    package_dir = _package_dir(root)
    result = _run_node(package_dir, "stop", home=root)
    if result.returncode != 0:
        print("DeepAgent WebUI is not running")
        return False
    try:
        (runtime_dir / "port.json").unlink()
    except FileNotFoundError:
        pass
    print("DeepAgent WebUI stopped")
    return True


def create_login_ticket(
    runtime_dir: Path,
    *,
    now: float | None = None,
    ttl_seconds: int = TICKET_TTL_SECONDS,
    ticket: str | None = None,
) -> str:
    runtime_dir = runtime_dir.expanduser().resolve()
    tickets_dir = runtime_dir / "login-tickets"
    tickets_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    tickets_dir.chmod(0o700)

    value = ticket or secrets.token_urlsafe(32)
    if not 32 <= len(value) <= 256:
        raise WebUiError("Generated login ticket has an invalid length")
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    expires_at = int(((now if now is not None else time.time()) + ttl_seconds) * 1000)
    _write_json_atomic(tickets_dir / f"{digest}.json", {
        "schema_version": 1,
        "product": "deepagent-webui-ticket",
        "sha256": digest,
        "expires_at": expires_at,
    })
    return value


def open_webui(home: Path | None = None, opener=webbrowser.open) -> str:
    root, _, runtime_dir = _product_paths(home)
    port = _read_port(runtime_dir)
    if not port or not status_webui(root):
        port = start_webui(root)

    ticket = create_login_ticket(runtime_dir)
    url = f"http://{DEFAULT_HOST}:{port}/#/?ticket={ticket}"
    if not opener(url, new=2):
        print("Could not open a browser. Open this one-time URL within 60 seconds:")
        print(url)
    else:
        print("Opened DeepAgent WebUI in your browser")
    return url


def run_webui_command(action: str, home: Path | None = None) -> None:
    try:
        if action == "start":
            start_webui(home)
        elif action == "open":
            open_webui(home)
        elif action == "status":
            status_webui(home)
        elif action == "stop":
            stop_webui(home)
        else:
            raise WebUiError(f"Unknown WebUI action: {action}")
    except WebUiError as exc:
        print(f"Error: {exc}", file=os.sys.stderr)
        raise SystemExit(1) from exc
