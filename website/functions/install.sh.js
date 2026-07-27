/** Serve the canonical CLI Alpha installer as shell text, never as an archive. */
export async function onRequest(context) {
  const assetUrl = new URL('/install-release.sh', context.request.url)
  const response = await context.env.ASSETS.fetch(new Request(assetUrl, context.request))
  if (!response.ok) {
    return new Response('Installer asset is unavailable\n', { status: 503 })
  }
  const headers = new Headers(response.headers)
  headers.set('Content-Type', 'text/x-shellscript; charset=utf-8')
  headers.set('Cache-Control', 'public, max-age=300, must-revalidate')
  headers.set('X-Content-Type-Options', 'nosniff')
  return new Response(response.body, { status: 200, headers })
}
