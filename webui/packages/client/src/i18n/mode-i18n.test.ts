// i18n mode keys test
import { describe, expect, it } from 'vitest'
import en from './locales/en'
import zh from './locales/zh'

const REQUIRED_KEYS = [
  'switcherLabel',
  'assistant',
  'code',
  'codeDesktopOnly',
  'starting',
  'startingHint',
  'running',
  'failed',
  'unsupported',
  'unsupportedHint',
  'restart',
  'retry',
  'modelLabel',
] as const

describe('i18n mode block', () => {
  for (const locale of [['en', en], ['zh', zh]] as const) {
    const [name, msg] = locale
    describe(name, () => {
      for (const key of REQUIRED_KEYS) {
        it(`has mode.${key}`, () => {
          expect(msg.mode).toBeTruthy()
          expect(typeof msg.mode[key]).toBe('string')
          expect(msg.mode[key].length).toBeGreaterThan(0)
        })
      }
    })
  }
})
