# Web/Search Backend Configuration

Hermes Agent's `web_search` and `web_extract` tools use a configured backend. If the backend is broken (wrong API key, missing package), search and extraction fail silently.

## Available Backends

| Backend | Key Required | Install | Search | Extract |
|---------|-------------|---------|--------|---------|
| **firecrawl** | `FIRECRAWL_API_KEY` | built-in | ✅ | ✅ |
| **ddgs** (DuckDuckGo) | none | `pipx inject hermes-agent ddgs` | ✅ | ❌ search-only |
| **tavily** | `TAVILY_API_KEY` | `pipx inject hermes-agent tavily-python` | ✅ | ✅ |
| **exa** | `EXA_API_KEY` | built-in | ✅ | ✅ |
| **parallel** | `PARALLEL_API_KEY` | built-in | ✅ | ✅ |
| **brave-free** | `BRAVE_SEARCH_API_KEY` | built-in (uses requests already in Hermes venv) | ✅ | ✅ (basic) |
| **searxng** | `SEARXNG_URL` (self-hosted URL) | built-in | ✅ | ✅ |

## Quick Diagnosis

```bash
# Check current backend
hermes config get web.backend
hermes config get web.search_backend
hermes config get web.extract_backend

# Check if API key is set
env | grep FIRECRAWL
# If value looks like a placeholder ("y", "xxx", empty), it's broken
```

## Switch to DuckDuckGo (no API key needed, search only)

Useful when Firecrawl or other paid backends have invalid/missing credentials.

```bash
# 1. Install ddgs in Hermes venv
pipx inject hermes-agent ddgs

# 2. Enable the plugin
hermes plugins enable web-ddgs

# 3. Switch config
hermes config set web.backend ddgs
hermes config set web.search_backend ddgs
hermes config set web.extract_backend ddgs

# 4. Verify
hermes config get web.backend  # should show 'ddgs'
```

**Limitation**: DuckDuckGo is **search-only**. `web_extract` will fail with:
> "DuckDuckGo (ddgs) is a search-only backend and cannot extract URL content."

For extraction, you need Firecrawl, Tavily, or another full backend.

## Switch to Firecrawl (full search + extract)

```bash
# Get a real API key from https://firecrawl.dev (free tier available)
# Then set it:
hermes config set web.backend firecrawl
hermes config set web.extract_backend firecrawl
# Add to ~/.hermes/.env:
# FIRECRAWL_API_KEY=your-real-key
```

## Switch to Tavily (full search + extract, free tier)

```bash
# 1. Sign up at https://app.tavily.com (free tier: 1000 queries/month)
pipx inject hermes-agent tavily-python

# 2. Enable plugin
hermes plugins enable web-tavily

# 3. Set key in ~/.hermes/.env:
# TAVILY_API_KEY=your-real-key

# 4. Configure
hermes config set web.backend tavily
hermes config set web.search_backend tavily
hermes config set web.extract_backend tavily
```

## Plugins vs Built-in Tools

- Hermes has **built-in** `web_search` and `web_extract` tools (available as function calls)
- The **plugins** (`web-ddgs`, `web-firecrawl`, etc.) provide alternative backends for these built-in tools
- Enable the plugin that matches your backend: `hermes plugins enable web-<backend>`
- The plugin is only needed if the backend requires non-built-in dependencies (ddgs, tavily)

## Common Failure Patterns

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "Set FIRECRAWL_API_KEY" | API key missing or placeholder | Get real key or switch backend |
| "not installed — run pip install" | Package missing from Hermes venv | `pipx inject hermes-agent <pkg>` |
| "search-only backend" | Using ddgs for extract | Switch to firecrawl/tavily for extract |
| "Takes effect on next session" | Plugin enabled but session not refreshed | Start `/new` or restart gateway |

## Trick: Use curl + GitHub API for READMEs

When web_extract is unavailable, read GitHub READMEs directly:

```bash
curl -sL https://api.github.com/repos/<owner>/<repo>/readme | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
print(base64.b64decode(d['content']).decode())"
```

## Multi-Machine Propagation

When the same web backend config needs to be applied across multiple machines (e.g. MacBook Air + AIPC + HomeServer):

### Prerequisites — SSH PATH Fallbacks

On Linux machines, `hermes` and `pipx` may NOT be in the SSH login PATH (even if they work in an interactive terminal). Always use full paths:

```bash
# Don't assume:
hermes config set web.backend tavily        # May fail: "hermes: not found"
pipx inject hermes-agent tavily-python      # May fail: "pipx: not found"

# Use full paths:
~/.local/bin/hermes config set web.backend tavily
~/.local/bin/pipx inject hermes-agent tavily-python
```

The Hermes venv Python is at `~/.local/share/pipx/venvs/hermes-agent/bin/python3` on Linux, NOT `python`.

### Propagation Recipe

```bash
# Per-machine: Add API keys to .env
ssh user@machine 'cat >> ~/.hermes/.env << '\''EOF'\''

# Web tools
TAVILY_API_KEY=your-key
BRAVE_SEARCH_API_KEY=your-key
EOF'

# Configure backend
ssh user@machine '~/.local/bin/hermes config set web.backend tavily'
ssh user@machine '~/.local/bin/hermes config set web.search_backend tavily'
ssh user@machine '~/.local/bin/hermes config set web.extract_backend tavily'

# Install package in Hermes venv
ssh user@machine '~/.local/bin/pipx inject hermes-agent tavily-python'

# Enable plugins
ssh user@machine '~/.local/bin/hermes plugins enable web-tavily'
ssh user@machine '~/.local/bin/hermes plugins enable web-ddgs'
ssh user@machine '~/.local/bin/hermes plugins enable web-brave-free'

# Hot-reload gateway (USR1 on Linux, launchctl on macOS)
ssh user@machine 'systemctl --user kill -s USR1 hermes-gateway'
```

### Verify Across Machines

```bash
for host in machine-a machine-b machine-c; do
  echo "=== $host ==="
  ssh user@$host 'grep -A3 "^web:" ~/.hermes/config.yaml'
done
```

### Plugin Activation Timing

`hermes plugins enable` prints "Takes effect on next session." The config change (`web.backend`) takes effect immediately in the built-in tools — the plugin enables additional backend implementations. Restarting the gateway (USR1) is sufficient to pick up plugin changes on the next agent session.

### Key Storage Safety

- API keys go into `~/.hermes/.env` (line-level append, never overwrite)
- Do NOT store keys in `memory()` — the system blocks them with a security rule ("hermes_env" pattern)
- Keys in `.env` survive `hermes update` (pipx replaces site-packages but leaves configs)
- For multi-machine, append to `.env` on each machine individually — do NOT share the same `.env` file across machines with different platform credentials

## Recovery From Broken Firecrawl

The default Hermes web backend is `firecrawl`. If `FIRECRAWL_API_KEY` is a placeholder (e.g. `y`, `xxx`, `changeme`), both `web_search` and `web_extract` fail. The fix is to switch to an alternative backend (see sections above). The Firecrawl key can remain in `.env` — switching the backend config is sufficient.
