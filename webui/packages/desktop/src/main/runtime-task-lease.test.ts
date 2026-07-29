import { describe, expect, it } from 'vitest'
import {
  RuntimeTaskLeaseAdapter,
  RuntimeTaskLeaseCoordinator,
  type RuntimeTaskLeaseResult,
} from './runtime-task-lease'

function coordinator(): RuntimeTaskLeaseCoordinator {
  return new RuntimeTaskLeaseCoordinator({
    defaultTtlMs: 10_000,
    minTtlMs: 1_000,
    maxTtlMs: 60_000,
  })
}

function acquire(
  leases: RuntimeTaskLeaseCoordinator,
  eventId: string,
  runtime: 'deepagent' | 'deepcode',
  taskId: string,
  access: 'read' | 'write',
  workspace = '/tmp/project',
  observedAt = 1_000,
): RuntimeTaskLeaseResult {
  return leases.dispatch({
    eventId,
    type: 'acquire',
    observedAt,
    identity: { runtime, workspace, taskId, access },
  })
}

function leaseId(result: RuntimeTaskLeaseResult): string {
  if (!result.lease) throw new Error('Expected a lease snapshot')
  return result.lease.leaseId
}

describe('RuntimeTaskLeaseCoordinator', () => {
  it('fails closed on malformed runtime, access, identity, and TTL payloads', () => {
    const leases = coordinator()

    expect(leases.dispatch({
      eventId: 'invalid-runtime',
      type: 'acquire',
      observedAt: 1,
      identity: { runtime: 'renderer', workspace: '/tmp/project', taskId: 'task', access: 'read' },
    })).toMatchObject({ ok: false, code: 'invalid-request' })
    expect(leases.dispatch({
      eventId: 'invalid-access',
      type: 'acquire',
      observedAt: 1,
      identity: { runtime: 'deepagent', workspace: '/tmp/project', taskId: 'task', access: 'execute' },
    })).toMatchObject({ ok: false, code: 'invalid-request' })
    expect(leases.dispatch({
      eventId: 'invalid-pid',
      type: 'acquire',
      observedAt: 1,
      identity: {
        runtime: 'deepagent',
        workspace: '/tmp/project',
        taskId: 'task',
        access: 'read',
        process: { pid: -1 },
      },
    })).toMatchObject({ ok: false, code: 'invalid-request' })
    expect(leases.dispatch({
      eventId: 'invalid-ttl',
      type: 'acquire',
      observedAt: 1,
      ttlMs: 100,
      identity: { runtime: 'deepagent', workspace: '/tmp/project', taskId: 'task', access: 'read' },
    })).toMatchObject({ ok: false, code: 'invalid-request' })
  })

  it('allows reader-reader and denies reader-writer and writer-writer conflicts', () => {
    const leases = coordinator()
    const firstReader = acquire(leases, 'read-1', 'deepagent', 'reader-agent', 'read')
    const secondReader = acquire(leases, 'read-2', 'deepcode', 'reader-code', 'read')

    expect(firstReader).toMatchObject({ ok: true, code: 'acquired', lease: { state: 'active' } })
    expect(secondReader).toMatchObject({ ok: true, code: 'acquired', lease: { state: 'active' } })
    expect(acquire(leases, 'write-blocked', 'deepagent', 'writer-agent', 'write')).toMatchObject({
      ok: false,
      code: 'conflict',
      conflict: {
        writerLeaseId: null,
        readerLeaseIds: [leaseId(firstReader), leaseId(secondReader)],
      },
    })

    const isolatedWriter = acquire(leases, 'write-other', 'deepagent', 'writer-other', 'write', '/tmp/other')
    expect(isolatedWriter.ok).toBe(true)
    expect(acquire(leases, 'write-other-blocked', 'deepcode', 'writer-other-2', 'write', '/tmp/other'))
      .toMatchObject({ ok: false, code: 'conflict' })
  })

  it('makes acquire and event replay idempotent while rejecting eventId payload reuse', () => {
    const leases = coordinator()
    const command = {
      eventId: 'acquire-1',
      type: 'acquire',
      observedAt: 1_000,
      identity: { runtime: 'deepagent', workspace: '/tmp/project', taskId: 'task-1', access: 'write' },
    } as const
    const first = leases.dispatch(command)

    expect(leases.dispatch({
      identity: command.identity,
      observedAt: command.observedAt,
      type: command.type,
      eventId: command.eventId,
    })).toEqual(first)
    expect(leases.dispatch({ ...command, eventId: 'acquire-2' })).toMatchObject({
      ok: true,
      code: 'already-acquired',
      lease: { leaseId: leaseId(first) },
    })
    expect(leases.dispatch({
      ...command,
      identity: { ...command.identity, workspace: '/tmp/other' },
    })).toMatchObject({ ok: false, code: 'replay-conflict' })
    expect(leases.dispatch({
      ...command,
      eventId: 'acquire-3',
      identity: { ...command.identity, access: 'read' },
    })).toMatchObject({ ok: false, code: 'owner-mismatch' })
  })

  it('renews active leases and expires late heartbeats without resurrection', () => {
    const leases = coordinator()
    const acquired = acquire(leases, 'acquire', 'deepagent', 'task', 'write')
    const id = leaseId(acquired)

    expect(leases.dispatch({
      eventId: 'heartbeat',
      type: 'heartbeat',
      runtime: 'deepagent',
      taskId: 'task',
      leaseId: id,
      observedAt: 5_000,
    })).toMatchObject({
      ok: true,
      code: 'heartbeat-accepted',
      lease: { state: 'active', lastHeartbeatAt: 5_000, expiresAt: 15_000 },
    })
    expect(leases.dispatch({
      eventId: 'late-heartbeat',
      type: 'heartbeat',
      runtime: 'deepagent',
      taskId: 'task',
      leaseId: id,
      observedAt: 15_000,
    })).toMatchObject({ ok: false, code: 'expired-lease', lease: { state: 'expired' } })
    expect(leases.dispatch({
      eventId: 'after-expiry',
      type: 'heartbeat',
      runtime: 'deepagent',
      taskId: 'task',
      leaseId: id,
      observedAt: 16_000,
    })).toMatchObject({ ok: false, code: 'expired-lease', lease: { state: 'expired' } })
    expect(acquire(leases, 'replacement', 'deepcode', 'replacement', 'write', '/tmp/project', 16_000).ok).toBe(true)
  })

  it('defines owner, unknown-task, early-timeout, and terminal idempotency errors', () => {
    const leases = coordinator()
    const acquired = acquire(leases, 'acquire', 'deepagent', 'task', 'read')
    const id = leaseId(acquired)

    expect(leases.dispatch({
      eventId: 'wrong-owner',
      type: 'release',
      runtime: 'deepagent',
      taskId: 'task',
      leaseId: 'lease:deepagent:999',
      observedAt: 2_000,
    })).toMatchObject({ ok: false, code: 'owner-mismatch' })
    expect(leases.dispatch({
      eventId: 'unknown',
      type: 'release',
      runtime: 'deepcode',
      taskId: 'missing',
      leaseId: 'lease:deepcode:1',
      observedAt: 2_000,
    })).toMatchObject({ ok: false, code: 'unknown-task' })
    expect(leases.dispatch({
      eventId: 'early-timeout',
      type: 'timeout',
      runtime: 'deepagent',
      taskId: 'task',
      leaseId: id,
      observedAt: 2_000,
    })).toMatchObject({ ok: false, code: 'invalid-state' })
    expect(leases.dispatch({
      eventId: 'cancel',
      type: 'cancel',
      runtime: 'deepagent',
      taskId: 'task',
      leaseId: id,
      observedAt: 3_000,
    })).toMatchObject({ ok: true, code: 'cancelled', lease: { state: 'released', terminalReason: 'cancelled' } })
    expect(leases.dispatch({
      eventId: 'cancel-again',
      type: 'cancel',
      runtime: 'deepagent',
      taskId: 'task',
      leaseId: id,
      observedAt: 4_000,
    })).toMatchObject({ ok: true, code: 'already-terminal', lease: { state: 'released' } })
  })

  it('keeps orphaned locks fail-closed until explicit recovery', () => {
    const leases = coordinator()
    const writer = acquire(leases, 'writer', 'deepcode', 'task-code', 'write')
    const id = leaseId(writer)

    expect(leases.dispatch({
      eventId: 'crash',
      type: 'runtime-crash',
      runtime: 'deepcode',
      observedAt: 2_000,
      reason: 'runtime disconnected',
    })).toMatchObject({ ok: true, code: 'orphaned', affected: [{ state: 'orphaned' }] })
    expect(acquire(leases, 'blocked-after-crash', 'deepagent', 'task-agent', 'read')).toMatchObject({
      ok: false,
      code: 'conflict',
    })
    expect(leases.dispatch({
      eventId: 'orphan-heartbeat',
      type: 'heartbeat',
      runtime: 'deepcode',
      taskId: 'task-code',
      leaseId: id,
      observedAt: 3_000,
    })).toMatchObject({ ok: false, code: 'invalid-state', lease: { state: 'orphaned' } })
    expect(leases.dispatch({
      eventId: 'recover',
      type: 'recover',
      runtime: 'deepcode',
      taskId: 'task-code',
      leaseId: id,
      observedAt: 4_000,
    })).toMatchObject({ ok: true, code: 'recovered', lease: { state: 'recovered' } })
    expect(acquire(leases, 'after-recovery', 'deepagent', 'task-agent', 'write', '/tmp/project', 5_000).ok).toBe(true)
  })

  it('uses process-exit as authoritative recovery evidence for an orphan', () => {
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
        process: { pid: 4242, treeId: 'tree-1' },
      },
    })
    const id = leaseId(acquired)
    leases.dispatch({ eventId: 'crash', type: 'runtime-crash', runtime: 'deepagent', observedAt: 2_000 })

    expect(leases.dispatch({
      eventId: 'process-exit',
      type: 'process-exit',
      runtime: 'deepagent',
      taskId: 'task',
      leaseId: id,
      observedAt: 3_000,
      exitCode: 137,
      signal: 'SIGKILL',
    })).toMatchObject({
      ok: true,
      code: 'recovered',
      lease: { state: 'recovered', terminalReason: 'process-exit' },
    })
  })

  it('pins DeepAgent and DeepCode adapters to their own runtime identities', () => {
    const leases = coordinator()
    const deepAgent = new RuntimeTaskLeaseAdapter('deepagent', leases)
    const deepCode = new RuntimeTaskLeaseAdapter('deepcode', leases)

    const agentLease = deepAgent.dispatch({
      eventId: 'agent-read',
      type: 'acquire',
      observedAt: 1_000,
      identity: { workspace: '/tmp/project', taskId: 'same-task', access: 'read' },
    })
    const codeLease = deepCode.dispatch({
      eventId: 'code-read',
      type: 'acquire',
      observedAt: 1_000,
      identity: { workspace: '/tmp/project', taskId: 'same-task', access: 'read' },
    })

    expect(agentLease).toMatchObject({ lease: { identity: { runtime: 'deepagent' } } })
    expect(codeLease).toMatchObject({ lease: { identity: { runtime: 'deepcode' } } })
    expect(leaseId(agentLease)).not.toBe(leaseId(codeLease))
  })

  it('records authoritative state transitions without exposing mutable snapshots', () => {
    const leases = coordinator()
    const acquired = acquire(leases, 'acquire', 'deepagent', 'task', 'write')
    const id = leaseId(acquired)
    leases.dispatch({
      eventId: 'release',
      type: 'release',
      runtime: 'deepagent',
      taskId: 'task',
      leaseId: id,
      observedAt: 2_000,
    })

    expect(leases.history().map(item => [item.from, item.to])).toEqual([
      [undefined, 'pending'],
      ['pending', 'active'],
      ['active', 'releasing'],
      ['releasing', 'released'],
    ])
    const snapshot = leases.snapshot('deepagent', 'task')
    if (!snapshot) throw new Error('Expected snapshot')
    snapshot.state = 'active'
    expect(leases.snapshot('deepagent', 'task')?.state).toBe('released')
  })
})
