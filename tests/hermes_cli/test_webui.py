import hashlib
import json
import stat
from pathlib import Path

from hermes_cli.webui import (
    _node_command,
    build_webui_env,
    create_login_ticket,
    select_available_port,
)


def test_webui_uses_product_managed_node_before_global_path(tmp_path):
    package = tmp_path / "webui"
    node = package / "runtime" / "node" / "bin" / "node"
    node.parent.mkdir(parents=True)
    node.write_text("#!/bin/sh\n")
    node.chmod(0o755)

    command = _node_command(package, "start", 8648)

    assert command[0] == str(node)
    assert command[-3:] == ["--port", "8648", "--no-open"]


def test_webui_child_environment_is_product_scoped_and_filters_secrets(tmp_path):
    env = build_webui_env(
        {
            "PATH": "/usr/bin",
            "HOME": "/Users/tester",
            "OPENAI_API_KEY": "must-not-leak",
            "AUTH_TOKEN": "unrelated-token",
            "HERMES_HOME": "/Users/tester/.hermes",
        },
        home=tmp_path / "deepagent",
        port=9000,
    )

    assert env["DEEPAGENT_HOME"] == str((tmp_path / "deepagent").resolve())
    assert env["HERMES_HOME"] == env["DEEPAGENT_HOME"]
    assert env["HERMES_WEB_UI_HOME"].endswith("/data/webui")
    assert env["DEEPAGENT_WEBUI_RUNTIME_DIR"].endswith("/runtime/webui")
    assert env["BIND_HOST"] == "127.0.0.1"
    assert env["HERMES_LAN_DISCOVERY_ENABLED"] == "false"
    assert env["PORT"] == "9000"
    assert "OPENAI_API_KEY" not in env
    assert "AUTH_TOKEN" not in env


def test_port_selection_skips_an_occupied_local_port(monkeypatch):
    class FakeSocket:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def setsockopt(self, *_args):
            return None

        def bind(self, address):
            if address[1] == 8648:
                raise OSError("occupied")

    monkeypatch.setattr("hermes_cli.webui.socket.socket", lambda *_args: FakeSocket())

    assert select_available_port(start=8648, attempts=2) == 8649


def test_login_ticket_file_contains_only_digest_and_is_owner_only(tmp_path):
    runtime_dir = tmp_path / "runtime" / "webui"
    ticket = "T" * 43

    returned = create_login_ticket(
        runtime_dir,
        now=100.0,
        ttl_seconds=60,
        ticket=ticket,
    )

    digest = hashlib.sha256(ticket.encode()).hexdigest()
    ticket_file = runtime_dir / "login-tickets" / f"{digest}.json"
    record = json.loads(ticket_file.read_text())
    assert returned == ticket
    assert ticket not in ticket_file.read_text()
    assert record == {
        "schema_version": 1,
        "product": "deepagent-webui-ticket",
        "sha256": digest,
        "expires_at": 160_000,
    }
    assert stat.S_IMODE(ticket_file.stat().st_mode) == 0o600
    assert stat.S_IMODE(ticket_file.parent.stat().st_mode) == 0o700
