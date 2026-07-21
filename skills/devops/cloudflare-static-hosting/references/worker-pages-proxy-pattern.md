# Worker-to-Pages Proxy Deployment

## When to Use This Pattern

A **Worker-based proxy** that strips a URL path prefix and proxies to a Cloudflare Pages deployment URL. This combines the flexibility of Workers (custom routing, auth, logic) with the convenience of Pages for static file serving.

Use when:
- You need a **subdirectory-style URL** (e.g. `/work/deepseek/*`) served from a different Cloudflare project
- You want **path rewriting** — a cleaner URL on your main domain maps to a Pages deployment at a different URL
- Your Pages project is published at `<project>.pages.dev` but you want it behind a custom path on your main domain

## Architecture

```
User → custom.domain/work/prefix/* → CF Worker → <project>.pages.dev/path/file
```

The Worker:
1. Receives the request at `custom.domain/work/prefix/path/file`
2. Strips `/work/prefix` from the URL path
3. Constructs a new URL pointing to `https://<project>.pages.dev/path/file`
4. Fetches and returns the response

## Worker Script

```javascript
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    // Strip the prefix for assets lookup
    const path = url.pathname.replace(/^\/work\/prefix/, '') || '/';
    const targetUrl = `https://<project>.pages.dev${path}${url.search}`;
    return fetch(targetUrl, request);
  }
};
```

**Key details:**
- The regex `replace(/^\/work\/prefix/, '')` removes the prefix — adjust regex for your path
- The fallback `|| '/'` ensures root access returns index.html
- Forward `request` as second argument to `fetch()` to preserve headers (cookies, auth, etc.)
- `url.search` preserves query parameters

## wrangler.toml

```toml
name = "your-worker-name"
main = "worker.js"
compatibility_date = "2024-01-01"

[assets]
directory = "."

[[routes]]
pattern = "yourdomain.com/work/prefix/*"
zone_id = "<your-zone-id>"
```

**⚠️ Route pattern**: The route pattern determines when the Worker fires. `domain.com/work/prefix/*` matches `/work/prefix/` and `/work/prefix/anything`.

## Deployment Flow

### 1. Prepare the deploy directory

```bash
# Copy static files from source to temp deploy dir
cp -R src_dir /private/tmp/my-deploy/
cd /private/tmp/my-deploy
```

### 2. Deploy the Worker with assets

```bash
# Auth via env vars (no wrangler login needed)
export CLOUDFLARE_ACCOUNT_ID="<account_id>"
export CLOUDFLARE_API_KEY="<global_api_key>"
export CLOUDFLARE_EMAIL="<email>"

wrangler deploy
```

On re-deploy, wrangler only uploads new/changed files.

### 3. (Optional) Deploy the Pages project separately

If the target is a Cloudflare Pages project:

```bash
# Create the Pages project first (if not exists)
wrangler pages project create <project-name>

# Deploy the static files to Pages
wrangler pages deploy --project-name <project-name> .
```

## Common Pitfalls

### 🔴 JS String Escaping in Inline Data Arrays

When JavaScript data arrays use **single-quoted strings**, any apostrophe/`'` inside a value will **break the script**:

```javascript
// ❌ BROKEN — the ' in "Isn't" closes the string early
const PAPERS = [
  { id: 12, enTitle: 'Memory Granularity Control: Stronger Isn't Always Better' }
];
// → Uncaught SyntaxError: Unexpected identifier 't'
```

**Fix options:**

1. **Escape the apostrophe** — simplest for quick fixes:
   ```javascript
   enTitle: 'Memory Granularity Control: Stronger Isn\\'t Always Better'
   ```

2. **Rephrase to avoid the apostrophe** — cleaner for published content:
   ```javascript
   enTitle: 'Memory Granularity Control: Stronger Is Not Always Better'
   ```

3. **Use double quotes** (if no double quotes inside the value):
   ```javascript
   enTitle: "Memory Granularity Control: Stronger Isn't Always Better"
   ```

**Scan before deploy:**
```bash
# Check for unescaped apostrophes in single-quoted strings
grep -n "n't\\|'s\\|'re\\|'ll\\|'ve\\|'d\\|'m" index.html | grep -v "\\\\\\\\'"
```

> 📖 **Full worked example**: See `references/debug-worker-r2-site.md` for the complete end-to-end debugging walkthrough that fixed this exact bug on a production site.

### 🔴 wrangler pages deploy — Project Not Found

If `wrangler pages deploy` fails with:

```
✘ [ERROR] A request to the Cloudflare API failed.
Project not found. The specified project name does not match any of your
existing projects.
```

The Pages project doesn't exist yet. Create it first:

```bash
wrangler pages project create <project-name>
```

Or use `wrangler deploy` (Workers + assets) instead of `wrangler pages deploy` if the project type is a Worker with `[assets]`.

### 🔴 wrangler auth — Login Expired

If `wrangler login` is expired, use **environment variables** instead:

```bash
export CLOUDFLARE_ACCOUNT_ID="<account_id>"
export CLOUDFLARE_API_KEY="<global_api_key>"
export CLOUDFLARE_EMAIL="<email>"
```

No `wrangler login` needed. Works with both `wrangler deploy` and `wrangler pages deploy`.

### 🔴 pages_build_output_dir Warning

wrangler may warn:

> We detected a configuration file but it is missing the "pages_build_output_dir" field, required by Pages.

If you're using `wrangler deploy` (Workers + assets), this warning is **irrelevant** — it fires because wrangler reads the `wrangler.toml` which lacks a Pages-specific field. The deploy still works. Ignore this warning.

### 🔴 Symlink Resolution

If your static files use **symlinks** (e.g. `zh-md -> /absolute/path/zh-md`), `wrangler deploy` may not follow them correctly or may miss files. **Resolve symlinks before deploying**:

```bash
cp -RL src_dir deploy_dir
rm -rf deploy_dir/.DS_Store
```

The `-L` flag follows symlinks and copies the actual files.

## Verification

```bash
# Check the Worker route exists
curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/workers/routes" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}" | python3 -m json.tool

# Test the proxied endpoint
curl -sI "https://custom.domain/work/prefix/index.html"

# Verify content is served
curl -s "https://custom.domain/work/prefix/" | head -5
```

## Real-World Reference

This pattern was used to deploy the **deepseek-papers** project:

| Parameter | Value |
|-----------|-------|
| Account ID | `d0a9c688290c80b51d6d4605ba32160a` |
| Zone ID | `f5264ddcfd4b8b524299c2e9f9cd55ec` |
| Worker name | `deepseek-papers` |
| Route pattern | `bluth.starseas.org/work/deepseek/*` |
| Staging directory | `/private/tmp/deepseek-deploy/` |

The deploy flow: copy to `/private/tmp/deepseek-deploy/` → `wrangler deploy` with `[assets]` pointing to the directory root.
