/**
 * Deep Agent — Electron Main Process
 *
 * A lightweight desktop wrapper for the Deep Agent WebUI.
 * Loads the pre-built dist/client/index.html directly.
 *
 * Usage:
 *   npx electron webui/electron/main.js
 *
 * Build:
 *   npm run build:electron   (from webui/)
 *   scripts/package-electron.sh
 */

const { app, BrowserWindow, Menu, shell } = require('electron')
const path = require('path')

// ---- Constants ----
const IS_MAC = process.platform === 'darwin'
const IS_DEV = !app.isPackaged
const WINDOW_TITLE = 'Deep Agent'
const WINDOW_WIDTH = 1280
const WINDOW_HEIGHT = 800
const MIN_WIDTH = 960
const MIN_HEIGHT = 600

// ---- Resolve the path to the built web client ----
function resolveDistIndex() {
  // In dev mode, __dirname is webui/electron/; dist is at webui/dist/
  // In packaged mode (electron-builder), the app.asar contains
  // electron/main.js and extraResources places dist/ alongside.
  if (IS_DEV) {
    // When running `npx electron webui/electron/main.js` from webui/
    return path.join(__dirname, '..', 'dist', 'client', 'index.html')
  }
  // Packaged — electron-builder config below copies dist/ into extraResources
  return path.join(process.resourcesPath, 'dist', 'client', 'index.html')
}

// ---- Build the application menu ----
function buildMenu() {
  const template = [
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
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        { type: 'separator' },
        ...(IS_MAC
          ? [{ role: 'front' }, { type: 'separator' }, { role: 'window' }]
          : [{ role: 'close' }]),
      ],
    },
  ]

  const menu = Menu.buildFromTemplate(template)
  Menu.setApplicationMenu(menu)
}

// ---- Create the main browser window ----
let mainWindow = null

function createWindow() {
  mainWindow = new BrowserWindow({
    width: WINDOW_WIDTH,
    height: WINDOW_HEIGHT,
    minWidth: MIN_WIDTH,
    minHeight: MIN_HEIGHT,
    title: WINDOW_TITLE,
    backgroundColor: '#1a1a1a',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  })

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
  })

  // Open external links in the system browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('file://') || url.startsWith('http://127.0.0.1') || url.startsWith('http://localhost')) {
      return { action: 'allow' }
    }
    shell.openExternal(url).catch(() => {})
    return { action: 'deny' }
  })

  // Load the built web client
  const indexPath = resolveDistIndex()
  mainWindow.loadFile(indexPath).catch((err) => {
    console.error('[electron] Failed to load index.html:', err)
    mainWindow.loadURL(
      `data:text/html;charset=utf-8,<h1>Error Loading Deep Agent</h1><p>${encodeURIComponent(err.message)}</p>`
    )
  })
}

// ---- App lifecycle ----
app.whenReady().then(() => {
  buildMenu()
  createWindow()

  app.on('activate', () => {
    // macOS: re-create window when dock icon is clicked
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (!IS_MAC) {
    app.quit()
  }
})
