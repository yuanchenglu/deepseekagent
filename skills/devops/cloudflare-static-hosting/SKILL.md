---
name: cloudflare-static-hosting
description: Deploy static sites and redirects on Cloudflare edge using Workers (with or without R2 bucket bindings). Covers Worker upload via multipart API, R2 bindings, Worker routes, and DNS setup.
triggers:
  - "deploy static site on cloudflare"
  - "cloudflare worker redirect"
  - "cloudflare worker r2 bucket"
  - "cloudflare worker with r2 binding"
  - "301 redirect cloudflare"
  - "host static content on cloudflare"
  - "cloudflare worker route"
  - "cloudflare pages deploy"
  - "cloudflare r2 custom domain"
  - "cloudflare 部署静态页面"
  - "cloudflare 跳转 / 重定向"
  - "cloudflare worker 上传"
  - "workers with assets wrangler"
  - "cloudflare subdirectory deployment"
  - "cloudflare route subpath"
  - "wrangler deploy static files"
  - "cloudflare api key wrangler auth"
  - "debug cloudflare worker r2"
  - "fix cloudflare static site"
  - "cloudflare r2 object download"
  - "cloudflare purge cache"
  - "cloudflare worker route inspect"
  - "cloudflare troubleshooting"
  - "修复 cloudflare 站点"
---

# Cloudflare Static Hosting

Deploy static content and redirects on Cloudflare's edge using Workers (with optional R2 bucket backing). All fully on Cloudflare — no local server, no Tunnel needed.

## Architecture Choices

| Need | Approach | API Complexity |
|------|----------|----------------|
| Simple single-page site (embedded HTML) | Worker with embedded HTML template string | Low (no R2, no bindings) |
| Simple 301/302 redirect | Worker (Service Worker format) + Route | Low |
| Serve static files from R2 | Worker with R2 bucket binding + Route + DNS | Medium |
| Full static site (Pages native) | Cloudflare Pages direct upload | Medium |
| Git-connected static site | Cloudflare Pages (git integration) | Low (UI) |

**Recommendation**: For static content that already lives in R2, use a Worker with R2 binding (reliable, full control). For new static sites, use Pages (simpler for pure static). Workers are preferred when you need arbitrary logic (redirect, auth, rewrite) combined with content serving.

## Prerequisites

- Cloudflare Global API Key (from Dashboard → My Profile → API Tokens)
- Account ID (from Dashboard right sidebar)
- Zone ID for the target domain
- Auth format: `X-Auth-Email` + `X-Auth-Key` headers

## Pattern 1: Simple Redirect Worker

Create a Worker that does a 301/302 redirect from one domain to another.

### 1. Create Worker Script

```javascript
// redirect-worker.js — Service Worker format
addEventListener('fetch', event => {
  event.respondWith(Response.redirect('https://target-domain.com', 301));
});
```

### 2. Upload Worker via API

```bash
curl -s -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT_NAME}" \
  -H "X-Auth-Email: ${EMAIL}" \
  -H "X-Auth-Key: ${API_KEY}" \
  -H "Content-Type: application/javascript" \
  --data-binary @redirect-worker.js
```

Simple redirect Workers with NO bindings can be uploaded as plain `application/javascript` (Service Worker format).

### 3. Create Worker Route

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/workers/routes" \
  -H "X-Auth-Email: ${EMAIL}" \
  -H "X-Auth-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  --data '{
    "pattern": "source-domain.com/*",
    "script": "'${SCRIPT_NAME}'"
  }'
```

**Route pattern syntax**: `hostname.com/*` matches all paths on that hostname. `*.hostname.com/*` matches all subdomains.

### 4. DNS Record

The source domain needs a proxied DNS record so Cloudflare can intercept the request:

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
  -H "X-Auth-Email: ${EMAIL}" \
  -H "X-Auth-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  --data '{
    "type": "CNAME",
    "name": "source-subdomain",
    "content": "public.r2.dev",
    "proxied": true,
    "ttl": 1
  }'
```

The `content` can be any valid target — the Worker route intercepts before reaching the origin. `public.r2.dev` is a safe default. **Must be proxied=true** (orange cloud) for the Worker to fire.

## Pattern 2: Worker with R2 Bucket Binding (Serve Static Content)

Serve files from an R2 bucket via a Worker. This is the most reliable approach for serving existing R2 content on a custom domain.

### 1. Worker Script

```javascript
// r2-server.js — Service Worker format
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  let key = url.pathname.slice(1) || 'index.html';
  
  const object = await RESUME_BUCKET.get(key);
  if (object === null) {
    return new Response('Not Found', { status: 404 });
  }
  
  const headers = new Headers();
  object.writeHttpMetadata(headers);
  headers.set('etag', object.httpEtag);
  headers.set('cache-control', 'public, max-age=3600');
  
  return new Response(object.body, { headers });
}
```

**Note**: The R2 bucket name in the script is the BINDING name (`RESUME_BUCKET`), not the actual bucket name. The mapping is in the metadata.

### 2. Upload Worker with Binding (Multipart Format)

**This is the critical part** — Workers with bindings require multipart upload:

```bash
# Prepare metadata JSON
cat > metadata.json << 'META'
{
  "body_part": "script",
  "bindings": [
    {
      "name": "RESUME_BUCKET",
      "type": "r2_bucket",
      "bucket_name": "resume-bluth"
    }
  ]
}
META

# Upload via multipart
curl -s -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT_NAME}" \
  -H "X-Auth-Email: ${EMAIL}" \
  -H "X-Auth-Key: ${API_KEY}" \
  -F "metadata=@metadata.json;type=application/json" \
  -F "script=@r2-server.js;type=application/javascript"
```

**Key requirements**:
- `body_part: "script"` tells Cloudflare which form field holds the script (REQUIRED for Service Worker format with bindings)
- Bindings are declared in metadata, accessed as **global variables** in the script (no `env` parameter)
- For ES Modules format (with `export default`), use `"main_module": "<filename>"` instead of `"body_part"`

### 3. Create Route + DNS

Same as Pattern 1 steps 3-4, but on the target domain's zone.

## Pattern 4: Worker Embedded Page (Single-Page Site, No R2)

For **simple single-page websites** (landing pages, product pages, under-construction pages) that don't need R2 or Pages. Embed the full HTML as a template string inside the Worker itself.

**Best for**: 1-2 page static sites, product landing pages, splash screens.
**Not for**: Sites with many pages, large file assets, or frequent content updates.

### 1. Create Worker Script

```javascript
// site-worker.js — Service Worker format
addEventListener('fetch', event => {
  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Site</title>
  <style>
    /* All styles inlined */
  </style>
</head>
<body>
  <!-- Full page content -->
  <script>
    /* All JavaScript inlined */
  </script>
</body>
</html>`;
  event.respondWith(new Response(html, {
    headers: {
      'Content-Type': 'text/html;charset=UTF-8',
      'Cache-Control': 'no-cache'
    }
  }));
});
```

### 2. Upload Worker

```bash
curl -s -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT_NAME}" \
  -H "X-Auth-Email: ${EMAIL}" \
  -H "X-Auth-Key: ${API_KEY}" \
  -H "Content-Type: application/javascript" \
  --data-binary @site-worker.js
```

**No multipart needed** — plain `application/javascript` works for Workers without bindings.

### 3. Create Route + DNS (same as Pattern 1 steps 3-4)

See `references/single-page-worker-example.md` for a full worked example with a real landing page deployment.

## Pattern 5: R2 Direct Hosting (No Worker — DNS → public.r2.dev)

For **static sites already in an R2 bucket** — no Worker, no Pages, just DNS and direct R2 serving.

**Best for**: Resume sites, portfolio pages, small static sites where you already have content in R2.
**Limitation**: R2 direct hosting via `public.r2.dev` provides a public URL but limited control over routing (no custom 404 pages, no redirect logic). For more control use Pattern 2 (Worker + R2 binding).

### 1. Upload Files to R2 Bucket

Use Python with boto3 (AWS SDK for S3-compatible API):

```python
import boto3

client = boto3.client(
    "s3",
    endpoint_url="https://${ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id="${ACCESS_KEY_ID}",
    aws_secret_access_key="${SECRET_ACCESS_KEY}",
    region_name="auto"
)

# Set correct Content-Type for each file
content_types = {
    ".html": "text/html; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".pdf": "application/pdf"
}

for filename in ["index.html", "resume.md", "resume.en.md", "resume.pdf", "resume.en.pdf"]:
    with open(filename, "rb") as f:
        ext = filename.split(".")[-1]
        ct = content_types.get("." + ext, "application/octet-stream")
        client.put_object(
            Bucket="${BUCKET_NAME}",
            Key=filename,
            Body=f,
            ContentType=ct
        )
```

**Alternative**: use `aws s3 cp` with `--endpoint-url` (but boto3 is more reliable for infrequent batch uploads). For a reusable script, see `references/r2-boto3-upload.py`.

### 2. DNS Record

Create a CNAME pointing to `public.r2.dev`:

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
  -H "X-Auth-Email: ${EMAIL}" \
  -H "X-Auth-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  --data '{
    "type": "CNAME",
    "name": "'${SUBDOMAIN}.${DOMAIN}'",
    "content": "public.r2.dev",
    "proxied": true,
    "ttl": 1
  }'
```

**Must be proxied=true** (orange cloud) for Cloudflare edge to serve the content.

### 3. R2 Bucket Public Access

The bucket needs to be configured for public access. Either:
- Set the bucket to public via Cloudflare Dashboard (R2 → bucket → Settings → Public access)
- Or add a custom domain directly in the R2 bucket settings (R2 → bucket → Settings → Custom Domains)

### Verification

See `references/r2-boto3-upload.py` for a reusable upload script (run with `R2_ACCESS_KEY` and `R2_SECRET_KEY` env vars).

```bash
# Check files served correctly
curl -sI "https://${SUBDOMAIN}.${DOMAIN}/index.html"
curl -s "https://${SUBDOMAIN}.${DOMAIN}/resume.md" | head -5

# Check Content-Type headers
curl -sI "https://${SUBDOMAIN}.${DOMAIN}/resume.pdf" | grep -i content-type
```

### DNS Record Lookup: Finding Which R2 Bucket Serves a Domain

When debugging a live resume site (e.g. `bluth.starseas.org` → CNAME `public.r2.dev`), you can find which R2 bucket it serves from by:

1. List all R2 buckets via Cloudflare API:
   ```bash
   curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/r2/buckets" \
     -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}"
   ```
2. The bucket name is typically descriptive (`resume-bluth`, `clawadmin`, etc.) — match based on context
3. DNS records tell you the CNAME target but not the bucket name directly

For brand-new static sites not yet in R2, prefer **Pattern 6** (Workers + Assets) instead.

## Pattern 6: Workers + Static Assets (wrangler deploy with [assets])

For **multi-page static sites with many files** (Markdown document sets, image-heavy sites, paper archives) that are too large for embedded HTML but don't need R2. Uses wrangler's native `[assets]` support.

**Best for**: Multi-page sites with moderate file count (tens to hundreds of files), static document archives, paper/reference sites.
**Not for**: Single-page sites (use Pattern 4), sites needing R2-scale storage (use Pattern 2).

### Prerequisites (wrangler auth)

Wrangler accepts Global API Key via environment variables — no `wrangler login` needed:

```bash
export CLOUDFLARE_ACCOUNT_ID="<account_id>"
export CLOUDFLARE_API_KEY="<global_api_key>"
export CLOUDFLARE_EMAIL="<email>"
```

### Symlink Resolution

If your static files use symlinks (e.g. `zh-md -> ../zh-md/`), resolve them before deploying:

```bash
cp -RL src_dir deploy_dir
rm -rf deploy_dir/.DS_Store deploy_dir/screenshots
```

### Deployment: Directory Structure

For subdirectory paths like `/work/deepseek/`, structure files to match the route path:

```
deploy_dir/
├── wrangler.toml
├── worker.js           # pass-through Worker
└── work/
    └── deepseek/
        ├── index.html
        ├── zh-md/
        ├── en-md/
        └── pdf/
```

`wrangler.toml`:
```toml
name = "my-project"
main = "worker.js"
compatibility_date = "2024-01-01"

[assets]
directory = "."

[[routes]]
pattern = "yourdomain.com/work/deepseek/*"
zone_id = "<zone_id>"
```

Worker (ES Modules pass-through):
```javascript
export default {
  async fetch(request, env, ctx) {
    return env.ASSETS.fetch(request);
  }
};
```

**⚠️ Critical**: The assets directory MUST match the route path. If the route is `/work/deepseek/*`, assets must be at `work/deepseek/index.html` — NOT at root `index.html`.

### Deployment Command

```bash
cd deploy_dir
CLOUDFLARE_ACCOUNT_ID="..." CLOUDFLARE_API_KEY="..." CLOUDFLARE_EMAIL="..." wrangler deploy
```

On re-deploy, wrangler only uploads new/modified files.

### Create Route (API alternative if not in wrangler.toml)

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/workers/routes" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"pattern": "yourdomain.com/work/deepseek/*", "script": "my-project"}'
```

### Key Details

- The warning `"Will match assets: /work/deepseek/*"` is expected — assets at that prefix are served directly.
- Use `CLOUDFLARE_API_KEY` + `CLOUDFLARE_EMAIL` env vars for non-interactive deployment.
- ES Modules Worker (`export default`) with `main = "worker.js"` in wrangler.toml.

### Variant: Worker-to-Pages Proxy

Instead of `env.ASSETS.fetch()`, the Worker can proxy to an external Pages deployment URL after stripping a path prefix. Use this when a clean subdirectory-style URL on your main domain should serve content from a separate Pages project:

```
User -> custom.domain/work/prefix/* -> Worker -> <project>.pages.dev/path/file
```

See `references/worker-pages-proxy-pattern.md` for the full pattern, including deployment flows, wrangler.toml setup, and coverage of common pitfalls (JS string escaping in inline data arrays, `pages_build_output_dir` warning, symlink resolution, wrangler auth expiry).

### Pitfall: Route Zone Mismatch

If wrangler reports `"Route pattern must include zone name"`, the zone_id in your route doesn't match the actual domain's zone. Verify:

```bash
curl -s "https://api.cloudflare.com/client/v4/zones" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}" | python3 -c "import sys,json; [print(z['name'],z['id']) for z in json.load(sys.stdin)['result']]"
```

## Verification

```bash
# Check redirect
curl -sI "https://source-domain.com" | grep -i "^location:\|^HTTP/"

# Check static content
curl -sI "https://target-domain.com"
curl -s "https://target-domain.com" | head -5

# Check Worker route exists
curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/workers/routes" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}"

# Check DNS record
curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records?name=domain.com" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}"
```

## Worker Formats Reference

### Service Worker Format (simpler, used in this session)
```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});
async function handleRequest(request) { ... }
```
- Upload with `"body_part": "script"` in metadata
- R2 bindings accessed as global variables (`RESUME_BUCKET.get(key)`)
- No `export default` — plain global functions

### ES Modules Format (modern, recommended for new projects)
```javascript
export default {
  async fetch(request, env) {
    const object = await env.RESUME_BUCKET.get(key);
    ...
  }
};
```
- Upload with `"main_module": "worker.js"` in metadata  
- Bindings accessed via `env` parameter
- Requires multipart format

## Pattern 7: Worker with R2 Binding — Multi-Route, ES Module Format

Serve different sites from the **same Worker** on **different URL paths**, using an R2 bucket with path prefixes. This is the approach used for hosting both `study.starseas.org/deepseek/` and `study.starseas.org/llmharnessagent/` from the same Worker + R2 bucket.

### R2 File Organization

Store files in R2 with prefix-based isolation:

```
Bucket: deepseek-papers
├── index.html                   # deepseek site root
├── zh-md/                       # deepseek Chinese translations
├── en-md/                       # deepseek English originals
├── thinking-md/                 # deepseek Socratic Q&A
├── pdf/                         # deepseek PDFs
└── llm/                         # llmharnessagent files
    ├── index.html
    ├── zh/
    ├── en/
    └── thinking-md/
```

### Worker Script (ES Module with R2 binding)

```javascript
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    let r2key;
    
    if (path.startsWith('/deepseek')) {
      r2key = (path.replace(/^\/deepseek\/?/, '') || 'index.html');
    } else if (path.startsWith('/llmharnessagent')) {
      r2key = 'llm/' + (path.replace(/^\/llmharnessagent\/?/, '') || 'index.html');
    } else {
      return new Response('Not Found', { status: 404 });
    }
    
    try {
      const object = await env.DEEPSEEK_BUCKET.get(r2key);
      if (object === null) {
        return new Response('Not Found: ' + r2key, { status: 404 });
      }
      const headers = new Headers();
      headers.set('Content-Type', getType(r2key));
      headers.set('Cache-Control', 'public, max-age=86400');
      headers.set('Access-Control-Allow-Origin', '*');
      return new Response(object.body, { headers });
    } catch(e) {
      return new Response('Error: ' + e.message, { status: 500 });
    }
  }
};

function getType(path) {
  if (path.endsWith('.html')) return 'text/html; charset=utf-8';
  if (path.endsWith('.md')) return 'text/markdown; charset=utf-8';
  if (path.endsWith('.pdf')) return 'application/pdf';
  if (path.endsWith('.png')) return 'image/png';
  if (path.endsWith('.css')) return 'text/css';
  if (path.endsWith('.js')) return 'application/javascript';
  return 'application/octet-stream';
}
```

**Key details:**
- ES Module format with `export default { async fetch(request, env, ctx) { ... } }`
- R2 binding accessed via `env.DEEPSEEK_BUCKET` (not as global variable)
- Multiple URL prefixes map to different R2 key prefixes
- Leading `/` from the URL path is stripped via regex before prepending the R2 prefix

### Upload Worker with R2 Binding via Multipart API (ES Module Format)

```python
import requests, io, json

worker_code = """export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    let r2key;
    if (path.startsWith('/deepseek')) {
      r2key = (path.replace(/^\/deepseek\/?/, '') || 'index.html');
    } else if (path.startsWith('/othersite')) {
      r2key = 'other/' + (path.replace(/^\/othersite\/?/, '') || 'index.html');
    }
    // ...serve from env.DEEPSEEK_BUCKET.get(r2key)...
  }
};"""

metadata = json.dumps({
    "main_module": "worker.mjs",
    "compatibility_date": "2024-01-01",
    "bindings": [
        {"name": "DEEPSEEK_BUCKET", "type": "r2_bucket", "bucket_name": "my-bucket"}
    ]
})

boundary = "----WorkerBoundary"
body = io.BytesIO()
body.write(f"--{boundary}\r\n".encode())
body.write(b'Content-Disposition: form-data; name="metadata"\r\n')
body.write(b"Content-Type: application/json\r\n\r\n")
body.write(metadata.encode())
body.write(b"\r\n")
body.write(f"--{boundary}\r\n".encode())
body.write(b'Content-Disposition: form-data; name="worker.mjs"; filename="worker.mjs"\r\n')
body.write(b"Content-Type: application/javascript+module\r\n\r\n")
body.write(worker_code.encode())
body.write(b"\r\n")
body.write(f"--{boundary}--\r\n".encode())

resp = requests.put(
    f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{script_name}",
    headers={"X-Auth-Email": email, "X-Auth-Key": api_key,
             "Content-Type": f"multipart/form-data; boundary={boundary}"},
    data=body.getvalue()
)
```

**⚠️ ES Module format rules:**
- Use `"main_module": "worker.mjs"` in metadata (NOT `"body_part"`)
- `.mjs` file with `Content-Type: application/javascript+module`
- Bindings accessed via `env.BINDING_NAME`, not as globals
- The file name in the multipart form (`"worker.mjs"`) must match `main_module` value

### Upload Files to R2 via boto3 (S3-compatible API)

```python
import boto3
s3 = boto3.client('s3',
    endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key)

# Upload with prefix
with open('local-file.html', 'rb') as f:
    s3.upload_fileobj(f, 'bucket-name', 'prefix/index.html')
```

**Path handling:** R2 keys DO NOT start with `/`. `get('index.html')` works, `get('/index.html')` returns null. Strip leading `/` from URL paths before R2 lookup.

### Add Worker Route via API

```python
requests.post(
    f"https://api.cloudflare.com/client/v4/zones/{zone_id}/workers/routes",
    headers=auth_headers,
    json={"pattern": "domain.com/path*", "script": "script-name"}
)
```

**Route pattern notes:**
- `domain.com/deepseek/*` matches `/deepseek/` and `/deepseek/anything` but NOT `/deepseek` (no trailing slash)
- `domain.com/deepseek*` matches `/deepseek`, `/deepseek/`, AND `/deepseek/anything` — use this for robustness

### Full End-to-End Workflow

1. **Upload content to R2** (via boto3 Python)
2. **Create/update Worker** (via multipart API — see above)
3. **Add Worker route** (via API)
4. **Add DNS record** (A record with dummy IP, proxied=true):
   ```python
   requests.post(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records",
       headers=auth_headers,
       json={"type": "A", "name": "subdomain", "content": "192.0.2.1",
             "ttl": 1, "proxied": True})
   ```
   **Must be proxied=true** (orange cloud). Use dummy IP `192.0.2.1` (RFC 5737). 
   For CNAME: avoid pointing to another Cloudflare customer domain (triggers Error 1014).

### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Error 1014 (CNAME Cross-User Banned) | DNS CNAME points to another Cloudflare customer domain | Change to A record with dummy IP + proxied=true |
| HTTP 404 for files that exist in R2 | R2 key has leading `/` | Strip `/` from the path before `bucket.get(key)` |
| HTTP 522 (Connection timed out) | Worker execution timeout, often from slow file serving | Check Worker code, ensure R2 binding is correct |
| HTTP 404 for path without trailing slash | Route pattern `base/*` doesn't match `base` (no slash) | Use `base*` (without `/` before `*`) instead of `base/*` |

## Debugging a Live Worker+R2 Site

When a deployed Worker+R2 site breaks (JS syntax error, blank page, missing content), use this systematic flow to diagnose and fix it.

### 1. Identify the Symptom

Start with the user's report and the browser console:

```bash
# Fetch the page and check for console errors
curl -s "https://site.com/path/"
# Look for "SyntaxError", "Uncaught", "Unexpected identifier" in the response

# Check HTTP status and cache headers
curl -sI "https://site.com/path/" | grep -i "content-type\|cache-control\|cf-cache"
```

### 2. Map the Architecture

Find which Worker serves the URL and how:

```bash
# List all Workers on the account
curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}"

# List Worker routes for the zone to find which Worker handles the URL
curl -s "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/workers/routes" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}"

# Get the Worker script to understand the serving logic
curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT_NAME}" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}"
```

Key questions:
- Does the Worker serve from R2 (`env.BUCKET.get(key)`)? → **R2-based**
- Does it proxy to Pages (`env.ASSETS.fetch(request)`)? → **Workers+Assets**
- Does it proxy to an external URL (`fetch(targetUrl)`)? → **Proxy pattern**

### 3. If R2-Based: Find the R2 Bucket

Get the Worker's bindings to find the R2 bucket name and key prefix:

```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT_NAME}/bindings" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}"
```

The response shows `bucket_name` (R2 bucket) and the URL→key mapping from the Worker code.

### 4. Download the Broken File from R2

Use boto3 (S3-compatible API) to download the file:

```python
import boto3
s3 = boto3.client('s3',
    endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    config=boto3.session.Config(signature_version='s3v4'),
    region_name='auto')

obj = s3.get_object(Bucket='bucket-name', Key='prefix/file.html')
content = obj['Body'].read()
```

### 5. Diagnose and Fix

Common failure modes for inline JavaScript in HTML files:

| Symptom | Likely Cause |
|---------|-------------|
| `SyntaxError: Unexpected identifier 't'` | Unescaped single quote in single-quoted JS string (`Isn't` → string break) |
| `SyntaxError: Unexpected token ')'` | Missing comma in object literal or close-paren |
| `SyntaxError: Invalid or unexpected token` | Template literal with stray backtick or `${}` in non-template string |
| Blank page / sidebar empty | JS parse error prevents `buildSidebar()` etc. from running |

**Fix**: Change the delimiters of the affected value (single→double quotes, or escape the apostrophe):

```python
import re
# Example: fix unescaped apostrophe in enTitle by switching to double quotes
fixed = re.sub(
    r"(enTitle:)'([^']*?)\bIsn't\b([^']*?)'",
    r'\1"\2Isn\'t\3"',
    content
)
```

See `references/debug-worker-r2-site.md` for a full worked example with the `Isn't` bug fix.

### 6. Upload the Fixed File Back to R2

```python
with open('fixed_file.html', 'rb') as f:
    s3.put_object(
        Bucket='bucket-name',
        Key='prefix/file.html',
        Body=f,
        ContentType='text/html; charset=utf-8',
        CacheControl='public, max-age=86400'
    )
```

### 7. Purge the CDN Cache

The old file may be cached at Cloudflare's edge (max-age=86400 by default). Purge the specific URL:

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/purge_cache" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"files":["https://site.com/path/"]}'
```

### 8. Verify

```bash
# Fetch with cache-busting
curl -s "https://site.com/path/?cb=1" | grep "the fixed string"

# Check console errors in a browser
# Use browser_console expression to check for JS errors

# Verify the page structure is intact
curl -s "https://site.com/path/" | grep -c "expected content marker"
```

See `references/debug-worker-r2-site.md` for a full end-to-end example.

## Related Skills

- `cloudflare-tunnel-troubleshoot` — For Tunnel-based deployments (local servers behind Cloudflare)
- `cf-workers-ai-api-proxy-china` — Workers for proxying AI APIs

## Reference Files

- `references/pages-direct-upload-pitfalls.md` — Cloudflare Pages direct upload via multipart API, deployment stuck issues, and Python upload script
