import { describe, expect, it } from 'vitest'
import { WorkspaceLockManager } from './workspace-lock'

describe('WorkspaceLockManager', () => {
  it('allows only one writer for the same workspace', () => {
    const locks = new WorkspaceLockManager()
    expect(locks.acquire('/tmp/project', 'write-1', 'write')).toBe(true)
    expect(locks.acquire('/tmp/project', 'write-2', 'write')).toBe(false)
    expect(locks.acquire('/tmp/other', 'write-2', 'write')).toBe(true)
  })

  it('allows parallel read-only tasks', () => {
    const locks = new WorkspaceLockManager()
    expect(locks.acquire('/tmp/project', 'read-1', 'read')).toBe(true)
    expect(locks.acquire('/tmp/project', 'read-2', 'read')).toBe(true)
    expect(locks.status('/tmp/project')).toEqual({ writer: null, readers: ['read-1', 'read-2'] })
  })

  it('releases all workspaces owned by a completed task', () => {
    const locks = new WorkspaceLockManager()
    locks.acquire('/tmp/project-a', 'task-1', 'write')
    locks.acquire('/tmp/project-b', 'task-1', 'read')

    locks.releaseTask('task-1')

    expect(locks.acquire('/tmp/project-a', 'task-2', 'write')).toBe(true)
    expect(locks.status('/tmp/project-b')).toEqual({ writer: null, readers: [] })
  })

  it('rejects malformed task identifiers', () => {
    const locks = new WorkspaceLockManager()
    expect(locks.acquire('/tmp/project', '../task', 'write')).toBe(false)
    expect(locks.acquire('', 'task', 'write')).toBe(false)
  })
})
