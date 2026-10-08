## Context

`db_connection.py` provides `SQLiteConnectionManager`, a base class designed to be the single home for SQLite connection lifecycle across the project: WAL mode, `sqlite3.Row` + foreign keys, autocommit (`isolation_level=None`), jitter-retried `BEGIN IMMEDIATE` write transactions, periodic passive WAL checkpointing, read helpers (`query` / `query_one` / `scalar`), and `_on_connect()` / `_on_close()` lifecycle hooks.

Its docstring names three intended inheritors that were never migrated:

| Store | File | Current state |
|-------|------|---------------|
| `SessionDB` | `hermes_state.py` | Duplicates the entire write-retry loop (`_execute_write`), checkpointing (`_try_wal_checkpoint`), connection PRAGMAs, and `close()`. Own `threading.Lock`. |
| `ResponseStore` | `gateway/platforms/api_server.py` | Hand-rolled `sqlite3.connect` + PRAGMAs + tables, no locking, per-statement `commit()`. |
| `MemoryStore` | `plugins/memory/holographic/store.py` | Hand-rolled connection, own `threading.RLock`, per-statement `commit()`, `close()`, context manager. |

`tests/test_db_connection.py::test_inherited_by_session_db` currently fails (`issubclass(SessionDB, SQLiteConnectionManager)` is `False`).

External consumers of store internals must keep working, notably `plugins/memory/holographic/__init__.py:186` reading `self._store._conn.execute(...)` directly.

## Goals / Non-Goals

**Goals:**
- Make `SessionDB`, `ResponseStore`, and `MemoryStore` subclasses of `SQLiteConnectionManager`, exercising the same connection lifecycle, write-retry, checkpointing, and read helpers.
- Delete the duplicated connection/locking/transaction code from all three modules.
- Preserve all external attributes (`_conn`, `_lock`, `db_path`) and public method signatures.
- Keep storage semantics identical: WAL, FTS5 virtual tables, `sqlite3.Row`, foreign keys, autocommit.
- Fix `test_inherited_by_session_db` and add inheritance coverage for all three stores.

**Non-Goals:**
- Migrating `plugins/memory/retaindb` (its `_WriteQueue` is a dedicated single-writer-thread design, not listed among the base class's inheritors).
- Migrating transient/read-only connections in `hermes_cli/backup.py` and `hermes_cli/doctor.py` (one-shot tooling, different lifecycle).
- Introducing any external DB driver, ORM, or async DB layer.
- Changing schemas, column layouts, or on-disk formats.

## Decisions

### D1: Subclassing (not composition)
Each store becomes `class X(SQLiteConnectionManager)`. Rationale: the base class's contract (`_on_connect()`, transaction helpers, read helpers) is explicitly designed for inheritance, the docstring promises these three inheritors, and `test_inherited_by_session_db` encodes it. Composition would force every store to re-expose a wrapper object and leave `issubclass` assertions false.

### D2: All schema DDL lives in `_on_connect()`
`SessionDB._init_schema()` (tables + migrations + FTS5), `ResponseStore` table creation, and `MemoryStore._init_db()` (schema + `hrr_vector` migration) all move into `_on_connect()`, which the base calls once after opening the connection. The base explicitly allows DDL to use `self._conn` directly; only data access must go through the helpers/transactions.

### D3: `SessionDB` replaces `_execute_write` with `write_transaction`
`_execute_write(fn)` and base `write_transaction(fn)` are semantically identical (BEGIN IMMEDIATE → fn → commit, rollback on error, jitter retry, periodic checkpoint). Every `self._execute_write(...)` call becomes `self.write_transaction(...)`; return values are preserved (`rowcount`, `lastrowid`). The tuning constants (`_WRITE_MAX_RETRIES`, etc.) already live on the base class and are deleted from `SessionDB`.

### D4: `SessionDB` reads use the base helpers
`with self._lock: self._conn.execute(...)` read patterns become `query` / `query_one` / `scalar`. Where a method needs both a row and a cursor detail (`rowcount`), use `write_transaction` / `write` as appropriate. This is a mechanical rewrite; no query text changes.

### D5: `ResponseStore` keeps its `:memory:` fallback in `_open_connection()`
The base constructor accepts `":memory:"` (its `Path()` handling is harmless for the magic name). Override `_open_connection()` to catch connection failures and fall back to `sqlite3.connect(":memory:")` + `_configure_connection(conn)`, so the on-disk→in-memory degradation the class relies on survives the migration. Method bodies switch to `write_transaction` (e.g. `put`: insert + eviction count + delete atomically) and `query_one` / `scalar` / `write`.

### D6: `MemoryStore` preserves its `connect_timeout=10.0` and RLock semantics
The current connection uses `timeout=10.0`; the base default is `1.0`. Pass `connect_timeout=10.0` through the constructor so cross-process busy tolerance doesn't regress while still gaining the base's app-level jitter retry (strictly better than the current bare-`commit()` approach). The base uses `threading.RLock`, matching the store's existing reentrant lock, so no deadlock risk from converted call sites. `add_fact` and similar read-then-write methods become a single `write_transaction` (more atomic than today's separate lock + commit).

### D7: External attributes preserved
The base sets `self.db_path`, `self._conn`, `self._lock` in `__init__`, so `plugins/memory/holographic/__init__.py`'s direct `self._store._conn.execute(...)` access and any `store._lock` / `store.db_path` references keep working without edits.

### D8: Dead code/import removal
After migration, remove now-unused imports and helpers from the three modules (`random`, `threading`, `Callable`, `TypeVar`/`T` in `hermes_state.py`; the RLock-only `threading` import in `store.py`; `ResponseStore.close()`, `MemoryStore.close()`/`__enter__`/`__exit__`).

### D9: Test coverage for inheritance
Keep `test_inherited_by_session_db`; add sibling assertions that `ResponseStore` and `MemoryStore` subclass `SQLiteConnectionManager`. Lazy-import inside the tests (as the SessionDB one already does) to keep the base test file import-light. Existing behavioral tests (`tests/test_hermes_state.py`, `tests/gateway/test_api_server.py::TestResponseStore`) must stay green unchanged.

### Alternatives considered
- **Composition over inheritance** → rejected (D1 rationale; base is explicitly an inheritable base class).
- **Full rewrite of `db_connection.py`** → rejected; the module's design is sound and already tested (17 passing tests), the defect is purely that adopters never migrated.
- **Migrate `retaindb` `_WriteQueue`** → out of scope; it is a dedicated writer-thread design with its own reconnect semantics.

## Risks / Trade-offs

- **`SessionDB` lock-error message on retry exhaustion differs** (base raises generic `"database is locked after max retries"` vs. the old re-raised underlying error). → Mitigation: acceptable; the exception type (`sqlite3.OperationalError`) is unchanged, and retry exhaustion is a pathological state.
- **`ResponseStore` gains a lock it never had** → Mitigation: an `RLock` is a strict superset for the API server's single-event-loop usage; no behavior regression, and it makes the store's thread-safety explicit.
- **`MemoryStore` per-statement `commit()` removed inside transaction fns** → Mitigation: `write_transaction` owns commit/rollback; forgetting this is the main implementation hazard, so it is called out as the #1 review checkpoint in tasks.
- **Import-weight / dependency availability for new inheritance tests** → Mitigation: lazy imports inside test functions; aiohttp is already a test dependency and the memory plugin imports cleanly.
- **`_on_connect()` DDL errors would fail construction** → Mitigation: unchanged from today (schema errors already fail `__init__`); no regression.

## Migration Plan

Single-commit change; no schema or data migration:

1. Migrate `SessionDB` (`hermes_state.py`), run `tests/test_hermes_state.py` + `tests/test_db_connection.py`.
2. Migrate `ResponseStore` (`gateway/platforms/api_server.py`), run `tests/gateway/test_api_server.py`.
3. Migrate `MemoryStore` (`plugins/memory/holographic/store.py`), run memory plugin tests.
4. Add inheritance assertions; run the full suite.

Rollback: revert the commit — the three stores return to their previous self-contained implementations; no on-disk format changed.

## Open Questions

- None blocking. (Minor: whether `db_connection.py` should also absorb the transient read-only connections in `backup.py`/`doctor.py` — explicitly out of scope for this change.)
