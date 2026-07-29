import { mkdtempSync, rmSync } from 'node:fs'
import { request as httpRequest } from 'node:http'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  RuntimeTaskSupervisor,
  type RuntimeTaskProcessEvidence,
  type RuntimeTaskProcessProbe,
  type RuntimeTaskSupervisorEnvironment,
} from './runtime-task-supervisor'

class FakeProcessProbe implements RuntimeTaskProcessProbe {
  readonly processes = new Map<number, RuntimeTaskProcessEvidence>()

  async inspect(pid: number): Promise<RuntimeTaskProcessEvidence | null> {
    const process = this.processes.get(pid)
    return process ? { ...process } : null
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
      agent: false,
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

async function waitUntil(predicate: () => boolean, timeoutMs = 2_000): Promise<void> {
  const deadline = Date.now() + timeoutMs
  while (!predicate()) {
    if (Date.now() >= deadline) throw new Error('condition did not become true before timeout')
    await new Promise(resolve => setTimeout(resolve, 25))
  }
}

describe('RuntimeTaskSupervisor Runtime crash semantics', () => {
  it('orphans every active task owned by a Runtime when its heartbeat expires', async () => {
    const stateDir = mkdtempSync(join(tmpdir(), 'deepagent-runtime-crash-'))
    const probe = new FakeProcessProbe()
    probe.processes.set(5201, {
      pid: 5201,
      fingerprint: 'shared-deepagent-bridge-process',
      command: 'python hermes_bridge.py --endpoint ipc:///tmp/deepagent.sock',
    })
    let observedAt = 1_000
    const supervisor = new RuntimeTaskSupervisor({
      stateDir,
      socketPath: join(stateDir, 'supervisor.sock'),
      heartbeatTtlMs: 1_000,
      monitorIntervalMs: 100,
      processProbe: probe,
      now: () => observedAt,
    })

    try {
      const environment = await supervisor.start()
      for (const [taskId, workspace] of [
        ['deepagent:session-a', join(stateDir, 'workspace-a')],
        ['deepagent:session-b', join(stateDir, 'workspace-b')],
      ] as const) {
        const started = await post(environment, '/v1/tasks/start', {
          runtime: 'deepagent',
          taskId,
          workspace,
          access: 'write',
          eventId: `${taskId}:start`,
        })
        expect(started).toMatchObject({ status: 201, body: { ok: true, code: 'acquired' } })

        const bound = await post(environment, '/v1/tasks/bind-process', {
          runtime: 'deepagent',
          taskId,
          pid: 5201,
          eventId: `${taskId}:bind`,
        })
        expect(bound).toMatchObject({ status: 200, body: { ok: true, code: 'process-bound' } })
      }

      observedAt = 2_001
      await waitUntil(() => supervisor.listTasks().every(task => task.state === 'orphaned'))

      expect(supervisor.listTasks()).toMatchObject([
        { runtime: 'deepagent', taskId: 'deepagent:session-a', state: 'orphaned', process: { pid: 5201 } },
        { runtime: 'deepagent', taskId: 'deepagent:session-b', state: 'orphaned', process: { pid: 5201 } },
      ])
    } finally {
      await supervisor.stop().catch(() => undefined)
      rmSync(stateDir, { recursive: true, force: true })
    }
  })
})
