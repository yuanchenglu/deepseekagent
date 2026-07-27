import { contextBridge, ipcRenderer } from 'electron'

type DesktopWindowKind = 'main' | 'pet'

function desktopWindowKind(): DesktopWindowKind {
  const arg = process.argv.find(item => item.startsWith('--hermes-window-kind='))
  return arg?.slice('--hermes-window-kind='.length) === 'pet' ? 'pet' : 'main'
}

contextBridge.exposeInMainWorld('hermesDesktop', {
  retryBootstrap: (source?: 'cf' | 'github'): Promise<void> => ipcRenderer.invoke('hermes-desktop:retry-bootstrap', source),
  notifyCompletion: (payload: { title: string; body?: string; icon?: string; tag?: string }): Promise<boolean> => ipcRenderer.invoke('hermes-desktop:notify-completion', payload),
  ensureAuth: async (): Promise<boolean> => {
    localStorage.removeItem('hermes_api_key')
    return Boolean(sessionStorage.getItem('deepagent_cookie_session'))
  },
  getWindowState: (): Promise<{ isMaximized: boolean }> => ipcRenderer.invoke('hermes-desktop:get-window-state'),
  windowControl: (action: 'minimize' | 'toggle-maximize' | 'close'): Promise<{ isMaximized: boolean }> => ipcRenderer.invoke('hermes-desktop:window-control', action),
  getPetWindowState: () => ipcRenderer.invoke('hermes-desktop:get-pet-window-state'),
  setPetWindowBounds: (bounds: { x: number; y: number; width: number; height: number }) => ipcRenderer.invoke('hermes-desktop:set-pet-window-bounds', bounds),
  setPetWindowVisible: (visible: boolean) => ipcRenderer.invoke('hermes-desktop:set-pet-window-visible', visible),
  getMode: (): Promise<'assistant' | 'code'> => ipcRenderer.invoke('hermes-desktop:get-mode'),
  setMode: (mode: 'assistant' | 'code'): Promise<void> => ipcRenderer.invoke('hermes-desktop:set-mode', mode),
  onModeChanged: (callback: (mode: 'assistant' | 'code') => void): (() => void) => {
    const listener = (_event: Electron.IpcRendererEvent, mode: 'assistant' | 'code') => callback(mode)
    ipcRenderer.on('hermes-desktop:mode-changed', listener)
    return () => ipcRenderer.removeListener('hermes-desktop:mode-changed', listener)
  },
  startCodeMode: (config: { model: string; provider: string; baseUrl?: string; profile?: string }) =>
    ipcRenderer.invoke('hermes-desktop:start-code-mode', config),
  stopCodeMode: (): Promise<void> => ipcRenderer.invoke('hermes-desktop:stop-code-mode'),
  setProviderCredential: (provider: string, value: string) => ipcRenderer.invoke('deepagent:credential:set', provider, value),
  hasProviderCredential: (provider: string): Promise<boolean> => ipcRenderer.invoke('deepagent:credential:has', provider),
  deleteProviderCredential: (provider: string) => ipcRenderer.invoke('deepagent:credential:delete', provider),
  acquireWorkspaceLock: (workspace: string, taskId: string, access: 'read' | 'write'): Promise<boolean> =>
    ipcRenderer.invoke('deepagent:workspace-lock:acquire', workspace, taskId, access),
  releaseWorkspaceLock: (workspace: string, taskId: string): Promise<void> =>
    ipcRenderer.invoke('deepagent:workspace-lock:release', workspace, taskId),
  releaseTaskLocks: (taskId: string): Promise<void> =>
    ipcRenderer.invoke('deepagent:workspace-lock:release-task', taskId),
  platform: process.platform,
  isDesktop: true,
  windowKind: desktopWindowKind(),
})
