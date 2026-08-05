#!/usr/bin/env node
import { spawn, execSync, execFileSync } from 'child_process'
import { resolve, dirname, join, delimiter } from 'path'
import { fileURLToPath } from 'url'
import { readFileSync, writeFileSync, unlinkSync, mkdirSync, openSync, chmodSync, statSync, existsSync, realpathSync } from 'fs'
import { randomBytes } from 'crypto'
import { homedir } from 'os'

const __dirname = dirname(fileURLToPath(import.meta.url))
const __filename = fileURLToPath(import.meta.url)
const serverEntry = resolve(__dirname, '..', 'dist', 'server', 'index.js')
const pkgDir = resolve(__dirname, '..')
const pkg = JSON.parse(readFileSync(resolve(pkgDir, 'package.json'), 'utf-8'))
const VERSION = pkg.version
const DEEPAGENT_HOME = process.env.DEEPAGENT_HOME?.trim()
  ? resolve(process.env.DEEPAGENT_HOME.trim())
  : resolve(homedir(), '.deepagent')
const WEB_UI_HOME = process.env.HERMES_WEB_UI_HOME?.trim()
  ? resolve(process.env.HERMES_WEB_UI_HOME.trim())
  : join(DEEPAGENT_HOME, 'data', 'webui')
const PID_DIR = process.env.DEEPAGENT_WEBUI_RUNTIME_DIR?.trim()
  ? resolve(process.env.DEEPAGENT_WEBUI_RUNTIME_DIR.trim())
  : join(DEEPAGENT_HOME, 'runtime', 'webui')
const PID_FILE = join(PID_DIR, 'server.pid')
const LOG_FILE = join(PID_DIR, 'server.log')
const TOKEN_FILE = join(WEB_UI_HOME, '.token')
const LOGIN_LOCK_FILE = join(WEB_UI_HOME, '.login-lock.json')
const DEFAULT_PORT = 8648
const DEFAULT_RESTART_GRACE_MS = 5000
const DEFAULT_STOP_GRACE_MS = 15000
const STOP_POLL_INTERVAL_MS = 500

function envPositiveInt(name) {
  const value = Number(process.env[name])
  return Number.isFinite(value) && value > 0 ? value : undefined
}

function shouldPreserveBridgeOnShutdown() {
  const raw = String(process.env.HERMES_AGENT_BRIDGE_STOP_ON_SHUTDOWN || '').trim().toLowerCase()
  return ['0', 'false', 'no', 'off'].includes(raw)
}

function getDaemonStopGraceMs(options = {}) {
  const { restart = false } = options
  if (restart && shouldPreserveBridgeOnShutdown()) {
    return envPositiveInt('HERMES_WEB_UI_RESTART_GRACE_MS') ?? DEFAULT_RESTART_GRACE_MS
  }
  if (restart) {
    return envPositiveInt('HERMES_WEB_UI_RESTART_GRACE_MS')
      ?? envPositiveInt('HERMES_WEB_UI_STOP_GRACE_MS')
      ?? DEFAULT_STOP_GRACE_MS
  }
  return envPositiveInt('HERMES_WEB_UI_STOP_GRACE_MS') ?? DEFAULT_STOP_GRACE_MS
}

// ─── Auto-fix node-pty native module ──────────────────────────
function ensureNativeModules() {
  const prebuildDir = join(pkgDir, 'node_modules', 'node-pty', 'prebuilds', `${process.platform}-${process.arch}`)
  const helper = join(prebuildDir, 'spawn-helper')
  try {
    chmodSync(helper, 0o755)
  } catch {}
}

function getToken() {
  try {
    return readFileSync(TOKEN_FILE, 'utf-8').trim()
  } catch {
    return null
  }
}

function ensureToken() {
  let token = getToken()
  if (!token) {
    mkdirSync(dirname(TOKEN_FILE), { recursive: true })
    token = randomBytes(32).toString('hex')
    writeFileSync(TOKEN_FILE, token + '\n', { mode: 0o600 })
  }
  return token
}

function getNodeBinDir() {
  return dirname(process.execPath)
}

function getNpmBin() {
  return join(getNodeBinDir(), process.platform === 'win32' ? 'npm.cmd' : 'npm')
}

function getCurrentNodeEnv() {
  return {
    ...process.env,
    PATH: [getNodeBinDir(), process.env.PATH].filter(Boolean).join(delimiter),
    npm_node_execpath: process.execPath,
  }
}

function getGlobalPrefix() {
  return execFileSync(getNpmBin(), ['prefix', '-g'], {
    encoding: 'utf-8',
    stdio: ['pipe', 'pipe', 'pipe'],
    env: getCurrentNodeEnv(),
  }).trim()
}

function getGlobalCliBin() {
  const prefix = getGlobalPrefix()
  return process.platform === 'win32'
    ? join(prefix, 'hermes-web-ui.cmd')
    : join(prefix, 'bin', 'hermes-web-ui')
}

function getWindowsShell() {
  const systemRoot = process.env.SystemRoot || 'C:\\Windows'
  const candidates = [
    process.env.ComSpec,
    join(systemRoot, 'System32', 'cmd.exe'),
  ].filter(Boolean)

  for (const candidate of candidates) {
    if (existsSync(candidate)) return candidate
  }

  return 'cmd.exe'
}

function quoteForWindowsCommand(value) {
  return `"${value.replace(/"/g, '""')}"`
}

function spawnCli(command, args, options) {
  if (process.platform === 'win32') {
    const lowerCommand = String(command).toLowerCase()
    if (!lowerCommand.endsWith('.cmd') && !lowerCommand.endsWith('.bat')) {
      return spawn(command, args, options)
    }

    const commandLine = `${quoteForWindowsCommand(command)} ${args.map(arg => String(arg)).join(' ')}`
    return spawn(getWindowsShell(), ['/d', '/s', '/c', commandLine], options)
  }

  return spawn(command, args, options)
}

function getPortFromArgs() {
  if (process.argv[3] && !isNaN(process.argv[3])) return parseInt(process.argv[3])
  if (process.argv.includes('--port')) return parseInt(process.argv[process.argv.indexOf('--port') + 1])
  return null
}

function getRunningPort() {
  const pid = getPid()
  if (!pid || !isRunning(pid)) return null

  try {
    if (process.platform === 'win32') {
      const out = execSync(`netstat -aon -p tcp | findstr LISTENING | findstr " ${pid}$"`, { encoding: 'utf-8' }).trim()
      const line = out.split('\n').find(Boolean)
      const address = line?.trim().split(/\s+/)[1]
      const port = address?.split(':').pop()
      return port ? parseInt(port, 10) : null
    }

    const out = execSync(`lsof -Pan -p ${pid} -iTCP -sTCP:LISTEN`, { encoding: 'utf-8' }).trim()
    const lines = out.split('\n').slice(1)
    for (const line of lines) {
      const match = line.match(/:(\d+)\s+\(LISTEN\)$/)
      if (match) return parseInt(match[1], 10)
    }
  } catch {}

  return null
}

function getUpdatePort() {
  const argPort = getPortFromArgs()
  if (argPort !== null) return argPort

  const runningPort = getRunningPort()
  if (runningPort !== null) return runningPort

  if (process.env.PORT && !isNaN(process.env.PORT)) return parseInt(process.env.PORT)
  return DEFAULT_PORT
}

function getPort() {
  const argPort = getPortFromArgs()
  return argPort ?? DEFAULT_PORT
}

function shouldOpenBrowser(argv = process.argv) {
  return !argv.includes('--no-open')
}

function getRestartArgs(port, argv = process.argv) {
  const args = ['restart', '--port', String(port)]
  if (!shouldOpenBrowser(argv)) args.push('--no-open')
  return args
}

function enableClientMode() {
  process.env.HERMES_WEB_UI_DISABLE_GATEWAY_AUTOSTART = '1'
  process.env.CORS_ORIGINS = '*'
}

function commandExists(command) {
  try {
    if (process.platform === 'win32') {
      execFileSync('where', [command], { stdio: 'ignore', windowsHide: true })
    } else {
      execFileSync('sh', ['-c', `command -v "$1" >/dev/null 2>&1`, 'sh', command], { stdio: 'ignore' })
    }
    return true
  } catch {
    return false
  }
}

function parseUnixNetstatListeningPids(out, port) {
  const pids = []
  for (const line of out.split(/\r?\n/)) {
    const parts = line.trim().split(/\s+/)
    if (parts.length < 6) continue

    const proto = parts[0]?.toLowerCase()
    if (!proto?.startsWith('tcp')) continue

    const localAddress = parts[3]
    const state = parts.find(part => part.toUpperCase() === 'LISTEN' || part.toUpperCase() === 'LISTENING')
    if (!state || !localAddress?.endsWith(`:${port}`)) continue

    const pidPart = parts.find(part => /^\d+\//.test(part))
    const pid = pidPart ? parseInt(pidPart.split('/')[0], 10) : NaN
    if (Number.isFinite(pid)) pids.push(pid)
  }
  return pids
}

function getListeningPids(port) {
  if (!port || isNaN(port)) return []
  const uniquePids = (pids) => [...new Set(pids.filter(pid => Number.isFinite(pid)))]

  try {
    if (process.platform === 'win32') {
      const out = execSync('netstat -aon -p tcp', { encoding: 'utf-8' })
      return uniquePids(out.split('\n')
        .map(line => line.trim())
        .filter(line => line.includes('LISTENING'))
        .map(line => line.split(/\s+/))
        .filter(parts => {
          const address = parts[1] || ''
          const listenPort = parseInt(address.split(':').pop(), 10)
          return listenPort === port
        })
        .map(parts => parseInt(parts[parts.length - 1], 10)))
    }
  } catch {
    return []
  }

  if (commandExists('ss')) {
    try {
      const out = execFileSync('ss', ['-ltnp', `sport = :${port}`], { encoding: 'utf-8', stdio: ['ignore', 'pipe', 'ignore'] })
      const pids = uniquePids(out.split(/\r?\n/)
        .map(line => line.match(/pid=(\d+)/)?.[1])
        .map(pid => parseInt(pid || '', 10)))
      if (pids.length) return pids
    } catch {}
  }

  if (commandExists('lsof')) {
    try {
      const out = execFileSync('lsof', [`-tiTCP:${port}`, '-sTCP:LISTEN'], { encoding: 'utf-8', stdio: ['ignore', 'pipe', 'ignore'] }).trim()
      const pids = uniquePids(out.split(/\r?\n/).map(pid => parseInt(pid, 10)))
      if (pids.length) return pids
    } catch {}
  }

  if (commandExists('netstat')) {
    try {
      const out = execFileSync('netstat', ['-anp', 'tcp'], { encoding: 'utf-8', stdio: ['ignore', 'pipe', 'ignore'] })
      const pids = uniquePids(parseUnixNetstatListeningPids(out, port))
      if (pids.length) return pids
    } catch {}
  }

  return []
}

function readPidFile() {
  try {
    const pid = parseInt(readFileSync(PID_FILE, 'utf-8').trim())
    return Number.isFinite(pid) ? pid : null
  } catch {}

  return null
}

function getPid() {
  const pid = readPidFile()
  if (pid) {
    if (isRunning(pid) && isOwnedServerProcess(pid)) return pid
    removePid()
  }

  return null
}

function isOwnedServerProcess(pid) {
  // Phase 2 officially supports macOS Apple Silicon. Refuse to stop an
  // unverifiable PID on other platforms rather than risk another product.
  if (process.platform === 'win32') return false
  try {
    const command = execFileSync('ps', ['-p', String(pid), '-o', 'command='], {
      encoding: 'utf-8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim()
    return command.includes(serverEntry)
  } catch {
    return false
  }
}

function isRunning(pid) {
  try {
    process.kill(pid, 0)
    return true
  } catch (err) {
    return err?.code === 'EPERM'
  }
}

function writePid(pid) {
  writeFileSync(PID_FILE, String(pid), { mode: 0o600 })
}

function removePid() {
  try { unlinkSync(PID_FILE) } catch {}
}

function buildServerEnv(port, token) {
  const passthrough = [
    'PATH', 'HOME', 'TMPDIR', 'TMP', 'TEMP', 'LANG', 'LC_ALL', 'LC_CTYPE',
    'SHELL', 'SystemRoot', 'ComSpec', 'PATHEXT', 'SSL_CERT_FILE', 'SSL_CERT_DIR',
    'NODE_EXTRA_CA_CERTS', 'PROFILE', 'WORKSPACE_BASE',
    'HERMES_DESKTOP', 'DEEPAGENT_RUNTIME_LEASE_SOCKET',
    'DEEPAGENT_RUNTIME_LEASE_TOKEN', 'DEEPAGENT_RUNTIME_LEASE_TTL_MS',
    'HERMES_WEB_UI_AUTH_JWT_EXPIRES_IN',
    'HERMES_WEB_UI_DISABLE_GATEWAY_AUTOSTART',
    'HERMES_WEB_UI_MANAGED_GATEWAY',
    'HERMES_WEB_UI_STOP_GATEWAYS_ON_SHUTDOWN',
    'HERMES_WEB_UI_DISABLE_MCP_AUTOINJECT',
    'HERMES_WEB_UI_DISABLE_SKILL_INJECTION',
  ]
  const env = {}
  for (const name of passthrough) {
    if (process.env[name]) env[name] = process.env[name]
  }
  Object.assign(env, {
    DEEPAGENT_HOME,
    HERMES_HOME: DEEPAGENT_HOME,
    HERMES_WEB_UI_HOME: WEB_UI_HOME,
    HERMES_WEBUI_STATE_DIR: WEB_UI_HOME,
    DEEPAGENT_WEBUI_RUNTIME_DIR: PID_DIR,
    BIND_HOST: '127.0.0.1',
    HERMES_LAN_DISCOVERY_ENABLED: 'false',
    NODE_ENV: 'production',
    PORT: String(port),
    AUTH_TOKEN: token,
  })
  return env
}

function startDaemon(port) {
  const existing = getPid()
  if (existing && isRunning(existing)) {
    console.log(`  ✗ DeepAgent WebUI is already running (PID: ${existing})`)
    console.log('    Use "deepagent webui stop" to stop it first')
    process.exit(1)
  }
  removePid()

  // Never kill, reuse, or adopt another product's process.
  const occupied = getListeningPids(port)
  if (occupied.length) {
    console.log(`  ✗ Port ${port} is already in use; choose another port`)
    process.exit(1)
  }

  mkdirSync(PID_DIR, { recursive: true, mode: 0o700 })
  chmodSync(PID_DIR, 0o700)

  ensureNativeModules()
  const token = ensureToken()

  // Rotate log if over 3MB — keep last 2000 lines
  const MAX_LOG_SIZE = 3 * 1024 * 1024
  const MAX_LOG_LINES = 2000
  try {
    const stat = statSync(LOG_FILE)
    if (stat.size > MAX_LOG_SIZE) {
      const content = readFileSync(LOG_FILE, 'utf-8')
      const lines = content.split('\n')
      const kept = lines.slice(-MAX_LOG_LINES)
      writeFileSync(LOG_FILE, kept.join('\n'), 'utf-8')
      console.log(`  ↻ Log rotated (${(stat.size / 1024 / 1024).toFixed(1)}MB → ${kept.length} lines)`)
    }
  } catch { }

  const logStream = openSync(LOG_FILE, 'a')
  const windowsShell = process.platform === 'win32' ? getWindowsShell() : null
  const serverEnv = buildServerEnv(port, token)
  if (windowsShell) {
    serverEnv.SHELL = serverEnv.SHELL?.trim() || windowsShell
    serverEnv.ComSpec = serverEnv.ComSpec?.trim() || windowsShell
  }
  const child = spawn(process.execPath, [serverEntry], {
    cwd: pkgDir,
    detached: true,
    stdio: ['ignore', logStream, logStream],
    env: serverEnv,
    windowsHide: true,
  })

  child.on('error', (err) => {
    console.error(`  ✗ Failed to start: ${err.message}`)
    removePid()
    process.exit(1)
  })

  child.unref()
  writePid(child.pid)

  // Poll health endpoint until server is ready (setTimeout to avoid overlapping requests)
  const healthUrl = `http://127.0.0.1:${port}/health`
  const maxWait = 30000
  const interval = 500
  let waited = 0

  console.log(`  ⏳ Starting DeepAgent WebUI (PID: ${child.pid}, port: ${port})...`)

  function poll() {
    waited += interval
    if (!isRunning(child.pid)) {
      console.log('  ✗ Failed to start DeepAgent WebUI')
      console.log(`    Check log: ${LOG_FILE}`)
      removePid()
      process.exit(1)
      return
    }

    fetch(healthUrl).then(res => {
      if (res.ok) {
        const url = `http://localhost:${port}`
        console.log('  ✓ DeepAgent WebUI started')
        console.log(`    ${url}`)
        console.log(`    Log: ${LOG_FILE}`)
        if (shouldOpenBrowser()) {
          const isWin = process.platform === 'win32'
          const cmd = isWin ? `start ${url}` : process.platform === 'darwin' ? `open ${url}` : `xdg-open ${url}`
          try { execSync(cmd, { stdio: 'ignore' }) } catch {}
        }
      } else if (waited < maxWait) {
        setTimeout(poll, interval)
      } else {
        console.log(`  ⚠ Server process is running but health check failed after ${maxWait / 1000}s`)
        console.log(`    Check log: ${LOG_FILE}`)
        const url = `http://localhost:${port}`
        console.log(`    ${url}`)
      }
    }).catch(() => {
      if (waited < maxWait) {
        setTimeout(poll, interval)
      } else {
        console.log(`  ⚠ Server process is running but health check failed after ${maxWait / 1000}s`)
        console.log(`    Check log: ${LOG_FILE}`)
        const url = `http://localhost:${port}`
        console.log(`    ${url}`)
      }
    })
  }

  setTimeout(poll, interval)
}

function stopDaemon(options = {}) {
  const { restart = false } = options
  let pidFromFile = readPidFile()
  let cleanedStalePid = false
  if (pidFromFile && !isRunning(pidFromFile)) {
    removePid()
    console.log(`  ✓ DeepAgent WebUI was not running (cleaned stale PID: ${pidFromFile})`)
    pidFromFile = null
    cleanedStalePid = true
  }
  if (pidFromFile && !isOwnedServerProcess(pidFromFile)) {
    console.log(`  ✗ Refusing to stop PID ${pidFromFile}: it is not the DeepAgent WebUI server`)
    process.exit(1)
  }

  const pid = pidFromFile
  if (!pid) {
    if (cleanedStalePid) return
    console.log('  ✗ DeepAgent WebUI is not running')
    process.exit(1)
  }

  if (!isRunning(pid)) {
    removePid()
    console.log('  ✓ DeepAgent WebUI was not running (cleaned stale PID)')
    return
  }

  try {
    try {
      process.kill(pid, restart ? 'SIGUSR2' : 'SIGTERM')
      // Restart uses a shorter grace window than stop. By default the server
      // still shuts down the bridge; set HERMES_AGENT_BRIDGE_STOP_ON_SHUTDOWN=0
      // to keep the bridge across restarts.
      const graceMs = getDaemonStopGraceMs({ restart })
      const attempts = Math.max(1, Math.ceil(graceMs / STOP_POLL_INTERVAL_MS))
      for (let i = 0; i < attempts; i++) {
        if (!isRunning(pid)) break
        Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, STOP_POLL_INTERVAL_MS)
      }
    } catch {}
    // Force kill if still alive
    if (isRunning(pid)) {
      try {
        process.kill(pid, 'SIGKILL')
      } catch (err) {
        if (err?.code !== 'ESRCH') throw err
      }
    }
    removePid()
    console.log(`  ✓ DeepAgent WebUI stopped (PID: ${pid})`)
  } catch (err) {
    console.log(`  ✗ Failed to stop: ${err.message}`)
    process.exit(1)
  }
}

function showStatus() {
  const pid = getPid()
  if (pid && isRunning(pid)) {
    console.log(`  ✓ DeepAgent WebUI is running (PID: ${pid})`)
    console.log(`    PID file: ${PID_FILE}`)
  } else {
    if (pid) removePid()
    console.log('  ✗ DeepAgent WebUI is not running')
  }
}

function clearLoginLocks(options = {}) {
  const { silent = false, checkRunning = true } = options
  const serverRunning = checkRunning ? !!getPid() : false
  let removed = false

  try {
    unlinkSync(LOGIN_LOCK_FILE)
    removed = true
    if (!silent) console.log(`  ✓ Removed login lock file: ${LOGIN_LOCK_FILE}`)
  } catch (err) {
    if (err?.code === 'ENOENT') {
      if (!silent) console.log(`  ✓ No login lock file found: ${LOGIN_LOCK_FILE}`)
    } else {
      if (!silent) console.log(`  ✗ Failed to remove login lock file: ${err.message}`)
      throw err
    }
  }

  if (!silent && serverRunning) {
    console.log('  ⚠ DeepAgent WebUI is running; restart it to clear in-memory login locks.')
    console.log('    Run: deepagent webui stop && deepagent webui start')
  }

  return { path: LOGIN_LOCK_FILE, removed, serverRunning }
}

async function main() {
  const command = process.argv[2] || 'start'

  if (['-v', '--version', 'version'].includes(command)) {
    console.log(`DeepAgent WebUI v${VERSION}`)
    process.exit(0)
  }

  if (['-h', '--help', 'help'].includes(command)) {
    console.log(`
DeepAgent WebUI v${VERSION}

Internal launcher used by: deepagent webui <command>

Commands:
  start [port]       Start the server (default port: ${DEFAULT_PORT})
  client [port]      Start server for a remote client (disable gateway autostart, allow all CORS)
  stop               Stop the server
  restart [port]     Restart the server
  status             Show server status
  clear-login-locks  Delete the login IP lock file
  version            Show version number

Options:
  -v, --version      Show version number
  -h, --help         Show this help message
  --no-open          Do not open a browser after startup
  --port <port>      Specify port (used with start/client/restart)
  --restart          Restart after clear-login-locks
`)
    process.exit(0)
  }

  switch (command) {
    case 'start':
      startDaemon(getPort())
      break
    case 'client':
      enableClientMode()
      startDaemon(getPort())
      break
    case 'stop':
      stopDaemon()
      break
    case 'restart':
      stopDaemon({ restart: true })
      setTimeout(() => startDaemon(getPort()), 500)
      break
    case 'status':
      showStatus()
      break
    case 'clear-login-locks': {
      const restartAfterClear = process.argv.includes('--restart')
      const result = clearLoginLocks()
      if (restartAfterClear && result.serverRunning) {
        const port = getRunningPort() ?? getPort()
        stopDaemon({ restart: true })
        setTimeout(() => startDaemon(port), 500)
      }
      break
    }
    default:
      console.error(`  ✗ Unknown DeepAgent WebUI command: ${command}`)
      console.error('    Run: deepagent webui --help')
      process.exit(1)
  }
}

if (process.argv[1] && realpathSync(resolve(process.argv[1])) === __filename) {
  main().catch(err => {
    console.error(`  ✗ ${err?.message || err}`)
    process.exit(1)
  })
}

export {
  clearLoginLocks,
  commandExists,
  getDaemonStopGraceMs,
  getListeningPids,
  getRestartArgs,
  parseUnixNetstatListeningPids,
  shouldOpenBrowser,
  stopDaemon,
}
