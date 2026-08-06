## ADDED Requirements

### Requirement: All SQLite stores use the shared connection manager

Every SQLite-backed store in the project (`SessionDB` in `hermes_state.py`, `ResponseStore` in `gateway/platforms/api_server.py`, `MemoryStore` in `plugins/memory/holographic/store.py`) SHALL subclass `SQLiteConnectionManager` from `db_connection.py` instead of hand-rolling connection setup, locking, transaction retry, and checkpointing.

#### Scenario: SessionDB inherits the manager
- **WHEN** a developer checks the class hierarchy of `SessionDB`
- **THEN** `SessionDB` is a subclass of `SQLiteConnectionManager`

#### Scenario: ResponseStore inherits the manager
- **WHEN** a developer checks the class hierarchy of `ResponseStore`
- **THEN** `ResponseStore` is a subclass of `SQLiteConnectionManager`

#### Scenario: MemoryStore inherits the manager
- **WHEN** a developer checks the class hierarchy of `MemoryStore`
- **THEN** `MemoryStore` is a subclass of `SQLiteConnectionManager`

### Requirement: Connection lifecycle is centralized in the manager

The `SQLiteConnectionManager` SHALL be the single place that opens and configures connections: WAL journal mode, `sqlite3.Row` row factory, `PRAGMA foreign_keys=ON`, and autocommit mode (`isolation_level=None`). Stores SHALL create their schema inside the `_on_connect()` lifecycle hook, and `close()` SHALL be idempotent and issue a final best-effort passive WAL checkpoint.

#### Scenario: Connection applies shared PRAGMAs
- **WHEN** a store opens its connection
- **THEN** the connection uses WAL journal mode, `sqlite3.Row` rows, foreign keys enabled, and autocommit mode

#### Scenario: Schema is created via the lifecycle hook
- **WHEN** a store is constructed
- **THEN** its tables, indexes, FTS virtual tables, and migrations run inside `_on_connect()` exactly once

#### Scenario: Close is idempotent and checkpoints
- **WHEN** a store's `close()` is called multiple times
- **THEN** the connection is released once, the connection is marked closed, and a final passive checkpoint is attempted without raising

### Requirement: Write transactions use jitter-retried BEGIN IMMEDIATE

All write paths in the stores SHALL run through the manager's `write_transaction()`, which acquires the WAL write lock with `BEGIN IMMEDIATE`, commits on success, rolls back on error, and retries on lock contention using random jitter (20–150 ms) up to a bounded number of attempts. A passive WAL checkpoint SHALL run periodically outside the write lock.

#### Scenario: Write commits atomically
- **WHEN** a store performs a write via `write_transaction`
- **THEN** the statements are committed atomically and the transaction's return value is returned to the caller

#### Scenario: Write rolls back on error
- **WHEN** the transaction callback raises
- **THEN** the partial statements are rolled back and the original exception propagates

#### Scenario: Lock contention is retried
- **WHEN** an external connection holds the WAL write lock
- **THEN** the write retries with jitter and succeeds once the lock is released

#### Scenario: Retries are bounded
- **WHEN** the write lock remains held for the full retry budget
- **THEN** a `sqlite3.OperationalError` is raised instead of hanging indefinitely

### Requirement: Reads use thread-safe helper methods

Stores SHALL perform ordinary reads through the manager's `query`, `query_one`, and `scalar` helpers, which serialize against writers and materialize results inside the read lock so returned rows stay valid afterwards.

#### Scenario: Read helpers return materialized rows
- **WHEN** a store runs a `SELECT` through the read helpers
- **THEN** all rows are fully materialized before the lock is released and remain usable

### Requirement: Store internals stay accessible

Migrating a store to the manager SHALL preserve the externally visible `_conn`, `_lock`, and `db_path` attributes so existing consumers (for example `plugins/memory/holographic/__init__.py`) keep working without modification.

#### Scenario: Existing internal attribute access keeps working
- **WHEN** code accesses `store._conn`, `store._lock`, or `store.db_path` after migration
- **THEN** the attributes exist and behave as before

### Requirement: ResponseStore preserves its in-memory fallback

`ResponseStore` SHALL degrade to an in-memory SQLite database when its on-disk connection cannot be opened, implemented by overriding the manager's `_open_connection()`.

#### Scenario: On-disk open fails
- **WHEN** `ResponseStore` cannot open its on-disk database file
- **THEN** it opens an in-memory SQLite connection with the same PRAGMA configuration instead of failing construction
