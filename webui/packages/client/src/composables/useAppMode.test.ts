// useAppMode 单元测试
// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { _resetAppModeForTests, useAppMode } from './useAppMode'

const LS: Record<string, string> = {}

beforeEach(() => {
  Object.keys(LS).forEach(k => delete LS[k])
  vi.stubGlobal('localStorage', {
    getItem: vi.fn((k: string) => LS[k] ?? null),
    setItem: vi.fn((k: string, v: string) => { LS[k] = String(v) }),
    removeItem: vi.fn((k: string) => { delete LS[k] }),
    clear: vi.fn(),
    get length() { return Object.keys(LS).length },
    key: vi.fn(),
  })
})

afterEach(() => {
  _resetAppModeForTests()
  vi.unstubAllGlobals()
})

function mockBridge(overrides: Record<string, unknown> = {}) {
  const onModeChanged = vi.fn((cb: (m: string) => void) => {
    ;(mockBridge as any)._cb = cb
    return () => { (mockBridge as any)._cb = null }
  })
  const bridge = {
    isDesktop: true,
    platform: 'linux',
    getMode: vi.fn().mockResolvedValue('assistant'),
    setMode: vi.fn().mockResolvedValue(undefined),
    onModeChanged,
    ...overrides,
  }
  return bridge
}

describe('useAppMode', () => {
  it('defaults to assistant mode', () => {
    const { mode } = useAppMode()
    expect(mode.value).toBe('assistant')
  })

  it('reads code from localStorage on init', () => {
    LS['hermes_app_mode'] = 'code'
    const { mode } = useAppMode()
    expect(mode.value).toBe('code')
  })

  it('setMode updates ref and localStorage', async () => {
    const bridge = mockBridge()
    vi.stubGlobal('window', { hermesDesktop: bridge })
    const { mode, setMode } = useAppMode()
    await setMode('code')
    expect(mode.value).toBe('code')
    expect(LS['hermes_app_mode']).toBe('code')
  })

  it('setMode calls bridge.setMode on desktop', async () => {
    const bridge = mockBridge()
    vi.stubGlobal('window', { hermesDesktop: bridge })
    const { setMode } = useAppMode()
    await setMode('code')
    expect(bridge.setMode).toHaveBeenCalledWith('code')
  })

  it('ignores invalid mode values', async () => {
    const { mode, setMode } = useAppMode()
    await setMode('invalid' as any)
    expect(mode.value).toBe('assistant')
  })

  it('subscribe receives updates on setMode', async () => {
    const fn = vi.fn()
    const { subscribe, setMode } = useAppMode()
    subscribe(fn)
    await setMode('code')
    expect(fn).toHaveBeenCalledWith('code')
  })

  it('isAssistant/isCode helpers work', async () => {
    const { isAssistant, isCode, setMode } = useAppMode()
    expect(isAssistant()).toBe(true)
    expect(isCode()).toBe(false)
    await setMode('code')
    expect(isCode()).toBe(true)
  })
})
