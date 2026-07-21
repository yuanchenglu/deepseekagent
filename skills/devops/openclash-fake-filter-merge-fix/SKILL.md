---
name: openclash-fake-filter-merge-fix
description: Fix OpenClash custom fake-ip-filter rules not being merged into running Clash config. When argotunnel.com or other domains still resolve to 198.18.x.x after adding rules to openclash_custom_fake_filter.list, the merge mechanism failed — inject rules directly into the running config.
triggers:
  - "cloudflared 1033"
  - "argotunnel 198.18"
  - "openclash fake-ip-filter not working"
  - "custom fake filter list not merged"
  - "tailscale 100.64 blocked by clash"
  - "cloudflare tunnel intermittent"
  - "opencode.ai connection reset"
  - "newapi upstream error do request failed"
  - "ai api behind openclash intermittent failure"
---

# OpenClash Fake-IP-Filter Merge Fix

## Problem Pattern (Recurring)

OpenClash's custom fake-ip-filter list (`/etc/openclash/custom/openclash_custom_fake_filter.list`) contains correct bypass rules, but they are **NOT merged** into the running Clash config (`/etc/openclash/Clash_*.yaml`). The running config's `fake-ip-filter` section only has default entries (e.g., `geosite:cn`), ignoring all custom additions.

**This has happened multiple times.** The root cause is OpenClash's config generation/merge mechanism failing silently.

## Symptoms

- `dig region1.v2.argotunnel.com` returns `198.18.x.x` (Fake-IP) instead of `198.41.x.x` (real Cloudflare)
- cloudflared logs show `ip=198.18.0.x` and `timeout: no recent network activity`
- Cloudflare Tunnel returns Error 1033 on all domains
- Rules exist in custom list but `grep argo /etc/openclash/Clash_*.yaml` returns nothing
- AI API calls (e.g., `opencode.ai` via NewAPI) intermittently fail with `connection reset by peer` or `EOF`
- NewAPI health monitor reports `upstream error: do request failed` for channels pointing to `opencode.ai`

## Diagnosis

```bash
ssh root@192.168.2.1

# 1. Check if rules exist in custom list
grep -n "argo\|cfargo" /etc/openclash/custom/openclash_custom_fake_filter.list

# 2. Check if they're in the RUNNING config (this is the real test)
RUNNING=$(ls -t /etc/openclash/config/Clash_*.yaml | head -1)
grep -A20 "fake-ip-filter" "$RUNNING"

# 3. If running config only has "geosite:cn" — merge failed
```

## Fix (Two Steps)

### Step 1: Inject into running config

```bash
ssh root@192.168.2.1

RUNNING=$(ls -t /etc/openclash/config/Clash_*.yaml | head -1)

# Add after the "fake-ip-filter:" line (before geosite:cn)
sed -i "/fake-ip-filter:/a\\\\  - \\\"+.argotunnel.com\\\"\\n  - \\\"+.cfargotunnel.com\\\"\\n  - \\\"100.64.0.0/10\\\"\\n  - \\\"+.opencode.ai\\\"\\n  - \\\"+.openai.com\\\"\\n  - \\\"+.anthropic.com\\\"\" \"$RUNNING\"

# Verify
grep -A6 "fake-ip-filter" "$RUNNING"

# ⚠️ RESTART required — SIGHUP is NOT sufficient for fake-ip-filter to take effect.
# kill -HUP will NOT make DNS return real IPs; a full restart is needed.
/etc/init.d/openclash restart
sleep 8

# Verify DNS resolves to real IPs
nslookup region1.v2.argotunnel.com
# Should show 198.41.x.x, NOT 198.18.x.x
```

If the running config has NO `fake-ip-filter` section at all, you must add one under the `dns:` block:

```bash
RUNNING=$(ls -t /etc/openclash/config/Clash_*.yaml 2>/dev/null | head -1)

# Add fake-ip-filter section after fake-ip-range line
sed -i '/fake-ip-range:/a\\\\  fake-ip-filter:\\n  - \\\"+.opencode.ai\\\"\\n  - \\\"+.token.clawadmin.org\\\"' "$RUNNING"

# Then full restart
/etc/init.d/openclash restart
sleep 8

# Verify
sed -n '/fake-ip-filter/,/use-hosts/p' "$RUNNING"
dig +short opencode.ai  # should show real IP, not 198.18.x.x
```

### Step 2: Restart cloudflared on client machine

```bash
# On the machine running cloudflared (e.g., bluth-ThinkPad-E450c)
sudo resolvectl flush-caches
sudo systemctl restart cloudflared-hermes

# Verify real IPs in logs
journalctl -u cloudflared-hermes -n 10 --since "5s ago" | grep "ip=198.41"
```

### Step 3: Ensure persistence in custom list

```bash
# Verify custom list has the rules (for next OpenClash restart)
grep "argo\|cfargo\|100.64" /etc/openclash/custom/openclash_custom_fake_filter.list
```

## Related Skills

- `openclash-whitelist-manager` — Broader OpenClash GFW whitelist strategy: MATCH rule modification, domain-level DIRECT rules, and the full diagnostic flow for determining whether traffic is incorrectly routed through the proxy.

### Domain Rules (Fake-IP bypass)

```
+.argotunnel.com      # Cloudflare Tunnel edge nodes (multi-level subdomains)
+.cfargotunnel.com    # Cloudflare Tunnel CNAME targets
+.opencode.ai         # AI API upstream — proxy causes intermittent TCP resets/EOF
+.token.clawadmin.org # Self-hosted NewAPI gateway — direct for stability
+.openai.com          # OpenAI API — bypass for stable AI API access
+.anthropic.com       # Anthropic API — bypass for stable AI API access
+.github.com          # Code hosting — direct for reliable git operations
```

### CIDR Rules (IP range bypass)

```
100.64.0.0/10         # Tailscale CGNAT range (DIRECT, no proxy)
```

### Principle

Any AI API / upstream service running behind OpenClash should bypass the proxy when:
- The service is **not blocked/restricted** in the local region (i.e., not on GFW list)
- The proxy server adds latency or causes intermittent TCP failures (reset/EOF)
- Stable, direct connections are preferred over proxied routes

When diagnosing NewAPI `upstream error: do request failed` errors:
1. Check DNS → if `dig +short <domain>` returns `198.18.x.x`, it's being intercepted
2. Compare direct vs proxy path (see `new-api-admin` skill for the diagnostic flow)
3. Add the domain to this list if direct access resolves the issue

## Why This Happens

OpenClash generates the running Clash config from a template + custom overrides. The `openclash_custom_fake_filter.list` is supposed to be merged into the `fake-ip-filter` section, but the merge script (`openclash_custom_overwrite.sh`) doesn't reference fake-ip-filter, so custom entries are silently dropped.

**The fix is always the same**: manually inject into running config + ensure custom list has entries for next restart.

## Verification Checklist

After fix, verify ALL of these:

```bash
# 1. DNS resolves to real IPs (from any machine on network)
dig +short region1.v2.argotunnel.com  # → 198.41.x.x
dig +short cfargotunnel.com           # → 198.41.x.x
dig +short opencode.ai                # → 172.x.x.x (NOT 198.18.x.x)

# 2. cloudflared connects to real IPs
journalctl -u cloudflared-hermes -n 5 | grep "Registered tunnel"
# → ip=198.41.x.x (NOT 198.18.x.x)

# 3. Tailscale works
tailscale status  # → nodes reachable

# 4. Cloudflare Tunnel domains respond
curl -sI https://file-tech.skysea.uk/ --max-time 5
# → 302 (Access login) or 200 (service)

# 5. AI API upstream works without proxy interference
curl -s -o /dev/null -w "HTTP %{http_code}" --max-time 10 https://opencode.ai/zen/go/v1/chat/completions
# → 404 (expected — path needs model endpoint; no Fake-IP error)
```
