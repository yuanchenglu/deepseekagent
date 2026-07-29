import { execFile } from 'node:child_process'
import { existsSync, readFileSync, realpathSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'
import { promisify } from 'node:util'
import { safeChildEnvironment } from './child-env'
import { deepAgentHome } from './paths'
import type { RuntimeTaskSupervisorEnvironment } from './runtime-task-supervisor'

const execFileAsync = promisify(execFile)
const READY_TIMEOUT_MS = 120_000

function managedCli(): string {
  const home = resolve(deepAgentHome())
  const candidate = join(home, 'current', '.venv', 'bin', 'deepagent')
  if (!existsSync(candidate)) {
    throw new Error('DeepAgent CLI is not installed. Install the current WebUI Beta before opening Electron Preview.')
  }
  const binary = realpathSync(candidate)
  const versions = realpathSync(join(home, 'versions'))
  const relation = relative(versions, binary)
  if (!relation || relation.startsWith('..') || relation.startsWith('/')) {
    throw new Error('DeepAgent CLI resolves outside the managed product directory')
  }
  return binary
}

function runtimeEnvironment(supervisorEnvironment: RuntimeTaskSupervisorEnvironment | null = null): NodeJS.ProcessEnv {
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
  const command = managedCli()
  try {
    await execFileAsync(command, args, {
      env: runtimeEnvironment(supervisorEnvironment),
      timeout: READY_TIMEOUT_MS,
      maxBuffer: 1024 * 1024,
    })
  } catch (error) {
    const value = error as Error & { stderr?: string }
    throw new Error(value.stderr?.trim() || value.message)
  }
}

function runtimePort(): number {
  const recordPath = join(deepAgentHome(), 'runtime', 'webui', 'port.json')
  let record: unknown
  try {
    record = JSON.parse(readFileSync(recordPath, 'utf8'))
  } catch {
    throw new Error('DeepAgent WebUI did not publish a valid runtime port record')
  }
  const value = record as { product?: unknown; host?: unknown; port?: unknown }
  const port = Number(value.port)
  if (value.product !== 'deepagent-webui' || value.host !== '127.0.0.1' || !Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error('DeepAgent WebUI runtime port record is invalid')
  }
  return port
}

async function waitForReady(port: number): Promise<void> {
  const deadline = Date.now() + READY_TIMEOUT_MS
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/health`, { signal: AbortSignal.timeout(1_000) })
      if (response.ok) return
    } catch {
      // The managed runtime is still starting.
    }
    await new Promise(resolveReady => setTimeout(resolveReady, 300))
  }
  throw new Error(`DeepAgent WebUI did not become ready on local port ${port}`)
}

export function getServerUrl(port: number): string {
  return `http://127.0.0.1:${port}`
}

export async function startWebUiServer(
  _preferredPort: number | undefined,
  supervisorEnvironment: RuntimeTaskSupervisorEnvironment,
): Promise<string> {
  await runCli(['webui', 'start'], supervisorEnvironment)
  const port = runtimePort()
  await waitForReady(port)
  return getServerUrl(port)
}

export async function stopWebUiServer(): Promise<void> {
  if (!existsSync(join(deepAgentHome(), 'current', '.venv', 'bin', 'deepagent'))) return
  await runCli(['webui', 'stop'])
}
