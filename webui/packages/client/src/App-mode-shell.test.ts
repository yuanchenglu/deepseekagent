// App.vue integration test for mode switching
// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia } from 'pinia'
import { createRouter, createWebHashHistory } from 'vue-router'
import { _resetAppModeForTests } from '@/composables/useAppMode'

// ─── mocks ──────────────────────────────────────────────────────────────
vi.mock('@/composables/useTheme', () => ({ useTheme: () => ({ isDark: { value: false }, isComic: { value: false } }) }))
vi.mock('@/composables/useKeyboard', () => ({ useKeyboard: () => {} }))
vi.mock('@/styles/theme', () => ({ getThemeOverrides: () => ({}) }))
vi.mock('@/components/layout/AppSidebar.vue', () => ({ default: { template: '<aside class="mock-sidebar"></aside>' } }))
vi.mock('@/components/layout/DesktopTitleBar.vue', () => ({ default: { template: '<div class="mock-titlebar"></div>' } }))
vi.mock('@/components/hermes/chat/SessionSearchModal.vue', () => ({ default: { template: '<div></div>' } }))
vi.mock('@/components/auth/AuthEventListener.vue', () => ({ default: { template: '<div></div>' } }))
vi.mock('@/components/auth/DefaultCredentialPrompt.vue', () => ({ default: { template: '<div></div>' } }))
vi.mock('@/components/hermes/pets/WebPet.vue', () => ({ default: { template: '<div></div>' } }))
vi.mock('@/components/layout/ModeSwitcher.vue', () => ({ default: { template: '<nav class="mock-mode-switcher"></nav>' } }))
vi.mock('@/views/hermes/CodeModeView.vue', () => ({ default: { template: '<section class="mock-code-view"></section>' } }))

// Mock app store
vi.mock('@/stores/hermes/app', () => ({
  useAppStore: () => ({
    sidebarOpen: true,
    sidebarCollapsed: false,
    connected: true,
    serverVersion: 'test',
    clientOutdated: false,
    updateAvailable: false,
    nodeVersion: '24.0.0',
    loadModels: vi.fn(),
    startHealthPolling: vi.fn(),
    stopHealthPolling: vi.fn(),
    toggleSidebar: vi.fn(),
    closeSidebar: vi.fn(),
    reloadClient: vi.fn(),
    doUpdate: vi.fn(),
  }),
}))

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
afterEach(() => { _resetAppModeForTests(); vi.unstubAllGlobals(); delete (window as any).hermesDesktop })

function i18n() {
  return createI18n({ legacy: false, locale: 'zh', messages: { zh: { sidebar: { nodeVersionWarning: '' } }, en: {} } })
}

function makeRouter() {
  return createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: '/', name: 'login', component: { template: '<div class="login-page">Login</div>' }, meta: { public: true } },
      { path: '/hermes/chat', name: 'hermes.chat', component: { template: '<div class="chat-page">Chat</div>' } },
      { path: '/hermes/code', name: 'hermes.code', component: { template: '<div class="code-route">CodeRoute</div>' } },
      { path: '/hermes/settings', name: 'hermes.settings', component: { template: '<div class="settings-page">Settings</div>' } },
    ],
  })
}

import App from './App.vue'

describe('App.vue mode shell', () => {
  it('renders ModeSwitcher when not on login page', async () => {
    const router = makeRouter()
    router.push({ name: 'hermes.settings' })
    await router.isReady()
    const wrapper = mount(App, {
      global: { plugins: [i18n(), createPinia(), router] },
    })
    await flushPromises()
    expect(wrapper.find('.mock-mode-switcher').exists()).toBe(true)
  })

  it('hides ModeSwitcher on login page', async () => {
    const router = makeRouter()
    router.push('/')
    await router.isReady()
    const wrapper = mount(App, {
      global: { plugins: [i18n(), createPinia(), router] },
    })
    await flushPromises()
    expect(wrapper.find('.mock-mode-switcher').exists()).toBe(false)
  })

  it('renders AppSidebar in assistant mode', async () => {
    const router = makeRouter()
    router.push({ name: 'hermes.settings' })
    await router.isReady()
    const wrapper = mount(App, { global: { plugins: [i18n(), createPinia(), router] } })
    await flushPromises()
    expect(wrapper.find('.mock-sidebar').exists()).toBe(true)
  })

  it('hides AppSidebar when app mode is code', async () => {
    LS['hermes_app_mode'] = 'code'
    const router = makeRouter()
    router.push({ name: 'hermes.code' })
    await router.isReady()
    const wrapper = mount(App, { global: { plugins: [i18n(), createPinia(), router] } })
    await flushPromises()
    // CodeModeView (mocked) should render instead of sidebar
    expect(wrapper.find('.mock-sidebar').exists()).toBe(false)
  })
})
