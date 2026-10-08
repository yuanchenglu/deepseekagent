"""Local dashboard account store — password login and first-run registration.

Pure logic, zero FastAPI/HTTP dependencies.  The account store and login
sessions live here as a plain callable "quick interface" so the route handlers
in ``web_server.py`` stay thin and unit tests can drive the whole feature
without a running server.

High-level quick interface::

    register(username, password, email, phone) -> Optional[str]  # session token
    login(login, password)                     -> Optional[str]  # session token
    logout(token)                              -> None
    session_user(token)                        -> Optional[str]
    has_users()                                -> bool

Lower-level primitives (on-disk store + session tokens) are exposed too for
callers that need finer control — e.g. the FastAPI handlers map the ``None``
results above to the appropriate HTTP status codes.

Security notes:
    - Passwords are hashed with PBKDF2-HMAC-SHA256 (260k iterations) and a
      per-user random salt; the store lives at ``HERMES_HOME/web_users.json``
      with ``0600`` permissions.
    - Login sessions are short-lived in-memory tokens — they die with the
      server process.
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

from hermes_constants import get_hermes_home

PBKDF2_ITERATIONS = 260_000
SESSION_TTL_SECONDS = 7 * 24 * 3600  # 7 days
USERNAME_MIN_LENGTH = 2
PASSWORD_MIN_LENGTH = 6

_user_sessions: dict[str, dict[str, Any]] = {}  # token -> {username, expires_at}


def users_path() -> Path:
    """Path of the on-disk account store for the active profile."""
    return get_hermes_home() / "web_users.json"


# ---------------------------------------------------------------------------
# Account store
# ---------------------------------------------------------------------------


def load_users() -> dict[str, dict[str, Any]]:
    """Return the on-disk account records keyed by username."""
    path = users_path()
    try:
        data = json.loads(path.read_text())
        users = data.get("users", {}) if isinstance(data, dict) else {}
    except (FileNotFoundError, ValueError, OSError):
        return {}
    return {
        name: record for name, record in users.items()
        if isinstance(record, dict) and record.get("salt") and record.get("hash")
    }


def has_users() -> bool:
    """Whether any account exists yet — drives first-run setup in the UI."""
    return bool(load_users())


def save_user(username: str, password: str, email: str = "", phone: str = "") -> None:
    """Create (or update) a user with a PBKDF2-hashed password."""
    salt = secrets.token_bytes(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    users = load_users()
    users[username] = {
        "username": username,
        "email": email or "",
        "phone": phone or "",
        "salt": salt.hex(),
        "hash": pw_hash.hex(),
        "created_at": int(time.time()),
    }
    path = users_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"users": users}, indent=2))
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def find_user_by_login(login: str) -> str | None:
    """Resolve a login identifier (username / email / phone) to a username."""
    login = login.strip().lower()
    for name, record in load_users().items():
        if (
            name.lower() == login
            or str(record.get("email") or "").lower() == login
            or str(record.get("phone") or "").lower() == login
        ):
            return name
    return None


def verify_password(username: str, password: str) -> bool:
    """Constant-time check of a password against the stored hash."""
    record = load_users().get(username)
    if not record:
        return False
    try:
        salt = bytes.fromhex(record["salt"])
        expected = bytes.fromhex(record["hash"])
    except (ValueError, KeyError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return hmac.compare_digest(actual, expected)


# ---------------------------------------------------------------------------
# Login sessions
# ---------------------------------------------------------------------------


def issue_session(username: str) -> str:
    """Create a login session and return its bearer token."""
    token = secrets.token_urlsafe(32)
    _user_sessions[token] = {"username": username, "expires_at": time.time() + SESSION_TTL_SECONDS}
    return token


def session_user(token: str | None) -> str | None:
    """Username behind a session token, or ``None`` when missing/expired."""
    if not token:
        return None
    record = _user_sessions.get(token)
    if not record:
        return None
    if record["expires_at"] < time.time():
        _user_sessions.pop(token, None)
        return None
    return record["username"]


def revoke_session(token: str | None) -> None:
    """Invalidate a single session token (no-op when absent)."""
    if token:
        _user_sessions.pop(token, None)


def clear_sessions() -> None:
    """Drop all login sessions (used by tests and logout-all)."""
    _user_sessions.clear()


# ---------------------------------------------------------------------------
# High-level quick interface
# ---------------------------------------------------------------------------


def register(username: str, password: str, email: str = "", phone: str = "") -> str | None:
    """Create the first account and return a live session token.

    Returns ``None`` when an account already exists (subsequent registrations
    are rejected).  Length validation is the caller's job so it can map
    failures to the right HTTP status code.
    """
    username = username.strip()
    if has_users():
        return None
    save_user(username, password, (email or "").strip(), (phone or "").strip())
    return issue_session(username)


def login(login: str, password: str) -> str | None:
    """Authenticate by username / email / phone.

    Returns a live session token, or ``None`` when the credentials are
    invalid or the account does not exist.
    """
    username = find_user_by_login(login)
    if username is None or not verify_password(username, password):
        return None
    return issue_session(username)


def logout(token: str | None) -> None:
    """Invalidate the given session token (no-op when absent)."""
    revoke_session(token)
