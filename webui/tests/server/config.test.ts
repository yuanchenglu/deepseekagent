import { describe, expect, it } from 'vitest'
import { homedir } from 'os'
import { join, resolve } from 'path'
import { getCorsOrigins, getListenHost, getWebUiHome, getWebUiRuntimeDir, shouldCreateWebUiDataDir } from '../../packages/server/src/config'

describe('server config', () => {
  it('defaults to an IPv4 bind host', () => {
    expect(getListenHost({})).toBe('127.0.0.1')
  })

  it('uses BIND_HOST when provided', () => {
    expect(getListenHost({ BIND_HOST: ' :: ' })).toBe('::')
  })

  it('ignores blank BIND_HOST values', () => {
    expect(getListenHost({ BIND_HOST: ' ' })).toBe('127.0.0.1')
  })

  it('defaults web-ui home under the DeepAgent product root', () => {
    expect(getWebUiHome({})).toBe(join(homedir(), '.deepagent', 'data', 'webui'))
  })

  it('uses DEEPAGENT_HOME without consulting Hermes data', () => {
    expect(getWebUiHome({ DEEPAGENT_HOME: '/tmp/deepagent-product' }))
      .toBe(join('/tmp/deepagent-product', 'data', 'webui'))
  })

  it('keeps process state in the DeepAgent runtime namespace', () => {
    expect(getWebUiRuntimeDir({ DEEPAGENT_HOME: '/tmp/deepagent-product' }))
      .toBe(join('/tmp/deepagent-product', 'runtime', 'webui'))
  })

  it('uses HERMES_WEB_UI_HOME when provided', () => {
    expect(getWebUiHome({ HERMES_WEB_UI_HOME: ' ./tmp/hermes-ui ' })).toBe(resolve('./tmp/hermes-ui'))
  })

  it('uses HERMES_WEBUI_STATE_DIR as a compatibility alias', () => {
    expect(getWebUiHome({ HERMES_WEBUI_STATE_DIR: ' ./tmp/hermes-state ' })).toBe(resolve('./tmp/hermes-state'))
  })

  it('only creates the development data directory outside production', () => {
    expect(shouldCreateWebUiDataDir({ NODE_ENV: 'development' })).toBe(true)
    expect(shouldCreateWebUiDataDir({ NODE_ENV: 'production' })).toBe(false)
  })

  it('does not enable cross-origin requests by default', () => {
    expect(getCorsOrigins({})).toBe('')
  })

  it('uses CORS_ORIGINS when provided', () => {
    expect(getCorsOrigins({ CORS_ORIGINS: ' https://app.example, http://localhost:3000 ' })).toBe('https://app.example, http://localhost:3000')
  })
})
