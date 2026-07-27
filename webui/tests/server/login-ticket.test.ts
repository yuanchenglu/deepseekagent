import { afterEach, describe, expect, it } from 'vitest'
import { createHash } from 'crypto'
import { chmodSync, mkdirSync, mkdtempSync, symlinkSync, writeFileSync } from 'fs'
import { tmpdir } from 'os'
import { join } from 'path'
import { consumeLoginTicket } from '../../packages/server/src/services/login-ticket'

const roots: string[] = []

function makeTicket(options: { expiresAt?: number; product?: string; sha256?: string } = {}) {
  const root = mkdtempSync(join(tmpdir(), 'deepagent-ticket-test-'))
  roots.push(root)
  const ticketsDir = join(root, 'login-tickets')
  mkdirSync(ticketsDir, { mode: 0o700 })
  chmodSync(ticketsDir, 0o700)

  const ticket = 'A'.repeat(43)
  const digest = createHash('sha256').update(ticket).digest('hex')
  const path = join(ticketsDir, `${digest}.json`)
  writeFileSync(path, JSON.stringify({
    schema_version: 1,
    product: options.product ?? 'deepagent-webui-ticket',
    sha256: options.sha256 ?? digest,
    expires_at: options.expiresAt ?? 2_000,
  }), { mode: 0o600 })
  return { root, ticketsDir, ticket, path }
}

afterEach(async () => {
  const { rmSync } = await import('fs')
  while (roots.length) rmSync(roots.pop()!, { recursive: true, force: true })
})

describe('one-time login ticket', () => {
  it('accepts a valid ticket exactly once', () => {
    const record = makeTicket()
    expect(consumeLoginTicket(record.ticket, 1_000, record.root)).toBe(true)
    expect(consumeLoginTicket(record.ticket, 1_000, record.root)).toBe(false)
  })

  it('rejects and consumes an expired ticket', () => {
    const record = makeTicket({ expiresAt: 999 })
    expect(consumeLoginTicket(record.ticket, 1_000, record.root)).toBe(false)
    expect(consumeLoginTicket(record.ticket, 500, record.root)).toBe(false)
  })

  it('rejects a record whose digest does not match', () => {
    const record = makeTicket({ sha256: '0'.repeat(64) })
    expect(consumeLoginTicket(record.ticket, 1_000, record.root)).toBe(false)
  })

  it('does not follow a ticket symlink', () => {
    const record = makeTicket()
    const target = join(record.root, 'outside.json')
    writeFileSync(target, '{}')
    const digest = createHash('sha256').update('B'.repeat(43)).digest('hex')
    symlinkSync(target, join(record.ticketsDir, `${digest}.json`))

    expect(consumeLoginTicket('B'.repeat(43), 1_000, record.root)).toBe(false)
  })
})
