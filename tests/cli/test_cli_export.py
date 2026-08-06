"""Tests for the /export CLI slash command."""

import json
import tarfile
from pathlib import Path
from unittest.mock import MagicMock

from cli import HermesCLI, _resolve_export_path, _write_export_jsonl
from hermes_state import SessionDB


def _make_cli(session_id="sess-123", session_db=None):
    cli_obj = HermesCLI.__new__(HermesCLI)
    cli_obj.config = {}
    cli_obj.console = MagicMock()
    cli_obj.agent = None
    cli_obj.conversation_history = []
    cli_obj.session_id = session_id
    cli_obj._pending_input = MagicMock()
    cli_obj._session_db = session_db
    return cli_obj


def _seed_session_db(db, session_id, n_messages=2):
    db.create_session(session_id, source="cli")
    for i in range(n_messages):
        db.append_message(
            session_id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"message {i}",
        )
    return db


def _fresh_db(tmp_path) -> SessionDB:
    return SessionDB(db_path=tmp_path / "state.db")


class TestExportCommand:
    def test_export_session_writes_jsonl(self, tmp_path, monkeypatch):
        db = _fresh_db(tmp_path)
        _seed_session_db(db, "sess-123")
        cli_obj = _make_cli(session_db=db)

        out = str(tmp_path / "export.jsonl")
        monkeypatch.chdir(tmp_path)
        result = cli_obj.process_command(f"/export session {out}")

        assert result is True
        lines = Path(out).read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["id"] == "sess-123"
        assert len(record["messages"]) == 2

    def test_export_session_default_path(self, tmp_path, monkeypatch):
        db = _fresh_db(tmp_path)
        _seed_session_db(db, "20240101_120000_abc123")
        cli_obj = _make_cli(session_id="20240101_120000_abc123", session_db=db)

        monkeypatch.chdir(tmp_path)
        cli_obj.process_command("/export")

        default = tmp_path / "deepagent_session_20240101_120000_abc123.jsonl"
        assert default.is_file()

    def test_export_all_writes_all_sessions(self, tmp_path, monkeypatch):
        db = _fresh_db(tmp_path)
        _seed_session_db(db, "sess-1", n_messages=1)
        _seed_session_db(db, "sess-2", n_messages=3)
        cli_obj = _make_cli(session_db=db)

        monkeypatch.chdir(tmp_path)
        cli_obj.process_command("/export all")

        written = list(tmp_path.glob("deepagent_sessions_*.jsonl"))
        assert len(written) == 1
        records = [
            json.loads(line)
            for line in written[0].read_text(encoding="utf-8").strip().splitlines()
        ]
        assert {r["id"] for r in records} == {"sess-1", "sess-2"}
        assert sum(len(r["messages"]) for r in records) == 4

    def test_export_data_archive(self, tmp_path, monkeypatch):
        from hermes_constants import get_hermes_home

        db = _fresh_db(tmp_path)
        _seed_session_db(db, "sess-9", n_messages=1)
        cli_obj = _make_cli(session_db=db)

        home = get_hermes_home()
        (home / "config.yaml").write_text("model: test/model\n", encoding="utf-8")
        (home / "memories").mkdir(parents=True, exist_ok=True)
        (home / "memories" / "MAP.md").write_text("# memory index\n", encoding="utf-8")

        monkeypatch.chdir(tmp_path)
        cli_obj.process_command("/export data")

        archives = list(tmp_path.glob("deepagent_data_*.tar.gz"))
        assert len(archives) == 1
        with tarfile.open(archives[0], "r:gz") as tar:
            names = tar.getnames()
        assert "config.yaml" in names
        assert "sessions.jsonl" in names
        assert "memories/MAP.md" in names

    def test_export_data_archive_minimal(self, tmp_path, monkeypatch):
        db = _fresh_db(tmp_path)
        _seed_session_db(db, "sess-9", n_messages=1)
        cli_obj = _make_cli(session_db=db)

        monkeypatch.chdir(tmp_path)
        cli_obj.process_command("/export data")

        archives = list(tmp_path.glob("deepagent_data_*.tar.gz"))
        assert len(archives) == 1
        with tarfile.open(archives[0], "r:gz") as tar:
            names = tar.getnames()
        assert "sessions.jsonl" in names
        assert "config.yaml" not in names
        assert not any(n.startswith("memories/") for n in names)

    def test_export_unknown_subcommand_shows_usage(self, tmp_path, monkeypatch, capsys):
        db = _fresh_db(tmp_path)
        _seed_session_db(db, "sess-1")
        cli_obj = _make_cli(session_db=db)

        monkeypatch.chdir(tmp_path)
        cli_obj.process_command("/export bogus")

        out = capsys.readouterr().out
        assert "Unknown subcommand" in out
        assert "Usage: /export" in out

    def test_export_session_not_found(self, tmp_path, monkeypatch, capsys):
        db = _fresh_db(tmp_path)
        cli_obj = _make_cli(session_id="missing", session_db=db)

        monkeypatch.chdir(tmp_path)
        cli_obj.process_command("/export session")

        assert "No session data to export" in capsys.readouterr().out


class TestExportHelpers:
    def test_resolve_export_path_default(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert _resolve_export_path("", "out.jsonl") == str(tmp_path / "out.jsonl")

    def test_resolve_export_path_directory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        target_dir = tmp_path / "exports"
        target_dir.mkdir()
        assert _resolve_export_path(str(target_dir), "out.jsonl") == str(
            target_dir / "out.jsonl"
        )

    def test_write_export_jsonl_creates_parents(self, tmp_path):
        path = tmp_path / "nested" / "dir" / "out.jsonl"
        _write_export_jsonl([{"a": 1}, {"b": 2}], str(path))
        assert path.read_text(encoding="utf-8") == '{"a": 1}\n{"b": 2}\n'


class TestExportCommandRegistration:
    def test_export_command_resolves(self):
        from hermes_cli.commands import resolve_command

        cmd = resolve_command("export")
        assert cmd is not None
        assert cmd.name == "export"
        assert cmd.cli_only is True
