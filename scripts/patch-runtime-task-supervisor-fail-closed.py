#!/usr/bin/env python3
from pathlib import Path

path = Path('webui/packages/desktop/src/main/runtime-task-supervisor.ts')
source = path.read_text(encoding='utf-8')

old_inspect = '''  private async inspectTasks(): Promise<void> {
    const now = this.now()
    const staleRuntimes = new Set<RuntimeKind>()
    for (const [key, record] of [...this.records]) {
      if (!record.process) {
        if (record.state === 'active' && now - record.lastHeartbeatAt >= this.heartbeatTtlMs) staleRuntimes.add(record.runtime)
        continue
      }
      const evidence = await this.processProbe.inspect(record.process.pid)
      if (!evidence || evidence.fingerprint !== record.process.fingerprint) {
        const result = this.coordinator.dispatch({
          type: 'process-exit', eventId: this.nextEventId('probe-exit'), observedAt: now, runtime: record.runtime,
          taskId: record.internalTaskId, leaseId: record.leaseId, exitCode: null, signal: null,
        })
        if (result.ok) this.records.delete(key)
        continue
      }
      if (record.state === 'active' && now - record.lastHeartbeatAt >= this.heartbeatTtlMs) staleRuntimes.add(record.runtime)
    }
    for (const runtime of staleRuntimes) this.markRuntimeOrphaned(runtime, 'heartbeat-timeout')
    this.persist()
  }
'''

new_inspect = '''  private async inspectTasks(): Promise<void> {
    const now = this.now()
    const staleRuntimes = new Set<RuntimeKind>()
    for (const [key, record] of [...this.records]) {
      // Orphaned tasks intentionally remain fail-closed. A missing or reused PID is
      // not sufficient evidence to release their workspace after Runtime/Main loss;
      // only an explicit process-exit confirmation or verified resume may do so.
      if (record.state === 'orphaned') continue
      if (!record.process) {
        if (now - record.lastHeartbeatAt >= this.heartbeatTtlMs) staleRuntimes.add(record.runtime)
        continue
      }
      const evidence = await this.processProbe.inspect(record.process.pid)
      if (!evidence || evidence.fingerprint !== record.process.fingerprint) {
        const result = this.coordinator.dispatch({
          type: 'process-exit', eventId: this.nextEventId('probe-exit'), observedAt: now, runtime: record.runtime,
          taskId: record.internalTaskId, leaseId: record.leaseId, exitCode: null, signal: null,
        })
        if (result.ok) this.records.delete(key)
        continue
      }
      if (now - record.lastHeartbeatAt >= this.heartbeatTtlMs) staleRuntimes.add(record.runtime)
    }
    for (const runtime of staleRuntimes) this.markRuntimeOrphaned(runtime, 'heartbeat-timeout')
    this.persist()
  }
'''

old_restore = '''  private async restorePersistedTasks(): Promise<void> {
    const persisted = this.readState()
    const activeRuntimes = new Set<RuntimeKind>()
    for (const item of persisted.generations) {
      if (item.runtime !== 'deepagent' || !validString(item.taskId) || !Number.isSafeInteger(item.generation) || item.generation < 1) continue
      this.generations.set(stableTaskKey(item.runtime, item.taskId), item.generation)
    }
    for (const task of persisted.tasks) {
      if (!validRuntime(task.runtime) || !validAccess(task.access) || !validString(task.taskId) || !validString(task.workspace, 4_096)) continue
      if (!task.process || !validPid(task.process.pid) || !validString(task.process.fingerprint, 128)) continue
      const evidence = await this.processProbe.inspect(task.process.pid)
      if (!evidence || evidence.fingerprint !== task.process.fingerprint) continue
      const key = stableTaskKey(task.runtime, task.taskId)
      const generation = task.runtime === 'deepagent'
        ? Math.max(1, task.generation || 1, this.generations.get(key) || 0)
        : Math.max(1, task.generation || 1)
      if (task.runtime === 'deepagent') this.generations.set(key, generation)
      const internalTaskId = safeInternalTaskId(task.runtime, task.taskId, generation)
      const acquired = this.adapters[task.runtime].dispatch({
        type: 'acquire', eventId: this.nextEventId('restore-acquire'), observedAt: this.now(), ttlMs: this.heartbeatTtlMs,
        identity: { workspace: task.workspace, taskId: internalTaskId, access: task.access },
      })
      if (!acquired.ok || !acquired.lease) continue
      const bound = this.coordinator.dispatch({
        type: 'bind-process', eventId: this.nextEventId('restore-bind'), observedAt: this.now(), runtime: task.runtime,
        taskId: internalTaskId, leaseId: acquired.lease.leaseId,
        process: { pid: evidence.pid, treeId: evidence.fingerprint.slice(0, 32) },
      })
      if (!bound.ok) continue
      this.records.set(key, {
        ...task, workspace: resolve(task.workspace), state: 'active', leaseId: acquired.lease.leaseId,
        internalTaskId, process: evidence, lastHeartbeatAt: this.now(), generation,
      })
      activeRuntimes.add(task.runtime)
    }
    for (const runtime of activeRuntimes) this.markRuntimeOrphaned(runtime, 'main-restart')
    this.persist()
  }
'''

new_restore = '''  private async restorePersistedTasks(): Promise<void> {
    const persisted = this.readState()
    const activeRuntimes = new Set<RuntimeKind>()
    for (const item of persisted.generations) {
      if (item.runtime !== 'deepagent' || !validString(item.taskId) || !Number.isSafeInteger(item.generation) || item.generation < 1) continue
      this.generations.set(stableTaskKey(item.runtime, item.taskId), item.generation)
    }
    for (const task of persisted.tasks) {
      if (!validRuntime(task.runtime) || !validAccess(task.access) || !validString(task.taskId) || !validString(task.workspace, 4_096)) continue
      if (task.process && (!validPid(task.process.pid) || !validString(task.process.fingerprint, 128))) continue
      const evidence = task.process ? await this.processProbe.inspect(task.process.pid) : null
      const processVerified = Boolean(evidence && task.process && evidence.fingerprint === task.process.fingerprint)
      const key = stableTaskKey(task.runtime, task.taskId)
      const generation = task.runtime === 'deepagent'
        ? Math.max(1, task.generation || 1, this.generations.get(key) || 0)
        : Math.max(1, task.generation || 1)
      if (task.runtime === 'deepagent') this.generations.set(key, generation)
      const internalTaskId = safeInternalTaskId(task.runtime, task.taskId, generation)
      const acquired = this.adapters[task.runtime].dispatch({
        type: 'acquire', eventId: this.nextEventId('restore-acquire'), observedAt: this.now(), ttlMs: this.heartbeatTtlMs,
        identity: { workspace: task.workspace, taskId: internalTaskId, access: task.access },
      })
      if (!acquired.ok || !acquired.lease) continue
      if (processVerified && evidence) {
        const bound = this.coordinator.dispatch({
          type: 'bind-process', eventId: this.nextEventId('restore-bind'), observedAt: this.now(), runtime: task.runtime,
          taskId: internalTaskId, leaseId: acquired.lease.leaseId,
          process: { pid: evidence.pid, treeId: evidence.fingerprint.slice(0, 32) },
        })
        if (!bound.ok) {
          this.adapters[task.runtime].dispatch({
            type: 'release', eventId: this.nextEventId('restore-bind-rollback'), observedAt: this.now(),
            taskId: internalTaskId, leaseId: acquired.lease.leaseId,
          })
          continue
        }
      }
      this.records.set(key, {
        ...task, workspace: resolve(task.workspace), state: 'active', leaseId: acquired.lease.leaseId,
        internalTaskId,
        process: processVerified && evidence ? evidence : task.process ? { ...task.process } : undefined,
        lastHeartbeatAt: this.now(), generation,
      })
      activeRuntimes.add(task.runtime)
    }
    for (const runtime of activeRuntimes) this.markRuntimeOrphaned(runtime, 'main-restart')
    this.persist()
  }
'''

if source.count(old_inspect) != 1:
    raise SystemExit('inspectTasks source contract changed; refusing patch')
if source.count(old_restore) != 1:
    raise SystemExit('restorePersistedTasks source contract changed; refusing patch')

source = source.replace(old_inspect, new_inspect).replace(old_restore, new_restore)
path.write_text(source, encoding='utf-8')
print(f'patched {path}')
