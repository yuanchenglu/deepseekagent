import { mkdtempSync, rmSync } from 'node:fs'
import { request as httpRequest } from 'node:http'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { RuntimeTaskSupervisor, type RuntimeTaskSupervisorEnvironment } from './runtime-task-supervisor'

async function health(environment: RuntimeTaskSupervisorEnvironment): Promise<{
  status: number
  connection: string | undefined
  body: any
}> {
  return new Promise((resolveRequest, rejectRequest) => {
    const request = httpRequest({
      socketPath: environment.DEEPAGENT_RUNTIME_LEASE_SOCKET,
      path: '/health',
      method: 'GET',
      agent: false,
      headers: {
        authorization: `Bearer ${environment.DEEPAGENT_RUNTIME_LEASE_TOKEN}`,
      },
    }, (response) => {
      const chunks: Buffer[] = []
      response.on('data', chunk => chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)))
      response.on('end', () => {
        resolveRequest({
          status: response.statusCode || 500,
          connection: typeof response.headers.connection === 'string' ? response.headers.connection : undefined,
          body: JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}'),
        })
      })
    })
    request.once('error', rejectRequest)
    request.end()
  })
}

describe('RuntimeTaskSupervisor connection lifecycle', () => {
  it('accepts a fresh RPC after Main restarts on the same socket path', async () => {
    const stateDir = mkdtempSync(join(tmpdir(), 'deepagent-runtime-connection-'))
    const socketPath = join(stateDir, 'supervisor.sock')
    const first = new RuntimeTaskSupervisor({ stateDir, socketPath })
    let firstStopped = false

    try {
      const firstEnvironment = await first.start()
      expect(await health(firstEnvironment)).toMatchObject({
        status: 200,
        connection: 'close',
        body: { ok: true, code: 'ready' },
      })

      await first.stop()
      firstStopped = true

      const second = new RuntimeTaskSupervisor({ stateDir, socketPath })
      try {
        const secondEnvironment = await second.start()
        expect(await health(secondEnvironment)).toMatchObject({
          status: 200,
          connection: 'close',
          body: { ok: true, code: 'ready' },
        })
      } finally {
        await second.stop().catch(() => undefined)
      }
    } finally {
      if (!firstStopped) await first.stop().catch(() => undefined)
      rmSync(stateDir, { recursive: true, force: true })
    }
  })
})
