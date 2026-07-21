---
name: docsify-docker-deploy
description: Deploy a Docsify documentation site with Docker nginx, auto-generated sidebar from local markdown files, and Cloudflare Tunnel for HTTPS. Zero-build markdown rendering — edit .md files, refresh browser.
triggers:
  - "deploy docsify"
  - "markdown documentation site"
  - "static docs from markdown"
  - "knowledge base from .md files"
  - "文档系统部署"
  - "知识库网站"
---

# Docsify + Docker + Cloudflare Tunnel Deployment

Deploy a zero-build Markdown documentation site that reads `.md` files directly from a local directory, auto-generates a sidebar from the folder structure, and serves via HTTPS through Cloudflare Tunnel.

## Architecture

```
User Browser → HTTPS (Cloudflare) → Tunnel → localhost:80 (nginx Docker) → ~/Documents/article/*.md
```

## Phase 1: Docsify + Nginx Docker

### Step 1: Create site directory

```
~/Documents/docsify-site/
├── index.html          # Docsify frontend
├── _sidebar.md         # Auto-generated sidebar
├── nginx.conf          # Nginx configuration
├── docker-compose.yml  # Docker setup
├── generate_sidebar.py # Sidebar generator script
└── docs/               # Symlinks to article dir (dev convenience)
```

### Step 2: index.html — Critical Config

```html
<script>
  window.$docsify = {
    name: 'Site Name',
    loadSidebar: '/_sidebar.md',    // ⚠️ MUST be absolute path starting with /
    loadNavbar: false,
    subMaxLevel: 3,
    auto2top: true,
    basePath: '/docs/',             // Where .md files are served from
    relativePath: true,
    homepage: 'README.md',          // Served from basePath
    search: {
      maxAge: 86400000,
      paths: 'auto',
      placeholder: '🔍 搜索...',
      depth: 4,
    },
  };
</script>
```

**CRITICAL PITFALL:** `loadSidebar` must be `'/_sidebar.md'` (absolute), NOT `'_sidebar.md'` (relative). When `basePath` is set (e.g., `/docs/`), Docsify resolves relative `loadSidebar` paths against `basePath`, causing requests to `/docs/_sidebar.md` which 404s. Use absolute path to bypass basePath resolution.

### Step 3: nginx.conf

```nginx
server {
    listen 80;
    server_name your.domain.org;

    # Static Docsify frontend
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Markdown files — served from mounted article directory
    location /docs/ {
        alias /articles/;
        autoindex off;
        add_header Access-Control-Allow-Origin *;
        types { text/markdown md; }
        default_type text/plain;
    }

    # Sidebar — exact match to catch absolute path requests
    location = /_sidebar.md {
        root /usr/share/nginx/html;
        expires 5m;
    }

    location /health {
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
```

### Step 4: docker-compose.yml

```yaml
services:
  nginx-docsify:
    image: nginx:alpine
    container_name: study-docsify
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - /home/USER/Documents/docsify-site:/usr/share/nginx/html:ro
      - /home/USER/Documents/article:/articles:ro
      - /home/USER/Documents/docsify-site/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - /home/USER/Documents/docsify-site/logs:/var/log/nginx
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

**⚠️ Healthcheck note:** nginx:alpine may or may not have `curl`. Check with `docker exec <container> which curl`. If missing, use a different approach or install curl.

### Step 5: Auto-generating sidebar

The `generate_sidebar.py` script scans `~/Documents/article/` recursively:
- Each folder becomes a sidebar section
- Prioritizes `article_optimized.md` > `article_final.md` > `article_full.md` > first `.md`
- Lists sub-files under each folder
- Handles loose `.md` files at root level as "未分类文章"
- Outputs `_sidebar.md` in Docsify-compatible format

**README.md for homepage:** Must exist at the article root (mounted as `/articles/README.md`) because Docsify loads `homepage: 'README.md'` relative to `basePath: '/docs/'`.

### Step 6: File watcher for auto-updates

```python
# watch_sidebar.py — polls ~/Documents/article/ every 10 seconds
# Detects new/modified/deleted .md files → regenerates _sidebar.md
```

Install as systemd user service:
```ini
# ~/.config/systemd/user/docsify-watcher.service
[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/USER/Documents/docsify-site/watch_sidebar.py
Restart=always
RestartSec=30
```

Enable with:
```bash
systemctl --user enable --now docsify-watcher.service
```

## Phase 2: Cloudflare Tunnel

### Step 7: Add to existing tunnel

**CRITICAL PITFALL:** Cloudflare tunnels can be `source: cloudflare` (cloud-managed) or `source: local` (config.yml). If `source: cloudflare`, editing the local `config.yml` has NO EFFECT. You must update via the Cloudflare API.

**Check the config source:**
```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/cfd_tunnel/${TUNNEL_ID}/configurations" \
  -H "X-Auth-Email: ${EMAIL}" \
  -H "X-Auth-Key: ${API_KEY}" | python3 -c "
import json,sys
d=json.load(sys.stdin)
r=d.get('result',{})
print(f\"Source: {r.get('source')}\")
print(f\"Version: {r.get('version')}\")
"
```

### Step 8: Update cloud-managed ingress

When `source: cloudflare`, PUT the **entire** ingress array (not a partial update):

```bash
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/cfd_tunnel/${TUNNEL_ID}/configurations" \
  -H "X-Auth-Email: ${EMAIL}" \
  -H "X-Auth-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "ingress": [
        {"hostname": "existing.domain.com", "service": "http://localhost:3000"},
        {"hostname": "new.docs.domain.com", "service": "http://localhost:80"},
        {"service": "http_status:404"}
      ],
      "warp-routing": {"enabled": false}
    }
  }'
```

The tunnel auto-reloads within seconds. Check logs for `Updated to new configuration version=X`.

### Step 9: Create DNS CNAME

```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
  -H "X-Auth-Email: ${EMAIL}" \
  -H "X-Auth-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "CNAME",
    "name": "subdomain",
    "content": "TUNNEL_ID.cfargotunnel.com",
    "proxied": true,
    "ttl": 1
  }'
```

### Step 10: Edge propagation delay

After creating a new CNAME + tunnel hostname, Cloudflare edge nodes need 5-30 minutes to sync. During this window:
- Some edge IPs return 200, others fail TLS handshake
- DNS may resolve to a non-working edge (198.18.0.x range)
- Different networks (WiFi vs cellular) may hit different edges

**Verification:** Force-test against a known-working edge:
```bash
# Find a working edge IP (from another domain on same tunnel)
dig +short existing-working.domain.com
# e.g., returns 198.18.0.246

# Force-test new domain against that IP
curl --resolve new.domain.com:443:198.18.0.246 https://new.domain.com/health
```

## Self-Test Checklist

Before declaring done, verify ALL of these:

```bash
# 1. Local nginx
curl -s -o /dev/null -w "%{http_code}" http://localhost/health
curl -s -o /dev/null -w "%{http_code}" http://localhost/_sidebar.md

# 2. Article serving
curl -s -o /dev/null -w "%{http_code}" "http://localhost/docs/SOME_FOLDER/some_article.md"

# 3. Index HTML has correct loadSidebar config
curl -s http://localhost/ | grep "loadSidebar: '/_sidebar.md'"

# 4. Sidebar has content (not empty)
curl -s http://localhost/_sidebar.md | wc -l

# 5. Through tunnel (use --resolve if edge still syncing)
curl -s --resolve domain.com:443:WORKING_EDGE_IP -o /dev/null -w "%{http_code}" https://domain.com/

# 6. Watcher service
systemctl --user is-active docsify-watcher.service
```

## Tab Navigation with Dynamic Sidebar (Optional)

For top-level category tabs (e.g., 文章/课程/开源项目), each tab needs its own sidebar. Implement a Docsify plugin that detects the section from the URL and fetches per-section `_sidebar.md` files. Full implementation: `references/dynamic-sidebar-plugin.md`.

Key points:
- `_navbar.md` contains tab links with `data-section` attributes
- Plugin's `afterEach` hook fires on route changes, fetches appropriate sidebar via AJAX
- Sidebar generator must produce per-section `_sidebar.md` files (文章/_sidebar.md, 课程/_sidebar.md, etc.)
- Cache sidebar content client-side to avoid repeated fetches

## Pitfalls

1. **`loadSidebar` relative path**: Must be `'/_sidebar.md'`, never `'_sidebar.md'` when `basePath` is set
2. **`loadSidebar` absolute path trap**: Some Docsify versions break with `loadSidebar: '/_sidebar.md'` — test which convention your version uses
3. **Non-ASCII paths**: Chinese folder names must be URL-encoded in sidebar links, otherwise Docsify router throws `URIError`
4. **Cloud-managed tunnel config**: Local `config.yml` changes are silently ignored when `source: cloudflare`
5. **Edge propagation**: New CNAMEs take 5-30 min to work on all Cloudflare edges
6. **README.md placement**: Must be at article root (`/articles/README.md`) for Docsify homepage
7. **nginx:alpine healthcheck**: wget may not be installed; use curl or adjust Dockerfile
8. **OpenClash interference**: 198.18.0.x edge IPs may be affected by router DNS hijacking (see `cloudflare-tunnel-troubleshoot` skill)
9. **Docker volume symlinks**: Symlinks inside bind mounts point to host paths that don't exist inside the container. Always **copy** files, don't symlink, when the container needs to read them.

## Reference Files

- `references/dynamic-sidebar-plugin.md` — Docsify plugin for tabbed navigation with per-section sidebar switching
- `references/debugging-notes.md` — Cloudflare Tunnel config detection, 1Panel API key extraction, loadSidebar resolution quirk
- `references/generate_sidebar.py` — Alternative sidebar generator (recursive scan, URL-encode, per-section support)
- `scripts/generate_sidebar.py` — Existing sidebar generator script
2. **Cloud-managed tunnel config**: Local `config.yml` changes are silently ignored when `source: cloudflare`
3. **Edge propagation**: New CNAMEs take 5-30 min to work on all Cloudflare edges
4. **README.md placement**: Must be at article root (`/articles/README.md`) for Docsify homepage
5. **nginx:alpine healthcheck**: wget may not be installed; use curl or adjust Dockerfile
6. **OpenClash interference**: 198.18.0.x edge IPs may be affected by router DNS hijacking (see `cloudflare-tunnel-troubleshoot`)
