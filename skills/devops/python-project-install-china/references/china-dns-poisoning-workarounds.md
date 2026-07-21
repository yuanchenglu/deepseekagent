# China DNS Poisoning & Binary Download Workarounds

## The Problem

GFW DNS poisoning targets key GitHub/CDN domains, returning `127.0.0.1` or `::1`:

| Poisoned Domain | Real Service |
|---|---|
| `release-assets.githubusercontent.com` | GitHub Release CDN (Fastly) |
| `*.blob.core.windows.net` | Azure Blob Storage |
| `codeload.github.com` | GitHub archive downloads |
| `raw.githubusercontent.com` | Raw file access |

GitHub's `api.github.com` and `github.com` itself usually resolve correctly — the poisoning targets the CDN/storage subdomains used for actual file downloads.

## Detection

```bash
# Quick check — if it returns 127.0.0.1, it's poisoned
getent hosts release-assets.githubusercontent.com

# Compare DNS between machines
ssh other-machine "getent hosts release-assets.githubusercontent.com"

# Check if systemd-resolved cache has stale entries
resolvectl flush-caches
resolvectl query release-assets.githubusercontent.com
```

## Workaround 1: /etc/hosts with Real IPs

Find real IPs from a machine with clean DNS (VPS, Tailscale peer with different network):

```bash
# On clean-DNS machine
getent hosts release-assets.githubusercontent.com
# → 185.199.109.133, 185.199.108.133, 185.199.111.133, 185.199.110.133

# Apply on target machine
echo "185.199.111.133 release-assets.githubusercontent.com" | sudo tee -a /etc/hosts
echo "185.199.109.133 release-assets.githubusercontent.com" | sudo tee -a /etc/hosts
echo "185.199.108.133 release-assets.githubusercontent.com" | sudo tee -a /etc/hosts
```

**Limitations:**
- Fastly CDN IPs may rotate
- TLS SNI must match the hostname (curl/wget handle this, but some tools don't)
- GFW DPI may still reset large download connections (observed at 29% of 661MB download)
- Not reliable for files >200MB

## Workaround 2: Cross-Machine Download + Transfer

When local download is blocked but a peer machine has clean DNS:

```bash
# On clean-DNS peer: download
ssh peer "curl -L -o /tmp/file.zip '$ASSET_URL'"

# Serve via HTTP for transfer
ssh peer "cd /tmp && python3 -m http.server 8899"

# On target: download from peer
wget -O /tmp/file.zip "http://<peer-ip>:8899/file.zip"
```

Speed depends on interconnect:
- **Tailscale DERP relay**: ~350KB/s (550ms RTT, Hong Kong relay)
- **Direct LAN**: Gigabit speed
- **WireGuard direct**: Near-LAN speed

## Workaround 3: npm-Specific Tactics

```bash
# China npm mirror (required — official registry times out)
npm install --registry=https://registry.npmmirror.com

# Skip postinstall binary downloads, fetch manually later
CAMOFOX_SKIP_DOWNLOAD=1 npm install

# After fixing DNS, run the fetch
npx camoufox-js fetch
```

## Workaround 4: GitHub API Asset Download

When the CDN redirect is blocked but `api.github.com` resolves:

```bash
# 1. Get asset ID from releases API
curl -s "https://api.github.com/repos/OWNER/REPO/releases?per_page=3" \
  | python3 -c "import json,sys; ..."

# 2. Download via API (still redirects to CDN without auth)
curl -L -H "Accept: application/octet-stream" \
  "https://api.github.com/repos/OWNER/REPO/releases/assets/ASSET_ID" \
  -o output.zip

# Note: unauthenticated requests still redirect to release-assets.githubusercontent.com
# A GITHUB_TOKEN may enable direct streaming from api.github.com
```

## Mirrors Tested (June 2026)

| Mirror | Status |
|---|---|
| `ghproxy.com` | ❌ Connection reset |
| `gh-proxy.com` | ❌ Timeout |
| `mirror.ghproxy.com` | ❌ Timeout |
| `hub.fastgit.xyz` | ❌ Timeout |
| `download.fastgit.org` | ❌ Timeout |
| `registry.npmmirror.com` | ✅ Works for npm |
| `pypi.tuna.tsinghua.edu.cn` | ✅ Works for pip |

## Pitfall: Tailscale `file cp` is Push-Only

`tailscale file cp` CANNOT pull files FROM a remote machine. The syntax `tailscale file cp remote:/path local` fails because the target must end in `:`.

```bash
# WRONG — fails with "final argument must end in colon"
tailscale file cp bluth-aipc:/tmp/file.zip /tmp/

# CORRECT — SSH into remote and push to local
ssh bluth-aipc "tailscale file cp /tmp/file.zip bluth-thinkpad-e450c:"
```

However, Tailscale file transfers use Taildrop which requires desktop notification service on the receiver — often unreliable on headless Linux. **Prefer HTTP server + wget for DERP transfers.**

## Pitfall: Multi-Connection Downloaders (axel/aria2c) with Python SimpleHTTP

Python's `http.server` does NOT support HTTP Range requests by default. Download accelerators like `axel -n 10` will fail because they require byte-range support to open parallel connections.

```bash
# FAILS — axel needs range requests, Python SimpleHTTP doesn't support them
axel -n 10 http://peer:8899/file.zip

# WORKS — single-connection wget with TCP auto-tuning
wget -O output.zip http://peer:8899/file.zip
```

If multi-connection is needed, use nginx or a proper HTTP server on the source machine.

## Tailscale DERP Transfer Speed Reference

Real-world data point (June 2026, Hong Kong DERP relay, 445ms RTT):

| Metric | Value |
|---|---|
| File size | 661 MB |
| Transfer time | 30m56s |
| Average speed | 348 KB/s |
| Speed range | 50–500 KB/s (TCP ramp-up) |
| Protocol | HTTP (Python SimpleHTTP → wget) |

Throughput improves over time as TCP congestion window scales with high BDP.

## CamoFox-Specific: Manual Binary Setup

When `npx camoufox-js fetch` can't download (DNS blocked), you can manually extract the binary and create `version.json`:

```bash
# 1. Obtain the binary zip by any means (cross-machine transfer, etc.)
# 2. Extract to cache
mkdir -p ~/.cache/camoufox
cd ~/.cache/camoufox
unzip /tmp/camoufox-linux.zip

# 3. Create version.json (required by camofox-browser server)
#    Version info from the release tag: e.g., v150.0.2-beta.25
cat > ~/.cache/camoufox/version.json << 'EOF'
{"version": "150.0.2", "release": "alpha.26"}
EOF

# 4. Start the server
cd ~/Code/camofox-browser && node server.js
# → http://localhost:9377
```

**Note:** In Hermes profile sessions, `~` expands to the profile home (e.g., `~/.hermes/profiles/cto/home/`), not the real user home. Use absolute paths (`/home/$USER/.cache/...`) for system-level operations.

## Key Takeaway

For binary downloads from GitHub Releases in China, the most reliable path is:
1. Identify a machine with clean DNS (VPS, Tailscale peer on different ISP)
2. Download the binary there
3. Transfer via the fastest available interconnect (Tailscale DERP ~350KB/s, WireGuard direct ~gigabit)

Direct local download with /etc/hosts override works sporadically but fails on large files (>200MB) due to GFW DPI connection resets.
