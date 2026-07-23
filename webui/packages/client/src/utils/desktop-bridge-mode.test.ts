// desktop-bridge types include new mode APIs
// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest'
import { desktopBridge, type HermesDesktopBridge, type SharedConfig } from './desktop-bridge'

afterEach(() => {
  delete (window as any).hermesDesktop
})

describe('desktopBridge', () => {
  it('returns undefined when hermesDesktop is not on window', () => {
    expect(desktopBridge()).toBeUndefined()
  })

  it('returns the bridge object when present', () => {
    const fake: HermesDesktopBridge = {
      isDesktop: true,
      platform: 'linux',
      getToken: async () => '',
      retryBootstrap: async () => {},
      notifyCompletion: async () => false,
      getWindowState: async () => ({ isMaximized: false }),
      windowControl: async () => ({ isMaximized: false }),
    }
    Object.defineProperty(window, 'hermesDesktop', { configurable: true, value: fake })
    expect(desktopBridge()?.isDesktop).toBe(true)
  })

  it('types allow optional mode APIs', () => {
    const bridge: HermesDesktopBridge = {
      isDesktop: true,
      platform: 'linux',
      getToken: async () => '',
      retryBootstrap: async () => {},
      notifyCompletion: async () => false,
      getWindowState: async () => ({ isMaximized: false }),
      windowControl: async () => ({ isMaximized: false }),
      getMode: async () => 'assistant',
      setMode: async () => {},
      onModeChanged: () => () => {},
      startCodeMode: async (_c: SharedConfig) => ({ ok: true, url: 'http://x' }),
      stopCodeMode: async () => {},
    }
    expect(bridge.getMode).toBeDefined()
    expect(bridge.startCodeMode).toBeDefined()
  })
})
