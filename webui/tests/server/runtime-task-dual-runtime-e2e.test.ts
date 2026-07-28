import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { request as httpRequest } from 'node:http'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { afterAll, afterEach, describe, expect, it } from 'vitest'
import {
  RuntimeTaskSupervisor,
  type RuntimeTaskProcessEvidence,
  type RuntimeTaskProcessProbe,
  type RuntimeTaskSupervisorEnvironment,
} from '../../packages/desktop/src/main/runtime-task-supervisor'
import {
  acquireRuntimeTaskLease,
  runtimeTaskId,
  type RuntimeTaskLeaseHandle,
} from '../../packages/server/src/services/runtime-task-supervisor-client'

class FakeProcessProbe implements RuntimeTaskProcessProbe {
  readonly processes = new Map<number, RuntimeTaskProcessEvidence>()

  set(pid: number, fingerprint: string, command = `runtime-process-${pid}`): void {
    this.processes.set(pid, { pid, fingerprint, command })
  }

  remove(pid: number): void {
    this.processes.delete(pid)
  }

  async inspect(pid: number): Promise<RuntimeTaskProcessEvidence | null> {
    const process = this.processes.get(pid)
    return process ? { ...process } : null
  }
}

interface Fixture {
  stateDir: string
  socketPath: string
  probe: FakeProcessProbe
  clock: { value: number }
  supervisor: RuntimeTaskSupervisor
  environment: RuntimeTaskSupervisorEnvironment
  supervisors: RuntimeTaskSupervisor[]
  activate(supervisor: RuntimeTaskSupervisor): Promise<RuntimeTaskSupervisorEnvironment>
}

const ENV_NAMES = [
  'DEEPAGENT_RUNTIME_LEASE_SOCKET',
  'DEEPAGENT_RUNTIME_LEASE_TOKEN',
  'DEEPAGENT_RUNTIME_LEASE_TTL_MS',
  'HERMES_DESKTOP',
] as const
const cleanups: Array<() => Promise<void>> = []
const evidence: Array<Record<string, unknown>> = []
const evidencePath = resolve(process.cwd(), '..', 'dist', 'test-results', 'runtime-task-dual-runtime-e2e.json')

function applyEnvironment(environment: RuntimeTaskSupervisorEnvironment): void {
  process.env.DEEPAGENT_RUNTIME_LEASE_SOCKET = environment.DEEPAGENT_RUNTIME_LEASE_SOCKET
  process.env.DEEPAGENT_RUNTIME_LEASE_TOKEN = environment.DEEPAGENT_RUNTIME_LEASE_TOKEN
  process.env.DEEPAGENT_RUNTIME_LEASE_TTL_MS = environment.DEEPAGENT_RUNTIME_LEASE_TTL_MS
  process.env.HERMES_DESKTOP = 'true'
}

async function fixture(): Promise<Fixture> {
  const previous = new Map<string, string | undefined>(ENV_NAMES.map(name => [name, process.env[name]]))
  const stateDir = mkdtempSync(join(tmpdir(), 'deepagent-dual-runtime-e2e-'))
  const socketPath = join(stateDir, 'supervisor.sock')
  const probe = new FakeProcessProbe()
  const clock = { value: 1_000 }
  const supervisors: RuntimeTaskSupervisor[] = []

  const createSupervisor = () => new RuntimeTaskSupervisor({
    stateDir,
    socketPath,
    heartbeatTtlMs: 1_000,
    monitorIntervalMs: 100,
    processProbe: probe,
    now: () => clock.value,
  })

  const supervisor = createSupervisor()
  supervisors.push(supervisor)
  const environment = await supervisor.start()
  applyEnvironment(environment)

  const result: Fixture = {
    stateDir,
    socketPath,
    probe,
    clock,
    supervisor,
    environment,
    supervisors,
    async activate(nextSupervisor) {
      supervisors.push(nextSupervisor)
      const nextEnvironment = await nextSupervisor.start()
      this.supervisor = nextSupervisor
      this.environment = nextEnvironment
      applyEnvironment(nextEnvironment)
      return nextEnvironment
    },
  }

  cleanups.push(async () => {
    for (const item of [...supervisors].reverse()) {
      await item.stop().catch(() => undefined)
    }
    for (const name of ENV_NAMES) {
      const value = previous.get(name)
      if (value === undefined) delete process.env[name]
      else process.env[name] = value
    }
    rmSync(stateDir, { recursive: true, force: true })
  })
  return result
}

function newSupervisor(value: Fixture): RuntimeTaskSupervisor {
  return new RuntimeTaskSupervisor({
    stateDir: value.stateDir,
    socketPath: value.socketPath,
    heartbeatTtlMs: 1_000,
    monitorIntervalMs: 100,
    processProbe: value.probe,
    now: () => value.clock.value,
  })
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

async function waitUntil(predicate: () => boolean, timeoutMs = 3_000): Promise<void> {
  const deadline = Date.now() + timeoutMs
  while (!predicate()) {
    if (Date.now() >= deadline) throw new Error('condition did not become true before timeout')
    await new Promise(resolveWait => setTimeout(resolveWait, 25))
  }
}

function record(label: string, value: Fixture, extra: Record<string, unknown> = {}): void {
  const state = existsSync(join(value.stateDir, 'leases.json'))
    ? JSON.parse(readFileSync(join(value.stateDir, 'leases.json'), 'utf8'))
    : null
  evidence.push({
    label,
    tasks: value.supervisor.listTasks(),
    persistedState: state,
    ...extra,
  })
}

async function deepagent(
  taskId: string,
  workspace: string,
  pid: number,
  access: 'read' | 'write' = 'write',
): Promise<RuntimeTaskLeaseHandle> {
  return acquireRuntimeTaskLease({
    runtime: 'deepagent',
    taskId,
    workspace,
    access,
    processPid: pid,
    requireProcess: true,
  })
}

async function deepcode(
  taskId: string,
  workspace: string,
  pid?: number,
  access: 'read' | 'write' = 'write',
): Promise<RuntimeTaskLeaseHandle> {
  const lease = await acquireRuntimeTaskLease({ runtime: 'deepcode', taskId, workspace, access })
  if (pid) await lease.bindProcess(pid)
  return lease
}

afterEach(async () => {
  while (cleanups.length > 0) await cleanups.pop()!()
})

afterAll(() => {
  mkdirSync(dirname(evidencePath), { recursive: true })
  writeFileSync(evidencePath, `${JSON.stringify({ schemaVersion: 1, evidence }, null, 2)}\n`, 'utf8')
})

describe.sequential('dual Runtime same-workspace production-client E2E', () => {
  it('enforces read/write conflicts before spawn or workspace side effects and releases on completion/cancel', async () => {
    const value = await fixture()
    value.probe.set(4101, 'deepagent-reader')
    value.probe.set(4201, 'deepcode-reader')
    value.probe.set(4202, 'deepcode-writer')
    const workspace = join(value.stateDir, 'shared-workspace')
    const sideEffect = join(workspace, 'must-not-exist.txt')

    const agentReader = await deepagent(runtimeTaskId('deepagent', 'reader-a'), workspace, 4101, 'read')
    const codeReader = await deepcode(runtimeTaskId('deepcode', 'reader-b'), workspace, 4201, 'read')
    expect(value.supervisor.listTasks()).toHaveLength(2)

    let spawnCount = 0
    await expect((async () => {
      const writer = await acquireRuntimeTaskLease({
        runtime: 'deepcode',
        taskId: runtimeTaskId('deepcode', 'rejected-writer'),
        workspace,
        access: 'write',
      })
      spawnCount += 1
      mkdirSync(workspace, { recursive: true })
      writeFileSync(sideEffect, 'write occurred after rejected acquire')
      await writer.bindProcess(4202)
    })()).rejects.toMatchObject({ code: 'conflict', status: 409 })
    expect(spawnCount).toBe(0)
    expect(existsSync(sideEffect)).toBe(false)

    await agentReader.finish('completed')
    await codeReader.finish('completed')
    const writer = await deepagent(runtimeTaskId('deepagent', 'writer-a'), workspace, 4101)

    await expect(deepcode(runtimeTaskId('deepcode', 'blocked-reader'), workspace, undefined, 'read'))
      .rejects.toMatchObject({ code: 'conflict', status: 409 })
    await expect(deepcode(runtimeTaskId('deepcode', 'blocked-writer'), workspace))
      .rejects.toMatchObject({ code: 'conflict', status: 409 })

    await writer.finish('cancelled')
    const afterCancel = await deepcode(runtimeTaskId('deepcode', 'writer-after-cancel'), workspace, 4202)
    await afterCancel.finish('completed')
    expect(value.supervisor.listTasks()).toEqual([])
    record('conflict-before-spawn-and-release', value, { spawnCount, sideEffectExists: existsSync(sideEffect) })
  })

  it('fails closed after one Runtime heartbeat timeout without blocking the healthy Runtime or other workspaces', async () => {
    const value = await fixture()
    value.probe.set(5101, 'deepagent-timeout')
    value.probe.set(5201, 'deepcode-healthy')
    value.probe.set(5301, 'deepcode-other-workspace')
    const workspaceA = join(value.stateDir, 'workspace-a')
    const workspaceB = join(value.stateDir, 'workspace-b')
    const workspaceC = join(value.stateDir, 'workspace-c')

    const agent = await deepagent(runtimeTaskId('deepagent', 'timeout'), workspaceA, 5101)
    const code = await deepcode(runtimeTaskId('deepcode', 'healthy'), workspaceB, 5201)
    agent.abandon()
    value.clock.value = 1_500
    await code.heartbeat()
    code.abandon()
    value.clock.value = 2_001

    await waitUntil(() => value.supervisor.listTasks().some(task => task.runtime === 'deepagent' && task.state === 'orphaned'))
    expect(value.supervisor.listTasks()).toEqual(expect.arrayContaining([
      expect.objectContaining({ runtime: 'deepagent', state: 'orphaned' }),
      expect.objectContaining({ runtime: 'deepcode', state: 'active' }),
    ]))
    await expect(deepcode(runtimeTaskId('deepcode', 'double-write-attempt'), workspaceA))
      .rejects.toMatchObject({ code: 'conflict', status: 409 })

    const independent = await deepcode(runtimeTaskId('deepcode', 'independent'), workspaceC, 5301)
    await independent.finish('completed')
    await code.finish('completed')
    const released = await post(value.environment, '/v1/tasks/process-exit', {
      runtime: 'deepagent',
      taskId: runtimeTaskId('deepagent', 'timeout'),
      exitCode: null,
      signal: null,
      eventId: 'e2e:deepagent-timeout-process-exit',
    })
    expect(released).toMatchObject({ status: 200, body: { ok: true, code: 'recovered' } })
    record('runtime-heartbeat-timeout-isolation', value)
  })

  it('handles shared bridge crash, DeepCode child crash, and PID reuse without cross-Runtime damage', async () => {
    const value = await fixture()
    value.probe.set(6101, 'shared-deepagent-bridge')
    value.probe.set(6201, 'deepcode-child')
    value.probe.set(6301, 'deepcode-pid-generation-one')

    const agentA = await deepagent(runtimeTaskId('deepagent', 'bridge-a'), join(value.stateDir, 'bridge-a'), 6101)
    const agentB = await deepagent(runtimeTaskId('deepagent', 'bridge-b'), join(value.stateDir, 'bridge-b'), 6101)
    const code = await deepcode(runtimeTaskId('deepcode', 'child-crash'), join(value.stateDir, 'code-crash'), 6201)
    agentA.abandon()
    agentB.abandon()
    code.abandon()

    value.probe.remove(6101)
    value.probe.remove(6201)
    await waitUntil(() => value.supervisor.listTasks().length === 0)

    const reusedWorkspace = join(value.stateDir, 'pid-reuse')
    const reused = await deepcode(runtimeTaskId('deepcode', 'pid-reuse-old'), reusedWorkspace, 6301)
    reused.abandon()
    value.probe.set(6301, 'deepcode-pid-generation-two')
    await waitUntil(() => value.supervisor.listTasks().length === 0)

    const replacement = await deepcode(runtimeTaskId('deepcode', 'pid-reuse-new'), reusedWorkspace, 6301)
    await replacement.finish('completed')
    expect(value.supervisor.listTasks()).toEqual([])
    record('bridge-child-crash-and-pid-reuse', value)
  })

  it('restores verified tasks as orphaned after Main restart and resumes only with matching process evidence', async () => {
    const value = await fixture()
    value.probe.set(7101, 'deepagent-surviving-process')
    const taskId = runtimeTaskId('deepagent', 'main-restart')
    const workspace = join(value.stateDir, 'main-restart')
    const lease = await deepagent(taskId, workspace, 7101)
    lease.abandon()
    await value.supervisor.stop()

    await value.activate(newSupervisor(value))
    expect(value.supervisor.listTasks()).toMatchObject([
      { runtime: 'deepagent', taskId, workspace, state: 'orphaned', generation: 1, process: { pid: 7101 } },
    ])
    await expect(deepcode(runtimeTaskId('deepcode', 'blocked-during-main-restart'), workspace))
      .rejects.toMatchObject({ code: 'conflict', status: 409 })

    const resumed = await post(value.environment, '/v1/tasks/resume', {
      runtime: 'deepagent',
      taskId,
      pid: 7101,
      eventId: 'e2e:main-restart-resume',
    })
    expect(resumed).toMatchObject({
      status: 200,
      body: { ok: true, code: 'resumed', task: { state: 'active', generation: 2, process: { pid: 7101 } } },
    })
    await lease.finish('completed')
    record('main-restart-verified-resume', value)
  })

  it('allows the same Runtime client to resume after heartbeat orphaning while unverifiable Main-restart tasks remain locked', async () => {
    const value = await fixture()
    value.probe.set(8101, 'deepagent-runtime-restart')
    const recoverTaskId = runtimeTaskId('deepagent', 'runtime-restart')
    const recoverWorkspace = join(value.stateDir, 'runtime-restart')
    const oldRuntime = await deepagent(recoverTaskId, recoverWorkspace, 8101)
    oldRuntime.abandon()
    value.clock.value = 2_001
    await waitUntil(() => value.supervisor.listTasks().some(task => task.taskId === recoverTaskId && task.state === 'orphaned'))

    const restartedRuntime = await deepagent(recoverTaskId, recoverWorkspace, 8101)
    expect(value.supervisor.listTasks()).toMatchObject([
      { runtime: 'deepagent', taskId: recoverTaskId, state: 'active', generation: 2, process: { pid: 8101 } },
    ])
    await restartedRuntime.finish('completed')

    value.probe.set(8201, 'deepcode-before-main-restart')
    const unverifiableTaskId = runtimeTaskId('deepcode', 'unverifiable-main-restart')
    const lockedWorkspace = join(value.stateDir, 'unverifiable-main-restart')
    const unverifiable = await deepcode(unverifiableTaskId, lockedWorkspace, 8201)
    unverifiable.abandon()
    await value.supervisor.stop()
    value.probe.set(8201, 'deepcode-reused-pid-after-main-restart')

    await value.activate(newSupervisor(value))
    expect(value.supervisor.listTasks()).toMatchObject([
      { runtime: 'deepcode', taskId: unverifiableTaskId, workspace: lockedWorkspace, state: 'orphaned', process: { pid: 8201, fingerprint: 'deepcode-before-main-restart' } },
    ])
    await expect(deepagent(runtimeTaskId('deepagent', 'must-remain-blocked'), lockedWorkspace, 8101))
      .rejects.toMatchObject({ code: 'conflict', status: 409 })

    await new Promise(resolveWait => setTimeout(resolveWait, 250))
    expect(value.supervisor.listTasks()).toMatchObject([
      { runtime: 'deepcode', taskId: unverifiableTaskId, state: 'orphaned' },
    ])
    const cleared = await post(value.environment, '/v1/tasks/process-exit', {
      runtime: 'deepcode',
      taskId: unverifiableTaskId,
      exitCode: null,
      signal: null,
      eventId: 'e2e:owner-confirmed-unverifiable-process-exit',
    })
    expect(cleared).toMatchObject({ status: 200, body: { ok: true, code: 'recovered' } })

    const afterConfirmation = await deepagent(runtimeTaskId('deepagent', 'after-owner-confirmation'), lockedWorkspace, 8101)
    await afterConfirmation.finish('completed')
    record('runtime-restart-and-unverifiable-main-restart', value)
  })
})
