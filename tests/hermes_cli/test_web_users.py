"""Unit tests for hermes_cli.web_users — the local dashboard account store.

``web_users`` is pure logic (no FastAPI/HTTP), so these tests drive the whole
user/auth feature directly against the quick interface and on-disk store.
"""

import json
import os

import pytest

from hermes_cli import web_users


@pytest.fixture(autouse=True)
def _clean_sessions():
    """Sessions are process-global; keep them isolated between tests."""
    web_users.clear_sessions()
    yield
    web_users.clear_sessions()


def _register(username="admin", password="correct-horse-42", **extra):
    return web_users.register(username, password, extra.get("email", ""), extra.get("phone", ""))


# ---------------------------------------------------------------------------
# Account store (on-disk)
# ---------------------------------------------------------------------------


class TestAccountStore:
    def test_users_path_lives_in_hermes_home(self):
        from hermes_cli.config import get_hermes_home

        assert web_users.users_path() == get_hermes_home() / "web_users.json"

    def test_load_users_returns_empty_when_no_file(self):
        assert web_users.load_users() == {}

    def test_load_users_ignores_malformed_file(self, tmp_path, monkeypatch):
        path = web_users.users_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not json {")
        assert web_users.load_users() == {}

    def test_load_users_skips_records_without_credentials(self, tmp_path, monkeypatch):
        path = web_users.users_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"users": {"broken": {"username": "broken"}, "ok": None}}))
        assert web_users.load_users() == {}

    def test_has_users_false_then_true(self):
        assert web_users.has_users() is False
        _register()
        assert web_users.has_users() is True

    def test_save_user_persists_hashed_password_only(self):
        web_users.save_user("admin", "plaintext-pass", "a@b.co", "13800138000")
        path = web_users.users_path()
        assert path.exists()
        assert "plaintext-pass" not in path.read_text()

        raw = json.loads(path.read_text())
        user = raw["users"]["admin"]
        assert user["username"] == "admin"
        assert user["email"] == "a@b.co"
        assert user["phone"] == "13800138000"
        assert user["salt"]
        assert user["hash"]
        assert user["hash"] != "plaintext-pass"
        assert "created_at" in user

    def test_save_user_writes_private_permissions(self):
        _register()
        assert os.stat(web_users.users_path()).st_mode & 0o777 == 0o600

    def test_save_user_updates_existing_record(self):
        web_users.save_user("admin", "first-pass")
        web_users.save_user("admin", "second-pass", "new@b.co")
        user = web_users.load_users()["admin"]
        assert user["email"] == "new@b.co"
        assert web_users.verify_password("admin", "second-pass") is True
        assert web_users.verify_password("admin", "first-pass") is False


# ---------------------------------------------------------------------------
# Login identifier resolution + password verification
# ---------------------------------------------------------------------------


class TestCredentials:
    def _seed(self):
        web_users.save_user("Alice", "s3cret-pass", "Alice@Example.com", "13800138000")

    def test_find_user_by_username(self):
        self._seed()
        assert web_users.find_user_by_login("alice") == "Alice"

    def test_find_user_by_email_is_case_insensitive(self):
        self._seed()
        assert web_users.find_user_by_login("alice@example.com") == "Alice"

    def test_find_user_by_phone(self):
        self._seed()
        assert web_users.find_user_by_login("13800138000") == "Alice"

    def test_find_user_strips_whitespace(self):
        self._seed()
        assert web_users.find_user_by_login("  Alice  ") == "Alice"

    def test_find_user_unknown(self):
        self._seed()
        assert web_users.find_user_by_login("ghost") is None

    def test_verify_password_correct_and_wrong(self):
        web_users.save_user("admin", "correct-horse-42")
        assert web_users.verify_password("admin", "correct-horse-42") is True
        assert web_users.verify_password("admin", "wrong") is False

    def test_verify_password_unknown_user(self):
        assert web_users.verify_password("nobody", "whatever1") is False

    def test_verify_password_tolerates_corrupt_record(self, tmp_path, monkeypatch):
        path = web_users.users_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"users": {"admin": {"salt": "zz", "hash": "!!"}}}))
        assert web_users.verify_password("admin", "anything") is False


# ---------------------------------------------------------------------------
# Registration + login quick interface
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_register_creates_first_account_and_session(self):
        token = _register("admin", "s3cret-pass", email="a@b.co", phone="13800138000")
        assert token
        assert web_users.session_user(token) == "admin"
        assert web_users.has_users() is True

    def test_register_strips_username_whitespace(self):
        token = _register("  admin  ")
        assert token
        assert web_users.session_user(token) == "admin"

    def test_register_rejects_second_account(self):
        _register("admin")
        assert web_users.register("someone-else", "another-pass") is None

    def test_register_returns_none_when_account_exists(self):
        _register("admin")
        assert web_users.register("admin", "another-pass") is None


class TestLogin:
    def _seed(self):
        _register("admin", "s3cret-pass", email="admin@example.com", phone="13800138000")

    def test_login_with_username(self):
        self._seed()
        token = web_users.login("admin", "s3cret-pass")
        assert token
        assert web_users.session_user(token) == "admin"

    def test_login_with_email(self):
        self._seed()
        assert web_users.login("admin@example.com", "s3cret-pass")

    def test_login_with_phone(self):
        self._seed()
        assert web_users.login("13800138000", "s3cret-pass")

    def test_login_wrong_password(self):
        self._seed()
        assert web_users.login("admin", "wrong") is None

    def test_login_unknown_user(self):
        assert web_users.login("ghost", "s3cret-pass") is None


# ---------------------------------------------------------------------------
# Login sessions
# ---------------------------------------------------------------------------


class TestSessions:
    def test_issue_and_resolve_session(self):
        token = web_users.issue_session("admin")
        assert token
        assert web_users.session_user(token) == "admin"

    def test_session_user_rejects_garbage_token(self):
        assert web_users.session_user("not-a-real-token") is None

    def test_session_user_rejects_none(self):
        assert web_users.session_user(None) is None

    def test_session_user_rejects_empty(self):
        assert web_users.session_user("") is None

    def test_session_expires(self, monkeypatch):
        now = [1_700_000_000.0]
        monkeypatch.setattr(web_users.time, "time", lambda: now[0])
        token = web_users.issue_session("admin")
        assert web_users.session_user(token) == "admin"

        now[0] = now[0] + web_users.SESSION_TTL_SECONDS + 1
        assert web_users.session_user(token) is None
        # The expired token should be pruned from the store.
        assert token not in web_users._user_sessions

    def test_revoke_session(self):
        token = web_users.issue_session("admin")
        web_users.revoke_session(token)
        assert web_users.session_user(token) is None

    def test_revoke_session_absent_is_noop(self):
        web_users.revoke_session(None)
        web_users.revoke_session("nope")

    def test_logout_invalidates_session(self):
        token = web_users.issue_session("admin")
        web_users.logout(token)
        assert web_users.session_user(token) is None

    def test_clear_sessions_drops_everything(self):
        web_users.issue_session("admin")
        web_users.issue_session("other")
        web_users.clear_sessions()
        assert web_users._user_sessions == {}


# ---------------------------------------------------------------------------
# Validation constants
# ---------------------------------------------------------------------------


def test_validation_constants():
    assert web_users.USERNAME_MIN_LENGTH == 2
    assert web_users.PASSWORD_MIN_LENGTH == 6
    assert web_users.PBKDF2_ITERATIONS == 260_000
    assert web_users.SESSION_TTL_SECONDS == 7 * 24 * 3600
