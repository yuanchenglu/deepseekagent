#!/usr/bin/env node

import { spawnSync } from 'node:child_process'
import { createRequire } from 'node:module'

const args = process.argv.slice(2)
if (args.some(arg => /^(--)?(win|windows|linux)(=|$)/.test(arg))) {
  console.error('Electron Preview supports macOS Apple Silicon only')
  process.exit(2)
}
if (args.some(arg => arg === '--x64' || arg === 'x64')) {
  console.error('Electron Preview does not publish Intel macOS builds')
  process.exit(2)
}

const finalArgs = [...args]
if (!finalArgs.some(arg => arg === '--mac' || arg.startsWith('--mac='))) finalArgs.push('--mac')
if (!finalArgs.some(arg => arg === '--arm64' || arg === 'arm64')) finalArgs.push('--arm64')

const require = createRequire(import.meta.url)
const electronBuilderCli = require.resolve('electron-builder/cli')
const result = spawnSync(process.execPath, [electronBuilderCli, ...finalArgs], { stdio: 'inherit' })
if (result.error) {
  console.error(result.error.message)
  process.exit(1)
}
process.exit(result.status ?? 1)
