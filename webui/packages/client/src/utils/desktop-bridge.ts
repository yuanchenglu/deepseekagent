export interface DesktopWindowBounds {
  x: number
  y: number
  width: number
  height: number
}

export interface DesktopPetWindowState {
  bounds: DesktopWindowBounds
  visible: boolean
}

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

export interface HermesDesktopBridge {
  ensureAuth?: () => Promise<boolean>
  retryBootstrap: (source?: 'cf' | 'github') => Promise<void>
  notifyCompletion: (payload: { title: string; body?: string; icon?: string; tag?: string }) => Promise<boolean>
  getWindowState: () => Promise<{ isMaximized: boolean }>
  windowControl: (action: 'minimize' | 'toggle-maximize' | 'close') => Promise<{ isMaximized: boolean }>
  getPetWindowState?: () => Promise<DesktopPetWindowState>
  setPetWindowBounds?: (bounds: DesktopWindowBounds) => Promise<DesktopPetWindowState>
  setPetWindowVisible?: (visible: boolean) => Promise<DesktopPetWindowState>
  getMode?: () => Promise<AppMode>
  setMode?: (mode: AppMode) => Promise<void>
  onModeChanged?: (callback: (mode: AppMode) => void) => () => void
  startCodeMode?: (config: SharedConfig) => Promise<StartCodeModeResult>
  stopCodeMode?: () => Promise<void>
  setProviderCredential?: (provider: string, value: string) => Promise<{ ok: boolean }>
  hasProviderCredential?: (provider: string) => Promise<boolean>
  deleteProviderCredential?: (provider: string) => Promise<{ ok: boolean }>
    acquireWorkspaceLock?: (workspace: string, taskId: string, access: 'read' | 'write') => Promise<boolean>
    releaseWorkspaceLock?: (workspace: string, taskId: string) => Promise<void>
    releaseTaskLocks?: (taskId: string) => Promise<void>
  platform: string
  isDesktop: boolean
  windowKind?: 'main' | 'pet'
}

export type { SharedConfig as DesktopSharedConfig }

export type WindowWithHermesDesktop = Window & typeof globalThis & {
  hermesDesktop?: HermesDesktopBridge
}

export function desktopBridge(): HermesDesktopBridge | undefined {
  return (window as WindowWithHermesDesktop).hermesDesktop
}

export function isDesktopShell(): boolean {
  return desktopBridge()?.isDesktop === true
}

export function isDesktopPetWindow(): boolean {
  return desktopBridge()?.windowKind === 'pet'
}
