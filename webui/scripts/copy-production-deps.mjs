#!/usr/bin/env node

import { cpSync, existsSync, mkdirSync, readFileSync } from 'node:fs'
import path from 'node:path'

function argument(name) {
  const index = process.argv.indexOf(name)
  return index === -1 ? undefined : process.argv[index + 1]
}

const sourceRoot = path.resolve(argument('--source') || process.cwd())
const destinationRoot = path.resolve(argument('--destination') || '')
if (!argument('--destination')) {
  console.error('--destination is required')
  process.exit(2)
}

const lock = JSON.parse(readFileSync(path.join(sourceRoot, 'package-lock.json'), 'utf8'))
if (lock.lockfileVersion !== 3 || !lock.packages || typeof lock.packages !== 'object') {
  console.error('A package-lock v3 file is required')
  process.exit(1)
}

const packagePaths = Object.entries(lock.packages)
  .filter(([packagePath, metadata]) =>
    packagePath.startsWith('node_modules/')
    && metadata
    && typeof metadata === 'object'
    && metadata.dev !== true,
  )
  .sort(([left], [right]) => left.split('/').length - right.split('/').length || left.localeCompare(right))

let copied = 0
for (const [packagePath, metadata] of packagePaths) {
  const source = path.join(sourceRoot, packagePath)
  if (!existsSync(source)) {
    if (metadata.optional === true) continue
    console.error(`Required production package is not installed: ${packagePath}`)
    process.exit(1)
  }
  const destination = path.join(destinationRoot, packagePath)
  mkdirSync(path.dirname(destination), { recursive: true })
  cpSync(source, destination, {
    recursive: true,
    dereference: false,
    filter(candidate) {
      if (candidate === source) return true
      const relative = path.relative(source, candidate)
      return !relative.split(path.sep).includes('node_modules')
    },
  })
  copied += 1
}

if (copied === 0) {
  console.error('No production packages were copied')
  process.exit(1)
}
console.log(`Copied ${copied} lockfile-pinned production packages`)
