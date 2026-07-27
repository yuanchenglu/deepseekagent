import { createHash, randomBytes } from 'node:crypto'
import { chmodSync, mkdirSync, renameSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

export function createDesktopLoginUrl(baseUrl: string, productHome: string, now = Date.now()): string {
  const ticket = randomBytes(32).toString('base64url')
  const digest = createHash('sha256').update(ticket).digest('hex')
  const ticketsDir = join(productHome, 'runtime', 'webui', 'login-tickets')
  mkdirSync(ticketsDir, { recursive: true, mode: 0o700 })
  chmodSync(ticketsDir, 0o700)
  const target = join(ticketsDir, `${digest}.json`)
  const temporary = `${target}.${process.pid}.tmp`
  writeFileSync(temporary, `${JSON.stringify({
    schema_version: 1,
    product: 'deepagent-webui-ticket',
    sha256: digest,
    expires_at: now + 60_000,
  })}\n`, { encoding: 'utf8', mode: 0o600 })
  renameSync(temporary, target)
  return `${baseUrl.replace(/\/$/, '')}/#/?ticket=${ticket}`
}
