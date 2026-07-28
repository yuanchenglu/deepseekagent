import { app, BrowserWindow, Menu, Tray, shell, ipcMain, nativeImage, Notification, safeStorage, screen } from 'electron'
import { existsSync } from 'node:fs'
import { homedir } from 'node:os'
import { join } from 'node:path'
import { startWebUiServer, stopWebUiServer } from './webui-server'
import { deepAgentHome, desktopIcon, desktopTrayTemplateIcon, desktopWindowsTrayIcon, webuiDir, webUiHome } from './paths'
import { checkForDesktopUpdates, initAutoUpdater } from './updater'
import { t } from './desktop-i18n'
// 双模式切换管理器（Stage 9 新增）
import { ModeManager, type AppMode, type SharedConfig, type StartCodeModeResult } from './mode-manager'
import { CredentialVault } from './credential-vault'
import { createDesktopLoginUrl } from './login-ticket'
import { runPhase3Migration } from './migration'
import { registerWorkspaceLockIpc } from './workspace-lock-ipc'
import { RuntimeTaskSupervisor, type RuntimeTaskSupervisorEnvironment } from './runtime-task-supervisor'

const PORT = Number(process.env.HERMES_DESKTOP_PORT) || 8748
const START_HIDDEN = process.argv.includes('--hidden')
const QUIT_EXISTING = process.argv.includes('--quit')
const APP_USER_MODEL_ID = 'org.starseas.deepagent'
const PET_WINDOW_DEFAULT_WIDTH = 300
const PET_WINDOW_DEFAULT_HEIGHT = 320
const PET_WINDOW_MIN_SIZE = 72
const PET_WINDOW_MAX_SIZE = 1200
type WindowControlAction = 'minimize' | 'toggle-maximize' | 'close'
type DesktopWindowBounds = { x: number; y: number; width: number; height: number }

let mainWindow: BrowserWindow | null = null
let petWindow: BrowserWindow | null = null
// 双模式管理器（Stage 9）：由 app.whenReady 时实例化
let modeManager: ModeManager | null = null
let credentialVault: CredentialVault | null = null
let runtimeTaskSupervisor: RuntimeTaskSupervisor | null = null
let runtimeTaskSupervisorEnvironment: RuntimeTaskSupervisorEnvironment | null = null
let petWindowLoadPromise: Promise<void> | null = null
let serverUrl: string | null = null
let tray: Tray | null = null
let isQuitting = false
let isBootstrapping = false
let windowFadeTimer: NodeJS.Timeout | null = null
const activeNotifications = new Set<Notification>()

if (process.platform === 'win32') {
  app.setAppUserModelId(APP_USER_MODEL_ID)
}

function cancelWindowFade() {
  if (windowFadeTimer) {
    clearInterval(windowFadeTimer)
    windowFadeTimer = null
  }
}

function showWindowWithFade(focus = true) {
  if (!mainWindow || mainWindow.isDestroyed()) return
  if (mainWindow.isMinimized()) mainWindow.restore()

  cancelWindowFade()
  if (process.platform !== 'win32' || mainWindow.isVisible()) {
    mainWindow.setOpacity(1)
    mainWindow.show()
    if (focus) mainWindow.focus()
    return
  }

  const durationMs = 180
  const startedAt = Date.now()
  mainWindow.setOpacity(0)
  mainWindow.show()
  if (focus) mainWindow.focus()
  windowFadeTimer = setInterval(() => {
    if (!mainWindow || mainWindow.isDestroyed()) {
      cancelWindowFade()
      return
    }
    const progress = Math.min(1, (Date.now() - startedAt) / durationMs)
    mainWindow.setOpacity(progress)
    if (progress >= 1) {
      mainWindow.setOpacity(1)
      cancelWindowFade()
    }
  }, 16)
}

function showMainWindow() {
  if (!mainWindow) {
    createWindow()
  }
  if (!mainWindow) return
  showWindowWithFade(true)
}

function quitApp() {
  isQuitting = true
  app.quit()
}

function defaultPetWindowBounds(): DesktopWindowBounds {
  const { workArea } = screen.getPrimaryDisplay()
  return {
    x: Math.round(workArea.x + workArea.width - PET_WINDOW_DEFAULT_WIDTH - 28),
    y: Math.round(workArea.y + workArea.height - PET_WINDOW_DEFAULT_HEIGHT - 28),
    width: PET_WINDOW_DEFAULT_WIDTH,
    height: PET_WINDOW_DEFAULT_HEIGHT,
  }
}

function petWindowState() {
  const target = petWindow && !petWindow.isDestroyed() ? petWindow : null
  return {
    bounds: target?.getBounds() || defaultPetWindowBounds(),
    visible: !!target?.isVisible(),
  }
}

function sanitizePetWindowBounds(input: unknown): DesktopWindowBounds | null {
  if (!input || typeof input !== 'object') return null
  const value = input as Partial<DesktopWindowBounds>
  const x = Number(value.x)
  const y = Number(value.y)
  const width = Number(value.width)
  const height = Number(value.height)
  if (![x, y, width, height].every(Number.isFinite)) return null
  return {
    x: Math.round(x),
    y: Math.round(y),
    width: Math.round(Math.min(PET_WINDOW_MAX_SIZE, Math.max(PET_WINDOW_MIN_SIZE, width))),
    height: Math.round(Math.min(PET_WINDOW_MAX_SIZE, Math.max(PET_WINDOW_MIN_SIZE, height))),
  }
}

function petRouteUrl(): string | null {
  if (!serverUrl) return null
  return `${serverUrl.replace(/#.*$/, '').replace(/\/$/, '')}/#/desktop-pet`
}

function ensurePetWindow(): BrowserWindow {
  if (petWindow && !petWindow.isDestroyed()) return petWindow

  petWindow = new BrowserWindow({
    ...defaultPetWindowBounds(),
    title: 'DeepAgent Pet',
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    hasShadow: false,
    ...(process.platform === 'darwin' ? { roundedCorners: false } : {}),
    ...(process.platform === 'win32' ? { thickFrame: false } : {}),
    resizable: false,
    maximizable: false,
    minimizable: false,
    fullscreenable: false,
    skipTaskbar: true,
    show: false,
    acceptFirstMouse: true,
    autoHideMenuBar: true,
    alwaysOnTop: true,
    webPreferences: {
      preload: join(__dirname, '..', 'preload', 'index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      additionalArguments: ['--hermes-window-kind=pet'],
    },
  })
  petWindow.setBackgroundColor('#00000000')
  petWindow.setHasShadow(false)
  petWindow.setAlwaysOnTop(true, process.platform === 'darwin' ? 'floating' : 'normal')
  if (process.platform === 'darwin') {
    petWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: false })
  }
  petWindow.on('closed', () => {
    petWindow = null
    petWindowLoadPromise = null
  })
  petWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https://') || url.startsWith('http://')) {
      shell.openExternal(url).catch(() => undefined)
    }
    return { action: 'deny' }
  })
  return petWindow
}

async function loadPetWindowRoute(): Promise<void> {
  const url = petRouteUrl()
  if (!url) return
  const target = ensurePetWindow()
  if (target.webContents.getURL() === url) return
  if (!petWindowLoadPromise) {
    petWindowLoadPromise = target.loadURL(url)
      .catch(err => {
        console.warn('[desktop-pet] failed to load pet window:', err)
      })
      .finally(() => {
        petWindowLoadPromise = null
      })
  }
  await petWindowLoadPromise
}

function windowState() {
  return {
    isMaximized: !!mainWindow?.isMaximized(),
  }
}

function handleWindowControl(action: WindowControlAction) {
  if (!mainWindow || mainWindow.isDestroyed()) return windowState()
  if (action === 'minimize') {
    mainWindow.minimize()
  } else if (action === 'toggle-maximize') {
    if (mainWindow.isMaximized()) mainWindow.unmaximize()
    else mainWindow.maximize()
  } else if (action === 'close') {
    mainWindow.close()
  }
  return windowState()
}

function hasQuitRequest(data: unknown): boolean {
  return typeof data === 'object'
    && data !== null
    && (data as { quit?: unknown }).quit === true
}

function loginItemOptions() {
  return {
    path: process.execPath,
    args: ['--hidden'],
  }
}

function getOpenAtLogin(): boolean {
  return app.getLoginItemSettings(loginItemOptions()).openAtLogin
}

function setOpenAtLogin(openAtLogin: boolean) {
  app.setLoginItemSettings({
    ...loginItemOptions(),
    openAtLogin,
    openAsHidden: true,
  })
}

function updateTrayMenu() {
  if (!tray) return
  const isVisible = !!mainWindow && mainWindow.isVisible()
  const menu = Menu.buildFromTemplate([
    {
      label: isVisible ? t('tray.hide') : t('tray.show'),
      click: () => {
        if (mainWindow?.isVisible()) {
          mainWindow.hide()
        } else {
          showMainWindow()
        }
        updateTrayMenu()
      },
    },
    {
      label: t('tray.checkForUpdates'),
      click: () => {
        checkForDesktopUpdates(true).catch(err => {
          console.error('[tray] update check failed:', err)
        })
      },
    },
    {
      label: t('tray.openAtLogin'),
      type: 'checkbox',
      checked: getOpenAtLogin(),
      click: (item) => {
        setOpenAtLogin(item.checked)
        updateTrayMenu()
      },
    },
    { type: 'separator' },
    {
      label: t('tray.quit'),
      click: quitApp,
    },
  ])
  tray.setContextMenu(menu)
}

function createTray() {
  if (tray) return
  const source = process.platform === 'darwin'
    ? desktopTrayTemplateIcon()
    : process.platform === 'win32'
      ? desktopWindowsTrayIcon()
      : desktopIcon()
  const icon = nativeImage.createFromPath(source).resize({
    width: process.platform === 'darwin' ? 18 : process.platform === 'win32' ? 24 : 16,
    height: process.platform === 'darwin' ? 18 : process.platform === 'win32' ? 24 : 16,
    quality: 'best',
  })
  if (process.platform === 'darwin') {
    icon.setTemplateImage(true)
  }
  tray = new Tray(icon)
  tray.setToolTip('DeepAgent')
  tray.on('click', () => {
    showMainWindow()
    updateTrayMenu()
  })
  updateTrayMenu()
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 960,
    minHeight: 600,
    title: 'DeepAgent',
    backgroundColor: '#1a1a1a',
    autoHideMenuBar: true,
    show: false,
    ...(process.platform === 'darwin'
      ? {
          titleBarStyle: 'hiddenInset' as const,
          trafficLightPosition: { x: 16, y: 12 },
        }
      : process.platform === 'win32'
        ? {
            frame: false,
          }
        : {}),
    ...(process.platform === 'linux' ? { icon: desktopIcon() } : {}),
    webPreferences: {
      preload: join(__dirname, '..', 'preload', 'index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  })

  mainWindow.once('ready-to-show', () => {
    if (!START_HIDDEN) showWindowWithFade(true)
  })

  mainWindow.on('close', (event) => {
    if (isQuitting) return
    event.preventDefault()
    cancelWindowFade()
    mainWindow?.hide()
    updateTrayMenu()
  })

  mainWindow.on('show', updateTrayMenu)
  mainWindow.on('hide', updateTrayMenu)

  // External links → system browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https://') || url.startsWith('http://')) {
      shell.openExternal(url).catch(() => undefined)
    }
    return { action: 'deny' }
  })

  // If the Web UI server is already up (re-opening window after close on
  // macOS), go straight to it. Otherwise show a loading splash; bootstrap()
  // will swap in the real URL once the server is ready.
  if (serverUrl) {
    mainWindow.loadURL(serverUrl)
  } else {
    mainWindow.loadURL(splashHtml(t('runtime.checking')))
  }
  updateTrayMenu()
}

function splashHtml(label = t('desktop.startingLocalServices')): string {
  const startingLabel = escapeHtml(label)
  const html = `<!doctype html><html><head><meta charset="utf-8"><title>DeepAgent</title>
<style>
  html,body{margin:0;height:100%;background:#1a1a1a;color:#e5e5e5;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;-webkit-app-region:drag;}
  .wrap{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:20px}
  .dot{width:10px;height:10px;border-radius:50%;background:#888;animation:pulse 1.2s ease-in-out infinite}
  @keyframes pulse{0%,100%{opacity:.3}50%{opacity:1}}
  .row{display:flex;gap:8px}
  .row .dot:nth-child(2){animation-delay:.2s}.row .dot:nth-child(3){animation-delay:.4s}
  .label{font-size:14px;color:#b8b8b8}
  .detail{min-height:18px;font-size:12px;color:#7f7f7f}
  .progress{width:320px;height:6px;border-radius:999px;background:#2b2b2b;overflow:hidden}
  .bar{width:0;height:100%;background:#d8d8d8;transition:width .18s ease}
  h1{font-weight:500;margin:0;font-size:18px}
</style></head><body><div class="wrap">
<h1>DeepAgent</h1>
<div class="row"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
<div id="label" class="label">${startingLabel}</div>
<div class="progress"><div id="bar" class="bar"></div></div>
<div id="detail" class="detail"></div>
</div></body></html>`
  return 'data:text/html;charset=utf-8,' + encodeURIComponent(html)
}

async function showShutdownSplash() {
  if (!mainWindow || mainWindow.isDestroyed()) return
  cancelWindowFade()
  try {
    await mainWindow.loadURL(splashHtml(t('desktop.shuttingDown')))
    if (mainWindow.isMinimized()) mainWindow.restore()
    mainWindow.setOpacity(1)
    mainWindow.show()
    updateTrayMenu()
  } catch {
    /* best effort during app shutdown */
  }
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char] || char))
}

async function ensureRuntimeTaskSupervisor(): Promise<RuntimeTaskSupervisorEnvironment> {
  if (!runtimeTaskSupervisor) {
    runtimeTaskSupervisor = new RuntimeTaskSupervisor({
      stateDir: join(webUiHome(), 'runtime', 'task-supervisor'),
    })
  }
  if (!runtimeTaskSupervisorEnvironment) {
    runtimeTaskSupervisorEnvironment = await runtimeTaskSupervisor.start()
  }
  return runtimeTaskSupervisorEnvironment
}

async function bootstrap() {
  if (isBootstrapping) return
  isBootstrapping = true

  try {
    const supervisorEnvironment = await ensureRuntimeTaskSupervisor()
    const url = await startWebUiServer(PORT, supervisorEnvironment)
    serverUrl = url
    if (mainWindow) await mainWindow.loadURL(createDesktopLoginUrl(url, deepAgentHome()))
    await loadPetWindowRoute()
  } catch (err) {
    console.error('Failed to start Web UI server:', err)
    if (mainWindow) {
      const msg = escapeHtml(String(err instanceof Error ? err.message : err))
      mainWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(
        `<html><body style="font-family:system-ui;padding:32px;background:#1a1a1a;color:#eee">
         <h2>${escapeHtml(t('desktop.failedStartServices'))}</h2><pre style="white-space:pre-wrap;color:#f88">${msg}</pre>
         </body></html>`,
      ))
    }
  } finally {
    isBootstrapping = false
  }
}

ipcMain.handle('hermes-desktop:get-window-state', () => windowState())
ipcMain.handle('hermes-desktop:window-control', (_event, action?: unknown) => {
  if (action !== 'minimize' && action !== 'toggle-maximize' && action !== 'close') return windowState()
  return handleWindowControl(action)
})
ipcMain.handle('hermes-desktop:get-pet-window-state', () => petWindowState())
ipcMain.handle('hermes-desktop:set-pet-window-bounds', (_event, bounds?: unknown) => {
  const nextBounds = sanitizePetWindowBounds(bounds)
  if (!nextBounds) return petWindowState()
  const target = ensurePetWindow()
  target.setBounds(nextBounds, false)
  return petWindowState()
})
ipcMain.handle('hermes-desktop:set-pet-window-visible', async (_event, visible?: unknown) => {
  if (visible === false) {
    if (!petWindow || petWindow.isDestroyed()) return petWindowState()
    petWindow.hide()
    return petWindowState()
  }
  await loadPetWindowRoute()
  const target = ensurePetWindow()
  target.showInactive()
  return petWindowState()
})
function resolveNotificationIcon(icon: unknown): string {
  if (typeof icon !== 'string') return desktopIcon()
  const normalized = icon.trim().replace(/^\/+/, '')
  if (!normalized || normalized.includes('..')) return desktopIcon()

  const candidates = [
    join(webuiDir(), 'dist', 'client', normalized),
    join(webuiDir(), 'dist', normalized),
    join(webuiDir(), 'packages', 'client', 'public', normalized),
    join(webuiDir(), normalized),
  ]
  return candidates.find(candidate => existsSync(candidate)) || desktopIcon()
}

ipcMain.handle('hermes-desktop:notify-completion', (_event, payload?: { title?: unknown; body?: unknown; icon?: unknown; tag?: unknown }) => {
  const supported = Notification.isSupported()
  if (!supported) {
    console.warn('[desktop-notification] Electron notifications are not supported on this system')
    return false
  }

  const title = typeof payload?.title === 'string' && payload.title.trim()
    ? payload.title.trim()
    : 'DeepAgent'
  const body = typeof payload?.body === 'string' ? payload.body.trim().slice(0, 240) : ''
  const icon = resolveNotificationIcon(payload?.icon)
  const notification = new Notification({
    title,
    body,
    icon,
    silent: false,
  })
  activeNotifications.add(notification)
  const releaseNotification = () => {
    activeNotifications.delete(notification)
  }
  notification.on('click', () => {
    releaseNotification()
    showMainWindow()
  })
  notification.on('close', releaseNotification)
  notification.on('failed', (_event, error) => {
    console.warn('[desktop-notification] notification failed', error)
    releaseNotification()
  })
  notification.show()
  return true
})
ipcMain.handle('hermes-desktop:retry-bootstrap', async () => {
  if (serverUrl) {
    await mainWindow?.loadURL(serverUrl)
    return
  }
  await mainWindow?.loadURL(splashHtml(t('runtime.downloading')))
  await bootstrap()
})

// ─── 双模式 IPC（Stage 9） ───────────────────────────────────────────
/** 向所有 BrowserWindow 广播模式变更事件 */
function broadcastMode(mode: AppMode): void {
  for (const win of BrowserWindow.getAllWindows()) {
    if (!win.isDestroyed()) win.webContents.send('hermes-desktop:mode-changed', mode)
  }
}
ipcMain.handle('hermes-desktop:get-mode', () => modeManager?.getMode() ?? 'assistant')
ipcMain.handle('hermes-desktop:set-mode', async (_event, mode?: unknown) => {
  if (!modeManager) return
  if (mode !== 'assistant' && mode !== 'code') return
  await modeManager.setMode(mode)
})
ipcMain.handle('hermes-desktop:start-code-mode', async (_event, config?: unknown): Promise<StartCodeModeResult> => {
  if (!modeManager) return { ok: false, error: 'not-ready' }
  return modeManager.startCodeMode((config as SharedConfig) ?? { model: '', provider: '' })
})
ipcMain.handle('hermes-desktop:stop-code-mode', async () => {
  await modeManager?.stopCodeMode()
})
ipcMain.handle('deepagent:credential:set', (_event, provider?: unknown, value?: unknown) => {
  if (!credentialVault || typeof provider !== 'string' || typeof value !== 'string') return { ok: false }
  credentialVault.set(provider, value)
  return { ok: true }
})
ipcMain.handle('deepagent:credential:has', (_event, provider?: unknown) => (
  Boolean(credentialVault && typeof provider === 'string' && credentialVault.has(provider))
))
ipcMain.handle('deepagent:credential:delete', (_event, provider?: unknown) => {
  if (credentialVault && typeof provider === 'string') credentialVault.delete(provider)
  return { ok: true }
})
registerWorkspaceLockIpc(ipcMain)

function runDesktopApp() {
  const gotLock = app.requestSingleInstanceLock(QUIT_EXISTING ? { quit: true } : undefined)
  if (!gotLock) {
    app.quit()
    return
  }

  app.on('second-instance', (_event, argv, _workingDirectory, additionalData) => {
    if (argv.includes('--quit') || hasQuitRequest(additionalData)) {
      quitApp()
      return
    }
    showMainWindow()
  })

  app.whenReady().then(() => {
    runPhase3Migration(deepAgentHome(), {
      legacyWebUiHome: join(homedir(), '.hermes-web-ui'),
      legacyDesktopHome: join(homedir(), 'Library', 'Application Support', 'Hermes Studio'),
    })
    credentialVault = new CredentialVault(deepAgentHome(), safeStorage)
    if (QUIT_EXISTING) {
      quitApp()
      return
    }

    // Drop the default File/Edit/View/Window menu on Windows/Linux. The web
    // UI provides its own in-page controls, so the native menu bar is just
    // visual clutter. macOS keeps a menu (system requirement) but Electron's
    // default is fine there.
    if (process.platform !== 'darwin') Menu.setApplicationMenu(null)
    createTray()
    createWindow()
    // 双模式管理器：注册 IPC，其 broadcast 推送到所有窗口
    modeManager = new ModeManager({
      productHome: deepAgentHome(),
      broadcast: broadcastMode,
      resolveCredentials: provider => Promise.resolve(credentialVault?.environmentFor(provider) ?? {}),
    })
    bootstrap()
    initAutoUpdater({
      beforeQuitAndInstall: () => {
        isQuitting = true
      },
    })
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow()
      } else if (mainWindow) {
        showMainWindow()
      }
    })
  })

  app.on('window-all-closed', () => {
    if (isQuitting && process.platform !== 'darwin') app.quit()
  })

  app.on('before-quit', async (e) => {
    if (!isQuitting && process.platform !== 'darwin') {
      e.preventDefault()
      mainWindow?.hide()
      updateTrayMenu()
      return
    }
    e.preventDefault()
    cancelWindowFade()
    await showShutdownSplash()
    await stopWebUiServer().catch(() => undefined)
    await runtimeTaskSupervisor?.stop().catch(() => undefined)
    runtimeTaskSupervisor = null
    runtimeTaskSupervisorEnvironment = null
    app.exit(0)
  })
}

runDesktopApp()
