## Why

`db_connection.py` ships a `SQLiteConnectionManager` base class that centralizes SQLite connection lifecycle (WAL, `sqlite3.Row`, foreign keys, jitter-retried `BEGIN IMMEDIATE` writes, passive checkpointing, read helpers), but the three stores its docstring names as inheritors — `SessionDB`, `ResponseStore`, and `MemoryStore` — never migrated. They still hand-roll their own connection setup, lock handling, write-retry loops, and checkpointing, so the maintenance burden and behavioral drift the module was created to eliminate remain, and `tests/test_db_connection.py::test_inherited_by_session_db` fails.

## What Changes

- **Migrate `SessionDB`** (`hermes_state.py`) to subclass `SQLiteConnectionManager`:
  - Move schema creation + version migrations into the `_on_connect()` hook.
  - Replace the private `_execute_write()` jitter-retry loop and `_try_wal_checkpoint()` with the base `write_transaction()` / checkpointing.
  - Replace direct `with self._lock: self._conn.execute(...)` reads with the base `query` / `query_one` / `scalar` helpers.
  - Drop duplicated `__init__` connection setup, `close()`, and tuning constants.
- **Migrate `ResponseStore`** (`gateway/platforms/api_server.py`) to subclass `SQLiteConnectionManager`:
  - Table creation moves into `_on_connect()`.
  - `get` / `put` / `delete` / `get_conversation` / `set_conversation` / `__len__` use the base helpers and transactions.
  - Preserve the on-disk→`:memory:` fallback via a `_open_connection()` override.
  - Remove the hand-rolled `close()`.
- **Migrate `MemoryStore`** (`plugins/memory/holographic/store.py`) to subclass `SQLiteConnectionManager`:
  - Schema + `hrr_vector` migration move into `_on_connect()`.
  - Read/write paths use `query` / `query_one` / `scalar` and `write_transaction`; remove per-statement `commit()` calls.
  - Remove the duplicate `close()` / context manager.
- **Remove dead imports** (`random`, `threading`, etc.) left over in the migrated modules.
- **Extend `tests/test_db_connection.py`** to assert `SessionDB`, `ResponseStore`, and `MemoryStore` all subclass `SQLiteConnectionManager`; keep existing store behavior tests green.

## Capabilities

### New Capabilities
- `sqlite-connection-manager`: The shared `SQLiteConnectionManager` base class in `db_connection.py` and its adoption by all SQLite-backed stores (`SessionDB`, `ResponseStore`, `MemoryStore`) — a single source of truth for connection lifecycle, WAL, transactional writes, and read helpers.

### Modified Capabilities
- (none — no existing specs)

## Impact

- **Code**: `db_connection.py` (unchanged API surface; minor hardening if needed), `hermes_state.py`, `gateway/platforms/api_server.py`, `plugins/memory/holographic/store.py`, `tests/test_db_connection.py`.
- **Behavior**: identical storage semantics (WAL, FTS5, `sqlite3.Row`, foreign keys, autocommit mode). `MemoryStore`'s effective SQLite busy timeout changes from 10s to base `connect_timeout=1.0` + app-level jitter retry unless preserved via `connect_timeout`; `ResponseStore` and `SessionDB` gain the same retry semantics they already had.
- **Public attributes**: `_conn`, `_lock`, `db_path` are preserved on all three stores, so existing external accesses (e.g. `plugins/memory/holographic/__init__.py` reading `_store._conn`) keep working.
- **Tests**: `tests/test_db_connection.py`, `tests/test_hermes_state.py`, `tests/gateway/test_api_server.py`, `tests/plugins/...`.
