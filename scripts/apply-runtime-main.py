#!/usr/bin/env python3
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:100]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


path = "webui/packages/desktop/src/main/runtime-task-supervisor.ts"
replace_once(path, """interface PersistedSupervisorState {
  schemaVersion: number
  tasks: RuntimeTaskSupervisorTask[]
}
""", """interface PersistedTaskGeneration {
  runtime: RuntimeKind
  taskId: string
  generation: number
}

interface PersistedSupervisorState {
  schemaVersion: number
  tasks: RuntimeTaskSupervisorTask[]
  generations: PersistedTaskGeneration[]
}
""")
replace_once(path, """  private readonly records = new Map<string, SupervisorRecord>()
  private server: Server | null = null
""", """  private readonly records = new Map<string, SupervisorRecord>()
  private readonly generations = new Map<string, number>()
  private server: Server | null = null
""")
replace_once(path, """    const generation = 1
    const internalTaskId = safeInternalTaskId(request.runtime, request.taskId, generation)
""", """    const generation = (this.generations.get(key) || 0) + 1
    const internalTaskId = safeInternalTaskId(request.runtime, request.taskId, generation)
""")
replace_once(path, """    this.records.set(key, record)
    this.persist()
    return { status: 201, body: { ok: true, code: 'acquired', task: cloneTask(record) } }
""", """    this.records.set(key, record)
    this.generations.set(key, generation)
    this.persist()
    return { status: 201, body: { ok: true, code: 'acquired', task: cloneTask(record) } }
""")
replace_once(path, """    record.process = evidence
    record.lastHeartbeatAt = this.now()
    this.persist()
    return { status: 200, body: { ok: true, code: 'resumed', task: cloneTask(record) } }
""", """    record.process = evidence
    record.lastHeartbeatAt = this.now()
    this.generations.set(key, generation)
    this.persist()
    return { status: 200, body: { ok: true, code: 'resumed', task: cloneTask(record) } }
""")
replace_once(path, """  private async restorePersistedTasks(): Promise<void> {
    const persisted = this.readState()
    const activeRuntimes = new Set<RuntimeKind>()
    for (const task of persisted.tasks) {
""", """  private async restorePersistedTasks(): Promise<void> {
    const persisted = this.readState()
    const activeRuntimes = new Set<RuntimeKind>()
    for (const item of persisted.generations) {
      if (!validRuntime(item.runtime) || !validString(item.taskId) || !Number.isSafeInteger(item.generation) || item.generation < 1) continue
      this.generations.set(stableTaskKey(item.runtime, item.taskId), item.generation)
    }
    for (const task of persisted.tasks) {
""")
replace_once(path, """      const generation = Math.max(1, task.generation || 1)
      const internalTaskId = safeInternalTaskId(task.runtime, task.taskId, generation)
""", """      const key = stableTaskKey(task.runtime, task.taskId)
      const generation = Math.max(1, task.generation || 1, this.generations.get(key) || 0)
      this.generations.set(key, generation)
      const internalTaskId = safeInternalTaskId(task.runtime, task.taskId, generation)
""")
replace_once(path, """      this.records.set(stableTaskKey(task.runtime, task.taskId), {
        ...task, workspace: resolve(task.workspace), state: 'active', leaseId: acquired.lease.leaseId,
""", """      this.records.set(key, {
        ...task, workspace: resolve(task.workspace), state: 'active', leaseId: acquired.lease.leaseId,
""")
replace_once(path, """  private readState(): PersistedSupervisorState {
    if (!existsSync(this.stateFile)) return { schemaVersion: STATE_SCHEMA_VERSION, tasks: [] }
    try {
      const parsed = JSON.parse(readFileSync(this.stateFile, 'utf8')) as Partial<PersistedSupervisorState>
      return parsed.schemaVersion === STATE_SCHEMA_VERSION && Array.isArray(parsed.tasks)
        ? { schemaVersion: STATE_SCHEMA_VERSION, tasks: parsed.tasks as RuntimeTaskSupervisorTask[] }
        : { schemaVersion: STATE_SCHEMA_VERSION, tasks: [] }
    } catch { return { schemaVersion: STATE_SCHEMA_VERSION, tasks: [] } }
  }

  private persist(): void {
    mkdirSync(dirname(this.stateFile), { recursive: true, mode: 0o700 })
    const temporary = `${this.stateFile}.tmp-${process.pid}-${Date.now()}`
    const payload: PersistedSupervisorState = { schemaVersion: STATE_SCHEMA_VERSION, tasks: this.listTasks() }
""", """  private readState(): PersistedSupervisorState {
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
      const separator = key.indexOf('\\u0000')
      return { runtime: key.slice(0, separator) as RuntimeKind, taskId: key.slice(separator + 1), generation }
    }).sort((left, right) => `${left.runtime}:${left.taskId}`.localeCompare(`${right.runtime}:${right.taskId}`))
    const payload: PersistedSupervisorState = {
      schemaVersion: STATE_SCHEMA_VERSION,
      tasks: this.listTasks(),
      generations,
    }
""")

path = "webui/packages/server/src/services/runtime-task-supervisor-client.ts"
replace_once(path, "  private async resume(): Promise<void> {", "  async resume(): Promise<void> {")
replace_once(path, "      await (handle as any).resume()", "      await handle.resume()")

path = "webui/packages/desktop/src/main/webui-server.ts"
replace_once(path, """import { safeChildEnvironment } from './child-env'
import { deepAgentHome } from './paths'
""", """import { safeChildEnvironment } from './child-env'
import { deepAgentHome } from './paths'
import type { RuntimeTaskSupervisorEnvironment } from './runtime-task-supervisor'
""")
replace_once(path, """function runtimeEnvironment(): NodeJS.ProcessEnv {
  const home = resolve(deepAgentHome())
  return safeChildEnvironment({
    DEEPAGENT_HOME: home,
    // Compatibility is scoped to the managed child only.
    HERMES_HOME: home,
  })
}

async function runCli(args: string[]): Promise<void> {
""", """function runtimeEnvironment(supervisorEnvironment: RuntimeTaskSupervisorEnvironment | null = null): NodeJS.ProcessEnv {
  const home = resolve(deepAgentHome())
  return safeChildEnvironment({
    DEEPAGENT_HOME: home,
    // Compatibility is scoped to the managed child only.
    HERMES_HOME: home,
    HERMES_DESKTOP: 'true',
    ...(supervisorEnvironment || {}),
  })
}

async function runCli(args: string[], supervisorEnvironment: RuntimeTaskSupervisorEnvironment | null = null): Promise<void> {
""")
replace_once(path, "      env: runtimeEnvironment(),", "      env: runtimeEnvironment(supervisorEnvironment),")
replace_once(path, """export async function startWebUiServer(_preferredPort?: number): Promise<string> {
  await runCli(['webui', 'start'])
""", """export async function startWebUiServer(
  _preferredPort: number | undefined,
  supervisorEnvironment: RuntimeTaskSupervisorEnvironment,
): Promise<string> {
  await runCli(['webui', 'start'], supervisorEnvironment)
""")

path = "webui/packages/desktop/src/main/index.ts"
replace_once(path, """import { runPhase3Migration } from './migration'
import { registerWorkspaceLockIpc } from './workspace-lock-ipc'
""", """import { runPhase3Migration } from './migration'
import { registerWorkspaceLockIpc } from './workspace-lock-ipc'
import { RuntimeTaskSupervisor, type RuntimeTaskSupervisorEnvironment } from './runtime-task-supervisor'
""")
replace_once(path, """let modeManager: ModeManager | null = null
let credentialVault: CredentialVault | null = null
let petWindowLoadPromise: Promise<void> | null = null
""", """let modeManager: ModeManager | null = null
let credentialVault: CredentialVault | null = null
let runtimeTaskSupervisor: RuntimeTaskSupervisor | null = null
let runtimeTaskSupervisorEnvironment: RuntimeTaskSupervisorEnvironment | null = null
let petWindowLoadPromise: Promise<void> | null = null
""")
replace_once(path, """async function bootstrap() {
  if (isBootstrapping) return
""", """async function ensureRuntimeTaskSupervisor(): Promise<RuntimeTaskSupervisorEnvironment> {
  if (!runtimeTaskSupervisor) {
    runtimeTaskSupervisor = new RuntimeTaskSupervisor({
      stateDir: join(deepAgentHome(), 'runtime', 'task-supervisor'),
    })
  }
  if (!runtimeTaskSupervisorEnvironment) {
    runtimeTaskSupervisorEnvironment = await runtimeTaskSupervisor.start()
  }
  return runtimeTaskSupervisorEnvironment
}

async function bootstrap() {
  if (isBootstrapping) return
""")
replace_once(path, """  try {
    const url = await startWebUiServer(PORT)
    serverUrl = url
""", """  try {
    const supervisorEnvironment = await ensureRuntimeTaskSupervisor()
    const url = await startWebUiServer(PORT, supervisorEnvironment)
    serverUrl = url
""")
replace_once(path, """    await showShutdownSplash()
    await stopWebUiServer().catch(() => undefined)
    app.exit(0)
""", """    await showShutdownSplash()
    await stopWebUiServer().catch(() => undefined)
    await runtimeTaskSupervisor?.stop().catch(() => undefined)
    runtimeTaskSupervisor = null
    runtimeTaskSupervisorEnvironment = null
    app.exit(0)
""")

path = "hermes_cli/webui.py"
replace_once(path, """    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "NODE_EXTRA_CA_CERTS",
}
""", """    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "NODE_EXTRA_CA_CERTS",
    "HERMES_DESKTOP",
    "DEEPAGENT_RUNTIME_LEASE_SOCKET",
    "DEEPAGENT_RUNTIME_LEASE_TOKEN",
    "DEEPAGENT_RUNTIME_LEASE_TTL_MS",
}
""")

path = "webui/bin/hermes-web-ui.mjs"
replace_once(path, """    'NODE_EXTRA_CA_CERTS', 'PROFILE', 'WORKSPACE_BASE',
    'HERMES_WEB_UI_AUTH_JWT_EXPIRES_IN',
""", """    'NODE_EXTRA_CA_CERTS', 'PROFILE', 'WORKSPACE_BASE',
    'HERMES_DESKTOP', 'DEEPAGENT_RUNTIME_LEASE_SOCKET',
    'DEEPAGENT_RUNTIME_LEASE_TOKEN', 'DEEPAGENT_RUNTIME_LEASE_TTL_MS',
    'HERMES_WEB_UI_AUTH_JWT_EXPIRES_IN',
""")

print("Main supervisor and managed environment chain transformed")
