import { vi } from 'vitest'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

// Product paths are process-global constants in the server. Keep every test
// worker inside an allowed disposable directory instead of a developer's home.
process.env.DEEPAGENT_HOME = join(tmpdir(), `deepagent-webui-vitest-${process.pid}`)
process.env.HERMES_HOME = process.env.DEEPAGENT_HOME
delete process.env.HERMES_WEB_UI_HOME
delete process.env.HERMES_WEBUI_STATE_DIR
delete process.env.DEEPAGENT_WEBUI_RUNTIME_DIR

// Vite injects this at build time; unit tests need a stable fallback.
;(globalThis as any).__APP_VERSION__ = 'test'
// Client-only setup (window/localStorage only exist in jsdom)
if (typeof window !== 'undefined') {
  // Mock window.matchMedia
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })

  // Mock localStorage
  const store: Record<string, string> = {}
  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: vi.fn((key: string) => store[key] ?? null),
      setItem: vi.fn((key: string, value: string) => { store[key] = value }),
      removeItem: vi.fn((key: string) => { delete store[key] }),
      clear: vi.fn(() => { for (const k of Object.keys(store)) delete store[k] }),
      get length() { return Object.keys(store).length },
      key: vi.fn((i: number) => Object.keys(store)[i] ?? null),
    },
  })
}
