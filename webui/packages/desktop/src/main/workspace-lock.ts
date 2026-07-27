import { resolve } from 'node:path'

export type WorkspaceAccess = 'read' | 'write'

type LockState = {
  writer: string | null
  readers: Set<string>
}

export class WorkspaceLockManager {
  private readonly locks = new Map<string, LockState>()

  acquire(workspace: string, taskId: string, access: WorkspaceAccess): boolean {
    if (!workspace || !taskId || !/^[A-Za-z0-9._:-]{1,128}$/.test(taskId)) return false
    const key = resolve(workspace)
    const state = this.locks.get(key) ?? { writer: null, readers: new Set<string>() }

    if (access === 'write') {
      // A writer is exclusive. A task may upgrade its own read lock only when
      // no other readers are present.
      if (state.writer && state.writer !== taskId) return false
      if ([...state.readers].some(reader => reader !== taskId)) return false
      state.readers.delete(taskId)
      state.writer = taskId
    } else {
      // Readers may run concurrently, but never alongside another task's writer.
      // Re-entrant read access by the current writer is treated as already held.
      if (state.writer && state.writer !== taskId) return false
      if (!state.writer) state.readers.add(taskId)
    }

    this.locks.set(key, state)
    return true
  }

  release(workspace: string, taskId: string): void {
    const key = resolve(workspace)
    const state = this.locks.get(key)
    if (!state) return
    if (state.writer === taskId) state.writer = null
    state.readers.delete(taskId)
    if (!state.writer && state.readers.size === 0) this.locks.delete(key)
  }

  releaseTask(taskId: string): void {
    for (const [workspace, state] of this.locks) {
      if (state.writer === taskId) state.writer = null
      state.readers.delete(taskId)
      if (!state.writer && state.readers.size === 0) this.locks.delete(workspace)
    }
  }

  status(workspace: string): { writer: string | null; readers: string[] } {
    const state = this.locks.get(resolve(workspace))
    return state
      ? { writer: state.writer, readers: [...state.readers].sort() }
      : { writer: null, readers: [] }
  }
}
