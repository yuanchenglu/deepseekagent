/** Serve immutable release objects through an R2 binding or public read URL. */
export async function onRequest(context) {
  const { env, params } = context
  const filePath = Array.isArray(params.path) ? params.path.join('/') : params.path
  if (
    !filePath ||
    filePath.startsWith('/') ||
    filePath.includes('..') ||
    filePath.includes('\\') ||
    !/^[A-Za-z0-9._/-]+$/.test(filePath)
  ) {
    return new Response('Invalid release path\n', { status: 400 })
  }

  if (env.RELEASES && typeof env.RELEASES.get === 'function') {
    const object = await env.RELEASES.get(filePath)
    if (!object) return new Response('Not found\n', { status: 404 })
    const headers = new Headers()
    object.writeHttpMetadata(headers)
    headers.set('etag', object.httpEtag)
    headers.set('Cache-Control', filePath.startsWith('channels/')
      ? 'public, max-age=60, must-revalidate'
      : 'public, max-age=31536000, immutable')
    return new Response(object.body, { headers })
  }

  const publicBase = env.R2_PUBLIC_URL?.replace(/\/$/, '')
  if (!publicBase) {
    return new Response('Release storage is not configured\n', { status: 503 })
  }
  const upstream = await fetch(`${publicBase}/${filePath}`)
  if (!upstream.ok) return new Response('Not found\n', { status: 404 })
  const headers = new Headers(upstream.headers)
  headers.set('Cache-Control', filePath.startsWith('channels/')
    ? 'public, max-age=60, must-revalidate'
    : 'public, max-age=31536000, immutable')
  return new Response(upstream.body, { status: 200, headers })
}
