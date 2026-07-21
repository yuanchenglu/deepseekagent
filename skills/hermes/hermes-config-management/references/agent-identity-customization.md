# Agent Identity Customization — Full Rebranding Checklist

When you fork Hermes Agent (or any agent platform built on it) and need to
change **every surface** where the original brand name/creator appears, use
this checklist. Missing even one surface leaves stale branding artifacts.

## Runtime Identity (Immediate Effect)

| File | What to Change | Effect |
|------|---------------|--------|
| `~/.config/SOUL.md` or `~/.hermes/SOUL.md` | The agent's self-introduction | Agent's answer to "who are you" |
| `~/.config/config.yaml` → `personalities` | noir/pirate persona text | Only if those personas are used |

## Source Code — Default Template

| File | What to Change |
|------|---------------|
| `hermes_cli/default_soul.py` | SOUL.md template seeded on first run |

## TUI / CLI — Startup Banner & Status Bar

| File | Lines | What to Change |
|------|-------|---------------|
| `hermes_cli/banner.py` | ~243 | Startup title: `f"OldName v{...}"` |
| `hermes_cli/banner.py` | ~380 | Status bar: `"OldCreator"` after model name |
| `hermes_cli/banner.py` | ~519 | Skin fallback: `_skin_branding("agent_name", "OldName")` |
| `hermes_cli/skin_engine.py` | ~59,84,180,275,306,343,380 | Default skin agent_name for all built-in skins |

## Web UI

| File | What to Change |
|------|---------------|
| `web/src/i18n/en.ts` | `brand`, `brandShort`, `footer.name`, `footer.org` |
| `web/src/i18n/zh.ts` | Same fields in Chinese |
| `web/src/index.css` | CSS comments referencing old brand |
| `hermes_cli/web_dist/index.html` | HTML `<title>` |

## CLI — Help Text, Status, Version

| File | What to Change |
|------|---------------|
| `hermes_cli/main.py` | ~25+ argparse `description=` and `help=` strings |
| `hermes_cli/status.py` | Status command header + docstrings |
| `hermes_cli/commands.py` | Docstring + CommandDef descriptions |
| `hermes_cli/setup.py` | Setup wizard header text |
| `hermes_cli/uninstall.py` | Uninstaller header + thank-you message |
| `hermes_cli/completion.py` | Shell completion comments |
| `hermes_cli/debug.py` | Module docstring |

## Service & Integration Names

| File | What to Change |
|------|---------------|
| `hermes_cli/web_server.py` | FastAPI `title=` |
| `hermes_cli/gateway.py` | `SERVICE_DESCRIPTION` |
| `tools/send_message_tool.py` | Email `Subject` |
| `tools/mcp_oauth.py` | OAuth `client_name` default + fallback |
| `agent/copilot_acp_client.py` | ACP `"title"` |
| `run_agent.py` + `agent/auxiliary_client.py` | `X-OpenRouter-Title` header |

## API & HTTP Headers

| File | What to Change |
|------|---------------|
| `tools/cronjob_tools.py` | Module docstring |
| `tools/environments/local.py` | Error messages |

## All Module Docstrings

When thorough, batch-replace the docstring in every `hermes_cli/` and `tools/`
Python file that starts with `"X for Hermes Agent."`:

- `config.py`, `skills_config.py`, `platforms.py`, `auth.py`, `providers.py`
- `__init__.py`, `tools_config.py`, `debug.py`, `gateway.py`, `web_server.py`

## Tests

All test assertions that check for the old brand name will fail. Batch-replace:

```
# In test_skin_engine.py, test_prompt_builder.py, test_run_agent.py,
# test_ha_integration.py, test_homeassistant.py
sed -i '' 's/"OldName"/"NewName"/g' tests/**/*.py
sed -i '' 's/OldName/NewName/g' tests/**/*.py
```

## README & Docs

| File | What to Change |
|------|---------------|
| `README.md` | Title, badges, description |
| `docker/SOUL.md` | Container persona |
| `website/docs/` | Hundreds of markdown files (optional — deploy new docs site) |

## URLs — GitHub & Docs

After forking the repo, update all URLs:

```bash
# GitHub repo URLs
sed -i '' 's|github.com/OldOrg/old-repo|github.com/NewOrg/new-repo|g' **/*.{py,ts,tsx,md,json,yaml}
sed -i '' 's|raw.githubusercontent.com/OldOrg/old-repo|raw.githubusercontent.com/NewOrg/new-repo|g' **/*.{py,md}

# Documentation URLs
sed -i '' 's|old-docs-site.com|new-docs-site.com|g' **/*.{py,ts,tsx,md}

# Config URLs (model catalog, skills index)
# ~/.hermes/config.yaml → url: under model_catalog
```

## Built-in API Key (Out-of-Box Experience)

For a fork that should work immediately without user API key configuration:

1. Create a NewAPI (or similar proxy) token that only allows one model
2. Add it as a `custom_providers` entry in config.yaml
3. Set `model.provider: custom:<builtin-name>`
4. The default key ships with the installed config, user can override later

```yaml
custom_providers:
  - name: builtin
    base_url: https://your-proxy.com/v1
    api_key: sk-your-builtin-token
    model: fixed-model-name
    models:
      fixed-model-name:
        name: fixed-model-name
        context_length: 1000000

model:
  default: fixed-model-name
  provider: custom:builtin
```

## Verification

After making all changes, verify no stale brand references remain:

```bash
# Check for old brand name
grep -rn 'OldBrandName\|OldCreatorName' \
  --include='*.py' --include='*.ts' --include='*.tsx' \
  --include='*.css' --include='*.json' --include='*.yaml' \
  --include='*.html' --include='*.md' . 2>/dev/null | \
  grep -v node_modules | grep -v __pycache__ | grep -v '.git/' | grep -v venv

# Check for old GitHub URLs
grep -rn 'OldOrg/old-repo' . 2>/dev/null | \
  grep -v node_modules | grep -v __pycache__ | grep -v '.git/' | grep -v venv
```

Expected remaining references (don't touch):
- `nousresearch.com` endpoint URLs (functional API endpoints, not brand)
- Old model names in technical model-switching code (e.g. Hermes 3/4 model families)
