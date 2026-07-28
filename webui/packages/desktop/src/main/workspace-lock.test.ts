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

  it('enforces reader and writer exclusion in both directions', () => {
    const locks = new WorkspaceLockManager()
    expect(locks.acquire('/tmp/project', 'read-1', 'read')).toBe(true)
    expect(locks.acquire('/tmp/project', 'write-1', 'write')).toBe(false)
    locks.release('/tmp/project', 'read-1')

    expect(locks.acquire('/tmp/project', 'write-1', 'write')).toBe(true)
    expect(locks.acquire('/tmp/project', 'read-2', 'read')).toBe(false)
  })

  it('allows a task to upgrade its own read lock when it is the only reader', () => {
    const locks = new WorkspaceLockManager()
    expect(locks.acquire('/tmp/project', 'task-1', 'read', 'renderer:1')).toBe(true)
    expect(locks.acquire('/tmp/project', 'task-1', 'write', 'renderer:1')).toBe(true)
    expect(locks.detailedStatus('/tmp/project')).toEqual({
      writer: { ownerId: 'renderer:1', taskId: 'task-1' },
      readers: [],
    })
  })

  it('does not let another owner release a lock with the same task id', () => {
    const locks = new WorkspaceLockManager()
    expect(locks.acquire('/tmp/project', 'shared-task', 'write', 'renderer:1')).toBe(true)

    locks.release('/tmp/project', 'shared-task', 'renderer:2')
    locks.releaseTask('shared-task', 'renderer:2')

    expect(locks.detailedStatus('/tmp/project')).toEqual({
      writer: { ownerId: 'renderer:1', taskId: 'shared-task' },
      readers: [],
    })
  })

  it('releases only the destroyed owner leases', () => {
    const locks = new WorkspaceLockManager()
    expect(locks.acquire('/tmp/project-a', 'task-a', 'read', 'renderer:1')).toBe(true)
    expect(locks.acquire('/tmp/project-a', 'task-b', 'read', 'renderer:2')).toBe(true)
    expect(locks.acquire('/tmp/project-b', 'task-c', 'write', 'renderer:1')).toBe(true)

    locks.releaseOwner('renderer:1')

    expect(locks.detailedStatus('/tmp/project-a')).toEqual({
      writer: null,
      readers: [{ ownerId: 'renderer:2', taskId: 'task-b' }],
    })
    expect(locks.status('/tmp/project-b')).toEqual({ writer: null, readers: [] })
  })

  it('releases all workspaces owned by a completed task', () => {
    const locks = new WorkspaceLockManager()
    locks.acquire('/tmp/project-a', 'task-1', 'write', 'renderer:1')
    locks.acquire('/tmp/project-b', 'task-1', 'read', 'renderer:1')
    locks.acquire('/tmp/project-b', 'task-1', 'read', 'renderer:2')

    locks.releaseTask('task-1', 'renderer:1')

    expect(locks.acquire('/tmp/project-a', 'task-2', 'write', 'renderer:2')).toBe(true)
    expect(locks.detailedStatus('/tmp/project-b')).toEqual({
      writer: null,
      readers: [{ ownerId: 'renderer:2', taskId: 'task-1' }],
    })
  })

  it('rejects malformed task and owner identifiers', () => {
    const locks = new WorkspaceLockManager()
    expect(locks.acquire('/tmp/project', '../task', 'write')).toBe(false)
    expect(locks.acquire('/tmp/project', 'task', 'write', '../owner')).toBe(false)
    expect(locks.acquire('', 'task', 'write')).toBe(false)
  })
})
