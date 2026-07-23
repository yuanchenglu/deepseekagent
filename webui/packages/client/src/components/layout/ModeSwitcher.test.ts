// ModeSwitcher.vue 单元测试
// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import ModeSwitcher from './ModeSwitcher.vue'

const LS: Record<string, string> = {}

beforeEach(() => {
  Object.keys(LS).forEach(k => delete LS[k])
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
})

function i18n() {
  return createI18n({
    legacy: false,
    locale: 'zh',
    messages: {
      zh: {
        'mode.switcherLabel': '模式切换',
        'mode.assistant': '助理模式',
        'mode.code': 'Code 模式',
        'mode.codeDesktopOnly': 'Code 模式仅桌面版本可用',
      },
      en: {
        'mode.switcherLabel': 'Mode switcher',
        'mode.assistant': 'Assistant',
        'mode.code': 'Code',
        'mode.codeDesktopOnly': 'Code mode is only available on desktop',
      },
    },
  })
}

function mountComp(desktop = false) {
  const bridge = desktop
    ? { isDesktop: true, platform: 'linux', getMode: vi.fn().mockResolvedValue('assistant') }
    : undefined
  if (desktop) Object.defineProperty(window, 'hermesDesktop', { configurable: true, value: bridge, writable: true })
  return mount(ModeSwitcher, { global: { plugins: [i18n()] } })
}

describe('ModeSwitcher', () => {
  afterEach(() => {
    delete (window as any).hermesDesktop
  })

  it('renders two mode tabs', () => {
    const wrapper = mountComp()
    const tabs = wrapper.findAll('.mode-tab')
    expect(tabs).toHaveLength(2)
    expect(tabs[0].text()).toContain('助理模式')
    expect(tabs[1].text()).toContain('Code 模式')
  })

  it('highlights assistant as active by default', () => {
    const wrapper = mountComp()
    const tabs = wrapper.findAll('.mode-tab')
    expect(tabs[0].classes()).toContain('active')
    expect(tabs[1].classes()).not.toContain('active')
  })

  it('emits mode switch when clicking code tab on desktop', async () => {
    const wrapper = mountComp(true)
    await wrapper.findAll('.mode-tab')[1].trigger('click')
    await flushPromises()
    // After click, composable ref changes; active class moves
    const tabs = wrapper.findAll('.mode-tab')
    expect(tabs[1].classes()).toContain('active')
  })

  it('disables code tab in non-desktop environment', () => {
    const wrapper = mountComp(false)
    const codeTab = wrapper.findAll('.mode-tab')[1]
    expect(codeTab.attributes('disabled')).toBeDefined()
    expect(codeTab.classes()).toContain('disabled')
    expect(codeTab.attributes('title')).toContain('仅桌面')
  })

  it('does not switch when clicking disabled code tab', async () => {
    const wrapper = mountComp(false)
    await wrapper.findAll('.mode-tab')[1].trigger('click')
    await flushPromises()
    const tabs = wrapper.findAll('.mode-tab')
    expect(tabs[0].classes()).toContain('active')
  })

  it('has role=tablist for accessibility', () => {
    const wrapper = mountComp()
    expect(wrapper.find('.mode-switcher').attributes('role')).toBe('tablist')
    expect(wrapper.findAll('[role="tab"]')).toHaveLength(2)
  })
})
