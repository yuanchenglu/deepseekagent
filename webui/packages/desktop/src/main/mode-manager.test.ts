// mode-manager 单元测试
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import type { ChildProcess } from 'node:child_process'
import { EventEmitter } from 'node:events'
import { ModeManager, type AppMode } from './mode-manager'

function fakeChild(): ChildProcess {
  const ee = new EventEmitter() as unknown as ChildProcess
  ;(ee as any).killed = false
  ;(ee as any).kill = vi.fn(() => { (ee as any).killed = true; ee.emit('exit', 0) })
  return ee
}

let tempDirs: string[] = []
function tempHome(): string {
  const d = mkdtempSync(join(tmpdir(), 'mode-manager-'))
  tempDirs.push(d)
  return d
}
beforeEach(() => { tempDirs = [] })
afterEach(() => { tempDirs.forEach(d => rmSync(d, { recursive: true, force: true })) })

function makeManager(overrides: Partial<ConstructorParameters<typeof ModeManager>[0]> = {}) {
  const spawned: Array<{ command: string; args: string[]; env: NodeJS.ProcessEnv }> = []
  const broadcast = vi.fn()
  const spawnOpenCode = vi.fn((command: string, args: string[], env: NodeJS.ProcessEnv) => {
    spawned.push({ command, args, env })
    return fakeChild()
  })
  const detectOpenCode = vi.fn(() => '/usr/local/bin/opencode')
  const waitForPort = vi.fn().mockResolvedValue(true)
  const getFreePort = vi.fn().mockResolvedValue(12345)
  const mm = new ModeManager({
    userDataPath: tempHome(),
    broadcast,
    spawnOpenCode,
    detectOpenCode,
    waitForPort,
    getFreePort,
    ...overrides,
  })
  return { mm, spawned, broadcast, spawnOpenCode, detectOpenCode, waitForPort, getFreePort }
}

describe('ModeManager', () => {
  it('defaults to assistant mode', () => {
    const { mm } = makeManager()
    expect(mm.getMode()).toBe('assistant')
  })

  it('setMode updates value and broadcasts', async () => {
    const { mm, broadcast } = makeManager()
    await mm.setMode('code')
    expect(mm.getMode()).toBe('code')
    expect(broadcast).toHaveBeenCalledWith('hermes-desktop:mode-changed', 'code')
  })

  it('persists mode across instances', async () => {
    const dir = tempHome()
    const m1 = new ModeManager({ userDataPath: dir })
    await m1.setMode('code')
    const m2 = new ModeManager({ userDataPath: dir })
    expect(m2.getMode()).toBe('code')
  })

  it('ignores invalid mode values', async () => {
    const { mm, broadcast } = makeManager()
    await mm.setMode('invalid' as AppMode)
    expect(mm.getMode()).toBe('assistant')
    expect(broadcast).not.toHaveBeenCalled()
  })

  it('startCodeMode returns not-found when opencode missing', async () => {
    const { mm } = makeManager({ detectOpenCode: () => null })
    const res = await mm.startCodeMode({ apiKey: '', model: '', provider: '' })
    expect(res.ok).toBe(false)
    if (!res.ok) expect(res.error).toMatch(/not found/i)
  })

  it('startCodeMode spawns opencode serve and returns url on success', async () => {
    const { mm, spawned, getFreePort } = makeManager()
    const res = await mm.startCodeMode({ apiKey: 'sk-1', model: 'm', provider: 'p', baseUrl: 'https://x' })
    expect(res.ok).toBe(true)
    if (res.ok) {
      expect(res.url).toBe('http://127.0.0.1:12345')
    }
    expect(getFreePort).toHaveBeenCalled()
    expect(spawned).toHaveLength(1)
    expect(spawned[0].args.slice(0, 2)).toEqual(['serve', '--port'])
    // env 注入了共享配置
    expect(spawned[0].env.OPENCODE_API_KEY).toBe('sk-1')
    expect(spawned[0].env.OPENCODE_MODEL).toBe('m')
    expect(spawned[0].env.OPENCODE_PROVIDER).toBe('p')
    expect(spawned[0].env.OPENCODE_BASE_URL).toBe('https://x')
  })

  it('startCodeMode caches url while process alive', async () => {
    const { mm, spawnOpenCode } = makeManager()
    await mm.startCodeMode({ apiKey: '', model: '', provider: '' })
    await mm.startCodeMode({ apiKey: '', model: '', provider: '' })
    expect(spawnOpenCode).toHaveBeenCalledTimes(1)
  })

  it('startCodeMode returns failure when port wait times out', async () => {
    const { mm } = makeManager({ waitForPort: vi.fn().mockResolvedValue(false) })
    const res = await mm.startCodeMode({ apiKey: '', model: '', provider: '' })
    expect(res.ok).toBe(false)
  })

  it('stopCodeMode kills running process', async () => {
    const { mm, spawnOpenCode } = makeManager()
    await mm.startCodeMode({ apiKey: '', model: '', provider: '' })
    await mm.stopCodeMode()
    expect(mm.getCodeModeUrl()).toBeNull()
    // 子进程 kill 已被触发
    const child = spawnOpenCode.mock.results[0].value as ChildProcess
    expect((child as any).kill).toHaveBeenCalled()
  })
})
