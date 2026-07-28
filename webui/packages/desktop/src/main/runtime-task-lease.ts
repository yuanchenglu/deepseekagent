import { resolve } from 'node:path'
import { WorkspaceLockManager, type WorkspaceAccess } from './workspace-lock'

/**
 * Main-process authority for Runtime Task / Workspace Lease state.
 *
 * This module deliberately stops at the typed protocol and deterministic state
 * machine. Binding the protocol to real child-process PID trees is a separate
 * work unit. The coordinator fails closed: an orphaned task keeps its
 * workspace lock until an explicit recovery or process-exit event proves it is
 * safe to release.
 */

export type RuntimeKind = 'deepagent' | 'deepcode'
export type RuntimeTaskLeaseState =
  | 'pending'
  | 'active'
  | 'releasing'
  | 'released'
  | 'expired'
  | 'orphaned'
  | 'recovered'

export type RuntimeTaskLeaseEventType =
  | 'acquire'
  | 'bind-process'
  | 'heartbeat'
  | 'release'
  | 'cancel'
  | 'timeout'
  | 'process-exit'
  | 'runtime-crash'
  | 'recover'

export type RuntimeTaskLeaseErrorCode =
  | 'invalid-request'
  | 'conflict'
  | 'unknown-task'
  | 'expired-lease'
  | 'owner-mismatch'
  | 'invalid-state'
  | 'replay-conflict'
  | 'recovery-failed'

export type RuntimeTaskLeaseSuccessCode =
  | 'acquired'
  | 'already-acquired'
  | 'process-bound'
  | 'heartbeat-accepted'
  | 'released'
  | 'cancelled'
  | 'expired'
  | 'orphaned'
  | 'recovered'
  | 'already-terminal'

export interface RuntimeProcessIdentity {
  pid?: number
  treeId?: string
}

export interface RuntimeTaskLeaseIdentity {
  runtime: RuntimeKind
  workspace: string
  taskId: string
  access: WorkspaceAccess
  process?: RuntimeProcessIdentity
}

export interface RuntimeTaskLeaseSnapshot {
  leaseId: string
  identity: RuntimeTaskLeaseIdentity
  state: RuntimeTaskLeaseState
  revision: number
  createdAt: number
  acquiredAt?: number
  lastHeartbeatAt?: number
  expiresAt?: number
  terminalAt?: number
  terminalReason?: 'released' | 'cancelled' | 'timeout' | 'process-exit' | 'runtime-crash' | 'recovered'
}

interface CommandBase {
  eventId: string
  type: RuntimeTaskLeaseEventType
  observedAt: number
}

export interface AcquireLeaseCommand extends CommandBase {
  type: 'acquire'
  identity: RuntimeTaskLeaseIdentity
  ttlMs?: number
}

interface TaskLeaseCommandBase extends CommandBase {
  runtime: RuntimeKind
  taskId: string
  leaseId: string
}

export interface BindProcessLeaseCommand extends TaskLeaseCommandBase {
  type: 'bind-process'
  process: RuntimeProcessIdentity
}

export interface HeartbeatLeaseCommand extends TaskLeaseCommandBase {
  type: 'heartbeat'
  ttlMs?: number
}

export interface ReleaseLeaseCommand extends TaskLeaseCommandBase {
  type: 'release'
}

export interface CancelLeaseCommand extends TaskLeaseCommandBase {
  type: 'cancel'
  reason?: string
}

export interface TimeoutLeaseCommand extends TaskLeaseCommandBase {
  type: 'timeout'
}

export interface ProcessExitLeaseCommand extends TaskLeaseCommandBase {
  type: 'process-exit'
  exitCode?: number | null
  signal?: string | null
}

export interface RecoverLeaseCommand extends TaskLeaseCommandBase {
  type: 'recover'
  reason?: string
}

export interface RuntimeCrashLeaseCommand extends CommandBase {
  type: 'runtime-crash'
  runtime: RuntimeKind
  reason?: string
}

export type RuntimeTaskLeaseCommand =
  | AcquireLeaseCommand
  | BindProcessLeaseCommand
  | HeartbeatLeaseCommand
  | ReleaseLeaseCommand
  | CancelLeaseCommand
  | TimeoutLeaseCommand
  | ProcessExitLeaseCommand
  | RecoverLeaseCommand
  | RuntimeCrashLeaseCommand

export interface RuntimeTaskLeaseConflict {
  workspace: string
  writerLeaseId: string | null
  readerLeaseIds: string[]
}

export interface RuntimeTaskLeaseResult {
  ok: boolean
  eventId: string
  type: RuntimeTaskLeaseEventType | 'invalid'
  code: RuntimeTaskLeaseSuccessCode | RuntimeTaskLeaseErrorCode
  lease?: RuntimeTaskLeaseSnapshot
  affected?: RuntimeTaskLeaseSnapshot[]
  conflict?: RuntimeTaskLeaseConflict
  message?: string
}

export interface RuntimeTaskLeaseTransition {
  sequence: number
  eventId: string
  type: RuntimeTaskLeaseEventType
  runtime: RuntimeKind
  taskId?: string
  leaseId?: string
  from?: RuntimeTaskLeaseState
  to?: RuntimeTaskLeaseState
  at: number
  code: RuntimeTaskLeaseSuccessCode | RuntimeTaskLeaseErrorCode
}

export interface RuntimeTaskLeaseCoordinatorOptions {
  defaultTtlMs?: number
  minTtlMs?: number
  maxTtlMs?: number
  maxReplayEntries?: number
  locks?: WorkspaceLockManager
}

/** Commands accepted from a runtime-scoped connection. */
export type RuntimeScopedLeaseCommand =
  | Omit<AcquireLeaseCommand, 'identity'> & { identity: Omit<RuntimeTaskLeaseIdentity, 'runtime'> }
  | Omit<HeartbeatLeaseCommand, 'runtime'>
  | Omit<ReleaseLeaseCommand, 'runtime'>
  | Omit<CancelLeaseCommand, 'runtime'>

/** Supervisory commands that only trusted Electron Main code may dispatch. */
export type MainOnlyLeaseCommand =
  | BindProcessLeaseCommand
  | TimeoutLeaseCommand
  | ProcessExitLeaseCommand
  | RecoverLeaseCommand
  | RuntimeCrashLeaseCommand

const IDENTIFIER_PATTERN = /^[A-Za-z0-9._:-]{1,128}$/
const DEFAULT_TTL_MS = 30_000
const MIN_TTL_MS = 1_000
const MAX_TTL_MS = 5 * 60_000
const DEFAULT_MAX_REPLAY_ENTRIES = 4_096
const RUNTIME_SCOPED_EVENT_TYPES = new Set<RuntimeTaskLeaseEventType>([
  'acquire',
  'heartbeat',
  'release',
  'cancel',
])

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function validIdentifier(value: unknown): value is string {
  return typeof value === 'string' && IDENTIFIER_PATTERN.test(value)
}

function validTimestamp(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0
}

function validRuntime(value: unknown): value is RuntimeKind {
  return value === 'deepagent' || value === 'deepcode'
}

function validAccess(value: unknown): value is WorkspaceAccess {
  return value === 'read' || value === 'write'
}

function validEventType(value: unknown): value is RuntimeTaskLeaseEventType {
  return value === 'acquire'
    || value === 'bind-process'
    || value === 'heartbeat'
    || value === 'release'
    || value === 'cancel'
    || value === 'timeout'
    || value === 'process-exit'
    || value === 'runtime-crash'
    || value === 'recover'
}

function commandRuntime(value: unknown): RuntimeKind | 'invalid' {
  if (!isRecord(value)) return 'invalid'
  if (validRuntime(value.runtime)) return value.runtime
  if (isRecord(value.identity) && validRuntime(value.identity.runtime)) return value.identity.runtime
  return 'invalid'
}

function replayKey(value: unknown, eventId: string): string {
  return `${commandRuntime(value)}\u0000${eventId}`
}

function validLeaseState(value: RuntimeTaskLeaseState, allowed: RuntimeTaskLeaseState[]): boolean {
  return allowed.includes(value)
}

function cloneIdentity(identity: RuntimeTaskLeaseIdentity): RuntimeTaskLeaseIdentity {
  return {
    ...identity,
    process: identity.process ? { ...identity.process } : undefined,
  }
}

function cloneSnapshot(snapshot: RuntimeTaskLeaseSnapshot): RuntimeTaskLeaseSnapshot {
  return {
    ...snapshot,
    identity: cloneIdentity(snapshot.identity),
  }
}

function cloneResult(result: RuntimeTaskLeaseResult): RuntimeTaskLeaseResult {
  return {
    ...result,
    lease: result.lease ? cloneSnapshot(result.lease) : undefined,
    affected: result.affected?.map(cloneSnapshot),
    conflict: result.conflict
      ? { ...result.conflict, readerLeaseIds: [...result.conflict.readerLeaseIds] }
      : undefined,
  }
}

function stableValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stableValue)
  if (!isRecord(value)) return value
  return Object.fromEntries(
    Object.entries(value)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => [key, stableValue(item)]),
  )
}

function fingerprint(value: unknown): string {
  try {
    return JSON.stringify(stableValue(value))
  } catch {
    return '[unserializable]'
  }
}

function sameProcess(left?: RuntimeProcessIdentity, right?: RuntimeProcessIdentity): boolean {
  return left?.pid === right?.pid && left?.treeId === right?.treeId
}

function sameAcquireIdentity(existing: RuntimeTaskLeaseIdentity, requested: RuntimeTaskLeaseIdentity): boolean {
  return existing.runtime === requested.runtime
    && existing.workspace === requested.workspace
    && existing.taskId === requested.taskId
    && existing.access === requested.access
    && (requested.process === undefined || sameProcess(existing.process, requested.process))
}

function taskKey(runtime: RuntimeKind, taskId: string): string {
  return `${runtime}\u0000${taskId}`
}

function ownerId(runtime: RuntimeKind): string {
  return `runtime:${runtime}`
}

function normalizeProcess(value: unknown): RuntimeProcessIdentity | undefined | null {
  if (value === undefined) return undefined
  if (!isRecord(value)) return null
  const pid = value.pid
  const treeId = value.treeId
  if (pid !== undefined && (!Number.isSafeInteger(pid) || (pid as number) <= 0)) return null
  if (treeId !== undefined && !validIdentifier(treeId)) return null
  if (pid === undefined && treeId === undefined) return undefined
  return {
    ...(pid !== undefined ? { pid: pid as number } : {}),
    ...(treeId !== undefined ? { treeId: treeId as string } : {}),
  }
}

function normalizeIdentity(value: unknown): RuntimeTaskLeaseIdentity | null {
  if (!isRecord(value)) return null
  if (!validRuntime(value.runtime) || !validIdentifier(value.taskId) || !validAccess(value.access)) return null
  if (typeof value.workspace !== 'string' || value.workspace.trim().length === 0) return null
  const process = normalizeProcess(value.process)
  if (process === null) return null
  return {
    runtime: value.runtime,
    workspace: resolve(value.workspace),
    taskId: value.taskId,
    access: value.access,
    process,
  }
}

function normalizeOptionalString(value: unknown): string | undefined | null {
  if (value === undefined) return undefined
  if (typeof value !== 'string') return null
  return value.slice(0, 512)
}

function normalizeCommand(value: unknown): RuntimeTaskLeaseCommand | null {
  if (!isRecord(value) || !validIdentifier(value.eventId) || !validTimestamp(value.observedAt)) return null
  const type = value.type
  if (type === 'acquire') {
    const identity = normalizeIdentity(value.identity)
    if (!identity) return null
    if (value.ttlMs !== undefined && (!Number.isFinite(value.ttlMs) || (value.ttlMs as number) <= 0)) return null
    return {
      eventId: value.eventId,
      type,
      observedAt: value.observedAt,
      identity,
      ...(value.ttlMs !== undefined ? { ttlMs: value.ttlMs as number } : {}),
    }
  }
  if (type === 'runtime-crash') {
    if (!validRuntime(value.runtime)) return null
    const reason = normalizeOptionalString(value.reason)
    if (reason === null) return null
    return {
      eventId: value.eventId,
      type,
      observedAt: value.observedAt,
      runtime: value.runtime,
      ...(reason !== undefined ? { reason } : {}),
    }
  }
  if (
    type !== 'bind-process'
    && type !== 'heartbeat'
    && type !== 'release'
    && type !== 'cancel'
    && type !== 'timeout'
    && type !== 'process-exit'
    && type !== 'recover'
  ) return null
  if (!validRuntime(value.runtime) || !validIdentifier(value.taskId) || !validIdentifier(value.leaseId)) return null

  const base = {
    eventId: value.eventId,
    type,
    observedAt: value.observedAt,
    runtime: value.runtime,
    taskId: value.taskId,
    leaseId: value.leaseId,
  }
  if (type === 'bind-process') {
    const process = normalizeProcess(value.process)
    if (!process || (process.pid === undefined && process.treeId === undefined)) return null
    return { ...base, type, process }
  }
  if (type === 'heartbeat') {
    if (value.ttlMs !== undefined && (!Number.isFinite(value.ttlMs) || (value.ttlMs as number) <= 0)) return null
    return { ...base, type, ...(value.ttlMs !== undefined ? { ttlMs: value.ttlMs as number } : {}) }
  }
  if (type === 'cancel' || type === 'recover') {
    const reason = normalizeOptionalString(value.reason)
    if (reason === null) return null
    return { ...base, type, ...(reason !== undefined ? { reason } : {}) }
  }
  if (type === 'process-exit') {
    const exitCode = value.exitCode
    const signal = value.signal
    if (exitCode !== undefined && exitCode !== null && !Number.isSafeInteger(exitCode)) return null
    if (signal !== undefined && signal !== null && typeof signal !== 'string') return null
    return {
      ...base,
      type,
      ...(exitCode !== undefined ? { exitCode: exitCode as number | null } : {}),
      ...(signal !== undefined ? { signal: signal as string | null } : {}),
    }
  }
  return { ...base, type }
}

export class RuntimeTaskLeaseCoordinator {
  private readonly defaultTtlMs: number
  private readonly minTtlMs: number
  private readonly maxTtlMs: number
  private readonly maxReplayEntries: number
  private readonly locks: WorkspaceLockManager
  private readonly leases = new Map<string, RuntimeTaskLeaseSnapshot>()
  private readonly replay = new Map<string, { fingerprint: string; result: RuntimeTaskLeaseResult }>()
  private readonly transitions: RuntimeTaskLeaseTransition[] = []
  private leaseSequence = 0
  private transitionSequence = 0

  constructor(options: RuntimeTaskLeaseCoordinatorOptions = {}) {
    this.minTtlMs = options.minTtlMs ?? MIN_TTL_MS
    this.maxTtlMs = options.maxTtlMs ?? MAX_TTL_MS
    this.defaultTtlMs = options.defaultTtlMs ?? DEFAULT_TTL_MS
    this.maxReplayEntries = options.maxReplayEntries ?? DEFAULT_MAX_REPLAY_ENTRIES
    if (
      !Number.isFinite(this.minTtlMs)
      || !Number.isFinite(this.maxTtlMs)
      || !Number.isFinite(this.defaultTtlMs)
      || this.minTtlMs <= 0
      || this.maxTtlMs < this.minTtlMs
      || this.defaultTtlMs < this.minTtlMs
      || this.defaultTtlMs > this.maxTtlMs
      || !Number.isSafeInteger(this.maxReplayEntries)
      || this.maxReplayEntries <= 0
    ) {
      throw new Error('Invalid RuntimeTaskLeaseCoordinator configuration')
    }
    this.locks = options.locks ?? new WorkspaceLockManager()
  }

  dispatch(input: unknown): RuntimeTaskLeaseResult {
    const rawEventId = isRecord(input) && typeof input.eventId === 'string' ? input.eventId : ''
    const rawFingerprint = fingerprint(input)
    const scopedReplayKey = rawEventId ? replayKey(input, rawEventId) : ''
    const replayed = scopedReplayKey ? this.replay.get(scopedReplayKey) : undefined
    if (replayed) {
      if (replayed.fingerprint === rawFingerprint) return cloneResult(replayed.result)
      return {
        ok: false,
        eventId: rawEventId,
        type: isRecord(input) && typeof input.type === 'string'
          ? input.type as RuntimeTaskLeaseEventType
          : 'invalid',
        code: 'replay-conflict',
        message: 'The eventId was already used for a different command payload',
      }
    }

    const command = normalizeCommand(input)
    const result = command
      ? this.apply(command)
      : {
          ok: false,
          eventId: rawEventId,
          type: 'invalid' as const,
          code: 'invalid-request' as const,
          message: 'Runtime Task / Workspace Lease command failed validation',
        }

    if (scopedReplayKey && validIdentifier(rawEventId)) {
      this.rememberReplay(scopedReplayKey, rawFingerprint, result)
    }
    return cloneResult(result)
  }

  replayEntryCount(): number {
    return this.replay.size
  }

  private rememberReplay(key: string, commandFingerprint: string, result: RuntimeTaskLeaseResult): void {
    this.replay.set(key, { fingerprint: commandFingerprint, result: cloneResult(result) })
    while (this.replay.size > this.maxReplayEntries) {
      const oldest = this.replay.keys().next().value as string | undefined
      if (oldest === undefined) break
      this.replay.delete(oldest)
    }
  }

  snapshot(runtime: RuntimeKind, taskId: string): RuntimeTaskLeaseSnapshot | undefined {
    const lease = this.leases.get(taskKey(runtime, taskId))
    return lease ? cloneSnapshot(lease) : undefined
  }

  list(runtime?: RuntimeKind): RuntimeTaskLeaseSnapshot[] {
    return [...this.leases.values()]
      .filter(lease => runtime === undefined || lease.identity.runtime === runtime)
      .map(cloneSnapshot)
      .sort((left, right) => left.leaseId.localeCompare(right.leaseId))
  }

  history(): RuntimeTaskLeaseTransition[] {
    return this.transitions.map(item => ({ ...item }))
  }

  private apply(command: RuntimeTaskLeaseCommand): RuntimeTaskLeaseResult {
    switch (command.type) {
      case 'acquire': return this.acquire(command)
      case 'bind-process': return this.bindProcess(command)
      case 'heartbeat': return this.heartbeat(command)
      case 'release': return this.release(command)
      case 'cancel': return this.cancel(command)
      case 'timeout': return this.timeout(command)
      case 'process-exit': return this.processExit(command)
      case 'runtime-crash': return this.runtimeCrash(command)
      case 'recover': return this.recover(command)
    }
  }

  private ttl(ttlMs?: number): number | null {
    const value = ttlMs ?? this.defaultTtlMs
    if (!Number.isFinite(value) || value < this.minTtlMs || value > this.maxTtlMs) return null
    return value
  }

  private acquire(command: AcquireLeaseCommand): RuntimeTaskLeaseResult {
    const ttlMs = this.ttl(command.ttlMs)
    if (ttlMs === null) return this.error(command, 'invalid-request', 'ttlMs is outside the allowed range')

    const key = taskKey(command.identity.runtime, command.identity.taskId)
    const existing = this.leases.get(key)
    if (existing) {
      if (!sameAcquireIdentity(existing.identity, command.identity)) {
        return this.error(command, 'owner-mismatch', 'taskId is already bound to a different lease identity', existing)
      }
      if (existing.state === 'active') {
        return this.success(command, 'already-acquired', existing)
      }
      return this.error(command, 'invalid-state', `taskId cannot be reused from ${existing.state}`, existing)
    }

    const leaseId = `lease:${command.identity.runtime}:${++this.leaseSequence}`
    const pending: RuntimeTaskLeaseSnapshot = {
      leaseId,
      identity: cloneIdentity(command.identity),
      state: 'pending',
      revision: 0,
      createdAt: command.observedAt,
    }
    const acquired = this.locks.acquire(
      pending.identity.workspace,
      pending.leaseId,
      pending.identity.access,
      ownerId(pending.identity.runtime),
    )
    if (!acquired) {
      this.leases.delete(key)
      const status = this.locks.detailedStatus(pending.identity.workspace)
      return {
        ok: false,
        eventId: command.eventId,
        type: command.type,
        code: 'conflict',
        conflict: {
          workspace: pending.identity.workspace,
          writerLeaseId: status.writer?.taskId ?? null,
          readerLeaseIds: status.readers.map(reader => reader.taskId).sort(),
        },
        message: 'Workspace access conflicts with an active lease',
      }
    }

    this.leases.set(key, pending)
    this.transition(command, pending, undefined, 'pending', 'acquired')

    const active: RuntimeTaskLeaseSnapshot = {
      ...pending,
      state: 'active',
      revision: 1,
      acquiredAt: command.observedAt,
      lastHeartbeatAt: command.observedAt,
      expiresAt: command.observedAt + ttlMs,
    }
    this.leases.set(key, active)
    this.transition(command, active, 'pending', 'active', 'acquired')
    return this.success(command, 'acquired', active)
  }

  private bindProcess(command: BindProcessLeaseCommand): RuntimeTaskLeaseResult {
    const lease = this.findTask(command)
    if ('error' in lease) return lease.error
    if (lease.state !== 'active') {
      return this.error(command, 'invalid-state', `Process binding requires active, got ${lease.state}`, lease)
    }
    if (lease.identity.process) {
      return sameProcess(lease.identity.process, command.process)
        ? this.success(command, 'process-bound', lease)
        : this.error(command, 'owner-mismatch', 'Lease is already bound to a different process', lease)
    }
    const updated: RuntimeTaskLeaseSnapshot = {
      ...lease,
      identity: { ...cloneIdentity(lease.identity), process: { ...command.process } },
      revision: lease.revision + 1,
    }
    this.leases.set(taskKey(command.runtime, command.taskId), updated)
    this.transition(command, updated, 'active', 'active', 'process-bound')
    return this.success(command, 'process-bound', updated)
  }

  private heartbeat(command: HeartbeatLeaseCommand): RuntimeTaskLeaseResult {
    const lease = this.findTask(command)
    if ('error' in lease) return lease.error
    if (lease.state === 'expired') return this.error(command, 'expired-lease', 'Lease is already expired', lease)
    if (lease.state !== 'active') return this.error(command, 'invalid-state', `Heartbeat requires active, got ${lease.state}`, lease)
    if (lease.expiresAt !== undefined && command.observedAt >= lease.expiresAt) {
      const expired = this.expire(command, lease, 'timeout')
      return this.error(command, 'expired-lease', 'Heartbeat arrived after lease expiry', expired)
    }
    if (lease.lastHeartbeatAt !== undefined && command.observedAt < lease.lastHeartbeatAt) {
      return this.error(command, 'invalid-state', 'Heartbeat timestamp moved backwards', lease)
    }
    const ttlMs = this.ttl(command.ttlMs)
    if (ttlMs === null) return this.error(command, 'invalid-request', 'ttlMs is outside the allowed range', lease)

    const updated: RuntimeTaskLeaseSnapshot = {
      ...lease,
      revision: lease.revision + 1,
      lastHeartbeatAt: command.observedAt,
      expiresAt: command.observedAt + ttlMs,
    }
    this.leases.set(taskKey(command.runtime, command.taskId), updated)
    this.transition(command, updated, 'active', 'active', 'heartbeat-accepted')
    return this.success(command, 'heartbeat-accepted', updated)
  }

  private release(command: ReleaseLeaseCommand): RuntimeTaskLeaseResult {
    const lease = this.findTask(command)
    if ('error' in lease) return lease.error
    if (lease.state === 'released') return this.success(command, 'already-terminal', lease)
    if (lease.state === 'expired') return this.error(command, 'expired-lease', 'Lease is expired', lease)
    if (!validLeaseState(lease.state, ['active', 'pending'])) {
      return this.error(command, 'invalid-state', `Release cannot transition ${lease.state}`, lease)
    }
    return this.finish(command, lease, 'released', 'released')
  }

  private cancel(command: CancelLeaseCommand): RuntimeTaskLeaseResult {
    const lease = this.findTask(command)
    if ('error' in lease) return lease.error
    if (validLeaseState(lease.state, ['released', 'expired', 'recovered'])) {
      return this.success(command, 'already-terminal', lease)
    }
    if (!validLeaseState(lease.state, ['active', 'pending'])) {
      return this.error(command, 'invalid-state', `Cancel cannot transition ${lease.state}`, lease)
    }
    return this.finish(command, lease, 'cancelled', 'cancelled')
  }

  private timeout(command: TimeoutLeaseCommand): RuntimeTaskLeaseResult {
    const lease = this.findTask(command)
    if ('error' in lease) return lease.error
    if (lease.state === 'expired') return this.success(command, 'expired', lease)
    if (validLeaseState(lease.state, ['released', 'recovered'])) return this.success(command, 'already-terminal', lease)
    if (lease.state !== 'active') return this.error(command, 'invalid-state', `Timeout requires active, got ${lease.state}`, lease)
    if (lease.expiresAt !== undefined && command.observedAt < lease.expiresAt) {
      return this.error(command, 'invalid-state', 'Timeout arrived before expiresAt', lease)
    }
    const expired = this.expire(command, lease, 'timeout')
    return this.success(command, 'expired', expired)
  }

  private processExit(command: ProcessExitLeaseCommand): RuntimeTaskLeaseResult {
    const lease = this.findTask(command)
    if ('error' in lease) return lease.error
    if (lease.state === 'orphaned') {
      const recovered = this.completeTerminal(command, lease, 'recovered', 'process-exit')
      return this.success(command, 'recovered', recovered)
    }
    if (validLeaseState(lease.state, ['released', 'expired', 'recovered'])) {
      return this.success(command, 'already-terminal', lease)
    }
    if (!validLeaseState(lease.state, ['active', 'pending'])) {
      return this.error(command, 'invalid-state', `Process exit cannot transition ${lease.state}`, lease)
    }
    return this.finish(command, lease, 'released', 'process-exit')
  }

  private runtimeCrash(command: RuntimeCrashLeaseCommand): RuntimeTaskLeaseResult {
    const affected: RuntimeTaskLeaseSnapshot[] = []
    for (const [key, lease] of this.leases) {
      if (lease.identity.runtime !== command.runtime) continue
      if (lease.state === 'orphaned') {
        affected.push(cloneSnapshot(lease))
        continue
      }
      if (!validLeaseState(lease.state, ['active', 'pending', 'releasing'])) continue
      const orphaned: RuntimeTaskLeaseSnapshot = {
        ...lease,
        state: 'orphaned',
        revision: lease.revision + 1,
        terminalReason: 'runtime-crash',
      }
      this.leases.set(key, orphaned)
      this.transition(command, orphaned, lease.state, 'orphaned', 'orphaned')
      affected.push(cloneSnapshot(orphaned))
    }
    return {
      ok: true,
      eventId: command.eventId,
      type: command.type,
      code: 'orphaned',
      affected: affected.sort((left, right) => left.leaseId.localeCompare(right.leaseId)),
    }
  }

  private recover(command: RecoverLeaseCommand): RuntimeTaskLeaseResult {
    const lease = this.findTask(command)
    if ('error' in lease) return lease.error
    if (lease.state === 'recovered') return this.success(command, 'recovered', lease)
    if (lease.state !== 'orphaned') {
      return this.error(command, 'recovery-failed', `Recovery requires orphaned, got ${lease.state}`, lease)
    }
    const recovered = this.completeTerminal(command, lease, 'recovered', 'recovered')
    return this.success(command, 'recovered', recovered)
  }

  private findTask(command: TaskLeaseCommandBase): RuntimeTaskLeaseSnapshot | { error: RuntimeTaskLeaseResult } {
    const lease = this.leases.get(taskKey(command.runtime, command.taskId))
    if (!lease) return { error: this.error(command, 'unknown-task', 'No lease exists for runtime/taskId') }
    if (lease.leaseId !== command.leaseId) {
      return { error: this.error(command, 'owner-mismatch', 'leaseId does not own runtime/taskId', lease) }
    }
    return lease
  }

  private finish(
    command: ReleaseLeaseCommand | CancelLeaseCommand | ProcessExitLeaseCommand,
    lease: RuntimeTaskLeaseSnapshot,
    code: 'released' | 'cancelled',
    reason: 'released' | 'cancelled' | 'process-exit',
  ): RuntimeTaskLeaseResult {
    const releasing: RuntimeTaskLeaseSnapshot = {
      ...lease,
      state: 'releasing',
      revision: lease.revision + 1,
    }
    this.leases.set(taskKey(lease.identity.runtime, lease.identity.taskId), releasing)
    this.transition(command, releasing, lease.state, 'releasing', code)
    const released = this.completeTerminal(command, releasing, 'released', reason)
    return this.success(command, code, released)
  }

  private expire(
    command: HeartbeatLeaseCommand | TimeoutLeaseCommand,
    lease: RuntimeTaskLeaseSnapshot,
    reason: 'timeout',
  ): RuntimeTaskLeaseSnapshot {
    return this.completeTerminal(command, lease, 'expired', reason)
  }

  private completeTerminal(
    command: RuntimeTaskLeaseCommand,
    lease: RuntimeTaskLeaseSnapshot,
    state: 'released' | 'expired' | 'recovered',
    reason: 'released' | 'cancelled' | 'timeout' | 'process-exit' | 'recovered',
  ): RuntimeTaskLeaseSnapshot {
    this.locks.release(
      lease.identity.workspace,
      lease.leaseId,
      ownerId(lease.identity.runtime),
    )
    const completed: RuntimeTaskLeaseSnapshot = {
      ...lease,
      state,
      revision: lease.revision + 1,
      terminalAt: command.observedAt,
      terminalReason: reason,
    }
    this.leases.set(taskKey(lease.identity.runtime, lease.identity.taskId), completed)
    const code: RuntimeTaskLeaseSuccessCode = state === 'expired' ? 'expired' : state === 'recovered' ? 'recovered' : reason === 'cancelled' ? 'cancelled' : 'released'
    this.transition(command, completed, lease.state, state, code)
    return completed
  }

  private transition(
    command: RuntimeTaskLeaseCommand,
    lease: RuntimeTaskLeaseSnapshot,
    from: RuntimeTaskLeaseState | undefined,
    to: RuntimeTaskLeaseState,
    code: RuntimeTaskLeaseSuccessCode | RuntimeTaskLeaseErrorCode,
  ): void {
    this.transitions.push({
      sequence: ++this.transitionSequence,
      eventId: command.eventId,
      type: command.type,
      runtime: lease.identity.runtime,
      taskId: lease.identity.taskId,
      leaseId: lease.leaseId,
      from,
      to,
      at: command.observedAt,
      code,
    })
  }

  private success(
    command: RuntimeTaskLeaseCommand,
    code: RuntimeTaskLeaseSuccessCode,
    lease: RuntimeTaskLeaseSnapshot,
  ): RuntimeTaskLeaseResult {
    return {
      ok: true,
      eventId: command.eventId,
      type: command.type,
      code,
      lease: cloneSnapshot(lease),
    }
  }

  private error(
    command: RuntimeTaskLeaseCommand | TaskLeaseCommandBase,
    code: RuntimeTaskLeaseErrorCode,
    message: string,
    lease?: RuntimeTaskLeaseSnapshot,
  ): RuntimeTaskLeaseResult {
    return {
      ok: false,
      eventId: command.eventId,
      type: command.type,
      code,
      lease: lease ? cloneSnapshot(lease) : undefined,
      message,
    }
  }
}

export class RuntimeTaskLeaseAdapter {
  constructor(
    readonly runtime: RuntimeKind,
    private readonly coordinator: RuntimeTaskLeaseCoordinator,
  ) {}

  dispatch(command: RuntimeScopedLeaseCommand): RuntimeTaskLeaseResult {
    const payload = command as unknown
    if (!isRecord(payload) || !RUNTIME_SCOPED_EVENT_TYPES.has(payload.type as RuntimeTaskLeaseEventType)) {
      return {
        ok: false,
        eventId: isRecord(payload) && typeof payload.eventId === 'string' ? payload.eventId : '',
        type: isRecord(payload) && validEventType(payload.type) ? payload.type : 'invalid',
        code: 'invalid-request',
        message: 'The command is reserved for trusted Electron Main supervision',
      }
    }
    if (command.type === 'acquire') {
      return this.coordinator.dispatch({
        ...command,
        identity: { ...command.identity, runtime: this.runtime },
      })
    }
    return this.coordinator.dispatch({ ...command, runtime: this.runtime })
  }
}
