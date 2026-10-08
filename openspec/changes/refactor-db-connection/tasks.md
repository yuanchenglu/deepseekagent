## 1. Migrate SessionDB (hermes_state.py)

- [ ] 1.1 Make `SessionDB` subclass `SQLiteConnectionManager`; replace `__init__` connection setup with `super().__init__(db_path or DEFAULT_DB_PATH)`
- [ ] 1.2 Rename `_init_schema()` to `_on_connect()` (schema DDL, version migrations, FTS5 setup; may keep using `self._conn` for DDL)
- [ ] 1.3 Delete `_execute_write()`, `_try_wal_checkpoint()`, `close()`, and the tuning constants; replace every `self._execute_write(...)` call with `self.write_transaction(...)`
- [ ] 1.4 Replace all `with self._lock: ... self._conn.execute(...)` read blocks with `query` / `query_one` / `scalar` helpers
- [ ] 1.5 Remove dead imports (`random`, `threading`, `Callable`, `TypeVar`/`T`) and stray attribute setup left unused

## 2. Migrate ResponseStore (gateway/platforms/api_server.py)

- [ ] 2.1 Make `ResponseStore` subclass `SQLiteConnectionManager`; resolve `db_path` (with `:memory:` default) then call `super().__init__(db_path)`
- [ ] 2.2 Move table creation into `_on_connect()`
- [ ] 2.3 Override `_open_connection()` to fall back to an in-memory connection on failure
- [ ] 2.4 Rewrite `get` / `put` / `delete` / `get_conversation` / `set_conversation` / `__len__` using `write_transaction`, `query_one`, `scalar`, and `write`; remove per-statement `commit()` calls
- [ ] 2.5 Remove the hand-rolled `close()` (base class handles idempotent close + final checkpoint)

## 3. Migrate MemoryStore (plugins/memory/holographic/store.py)

- [ ] 3.1 Make `MemoryStore` subclass `SQLiteConnectionManager`; keep `db_path` / `default_trust` / `hrr_dim` attributes, pass `connect_timeout=10.0`
- [ ] 3.2 Move `_init_db()` schema + `hrr_vector` migration into `_on_connect()`
- [ ] 3.3 Convert read paths to `query` / `query_one` / `scalar` / `read_transaction` and write paths (including `add_fact`, feedback, entity, and bank methods) to `write_transaction`, removing per-statement `commit()`
- [ ] 3.4 Remove duplicate `close()`, `__enter__`, `__exit__`, and the now-unused `threading` import
- [ ] 3.5 Verify `plugins/memory/holographic/__init__.py` `_store._conn` access still works (spec: store internals preserved)

## 4. Tests

- [ ] 4.1 Extend `tests/test_db_connection.py` so `SessionDB`, `ResponseStore`, and `MemoryStore` all assert `issubclass(..., SQLiteConnectionManager)` (lazy imports)
- [ ] 4.2 Run `tests/test_db_connection.py`, `tests/test_hermes_state.py`, and `tests/gateway/test_api_server.py` — all existing behavioral tests stay green

## 5. Verification

- [ ] 5.1 Run the full pytest suite and confirm no regressions
- [ ] 5.2 Grep for leftover duplicated connection code (`BEGIN IMMEDIATE`, `journal_mode=WAL`, `wal_checkpoint`) outside `db_connection.py` and the stores' intended migrations
