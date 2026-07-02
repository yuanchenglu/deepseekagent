/**
 * Cloudflare Pages Function — /releases/* proxy to R2
 *
 * Proxies release file requests from the Pages deployment to the R2 bucket,
 * making tarballs and checksums publicly accessible without requiring
 * R2 bucket public access configuration.
 *
 * The install-release.sh script uses R2_BASE_URL:
 *   https://deepseekagent.starseas.org/releases
 *
 * Which routes here: /releases/deepagent-{version}.tar.gz
 *
 * Env vars (set in Pages dashboard → Settings → Environment variables):
 *   R2_ACCESS_KEY_ID     — R2 S3-compatible access key
 *   R2_SECRET_ACCESS_KEY — R2 S3-compatible secret key
 *   R2_ENDPOINT          — R2 S3-compatible endpoint URL
 *   R2_BUCKET            — R2 bucket name (default: deepagent-releases)
 */
export async function onRequest(context) {
  const { request, env, params } = context;
  
  // Extract the file path from the URL (everything after /releases/)
  const filePath = params.path || 'index.html';
  
  // Build the R2 S3 URL
  const endpoint = env.R2_ENDPOINT || 'https://d0a9c688290c80b51d6d4605ba32160a.r2.cloudflarestorage.com';
  const bucket = env.R2_BUCKET || 'deepagent-releases';
  const r2Url = `${endpoint}/${bucket}/${filePath}`;
  
  // Fetch from R2 with the access key
  const accessKey = env.R2_ACCESS_KEY_ID || '9a4ccbd58399df30a5631d5e5d903874';
  const secretKey = env.R2_SECRET_ACCESS_KEY || 'af4901e38119d431e858253f878e5810328a3ab93a9c475b6ab15991c1fc1cc3';
  
  // For simple authentication, use the R2 API token approach or Bearer
  // For production, set env vars in Pages dashboard
  const response = await fetch(r2Url, {
    headers: {
      'Authorization': `Bearer ${secretKey}`,
    },
  });
  
  if (!response.ok) {
    return new Response(`Not found: ${filePath}`, { status: 404 });
  }
  
  // Proxy the response with appropriate headers
  const headers = new Headers(response.headers);
  headers.set('Access-Control-Allow-Origin', '*');
  headers.set('Cache-Control', 'public, max-age=86400');
  
  return new Response(response.body, {
    status: response.status,
    headers,
  });
}
