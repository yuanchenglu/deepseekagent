/**
 * Deep Agent — Electron Preload Script
 *
 * Bridges a minimal set of Electron APIs to the renderer process safely
 * via contextBridge. The renderer can access `window.deepAgentDesktop`.
 */

const { contextBridge } = require('electron')

contextBridge.exposeInMainWorld('deepAgentDesktop', {
  /** Platform identifier: 'darwin', 'win32', 'linux' */
  platform: process.platform,
  /** Always true so the web app knows it's running inside Electron */
  isDesktop: true,
  /** Electron app version */
  appVersion: process.env.npm_package_version || '',
})
