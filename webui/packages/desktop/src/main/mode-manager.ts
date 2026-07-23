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
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

export type AppMode = 'assistant' | 'code'

export interface SharedConfig {
  apiKey: string
  model: string
  provider: string
  baseUrl?: string
  profile?: string
}

export type StartCodeModeResult =
  | { ok: true; url: string }
  | { ok: false; error: string }

export interface ModeManagerDeps {
  /** Electron app.getPath('userData') */
  userDataPath: string
  /** 发送广播到主窗口 webContents */
  broadcast?: (channel: string, payload: unknown) => void
  /** 启动 opencode 子进程的工厂（可测试 mock） */
  spawnOpenCode?: (command: string, args: string[], env: NodeJS.ProcessEnv) => ChildProcess
  /** 探测 opencode 二进制路径（可测试 mock），返回 null 表示未找到 */
  detectOpenCode?: () => string | null
  /** 等待端口 ready 的探活函数（可测试 mock） */
  waitForPort?: (port: number, timeoutMs?: number) => Promise<boolean>
  /** 分配空闲端口 */
  getFreePort?: () => Promise<number>
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
    return join(this.deps.userDataPath, MODE_FILE)
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
      writeFileSync(this.modeFile(), JSON.stringify({ mode }), 'utf8')
    } catch {
      /* best effort */
    }
  }

  private broadcast(mode: AppMode): void {
    this.deps.broadcast?.('hermes-desktop:mode-changed', mode)
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
    const detect = this.deps.detectOpenCode ?? defaultDetectOpenCode
    const bin = detect()
    if (!bin) {
      return { ok: false, error: 'opencode binary not found on PATH' }
    }
    const getPort = this.deps.getFreePort ?? defaultGetFreePort
    const wait = this.deps.waitForPort ?? defaultWaitForPort
    const spawnFn = this.deps.spawnOpenCode ?? defaultSpawnOpenCode
    const command = bin

    let port = 0
    try {
      port = await getPort()
    } catch (err) {
      return { ok: false, error: `failed to allocate port: ${(err as Error).message}` }
    }
    const env: NodeJS.ProcessEnv = {
      ...process.env,
      // 把共享配置作为 env 注入；opencode 支持 OPENCODE_API_KEY/MODEL/PROVIDER/BASE_URL
      OPENCODE_API_KEY: config.apiKey || '',
      OPENCODE_MODEL: config.model || '',
      OPENCODE_PROVIDER: config.provider || '',
      ...(config.baseUrl ? { OPENCODE_BASE_URL: config.baseUrl } : {}),
      ...(config.profile ? { OPENCODE_PROFILE: config.profile } : {}),
    }
    const args = ['serve', '--port', String(port), '--no-open']
    try {
      this.codeProcess = spawnFn(bin.includes('/') ? bin : 'opencode', args, env)
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
/** 默认检测：优先 OPENCODE_BIN，否则返回 'opencode' 让 PATH 解析 */
function defaultDetectOpenCode(): string | null {
  return process.env.OPENCODE_BIN || 'opencode'
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
