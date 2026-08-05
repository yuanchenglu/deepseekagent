import { resolve } from 'node:path'

export type WorkspaceAccess = 'read' | 'write'

export interface WorkspaceLockHolder {
  ownerId: string
  taskId: string
}

type LockState = {
  writer: WorkspaceLockHolder | null
  readers: Map<string, WorkspaceLockHolder>
}

const IDENTIFIER_PATTERN = /^[A-Za-z0-9._:-]{1,128}$/
const LEGACY_OWNER = 'legacy'

function holderKey(ownerId: string, taskId: string): string {
  return `${ownerId}\u0000${taskId}`
}

function validIdentifier(value: string): boolean {
  return IDENTIFIER_PATTERN.test(value)
}

export class WorkspaceLockManager {
  private readonly locks = new Map<string, LockState>()

  acquire(
    workspace: string,
    taskId: string,
    access: WorkspaceAccess,
    ownerId = LEGACY_OWNER,
  ): boolean {
    if (!workspace || !validIdentifier(taskId) || !validIdentifier(ownerId)) return false

    const key = resolve(workspace)
    const holder: WorkspaceLockHolder = { ownerId, taskId }
    const holderId = holderKey(ownerId, taskId)
    const state = this.locks.get(key) ?? {
      writer: null,
      readers: new Map<string, WorkspaceLockHolder>(),
    }

    if (access === 'write') {
      const writerId = state.writer
        ? holderKey(state.writer.ownerId, state.writer.taskId)
        : null
      if (writerId && writerId !== holderId) return false
      if ([...state.readers.keys()].some(readerId => readerId !== holderId)) return false

      state.readers.delete(holderId)
      state.writer = holder
    } else {
      const writerId = state.writer
        ? holderKey(state.writer.ownerId, state.writer.taskId)
        : null
      if (writerId && writerId !== holderId) return false
      if (!state.writer) state.readers.set(holderId, holder)
    }

    this.locks.set(key, state)
    return true
  }

  release(workspace: string, taskId: string, ownerId = LEGACY_OWNER): void {
    if (!workspace || !validIdentifier(taskId) || !validIdentifier(ownerId)) return

    const key = resolve(workspace)
    const state = this.locks.get(key)
    if (!state) return

    const holderId = holderKey(ownerId, taskId)
    if (state.writer && holderKey(state.writer.ownerId, state.writer.taskId) === holderId) {
      state.writer = null
    }
    state.readers.delete(holderId)
    if (!state.writer && state.readers.size === 0) this.locks.delete(key)
  }

  releaseTask(taskId: string, ownerId = LEGACY_OWNER): void {
    if (!validIdentifier(taskId) || !validIdentifier(ownerId)) return
    const holderId = holderKey(ownerId, taskId)

    for (const [workspace, state] of this.locks) {
      if (state.writer && holderKey(state.writer.ownerId, state.writer.taskId) === holderId) {
        state.writer = null
      }
      state.readers.delete(holderId)
      if (!state.writer && state.readers.size === 0) this.locks.delete(workspace)
    }
  }

  releaseOwner(ownerId: string): void {
    if (!validIdentifier(ownerId)) return

    for (const [workspace, state] of this.locks) {
      if (state.writer?.ownerId === ownerId) state.writer = null
      for (const [readerId, reader] of state.readers) {
        if (reader.ownerId === ownerId) state.readers.delete(readerId)
      }
      if (!state.writer && state.readers.size === 0) this.locks.delete(workspace)
    }
  }

  status(workspace: string): { writer: string | null; readers: string[] } {
    const state = this.locks.get(resolve(workspace))
    return state
      ? {
          writer: state.writer?.taskId ?? null,
          readers: [...state.readers.values()].map(reader => reader.taskId).sort(),
        }
      : { writer: null, readers: [] }
  }

  detailedStatus(workspace: string): {
    writer: WorkspaceLockHolder | null
    readers: WorkspaceLockHolder[]
  } {
    const state = this.locks.get(resolve(workspace))
    return state
      ? {
          writer: state.writer ? { ...state.writer } : null,
          readers: [...state.readers.values()]
            .map(reader => ({ ...reader }))
            .sort((left, right) => holderKey(left.ownerId, left.taskId).localeCompare(holderKey(right.ownerId, right.taskId))),
        }
      : { writer: null, readers: [] }
  }
}
