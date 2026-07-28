#!/usr/bin/env python3
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{path}: expected exactly one match, found {count}: {old[:120]!r}')
    target.write_text(text.replace(old, new, 1), encoding='utf-8')


path = 'webui/packages/desktop/src/main/runtime-task-supervisor.ts'
replace_once(path, """export class MacOsRuntimeTaskProcessProbe implements RuntimeTaskProcessProbe {
  async inspect(pid: number): Promise<RuntimeTaskProcessEvidence | null> {
    if (!validPid(pid) || process.platform === 'win32') return null
    try {
      const { stdout } = await execFileAsync('ps', ['-p', String(pid), '-o', 'lstart=', '-o', 'command='], {
        encoding: 'utf8',
        timeout: 5_000,
        maxBuffer: 64 * 1024,
      })
      const command = stdout.replace(/\\s+/g, ' ').trim()
      if (!command) return null
      return {
        pid,
        fingerprint: createHash('sha256').update(command).digest('hex'),
        command: command.slice(0, 512),
      }
    } catch {
      return null
    }
  }
}
""", """function windowsPowerShell(): string {
  const systemRoot = String(process.env.SystemRoot || '').trim()
  if (systemRoot) {
    const candidate = join(systemRoot, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
    if (existsSync(candidate)) return candidate
  }
  return 'powershell.exe'
}

export class SystemRuntimeTaskProcessProbe implements RuntimeTaskProcessProbe {
  async inspect(pid: number): Promise<RuntimeTaskProcessEvidence | null> {
    if (!validPid(pid)) return null
    return process.platform === 'win32'
      ? this.inspectWindows(pid)
      : this.inspectPosix(pid)
  }

  private async inspectPosix(pid: number): Promise<RuntimeTaskProcessEvidence | null> {
    try {
      const { stdout } = await execFileAsync('ps', ['-p', String(pid), '-o', 'lstart=', '-o', 'command='], {
        encoding: 'utf8',
        timeout: 5_000,
        maxBuffer: 64 * 1024,
      })
      const command = stdout.replace(/\\s+/g, ' ').trim()
      if (!command) return null
      return {
        pid,
        fingerprint: createHash('sha256').update(command).digest('hex'),
        command: command.slice(0, 512),
      }
    } catch {
      return null
    }
  }

  private async inspectWindows(pid: number): Promise<RuntimeTaskProcessEvidence | null> {
    const script = [
      \"$ErrorActionPreference = 'Stop'\",
      `$target = Get-CimInstance Win32_Process -Filter \\\"ProcessId = ${pid}\\\"`,
      'if ($null -eq $target) { exit 3 }',
      \"$creation = if ($target.CreationDate -is [DateTime]) { $target.CreationDate.ToUniversalTime().ToString('o') } else { [string]$target.CreationDate }\",
      \"[pscustomobject]@{ creation = $creation; executable = [string]$target.ExecutablePath; commandLine = [string]$target.CommandLine } | ConvertTo-Json -Compress\",
    ].join('; ')
    try {
      const { stdout } = await execFileAsync(windowsPowerShell(), [
        '-NoProfile',
        '-NonInteractive',
        '-ExecutionPolicy',
        'Bypass',
        '-Command',
        script,
      ], {
        encoding: 'utf8',
        timeout: 5_000,
        maxBuffer: 64 * 1024,
        windowsHide: true,
      })
      const parsed = JSON.parse(stdout.trim()) as {
        creation?: unknown
        executable?: unknown
        commandLine?: unknown
      }
      const creation = String(parsed.creation || '').trim()
      const executable = String(parsed.executable || '').trim()
      const commandLine = String(parsed.commandLine || '').trim()
      if (!creation && !executable && !commandLine) return null
      const identity = [creation, executable, commandLine].join('\\u0000')
      return {
        pid,
        fingerprint: createHash('sha256').update(identity).digest('hex'),
        command: (executable || commandLine || `pid ${pid}`).slice(0, 512),
      }
    } catch {
      return null
    }
  }
}
""")
replace_once(path, """    this.processProbe = options.processProbe ?? new MacOsRuntimeTaskProcessProbe()
""", """    this.processProbe = options.processProbe ?? new SystemRuntimeTaskProcessProbe()
""")
replace_once(path, """    const generation = (this.generations.get(key) || 0) + 1
""", """    const generation = request.runtime === 'deepagent'
      ? (this.generations.get(key) || 0) + 1
      : 1
""")
replace_once(path, """    this.records.set(key, record)
    this.generations.set(key, generation)
    this.persist()
""", """    this.records.set(key, record)
    if (request.runtime === 'deepagent') this.generations.set(key, generation)
    this.persist()
""")
replace_once(path, """    this.generations.set(key, generation)
    this.persist()
    return { status: 200, body: { ok: true, code: 'resumed', task: cloneTask(record) } }
""", """    if (record.runtime === 'deepagent') this.generations.set(key, generation)
    this.persist()
    return { status: 200, body: { ok: true, code: 'resumed', task: cloneTask(record) } }
""")
replace_once(path, """    for (const item of persisted.generations) {
      if (!validRuntime(item.runtime) || !validString(item.taskId) || !Number.isSafeInteger(item.generation) || item.generation < 1) continue
      this.generations.set(stableTaskKey(item.runtime, item.taskId), item.generation)
    }
""", """    for (const item of persisted.generations) {
      if (item.runtime !== 'deepagent' || !validString(item.taskId) || !Number.isSafeInteger(item.generation) || item.generation < 1) continue
      this.generations.set(stableTaskKey(item.runtime, item.taskId), item.generation)
    }
""")
replace_once(path, """      const generation = Math.max(1, task.generation || 1, this.generations.get(key) || 0)
      this.generations.set(key, generation)
""", """      const generation = task.runtime === 'deepagent'
        ? Math.max(1, task.generation || 1, this.generations.get(key) || 0)
        : Math.max(1, task.generation || 1)
      if (task.runtime === 'deepagent') this.generations.set(key, generation)
""")
replace_once(path, """    const generations = [...this.generations].map(([key, generation]) => {
""", """    const generations = [...this.generations].map(([key, generation]) => {
""")

path = 'webui/packages/desktop/src/main/index.ts'
replace_once(path, """import { deepAgentHome, desktopIcon, desktopTrayTemplateIcon, desktopWindowsTrayIcon, webuiDir } from './paths'
""", """import { deepAgentHome, desktopIcon, desktopTrayTemplateIcon, desktopWindowsTrayIcon, webuiDir, webUiHome } from './paths'
""")
replace_once(path, """      stateDir: join(deepAgentHome(), 'runtime', 'task-supervisor'),
""", """      stateDir: join(webUiHome(), 'runtime', 'task-supervisor'),
""")

print('Runtime lifecycle review fixes applied')
