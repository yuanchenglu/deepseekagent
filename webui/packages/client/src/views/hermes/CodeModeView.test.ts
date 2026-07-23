// CodeModeView.vue 单元测试
// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import CodeModeView from './CodeModeView.vue'

const LS: Record<string, string> = {}

beforeEach(() => {
  Object.keys(LS).forEach(k => delete LS[k])
  LS['hermes_api_key'] = 'sk-test'
  LS['hermes_selected_model'] = 'test-model'
  LS['hermes_selected_provider'] = 'test-provider'
  vi.stubGlobal('localStorage', {
    getItem: vi.fn((k: string) => LS[k] ?? null),
    setItem: vi.fn((k: string, v: string) => { LS[k] = String(v) }),
    removeItem: vi.fn(),
    clear: vi.fn(),
    get length() { return Object.keys(LS).length },
    key: vi.fn(),
  })
})

afterEach(() => {
  vi.unstubAllGlobals()
  delete (window as any).hermesDesktop
})

function i18n() {
  return createI18n({
    legacy: false,
    locale: 'zh',
    messages: {
      zh: {
        'mode.starting': '正在启动 OpenCode…',
        'mode.startingHint': '正在注入共享配置',
        'mode.running': '运行中',
        'mode.failed': '启动失败',
        'mode.unsupported': '仅桌面版本可用',
        'mode.unsupportedHint': '请在桌面版本中使用 Code 模式',
        'mode.restart': '重启',
        'mode.retry': '重试',
        'mode.modelLabel': '模型',
      },
    },
  })
}

function setBridge(bridge: Record<string, unknown>) {
  Object.defineProperty(window, 'hermesDesktop', { configurable: true, value: bridge, writable: true })
}

describe('CodeModeView', () => {
  it('shows unsupported panel in non-desktop environment', async () => {
    const wrapper = mount(CodeModeView, { global: { plugins: [i18n()] } })
    await flushPromises()
    expect(wrapper.text()).toContain('仅桌面版本可用')
  })

  it('shows loading state initially on desktop', async () => {
    setBridge({
      isDesktop: true,
      platform: 'linux',
      startCodeMode: vi.fn().mockResolvedValue({ ok: true, url: 'http://127.0.0.1:1234' }),
    })
    const wrapper = mount(CodeModeView, { global: { plugins: [i18n()] } })
    // Starting state (before promise resolves)
    expect(wrapper.text()).toContain('正在启动')
    await flushPromises()
  })

  it('renders webview when startCodeMode succeeds on desktop', async () => {
    setBridge({
      isDesktop: true,
      platform: 'linux',
      startCodeMode: vi.fn().mockResolvedValue({ ok: true, url: 'http://127.0.0.1:1234' }),
    })
    const wrapper = mount(CodeModeView, { global: { plugins: [i18n()] } })
    await flushPromises()
    expect(wrapper.find('webview').exists()).toBe(true)
    expect(wrapper.find('webview').attributes('src')).toBe('http://127.0.0.1:1234')
  })

  it('shows error panel when startCodeMode fails', async () => {
    setBridge({
      isDesktop: true,
      platform: 'linux',
      startCodeMode: vi.fn().mockResolvedValue({ ok: false, error: 'opencode binary not found' }),
    })
    const wrapper = mount(CodeModeView, { global: { plugins: [i18n()] } })
    await flushPromises()
    expect(wrapper.text()).toContain('启动失败')
    expect(wrapper.text()).toContain('opencode binary not found')
    expect(wrapper.find('.retry-btn').exists()).toBe(true)
  })

  it('retry button re-invokes startCodeMode', async () => {
    const startCodeMode = vi.fn().mockResolvedValue({ ok: false, error: 'fail' })
    setBridge({ isDesktop: true, platform: 'linux', startCodeMode })
    const wrapper = mount(CodeModeView, { global: { plugins: [i18n()] } })
    await flushPromises()
    startCodeMode.mockResolvedValueOnce({ ok: true, url: 'http://x' })
    await wrapper.find('.retry-btn').trigger('click')
    await flushPromises()
    expect(startCodeMode).toHaveBeenCalledTimes(2)
  })

  it('displays injected model/provider in header', async () => {
    setBridge({
      isDesktop: true,
      platform: 'linux',
      startCodeMode: vi.fn().mockResolvedValue({ ok: true, url: 'http://x' }),
    })
    const wrapper = mount(CodeModeView, { global: { plugins: [i18n()] } })
    await flushPromises()
    expect(wrapper.text()).toContain('test-model')
    expect(wrapper.text()).toContain('test-provider')
  })
})
