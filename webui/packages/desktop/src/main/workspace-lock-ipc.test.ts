import { EventEmitter } from 'node:events'
import { describe, expect, it } from 'vitest'
import {
  registerWorkspaceLockIpc,
  WORKSPACE_LOCK_CHANNELS,
  type WorkspaceLockIpcEvent,
  type WorkspaceLockIpcMain,
} from './workspace-lock-ipc'

class FakeSender extends EventEmitter {
  constructor(readonly id: number) {
    super()
  }

  destroy(): void {
    this.emit('destroyed')
  }
}

class FakeIpcMain implements WorkspaceLockIpcMain {
  readonly handlers = new Map<
    string,
    (event: WorkspaceLockIpcEvent, ...args: unknown[]) => unknown
  >()

  handle(
    channel: string,
    listener: (event: WorkspaceLockIpcEvent, ...args: unknown[]) => unknown,
  ): void {
    this.handlers.set(channel, listener)
  }

  invoke(channel: string, sender: FakeSender, ...args: unknown[]): unknown {
    const handler = this.handlers.get(channel)
    if (!handler) throw new Error(`No IPC handler registered for ${channel}`)
    return handler({ sender }, ...args)
  }
}

describe('workspace lock IPC', () => {
  it('enforces read/write exclusion across renderer owners', async () => {
    const ipc = new FakeIpcMain()
    registerWorkspaceLockIpc(ipc)
    const writer = new FakeSender(1)
    const reader = new FakeSender(2)

    const [writeAcquired, readAcquired] = await Promise.all([
      ipc.invoke(WORKSPACE_LOCK_CHANNELS.acquire, writer, '/tmp/project', 'write-1', 'write'),
      ipc.invoke(WORKSPACE_LOCK_CHANNELS.acquire, reader, '/tmp/project', 'read-1', 'read'),
    ])

    expect([writeAcquired, readAcquired].filter(Boolean)).toHaveLength(1)
  })

  it('does not let one renderer release another renderer lock', () => {
    const ipc = new FakeIpcMain()
    const locks = registerWorkspaceLockIpc(ipc)
    const owner = new FakeSender(10)
    const attacker = new FakeSender(11)

    expect(ipc.invoke(
      WORKSPACE_LOCK_CHANNELS.acquire,
      owner,
      '/tmp/project',
      'same-task',
      'write',
    )).toBe(true)

    ipc.invoke(WORKSPACE_LOCK_CHANNELS.release, attacker, '/tmp/project', 'same-task')
    ipc.invoke(WORKSPACE_LOCK_CHANNELS.releaseTask, attacker, 'same-task')

    expect(locks.detailedStatus('/tmp/project')).toEqual({
      writer: { ownerId: 'renderer:10', taskId: 'same-task' },
      readers: [],
    })
  })

  it('reclaims every renderer lease when its webContents is destroyed', () => {
    const ipc = new FakeIpcMain()
    const locks = registerWorkspaceLockIpc(ipc)
    const crashed = new FakeSender(20)
    const survivor = new FakeSender(21)

    expect(ipc.invoke(
      WORKSPACE_LOCK_CHANNELS.acquire,
      crashed,
      '/tmp/project-a',
      'read-a',
      'read',
    )).toBe(true)
    expect(ipc.invoke(
      WORKSPACE_LOCK_CHANNELS.acquire,
      crashed,
      '/tmp/project-b',
      'write-b',
      'write',
    )).toBe(true)
    expect(ipc.invoke(
      WORKSPACE_LOCK_CHANNELS.acquire,
      survivor,
      '/tmp/project-a',
      'read-c',
      'read',
    )).toBe(true)

    crashed.destroy()

    expect(locks.detailedStatus('/tmp/project-a')).toEqual({
      writer: null,
      readers: [{ ownerId: 'renderer:21', taskId: 'read-c' }],
    })
    expect(locks.status('/tmp/project-b')).toEqual({ writer: null, readers: [] })
    expect(ipc.invoke(
      WORKSPACE_LOCK_CHANNELS.acquire,
      survivor,
      '/tmp/project-b',
      'write-after-crash',
      'write',
    )).toBe(true)
  })

  it('registers only one destruction listener per renderer', () => {
    const ipc = new FakeIpcMain()
    registerWorkspaceLockIpc(ipc)
    const sender = new FakeSender(30)

    expect(ipc.invoke(
      WORKSPACE_LOCK_CHANNELS.acquire,
      sender,
      '/tmp/project-a',
      'task-a',
      'read',
    )).toBe(true)
    expect(ipc.invoke(
      WORKSPACE_LOCK_CHANNELS.acquire,
      sender,
      '/tmp/project-b',
      'task-b',
      'read',
    )).toBe(true)

    expect(sender.listenerCount('destroyed')).toBe(1)
  })

  it('rejects malformed sender and argument payloads', () => {
    const ipc = new FakeIpcMain()
    registerWorkspaceLockIpc(ipc)

    expect(ipc.invoke(
      WORKSPACE_LOCK_CHANNELS.acquire,
      new FakeSender(Number.NaN),
      '/tmp/project',
      'task',
      'write',
    )).toBe(false)
    expect(ipc.invoke(
      WORKSPACE_LOCK_CHANNELS.acquire,
      new FakeSender(40),
      '',
      'task',
      'write',
    )).toBe(false)
    expect(ipc.invoke(
      WORKSPACE_LOCK_CHANNELS.acquire,
      new FakeSender(40),
      '/tmp/project',
      'task',
      'execute',
    )).toBe(false)
  })
})
