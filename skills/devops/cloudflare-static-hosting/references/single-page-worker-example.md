# Single-Page Worker: Embed HTML Directly in Worker

## When to Use This Pattern

For **simple single-page websites** (landing pages, product pages, under-construction pages) where you want:

- Zero infrastructure beyond the Worker itself
- No R2 bucket setup
- No git repo or CI pipeline
- One API call to deploy
- Maximum reliability (no Pages "success→404" failure mode)

## Pattern

Embed the full HTML as a template string inside the Worker JS. The Worker returns it on every request.

## Worker Script Structure

```javascript
addEventListener('fetch', event => {
  const html = `<!DOCTYPE html>
<html>
<head>
  <title>Your Page</title>
  <style>
    /* All CSS inlined — no external dependencies needed */
  </style>
</head>
<body>
  <!-- Full page content here -->
  <script>
    /* All JS inlined */
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

## Deployment (3 Steps)

### 1. Upload Worker (Service Worker format, no bindings)

```bash
curl -s -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts/${SCRIPT_NAME}" \
  -H "X-Auth-Email: ${EMAIL}" \
  -H "X-Auth-Key: ${API_KEY}" \
  -H "Content-Type: application/javascript" \
  --data-binary @worker.js
```

**No multipart needed** — plain `Content-Type: application/javascript` works when there are no bindings.

### 2. Create Worker Route

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/workers/routes" \
  -H "X-Auth-Email: ${EMAIL}" \
  -H "X-Auth-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"pattern": "yourdomain.com/*", "script": "'"${SCRIPT_NAME}"'"}'
```

### 3. Ensure DNS Record Exists (proxied)

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
  -H "X-Auth-Email: ${EMAIL}" \
  -H "X-Auth-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "CNAME",
    "name": "yourdomain.com",
    "content": "openstudy.pages.dev",
    "proxied": true,
    "ttl": 1
  }'
```

The `content` (CNAME target) doesn't matter when proxied — the Worker route intercepts first. Use any valid target as placeholder.

## Verification

```bash
curl -s -o /dev/null -w "HTTP %{http_code} | Size: %{size_download} bytes\n" \
  "https://yourdomain.com/"
```

Use `--resolve` for immediate testing before DNS propagates:
```bash
curl -s "https://yourdomain.com/" \
  --resolve "yourdomain.com:443:198.18.1.83"
```

## Known-Large HTML Files

Workers have a **1MB code size limit** (including the template string). For very large HTML, consider:
- Minifying the HTML before embedding
- Splitting into multiple Workers with routes
- Switching to R2-based serving (Pattern 2 in the main skill)

For a typical landing page (< 50KB), the embedded approach is fine.

## Real-World Example

This approach was used to deploy the **OpenStudy** landing page at https://openedstudy.com:
- Single-page site with CSS animations, particle canvas, responsive design
- Full HTML embedded in Worker JS
- Cloudflare Pages direct upload first failed (HTTP 404 despite "deploy: success")
- Switching to Worker embedded HTML resolved it on first attempt
- Full workflow: Worker upload → route creation → DNS record → live in minutes
