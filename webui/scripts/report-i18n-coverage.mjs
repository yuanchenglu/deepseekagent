#!/usr/bin/env node

import { Buffer } from 'node:buffer'
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import process from 'node:process'

const root = process.cwd()
const sourceRoot = join(root, 'packages', 'client', 'src')
const localeRoot = join(sourceRoot, 'i18n', 'locales')
const localeFiles = {
  en: 'en.ts',
  zh: 'zh.ts',
  'zh-TW': 'zh-TW.ts',
  ja: 'ja.ts',
  ko: 'ko.ts',
  fr: 'fr.ts',
  es: 'es.ts',
  de: 'de.ts',
  pt: 'pt.ts',
  ru: 'ru.ts',
}
const allowedMissing = new Set([
  'changelog.new_0_5_4_7',
  'chat.sessionNotFound',
])

function walkFiles(directory, files = []) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name)
    if (entry.isDirectory()) {
      walkFiles(path, files)
    } else if (/\.(ts|vue)$/.test(entry.name) && !path.replaceAll('\\', '/').includes('/i18n/locales/')) {
      files.push(path)
    }
  }
  return files
}

function collectLiteralTranslationKeys() {
  const keys = new Set()
  const translationCall = /(?:\b|\$)t\(\s*['"]([^'"]+)['"]/g
  for (const file of walkFiles(sourceRoot)) {
    const source = readFileSync(file, 'utf8')
    for (const match of source.matchAll(translationCall)) keys.add(match[1])
  }

  const changelogSource = readFileSync(join(sourceRoot, 'data', 'changelog.ts'), 'utf8')
  for (const block of changelogSource.matchAll(/changes\s*:\s*\[([\s\S]*?)\]/g)) {
    for (const match of block[1].matchAll(/['"]([^'"]+)['"]/g)) keys.add(match[1])
  }
  return [...keys].sort()
}

async function loadLocale(fileName) {
  const source = readFileSync(join(localeRoot, fileName), 'utf8')
  const url = `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`
  return (await import(url)).default
}

function isRecord(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function deepMerge(base, override) {
  if (!isRecord(base) || !isRecord(override)) return override
  const merged = { ...base }
  for (const [key, value] of Object.entries(override)) {
    merged[key] = isRecord(value) && isRecord(base[key])
      ? deepMerge(base[key], value)
      : value
  }
  return merged
}

function hasPath(messages, key) {
  let current = messages
  for (const part of key.split('.')) {
    if (!current || typeof current !== 'object' || !(part in current)) return false
    current = current[part]
  }
  return typeof current !== 'undefined'
}

const outputArgIndex = process.argv.indexOf('--output')
const outputPath = resolve(root, outputArgIndex >= 0 ? process.argv[outputArgIndex + 1] : '../dist/test-results/i18n-coverage.json')
const requiredKeys = collectLiteralTranslationKeys()
const rawLocales = Object.fromEntries(
  await Promise.all(Object.entries(localeFiles).map(async ([name, file]) => [name, await loadLocale(file)])),
)
const effectiveLocales = Object.fromEntries(
  Object.entries(rawLocales).map(([locale, messages]) => [
    locale,
    locale === 'en' ? messages : deepMerge(rawLocales.en, messages),
  ]),
)

const rawMissingByLocale = Object.fromEntries(
  Object.entries(rawLocales).map(([locale, messages]) => [
    locale,
    requiredKeys.filter(key => !allowedMissing.has(key) && !hasPath(messages, key)),
  ]),
)
const effectiveMissingByLocale = Object.fromEntries(
  Object.entries(effectiveLocales).map(([locale, messages]) => [
    locale,
    requiredKeys.filter(key => !allowedMissing.has(key) && !hasPath(messages, key)),
  ]),
)
const missingEnglish = rawMissingByLocale.en
const missingRuntime = Object.entries(effectiveMissingByLocale)
  .flatMap(([locale, keys]) => keys.map(key => `${locale}: ${key}`))

const report = {
  requiredKeyCount: requiredKeys.length,
  missingEnglish,
  effectiveMissingByLocale,
  missingRuntime,
  rawMissingByLocale,
}
mkdirSync(dirname(outputPath), { recursive: true })
writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8')

if (missingRuntime.length > 0) {
  console.error(`Missing English i18n keys (${missingEnglish.length}):`)
  for (const key of missingEnglish) console.error(`- ${key}`)
  console.error(`Missing effective runtime i18n entries (${missingRuntime.length}); report: ${outputPath}`)
  process.exit(1)
}

const rawFallbackCount = Object.values(rawMissingByLocale).reduce((total, keys) => total + keys.length, 0)
console.log(`i18n static coverage passed for ${requiredKeys.length} keys across ${Object.keys(rawLocales).length} effective locales`)
console.log(`Raw locale fallback entries recorded for follow-up: ${rawFallbackCount}`)
