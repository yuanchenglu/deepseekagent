# Cloudflare Deployment Guide — DeepAgent Website

All commands assume:
- `wrangler` is installed (`npm i -g wrangler` or `npx wrangler`)
- Authenticated: `wrangler login` (or `CF_API_TOKEN` env var set)
- Working directory: repo root (where `website/`, `landingpage/`, `scripts/` live)
- Placeholder values are marked `<LIKE_THIS>` — replace before running.

---

## 0. Prerequisites

```bash
# Install wrangler if not present
npm install -g wrangler

# Authenticate
wrangler login

# Verify auth
wrangler whoami
# Expected: output showing your account email + Account ID
```

Verify:
```bash
wrangler whoami | grep -E 'Account ID|Email' | head -2
```

---

## 1. Create R2 Bucket

```bash
# Create the releases bucket
wrangler r2 bucket create deepagent-releases

# Verify bucket exists
wrangler r2 bucket list | grep deepagent-releases
# Expected: deepagent-releases listed
```

### 1a. Enable public access on the R2 bucket (custom domain for releases)

```bash
# Set R2_PUBLIC_URL to your releases subdomain in wrangler.toml vars
# Already configured as: https://releases.deepseekagent.starseas.org

# Add custom domain to R2 bucket (requires DNS on Cloudflare)
wrangler r2 bucket add-custom-domain deepagent-releases releases.deepseekagent.starseas.org
```

Verify:
```bash
curl -sI https://releases.deepseekagent.starseas.org/ | head -1
# Expected: HTTP/2 404 (bucket exists, file not found at root)
# Or HTTP/2 200 after first upload
```

### 1b. Upload initial install.sh to R2 (optional, for testing)

```bash
# After building a release, upload install.sh
# wrangler r2 object put deepagent-releases/v<VERSION>/install.sh --file scripts/install.sh
# Example:
echo '#!/bin/sh\necho "DeepAgent installer"' | wrangler r2 object put deepagent-releases/v0.9.0/install.sh --file -
```

Verify:
```bash
curl -sI https://releases.deepseekagent.starseas.org/v0.9.0/install.sh | head -1
# Expected: HTTP/2 200
```

---

## 2. Build the Website

```bash
# Run the build script
bash scripts/build-website.sh
```

Verify:
```bash
# Check build output exists
ls -la website/build/index.html
ls -la website/build/_redirects
ls -la website/build/install.sh 2>/dev/null; echo "(install.sh served by Pages Function, not static file)"

# Verify no brand leaks
grep -rci 'hermes\|nous' website/build/index.html website/build/style.css website/build/script.js
# Expected: all lines show :0
```

---

## 3. Create Pages Project & Deploy

```bash
cd website

# Deploy to Pages (creates project on first run)
npx wrangler pages deploy build --project-name=deepagent-website --branch=main
```

Verify:
```bash
# List Pages projects
npx wrangler pages project list | grep deepagent-website
# Expected: deepagent-website listed

# Get the pages.dev URL
npx wrangler pages deployment list --project-name=deepagent-website | head -5
# Expected: deployment URL shown (e.g., https://<hash>.deepagent-website.pages.dev)
```

Test the deployment:
```bash
PAGES_URL=$(npx wrangler pages deployment list --project-name=deepagent-website 2>/dev/null | grep -oE 'https://[a-f0-9]+\.deepagent-website\.pages\.dev' | head -1)
echo "Testing $PAGES_URL"

# 1. Landing page loads
curl -sI "$PAGES_URL/" | head -1
# Expected: HTTP/2 200

# 2. install.sh endpoint works (302 redirect)
curl -sI "$PAGES_URL/install.sh" | head -1
# Expected: HTTP/2 302

# 3. /latest returns JSON
curl -s "$PAGES_URL/latest"
# Expected: {"version":"0.9.0"} or a real version from GitHub API

# 4. /download redirects to /download/
curl -sI "$PAGES_URL/download" | head -1
# Expected: HTTP/2 301
```

---

## 4. Configure R2 Binding & Secrets

```bash
cd website

# Set R2 bucket binding (already in wrangler.toml, but verify)
# wrangler.toml should contain:
#   [[r2_buckets]]
#   binding = "RELEASES"
#   bucket_name = "deepagent-releases"

# Deploy with binding (wrangler.toml includes it, this picks it up)
npx wrangler pages deploy build --project-name=deepagent-website --branch=main

# Set R2_PUBLIC_URL as a Pages environment variable (secret-like, non-sensitive)
npx wrangler pages secret put R2_PUBLIC_URL --project-name=deepagent-website --production <<<"https://releases.deepseekagent.starseas.org"
```

Verify:
```bash
# After deployment, test install.sh redirect points to R2
curl -sI "$PAGES_URL/install.sh" | grep -i location
# Expected: location: https://releases.deepseekagent.starseas.org/v<VERSION>/install.sh
```

---

## 5. Custom Domain (deepseekagent.starseas.org)

```bash
# Add custom domain to the Pages project
npx wrangler pages domain add deepagent-website deepseekagent.starseas.org

# If DNS is NOT already on Cloudflare, add these records at your DNS provider:
#   Type: CNAME
#   Name: deepseekagent.starseas.org (or @ for apex)
#   Value: deepagent-website.pages.dev
#   Proxy: ON (orange cloud)
```

Verify:
```bash
# Wait 2-5 minutes for DNS propagation, then:
curl -sI https://deepseekagent.starseas.org/ | head -1
# Expected: HTTP/2 200

curl -sI https://deepseekagent.starseas.org/install.sh | head -1
# Expected: HTTP/2 302

curl -s https://deepseekagent.starseas.org/latest
# Expected: {"version":"<version>"}
```

### 5a. DNS records summary

If managing DNS manually, add these records:

| Type | Name                        | Value                        | Proxy |
|------|-----------------------------|------------------------------|-------|
| CNAME| deepseekagent.starseas.org  | deepagent-website.pages.dev  | On    |
| CNAME| releases.deepseekagent.starseas.org | (R2 custom domain, auto-managed by Cloudflare) | On |

Verify:
```bash
dig deepseekagent.starseas.org +short
# Expected: Cloudflare IP(s)

dig releases.deepseekagent.starseas.org +short
# Expected: Cloudflare IP(s)
```

---

## 6. CI/CD (Optional — GitHub Actions)

Create `.github/workflows/deploy-website.yml`:

```yaml
name: Deploy Website
on:
  push:
    branches: [main]
    paths:
      - 'landingpage/**'
      - 'website/**'
      - 'scripts/build-website.sh'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm install -g wrangler
      - run: bash scripts/build-website.sh
      - name: Deploy to Cloudflare Pages
        working-directory: website
        run: npx wrangler pages deploy build --project-name=deepagent-website --branch=main
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
```

---

## 7. End-to-End Verification Checklist

Run these after full deployment:

```bash
DOMAIN="https://deepseekagent.starseas.org"

echo "=== 1. Landing page ==="
curl -sI "$DOMAIN/" | head -1                          # 200
curl -s "$DOMAIN/" | grep -c '7ColorAI'                # >=1
curl -s "$DOMAIN/" | grep -ci 'hermes\|nous'           # 0
curl -s "$DOMAIN/" | grep -c 'curl -fsSL'              # >=1
curl -s "$DOMAIN/" | grep -c 'Apple Silicon'           # >=1
curl -s "$DOMAIN/" | grep -c 'Intel Mac'               # >=1

echo "=== 2. install.sh ==="
curl -sI "$DOMAIN/install.sh" | head -1                # 302
curl -sI "$DOMAIN/install.sh?version=0.9.0" | grep -i location

echo "=== 3. /latest ==="
curl -s "$DOMAIN/latest"                               # {"version":"..."}

echo "=== 4. /download ==="
curl -sI "$DOMAIN/download" | head -1                  # 301

echo "=== 5. Releases ==="
curl -sI "$DOMAIN/releases/" | head -1                 # 302 to R2

echo "=== 6. Docs ==="
curl -sI "$DOMAIN/docs/" | head -1                     # 200

echo "=== All checks passed ==="
```

---

## 8. Rollback

If a deployment breaks:

```bash
# List deployments
npx wrangler pages deployment list --project-name=deepagent-website

# Rollback to a previous deployment (by ID)
npx wrangler pages deployment rollback --project-name=deepagent-website <DEPLOYMENT_ID>
```

---

## File Reference

| File | Purpose |
|------|---------|
| `website/wrangler.toml` | Pages project config (name, R2 binding, vars) |
| `website/functions/install.sh.js` | Pages Function for /install.sh (version resolution + 302) |
| `website/functions/latest.json.js` | Pages Function for /latest (version JSON) |
| `website/static/_redirects` | Cloudflare Pages redirect rules |
| `scripts/build-website.sh` | Build script (Docusaurus + landing page merge) |
| `landingpage/` | Landing page source (HTML/CSS/JS + assets) |
| `website/docs/` | Docusaurus markdown docs |
