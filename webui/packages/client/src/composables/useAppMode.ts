/**
 * useAppMode — 双模式状态 composable
 *
 * 维护当前应用模式（assistant | code），同步到 localStorage 与 Electron 主进程，
 * 并订阅主进程广播以支持外部触发（托盘菜单/deep link）。
 */
import { ref, readonly } from 'vue'
import { desktopBridge, type HermesDesktopBridge } from '@/utils/desktop-bridge'
import { APP_MODE_STORAGE_KEY, readStoredMode, writeStoredMode, type AppMode } from '@/utils/mode-config'

/** 当前模式（内部可变 ref） */
const modeRef = ref<AppMode>('assistant')

/** 是否已完成初始化（从主进程拉取过一次） */
let initialized = false

/** 订阅者集合 */
const listeners = new Set<(mode: AppMode) => void>()

function notify(mode: AppMode): void {
  for (const fn of listeners) fn(mode)
}

/** 从 localStorage 初始化（同步），再异步与主进程对齐 */
function init(): void {
  if (initialized) return
  initialized = true
  modeRef.value = readStoredMode()
  const bridge = desktopBridge()
  if (bridge?.isDesktop && typeof bridge.getMode === 'function') {
    bridge.getMode().then(m => {
      if (m === 'assistant' || m === 'code') {
        modeRef.value = m
        writeStoredMode(m)
        notify(m)
      }
    }).catch(() => { /* ignore */ })
    if (typeof bridge.onModeChanged === 'function') {
      bridge.onModeChanged((m: AppMode) => {
        if (m !== 'assistant' && m !== 'code') return
        modeRef.value = m
        writeStoredMode(m)
        notify(m)
      })
    }
  }
}

/**
 * 设置当前模式。
 * 同步更新 ref、localStorage，并通过 IPC 通知主进程。
 */
async function setMode(mode: AppMode): Promise<void> {
  if (mode !== 'assistant' && mode !== 'code') return
  if (modeRef.value === mode) return
  modeRef.value = mode
  writeStoredMode(mode)
  notify(mode)
  const bridge = desktopBridge()
  if (bridge?.isDesktop && typeof bridge.setMode === 'function') {
    try { await bridge.setMode(mode) } catch { /* ignore */ }
  }
}

/** 订阅模式变化（返回取消订阅函数） */
function subscribe(fn: (mode: AppMode) => void): () => void {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

/**
 * useAppMode — 在组件 setup 中使用。
 * 自动确保初始化（在 client 端调用一次）。
 */
export function useAppMode(_bridge?: HermesDesktopBridge) {
  init()
  return {
    mode: readonly(modeRef),
    setMode,
    subscribe,
    isAssistant: () => modeRef.value === 'assistant',
    isCode: () => modeRef.value === 'code',
  }
}

/** 导出内部 ref 便于测试重置 */
export function _resetAppModeForTests(): void {
  modeRef.value = 'assistant'
  initialized = false
  listeners.clear()
  try { localStorage.removeItem(APP_MODE_STORAGE_KEY) } catch { /* */ }
}
