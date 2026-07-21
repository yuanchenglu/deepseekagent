# Multi-Machine Hermes Config Deployment (via Tailscale SSH)

Apply the same provider/model config across all online Tailscale machines.

## Workflow

### 1. Check Online Machines via Tailscale

```bash
# Start Tailscale if stopped
/Applications/Tailscale.app/Contents/MacOS/Tailscale up

# List all machines / check online status
/Applications/Tailscale.app/Contents/MacOS/Tailscale status
```

- **Online**: no "offline" or "last seen" suffix, or shows "active; relay ..."
- **Offline**: marked "offline, last seen X ago"
- Skip offline machines — they won't receive the update

> On macOS the binary lives at `/Applications/Tailscale.app/Contents/MacOS/Tailscale`.
> On Linux it's usually `/usr/bin/tailscale` or installed via apt/brew.

### 2. Test SSH Access

```bash
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 bluth@<tailscale-ip>
```

Tailscale IPs are in the `100.x.x.x` range. Verify:
- SSH key auth works
- The machine has a `~/.hermes/config.yaml` (Hermes installed)

### 3. Remote Config Update via Python YAML

Use Python's `yaml` module over SSH for safe structural edits — never use `sed` on complex nested YAML.

```python
# Template: edit_config_remote.py
import yaml, os

with open(os.path.expanduser("~/.hermes/config.yaml")) as f:
    cfg = yaml.safe_load(f)

# Backup
bak = os.path.expanduser("~/.hermes/config.yaml.bak-<tag>")
with open(bak, "w") as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

# Set model section with named custom provider
cfg["model"] = {
    "default": "<model-name>",
    "provider": "custom:<provider-name>",
    "base_url": "<endpoint-url>/v1",
    "api_key": "<api-key>",
}

# Set reasoning effort (both locations)
cfg["reasoning"] = {"effort": "xhigh"}
if "agent" not in cfg:
    cfg["agent"] = {}
cfg["agent"]["reasoning_effort"] = "xhigh"

# Set custom_providers with model definitions
cfg["custom_providers"] = [{
    "name": "<provider-name>",
    "base_url": "<endpoint-url>/v1",
    "api_key": "<api-key>",
    "model": "<model-name>",
    "models": {
        "<model-name>": {
            "name": "<model-name>",
            "context_length": 1000000
        }
    }
}]

# Clean up stale provider defs
if "providers" in cfg and not cfg["providers"]:
    del cfg["providers"]

with open(os.path.expanduser("~/.hermes/config.yaml"), "w") as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

print("Config updated. Backup:", bak)
```

Pipe it via SSH:

```bash
ssh bluth@<tailscale-ip> python3 -c '<python code above>'
```

> **Important**: Escape quotes properly when embedding Python in SSH. Use `-c '...'` with single quotes for the outer shell and double quotes inside Python.

### 4. Verify the Config

```python
import yaml
with open("~/.hermes/config.yaml") as f:
    cfg = yaml.safe_load(f)
m = cfg.get("model", {})
print("default:", m.get("default"))
print("provider:", m.get("provider"))
print("base_url:", m.get("base_url"))
a = cfg.get("agent", {})
print("reasoning_effort:", a.get("reasoning_effort"))
cp = cfg.get("custom_providers", [])
for p in cp:
    print("  custom_provider:", p.get("name"))
    print("  models:", list(p.get("models", {}).keys()))
```

### 5. Verify API Endpoint Works

```bash
curl -s -w "\nHTTP_CODE:%{http_code}" <base_url>/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <api-key>" \
  -d '{"model":"<model-name>","messages":[{"role":"user","content":"Say hi"}],"max_tokens":20}'
```

Expect `HTTP_CODE:200` with a valid response.

## Pitfalls

- **Tailscale stopped**: `.app` on macOS doesn't auto-start the CLI. Run `tailscale up` explicitly.
- **PATH issues**: Remote Linux may have `hermes` installed via pipx but not in default SSH PATH (`~/.local/bin`). Use full path or rely on `~/.hermes/config.yaml` existing as proof of installation.
- **One machine at a time**: Don't try to parallelize SSH config writes — if one fails mid-way, the error is easier to diagnose sequentially.
- **Backup first**: Always write a timestamped backup before modifying remote config, in case the edit leaves the config in an inconsistent state.
- **No restart needed**: Config changes take effect on next `hermes` session (`/new` or restart). No need to restart gateway for config-only changes.
