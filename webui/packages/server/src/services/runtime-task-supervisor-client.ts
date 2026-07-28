import { createHash, randomUUID } from 'node:crypto'
import { request as httpRequest } from 'node:http'
import type { RequestOptions } from 'node:http'

export type RuntimeTaskKind = 'deepagent' | 'deepcode'
export type RuntimeTaskAccess = 'read' | 'write'
export type RuntimeTaskOutcome = 'completed' | 'failed' | 'cancelled'

export const RUNTIME_TASK_SUPERVISOR_ENV_NAMES = [
  'DEEPAGENT_RUNTIME_LEASE_SOCKET',
  'DEEPAGENT_RUNTIME_LEASE_TOKEN',
  'DEEPAGENT_RUNTIME_LEASE_TTL_MS',
] as const

const DEFAULT_REQUEST_TIMEOUT_MS = 5_000
const MIN_HEARTBEAT_INTERVAL_MS = 1_000
const MAX_BIND_ATTEMPTS = 20
const BIND_RETRY_MS = 50

interface RuntimeTaskSupervisorConfig {
  socketPath: string
  token: string
  ttlMs: number
}

interface RuntimeTaskSupervisorTask {
  runtime: RuntimeTaskKind
  taskId: string
  workspace: string
  access: RuntimeTaskAccess
  state: 'active' | 'orphaned'
  generation: number
  leaseId: string
  process?: { pid: number; fingerprint: string; command: string }
}

interface RuntimeTaskSupervisorResponse {
  ok: boolean
  code: string
  task?: RuntimeTaskSupervisorTask
  message?: string
  conflict?: unknown
}

export interface AcquireRuntimeTaskLeaseInput {
  runtime: RuntimeTaskKind
  taskId: string
  workspace: string
  access: RuntimeTaskAccess
  processPid?: number
  requireProcess?: boolean
}

export interface RuntimeTaskLeaseHandle {
  readonly enabled: boolean
  readonly runtime: RuntimeTaskKind
  readonly taskId: string
  readonly workspace: string
  readonly access: RuntimeTaskAccess
  readonly processPid?: number
  bindProcess(pid: number): Promise<void>
  heartbeat(): Promise<void>
  finish(outcome: RuntimeTaskOutcome): Promise<void>
  processExit(exitCode?: number | null, signal?: string | null): Promise<void>
  abandon(): void
}

export class RuntimeTaskSupervisorError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number,
    readonly response?: RuntimeTaskSupervisorResponse,
  ) {
    super(message)
    this.name = 'RuntimeTaskSupervisorError'
  }
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function desktopRuntimeRequired(): boolean {
  return String(process.env.HERMES_DESKTOP || '').trim().toLowerCase() === 'true'
}

function positiveInt(value: unknown): number | null {
  const parsed = Number(value)
  return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : null
}

function supervisorConfig(): RuntimeTaskSupervisorConfig | null {
  const socketPath = String(process.env.DEEPAGENT_RUNTIME_LEASE_SOCKET || '').trim()
  const token = String(process.env.DEEPAGENT_RUNTIME_LEASE_TOKEN || '').trim()
  const ttlMs = positiveInt(process.env.DEEPAGENT_RUNTIME_LEASE_TTL_MS) || 30_000
  if (!socketPath && !token) {
    if (desktopRuntimeRequired()) {
      throw new RuntimeTaskSupervisorError(
        'Electron Runtime task supervision is required but not configured',
        'supervisor-not-configured',
        503,
      )
    }
    return null
  }
  if (!socketPath || token.length < 32) {
    throw new RuntimeTaskSupervisorError(
      'Electron Runtime task supervision configuration is incomplete',
      'supervisor-config-invalid',
      503,
    )
  }
  return { socketPath, token, ttlMs }
}

function nextEventId(runtime: RuntimeTaskKind, action: string): string {
  return `${runtime}:${action}:${randomUUID().replace(/-/g, '')}`
}

async function postSupervisor(
  config: RuntimeTaskSupervisorConfig,
  path: string,
  body: Record<string, unknown>,
): Promise<{ status: number; response: RuntimeTaskSupervisorResponse }> {
  const payload = Buffer.from(JSON.stringify(body))
  const options: RequestOptions = {
    socketPath: config.socketPath,
    path,
    method: 'POST',
    headers: {
      authorization: `Bearer ${config.token}`,
      'content-type': 'application/json; charset=utf-8',
      'content-length': String(payload.length),
    },
  }
  return new Promise((resolveRequest, rejectRequest) => {
    const request = httpRequest(options, (response) => {
      const chunks: Buffer[] = []
      response.on('data', chunk => chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)))
      response.on('end', () => {
        const status = response.statusCode || 500
        try {
          const parsed = JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}') as RuntimeTaskSupervisorResponse
          resolveRequest({ status, response: parsed })
        } catch (error) {
          rejectRequest(new RuntimeTaskSupervisorError(
            `Runtime task supervisor returned invalid JSON: ${error instanceof Error ? error.message : String(error)}`,
            'invalid-supervisor-response',
            status,
          ))
        }
      })
    })
    request.setTimeout(DEFAULT_REQUEST_TIMEOUT_MS, () => {
      request.destroy(new RuntimeTaskSupervisorError('Runtime task supervisor request timed out', 'supervisor-timeout', 504))
    })
    request.once('error', rejectRequest)
    request.end(payload)
  })
}

function responseError(
  result: { status: number; response: RuntimeTaskSupervisorResponse },
  fallback: string,
): RuntimeTaskSupervisorError {
  return new RuntimeTaskSupervisorError(
    result.response.message || `${fallback}: ${result.response.code}`,
    result.response.code || 'supervisor-error',
    result.status,
    result.response,
  )
}

function assertPid(pid: number): void {
  if (!Number.isSafeInteger(pid) || pid <= 0) {
    throw new RuntimeTaskSupervisorError('Runtime task process PID is invalid', 'invalid-pid', 400)
  }
}

class NoopRuntimeTaskLeaseHandle implements RuntimeTaskLeaseHandle {
  readonly enabled = false

  constructor(
    readonly runtime: RuntimeTaskKind,
    readonly taskId: string,
    readonly workspace: string,
    readonly access: RuntimeTaskAccess,
    readonly processPid?: number,
  ) {}

  async bindProcess(_pid: number): Promise<void> {}
  async heartbeat(): Promise<void> {}
  async finish(_outcome: RuntimeTaskOutcome): Promise<void> {}
  async processExit(_exitCode?: number | null, _signal?: string | null): Promise<void> {}
  abandon(): void {}
}

class ManagedRuntimeTaskLeaseHandle implements RuntimeTaskLeaseHandle {
  readonly enabled = true
  private heartbeatTimer: NodeJS.Timeout | null = null
  private heartbeatStopped = false
  private finalized = false
  private boundPid?: number

  constructor(
    private readonly config: RuntimeTaskSupervisorConfig,
    readonly runtime: RuntimeTaskKind,
    readonly taskId: string,
    readonly workspace: string,
    readonly access: RuntimeTaskAccess,
    processPid?: number,
  ) {
    this.boundPid = processPid
    this.startHeartbeatTimer()
  }

  get processPid(): number | undefined {
    return this.boundPid
  }

  private startHeartbeatTimer(): void {
    if (this.finalized || this.heartbeatStopped || this.heartbeatTimer) return
    const intervalMs = Math.max(MIN_HEARTBEAT_INTERVAL_MS, Math.floor(this.config.ttlMs / 3))
    this.heartbeatTimer = setInterval(() => {
      this.heartbeat().catch((error) => {
        const message = error instanceof Error ? error.message : String(error)
        console.warn(`[runtime-task-supervisor] heartbeat failed for ${this.runtime}/${this.taskId}: ${message}`)
      })
    }, intervalMs)
    this.heartbeatTimer.unref?.()
  }

  private stopHeartbeatTimer(): void {
    this.heartbeatStopped = true
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer)
    this.heartbeatTimer = null
  }

  private async reestablish(): Promise<void> {
    const started = await postSupervisor(this.config, '/v1/tasks/start', {
      runtime: this.runtime,
      taskId: this.taskId,
      workspace: this.workspace,
      access: this.access,
      eventId: nextEventId(this.runtime, 'reestablish'),
    })
    if (!started.response.ok && started.response.code !== 'resume-required') {
      throw responseError(started, 'Failed to re-establish Runtime task lease')
    }
    if (started.response.code === 'resume-required') {
      await this.resume()
      return
    }
    if (this.boundPid) await this.bindProcess(this.boundPid)
  }

  async resume(): Promise<void> {
    if (!this.boundPid) {
      throw new RuntimeTaskSupervisorError(
        'Runtime task lease is orphaned and cannot resume without the original PID',
        'process-required',
        409,
      )
    }
    const resumed = await postSupervisor(this.config, '/v1/tasks/resume', {
      runtime: this.runtime,
      taskId: this.taskId,
      pid: this.boundPid,
      eventId: nextEventId(this.runtime, 'resume'),
    })
    if (!resumed.response.ok) throw responseError(resumed, 'Failed to resume Runtime task lease')
  }

  async bindProcess(pid: number): Promise<void> {
    if (this.finalized) return
    assertPid(pid)
    let last: { status: number; response: RuntimeTaskSupervisorResponse } | null = null
    for (let attempt = 0; attempt < MAX_BIND_ATTEMPTS; attempt += 1) {
      const result = await postSupervisor(this.config, '/v1/tasks/bind-process', {
        runtime: this.runtime,
        taskId: this.taskId,
        pid,
        eventId: nextEventId(this.runtime, 'bind'),
      })
      last = result
      if (result.response.ok) {
        this.boundPid = pid
        return
      }
      if (result.response.code === 'resume-required') {
        this.boundPid = pid
        await this.resume()
        return
      }
      if (result.response.code !== 'process-unverifiable') break
      await delay(BIND_RETRY_MS)
    }
    throw responseError(last!, 'Failed to bind Runtime task process')
  }

  async heartbeat(): Promise<void> {
    if (this.finalized || this.heartbeatStopped) return
    const result = await postSupervisor(this.config, '/v1/tasks/heartbeat', {
      runtime: this.runtime,
      taskId: this.taskId,
      eventId: nextEventId(this.runtime, 'heartbeat'),
    })
    if (result.response.ok) return
    if (result.response.code === 'resume-required') {
      await this.resume()
      return
    }
    if (result.response.code === 'unknown-task') {
      await this.reestablish()
      return
    }
    throw responseError(result, 'Runtime task heartbeat was rejected')
  }

  async finish(outcome: RuntimeTaskOutcome): Promise<void> {
    if (this.finalized) return
    this.stopHeartbeatTimer()
    const finish = async () => postSupervisor(this.config, '/v1/tasks/finish', {
      runtime: this.runtime,
      taskId: this.taskId,
      outcome,
      eventId: nextEventId(this.runtime, `finish-${outcome}`),
    })
    let result = await finish()
    if (!result.response.ok && result.response.code === 'resume-required') {
      await this.resume()
      result = await finish()
    } else if (!result.response.ok && result.response.code === 'unknown-task') {
      await this.reestablish()
      result = await finish()
    }
    if (!result.response.ok) throw responseError(result, 'Failed to finish Runtime task lease')
    this.finalized = true
  }

  async processExit(exitCode?: number | null, signal?: string | null): Promise<void> {
    if (this.finalized) return
    this.stopHeartbeatTimer()
    const result = await postSupervisor(this.config, '/v1/tasks/process-exit', {
      runtime: this.runtime,
      taskId: this.taskId,
      exitCode,
      signal,
      eventId: nextEventId(this.runtime, 'process-exit'),
    })
    if (!result.response.ok && result.response.code !== 'unknown-task') {
      throw responseError(result, 'Failed to record Runtime task process exit')
    }
    this.finalized = true
  }

  abandon(): void {
    this.stopHeartbeatTimer()
  }
}

export function runtimeTaskId(runtime: RuntimeTaskKind, scope: string): string {
  const digest = createHash('sha256').update(`${runtime}\u0000${scope}`).digest('hex').slice(0, 40)
  return `${runtime}:${digest}`
}

export function stripRuntimeTaskSupervisorEnvironment(env: NodeJS.ProcessEnv): NodeJS.ProcessEnv {
  const sanitized = { ...env }
  for (const name of RUNTIME_TASK_SUPERVISOR_ENV_NAMES) delete sanitized[name]
  return sanitized
}

export async function acquireRuntimeTaskLease(input: AcquireRuntimeTaskLeaseInput): Promise<RuntimeTaskLeaseHandle> {
  const config = supervisorConfig()
  if (!config) {
    return new NoopRuntimeTaskLeaseHandle(
      input.runtime,
      input.taskId,
      input.workspace,
      input.access,
      input.processPid,
    )
  }
  if (input.requireProcess && !input.processPid) {
    throw new RuntimeTaskSupervisorError(
      `${input.runtime} task process is not verifiable`,
      'process-required',
      409,
    )
  }
  if (input.processPid !== undefined) assertPid(input.processPid)

  const started = await postSupervisor(config, '/v1/tasks/start', {
    runtime: input.runtime,
    taskId: input.taskId,
    workspace: input.workspace,
    access: input.access,
    eventId: nextEventId(input.runtime, 'start'),
  })
  if (!started.response.ok && started.response.code !== 'resume-required') {
    throw responseError(started, 'Failed to acquire Runtime task lease')
  }

  const handle = new ManagedRuntimeTaskLeaseHandle(
    config,
    input.runtime,
    input.taskId,
    input.workspace,
    input.access,
    input.processPid,
  )
  try {
    if (started.response.code === 'resume-required') {
      await handle.resume()
    } else if (input.processPid) {
      await handle.bindProcess(input.processPid)
    }
    return handle
  } catch (error) {
    handle.abandon()
    throw error
  }
}
