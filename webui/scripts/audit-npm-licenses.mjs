#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { mkdir, readdir, readFile, realpath, writeFile } from 'node:fs/promises'
import path from 'node:path'

function argument(name) {
  const index = process.argv.indexOf(name)
  return index === -1 ? undefined : process.argv[index + 1]
}

const root = path.resolve(argument('--root') || process.cwd())
const roots = [
  path.join(root, 'node_modules'),
  path.join(root, 'packages', 'desktop', 'node_modules'),
]
const LICENSE_OVERRIDES = new Map([
  ['only@0.0.2', {
    license: 'MIT',
    source: 'upstream repository LICENSE',
    evidence_url: 'https://github.com/tj/node-only/blob/master/LICENSE',
  }],
])

function outputPath() {
  const value = argument('--output')
  if (!value) {
    return path.join(root, 'dist', 'releases', 'deepagent-webui-npm-licenses.json')
  }
  return path.resolve(value)
}

function normalizeLicense(value) {
  if (typeof value === 'string') return value.trim()
  if (Array.isArray(value)) return value.map(normalizeLicense).filter(Boolean).join(' OR ')
  if (value && typeof value === 'object') return normalizeLicense(value.type)
  return ''
}

async function detectBundledLicense(packageDir) {
  let entries
  try {
    entries = await readdir(packageDir, { withFileTypes: true })
  } catch {
    return ''
  }
  const candidates = entries
    .filter(entry => entry.isFile() && /^(licen[cs]e|copying|notice)(\.|$)/i.test(entry.name))
    .map(entry => entry.name)
    .sort()

  for (const name of candidates) {
    let text
    try {
      text = (await readFile(path.join(packageDir, name), 'utf8')).slice(0, 100_000)
    } catch {
      continue
    }
    if (/permission is hereby granted, free of charge/i.test(text)) return 'MIT (bundled text)'
    if (/apache license[\s\S]{0,80}version 2\.0/i.test(text)) return 'Apache-2.0 (bundled text)'
    if (/redistribution and use in source and binary forms/i.test(text)) return 'BSD (bundled text)'
    if (/permission to use, copy, modify, and\/or distribute this software/i.test(text)) return 'ISC (bundled text)'
  }
  return ''
}

function licenseRisk(license) {
  const normalized = license.toUpperCase()
  const alternatives = normalized.split(/\s+OR\s+/)
  const permissiveAlternative = alternatives.some(value =>
    /\b(MIT|ISC|BSD|APACHE-2\.0|0BSD|UNLICENSE)\b/.test(value),
  )
  if (!permissiveAlternative && /\b(AGPL|SSPL|BUSL|GPL)(?:[- .(]|$)/.test(normalized)) {
    return 'forbidden'
  }
  if (!permissiveAlternative && /\b(LGPL|MPL|EPL|CDDL)(?:[- .(]|$)/.test(normalized)) return 'review'
  return 'accepted'
}

async function packageDirectories(nodeModulesDir) {
  let entries
  try {
    entries = await readdir(nodeModulesDir, { withFileTypes: true })
  } catch {
    return []
  }
  const result = []
  for (const entry of entries) {
    if (entry.name === '.bin' || entry.name.startsWith('.package-lock')) continue
    const candidate = path.join(nodeModulesDir, entry.name)
    if (entry.name.startsWith('@')) {
      let scoped
      try {
        scoped = await readdir(candidate, { withFileTypes: true })
      } catch {
        continue
      }
      for (const child of scoped) {
        if (child.isDirectory() || child.isSymbolicLink()) result.push(path.join(candidate, child.name))
      }
    } else if (entry.isDirectory() || entry.isSymbolicLink()) {
      result.push(candidate)
    }
  }
  return result
}

async function collectPackages() {
  const queue = [...roots]
  const visitedNodeModules = new Set()
  const packages = new Map()

  while (queue.length > 0) {
    const nodeModulesDir = queue.shift()
    let resolved
    try {
      resolved = await realpath(nodeModulesDir)
    } catch {
      continue
    }
    if (visitedNodeModules.has(resolved)) continue
    visitedNodeModules.add(resolved)

    for (const packageDir of await packageDirectories(nodeModulesDir)) {
      let packageJson
      try {
        packageJson = JSON.parse(await readFile(path.join(packageDir, 'package.json'), 'utf8'))
      } catch {
        continue
      }
      if (!packageJson.name || !packageJson.version) continue

      const key = `${packageJson.name}@${packageJson.version}`
      const override = LICENSE_OVERRIDES.get(key)
      const declared = normalizeLicense(packageJson.license || packageJson.licenses)
      const license = override?.license || declared || await detectBundledLicense(packageDir) || 'UNKNOWN'
      packages.set(key, {
        name: packageJson.name,
        version: packageJson.version,
        license,
        source: override?.source || (declared ? 'package.json' : license === 'UNKNOWN' ? 'missing' : 'bundled text'),
        ...(override?.evidence_url ? { evidence_url: override.evidence_url } : {}),
        risk: license === 'UNKNOWN' ? 'unknown' : licenseRisk(license),
      })
      queue.push(path.join(packageDir, 'node_modules'))
    }
  }
  return [...packages.values()].sort((a, b) =>
    a.name.localeCompare(b.name) || a.version.localeCompare(b.version),
  )
}

async function main() {
  const packages = await collectPackages()
  if (packages.length === 0) {
    throw new Error('No installed npm packages found; run npm ci before the license audit')
  }
  const unknown = packages.filter(item => item.risk === 'unknown')
  const forbidden = packages.filter(item => item.risk === 'forbidden')
  const review = packages.filter(item => item.risk === 'review')
  const lockfile = await readFile(path.join(root, 'package-lock.json'))
  const report = {
    schema_version: 1,
    product: 'deepagent-webui',
    product_license: 'BSL-1.1',
    package_lock_sha256: createHash('sha256').update(lockfile).digest('hex'),
    package_count: packages.length,
    result: unknown.length === 0 && forbidden.length === 0 ? 'pass' : 'fail',
    unknown: unknown.map(item => `${item.name}@${item.version}`),
    forbidden: forbidden.map(item => `${item.name}@${item.version}: ${item.license}`),
    notice_required: review.map(item => `${item.name}@${item.version}: ${item.license}`),
    packages,
  }
  const target = outputPath()
  await mkdir(path.dirname(target), { recursive: true })
  await writeFile(target, `${JSON.stringify(report, null, 2)}\n`, 'utf8')
  console.log(`Audited ${packages.length} npm packages; report: ${target}`)
  if (review.length > 0) console.log(`Recorded ${review.length} weak-copyleft package notice(s)`)
  if (unknown.length > 0 || forbidden.length > 0) {
    console.error(`License audit failed: ${unknown.length} unknown, ${forbidden.length} forbidden`)
    process.exitCode = 1
  }
}

main().catch(error => {
  console.error(error instanceof Error ? error.message : String(error))
  process.exitCode = 1
})
