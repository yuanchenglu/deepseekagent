# Cloudflare Tunnel & Docsify Debugging Notes

## Cloudflare Tunnel Config: Local vs Cloud-Managed

When a tunnel was created through the Cloudflare Zero Trust dashboard, its config is stored on Cloudflare's side (`source: "cloudflare"`). The local `config.yml` file is **ignored**. Changes must go through the API.

### Detection

```bash
# Check where config lives
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/configurations" \
  -H "X-Auth-Email: $EMAIL" -H "X-Auth-Key: $KEY"
# Look for: "source": "cloudflare"
```

If local config edits don't take effect after tunnel restart, check this first.

### API-based config update

```bash
# PUT new config (must include ALL ingress rules, not just the new one)
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/configurations" \
  -H "X-Auth-Email: $EMAIL" -H "X-Auth-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"config": {"ingress": [...all rules...], "warp-routing": {"enabled": false}}}'
```

### Edge propagation delay

New CNAME→cfargotunnel.com records take 5-30 min for all edges. Test with:

```bash
# Find a working edge IP from another domain on the same tunnel
dig +short <existing-working-domain>
# Force test via that IP
curl --resolve <new-domain>:443:<working-ip> https://<new-domain>/health
```

## 1Panel API Key Extraction

```bash
# Get API key from SQLite
sudo sqlite3 /opt/1panel/db/core.db "SELECT value FROM settings WHERE key='ApiKey';"
# Enable API if disabled
sudo sqlite3 /opt/1panel/db/core.db "UPDATE settings SET value='Enable' WHERE key='ApiInterfaceStatus';"
# Restart 1Panel core
sudo 1pctl restart core
```

API port: check with `ss -tlnp | grep 1panel-core` (often 27930).

## Docsify: loadSidebar Resolution

Docsify resolves `loadSidebar` relative to `basePath`, not the page URL:

- `basePath: '/docs/'` + `loadSidebar: '_sidebar.md'` → requests `/docs/_sidebar.md`
- `basePath: '/docs/'` + `loadSidebar: '/_sidebar.md'` → **BROKEN**: Docsify treats `/` prefix as a URL, resulting in `https://_sidebar.md/`

**Correct pattern**: use relative path in `loadSidebar` and ensure the file exists at the resolved path under `basePath`.

## Docker Volume Mounts & Symlinks

Symlinks inside a Docker bind mount point to paths on the **host** filesystem. Those paths don't exist inside the container. Always **copy** files rather than symlinking when the container needs to read them.

nginx `alias` directive resolves symlinks — a dangling symlink inside the container means a 404 even if the file exists on the host.
