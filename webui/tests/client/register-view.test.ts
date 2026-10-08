// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

const mockReplace = vi.hoisted(() => vi.fn())
const mockRegisterAccount = vi.hoisted(() => vi.fn())
const mockMarkCookieSession = vi.hoisted(() => vi.fn())

vi.mock('vue-router', () => ({
  useRouter: () => ({
    replace: mockReplace,
  }),
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}))

vi.mock('@/api/client', () => ({
  markCookieSession: mockMarkCookieSession,
}))

vi.mock('@/api/auth', () => ({
  registerAccount: mockRegisterAccount,
}))

import RegisterView from '@/views/RegisterView.vue'

const mountOptions = { global: { stubs: { RouterLink: true } } }

describe('RegisterView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('registers a new account and signs in automatically', async () => {
    mockRegisterAccount.mockResolvedValue({
      user: { id: 1, username: 'alice', role: 'admin' },
    })
    const wrapper = mount(RegisterView, mountOptions)

    const inputs = wrapper.findAll('input.register-input')
    await inputs[0].setValue('alice')
    await inputs[1].setValue('secret123')
    await inputs[2].setValue('secret123')
    await wrapper.find('form.register-form').trigger('submit')

    expect(mockRegisterAccount).toHaveBeenCalledWith('alice', 'secret123')
    expect(mockMarkCookieSession).toHaveBeenCalledWith({ id: 1, username: 'alice', role: 'admin' })
    expect(mockReplace).toHaveBeenCalledWith('/hermes/chat')
  })

  it('shows an error when passwords do not match', async () => {
    const wrapper = mount(RegisterView, mountOptions)

    const inputs = wrapper.findAll('input.register-input')
    await inputs[0].setValue('alice')
    await inputs[1].setValue('secret123')
    await inputs[2].setValue('different')
    await wrapper.find('form.register-form').trigger('submit')

    expect(wrapper.find('.register-error').text()).toBe('register.passwordMismatch')
    expect(mockRegisterAccount).not.toHaveBeenCalled()
    expect(mockMarkCookieSession).not.toHaveBeenCalled()
    expect(mockReplace).not.toHaveBeenCalled()
  })

  it('shows a server error message when registration fails', async () => {
    mockRegisterAccount.mockRejectedValue(new Error('Username already exists'))
    const wrapper = mount(RegisterView, mountOptions)

    const inputs = wrapper.findAll('input.register-input')
    await inputs[0].setValue('alice')
    await inputs[1].setValue('secret123')
    await inputs[2].setValue('secret123')
    await wrapper.find('form.register-form').trigger('submit')

    expect(wrapper.find('.register-error').text()).toBe('Username already exists')
    expect(mockMarkCookieSession).not.toHaveBeenCalled()
  })
})
