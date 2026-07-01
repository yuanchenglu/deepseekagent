/**
 * Cloudflare Pages Function — /install.sh redirect
 *
 * Redirects install.sh requests to the latest release tarball on R2.
 *
 * The install.sh endpoint is the public entrypoint for:
 *   curl -fsSL https://deepseekagent.starseas.org/install.sh | sh
 *
 * Env vars (set in Pages dashboard → Settings → Environment variables):
 *   R2_PUBLIC_URL — Public R2 bucket URL (optional)
 *     Default: https://releases.deepseekagent.starseas.org
 *     Example: https://deepagent-releases.<account-id>.r2.dev
 *
 * Routing:
 *   - /install.sh?version=latest        → deepagent-latest.tar.gz
 *   - /install.sh?version=v0.9.0       → deepagent-v0.9.0.tar.gz
 *   - /install.sh (default)            → deepagent-latest.tar.gz
 *
 * @see Also: scripts/install-release.sh for the actual installer
 * @see Also: scripts/setup-cloudflare.sh for R2 + Pages setup
 */
export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);

  // Parse version from query param, default to 'latest'
  const version = url.searchParams.get('version') || 'latest';

  // Construct download URL
  // R2_PUBLIC_URL can be set in Pages dashboard env vars.
  // Falls back to the public R2.dev subdomain.
  const baseUrl = env.R2_PUBLIC_URL || 'https://releases.deepseekagent.starseas.org';
  const downloadUrl = version === 'latest'
    ? `${baseUrl}/deepagent-latest.tar.gz`
    : `${baseUrl}/deepagent-${version}.tar.gz`;

  // 302 redirect to R2 (transient — clients should follow to the actual CDN)
  return Response.redirect(downloadUrl, 302);
}
