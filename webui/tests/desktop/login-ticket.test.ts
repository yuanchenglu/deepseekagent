import { afterEach, describe, expect, it } from 'vitest'
import { createHash } from 'node:crypto'
import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { createDesktopLoginUrl } from '../../packages/desktop/src/main/login-ticket'

const roots: string[] = []

afterEach(() => {
  while (roots.length) rmSync(roots.pop()!, { recursive: true, force: true })
})

describe('desktop one-time login URL', () => {
  it('stores only the ticket digest in the DeepAgent runtime directory', () => {
    const root = mkdtempSync(join(tmpdir(), 'deepagent-desktop-ticket-'))
    roots.push(root)

    const url = createDesktopLoginUrl('http://127.0.0.1:8748', root, 1_000)
    const ticket = new URL(url.replace('/#/', '/')).searchParams.get('ticket')!
    const digest = createHash('sha256').update(ticket).digest('hex')
    const recordText = readFileSync(join(root, 'runtime', 'webui', 'login-tickets', `${digest}.json`), 'utf8')

    expect(recordText).not.toContain(ticket)
    expect(JSON.parse(recordText)).toMatchObject({
      product: 'deepagent-webui-ticket',
      sha256: digest,
      expires_at: 61_000,
    })
  })
})
