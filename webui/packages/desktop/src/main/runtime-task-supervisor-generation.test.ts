import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { request as httpRequest } from 'node:http'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { RuntimeTaskSupervisor, type RuntimeTaskSupervisorEnvironment } from './runtime-task-supervisor'

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

async function startAndFinish(
  environment: RuntimeTaskSupervisorEnvironment,
  input: { runtime: 'deepagent' | 'deepcode'; taskId: string; workspace: string },
): Promise<number> {
  const started = await post(environment, '/v1/tasks/start', {
    ...input,
    access: 'write',
    eventId: `${input.taskId}:start`,
  })
  expect(started).toMatchObject({ status: 201, body: { ok: true, code: 'acquired' } })

  const finished = await post(environment, '/v1/tasks/finish', {
    runtime: input.runtime,
    taskId: input.taskId,
    outcome: 'completed',
    eventId: `${input.taskId}:finish`,
  })
  expect(finished).toMatchObject({ status: 200, body: { ok: true, code: 'completed' } })
  return Number(started.body.task.generation)
}

describe('RuntimeTaskSupervisor generation persistence', () => {
  it('retains reusable DeepAgent generations without accumulating one-shot DeepCode task IDs', async () => {
    const stateDir = mkdtempSync(join(tmpdir(), 'deepagent-runtime-generations-'))
    const socketPath = join(stateDir, 'supervisor.sock')
    const first = new RuntimeTaskSupervisor({ stateDir, socketPath })

    try {
      const environment = await first.start()
      expect(await startAndFinish(environment, {
        runtime: 'deepagent',
        taskId: 'deepagent:reusable-session',
        workspace: join(stateDir, 'deepagent-workspace'),
      })).toBe(1)
      expect(await startAndFinish(environment, {
        runtime: 'deepcode',
        taskId: 'deepcode:one-shot-turn',
        workspace: join(stateDir, 'deepcode-workspace'),
      })).toBe(1)

      const persisted = JSON.parse(readFileSync(first.stateFile, 'utf8')) as {
        tasks: unknown[]
        generations: Array<{ runtime: string; taskId: string; generation: number }>
      }
      expect(persisted.tasks).toEqual([])
      expect(persisted.generations).toEqual([
        { runtime: 'deepagent', taskId: 'deepagent:reusable-session', generation: 1 },
      ])

      await first.stop()
      const second = new RuntimeTaskSupervisor({ stateDir, socketPath })
      try {
        const restartedEnvironment = await second.start()
        expect(await startAndFinish(restartedEnvironment, {
          runtime: 'deepagent',
          taskId: 'deepagent:reusable-session',
          workspace: join(stateDir, 'deepagent-workspace'),
        })).toBe(2)
      } finally {
        await second.stop().catch(() => undefined)
      }
    } finally {
      await first.stop().catch(() => undefined)
      rmSync(stateDir, { recursive: true, force: true })
    }
  })
})
