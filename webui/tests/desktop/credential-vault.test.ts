import { afterEach, describe, expect, it } from 'vitest'
import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { CredentialVault, type SafeStorageAdapter } from '../../packages/desktop/src/main/credential-vault'

const roots: string[] = []

function fakeSafeStorage(): SafeStorageAdapter {
  return {
    isEncryptionAvailable: () => true,
    encryptString: value => Buffer.from([...Buffer.from(value)].map(byte => byte ^ 0x5a)),
    decryptString: value => Buffer.from([...value].map(byte => byte ^ 0x5a)).toString('utf8'),
  }
}

afterEach(() => {
  while (roots.length) rmSync(roots.pop()!, { recursive: true, force: true })
})

describe('desktop credential vault', () => {
  it('stores encrypted provider credentials and injects only the selected provider', () => {
    const root = mkdtempSync(join(tmpdir(), 'deepagent-vault-'))
    roots.push(root)
    const vault = new CredentialVault(root, fakeSafeStorage())

    vault.set('anthropic', 'secret-anthropic-key')

    const stored = readFileSync(join(root, 'data', 'electron', 'credentials.v1.json'), 'utf8')
    expect(stored).not.toContain('secret-anthropic-key')
    expect(vault.has('anthropic')).toBe(true)
    expect(vault.environmentFor('anthropic')).toEqual({ ANTHROPIC_API_KEY: 'secret-anthropic-key' })
    expect(vault.environmentFor('openai')).toEqual({})
  })

  it('fails closed when operating-system encryption is unavailable', () => {
    const root = mkdtempSync(join(tmpdir(), 'deepagent-vault-'))
    roots.push(root)
    const vault = new CredentialVault(root, {
      ...fakeSafeStorage(),
      isEncryptionAvailable: () => false,
    })

    expect(() => vault.set('openai', 'secret')).toThrow(/Keychain/)
  })
})
