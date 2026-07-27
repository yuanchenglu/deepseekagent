import { copyFileSync, existsSync, lstatSync, mkdirSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'

const MIGRATION_ID = 'phase3-v1'
const LEGACY_WEBUI_FILES = ['hermes-web-ui.db', 'hermes-web-ui.db-wal', 'hermes-web-ui.db-shm']

export interface MigrationOptions {
  legacyWebUiHome: string
  legacyDesktopHome: string
  now?: number
}

function safeRegularFile(path: string): boolean {
  try {
    const stat = lstatSync(path)
    return stat.isFile() && !stat.isSymbolicLink()
  } catch {
    return false
  }
}

export function runPhase3Migration(productHome: string, options: MigrationOptions): { migrated: string[]; backup: string | null } {
  const migrationsDir = join(productHome, 'data', 'migrations')
  const marker = join(migrationsDir, `${MIGRATION_ID}.json`)
  if (existsSync(marker)) return { migrated: [], backup: null }

  const timestamp = options.now ?? Date.now()
  const backup = join(productHome, 'data', 'migration-backups', `${MIGRATION_ID}-${timestamp}`)
  const webUiDestination = join(productHome, 'data', 'webui')
  const electronDestination = join(productHome, 'data', 'electron')
  const candidates = [
    ...LEGACY_WEBUI_FILES.map(name => ({
      source: join(options.legacyWebUiHome, name),
      destination: join(webUiDestination, name),
      backup: join(backup, 'webui', name),
      label: `webui/${name}`,
    })),
    {
      source: join(options.legacyDesktopHome, 'app-mode.json'),
      destination: join(electronDestination, 'app-mode.json'),
      backup: join(backup, 'desktop', 'app-mode.json'),
      label: 'desktop/app-mode.json',
    },
  ]

  const copied: string[] = []
  try {
    for (const item of candidates) {
      if (!safeRegularFile(item.source) || existsSync(item.destination)) continue
      mkdirSync(dirname(item.backup), { recursive: true, mode: 0o700 })
      mkdirSync(dirname(item.destination), { recursive: true, mode: 0o700 })
      copyFileSync(item.source, item.backup)
      copyFileSync(item.source, item.destination)
      copied.push(item.destination)
    }
    mkdirSync(migrationsDir, { recursive: true, mode: 0o700 })
    const migrated = candidates.filter(item => copied.includes(item.destination)).map(item => item.label)
    writeFileSync(marker, `${JSON.stringify({
      schemaVersion: 1,
      migration: MIGRATION_ID,
      migrated,
      backup: migrated.length ? backup : null,
    })}\n`, { encoding: 'utf8', mode: 0o600 })
    return { migrated, backup: migrated.length ? backup : null }
  } catch (error) {
    for (const path of copied) rmSync(path, { force: true })
    throw error
  }
}
