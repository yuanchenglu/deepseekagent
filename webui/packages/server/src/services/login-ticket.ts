import { createHash, timingSafeEqual } from 'crypto'
import { lstatSync, readFileSync, realpathSync, unlinkSync } from 'fs'
import { resolve } from 'path'
import { getWebUiRuntimeDir } from '../config'

interface TicketRecord {
  schema_version: number
  product: string
  sha256: string
  expires_at: number
}

function equalHex(left: string, right: string): boolean {
  if (!/^[a-f0-9]{64}$/.test(left) || !/^[a-f0-9]{64}$/.test(right)) return false
  return timingSafeEqual(Buffer.from(left, 'hex'), Buffer.from(right, 'hex'))
}

export function consumeLoginTicket(
  ticket: string,
  now = Date.now(),
  runtimeDir = getWebUiRuntimeDir(),
): boolean {
  if (!/^[A-Za-z0-9_-]{32,256}$/.test(ticket)) return false

  const digest = createHash('sha256').update(ticket).digest('hex')
  const ticketsDir = resolve(runtimeDir, 'login-tickets')
  const ticketPath = resolve(ticketsDir, `${digest}.json`)
  if (!ticketPath.startsWith(`${ticketsDir}/`)) return false

  try {
    const stat = lstatSync(ticketPath)
    if (!stat.isFile() || stat.isSymbolicLink()) return false
    const real = realpathSync(ticketPath)
    if (!real.startsWith(`${realpathSync(ticketsDir)}/`)) return false

    const parsed = JSON.parse(readFileSync(real, 'utf8')) as Partial<TicketRecord>
    unlinkSync(real)
    return parsed.schema_version === 1 &&
      parsed.product === 'deepagent-webui-ticket' &&
      Number.isSafeInteger(parsed.expires_at) &&
      Number(parsed.expires_at) >= now &&
      typeof parsed.sha256 === 'string' &&
      equalHex(parsed.sha256, digest)
  } catch {
    return false
  }
}
