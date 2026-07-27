import { afterEach, describe, expect, it } from 'vitest'
import { existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { runPhase3Migration } from './migration'

const roots: string[] = []

function root(): string {
  const path = mkdtempSync(join(tmpdir(), 'deepagent-migration-'))
  roots.push(path)
  return path
}

afterEach(() => {
  for (const path of roots.splice(0)) rmSync(path, { recursive: true, force: true })
})

describe('runPhase3Migration', () => {
  it('copies legacy state once and keeps a versioned backup', () => {
    const base = root()
    const productHome = join(base, 'product')
    const legacyWebUiHome = join(base, 'legacy-webui')
    const legacyDesktopHome = join(base, 'legacy-desktop')
    mkdirSync(legacyWebUiHome, { recursive: true })
    mkdirSync(legacyDesktopHome, { recursive: true })
    writeFileSync(join(legacyWebUiHome, 'hermes-web-ui.db'), 'database-v1')
    writeFileSync(join(legacyDesktopHome, 'app-mode.json'), '{"mode":"code"}')

    const result = runPhase3Migration(productHome, { legacyWebUiHome, legacyDesktopHome, now: 42 })

    expect(result.migrated).toEqual(['webui/hermes-web-ui.db', 'desktop/app-mode.json'])
    expect(readFileSync(join(productHome, 'data', 'webui', 'hermes-web-ui.db'), 'utf8')).toBe('database-v1')
    expect(readFileSync(join(productHome, 'data', 'electron', 'app-mode.json'), 'utf8')).toBe('{"mode":"code"}')
    expect(readFileSync(join(result.backup!, 'webui', 'hermes-web-ui.db'), 'utf8')).toBe('database-v1')

    writeFileSync(join(legacyWebUiHome, 'hermes-web-ui.db'), 'database-v2')
    expect(runPhase3Migration(productHome, { legacyWebUiHome, legacyDesktopHome, now: 43 })).toEqual({ migrated: [], backup: null })
    expect(readFileSync(join(productHome, 'data', 'webui', 'hermes-web-ui.db'), 'utf8')).toBe('database-v1')
  })

  it('does not overwrite product data that already exists', () => {
    const base = root()
    const productHome = join(base, 'product')
    const legacyWebUiHome = join(base, 'legacy-webui')
    mkdirSync(legacyWebUiHome, { recursive: true })
    mkdirSync(join(productHome, 'data', 'webui'), { recursive: true })
    writeFileSync(join(legacyWebUiHome, 'hermes-web-ui.db'), 'legacy')
    writeFileSync(join(productHome, 'data', 'webui', 'hermes-web-ui.db'), 'current')

    const result = runPhase3Migration(productHome, { legacyWebUiHome, legacyDesktopHome: join(base, 'missing'), now: 44 })

    expect(result).toEqual({ migrated: [], backup: null })
    expect(readFileSync(join(productHome, 'data', 'webui', 'hermes-web-ui.db'), 'utf8')).toBe('current')
  })

  it('does not follow legacy symlinks', () => {
    const base = root()
    const productHome = join(base, 'product')
    const legacyWebUiHome = join(base, 'legacy-webui')
    mkdirSync(legacyWebUiHome, { recursive: true })
    const secret = join(base, 'outside.db')
    writeFileSync(secret, 'outside')
    symlinkSync(secret, join(legacyWebUiHome, 'hermes-web-ui.db'))

    const result = runPhase3Migration(productHome, { legacyWebUiHome, legacyDesktopHome: join(base, 'missing'), now: 45 })

    expect(result).toEqual({ migrated: [], backup: null })
    expect(existsSync(join(productHome, 'data', 'webui', 'hermes-web-ui.db'))).toBe(false)
  })
})
