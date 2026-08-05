/**
 * mode-manager.ts — 双模式切换主进程状态与 IPC
 *
 * 职责：
 *  - 持有当前 AppMode（'assistant' | 'code'），持久化到 userData/app-mode.json
 *  - 注册 IPC handlers：get-mode / set-mode / start-code-mode / stop-code-mode
 *  - start-code-mode 负责启动 opencode serve 子进程，返回本地 URL
 *  - 不直接依赖 BrowserWindow 实例（通过回调注入），便于单测
 *
 * 本模块是 Stage 9 从 src/main/index.ts 抽离出来的独立单元，
 * 保持 index.ts 不继续膨胀并便于单测。
 */
import { spawn, type ChildProcess } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'

export type AppMode = 'assistant' | 'code'

export interface SharedConfig {
  model: string
  provider: string
  baseUrl?: string
  profile?: string
}

export type StartCodeModeResult =
  | { ok: true; url: string }
  | { ok: false; error: string }

export interface ModeManagerDeps {
  /** DeepAgent product root, normally ~/.deepagent. */
  productHome: string
  /** 发送广播到主窗口 webContents */
  broadcast?: (mode: AppMode) => void
  /** 启动 opencode 子进程的工厂（可测试 mock） */
  spawnOpenCode?: (command: string, args: string[], env: NodeJS.ProcessEnv) => ChildProcess
  /** 探测 opencode 二进制路径（可测试 mock），返回 null 表示未找到 */
  detectOpenCode?: () => string | null
  /** 等待端口 ready 的探活函数（可测试 mock） */
  waitForPort?: (port: number, timeoutMs?: number) => Promise<boolean>
  /** 分配空闲端口 */
  getFreePort?: () => Promise<number>
  /** Main-process credential resolver backed by Keychain/safe storage. */
  resolveCredentials?: (provider: string) => Promise<NodeJS.ProcessEnv>
}

const MODE_FILE = 'app-mode.json'
const DEFAULT_MODE: AppMode = 'assistant'
const START_TIMEOUT_MS = 20_000

export class ModeManager {
  private currentMode: AppMode = DEFAULT_MODE
  private codeModeUrl: string | null = null
  private codeProcess: ChildProcess | null = null
  constructor(private readonly deps: ModeManagerDeps) {
    this.currentMode = this.readPersistedMode()
  }

  // ─── 持久化 ─────────────────────────────────────────────────
  private modeFile(): string {
    return join(this.deps.productHome, 'data', 'electron', MODE_FILE)
  }

  private readPersistedMode(): AppMode {
    try {
      if (!existsSync(this.modeFile())) return DEFAULT_MODE
      const raw = readFileSync(this.modeFile(), 'utf8')
      const parsed = JSON.parse(raw) as { mode?: AppMode }
      return parsed.mode === 'code' ? 'code' : 'assistant'
    } catch {
      return DEFAULT_MODE
    }
  }

  private persistMode(mode: AppMode): void {
    try {
      mkdirSync(join(this.deps.productHome, 'data', 'electron'), { recursive: true, mode: 0o700 })
      writeFileSync(this.modeFile(), JSON.stringify({ mode }), 'utf8')
    } catch {
      /* best effort */
    }
  }

  private broadcast(mode: AppMode): void {
    this.deps.broadcast?.(mode)
  }

  // ─── 公共 API ───────────────────────────────────────────────
  getMode(): AppMode {
    return this.currentMode
  }

  async setMode(mode: AppMode): Promise<void> {
    if (mode !== 'assistant' && mode !== 'code') return
    if (this.currentMode === mode) return
    this.currentMode = mode
    this.persistMode(mode)
    this.broadcast(mode)
  }

  getCodeModeUrl(): string | null {
    return this.codeModeUrl
  }

  /**
   * 启动 OpenCode 子进程。
   * 真实环境调用 `opencode serve --port <port>` 并等待端口 ready。
   * 注入的 spawn/waitForPort/detectOpenCode/getFreePort 便于单测。
   */
  async startCodeMode(config: SharedConfig): Promise<StartCodeModeResult> {
    // 已经在运行且 URL 有效，直接返回
    if (this.codeModeUrl && this.codeProcess && !this.codeProcess.killed) {
      return { ok: true, url: this.codeModeUrl }
    }
    const detect = this.deps.detectOpenCode ?? (() => defaultDetectOpenCode(this.deps.productHome))
    const bin = detect()
    if (!bin) {
      return { ok: false, error: 'DeepCode runtime is not installed' }
    }
    const deepCodeRuntimeRoot = resolve(this.deps.productHome, 'runtime', 'deepcode')
    let realBinary: string
    let realRuntimeRoot: string
    try {
      realBinary = realpathSync(bin)
      realRuntimeRoot = realpathSync(deepCodeRuntimeRoot)
    } catch {
      return { ok: false, error: 'DeepCode runtime path is invalid' }
    }
    if (!realBinary.startsWith(`${realRuntimeRoot}/`)) {
      return { ok: false, error: 'Refusing an OpenCode binary outside DeepAgent runtime' }
    }
    const getPort = this.deps.getFreePort ?? defaultGetFreePort
    const wait = this.deps.waitForPort ?? defaultWaitForPort
    const spawnFn = this.deps.spawnOpenCode ?? defaultSpawnOpenCode
    const command = realBinary

    let port = 0
    try {
      port = await getPort()
    } catch (err) {
      return { ok: false, error: `failed to allocate port: ${(err as Error).message}` }
    }
    const deepCodeDataRoot = resolve(this.deps.productHome, 'data', 'deepcode')
    const deepCodeCacheRoot = resolve(this.deps.productHome, 'cache', 'deepcode')
    const deepCodeHome = resolve(deepCodeDataRoot, 'home')
    for (const directory of [deepCodeDataRoot, deepCodeCacheRoot, deepCodeHome]) {
      mkdirSync(directory, { recursive: true, mode: 0o700 })
    }
    const credentialEnv = this.deps.resolveCredentials
      ? await this.deps.resolveCredentials(config.provider).catch(() => ({}))
      : {}
    const env: NodeJS.ProcessEnv = {
      PATH: process.env.PATH,
      TMPDIR: process.env.TMPDIR,
      LANG: process.env.LANG,
      LC_ALL: process.env.LC_ALL,
      HOME: deepCodeHome,
      XDG_CONFIG_HOME: join(deepCodeDataRoot, 'config'),
      XDG_DATA_HOME: join(deepCodeDataRoot, 'data'),
      XDG_STATE_HOME: join(deepCodeDataRoot, 'state'),
      XDG_CACHE_HOME: deepCodeCacheRoot,
      OPENCODE_CONFIG_DIR: join(deepCodeDataRoot, 'config', 'opencode'),
      OPENCODE_MODEL: config.model || '',
      OPENCODE_PROVIDER: config.provider || '',
      ...(config.baseUrl ? { OPENCODE_BASE_URL: config.baseUrl } : {}),
      ...(config.profile ? { OPENCODE_PROFILE: config.profile } : {}),
      ...credentialEnv,
    }
    const args = ['serve', '--hostname', '127.0.0.1', '--port', String(port)]
    try {
      this.codeProcess = spawnFn(command, args, env)
    } catch (err) {
      return { ok: false, error: `spawn failed: ${(err as Error).message}` }
    }
    this.codeProcess.on('exit', () => {
      this.codeProcess = null
      this.codeModeUrl = null
    })
    const ready = await wait(port, START_TIMEOUT_MS).catch(() => false)
    if (!ready) {
      this.codeProcess?.kill()
      this.codeProcess = null
      return { ok: false, error: 'opencode serve did not start within 20s' }
    }
    this.codeModeUrl = `http://127.0.0.1:${port}`
    return { ok: true, url: this.codeModeUrl }
  }

  async stopCodeMode(): Promise<void> {
    if (this.codeProcess && !this.codeProcess.killed) {
      this.codeProcess.kill()
    }
    this.codeProcess = null
    this.codeModeUrl = null
  }
}

// ─── 默认实现（可被 deps 覆盖） ─────────────────────────────
/** Only use the DeepAgent-managed runtime; never search PATH or user OpenCode. */
function defaultDetectOpenCode(productHome: string): string | null {
  const binary = join(resolve(productHome), 'runtime', 'deepcode', 'current', process.platform === 'win32' ? 'opencode.exe' : 'opencode')
  return existsSync(binary) ? binary : null
}

function defaultSpawnOpenCode(cmd: string, args: string[], env: NodeJS.ProcessEnv): ChildProcess {
  return spawn(cmd, args, { env, stdio: ['ignore', 'ignore', 'ignore'] })
}

async function defaultGetFreePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    try {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const net = require('node:net') as typeof import('node:net')
      const srv = net.createServer()
      srv.unref()
      srv.on('error', reject)
      srv.listen(0, '127.0.0.1', () => {
        const addr = srv.address() as { port: number } | null
        const port = addr?.port ?? 0
        srv.close(() => resolve(port))
      })
    } catch (err) {
      reject(err)
    }
  })
}

async function defaultWaitForPort(port: number, timeoutMs = 20_000): Promise<boolean> {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const ok = await new Promise<boolean>(resolve => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const net = require('node:net') as typeof import('node:net')
        const sock = net.connect(port, '127.0.0.1')
        sock.once('connect', () => { sock.destroy(); resolve(true) })
        sock.once('error', () => { sock.destroy(); resolve(false) })
        setTimeout(() => { sock.destroy(); resolve(false) }, 500)
      } catch {
        resolve(false)
      }
    })
    if (ok) return true
    await new Promise(r => setTimeout(r, 300))
  }
  return false
}
