/**
 * DeepAgent Legacy Preview — security-only desktop wrapper.
 *
 * This preview contains no Agent runtime. It starts the installed DeepAgent
 * WebUI through the managed CLI and authenticates with a one-time ticket.
 */

const { app, BrowserWindow, Menu, shell } = require('electron')
const { createHash, randomBytes } = require('crypto')
const { execFileSync } = require('child_process')
const { existsSync, mkdirSync, readFileSync, realpathSync, writeFileSync } = require('fs')
const { homedir } = require('os')
const path = require('path')

const IS_MAC = process.platform === 'darwin'
const WINDOW_TITLE = 'DeepAgent Legacy Preview'
const DEEPAGENT_HOME = path.resolve(process.env.DEEPAGENT_HOME || path.join(homedir(), '.deepagent'))
const RUNTIME_DIR = path.join(DEEPAGENT_HOME, 'runtime', 'webui')
const SAFE_ENV_NAMES = [
  'PATH', 'HOME', 'TMPDIR', 'TMP', 'TEMP', 'LANG', 'LC_ALL', 'LC_CTYPE',
  'SHELL', 'SSL_CERT_FILE', 'SSL_CERT_DIR', 'NODE_EXTRA_CA_CERTS',
]

mkdirSync(path.join(DEEPAGENT_HOME, 'data', 'electron-legacy'), { recursive: true, mode: 0o700 })
app.setName(WINDOW_TITLE)
app.setPath('userData', path.join(DEEPAGENT_HOME, 'data', 'electron-legacy'))

function managedCli() {
  const configured = process.env.DEEPAGENT_CLI
  const candidate = configured
    ? path.resolve(configured)
    : path.join(DEEPAGENT_HOME, 'current', '.venv', 'bin', 'deepagent')
  if (!existsSync(candidate)) throw new Error('DeepAgent CLI is not installed')
  const real = realpathSync(candidate)
  const managedRoot = realpathSync(DEEPAGENT_HOME)
  if (!configured && !real.startsWith(`${managedRoot}${path.sep}`)) {
    throw new Error('DeepAgent CLI path escapes the product directory')
  }
  return real
}

function childEnv() {
  const env = {}
  for (const name of SAFE_ENV_NAMES) {
    if (process.env[name]) env[name] = process.env[name]
  }
  return {
    ...env,
    DEEPAGENT_HOME,
    HERMES_HOME: DEEPAGENT_HOME,
  }
}

function readManagedPort() {
  const record = JSON.parse(readFileSync(path.join(RUNTIME_DIR, 'port.json'), 'utf8'))
  const port = Number(record.port)
  if (record.product !== 'deepagent-webui' || record.host !== '127.0.0.1' || !Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error('DeepAgent WebUI returned an invalid local endpoint')
  }
  return port
}

function createLoginUrl(port) {
  const ticket = randomBytes(32).toString('base64url')
  const digest = createHash('sha256').update(ticket).digest('hex')
  const tickets = path.join(RUNTIME_DIR, 'login-tickets')
  mkdirSync(tickets, { recursive: true, mode: 0o700 })
  writeFileSync(path.join(tickets, `${digest}.json`), `${JSON.stringify({
    schema_version: 1,
    product: 'deepagent-webui-ticket',
    sha256: digest,
    expires_at: Date.now() + 60_000,
  })}\n`, { encoding: 'utf8', flag: 'wx', mode: 0o600 })
  return `http://127.0.0.1:${port}/#/?ticket=${ticket}`
}

function startManagedWebUi() {
  execFileSync(managedCli(), ['webui', 'start'], {
    env: childEnv(),
    stdio: ['ignore', 'pipe', 'pipe'],
    timeout: 60_000,
  })
  return createLoginUrl(readManagedPort())
}

function buildMenu() {
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    {
      label: WINDOW_TITLE,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' },
      ],
    },
    { label: 'Edit', submenu: [{ role: 'undo' }, { role: 'redo' }, { type: 'separator' }, { role: 'cut' }, { role: 'copy' }, { role: 'paste' }, { role: 'selectAll' }] },
    { label: 'View', submenu: [{ role: 'reload' }, { role: 'forceReload' }, { type: 'separator' }, { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' }, { type: 'separator' }, { role: 'togglefullscreen' }] },
    { label: 'Window', submenu: [{ role: 'minimize' }, { role: 'zoom' }, { type: 'separator' }, ...(IS_MAC ? [{ role: 'front' }, { role: 'window' }] : [{ role: 'close' }])] },
  ]))
}

let mainWindow = null

function errorPage(error) {
  const message = String(error instanceof Error ? error.message : error)
    .replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]))
  return `data:text/html;charset=utf-8,${encodeURIComponent(`<!doctype html><meta charset="utf-8"><title>${WINDOW_TITLE}</title><body style="font-family:system-ui;padding:32px;background:#1a1a1a;color:#eee"><h2>DeepAgent WebUI is unavailable</h2><p>${message}</p><p>Install it with <code>deepagent webui install</code>, then reopen this preview.</p></body>`)}`
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 960,
    minHeight: 600,
    title: WINDOW_TITLE,
    backgroundColor: '#1a1a1a',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  })
  mainWindow.once('ready-to-show', () => mainWindow?.show())
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https://') || url.startsWith('http://')) shell.openExternal(url).catch(() => {})
    return { action: 'deny' }
  })
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (url.startsWith('http://127.0.0.1:')) return
    event.preventDefault()
    if (url.startsWith('https://') || url.startsWith('http://')) shell.openExternal(url).catch(() => {})
  })
  try {
    mainWindow.loadURL(startManagedWebUi())
  } catch (error) {
    mainWindow.loadURL(errorPage(error))
  }
}

app.whenReady().then(() => {
  buildMenu()
  createWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (!IS_MAC) app.quit()
})
