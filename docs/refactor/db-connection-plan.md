# 数据库连接模块重构计划

## 现状分析

`db_connection.py` — `SQLiteConnectionManager` 类，271 行。
- WAL 模式 + 写事务重试（jitter 退避）
- `write_transaction()` / `read_transaction()` / `transaction()`
- 被动 Checkpoint（每 50 次写触发）

继承者：
- `SessionDB` (hermes_state.py)
- `ResponseStore` (gateway/platforms/api_server.py)
- `MemoryStore` (plugins/memory/holographic/store.py)

## 问题清单

### 1. `_on_connect()` 在 `open()` 中调用但无对称的 `_on_close()` 钩子
`_on_connect()` 在连接建立后调用，用于执行 DDL/迁移。但 `close()` 没有对应的 `_on_close()` 生命周期钩子。继承类如需做关闭前的清理（如刷缓冲区），只能重写 `close()` 整个方法。

### 2. Checkpoint 在写锁内部执行，徒增锁竞争
```python
try:
    result = fn(conn)
    conn.commit()
except Exception:
    conn.rollback()
    raise
self._write_count += 1
if self._write_count % self._CHECKPOINT_EVERY_N_WRITES == 0:
    self._try_wal_checkpoint()  # ← 还在锁内
return result
```
`PRAGMA wal_checkpoint(PASSIVE)` 不需要写锁，可以移到锁外。

### 3. `close()` 没有剩余 checkpoint
当前 `close()` 在锁内做了一次 passive checkpoint 后关闭。问题不大。

### 4. `_try_wal_checkpoint()` 内部重复获取 `self._lock`
`_try_wal_checkpoint()` 内部做了 `with self._lock:`，但此函数已经假设在锁内或锁外可调用。目前只被 `write_transaction` 调用（已在锁内），所以内部锁是空操作。但如果将来在其他地方调用会出错。

## 重构步骤

### Step 1: 添加 `_on_close()` 钩子
- 与 `_on_connect()` 对称，`close()` 中调用
- 默认空实现

### Step 2: 将 WAL checkpoint 移出写锁
- `_try_wal_checkpoint()` 不再在锁内调用
- 使用独立锁（`_checkpoint_lock`）保护 checkpoint 计数，减小临界区

### Step 3: 清理 `_try_wal_checkpoint()` 的锁
- 去掉内部 `self._lock` 获取，改为仅在需要时获取 `_checkpoint_lock`
- 明确函数契约：调用者不需要持有任何锁

### Step 4: 验证
- 运行 `tests/test_db_connection.py` 全量测试
- 运行 `tests/test_hermes_state.py` 验证下游不受影响
