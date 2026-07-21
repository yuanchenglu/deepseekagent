# Multi-Machine Hermes Config Verification (read-only)

Check that Hermes config (model, provider, reasoning) is consistent across all online Tailscale machines — the read-only companion to `multi-machine-deploy.md`.

## When To Use

- User asks "check that the config on machine X is the same as here"
- Before deploying config changes — verify the baseline first
- After deploying — verify the change landed correctly
- Cross-referencing a remote machine's provider/model against local `hermes status`

## Workflow

### 1. Know Your Current Config

```bash
# Local — shows model, provider, reasoning_effort
hermes status
```

Key fields to capture for comparison:
- **default model** (under "Model:" row)
- **provider** (under "Provider:" row, e.g. `custom:clawadmin`)
- **reasoning_effort** (from `agent.reasoning_effort` in config.yaml)

### 2. Find the Target Machine via Tailscale

```bash
# macOS: binary not in PATH, use full path
/Applications/Tailscale.app/Contents/MacOS/Tailscale up --accept-routes

# List all machines with IPs, names, and online status
/Applications/Tailscale.app/Contents/MacOS/Tailscale status
```

**Identifying machines by real-world description:**
- "联想笔记本" → look for hostnames containing `thinkpad` / `lenovo` / `e450`
- "AIPC" → `bluth-aipc`
- "MacBook" → `macbook-air` or `bluthmacbook-pro`

**Online markers:**
- `active; relay "xxx"` = online (behind NAT/relay)
- `active; direct xxx` = online (direct connection)
- `offline, last seen X ago` = skip, not reachable

### 3. Remote Config Extraction

Use a Python one-liner over SSH to extract only the comparison-relevant fields:

```bash
ssh bluth@<tailscale-ip> python3 -c '
import yaml
with open("/home/bluth/.hermes/config.yaml") as f:
    cfg = yaml.safe_load(f)
m = cfg.get("model", {})
a = cfg.get("agent", {})
r = cfg.get("reasoning", {})
cp = cfg.get("custom_providers", [])
print("default:", m.get("default"))
print("provider:", m.get("provider"))
print("base_url:", m.get("base_url"))
print("agent.reasoning_effort:", a.get("reasoning_effort"))
print("global_reasoning_effort:", r.get("effort"))
for p in cp:
    print("custom_provider:", p.get("name"))
    models_list = list(p.get("models", {}).keys()) if p.get("models") else []
    print("  models:", " ".join(models_list))
'
```

The `~` expansion doesn't work over SSH `-c` strings; use the absolute path `/home/<user>/.hermes/config.yaml`.

If the remote machine's Hermes binary isn't in SSH PATH (common with pipx installs), the `~/.hermes/config.yaml` path is still the reliable anchor — Hermes is installed if that file exists.

### 4. Build a Comparison Table

Compare the extracted fields against `hermes status` output from step 1:

| Field | Local | Remote | Match? |
|-------|-------|--------|--------|
| default model | deepseek-v4-flash | deepseek-v4-flash | ✅ |
| provider | custom:clawadmin | custom:clawadmin | ✅ |
| base_url | https://.../v1 | same | ✅ |
| reasoning_effort | xhigh | xhigh | ✅ |
| custom providers | clawadmin | clawadmin | ✅ |

Mismatches worth flagging:
- **provider name differs** → the remote won't use the same endpoint
- **reasoning_effort differs** → different thinking budget
- **base_url differs** → different endpoint (may still work, but worth flagging)
- **custom_providers model lists differ** → remote may not have all models available

### 5. Report Results

**All match** → state "配置完全一致" and list the confirmed fields.

**Mismatches found** → for each mismatch, show both values and a one-line remediation:
- `hermes config set model.default "<value>"` over SSH
- Or `python3 -c` block to patch the YAML (see `multi-machine-deploy.md` for the safe edit pattern)

## User Translation Table

Users may refer to machines / software differently than the hostname or config suggests:

| User says | What they mean |
|-----------|---------------|
| "Hams" | Hermes Agent (the user's nickname) |
| "联想笔记本" / "thinkpad" | `bluth-thinkpad-e450c` (100.108.145.79) |
| "AIPC" | `bluth-aipc` (100.89.88.88) |
| "Clawadmin" | The custom provider named `clawadmin` in `custom_providers` with base_url `https://token.clawadmin.org/v1` |
| "Max" / "最强推理" | `reasoning_effort: xhigh` or `agent.reasoning_effort: xhigh` |

## Pitfalls

- **Tailscale stopped**: `tailscale` CLI won't be in macOS PATH. Use absolute path `/Applications/Tailscale.app/Contents/MacOS/Tailscale` and run `up --accept-routes` first.
- **~ expansion fails over SSH**: Use absolute paths like `/home/bluth/.hermes/config.yaml`.
- **Config.yaml is user-specific**: The remote `bluth` user's config may differ from another user's. Always check who you SSH'd as.
- **Multiple Hermes profiles**: The machine may have `profiles/` subdirectories with separate configs. The default profile's config is at `~/.hermes/config.yaml`. To check a non-default profile, look at `~/.hermes/profiles/<name>/config.yaml`.
- **New API is separate**: New API (one-api/one-hub) is a proxy layer, not Hermes config. It has its own model/channel config via its Web UI (typically port 9090, may be localhost-only). Don't conflate the two.
