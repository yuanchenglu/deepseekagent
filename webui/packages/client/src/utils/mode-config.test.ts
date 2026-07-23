// mode-config 单元测试 — 阶段 9
// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  APP_MODE_STORAGE_KEY,
  EMPTY_SHARED_CONFIG,
  applyToOpenCode,
  getSharedConfig,
  readStoredMode,
  writeStoredMode,
  type SharedConfig,
} from './mode-config'

const LS: Record<string, string> = {}

beforeEach(() => {
  Object.keys(LS).forEach(k => delete LS[k])
  vi.stubGlobal('localStorage', {
    getItem: vi.fn((k: string) => LS[k] ?? null),
    setItem: vi.fn((k: string, v: string) => { LS[k] = String(v) }),
    removeItem: vi.fn((k: string) => { delete LS[k] }),
    clear: vi.fn(() => Object.keys(LS).forEach(k => delete LS[k])),
    get length() { return Object.keys(LS).length },
    key: vi.fn(),
  })
})

afterEach(() => { vi.unstubAllGlobals() })

describe('mode-config.getSharedConfig', () => {
  it('returns empty config when nothing stored', () => {
    const cfg = getSharedConfig()
    expect(cfg).toEqual(EMPTY_SHARED_CONFIG)
  })

  it('reads api key, baseUrl, profile from localStorage', () => {
    LS['hermes_api_key'] = 'sk-123'
    LS['hermes_server_url'] = 'https://example.com'
    LS['hermes_active_profile_name'] = 'work'
    const cfg = getSharedConfig()
    expect(cfg.apiKey).toBe('sk-123')
    expect(cfg.baseUrl).toBe('https://example.com')
    expect(cfg.profile).toBe('work')
  })

  it('prefers appState selection over localStorage for model/provider', () => {
    LS['hermes_selected_model'] = 'gpt-4'
    LS['hermes_selected_provider'] = 'openai'
    const cfg = getSharedConfig({ selectedModel: 'claude-sonnet', selectedProvider: 'anthropic' })
    expect(cfg.model).toBe('claude-sonnet')
    expect(cfg.provider).toBe('anthropic')
  })

  it('falls back to localStorage for model/provider when appState missing', () => {
    LS['hermes_selected_model'] = 'gpt-4'
    LS['hermes_selected_provider'] = 'openai'
    const cfg = getSharedConfig()
    expect(cfg.model).toBe('gpt-4')
    expect(cfg.provider).toBe('openai')
  })
})

describe('mode-config.applyToOpenCode', () => {
  it('returns desktop-only error in non-desktop environment', async () => {
    const res = await applyToOpenCode({ apiKey: 'x', model: 'm', provider: 'p' })
    expect(res.ok).toBe(false)
    if (!res.ok) expect(res.error).toBe('desktop-only')
  })

  it('invokes bridge.startCodeMode with the config on desktop', async () => {
    const cfg: SharedConfig = { apiKey: 'sk-1', model: 'm1', provider: 'p1' }
    const startCodeMode = vi.fn().mockResolvedValue({ ok: true, url: 'http://127.0.0.1:9999' })
    const bridge = { isDesktop: true, platform: 'linux', startCodeMode } as any
    const res = await applyToOpenCode(cfg, bridge)
    expect(startCodeMode).toHaveBeenCalledWith(cfg)
    expect(res).toEqual({ ok: true, url: 'http://127.0.0.1:9999' })
  })

  it('catches thrown errors from bridge', async () => {
    const startCodeMode = vi.fn().mockRejectedValue(new Error('boom'))
    const bridge = { isDesktop: true, platform: 'linux', startCodeMode } as any
    const res = await applyToOpenCode({ apiKey: '', model: '', provider: '' }, bridge)
    expect(res.ok).toBe(false)
    if (!res.ok) expect(res.error).toContain('boom')
  })
})

describe('mode-config.readStoredMode / writeStoredMode', () => {
  it('defaults to assistant when storage empty', () => {
    expect(readStoredMode()).toBe('assistant')
  })
  it('returns code when stored as code', () => {
    LS[APP_MODE_STORAGE_KEY] = 'code'
    expect(readStoredMode()).toBe('code')
  })
  it('writeStoredMode persists the value', () => {
    writeStoredMode('code')
    expect(LS[APP_MODE_STORAGE_KEY]).toBe('code')
  })
  it('writeStoredMode(assistant) overwrites code', () => {
    LS[APP_MODE_STORAGE_KEY] = 'code'
    writeStoredMode('assistant')
    expect(LS[APP_MODE_STORAGE_KEY]).toBe('assistant')
  })
})
