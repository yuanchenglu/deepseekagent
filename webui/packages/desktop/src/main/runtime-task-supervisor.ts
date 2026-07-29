import { createHash, randomBytes } from 'node:crypto'
import { execFile } from 'node:child_process'
import { chmodSync, closeSync, existsSync, mkdirSync, openSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs'
import { createServer, type IncomingMessage, type Server, type ServerResponse } from 'node:http'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { promisify } from 'node:util'
import {
  RuntimeTaskLeaseAdapter,
  RuntimeTaskLeaseCoordinator,
  type RuntimeKind,
  type RuntimeTaskLeaseResult,
} from './runtime-task-lease'
import type { WorkspaceAccess } from './workspace-lock'

const execFileAsync = promisify(execFile)
const DEFAULT_HEARTBEAT_TTL_MS = 30_000
const DEFAULT_MONITOR_INTERVAL_MS = 1_000
const MAX_REQUEST_BYTES = 64 * 1024
const STATE_SCHEMA_VERSION = 1

export interface RuntimeTaskProcessEvidence {
  pid: number
  fingerprint: string
  command: string
}

export interface RuntimeTaskProcessProbe {
  inspect(pid: number): Promise<RuntimeTaskProcessEvidence | null>
}

export interface RuntimeTaskSupervisorOptions {
  stateDir: string
  socketPath?: string
  tokenFile?: string
  stateFile?: string
  heartbeatTtlMs?: number
  monitorIntervalMs?: number
  coordinator?: RuntimeTaskLeaseCoordinator
  processProbe?: RuntimeTaskProcessProbe
  now?: () => number
}

export interface RuntimeTaskSupervisorEnvironment {
  DEEPAGENT_RUNTIME_LEASE_SOCKET: string
  DEEPAGENT_RUNTIME_LEASE_TOKEN: string
  DEEPAGENT_RUNTIME_LEASE_TTL_MS: string
}

interface RuntimeTaskStartRequest {
  runtime: RuntimeKind
  taskId: string
  workspace: string
  access: WorkspaceAccess
  eventId: string
}

interface RuntimeTaskResumeRequest {
  runtime: RuntimeKind
  taskId: string
  pid: number
  eventId: string
}

interface RuntimeTaskBindRequest extends RuntimeTaskResumeRequest {
  treeId?: string
}

interface RuntimeTaskHeartbeatRequest {
  runtime: RuntimeKind
  taskId: string
  eventId: string
}

interface RuntimeTaskFinishRequest extends RuntimeTaskHeartbeatRequest {
  outcome: 'completed' | 'failed' | 'cancelled'
}

interface RuntimeTaskProcessExitRequest extends RuntimeTaskHeartbeatRequest {
  exitCode?: number | null
  signal?: string | null
}

interface RuntimeTaskSupervisorResponse {
  ok: boolean
  code: string
  task?: RuntimeTaskSupervisorTask
  conflict?: RuntimeTaskLeaseResult['conflict']
  message?: string
}

export interface RuntimeTaskSupervisorTask {
  runtime: RuntimeKind
  taskId: string
  workspace: string
  access: WorkspaceAccess
  state: 'active' | 'orphaned'
  generation: number
  leaseId: string
  process?: RuntimeTaskProcessEvidence
  lastHeartbeatAt: number
  createdAt: number
}

interface PersistedTaskGeneration {
  runtime: RuntimeKind
  taskId: string
  generation: number
}

interface PersistedSupervisorState {
  schemaVersion: number
  tasks: RuntimeTaskSupervisorTask[]
  generations: PersistedTaskGeneration[]
}

interface SupervisorRecord extends RuntimeTaskSupervisorTask {
  internalTaskId: string
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function validRuntime(value: unknown): value is RuntimeKind {
  return value === 'deepagent' || value === 'deepcode'
}

function validAccess(value: unknown): value is WorkspaceAccess {
  return value === 'read' || value === 'write'
}

function validString(value: unknown, max = 256): value is string {
  return typeof value === 'string' && value.trim().length > 0 && value.length <= max
}

function validPid(value: unknown): value is number {
  return Number.isSafeInteger(value) && (value as number) > 0
}

function stableTaskKey(runtime: RuntimeKind, taskId: string): string {
  return `${runtime}\u0000${taskId}`
}

function safeInternalTaskId(runtime: RuntimeKind, taskId: string, generation: number): string {
  const digest = createHash('sha256').update(`${runtime}\u0000${taskId}`).digest('hex').slice(0, 24)
  return `task:${runtime}:${digest}:${generation}`
}

function defaultSocketPath(stateDir: string): string {
  const digest = createHash('sha256').update(resolve(stateDir)).digest('hex').slice(0, 20)
  return process.platform === 'win32'
    ? `\\\\.\\pipe\\deepagent-runtime-lease-${digest}`
    : join(tmpdir(), `deepagent-runtime-lease-${digest}.sock`)
}

function cloneTask(record: SupervisorRecord): RuntimeTaskSupervisorTask {
  return {
    runtime: record.runtime,
    taskId: record.taskId,
    workspace: record.workspace,
    access: record.access,
    state: record.state,
    generation: record.generation,
    leaseId: record.leaseId,
    process: record.process ? { ...record.process } : undefined,
    lastHeartbeatAt: record.lastHeartbeatAt,
    createdAt: record.createdAt,
  }
}

function sendJson(response: ServerResponse, status: number, body: RuntimeTaskSupervisorResponse): void {
  const payload = Buffer.from(JSON.stringify(body))
  response.statusCode = status
  response.setHeader('content-type', 'application/json; charset=utf-8')
  response.setHeader('content-length', String(payload.length))
  response.setHeader('connection', 'close')
  response.end(payload)
}

async function readJson(request: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = []
  let size = 0
  for await (const chunk of request) {
    const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)
    size += buffer.length
    if (size > MAX_REQUEST_BYTES) throw new Error('request-too-large')
    chunks.push(buffer)
  }
  if (chunks.length === 0) return {}
  return JSON.parse(Buffer.concat(chunks).toString('utf8'))
}

function windowsPowerShell(): string {
  const systemRoot = String(process.env.SystemRoot || '').trim()
  if (systemRoot) {
    const candidate = join(systemRoot, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
    if (existsSync(candidate)) return candidate
  }
  return 'powershell.exe'
}

export class SystemRuntimeTaskProcessProbe implements RuntimeTaskProcessProbe {
  async inspect(pid: number): Promise<RuntimeTaskProcessEvidence | null> {
    if (!validPid(pid)) return null
    return process.platform === 'win32'
      ? this.inspectWindows(pid)
      : this.inspectPosix(pid)
  }

  private async inspectPosix(pid: number): Promise<RuntimeTaskProcessEvidence | null> {
    try {
      const { stdout } = await execFileAsync('ps', ['-p', String(pid), '-o', 'lstart=', '-o', 'command='], {
        encoding: 'utf8',
        timeout: 5_000,
        maxBuffer: 64 * 1024,
      })
      const command = stdout.replace(/\s+/g, ' ').trim()
      if (!command) return null
      return {
        pid,
        fingerprint: createHash('sha256').update(command).digest('hex'),
        command: command.slice(0, 512),
      }
    } catch {
      return null
    }
  }

  private async inspectWindows(pid: number): Promise<RuntimeTaskProcessEvidence | null> {
    const script = [
      "$ErrorActionPreference = 'Stop'",
      `$target = Get-CimInstance Win32_Process -Filter \"ProcessId = ${pid}\"`,
      'if ($null -eq $target) { exit 3 }',
      "$creation = if ($target.CreationDate -is [DateTime]) { $target.CreationDate.ToUniversalTime().ToString('o') } else { [string]$target.CreationDate }",
      "[pscustomobject]@{ creation = $creation; executable = [string]$target.ExecutablePath; commandLine = [string]$target.CommandLine } | ConvertTo-Json -Compress",
    ].join('; ')
    try {
      const { stdout } = await execFileAsync(windowsPowerShell(), [
        '-NoProfile',
        '-NonInteractive',
        '-ExecutionPolicy',
        'Bypass',
        '-Command',
        script,
      ], {
        encoding: 'utf8',
        timeout: 5_000,
        maxBuffer: 64 * 1024,
        windowsHide: true,
      })
      const parsed = JSON.parse(stdout.trim()) as {
        creation?: unknown
        executable?: unknown
        commandLine?: unknown
      }
      const creation = String(parsed.creation || '').trim()
      const executable = String(parsed.executable || '').trim()
      const commandLine = String(parsed.commandLine || '').trim()
      if (!creation && !executable && !commandLine) return null
      const identity = [creation, executable, commandLine].join('\u0000')
      return {
        pid,
        fingerprint: createHash('sha256').update(identity).digest('hex'),
        command: (executable || commandLine || `pid ${pid}`).slice(0, 512),
      }
    } catch {
      return null
    }
  }
}

export class RuntimeTaskSupervisor {
  readonly stateDir: string
  readonly socketPath: string
  readonly tokenFile: string
  readonly stateFile: string
  readonly heartbeatTtlMs: number

  private readonly monitorIntervalMs: number
  private readonly coordinator: RuntimeTaskLeaseCoordinator
  private readonly adapters: Record<RuntimeKind, RuntimeTaskLeaseAdapter>
  private readonly processProbe: RuntimeTaskProcessProbe
  private readonly now: () => number
  private readonly records = new Map<string, SupervisorRecord>()
  private readonly generations = new Map<string, number>()
  private server: Server | null = null
  private monitorTimer: NodeJS.Timeout | null = null
  private token = ''
  private eventSequence = 0
  private mutation: Promise<void> = Promise.resolve()

  constructor(options: RuntimeTaskSupervisorOptions) {
    this.stateDir = resolve(options.stateDir)
    this.socketPath = options.socketPath || defaultSocketPath(this.stateDir)
    this.tokenFile = resolve(options.tokenFile || join(this.stateDir, 'auth-token'))
    this.stateFile = resolve(options.stateFile || join(this.stateDir, 'leases.json'))
    this.heartbeatTtlMs = options.heartbeatTtlMs ?? DEFAULT_HEARTBEAT_TTL_MS
    this.monitorIntervalMs = options.monitorIntervalMs ?? DEFAULT_MONITOR_INTERVAL_MS
    if (!Number.isFinite(this.heartbeatTtlMs) || this.heartbeatTtlMs < 1_000) throw new Error('Runtime task supervisor heartbeat TTL must be at least 1000ms')
    if (!Number.isFinite(this.monitorIntervalMs) || this.monitorIntervalMs < 100) throw new Error('Runtime task supervisor monitor interval must be at least 100ms')
    this.coordinator = options.coordinator ?? new RuntimeTaskLeaseCoordinator({
      defaultTtlMs: this.heartbeatTtlMs,
      minTtlMs: 1_000,
      maxTtlMs: Math.max(this.heartbeatTtlMs * 4, 5 * 60_000),
    })
    this.adapters = {
      deepagent: new RuntimeTaskLeaseAdapter('deepagent', this.coordinator),
      deepcode: new RuntimeTaskLeaseAdapter('deepcode', this.coordinator),
    }
    this.processProbe = options.processProbe ?? new SystemRuntimeTaskProcessProbe()
    this.now = options.now ?? (() => Date.now())
  }

  async start(): Promise<RuntimeTaskSupervisorEnvironment> {
    if (this.server) return this.environment()
    mkdirSync(this.stateDir, { recursive: true, mode: 0o700 })
    chmodSync(this.stateDir, 0o700)
    this.token = this.loadOrCreateToken()
    await this.restorePersistedTasks()
    if (process.platform !== 'win32') rmSync(this.socketPath, { force: true })
    this.server = createServer((request, response) => { void this.handleRequest(request, response) })
    await new Promise<void>((resolveStart, rejectStart) => {
      const server = this.server!
      const onError = (error: Error) => { server.off('listening', onListening); rejectStart(error) }
      const onListening = () => { server.off('error', onError); resolveStart() }
      server.once('error', onError)
      server.once('listening', onListening)
      server.listen(this.socketPath)
    })
    if (process.platform !== 'win32') chmodSync(this.socketPath, 0o600)
    this.monitorTimer = setInterval(() => { void this.serializeMutation(async () => this.inspectTasks()) }, this.monitorIntervalMs)
    this.monitorTimer.unref?.()
    return this.environment()
  }

  environment(): RuntimeTaskSupervisorEnvironment {
    if (!this.token) throw new Error('Runtime task supervisor is not started')
    return {
      DEEPAGENT_RUNTIME_LEASE_SOCKET: this.socketPath,
      DEEPAGENT_RUNTIME_LEASE_TOKEN: this.token,
      DEEPAGENT_RUNTIME_LEASE_TTL_MS: String(this.heartbeatTtlMs),
    }
  }

  listTasks(): RuntimeTaskSupervisorTask[] {
    return [...this.records.values()].map(cloneTask).sort((a, b) => `${a.runtime}:${a.taskId}`.localeCompare(`${b.runtime}:${b.taskId}`))
  }

  async stop(): Promise<void> {
    await this.serializeMutation(async () => {
      if (this.monitorTimer) { clearInterval(this.monitorTimer); this.monitorTimer = null }
      const runtimes = new Set<RuntimeKind>()
      for (const record of this.records.values()) if (record.state === 'active') runtimes.add(record.runtime)
      for (const runtime of runtimes) this.markRuntimeOrphaned(runtime, 'main-shutdown')
      this.persist()
    })
    const server = this.server
    this.server = null
    if (server) await new Promise<void>(resolveClose => server.close(() => resolveClose()))
    if (process.platform !== 'win32') rmSync(this.socketPath, { force: true })
  }

  private authenticated(request: IncomingMessage): boolean {
    return String(request.headers.authorization || '') === `Bearer ${this.token}`
  }

  private async handleRequest(request: IncomingMessage, response: ServerResponse): Promise<void> {
    if (!this.authenticated(request)) { sendJson(response, 401, { ok: false, code: 'unauthorized' }); return }
    if (request.method === 'GET' && request.url === '/health') { sendJson(response, 200, { ok: true, code: 'ready' }); return }
    if (request.method !== 'POST') { sendJson(response, 405, { ok: false, code: 'method-not-allowed' }); return }
    let body: unknown
    try { body = await readJson(request) } catch (error) {
      const code = error instanceof Error && error.message === 'request-too-large' ? 'request-too-large' : 'invalid-json'
      sendJson(response, code === 'request-too-large' ? 413 : 400, { ok: false, code }); return
    }
    try {
      const result = await this.serializeMutation(async () => {
        switch (request.url) {
          case '/v1/tasks/start': return this.startTask(body)
          case '/v1/tasks/bind-process': return this.bindProcess(body)
          case '/v1/tasks/heartbeat': return this.heartbeat(body)
          case '/v1/tasks/finish': return this.finishTask(body)
          case '/v1/tasks/process-exit': return this.processExit(body)
          case '/v1/tasks/resume': return this.resumeTask(body)
          default: return { status: 404, body: { ok: false, code: 'not-found' } as RuntimeTaskSupervisorResponse }
        }
      })
      sendJson(response, result.status, result.body)
    } catch (error) {
      sendJson(response, 500, { ok: false, code: 'internal-error', message: error instanceof Error ? error.message : String(error) })
    }
  }

  private startTask(value: unknown): { status: number; body: RuntimeTaskSupervisorResponse } {
    const request = this.parseStartRequest(value)
    if (!request) return { status: 400, body: { ok: false, code: 'invalid-request' } }
    const key = stableTaskKey(request.runtime, request.taskId)
    const existing = this.records.get(key)
    if (existing) {
      if (existing.workspace !== resolve(request.workspace) || existing.access !== request.access) return { status: 409, body: { ok: false, code: 'owner-mismatch', task: cloneTask(existing) } }
      if (existing.state === 'orphaned') return { status: 409, body: { ok: false, code: 'resume-required', task: cloneTask(existing) } }
      return { status: 200, body: { ok: true, code: 'already-active', task: cloneTask(existing) } }
    }
    const generation = request.runtime === 'deepagent'
      ? (this.generations.get(key) || 0) + 1
      : 1
    const internalTaskId = safeInternalTaskId(request.runtime, request.taskId, generation)
    const result = this.adapters[request.runtime].dispatch({
      type: 'acquire', eventId: request.eventId, observedAt: this.now(), ttlMs: this.heartbeatTtlMs,
      identity: { workspace: request.workspace, taskId: internalTaskId, access: request.access },
    })
    if (!result.ok || !result.lease) return { status: result.code === 'conflict' ? 409 : 400, body: { ok: false, code: result.code, conflict: result.conflict, message: result.message } }
    const now = this.now()
    const record: SupervisorRecord = {
      runtime: request.runtime, taskId: request.taskId, workspace: result.lease.identity.workspace, access: request.access,
      state: 'active', generation, leaseId: result.lease.leaseId, internalTaskId, lastHeartbeatAt: now, createdAt: now,
    }
    this.records.set(key, record)
    if (request.runtime === 'deepagent') this.generations.set(key, generation)
    this.persist()
    return { status: 201, body: { ok: true, code: 'acquired', task: cloneTask(record) } }
  }

  private async bindProcess(value: unknown): Promise<{ status: number; body: RuntimeTaskSupervisorResponse }> {
    const request = this.parseBindRequest(value)
    if (!request) return { status: 400, body: { ok: false, code: 'invalid-request' } }
    const record = this.records.get(stableTaskKey(request.runtime, request.taskId))
    if (!record) return { status: 404, body: { ok: false, code: 'unknown-task' } }
    if (record.state !== 'active') return { status: 409, body: { ok: false, code: 'resume-required', task: cloneTask(record) } }
    const evidence = await this.processProbe.inspect(request.pid)
    if (!evidence) return { status: 409, body: { ok: false, code: 'process-unverifiable' } }
    if (record.process) {
      if (record.process.pid === evidence.pid && record.process.fingerprint === evidence.fingerprint) return { status: 200, body: { ok: true, code: 'already-bound', task: cloneTask(record) } }
      return { status: 409, body: { ok: false, code: 'owner-mismatch', task: cloneTask(record) } }
    }
    const result = this.coordinator.dispatch({
      type: 'bind-process', eventId: request.eventId, observedAt: this.now(), runtime: record.runtime,
      taskId: record.internalTaskId, leaseId: record.leaseId,
      process: { pid: evidence.pid, treeId: request.treeId || evidence.fingerprint.slice(0, 32) },
    })
    if (!result.ok) return { status: 409, body: { ok: false, code: result.code, message: result.message } }
    record.process = evidence
    record.lastHeartbeatAt = this.now()
    this.persist()
    return { status: 200, body: { ok: true, code: 'process-bound', task: cloneTask(record) } }
  }

  private heartbeat(value: unknown): { status: number; body: RuntimeTaskSupervisorResponse } {
    const request = this.parseHeartbeatRequest(value)
    if (!request) return { status: 400, body: { ok: false, code: 'invalid-request' } }
    const record = this.records.get(stableTaskKey(request.runtime, request.taskId))
    if (!record) return { status: 404, body: { ok: false, code: 'unknown-task' } }
    if (record.state !== 'active') return { status: 409, body: { ok: false, code: 'resume-required', task: cloneTask(record) } }
    const result = this.adapters[record.runtime].dispatch({
      type: 'heartbeat', eventId: request.eventId, observedAt: this.now(), taskId: record.internalTaskId,
      leaseId: record.leaseId, ttlMs: this.heartbeatTtlMs,
    })
    if (!result.ok) return { status: 409, body: { ok: false, code: result.code, message: result.message } }
    record.lastHeartbeatAt = this.now()
    this.persist()
    return { status: 200, body: { ok: true, code: 'heartbeat-accepted', task: cloneTask(record) } }
  }

  private finishTask(value: unknown): { status: number; body: RuntimeTaskSupervisorResponse } {
    const request = this.parseFinishRequest(value)
    if (!request) return { status: 400, body: { ok: false, code: 'invalid-request' } }
    const key = stableTaskKey(request.runtime, request.taskId)
    const record = this.records.get(key)
    if (!record) return { status: 200, body: { ok: true, code: 'already-terminal' } }
    if (record.state === 'orphaned') {
      // A task restored without process evidence must remain fail-closed: it may
      // not bind or resume an arbitrary PID. The original Runtime can still
      // explicitly confirm that the unbound attempt is terminal, which closes
      // the orphaned coordinator lease through the existing process-exit path.
      if (record.process) return { status: 409, body: { ok: false, code: 'resume-required', task: cloneTask(record) } }
      const terminal = this.coordinator.dispatch({
        type: 'process-exit', eventId: request.eventId, observedAt: this.now(), runtime: record.runtime,
        taskId: record.internalTaskId, leaseId: record.leaseId, exitCode: null, signal: null,
      })
      if (!terminal.ok) return { status: 409, body: { ok: false, code: terminal.code, message: terminal.message } }
      this.records.delete(key)
      this.persist()
      return { status: 200, body: { ok: true, code: request.outcome } }
    }
    const result = request.outcome === 'cancelled'
      ? this.adapters[record.runtime].dispatch({ type: 'cancel', eventId: request.eventId, observedAt: this.now(), taskId: record.internalTaskId, leaseId: record.leaseId, reason: 'cancelled-by-runtime' })
      : this.adapters[record.runtime].dispatch({ type: 'release', eventId: request.eventId, observedAt: this.now(), taskId: record.internalTaskId, leaseId: record.leaseId })
    if (!result.ok) return { status: 409, body: { ok: false, code: result.code, message: result.message } }
    this.records.delete(key)
    this.persist()
    return { status: 200, body: { ok: true, code: request.outcome } }
  }

  private processExit(value: unknown): { status: number; body: RuntimeTaskSupervisorResponse } {
    const request = this.parseProcessExitRequest(value)
    if (!request) return { status: 400, body: { ok: false, code: 'invalid-request' } }
    const key = stableTaskKey(request.runtime, request.taskId)
    const record = this.records.get(key)
    if (!record) return { status: 200, body: { ok: true, code: 'already-terminal' } }
    const result = this.coordinator.dispatch({
      type: 'process-exit', eventId: request.eventId, observedAt: this.now(), runtime: record.runtime,
      taskId: record.internalTaskId, leaseId: record.leaseId, exitCode: request.exitCode, signal: request.signal,
    })
    if (!result.ok) return { status: 409, body: { ok: false, code: result.code, message: result.message } }
    this.records.delete(key)
    this.persist()
    return { status: 200, body: { ok: true, code: result.code } }
  }

  private async resumeTask(value: unknown): Promise<{ status: number; body: RuntimeTaskSupervisorResponse }> {
    const request = this.parseResumeRequest(value)
    if (!request) return { status: 400, body: { ok: false, code: 'invalid-request' } }
    const key = stableTaskKey(request.runtime, request.taskId)
    const record = this.records.get(key)
    if (!record) return { status: 404, body: { ok: false, code: 'unknown-task' } }
    if (record.state === 'active') return { status: 200, body: { ok: true, code: 'already-active', task: cloneTask(record) } }
    if (!record.process || record.process.pid !== request.pid) return { status: 409, body: { ok: false, code: 'process-mismatch', task: cloneTask(record) } }
    const evidence = await this.processProbe.inspect(request.pid)
    if (!evidence || evidence.fingerprint !== record.process.fingerprint) return { status: 409, body: { ok: false, code: 'process-mismatch', task: cloneTask(record) } }
    const recovered = this.coordinator.dispatch({
      type: 'recover', eventId: `${request.eventId}:recover`, observedAt: this.now(), runtime: record.runtime,
      taskId: record.internalTaskId, leaseId: record.leaseId, reason: 'verified-process-resume',
    })
    if (!recovered.ok) return { status: 409, body: { ok: false, code: recovered.code, message: recovered.message } }
    const generation = record.generation + 1
    const internalTaskId = safeInternalTaskId(record.runtime, record.taskId, generation)
    const acquired = this.adapters[record.runtime].dispatch({
      type: 'acquire', eventId: `${request.eventId}:acquire`, observedAt: this.now(), ttlMs: this.heartbeatTtlMs,
      identity: { workspace: record.workspace, taskId: internalTaskId, access: record.access },
    })
    if (!acquired.ok || !acquired.lease) { this.records.delete(key); this.persist(); return { status: 409, body: { ok: false, code: acquired.code, conflict: acquired.conflict } } }
    const bound = this.coordinator.dispatch({
      type: 'bind-process', eventId: `${request.eventId}:bind`, observedAt: this.now(), runtime: record.runtime,
      taskId: internalTaskId, leaseId: acquired.lease.leaseId,
      process: { pid: evidence.pid, treeId: evidence.fingerprint.slice(0, 32) },
    })
    if (!bound.ok) {
      this.adapters[record.runtime].dispatch({ type: 'release', eventId: `${request.eventId}:rollback`, observedAt: this.now(), taskId: internalTaskId, leaseId: acquired.lease.leaseId })
      this.records.delete(key); this.persist(); return { status: 409, body: { ok: false, code: bound.code, message: bound.message } }
    }
    record.internalTaskId = internalTaskId
    record.generation = generation
    record.leaseId = acquired.lease.leaseId
    record.state = 'active'
    record.process = evidence
    record.lastHeartbeatAt = this.now()
    if (record.runtime === 'deepagent') this.generations.set(key, generation)
    this.persist()
    return { status: 200, body: { ok: true, code: 'resumed', task: cloneTask(record) } }
  }

  private async inspectTasks(): Promise<void> {
    const now = this.now()
    const staleRuntimes = new Set<RuntimeKind>()
    for (const [key, record] of [...this.records]) {
      // Orphaned tasks intentionally remain fail-closed. A missing or reused PID is
      // not sufficient evidence to release their workspace after Runtime/Main loss;
      // only an explicit process-exit confirmation or verified resume may do so.
      if (record.state === 'orphaned') continue
      if (!record.process) {
        if (now - record.lastHeartbeatAt >= this.heartbeatTtlMs) staleRuntimes.add(record.runtime)
        continue
      }
      const evidence = await this.processProbe.inspect(record.process.pid)
      if (!evidence || evidence.fingerprint !== record.process.fingerprint) {
        const result = this.coordinator.dispatch({
          type: 'process-exit', eventId: this.nextEventId('probe-exit'), observedAt: now, runtime: record.runtime,
          taskId: record.internalTaskId, leaseId: record.leaseId, exitCode: null, signal: null,
        })
        if (result.ok) this.records.delete(key)
        continue
      }
      if (now - record.lastHeartbeatAt >= this.heartbeatTtlMs) staleRuntimes.add(record.runtime)
    }
    for (const runtime of staleRuntimes) this.markRuntimeOrphaned(runtime, 'heartbeat-timeout')
    this.persist()
  }

  private markRuntimeOrphaned(runtime: RuntimeKind, reason: string): void {
    this.coordinator.dispatch({ type: 'runtime-crash', eventId: this.nextEventId(`runtime-crash:${reason}`), observedAt: this.now(), runtime, reason })
    for (const record of this.records.values()) if (record.runtime === runtime && record.state === 'active') record.state = 'orphaned'
  }

  private async restorePersistedTasks(): Promise<void> {
    const persisted = this.readState()
    const activeRuntimes = new Set<RuntimeKind>()
    for (const item of persisted.generations) {
      if (item.runtime !== 'deepagent' || !validString(item.taskId) || !Number.isSafeInteger(item.generation) || item.generation < 1) continue
      this.generations.set(stableTaskKey(item.runtime, item.taskId), item.generation)
    }
    for (const task of persisted.tasks) {
      if (!validRuntime(task.runtime) || !validAccess(task.access) || !validString(task.taskId) || !validString(task.workspace, 4_096)) continue
      if (task.process && (!validPid(task.process.pid) || !validString(task.process.fingerprint, 128))) continue
      const evidence = task.process ? await this.processProbe.inspect(task.process.pid) : null
      const processVerified = Boolean(evidence && task.process && evidence.fingerprint === task.process.fingerprint)
      const key = stableTaskKey(task.runtime, task.taskId)
      const generation = task.runtime === 'deepagent'
        ? Math.max(1, task.generation || 1, this.generations.get(key) || 0)
        : Math.max(1, task.generation || 1)
      if (task.runtime === 'deepagent') this.generations.set(key, generation)
      const internalTaskId = safeInternalTaskId(task.runtime, task.taskId, generation)
      const acquired = this.adapters[task.runtime].dispatch({
        type: 'acquire', eventId: this.nextEventId('restore-acquire'), observedAt: this.now(), ttlMs: this.heartbeatTtlMs,
        identity: { workspace: task.workspace, taskId: internalTaskId, access: task.access },
      })
      if (!acquired.ok || !acquired.lease) continue
      if (processVerified && evidence) {
        const bound = this.coordinator.dispatch({
          type: 'bind-process', eventId: this.nextEventId('restore-bind'), observedAt: this.now(), runtime: task.runtime,
          taskId: internalTaskId, leaseId: acquired.lease.leaseId,
          process: { pid: evidence.pid, treeId: evidence.fingerprint.slice(0, 32) },
        })
        if (!bound.ok) {
          this.adapters[task.runtime].dispatch({
            type: 'release', eventId: this.nextEventId('restore-bind-rollback'), observedAt: this.now(),
            taskId: internalTaskId, leaseId: acquired.lease.leaseId,
          })
          continue
        }
      }
      this.records.set(key, {
        ...task, workspace: resolve(task.workspace), state: 'active', leaseId: acquired.lease.leaseId,
        internalTaskId,
        process: processVerified && evidence ? evidence : task.process ? { ...task.process } : undefined,
        lastHeartbeatAt: this.now(), generation,
      })
      activeRuntimes.add(task.runtime)
    }
    for (const runtime of activeRuntimes) this.markRuntimeOrphaned(runtime, 'main-restart')
    this.persist()
  }

  private loadOrCreateToken(): string {
    try { const token = readFileSync(this.tokenFile, 'utf8').trim(); if (token.length >= 32) return token } catch {}
    mkdirSync(dirname(this.tokenFile), { recursive: true, mode: 0o700 })
    const token = randomBytes(32).toString('hex')
    const fd = openSync(this.tokenFile, 'w', 0o600)
    try { writeFileSync(fd, `${token}\n`, 'utf8') } finally { closeSync(fd) }
    chmodSync(this.tokenFile, 0o600)
    return token
  }

  private readState(): PersistedSupervisorState {
    if (!existsSync(this.stateFile)) return { schemaVersion: STATE_SCHEMA_VERSION, tasks: [], generations: [] }
    try {
      const parsed = JSON.parse(readFileSync(this.stateFile, 'utf8')) as Partial<PersistedSupervisorState>
      return parsed.schemaVersion === STATE_SCHEMA_VERSION && Array.isArray(parsed.tasks)
        ? {
            schemaVersion: STATE_SCHEMA_VERSION,
            tasks: parsed.tasks as RuntimeTaskSupervisorTask[],
            generations: Array.isArray(parsed.generations) ? parsed.generations as PersistedTaskGeneration[] : [],
          }
        : { schemaVersion: STATE_SCHEMA_VERSION, tasks: [], generations: [] }
    } catch { return { schemaVersion: STATE_SCHEMA_VERSION, tasks: [], generations: [] } }
  }

  private persist(): void {
    mkdirSync(dirname(this.stateFile), { recursive: true, mode: 0o700 })
    const temporary = `${this.stateFile}.tmp-${process.pid}-${Date.now()}`
    const generations = [...this.generations].map(([key, generation]) => {
      const separator = key.indexOf('\u0000')
      return { runtime: key.slice(0, separator) as RuntimeKind, taskId: key.slice(separator + 1), generation }
    }).sort((left, right) => `${left.runtime}:${left.taskId}`.localeCompare(`${right.runtime}:${right.taskId}`))
    const payload: PersistedSupervisorState = {
      schemaVersion: STATE_SCHEMA_VERSION,
      tasks: this.listTasks(),
      generations,
    }
    const fd = openSync(temporary, 'w', 0o600)
    try { writeFileSync(fd, `${JSON.stringify(payload, null, 2)}\n`, 'utf8') } finally { closeSync(fd) }
    chmodSync(temporary, 0o600)
    renameSync(temporary, this.stateFile)
  }

  private nextEventId(prefix: string): string { this.eventSequence += 1; return `main:${prefix}:${this.eventSequence}` }

  private serializeMutation<T>(operation: () => Promise<T> | T): Promise<T> {
    const next = this.mutation.then(operation, operation)
    this.mutation = next.then(() => undefined, () => undefined)
    return next
  }

  private parseStartRequest(value: unknown): RuntimeTaskStartRequest | null {
    if (!isRecord(value) || !validRuntime(value.runtime) || !validAccess(value.access)) return null
    if (!validString(value.taskId) || !validString(value.workspace, 4_096) || !validString(value.eventId)) return null
    return { runtime: value.runtime, taskId: value.taskId, workspace: value.workspace, access: value.access, eventId: value.eventId }
  }

  private parseBindRequest(value: unknown): RuntimeTaskBindRequest | null {
    if (!isRecord(value) || !validRuntime(value.runtime) || !validPid(value.pid)) return null
    if (!validString(value.taskId) || !validString(value.eventId)) return null
    if (value.treeId !== undefined && !validString(value.treeId)) return null
    return { runtime: value.runtime, taskId: value.taskId, pid: value.pid, eventId: value.eventId, treeId: value.treeId as string | undefined }
  }

  private parseResumeRequest(value: unknown): RuntimeTaskResumeRequest | null {
    if (!isRecord(value) || !validRuntime(value.runtime) || !validPid(value.pid)) return null
    if (!validString(value.taskId) || !validString(value.eventId)) return null
    return { runtime: value.runtime, taskId: value.taskId, pid: value.pid, eventId: value.eventId }
  }

  private parseHeartbeatRequest(value: unknown): RuntimeTaskHeartbeatRequest | null {
    if (!isRecord(value) || !validRuntime(value.runtime) || !validString(value.taskId) || !validString(value.eventId)) return null
    return { runtime: value.runtime, taskId: value.taskId, eventId: value.eventId }
  }

  private parseFinishRequest(value: unknown): RuntimeTaskFinishRequest | null {
    const base = this.parseHeartbeatRequest(value)
    if (!base || !isRecord(value) || (value.outcome !== 'completed' && value.outcome !== 'failed' && value.outcome !== 'cancelled')) return null
    return { ...base, outcome: value.outcome }
  }

  private parseProcessExitRequest(value: unknown): RuntimeTaskProcessExitRequest | null {
    const base = this.parseHeartbeatRequest(value)
    if (!base || !isRecord(value)) return null
    if (value.exitCode !== undefined && value.exitCode !== null && !Number.isSafeInteger(value.exitCode)) return null
    if (value.signal !== undefined && value.signal !== null && typeof value.signal !== 'string') return null
    return { ...base, exitCode: value.exitCode as number | null | undefined, signal: value.signal as string | null | undefined }
  }
}
