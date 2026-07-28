import { afterEach, describe, expect, it } from 'vitest'
import {
  RUNTIME_TASK_SUPERVISOR_ENV_NAMES,
  RuntimeTaskSupervisorError,
  acquireRuntimeTaskLease,
  runtimeTaskId,
  stripRuntimeTaskSupervisorEnvironment,
} from './runtime-task-supervisor-client'

const originalEnvironment = { ...process.env }

afterEach(() => {
  for (const key of Object.keys(process.env)) delete process.env[key]
  Object.assign(process.env, originalEnvironment)
})

describe.sequential('runtime task supervisor client', () => {
  it('derives stable Runtime-scoped task IDs', () => {
    expect(runtimeTaskId('deepagent', 'session-a')).toBe(runtimeTaskId('deepagent', 'session-a'))
    expect(runtimeTaskId('deepagent', 'session-a')).not.toBe(runtimeTaskId('deepcode', 'session-a'))
    expect(runtimeTaskId('deepagent', 'session-a')).not.toBe(runtimeTaskId('deepagent', 'session-b'))
    expect(runtimeTaskId('deepagent', 'session-a')).toMatch(/^deepagent:[0-9a-f]{40}$/)
  })

  it('removes Main supervisor credentials before spawning descendants', () => {
    const input: NodeJS.ProcessEnv = {
      PATH: '/usr/bin',
      HOME: '/tmp/home',
      DEEPAGENT_RUNTIME_LEASE_SOCKET: '/tmp/private.sock',
      DEEPAGENT_RUNTIME_LEASE_TOKEN: 'secret-token',
      DEEPAGENT_RUNTIME_LEASE_TTL_MS: '30000',
    }
    const sanitized = stripRuntimeTaskSupervisorEnvironment(input)

    expect(sanitized).toMatchObject({ PATH: '/usr/bin', HOME: '/tmp/home' })
    for (const name of RUNTIME_TASK_SUPERVISOR_ENV_NAMES) {
      expect(sanitized[name]).toBeUndefined()
    }
    expect(input.DEEPAGENT_RUNTIME_LEASE_TOKEN).toBe('secret-token')
  })

  it('allows an empty workspace only when supervision is disabled outside Electron Desktop', async () => {
    delete process.env.HERMES_DESKTOP
    for (const name of RUNTIME_TASK_SUPERVISOR_ENV_NAMES) delete process.env[name]

    const lease = await acquireRuntimeTaskLease({
      runtime: 'deepagent',
      taskId: runtimeTaskId('deepagent', 'browser-session'),
      workspace: '',
      access: 'write',
    })

    expect(lease.enabled).toBe(false)
    expect(lease.workspace).toBe('')
    await expect(lease.heartbeat()).resolves.toBeUndefined()
    await expect(lease.finish('completed')).resolves.toBeUndefined()
  })

  it('fails closed in Electron Desktop when the Main supervisor is missing', async () => {
    process.env.HERMES_DESKTOP = 'true'
    for (const name of RUNTIME_TASK_SUPERVISOR_ENV_NAMES) delete process.env[name]

    const expected: Partial<RuntimeTaskSupervisorError> = {
      code: 'supervisor-not-configured',
      status: 503,
    }
    await expect(acquireRuntimeTaskLease({
      runtime: 'deepagent',
      taskId: runtimeTaskId('deepagent', 'desktop-session'),
      workspace: '/tmp/workspace',
      access: 'write',
    })).rejects.toMatchObject(expected)
  })

  it('rejects an empty workspace when Main supervision is configured', async () => {
    process.env.HERMES_DESKTOP = 'true'
    process.env.DEEPAGENT_RUNTIME_LEASE_SOCKET = '/tmp/runtime-task-supervisor.sock'
    process.env.DEEPAGENT_RUNTIME_LEASE_TOKEN = 'a'.repeat(64)
    process.env.DEEPAGENT_RUNTIME_LEASE_TTL_MS = '30000'

    const expected: Partial<RuntimeTaskSupervisorError> = {
      code: 'workspace-required',
      status: 400,
    }
    await expect(acquireRuntimeTaskLease({
      runtime: 'deepagent',
      taskId: runtimeTaskId('deepagent', 'desktop-session-without-workspace'),
      workspace: '',
      access: 'write',
    })).rejects.toMatchObject(expected)
  })
})
