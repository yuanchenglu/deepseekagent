import { beforeEach, describe, expect, it, vi } from 'vitest'

const { startOutboundRelayClientMock, stopOutboundRelayClientMock } = vi.hoisted(() => ({
  startOutboundRelayClientMock: vi.fn(),
  stopOutboundRelayClientMock: vi.fn(),
}))

vi.mock('../../packages/server/src/services/global-agent/outbound-relay-client', () => ({
  startOutboundRelayClient: startOutboundRelayClientMock,
  stopOutboundRelayClient: stopOutboundRelayClientMock,
}))

vi.mock('../../packages/server/src/services/hermes/hermes-profile', () => ({
  listProfileNamesFromDisk: () => ['default', 'research'],
}))

describe('user registration controller', () => {
  let db: any = null

  beforeEach(async () => {
    vi.resetModules()
    vi.clearAllMocks()
    vi.stubEnv('AUTH_JWT_SECRET', 'test-secret')

    const { DatabaseSync } = await import('node:sqlite')
    db = new DatabaseSync(':memory:')
    vi.doMock('../../packages/server/src/db/index', () => ({
      getDb: () => db,
      getStoragePath: () => ':memory:',
    }))

    const schemas = await import('../../packages/server/src/db/hermes/schemas')
    schemas.initAllHermesTables()
  })

  async function loadModules() {
    return {
      ctrl: await import('../../packages/server/src/controllers/auth'),
      users: await import('../../packages/server/src/db/hermes/users-store'),
      auth: await import('../../packages/server/src/middleware/user-auth'),
    }
  }

  function makeCtx(body: Record<string, unknown>) {
    return {
      request: { body },
      headers: {},
      query: {},
      ip: '127.0.0.1',
      status: 200,
      body: null,
      cookies: { set: vi.fn() },
      get: vi.fn(() => ''),
      req: { socket: { remoteAddress: '127.0.0.1' } },
    } as any
  }

  it('rejects self-service registration while it is disabled', async () => {
    vi.stubEnv('HERMES_WEB_UI_ALLOW_REGISTRATION', '')
    const { ctrl } = await loadModules()
    const ctx = makeCtx({ username: 'alice', password: 'secret123' })

    await ctrl.register(ctx)

    expect(ctx.status).toBe(403)
    expect(ctx.body).toEqual({ error: 'Self-service registration is disabled' })
  })

  it('accepts valid registration and binds the account to the default profile', async () => {
    vi.stubEnv('HERMES_WEB_UI_ALLOW_REGISTRATION', '1')
    const { ctrl, users } = await loadModules()
    const ctx = makeCtx({ username: 'alice', password: 'secret123' })

    await ctrl.register(ctx)

    expect(ctx.status).toBe(201)
    expect(ctx.body.user).toEqual({ id: 1, username: 'alice', role: 'admin' })

    const user = users.findUserByUsername('alice')
    expect(user?.role).toBe('admin')
    expect(user?.status).toBe('active')
    expect(users.verifyPassword('secret123', user!.password_hash)).toBe(true)
    expect(users.listUserProfiles(user!.id).map(profile => profile.profile_name)).toEqual(['default'])
    expect(ctx.cookies.set).toHaveBeenCalled()
  })

  it('rejects usernames shorter than 2 characters', async () => {
    vi.stubEnv('HERMES_WEB_UI_ALLOW_REGISTRATION', '1')
    const { ctrl } = await loadModules()
    const ctx = makeCtx({ username: 'a', password: 'secret123' })

    await ctrl.register(ctx)

    expect(ctx.status).toBe(400)
    expect(ctx.body).toEqual({ error: 'Username must be at least 2 characters' })
  })

  it('rejects passwords shorter than 6 characters', async () => {
    vi.stubEnv('HERMES_WEB_UI_ALLOW_REGISTRATION', '1')
    const { ctrl } = await loadModules()
    const ctx = makeCtx({ username: 'alice', password: '12345' })

    await ctrl.register(ctx)

    expect(ctx.status).toBe(400)
    expect(ctx.body).toEqual({ error: 'Password must be at least 6 characters' })
  })

  it('rejects an already registered username', async () => {
    vi.stubEnv('HERMES_WEB_UI_ALLOW_REGISTRATION', '1')
    const { ctrl, users } = await loadModules()
    users.createUser({ username: 'alice', password: 'secret123', role: 'admin' })
    const ctx = makeCtx({ username: 'alice', password: 'other123' })

    await ctrl.register(ctx)

    expect(ctx.status).toBe(409)
    expect(ctx.body).toEqual({ error: 'Username already exists' })
  })

  it('reports registration availability through auth status', async () => {
    vi.stubEnv('HERMES_WEB_UI_ALLOW_REGISTRATION', 'on')
    const { ctrl } = await loadModules()
    const ctx = makeCtx({})

    await ctrl.authStatus(ctx)

    expect(ctx.body).toEqual({
      hasPasswordLogin: true,
      hasUsers: false,
      registrationEnabled: true,
    })
  })

  it('mounts POST /api/auth/register on the public router', async () => {
    const { authPublicRoutes } = await import('../../packages/server/src/routes/auth')
    const layer = authPublicRoutes.stack.find(
      (entry: any) => Array.isArray(entry.methods) && entry.methods.includes('POST') && entry.path === '/api/auth/register',
    )
    expect(layer).toBeDefined()
  })
})
