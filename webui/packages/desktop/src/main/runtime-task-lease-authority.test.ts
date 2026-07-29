import { describe, expect, it } from 'vitest'
import { RuntimeTaskLeaseAdapter, RuntimeTaskLeaseCoordinator } from './runtime-task-lease'

function coordinator(maxReplayEntries = 64): RuntimeTaskLeaseCoordinator {
  return new RuntimeTaskLeaseCoordinator({
    defaultTtlMs: 10_000,
    minTtlMs: 1_000,
    maxTtlMs: 60_000,
    maxReplayEntries,
  })
}

describe('Runtime task lease authority boundaries', () => {
  it('keeps supervisory events on the trusted Main-only coordinator path', () => {
    const leases = coordinator()
    const runtime = new RuntimeTaskLeaseAdapter('deepagent', leases)
    const acquired = runtime.dispatch({
      eventId: 'acquire',
      type: 'acquire',
      observedAt: 1_000,
      identity: {
        workspace: '/tmp/project',
        taskId: 'task',
        access: 'write',
      },
    })
    if (!acquired.lease) throw new Error('Expected active lease')

    for (const type of ['bind-process', 'timeout', 'process-exit', 'runtime-crash', 'recover'] as const) {
      const payload = type === 'runtime-crash'
        ? { eventId: type, type, observedAt: 2_000 }
        : type === 'bind-process'
          ? {
              eventId: type,
              type,
              observedAt: 2_000,
              taskId: 'task',
              leaseId: acquired.lease.leaseId,
              process: { pid: 4242 },
            }
          : {
              eventId: type,
              type,
              observedAt: 2_000,
              taskId: 'task',
              leaseId: acquired.lease.leaseId,
            }
      expect(runtime.dispatch(payload as never)).toMatchObject({
        ok: false,
        type,
        code: 'invalid-request',
      })
    }

    expect(leases.snapshot('deepagent', 'task')).toMatchObject({ state: 'active' })
    expect(leases.dispatch({
      eventId: 'main-bind',
      type: 'bind-process',
      runtime: 'deepagent',
      taskId: 'task',
      leaseId: acquired.lease.leaseId,
      observedAt: 2_100,
      process: { pid: 4242 },
    })).toMatchObject({ ok: true, code: 'process-bound' })
  })

  it('scopes identical event IDs independently to DeepAgent and DeepCode', () => {
    const leases = coordinator()
    const deepAgent = new RuntimeTaskLeaseAdapter('deepagent', leases)
    const deepCode = new RuntimeTaskLeaseAdapter('deepcode', leases)

    expect(deepAgent.dispatch({
      eventId: '1',
      type: 'acquire',
      observedAt: 1_000,
      identity: {
        workspace: '/tmp/agent',
        taskId: 'task',
        access: 'read',
      },
    })).toMatchObject({ ok: true, code: 'acquired', lease: { identity: { runtime: 'deepagent' } } })
    expect(deepCode.dispatch({
      eventId: '1',
      type: 'acquire',
      observedAt: 1_000,
      identity: {
        workspace: '/tmp/code',
        taskId: 'task',
        access: 'read',
      },
    })).toMatchObject({ ok: true, code: 'acquired', lease: { identity: { runtime: 'deepcode' } } })
  })

  it('bounds replay memory and evicts the oldest result', () => {
    const leases = coordinator(2)
    const runtime = new RuntimeTaskLeaseAdapter('deepagent', leases)
    const acquired = runtime.dispatch({
      eventId: 'oldest',
      type: 'acquire',
      observedAt: 1_000,
      identity: {
        workspace: '/tmp/project',
        taskId: 'task',
        access: 'read',
      },
    })
    if (!acquired.lease) throw new Error('Expected active lease')

    expect(runtime.dispatch({
      eventId: 'heartbeat-1',
      type: 'heartbeat',
      observedAt: 2_000,
      taskId: 'task',
      leaseId: acquired.lease.leaseId,
    })).toMatchObject({ ok: true, code: 'heartbeat-accepted' })
    expect(runtime.dispatch({
      eventId: 'heartbeat-2',
      type: 'heartbeat',
      observedAt: 3_000,
      taskId: 'task',
      leaseId: acquired.lease.leaseId,
    })).toMatchObject({ ok: true, code: 'heartbeat-accepted' })
    expect(leases.replayEntryCount()).toBe(2)

    expect(runtime.dispatch({
      eventId: 'oldest',
      type: 'acquire',
      observedAt: 1_000,
      identity: {
        workspace: '/tmp/project',
        taskId: 'task',
        access: 'read',
      },
    })).toMatchObject({ ok: true, code: 'already-acquired' })
    expect(leases.replayEntryCount()).toBe(2)
  })

  it('rejects non-positive replay cache limits', () => {
    expect(() => coordinator(0)).toThrow('Invalid RuntimeTaskLeaseCoordinator configuration')
  })
})
