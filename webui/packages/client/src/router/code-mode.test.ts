// router/code-mode — Code 路由测试
// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Mock api/client before importing router
vi.mock('@/api/client', () => ({
  hasApiKey: vi.fn(() => true),
  isStoredSuperAdmin: vi.fn(() => true),
}))

import router from './index'

describe('router /hermes/code', () => {
  it('registers the hermes.code route', () => {
    expect(router.hasRoute('hermes.code')).toBe(true)
  })

  it('resolves /hermes/code to CodeModeView', () => {
    const resolved = router.resolve('/hermes/code')
    expect(resolved.name).toBe('hermes.code')
  })

  it('route path is /hermes/code', () => {
    const resolved = router.resolve({ name: 'hermes.code' })
    expect(resolved.path).toBe('/hermes/code')
  })
})
