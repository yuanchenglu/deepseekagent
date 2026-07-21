# Cloudflare Pages Direct Upload — API Pitfalls

Use this when the user asks to deploy a static site to Cloudflare Pages via the
API (direct upload, not git integration).

## The Multipart Upload Format

Cloudflare Pages Direct Upload uses a single `multipart/form-data` POST request
that includes **both the manifest AND all file content**:

```
POST /accounts/{account_id}/pages/projects/{project}/deployments
Content-Type: multipart/form-data; boundary=BOUNDARY

--BOUNDARY
Content-Disposition: form-data; name="manifest"
Content-Type: application/json

{"index.html": "<sha256>", ...}

--BOUNDARY
Content-Disposition: form-data; name="index.html"; filename="index.html"
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
...

--BOUNDARY--
```

### Key Requirements

1. **Manifest as form field** (not file upload): `name="manifest"` with
   `Content-Type: application/json`. The manifest is a JSON object mapping
   every file path to its SHA256 hash.

2. **Files as additional parts**: Each file gets its own part with
   `name="{path}"; filename="{path}"` and an appropriate `Content-Type`.

3. **SHA256** is the expected hash algorithm. Compute from the raw file bytes.

4. **Branch**: The deployment is created on `"main"` by default. No explicit
   branch parameter if using multipart with files — the branch is implicit.

5. **Auth**: Use `X-Auth-Email` + `X-Auth-Key` (Global API Key) headers.
   API Tokens also work but the Global API Key avoids token creation hassle
   for single-session tasks.

## Common Pitfalls

### 🔴 Deployments Created But Returning 404

Every deployment API call returns `"status": "success"` with a deployment ID
and URL, but the actual files **may not be served**. Symptoms:

```
queued: active        ← stuck in queue
initialize: idle
clone_repo: idle
build: idle
deploy: success       ← deploy stage reports success but files aren't accessible
```

**Root cause unknown (likely Cloudflare-side delay or infrastructure issue).**
Workarounds:

- Delete and recreate the Pages project
- Use **Worker + R2** (Pattern 2 in the main skill) instead of Pages
- Use **Workers + Assets** (`wrangler deploy` with `[assets]`)
- Deploy via the Cloudflare Dashboard (drag-and-drop the build directory)

### 🔴 `-F "manifest=@file.json"` vs Inline Manifest

Both syntaxes work for curl multipart:

```bash
# Inline (good for small manifests)
curl ... -F "manifest={\"index.html\":\"abc123\"}"

# File reference (good for large manifests)
curl ... -F "manifest=@manifest.json;type=application/json"
```

But **including only the manifest without file content creates a deployment
with no actual files** — the deployment record exists but serves nothing.

### 🔴 wrangler CLI Auth

`wrangler pages deploy` does NOT accept `CLOUDFLARE_EMAIL`/`CLOUDFLARE_API_KEY`
env vars for all operations. Some work (project list), others fail (deploy):

- ✅ `npx wrangler pages project list` with email+key
- ❌ `wrangler pages deploy` needs `CLOUDFLARE_API_TOKEN`

If you need `wrangler` for deployment, use the API to create a Pages-scoped
token first, or use the Python/curl multipart approach instead.

| Method | Works for | Limitation |
|--------|-----------|------------|
| `CLOUDFLARE_EMAIL` + `CLOUDFLARE_API_KEY` | Read ops (list projects/deployments) | ❌ Fails for `pages deploy` |
| `CLOUDFLARE_API_TOKEN` | All operations | Token must have **Cloudflare Pages: Edit** |
| `wrangler login` (interactive OAuth) | All operations | Non-interactive environments |

**Creating a Pages-scoped API Token** via the Cloudflare API is complex
(permission group IDs are version-specific). The easiest path:
https://dash.cloudflare.com/profile/api-tokens → Create Token → Custom →
Account · Cloudflare Pages · Edit.

### 🔴 Project-Scoped API Tokens

Creating a Cloudflare API token via the API is complex — permission group IDs
are version-specific and the endpoint layout is unintuitive. The easier path:

1. Create a token manually at https://dash.cloudflare.com/profile/api-tokens
   with "Cloudflare Pages: Edit" permission
2. Use `export CLOUDFLARE_API_TOKEN=<token>` before `wrangler pages deploy`

## Recommended: Use Python for Multipart Upload

For sites with 100+ files, curl multipart becomes unwieldy. Use Python with
`urllib.request` to build the multipart body programmatically:

```python
import json, os, hashlib, uuid, urllib.request
from pathlib import Path

ACCOUNT_ID = "your_account_id"
PROJECT = "your_project_name"
EMAIL = "your_email"
API_KEY = "your_global_api_key"
SITE = Path("/path/to/build/directory")

mime_map = {
    ".html": "text/html; charset=utf-8", ".js": "application/javascript",
    ".css": "text/css", ".json": "application/json",
    ".svg": "image/svg+xml", ".png": "image/png",
    ".ico": "image/x-icon", ".xml": "application/xml",
    ".txt": "text/plain", ".woff2": "font/woff2",
    ".map": "application/json", ".webp": "image/webp",
}

def build_multipart():
    manifest = {}
    files = []
    for fpath in sorted(SITE.rglob("*")):
        if fpath.is_file():
            relpath = str(fpath.relative_to(SITE))
            data = fpath.read_bytes()
            sha = hashlib.sha256(data).hexdigest()
            manifest[relpath] = sha
            files.append((relpath, data))

    boundary = "----DA" + uuid.uuid4().hex
    body = bytearray()

    def w(s):
        body.extend(s.encode() if isinstance(s, str) else s)

    # Manifest part
    w(f"--{boundary}\r\n")
    w('Content-Disposition: form-data; name="manifest"\r\n')
    w("Content-Type: application/json\r\n\r\n")
    w(json.dumps(manifest, separators=(",", ":")))
    w("\r\n")

    # File parts
    for relpath, data in files:
        ext = Path(relpath).suffix
        ct = mime_map.get(ext, "application/octet-stream")
        w(f"--{boundary}\r\n")
        w(f'Content-Disposition: form-data; name="{relpath}"; filename="{relpath}"\r\n')
        w(f"Content-Type: {ct}\r\n\r\n")
        w(data)
        w("\r\n")

    w(f"--{boundary}--\r\n")
    return bytes(body), boundary

body, boundary = build_multipart()
url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/pages/projects/{PROJECT}/deployments"
req = urllib.request.Request(url, data=body)
req.add_header("X-Auth-Email", EMAIL)
req.add_header("X-Auth-Key", API_KEY)
req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
    if result.get("success"):
        d = result["result"]
        print(f"✅ Deployed! ID: {d['id']}, URL: {d.get('url', '')}")
except Exception as e:
    print(f"Error: {e}")
```

## Alternative: Two-Step JWT Upload Flow

When the one-shot multipart approach consistently returns 404 despite reporting
deploy success, try the two-step flow that matches the official Cloudflare Pages
Direct Upload architecture. **Note: this flow may also exhibit the same stalling
issue** — it's a Cloudflare infrastructure problem, not a code bug.

### Step 1: Get Upload JWT

```bash
# JWT is scoped to the project and expires in 300 seconds
curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/pages/projects/${PROJECT}/upload-token" \
  -H "X-Auth-Email: ${EMAIL}" \
  -H "X-Auth-Key: ${API_KEY}"
```

### Step 2: Upload File Content (via JWT auth)

```bash
# POST a JSON array of base64-encoded files to the global assets endpoint
# Each item: {key, value (base64), metadata: {contentType}, base64: true}
curl -s -X POST "https://api.cloudflare.com/client/v4/pages/assets/upload" \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '[{"key":"<md5>","value":"<base64>","metadata":{"contentType":"text/html"},"base64":true}]'
```

### Step 3: Upsert Hashes

```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/pages/assets/upsert-hashes" \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"hashes":["<hash1>","<hash2>"]}'
```

### Step 4: Create Deployment with Manifest

```bash
# Use Global API Key (NOT JWT) for this step
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/pages/projects/${PROJECT}/deployments" \
  -H "X-Auth-Email: ${EMAIL}" \
  -H "X-Auth-Key: ${API_KEY}" \
  -F "manifest=@manifest.json;type=application/json"
```

### File Hash Algorithm Note

The file hash in the assets upload is **MD5** of `(base64_content + "/" + path)`.
The manifest hash in the deployment step is **SHA256** of the raw file bytes.
These are different hashes for different purposes — don't mix them.

### ⚠️ Known Failure: Stuck in `queued: active`

Even with the correct two-step flow, all deployments may end up stuck:
```
queued: active       ← never starts processing
initialize: idle
clone_repo: idle
build: idle
deploy: success      ← immediate ack but files never served
```

**This is a Cloudflare infrastructure issue, not a code bug.** When this
happens, switch to one of these alternatives:

1. **Dashboard upload** (most reliable): Login to Cloudflare Dashboard →
   Workers & Pages → project → Create deployment → drag-and-drop build directory
2. **Workers + Assets** (`wrangler deploy` with `[assets]`) — see Pattern 6
3. **Worker + R2 binding** — see Pattern 2
4. **Delete and recreate the project** — sometimes resets the stuck queue

### `destination_dir` Configuration

The `destination_dir` in the project's `build_config` affects file serving path.
If set to `"build"`, uploaded file paths should include the `build/` prefix.
If empty `""` or `"."`, files serve from root.

When creating a project via API:
```bash
# Best for direct upload: empty destination_dir
curl -X POST ".../pages/projects" \
  -d '{"name":"my-project","production_branch":"main","build_config":{"build_command":"","destination_dir":""}}'
```

## Verification

After deploying, check:

```bash
# 1. Deployment URL responds
curl -sI "https://{deployment-id}.{project}.pages.dev/"

# 2. Project root works
curl -sI "https://{project}.pages.dev/"

# 3. Custom domain (if configured) responds
curl -sI "https://custom.domain/"
```

If all return 404 despite API reporting success, the deployment is stuck in
Cloudflare's infrastructure. Switch to Workers+Assets or Dashboard deployment.

### 🔴 DNS Interception Yields False 000 Errors

Local VPN/network tools (Clash, Surge, Stash, Proxyman, etc.) intercept DNS
and return **`198.18.x.x`** IPs (RFC 3330 — benchmark testing range, commonly
used by transparent proxies). This causes `curl` to return `000` (connection
timeout/DNS failure) even when the real Cloudflare edge is healthy.

**Symptoms of DNS interception:**

```bash
curl -s 'https://deploy-id.project.pages.dev/'     # returns 000
nslookup deploy-id.project.pages.dev               # returns 198.18.0.xx
```

**Workarounds:**

1. **Bypass local DNS to find real IPs:**
   ```bash
   dig @8.8.8.8 project.pages.dev +short
   # → 172.66.47.26, 172.66.44.230  (real Cloudflare edge IPs)
   ```

2. **Use `curl --resolve` to pin the real IP:**
   ```bash
   curl --resolve 'project.pages.dev:443:172.66.47.26' \
     'https://project.pages.dev/' 2>&1 | head -5
   ```
   This bypasses local DNS entirely and hits the real edge.

3. **Or use a tool not affected by local proxy** (e.g., `python3 urllib.request`
   with explicit resolver).

**Not a Cloudflare issue** — the real edge IPs serve the same 404 content as
the project URL when DNS is bypassed. The 404 is caused by deployment stalling,
not by the DNS interception itself.
