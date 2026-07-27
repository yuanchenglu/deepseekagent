/**
 * mode-config.ts — 双模式配置共享模块
 *
 * 负责把助理模式当前选中的模型/Provider/API Key/baseUrl/profile 聚合成
 * 一份可序列化的纯对象，供 Code 模式启动 OpenCode 时注入使用。
 *
 * 设计原则：
 *  - 纯函数，无副作用（桌面下的 applyToOpenCode 除外）
 *  - 所有 localStorage 访问包裹在 try/catch，SSR 或异常环境不崩
 *  - 不直接依赖 Pinia store，避免耦合；调用方从 appStore 取值传入
 */

import { desktopBridge, type HermesDesktopBridge, type SharedConfig } from './desktop-bridge'
export type { SharedConfig } from './desktop-bridge'

/** 模式切换持久化键 */
export const APP_MODE_STORAGE_KEY = 'hermes_app_mode'

/** 应用模式类型 */
export type AppMode = 'assistant' | 'code'

/**
 * 共享配置 —— 两种模式间共享的连接信息
 */
/** 空配置常量，用于降级/初始状态 */
export const EMPTY_SHARED_CONFIG: SharedConfig = {
  model: '',
  provider: '',
  baseUrl: undefined,
  profile: undefined,
}

/** 从 localStorage 安全读取字符串 */
function safeGetItem(key: string): string {
  try {
    if (typeof localStorage === 'undefined') return ''
    return localStorage.getItem(key) || ''
  } catch {
    return ''
  }
}

/**
 * 从 localStorage + 传入的 appStore 状态聚合共享配置。
 *
 * @param appState  助理模式当前选择（model/provider），由调用方传入
 * @returns         可序列化的 SharedConfig
 */
export function getSharedConfig(appState?: {
  selectedModel?: string
  selectedProvider?: string
}): SharedConfig {
  const baseUrl = safeGetItem('hermes_server_url') || undefined
  const profile = safeGetItem('hermes_active_profile_name') || undefined
  const model = appState?.selectedModel || safeGetItem('hermes_selected_model') || ''
  const provider = appState?.selectedProvider || safeGetItem('hermes_selected_provider') || ''
  return { model, provider, baseUrl, profile }
}

/**
 * 把共享配置应用到 OpenCode 运行时。
 *
 * - 桌面环境：通过 IPC 调用主进程 spawn opencode serve 并注入 env
 * - 浏览器环境：no-op（返回 { ok:false, error: 'desktop-only' }）
 *
 * @param config   要注入的共享配置
 * @param bridge   可选的 desktop bridge 注入点（测试用）
 */
export async function applyToOpenCode(
  config: SharedConfig,
  bridge?: HermesDesktopBridge,
): Promise<{ ok: true; url: string } | { ok: false; error: string }> {
  const b = bridge ?? desktopBridge()
  if (!b?.isDesktop || typeof b.startCodeMode !== 'function') {
    return { ok: false, error: 'desktop-only' }
  }
  try {
    return await b.startCodeMode(config)
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}

/**
 * 从 localStorage 读取当前模式（不触发 IPC）。
 * 仅用于首屏渲染时初始值。
 */
export function readStoredMode(): AppMode {
  const stored = safeGetItem(APP_MODE_STORAGE_KEY)
  return stored === 'code' ? 'code' : 'assistant'
}

/**
 * 写入模式到 localStorage。供 useAppMode 使用。
 */
export function writeStoredMode(mode: AppMode): void {
  try {
    if (typeof localStorage === 'undefined') return
    localStorage.setItem(APP_MODE_STORAGE_KEY, mode)
  } catch {
    /* ignore */
  }
}
