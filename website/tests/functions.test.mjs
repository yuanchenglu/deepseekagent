import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'


async function importFunction(relativePath) {
  const source = await readFile(new URL(`../functions/${relativePath}`, import.meta.url), 'utf8')
  const encoded = Buffer.from(source).toString('base64')
  return import(`data:text/javascript;base64,${encoded}`)
}


test('install endpoint serves the canonical script as shell text', async () => {
  const { onRequest } = await importFunction('install.sh.js')
  let requestedPath
  const response = await onRequest({
    request: new Request('https://deepseekagent.starseas.org/install.sh'),
    env: {
      ASSETS: {
        async fetch(request) {
          requestedPath = new URL(request.url).pathname
          return new Response('#!/usr/bin/env bash\n', {
            headers: { 'Content-Type': 'application/octet-stream' },
          })
        },
      },
    },
  })

  assert.equal(requestedPath, '/install-release.sh')
  assert.equal(response.status, 200)
  assert.match(response.headers.get('content-type'), /^text\/x-shellscript/)
  assert.equal(response.headers.get('x-content-type-options'), 'nosniff')
  assert.equal(await response.text(), '#!/usr/bin/env bash\n')
})


test('install endpoint fails closed when the installer asset is missing', async () => {
  const { onRequest } = await importFunction('install.sh.js')
  const response = await onRequest({
    request: new Request('https://deepseekagent.starseas.org/install.sh'),
    env: { ASSETS: { fetch: async () => new Response('missing', { status: 404 }) } },
  })
  assert.equal(response.status, 503)
})


test('release endpoint serves bindings and rejects traversal paths', async () => {
  const { onRequest } = await importFunction('releases/[[path]].js')
  const rejected = await onRequest({
    env: {},
    params: { path: ['manifests', '..', 'secret'] },
  })
  assert.equal(rejected.status, 400)

  let requestedKey
  const response = await onRequest({
    env: {
      RELEASES: {
        async get(key) {
          requestedKey = key
          return {
            body: 'manifest',
            httpEtag: 'etag-value',
            writeHttpMetadata(headers) {
              headers.set('Content-Type', 'application/json')
            },
          }
        },
      },
    },
    params: { path: ['manifests', '0.9.0-alpha.1.json'] },
  })

  assert.equal(requestedKey, 'manifests/0.9.0-alpha.1.json')
  assert.equal(response.status, 200)
  assert.equal(response.headers.get('content-type'), 'application/json')
  assert.match(response.headers.get('cache-control'), /immutable/)
  assert.equal(await response.text(), 'manifest')
})


test('release channel responses are short-lived and a missing object is 404', async () => {
  const { onRequest } = await importFunction('releases/[[path]].js')
  const channel = await onRequest({
    env: {
      RELEASES: {
        async get() {
          return {
            body: '{}',
            httpEtag: 'channel-etag',
            writeHttpMetadata() {},
          }
        },
      },
    },
    params: { path: ['channels', 'alpha.json'] },
  })
  assert.match(channel.headers.get('cache-control'), /max-age=60/)

  const missing = await onRequest({
    env: { RELEASES: { get: async () => null } },
    params: { path: ['manifests', 'missing.json'] },
  })
  assert.equal(missing.status, 404)
})
