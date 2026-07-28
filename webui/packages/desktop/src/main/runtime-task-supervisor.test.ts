import { mkdtempSync, rmSync } from 'node:fs'
import { request as httpRequest } from 'node:http'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { afterEach, describe, expect, it } from 'vitest'
import {
  RuntimeTaskSupervisor,
  type RuntimeTaskProcessEvidence,
  type RuntimeTaskProcessProbe,
  type RuntimeTaskSupervisorEnvironment,
} from './runtime-task-supervisor'

class FakeProcessProbe implements RuntimeTaskProcessProbe {
  readonly processes = new Map<number, RuntimeTaskProcessEvidence>()

  async inspect(pid: number): Promise<RuntimeTaskProcessEvidence | null> {
    const value = this.processes.get(pid)
    return value ? { ...value } : null
  }
}

async function post(
  environment: RuntimeTaskSupervisorEnvironment,
  path: string,
  body: Record<string, unknown>,
): Promise<{ status: number; body: any }> {
  const payload = Buffer.from(JSON.stringify(body))
  return new Promise((resolveRequest, rejectRequest) => {
    const request = httpRequest({
      socketPath: environment.DEEPAGENT_RUNTIME_LEASE_SOCKET,
      path,
      method: 'POST',
      headers: {
        authorization: `Bearer ${environment.DEEPAGENT_RUNTIME_LEASE_TOKEN}`,
        'content-type': 'application/json',
        'content-length': String(payload.length),
      },
    }, (response) => {
      const chunks: Buffer[] = []
      response.on('data', chunk => chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)))
      response.on('end', () => {
        resolveRequest({
          status: response.statusCode || 500,
          body: JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}'),
        })
      })
    })
    request.once('error', rejectRequest)
    request.end(payload)
  })
}

const temporaryDirectories: string[] = []

afterEach(() => {
  while (temporaryDirectories.length > 0) {
    rmSync(temporaryDirectories.pop()!, { recursive: true, force: true })
  }
})

function fixture() {
  const stateDir = mkdtempSync(join(tmpdir(), 'deepagent-runtime-supervisor-'))
  temporaryDirectories.push(stateDir)
  const probe = new FakeProcessProbe()
  probe.processes.set(4101, {
    pid: 4101,
    fingerprint: 'fingerprint-4101',
    command: 'python hermes_bridge.py --endpoint ipc:///tmp/bridge.sock',
  })
  return { stateDir, probe }
}

describe('RuntimeTaskSupervisor', () => {
  it('binds real process evidence, releases conflicts, and safely reuses external task IDs', async () => {
    const { stateDir, probe } = fixture()
    const supervisor = new RuntimeTaskSupervisor({
      stateDir,
      socketPath: join(stateDir, 'supervisor.sock'),
      heartbeatTtlMs: 10_000,
      processProbe: probe,
    })
    const environment = await supervisor.start()

    const first = await post(environment, '/v1/tasks/start', {
      runtime: 'deepagent',
      taskId: 'deepagent:session-a',
      workspace: join(stateDir, 'workspace'),
      access: 'write',
      eventId: 'deepagent:start:1',
    })
    expect(first).toMatchObject({ status: 201, body: { ok: true, code: 'acquired', task: { generation: 1 } } })

    const bound = await post(environment, '/v1/tasks/bind-process', {
      runtime: 'deepagent',
      taskId: 'deepagent:session-a',
      pid: 4101,
      eventId: 'deepagent:bind:1',
    })
    expect(bound).toMatchObject({ status: 200, body: { ok: true, code: 'process-bound', task: { process: { pid: 4101 } } } })

    const conflict = await post(environment, '/v1/tasks/start', {
      runtime: 'deepcode',
      taskId: 'deepcode:turn-b',
      workspace: join(stateDir, 'workspace'),
      access: 'write',
      eventId: 'deepcode:start:1',
    })
    expect(conflict).toMatchObject({ status: 409, body: { ok: false, code: 'conflict' } })

    const finished = await post(environment, '/v1/tasks/finish', {
      runtime: 'deepagent',
      taskId: 'deepagent:session-a',
      outcome: 'completed',
      eventId: 'deepagent:finish:1',
    })
    expect(finished).toMatchObject({ status: 200, body: { ok: true, code: 'completed' } })

    const reused = await post(environment, '/v1/tasks/start', {
      runtime: 'deepagent',
      taskId: 'deepagent:session-a',
      workspace: join(stateDir, 'workspace'),
      access: 'write',
      eventId: 'deepagent:start:2',
    })
    expect(reused).toMatchObject({ status: 201, body: { ok: true, task: { generation: 2 } } })

    await supervisor.stop()
  })

  it('restores surviving PID evidence as orphaned and requires explicit verified resume', async () => {
    const { stateDir, probe } = fixture()
    const socketPath = join(stateDir, 'supervisor.sock')
    const firstSupervisor = new RuntimeTaskSupervisor({
      stateDir,
      socketPath,
      heartbeatTtlMs: 10_000,
      processProbe: probe,
    })
    const firstEnvironment = await firstSupervisor.start()

    await post(firstEnvironment, '/v1/tasks/start', {
      runtime: 'deepagent',
      taskId: 'deepagent:session-resume',
      workspace: join(stateDir, 'workspace-resume'),
      access: 'write',
      eventId: 'deepagent:start:resume',
    })
    await post(firstEnvironment, '/v1/tasks/bind-process', {
      runtime: 'deepagent',
      taskId: 'deepagent:session-resume',
      pid: 4101,
      eventId: 'deepagent:bind:resume',
    })
    await firstSupervisor.stop()

    const secondSupervisor = new RuntimeTaskSupervisor({
      stateDir,
      socketPath,
      heartbeatTtlMs: 10_000,
      processProbe: probe,
    })
    const secondEnvironment = await secondSupervisor.start()
    expect(secondSupervisor.listTasks()).toMatchObject([
      { runtime: 'deepagent', taskId: 'deepagent:session-resume', state: 'orphaned', generation: 1 },
    ])

    const blocked = await post(secondEnvironment, '/v1/tasks/start', {
      runtime: 'deepagent',
      taskId: 'deepagent:session-resume',
      workspace: join(stateDir, 'workspace-resume'),
      access: 'write',
      eventId: 'deepagent:start:after-restart',
    })
    expect(blocked).toMatchObject({ status: 409, body: { ok: false, code: 'resume-required' } })

    const resumed = await post(secondEnvironment, '/v1/tasks/resume', {
      runtime: 'deepagent',
      taskId: 'deepagent:session-resume',
      pid: 4101,
      eventId: 'deepagent:resume:after-restart',
    })
    expect(resumed).toMatchObject({
      status: 200,
      body: { ok: true, code: 'resumed', task: { state: 'active', generation: 2, process: { pid: 4101 } } },
    })

    await secondSupervisor.stop()
  })

  it('rejects unauthenticated callers', async () => {
    const { stateDir, probe } = fixture()
    const supervisor = new RuntimeTaskSupervisor({
      stateDir,
      socketPath: join(stateDir, 'supervisor.sock'),
      processProbe: probe,
    })
    const environment = await supervisor.start()
    const unauthorized = await post({ ...environment, DEEPAGENT_RUNTIME_LEASE_TOKEN: 'wrong-token' }, '/v1/tasks/start', {})
    expect(unauthorized).toMatchObject({ status: 401, body: { ok: false, code: 'unauthorized' } })
    await supervisor.stop()
  })
})
