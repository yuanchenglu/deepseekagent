---
name: multi-machine-config-sync
description: >-
  Sync model/provider configs across multiple machines via Tailscale SSH.
  Field-level replacement — replaces only model-related fields while preserving
  machine-specific settings (CORS, MCP, plugins, env). Gear/tier system for
  organizing model configurations. Supports Hermes + OpenCode + OMO.
version: 1.0.0
platforms: [linux, macos]
---

# Multi-Machine Config Sync

> Companion to `hermes-config-management` — extends it with field-level replacement
> and multi-app (Hermes + OpenCode + OMO) support.

## Critical Insight: Not All Config Fields Are Portable

Configuration files mix **shared** (model/provider) and **machine-specific** (CORS, MCP)
fields. Whole-file copy destroys machine-specific parts. Use **field-level replacement**
instead: read → parse → replace model fields only → write back.

### Field Classification

| Category | Examples | Portable? |
|----------|----------|-----------|
| **Model config** | `model.default`, `model.provider`, agent `variant` | ✅ Yes |
| **OMO agent models** | `agents.sisyphus.model`, `categories.deep.model` | ✅ Yes |
| **API keys** | `.env` file lines | ✅ Independent |
| **CORS/server** | `server.cors` (domains per-machine) | ❌ No |
| **MCP credentials** | `mcp.lark.command`, `mcp.lark.environment` | ❌ No |
| **Plugin list** | `plugin` array (may differ per-machine) | ❌ Check |
| **Instructions** | `instructions` array (file paths) | ❌ No |
| **Watcher** | `watcher.ignore` (paths per-project) | ❌ No |

## Three Independent Dimensions

Never conflate these. A gear switch changes only (1), never (2) or (3).

```
① GEAR — model config (what model to use)
② API KEYS — credentials (can the provider authenticate)
③ MACHINE IDENTITY — CORS, MCP, plugins, paths (per-machine)
```

## Gear/Tier System

Organize model configurations into named gears. Each gear has a free-text description
explaining when to use it. Users can add, duplicate, rename, delete gears.

### Two-Initial-Gear Example

**Gear 1 (高效性价比)** — All agents use `opencode-go/deepseek-v4-flash`, variant=max.
Use for everyday tasks, quick coding, and cost efficiency.

**Gear 2 (混合性能)** — The orchestration/planning/reasoning agents
(Sisyphus, Hephaestus, Oracle, Prometheus, ultrabrain category) use
`opencode-go/deepseek-v4-pro`, variant=max. All other agents use
`opencode-go/deepseek-v4-flash`, variant=max.
Use for complex multi-file changes and deep reasoning.

Extra gears can be added: Gear 3 (最强推理, add glm-5 fallback), etc.
Users copy an existing gear and tweak individual agent models.

## Per-App Field Replacement Guide

### Hermes — `~/.hermes/config.yaml`

```yaml
# SAFE to replace (model config):
model:
  default: <model-name>
  provider: <provider-name>
agent:
  reasoning_effort: xhigh

# NEVER touch (machine-specific):
#   mcp.*, feishu/telegram/discord keys, web.*, cron.*,
#   skills.external_dirs, display.*, privacy.*, security.*
```

Hot-reload: ✅ Next `/new` session picks up changes. No restart needed.

Python replacement via SSH:
```python
python3 -c "
import yaml
with open('$HOME/.hermes/config.yaml') as f:
    c = yaml.safe_load(f)
c['model'] = {'default': 'deepseek-v4-flash', 'provider': 'opencode-go'}
c['agent']['reasoning_effort'] = 'xhigh'
with open('$HOME/.hermes/config.yaml', 'w') as f:
    yaml.dump(c, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
print('Hermes model config updated')
"
```

### OpenCode — `~/.config/opencode/opencode.json`

```json
// SAFE to replace:
{
  "model": "opencode-go/deepseek-v4-flash",
  "provider": {
    "opencode-go": {
      "models": {
        "deepseek-v4-flash": { "name": "DeepSeek V4 Flash", "reasoning": true,
          "variants": { "max": {"disabled": false} } },
        "deepseek-v4-pro": { "name": "DeepSeek V4 Pro", "reasoning": true,
          "variants": { "max": {"disabled": false} } }
      }
    }
  }
}

// NEVER touch:
//   server.cors, mcp.*, plugin[], watcher.ignore, instructions[], disabled_providers[]
```

Hot-reload: ❌ Requires `opencode serve` restart.
Workaround: Use `--model` flag per-call (`opencode run --model opencode-go/deepseek-v4-pro`).

Python replacement via SSH:
```python
python3 -c "
import json
with open('$HOME/.config/opencode/opencode.json') as f:
    c = json.load(f)
c['model'] = 'opencode-go/deepseek-v4-flash'
c['provider']['opencode-go']['models'] = {
    'deepseek-v4-flash': {'name': 'DeepSeek V4 Flash', 'reasoning': True,
        'variants': {'max': {'disabled': False}}},
    'deepseek-v4-pro': {'name': 'DeepSeek V4 Pro', 'reasoning': True,
        'variants': {'max': {'disabled': False}}}
}
with open('$HOME/.config/opencode/opencode.json', 'w') as f:
    json.dump(c, f, indent=2, ensure_ascii=False)
print('OpenCode model config updated')
"
```

### OMO — `~/.config/opencode/oh-my-openagent.json`

**Exception**: This file contains ONLY model configuration. Whole-file copy is safe.

```json
{
  "agents": {
    "sisyphus": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "prometheus": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "atlas": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "hephaestus": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "oracle": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "explore": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "librarian": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "multimodal-looker": {"model": "opencode-go/mimo-v2.5"},
    "metis": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "momus": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "sisyphus-junior": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"}
  },
  "categories": {
    "visual-engineering": {"model": "opencode-go/mimo-v2.5", "variant": "max"},
    "ultrabrain": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "deep": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "quick": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "writing": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "unspecified-high": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "unspecified-low": {"model": "opencode-go/deepseek-v4-flash", "variant": "max"},
    "artistry": {"model": "opencode-go/mimo-v2.5", "variant": "max"}
  }
}
```

Hot-reload: ❌ Requires OpenCode restart (OMO config loaded at plugin startup).

## .env Key Replacement (Independent)

API keys are a separate dimension from model config. Replace them when keys expire,
without changing the active gear.

```bash
# Hermes .env
ssh user@machine "sed -i '' 's/^OPENCODE_GO_API_KEY=.*/OPENCODE_GO_API_KEY=sk-new-key/' ~/.hermes/.env"

# OpenCode .env (may not exist — keys can be inline in opencode.json)
ssh user@machine "sed -i '' 's/^OPENCODE_GO_API_KEY=.*/OPENCODE_GO_API_KEY=sk-new-key/' ~/.config/opencode/.env"
```

⚠️ Always use `sed -i` for line-level replace. Never `>` overwrite .env.

## SSH Restart Commands

After replacing OpenCode config:

| Platform | Command |
|----------|---------|
| **Linux (systemd)** | `sudo systemctl restart opencode-web-4096` |
| **macOS (launchctl)** | `launchctl stop com.opencode.server && launchctl start com.opencode.server` |
| **Docker** | `docker restart opencode-server` |

Hermes config does NOT need restart (hot-loaded).

## Homeserver Backend Architecture

For a central management panel running on one machine (e.g. 联想笔记本):

### Template Storage

```
config-templates/
├── hermes/           # Per-gear YAML templates (model fields only)
├── opencode/         # Per-gear JSON templates (model + provider.models)
└── omo/              # Per-gear JSON templates (whole-file safe)
```

Templates contain ONLY the model-related fields that are safe to replace.
Templates are uploaded via the management UI and stored as files.

### Backend API

```
GET  /api/devices           → list managed devices (name, IP, SSH user, online status)
POST /api/devices           → add a device
DELETE /api/devices/:id     → remove a device

GET  /api/templates/:app    → list templates for an app
POST /api/templates/:app    → upload a new template
DELETE /api/templates/:app/:gear → delete a template

POST /api/deploy            → deploy: {device_id, app, gear, restart_opencode?: bool}
                              Returns SSE stream with progress events.

GET  /api/keys/:device      → list API keys on remote .env
POST /api/keys/:device      → replace a specific key
```

### Deploy Flow (SSE stream)

```
Step 1: 检查设备在线
Step 2: 读取远程当前配置
Step 3: 备份 (.bak-timestamp)
Step 4: 字段级替换模型配置
Step 5: 写回
Step 6: 重启 OpenCode (if app = opencode or omo)
Step 7: 验证
```

## Cross-Machine Hermes Audit (Skills + Memory + DB)

Use this when you need to compare/consolidate Hermes installations across machines — pre-migration reconnaissance, setting up a central node, or verifying backup completeness.

### Pre-Audit: Check Online Machines

```bash
tailscale status
# Only lines WITHOUT "offline" are reachable
```

### Username Discovery (Critical First Step)

SSH usernames differ by machine. Don't assume your current username works:

```bash
for user in bluth ycl_pj root admin; do
  ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 \
    -o NumberOfPasswordPrompts=0 "$user@100.89.88.88" "hostname" 2>&1 || true
done
```

### Minimal Audit Checklist Per Machine

```bash
hostname

# Hermes version
command -v hermes 2>/dev/null && hermes --version || echo "no hermes in PATH"
~/.local/bin/hermes --version 2>/dev/null  # pipx fallback

# Skills count
echo "~/.hermes/skills: $(ls -1 ~/.hermes/skills/ 2>/dev/null | wc -l)"

# .agents/skills centralized dir
ls -d ~/.agents/skills/ 2>/dev/null && \
  echo ".agents/skills: $(ls -1 ~/.agents/skills/ 2>/dev/null | wc -l)" || \
  echo ".agents/skills does not exist"

# Symlink relationship
find ~/.hermes/skills -type l 2>/dev/null | while read link; do
  echo "SYMLINK: $(basename "$(dirname "$link")") -> $(readlink "$link")"
done

# state.db
ls -lh ~/.hermes/state.db 2>/dev/null

# Memories
ls ~/.hermes/memories/*.md 2>/dev/null | while read f; do
  echo "$(basename "$f"): $(wc -c < "$f") bytes"
done

# Profiles & Cron
ls ~/.hermes/profiles/ 2>/dev/null || echo "no profiles"
ls ~/.hermes/cron/jobs.json 2>/dev/null && echo "cron: $(wc -c < ~/.hermes/cron/jobs.json) bytes"
```

### Skill Modification Times

**macOS** (stat -f %m):
```bash
cd ~/.hermes/skills && for d in */; do
  echo "$(date -r "$(stat -f '%m' "$d")" '+%Y-%m-%d %H:%M')  ${d%/}"
done | sort
```

**Linux** (stat -c %Y):
```bash
cd ~/.hermes/skills && for d in */; do
  echo "$(date -d "@$(stat -c '%Y' "$d")" '+%Y-%m-%d %H:%M')  ${d%/}"
done | sort
```

### `.agents/skills` Centralized Pattern Audit

Check whether the desired architecture (skills in `~/.agents/skills/`, symlinked from `~/.hermes/skills/`) is implemented:

```bash
# Skills in BOTH places - which are symlinked vs independent copies?
for skill in $(comm -12 <(ls ~/.hermes/skills/ | sort) <(ls ~/.agents/skills/ | sort)); do
  readlink ~/.hermes/skills/$skill 2>/dev/null || echo "$skill: independent copy"
done

# Symlink coverage
total=$(ls -1 ~/.hermes/skills/ | wc -l)
linked=$(find ~/.hermes/skills -type l | wc -l)
echo "Symlinked: $linked/$total"
```

## Pitfalls

- **OpenCode config change requires restart** — unlike Hermes, `opencode serve` caches
  config at startup. Plan for a brief service interruption.
- **No LLM dependency** — deployment must work even when all API keys are expired.
  The SSH+Python approach uses no external APIs.
- **OMO file is the only one safe for whole-file copy** — all other config files
  contain machine-specific fields.
- **macOS vs Linux paths differ** — `~/.config/opencode/opencode.json` same on both,
  but restart commands and .env locations vary.
- **User's homeserver project** — if implementing as a web panel, the project lives at
  `~/Code/homeservers/` (FastAPI + vanilla HTML). The current implementation attempts
  dynamic config building (buggy); replace with template-based field-level replacement.
