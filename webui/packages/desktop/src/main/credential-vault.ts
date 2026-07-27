import { mkdirSync, readFileSync, renameSync, unlinkSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'

export interface SafeStorageAdapter {
  isEncryptionAvailable(): boolean
  encryptString(value: string): Buffer
  decryptString(value: Buffer): string
}

type VaultRecord = {
  schemaVersion: 1
  credentials: Record<string, string>
}

const PROVIDER_ENV: Record<string, string> = {
  anthropic: 'ANTHROPIC_API_KEY',
  openai: 'OPENAI_API_KEY',
  openrouter: 'OPENROUTER_API_KEY',
  google: 'GEMINI_API_KEY',
  gemini: 'GEMINI_API_KEY',
  xai: 'XAI_API_KEY',
  groq: 'GROQ_API_KEY',
  deepseek: 'DEEPSEEK_API_KEY',
  mistral: 'MISTRAL_API_KEY',
}

function validProvider(provider: string): boolean {
  return /^[a-z0-9][a-z0-9_-]{0,63}$/.test(provider)
}

export class CredentialVault {
  private readonly path: string

  constructor(productHome: string, private readonly storage: SafeStorageAdapter) {
    this.path = join(productHome, 'data', 'electron', 'credentials.v1.json')
  }

  isAvailable(): boolean {
    return this.storage.isEncryptionAvailable()
  }

  private read(): VaultRecord {
    try {
      const parsed = JSON.parse(readFileSync(this.path, 'utf8')) as Partial<VaultRecord>
      if (parsed.schemaVersion !== 1 || !parsed.credentials || typeof parsed.credentials !== 'object') {
        throw new Error('invalid credential vault')
      }
      return { schemaVersion: 1, credentials: { ...parsed.credentials } }
    } catch {
      return { schemaVersion: 1, credentials: {} }
    }
  }

  private write(record: VaultRecord): void {
    mkdirSync(dirname(this.path), { recursive: true, mode: 0o700 })
    const temporary = `${this.path}.${process.pid}.tmp`
    writeFileSync(temporary, `${JSON.stringify(record)}\n`, { encoding: 'utf8', mode: 0o600 })
    renameSync(temporary, this.path)
  }

  set(provider: string, secret: string): void {
    if (!validProvider(provider) || !secret || secret.length > 16_384) throw new Error('invalid provider credential')
    if (!this.isAvailable()) throw new Error('macOS Keychain encryption is unavailable')
    const record = this.read()
    record.credentials[provider] = this.storage.encryptString(secret).toString('base64')
    this.write(record)
  }

  has(provider: string): boolean {
    if (!validProvider(provider)) return false
    return typeof this.read().credentials[provider] === 'string'
  }

  delete(provider: string): void {
    if (!validProvider(provider)) return
    const record = this.read()
    delete record.credentials[provider]
    if (Object.keys(record.credentials).length === 0) {
      try { unlinkSync(this.path) } catch { /* already absent */ }
      return
    }
    this.write(record)
  }

  private get(provider: string): string | null {
    if (!validProvider(provider) || !this.isAvailable()) return null
    const encrypted = this.read().credentials[provider]
    if (!encrypted) return null
    try {
      return this.storage.decryptString(Buffer.from(encrypted, 'base64'))
    } catch {
      return null
    }
  }

  environmentFor(provider: string): NodeJS.ProcessEnv {
    const variable = PROVIDER_ENV[provider]
    const secret = variable ? this.get(provider) : null
    return variable && secret ? { [variable]: secret } : {}
  }
}
