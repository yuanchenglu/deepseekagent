import { describe, expect, it } from 'vitest'
import { RuntimeTaskLeaseCoordinator, type RuntimeTaskLeaseResult } from './runtime-task-lease'

function coordinator(): RuntimeTaskLeaseCoordinator {
  return new RuntimeTaskLeaseCoordinator({
    defaultTtlMs: 10_000,
    minTtlMs: 1_000,
    maxTtlMs: 60_000,
  })
}

function leaseId(result: RuntimeTaskLeaseResult): string {
  if (!result.lease) throw new Error('Expected a lease snapshot')
  return result.lease.leaseId
}

describe('Runtime task process binding contract', () => {
  it('binds the spawned process once and rejects process identity replacement', () => {
    const leases = coordinator()
    const acquired = leases.dispatch({
      eventId: 'acquire',
      type: 'acquire',
      observedAt: 1_000,
      identity: {
        runtime: 'deepagent',
        workspace: '/tmp/project',
        taskId: 'task',
        access: 'write',
      },
    })
    const id = leaseId(acquired)
    const command = {
      eventId: 'bind-process',
      type: 'bind-process',
      runtime: 'deepagent',
      taskId: 'task',
      leaseId: id,
      observedAt: 1_500,
      process: { pid: 4242, treeId: 'tree-1' },
    } as const

    expect(leases.dispatch(command)).toMatchObject({
      ok: true,
      code: 'process-bound',
      lease: {
        state: 'active',
        identity: { process: { pid: 4242, treeId: 'tree-1' } },
      },
    })
    expect(leases.dispatch({ ...command, eventId: 'bind-again' })).toMatchObject({
      ok: true,
      code: 'process-bound',
    })
    expect(leases.dispatch({
      ...command,
      eventId: 'replace-process',
      process: { pid: 5000, treeId: 'tree-2' },
    })).toMatchObject({ ok: false, code: 'owner-mismatch' })
    expect(leases.dispatch({
      eventId: 'acquire-after-bind',
      type: 'acquire',
      observedAt: 2_000,
      identity: {
        runtime: 'deepagent',
        workspace: '/tmp/project',
        taskId: 'task',
        access: 'write',
      },
    })).toMatchObject({
      ok: true,
      code: 'already-acquired',
      lease: { leaseId: id, identity: { process: { pid: 4242, treeId: 'tree-1' } } },
    })
  })

  it('rejects empty process bindings and binding after the lease is terminal', () => {
    const leases = coordinator()
    const acquired = leases.dispatch({
      eventId: 'acquire',
      type: 'acquire',
      observedAt: 1_000,
      identity: {
        runtime: 'deepcode',
        workspace: '/tmp/project',
        taskId: 'task',
        access: 'read',
      },
    })
    const id = leaseId(acquired)

    expect(leases.dispatch({
      eventId: 'empty-process',
      type: 'bind-process',
      runtime: 'deepcode',
      taskId: 'task',
      leaseId: id,
      observedAt: 1_100,
      process: {},
    })).toMatchObject({ ok: false, code: 'invalid-request' })
    expect(leases.dispatch({
      eventId: 'release',
      type: 'release',
      runtime: 'deepcode',
      taskId: 'task',
      leaseId: id,
      observedAt: 2_000,
    })).toMatchObject({ ok: true, code: 'released' })
    expect(leases.dispatch({
      eventId: 'late-bind',
      type: 'bind-process',
      runtime: 'deepcode',
      taskId: 'task',
      leaseId: id,
      observedAt: 2_100,
      process: { pid: 4242 },
    })).toMatchObject({ ok: false, code: 'invalid-state', lease: { state: 'released' } })
  })

  it('does not persist a denied acquire or add a phantom pending transition', () => {
    const leases = coordinator()
    expect(leases.dispatch({
      eventId: 'writer',
      type: 'acquire',
      observedAt: 1_000,
      identity: {
        runtime: 'deepagent',
        workspace: '/tmp/project',
        taskId: 'writer',
        access: 'write',
      },
    })).toMatchObject({ ok: true, code: 'acquired' })
    const historyLength = leases.history().length

    expect(leases.dispatch({
      eventId: 'blocked-reader',
      type: 'acquire',
      observedAt: 1_100,
      identity: {
        runtime: 'deepcode',
        workspace: '/tmp/project',
        taskId: 'reader',
        access: 'read',
      },
    })).toMatchObject({ ok: false, code: 'conflict' })
    expect(leases.snapshot('deepcode', 'reader')).toBeUndefined()
    expect(leases.history()).toHaveLength(historyLength)
  })
})
